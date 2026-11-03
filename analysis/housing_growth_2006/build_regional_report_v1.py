"""Create one portable HTML research report from frozen, verified analysis outputs."""
from pathlib import Path
import base64
import csv
import hashlib
import html
import json

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).parent
DATA=HERE/'regional_expansion_v1'
EP=ROOT/'video-agent-studio/episodes/housing-choice-networth-20261020'
OUT=ROOT/'reports/regional_growth_report_v1'
OUT.mkdir(parents=True,exist_ok=True)
TARGET=OUT/'지역별_집값상승_분석보고서_v1.html'
ORDER=['서울','경기','인천','부산','대구','대전','세종']
PALETTE=['#286cda','#a95025','#28735e','#8059a0','#b34252','#7a6518','#366c85']
def load(path):return json.loads(path.read_text(encoding='utf8'))
def records(path):return list(csv.DictReader(path.open(encoding='utf-8-sig')))
def qlabel(q):return q[:4]+'년 '+q[-1]+'분기'
def pct(x,n=2):return f'{x:+.{n}f}%'.replace('-','−')
def span(x):return f'<span class="{"positive" if x>=0 else "negative"}">{pct(x)}</span>'
def name(region):return '대구 <small>군위 제외</small>' if region=='대구' else region
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
result=load(DATA/'results.json')
qa=load(EP/'qa/regional-analysis-v1/findings.json')
audit=load(EP/'research/regional-coverage-v1/coverage.json')
assert result['included_regions']==ORDER and result['normalization']['api_rows']['광주']==0
assert qa['summary']['discrepancies']==0
summaries={r['region']:r for r in result['summaries']}
paths={r:[] for r in ORDER}
for row in records(DATA/'quarterly_index.csv'):
    paths[row['region']].append({'q':row['quarter'],'v':float(row['index']),
                                'n':int(float(row['matched_complexes'])) if row['matched_complexes'] else None})
for region in ORDER:
    series={p['q']:p['v'] for p in paths[region]}
    for n,start in [(3,'2023Q2'),(5,'2021Q2'),(10,'2016Q2')]:
        assert abs(((series['2026Q2']/series[start])**(1/n)-1)*100-summaries[region][f'cagr_{n}y_pct'])<1e-10
coverage={r['region']:r for r in records(DATA/'analysis_coverage.csv')}
valid_transactions=sum(int(r['transactions']) for r in coverage.values())
sens={(r['region'],int(r['min_trades'])):r for r in result['sensitivity']}

def mini(region):
    s=[p for p in paths[region] if p['q']>='2020Q1']
    start=s[0]['v']
    coords=[(42+i/(len(s)-1)*480,166-(p['v']/start*100)/200*144) for i,p in enumerate(s)]
    d=' '.join(('M' if i==0 else 'L')+f'{x:.2f},{y:.2f}' for i,(x,y) in enumerate(coords))
    x,y=coords[-1]
    return f'''<svg class="mini-chart" viewBox="0 0 560 210" role="img" aria-label="{region} 2020년 1분기부터 2026년 2분기까지의 가격 경로, 2020년 1분기 100 기준">
    <line x1="42" x2="522" y1="94" y2="94" stroke="#b6c0c5" stroke-dasharray="4 4"/>
    <line x1="42" x2="522" y1="166" y2="166" stroke="#dce1e2"/>
    <text x="5" y="98">100</text><text x="18" y="170">0</text><text x="5" y="26">200</text>
    <path d="{d}" fill="none" stroke="{PALETTE[ORDER.index(region)]}" stroke-width="3.5" stroke-linejoin="round"/>
    <circle cx="{x}" cy="{y}" r="4" fill="{PALETTE[ORDER.index(region)]}"/>
    <text x="42" y="197">2020</text><text x="259" y="197">2023</text><text x="482" y="197">2026 Q2</text></svg>'''

summary_rows=[]
profile_cards=[]
observations={
 '서울':'기본 표본에서 이전 고점을 넘어섰고, 최근 3년 상승률이 5년 상승률보다 높습니다. 최근 반등의 체감과 2022년 출발 연간 평균의 결과를 구분해서 읽어야 합니다.',
 '경기':'기본 표본에서는 이전 고점보다 낮지만, 거래 문턱을 5건으로 높이면 회복으로 판정됩니다. 하나의 회복 여부를 확정하기보다 표본 민감도를 함께 봐야 합니다.',
 '인천':'3년·10년 상승률이 양수여도 이전 고점까지 회복했다는 뜻은 아닙니다. 구간 상승과 고점 회복은 서로 다른 질문입니다.',
 '부산':'10년 상승률은 양수지만 5년은 음수입니다. 이 지표의 관측 저점은 2025년 2분기이며, 저점 이후 반등과 장기 성과를 나눠 읽습니다.',
 '대구':'3년 연복리는 약 −0.02%로 거의 보합이며 5년은 음수입니다. 행정경계 변화의 영향을 줄이기 위해 모든 기간에서 군위를 제외했습니다.',
 '대전':'10년 연복리는 양수인 반면 5년은 소폭 음수입니다. 지역 전체의 장기 상승만으로 특정 매수 시점의 결과를 설명할 수 없습니다.',
 '세종':'10년 상승과 5년 하락이 함께 관측됩니다. 단지 30개 이상이라는 조건을 연속 충족하는 기본 경로가 2015년 1분기부터여서 그 이전 선은 연결하지 않았습니다.'}
