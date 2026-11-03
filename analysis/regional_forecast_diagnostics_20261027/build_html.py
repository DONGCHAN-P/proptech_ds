"""Build a self-contained, readable companion to the new diagnostic report."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import base64
import html
import json
import re
import pandas as pd
import mistune
from bs4 import BeautifulSoup
from diagnostics import OUT,sha,save,load

def main():
    root=OUT.parent.parent
    report=root/'reports/지역별 집값 예측 실패 진단.md'
    text=report.read_text('utf-8')
    sections=re.split(r'\n## ',text)
    md=mistune.create_markdown(plugins=['table'])
    old=(root/'reports/regional_forecast_report_v1/template.html').read_text('utf-8')
    style=re.search(r'<style>(.*?)</style>',old,re.S).group(1)
    style+='''
    .sidebar nav span{flex:0 0 18px;white-space:nowrap}.article p{margin:16px 0;line-height:1.95}.article table{margin:20px 0}.article img{width:100%;height:auto;border:1px solid #e8edf3;border-radius:8px;margin:7px 0}.article h2{margin-bottom:18px}.article p:has(img){margin:24px 0}.article a{overflow-wrap:anywhere}.article code{background:#f1f4f9;padding:2px 4px}.article table th,.article table td{white-space:normal;min-width:85px}.article table th:first-child,.article table td:first-child{min-width:170px}.article .table-wrap{margin:15px 0}.article .table-wrap table{margin:0}.intro p{font-size:14px;color:#465b70}.cases table th,.cases table td{white-space:nowrap}.section>h2{margin-bottom:12px}.hero .lead{max-width:780px}.case-note{font-size:12px;color:var(--muted);margin-top:14px}.scroll-hint{display:none}@media(max-width:800px){.article p{font-size:14px}.article table{font-size:12px}.card.article{padding:23px 19px}.scroll-hint{display:block;font-size:11px;color:var(--muted)}}@media(max-width:450px){.article table th:first-child,.article table td:first-child{min-width:110px}.article table th,.article table td{min-width:75px;padding:10px 7px}}@media print{.article p{font-size:10pt}.article img{break-inside:avoid}.article table{font-size:8.5pt}.article table th,.article table td{min-width:0}.article table th:first-child,.article table td:first-child{min-width:0}.scroll-hint{display:none}}
    '''
    nav='<a href="#summary"><span>00</span>핵심 결과</a>'
    content=''
    for i,section in enumerate(sections[1:],1):
        heading,body=section.split('\n',1)
        nav+=f'<a href="#section-{i}"><span>{i:02d}</span>{html.escape(heading)}</a>'
        content+=f'<section class="section" id="section-{i}"><div class="card article"><h2>{html.escape(heading)}</h2>{md(body)}</div></section>'
    intro='\n'.join(sections[0].splitlines()[2:])
    regime=pd.read_csv(OUT/'regime_diagnostics.csv')
    share=regime[regime.regime.isin(['boom','turn'])].groupby('level').error_share.sum()*100
    cases=json.loads(pd.read_csv(OUT/'worst_cases.csv').to_json(orient='records',force_ascii=False))
    case_payload=json.dumps(cases,ensure_ascii=False,allow_nan=False).replace('</','<\\/')
    page=f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>지역별 집값 예측 실패 진단</title><style>{style}</style></head><body>
    <a class="sr-only" href="#main">본문 바로가기</a><div class="wrap"><aside class="sidebar"><div class="brand">데이터로 보는 부동산</div><p class="eyebrow muted">Forecast / Diagnostic study</p><nav>{nav}<a href="#cases"><span>07</span>실패 사례 검색</a></nav><div class="side-bottom">분석 기준일<br><b>2026년 10월 27일</b><br><br>앞선 연구의 후속 진단<br>19개 같은 시점에서 비교</div></aside>
    <main id="main"><div class="topbar"><p>지역별 집값 예측 · 실패 진단 및 후속 실험</p><button id="print-btn" type="button">인쇄 / PDF 저장</button></div><header class="hero" id="summary"><p class="eyebrow">Failure analysis · controlled experiments</p><h1>집값 예측의 실패를<br>지역과 국면으로 분해했습니다</h1><p class="lead">큰 상승·하락의 폭을 작게 예측하는 문제를 확인했습니다. 새 전세 자료와 모멘텀 보정 구조를 시험했고, 가격 목표의 측정 차이까지 대조했습니다.</p><div class="decision"><span class="dot"></span>기존 v3 HGB 유지 · 다음 우선순위: 가격 목표의 강건성 검증</div></header>
    <div class="kpis"><div class="kpi"><span>2020~2023년의 균형 오차 비중</span><strong>{share['province']:.1f}%</strong><em>시도 · 시군구 {share['district']:.1f}%</em></div><div class="kpi"><span>새로 확보한 공식 전세 관측</span><strong>4,533</strong><em>11개 시도 · 가격 + 수급 지수</em></div><div class="kpi"><span>추가로 비교한 점예측 대안</span><strong>2개</strong><em>전세 변수군 / 모멘텀 + 잔차</em></div><div class="kpi"><span>관련 Python 회귀 테스트</span><strong>58개</strong><em>모델·범위의 저장본 재현 확인</em></div></div>
    <div class="card article intro">{md(intro)}</div><div style="height:25px"></div>{content}
    <section class="section" id="cases"><div class="section-head"><p class="eyebrow">Case explorer</p><h2>큰 오차 사례를 직접 확인</h2><p>행정 수준별 절대오차 상위 25건입니다. 아래 표는 원인 진단용 사례이며 전체 지역을 대표하는 표본은 아닙니다.</p></div><div class="card cases"><div class="toolbar"><label>지역 수준<select id="case-level"><option value="province">시도</option><option value="district">시군구</option></select></label><label>지역 검색<input id="case-search" type="search" placeholder="예: 세종, 김포, 서대문"></label><button id="case-download" class="spacer" type="button">선택 사례 CSV</button></div><p id="case-caption" class="small muted" aria-live="polite"></p><div class="table-wrap"><table><thead><tr><th>지역</th><th>예측 시점</th><th>실제 변화율</th><th>예측 변화율</th><th>절대오차</th></tr></thead><tbody id="case-table"></tbody></table></div><p class="case-note">변화율 단위 %, 절대오차 단위 %p. 실제는 자체 단지·면적 매칭 추정량입니다. 입력월·거래 품질·방향 전환 표시는 <a href="../analysis/regional_forecast_diagnostics_20261027/worst_cases.csv">상세 원표</a>에 남겼습니다.</p></div></section>
    <footer class="footer"><p>데이터로 보는 부동산 · 2026.10.27</p><p><a href="./지역별%20집값%20예측%20실패%20진단.md">Markdown 원문</a> · <a href="./지역별%20집값%20예측%20반복%20검증.html">앞선 반복 검증 보고서</a> · <a href="../analysis/regional_forecast_diagnostics_20261027/README.md">재현·고정본 목록</a></p><p>차트와 사례 집계를 이 파일에 내장했습니다. 프로젝트 원표 링크는 원래 폴더 구조에서 열 수 있습니다.</p></footer></main></div>
    <script id="case-data" type="application/json">{case_payload}</script>
    <script>
    const $=id=>document.getElementById(id),D=JSON.parse($('case-data').textContent);let shown=[];
    const escapeText=s=>String(s).replace(/[&<>"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));
    function render(){{const q=$('case-search').value.trim();shown=D.filter(r=>r.level===$('case-level').value&&r.name.includes(q));$('case-caption').textContent=shown.length+'개 사례';$('case-table').innerHTML=shown.map(r=>`<tr><th>${{escapeText(r.name)}}</th><td>${{r.origin.slice(0,7)}}</td><td>${{r.actual_pct.toFixed(2)}}%</td><td>${{r.prediction_pct.toFixed(2)}}%</td><td>${{r.ae_pp.toFixed(2)}}%p</td></tr>`).join('')||'<tr><td colspan="5">검색 결과가 없습니다.</td></tr>';}}
    $('case-level').addEventListener('change',render);$('case-search').addEventListener('input',render);$('print-btn').addEventListener('click',()=>window.print());
    $('case-download').addEventListener('click',()=>{{if(!shown.length)return;const columns=['level','name','origin','actual_pct','prediction_pct','ae_pp'],cell=v=>'"'+String(v??'').replaceAll('"','""')+'"';const text='\\ufeff'+[columns.map(cell).join(','),...shown.map(r=>columns.map(c=>cell(r[c])).join(','))].join('\\r\\n');const url=URL.createObjectURL(new Blob([text],{{type:'text/csv;charset=utf-8'}}));const a=document.createElement('a');a.href=url;a.download='forecast_failure_cases.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),3000);}});
    render();document.body.dataset.ready='true';
    </script></body></html>'''
    soup=BeautifulSoup(page,'html.parser')
    for image in soup.select('img[src]'):
        path=(report.parent/image['src']).resolve()
        image['src']='data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode()
    for table in soup.select('.article table'):
        div=soup.new_tag('div',attrs={'class':'table-wrap'});table.wrap(div)
        hint=soup.new_tag('p',attrs={'class':'scroll-hint'})
        hint.string='표가 화면보다 넓으면 좌우로 움직여 확인할 수 있습니다.'
        div.insert_after(hint)
    target=root/'reports/지역별 집값 예측 실패 진단.html'
    target.write_text(str(soup),'utf-8')
    save(OUT/'html_manifest.json',{'output':str(target.relative_to(root)),'sha256':sha(target),
        'markdown_sha256':sha(report),'self_contained_charts':True,'embedded_cases':len(cases),
        'figure_sha256':{name:sha(OUT/name) for name in ['error_concentration.png','factor_effects.png',
           'extreme_moves.png','interval_comparison.png','model_trials.png']},'builder_sha256':sha(Path(__file__))})
    print(str(target),target.stat().st_size)

if __name__=='__main__':main()