for region in ORDER:
    r=summaries[region]
    summary_rows.append(f'<tr><th scope="row">{name(region)}</th>'+''.join(f'<td>{span(r[f"cagr_{n}y_pct"])}</td>' for n in (3,5,10))+f'<td>{span(r["latest_vs_peak_pct"])}</td><td>{r["latest_matched_complexes"]:,}</td></tr>')
    recovery=qlabel(r['first_recovery_quarter']) if r['first_recovery_quarter'] else '기본 표본에서 미회복'
    profile_cards.append(f'''<article class="region-card" id="region-{ORDER.index(region)}"><div class="region-heading"><h3>{name(region)}</h3><span class="pill">3년 연복리 {pct(r['cagr_3y_pct'])}</span></div>
    <p>{observations[region]}</p>{mini(region)}<dl class="region-metrics"><div><dt>이전 고점</dt><dd>{qlabel(r['peak_quarter'])}</dd></div><div><dt>이후 관측 저점</dt><dd>{qlabel(r['trough_quarter'])}</dd></div><div><dt>고점→저점 하락</dt><dd>{span(r['drawdown_pct'])}</dd></div><div><dt>저점 대비 반등</dt><dd>{span(r['latest_vs_trough_pct'])}</dd></div></dl>
    <p class="micro">최초 고점 재도달: {recovery} · 전체 연결 경로의 최소 단지 수 {r['min_matched_complexes']:,}개</p></article>''')

sensitivity_rows=[]
for region in ORDER:
    cells=[]
    for minimum in (2,3,5):
        r=sens.get((region,minimum))
        cells.append('<td class="unavailable">경로 부족</td>' if r is None else f'<td>{span(r["latest_vs_peak_pct"])}<small>최소 {r["min_matched_complexes"]:,}개 단지</small></td>')
    sensitivity_rows.append(f'<tr><th scope="row">{name(region)}</th>'+''.join(cells)+'</tr>')

coverage_rows=[]
for region in ORDER+['광주']:
    r=coverage.get(region)
    count=f'{int(r["transactions"]):,}' if r else '미확보'
    start=qlabel(summaries[region]['first_contiguous_quarter']) if r else '—'
    note='기존 수도권 마스터' if region in ('서울','경기','인천') else '추가 수집 XML'
    if region=='대구':note+=' · 군위 325건 제외'
    if region=='광주':note='추가 수집 응답 1,245셀 모두 0건'
    if region=='세종':note+=' · 2015년 이전 연결 제외'
    coverage_rows.append(f'<tr><th scope="row">{region}</th><td>{count}</td><td>{start}</td><td>{note}</td></tr>')

sources=[DATA/'results.json',DATA/'quarterly_index.csv',DATA/'regional_summary.csv',DATA/'sensitivity.csv',DATA/'analysis_coverage.csv',EP/'research/regional-coverage-v1/coverage.json',EP/'qa/regional-analysis-v1/findings.json',HERE/'research/collection_status.json',HERE/'research/external_factors_sources.json']
manifest={p.relative_to(ROOT).as_posix():digest(p) for p in sources}
payload={'regions':ORDER,'colors':dict(zip(ORDER,PALETTE)),'paths':paths,'summaries':summaries,'endpoint':'2026Q2'}
substitutions={
 'FONT_REGULAR':base64.b64encode((ROOT/'assets/fonts/Pretendard-Regular.woff2').read_bytes()).decode(),
 'FONT_BOLD':base64.b64encode((ROOT/'assets/fonts/Pretendard-Bold.woff2').read_bytes()).decode(),
 'SUMMARY_ROWS':''.join(summary_rows),'PROFILE_CARDS':''.join(profile_cards),'SENSITIVITY_ROWS':''.join(sensitivity_rows),'COVERAGE_ROWS':''.join(coverage_rows),
 'VALID_COUNT':f'{valid_transactions:,}',
 'PAYLOAD':json.dumps(payload,ensure_ascii=False,separators=(',',':')).replace('</','<\\/'),
 'CSV_DATA':json.dumps((DATA/'regional_summary.csv').read_text(encoding='utf-8-sig'),ensure_ascii=False).replace('</','<\\/'),
 'SOURCE_ITEMS':''.join(f'<li><code>{html.escape(path)}</code><small>SHA-256 {sha[:16]}…</small></li>' for path,sha in manifest.items()),
 'INITIAL_CHART':'',
 'REPORT_SCRIPT':(HERE/'regional_report.js').read_text(encoding='utf8'),
}
document=(HERE/'regional_report_template.html').read_text(encoding='utf8')
for key,value in substitutions.items():document=document.replace('{{'+key+'}}',value)
assert '{{' not in document
assert '<script src=' not in document and 'https://cdn.' not in document
TARGET.write_text(document,encoding='utf8')
(OUT/'source_manifest.json').write_text(json.dumps({'report':TARGET.name,'sha256':digest(TARGET),'source_hashes':manifest,'endpoint':'2026Q2','valid_transactions':valid_transactions,'regions':ORDER,'data_checks':21},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'report':str(TARGET),'bytes':TARGET.stat().st_size,'validated_cagr_values':21,'valid_transactions':valid_transactions},ensure_ascii=False))
