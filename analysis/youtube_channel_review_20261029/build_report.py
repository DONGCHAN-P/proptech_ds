"""Reproducible local HTML/Markdown analysis from frozen owner API responses."""
import csv
import html
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
REPORT = ROOT / 'reports/유튜브_채널분석_20261029'
REPORT.mkdir(parents=True, exist_ok=True)


def load(p): return json.loads((BASE / p).read_text(encoding='utf-8'))
def esc(s): return html.escape(str(s))
def pct(n, d): return 100*n/d if d else 0
def num(n): return f'{n:,.0f}'


def main():
    snapshot = load('raw/data_api_snapshot.json')
    initial = load('raw/initial_analytics.json')
    ext = load('raw/extended_analytics.json')['reports']
    lookup = {v['id']:v for v in snapshot['videos']}
    metrics = {v['video']:v for v in ext['video_engaged']['rows']}
    long_ids = [v['id'] for v in snapshot['videos'] if v['privacy']=='public' and v['duration_s']>180 and v['id'] in metrics]
    short_ids = [v['id'] for v in snapshot['videos'] if v['privacy']=='public' and v['duration_s']<=180 and v['id'] in metrics]
    rows = []
    for video in snapshot['videos']:
        m = metrics.get(video['id'], {})
        early = ext.get('early3_'+video['id'], {}).get('rows', [])
        rows.append({**video, 'format_proxy': '본편' if video['duration_s']>180 else '쇼츠 후보',
                     **{'period_'+k:v for k,v in m.items() if k!='video'},
                     'early3_report_days_views':sum(x['views'] for x in early) if early else None,
                     'early3_report_days_watch_minutes':sum(x['estimatedMinutesWatched'] for x in early) if early else None})
    all_fields = list(dict.fromkeys(k for row in rows for k in row))
    with (BASE / 'tables/videos_joined.csv').open('w', encoding='utf-8-sig', newline='') as f:
        writer=csv.DictWriter(f,fieldnames=all_fields);writer.writeheader();writer.writerows(rows)
    formats={r['creatorContentType']:r for r in ext['formats']['rows']}
    long, short=formats['videoOnDemand'],formats['shorts']
    total=initial['reports']['totals']['rows'][0]
    search_long=next(r for r in ext['traffic_formats']['rows'] if r['insightTrafficSourceType']=='YT_SEARCH' and r['creatorContentType']=='videoOnDemand')
    cards = [
      ('공개 영상', '19편', '본편 6 · 쇼츠 13 / 현재 누적 스냅샷'),
      ('현재 구독자', num(snapshot['channel']['subscribers'])+'명', '기간 구독 증가와 현재 구독자 수는 별도'),
      ('분석 기간 조회수', num(total['views']), '10/02~10/25 · 이후 영상은 평가 대기'),
      ('분석 기간 시청시간', f"{total['estimatedMinutesWatched']/60:.1f}시간", '본편과 쇼츠를 분리해 해석'),
    ]
    insights = [
      ('01', '채널의 주력은 지역을 콕 집은 검색형 분석이다.',
       f"본편 검색 유입은 {num(search_long['views'])}회로 본편 조회수의 {pct(search_long['views'],long['views']):.1f}%다. 시청시간에서는 {num(search_long['estimatedMinutesWatched'])}분, {pct(search_long['estimatedMinutesWatched'],long['estimatedMinutesWatched']):.1f}%를 차지한다. 검색어 상위에는 ‘창릉신도시’ 456회, ‘창릉’ 385회, ‘왕숙’ 182회가 보인다.",
       '지역명 + 시청자의 선택을 제목 앞에 둔다. 예: ‘창릉 S1·S4·S5, 내 예산으로 고르면?’ 지도·가격·입주 시점을 연결하는 기존 강점을 살린다. 검색어 표는 상위 25개 부분집합이다.'),
      ('02', '조회수를 만드는 쇼츠와 시간을 만드는 본편의 역할을 나눠야 한다.',
       f"쇼츠는 기간 조회수의 {pct(short['views'],total['views']):.1f}%지만 시청시간은 {pct(short['estimatedMinutesWatched'],total['estimatedMinutesWatched']):.1f}%다. 본편은 반대로 시청시간의 {pct(long['estimatedMinutesWatched'],total['estimatedMinutesWatched']):.1f}%를 만든다. 창릉·왕숙 두 본편이 합쳐 전체 시청시간의 {pct(2711+2388,total['estimatedMinutesWatched']):.1f}%를 차지한다.",
       '쇼츠는 한 질문에 한 답을 주고, 본편은 선택 근거를 완성한다. 쇼츠 조회수 대비 본편 조회수를 전환율로 계산하지 않는다. 같은 시청자의 이동 경로는 이번 자료에서 확인되지 않는다.'),
      ('03', '구체적인 반문이 목록형 설명보다 강한 후보로 보인다.',
       '‘GTX만 생기면 신도시 가격도 같아질까?’는 평균 시청비율 122.6%, ‘수도권 부동산 시장을 데이터로 시각화하면?’은 100.0%다. ‘신도시 청약 전, 이 5가지’는 22.1%, ‘왕숙 교통 시차’는 27.1%였다. 다만 GTX 쇼츠의 참여 조회수는 96회, 체크리스트는 33회다.',
       '새 쇼츠는 ‘정보 5가지’보다 ‘당연해 보이는 계산이 달라지는 이유’ 한 가지로 만든다. 100% 초과는 재시청 등이 섞인 구간/재생 비율이며 완주한 사람의 비율로 읽지 않는다. 제목 효과와 편집 효과는 아직 분리되지 않았다.'),
      ('04', '가장 먼저 손댈 편집 지점은 본편 시작 30초다.',
       '약 30초에 가장 가까운 유지율 표본은 창릉 34.0초 64.2%, 왕숙 28.0초 69.5%, 교산 32.3초 68.6%, 광교·동탄 31.8초 38.1%다. 광교·동탄은 19.1초 68.0%에서 31.8초 38.1%로 내려간다.',
       '첫 3초에 질문, 10초 안에 지도나 비교 결과 일부, 30초 안에 첫 근거를 보여준다. 이탈 구간의 원인은 해당 영상의 실제 대사·화면과 대조해 후속 검증한다. 이 보고서는 유지율만으로 특정 장면을 원인이라고 단정하지 않는다.'),
      ('05', '같은 게시 초기 기간에서도 창릉의 시청시간이 두드러졌다.',
       '게시일과 다음 이틀을 합친 API 보고일 3개에서 창릉 본편은 573회·1,317분, 왕숙은 134회·292분, 교산은 201회·264분, 광교·동탄은 198회·96분이다. 누적 노출 기간 차이만으로 창릉의 우위를 설명하기 어렵다.',
       '창릉의 ‘후보를 좁혀 주는 비교’ 구성을 다음 지역편의 우선 가설로 삼는다. 게시 시간·수요·유입의 차이는 남아 있다. 이 비교는 달력 보고일 기준이며 정확한 첫 72시간 비교가 아니다.'),
      ('06', '모바일 가독성이 우선이고, 본편은 TV 시청도 챙겨야 한다.',
       f"기기별 표에서 쇼츠 모바일 조회는 4,721회로 형식 합계 대비 {pct(4721,short['views']):.1f}%다. 본편은 모바일 2,191회, TV 214회다. TV는 조회수의 {pct(214,long['views']):.1f}%이지만 시청시간의 {pct(1252,long['estimatedMinutesWatched']):.1f}%를 만든다.",
       '쇼츠는 큰 숫자와 하나의 시선 초점을 유지한다. 본편 지도·출처는 TV에서도 읽을 크기를 확보한다. 기기 표와 형식 합계는 개인정보 보호·집계 처리 등의 영향으로 일부 불일치할 수 있어 비율의 분모를 명시했다.'),
      ('07', '왕숙은 구독 기여 신호가 있지만 표본은 작다.',
       '왕숙 본편의 영상 시청 페이지에서 구독 5건이 기록됐다. 창릉 1건, 광교·동탄 1건과 대비된다. 왕숙의 참여 조회수 471회 대비 1,000회당 약 10.6건이다. 전체 채널 구독 증가는 12건이며 영상별 합계와 같을 필요가 없다.',
       '구독 CTA는 ‘다음에 무엇을 해결해 주는가’와 연결한다. 신규 채널의 5건 차이로 주제의 장기 구독 효과를 확정하지 않는다. 영상별 지표는 해당 영상 시청 페이지에서 발생한 구독만 포함한다.'),
      ('08', '새 예산 영상과 매매·전세·월세편의 성패는 아직 판단할 수 없다.',
       'Analytics의 조회수만 요청한 경우와 시청 지표를 함께 요청한 경우 모두 마지막 반환일이 10월 25일이었다. 10월 26일 공개한 매매·전세·월세편과 10월 28일 공개한 예산 본편·새 쇼츠는 그 이후다. Data API 현재 누적 수치는 별도 표에서만 제공한다.',
       '두 신규 주제를 기존 지역 영상보다 약하다고 판정하지 않는다. 실제 처리된 보고일이 늘면 같은 게시 후 보고일로 다시 비교한다. 최신 영상의 CTR·유지율·유입은 빈칸을 유지한다.'),
    ]
    actions=[
      ('1 · 이번 쇼츠','질문 하나 → 숫자가 변하는 이유 → 생활 속 차이','반문형 훅 / 핵심 수치 1~2개 / 30~45초 내외를 우선 설계','기존 우수 쇼츠와 게시 후 보고일 3개·7개 기준 참여 조회수, 평균 시청비율, 공유 수를 비교'),
      ('2 · 다음 본편','지역명과 실제 선택 질문을 제목 전면에','전반 30초에 첫 비교 결과와 근거를 보여주고 공통 설명은 뒤로','약 30초 유지율과 평균 시청비율을 같은 길이대 기존 본편과 비교'),
      ('3 · 연결 설계','쇼츠에서 해결한 질문을 본편의 한 장면에 연결','관련 동영상·고정 댓글 등 실제 설정 여부를 별도 확인','단순 조회수 비율 대신 확인 가능한 유입 소스와 시청시간 변화 기록'),
      ('4 · 후속 측정','변수 하나씩 바꿔 3~5편 축적','훅·길이·주제·발행 시간 중 하나만 우선 변경','현재 표본의 최고값을 성공 보장 수치로 쓰지 않고 기존 분포와 비교'),
    ]
    methods=[
      '추출 시각: '+snapshot['fetched_at_kst']+' (KST). API 조회 권한으로 채널 ID를 검증했다. 메타데이터·공개 상태 변경은 수행하지 않았다.',
      '현재 누적 스냅샷: 공개 19편(본편 6, 180초 이하 쇼츠 후보 13), 비공개 2편. 영상별 형식 표시는 길이 기반 보조 분류이며 형식 합계는 creatorContentType API 응답을 사용했다.',
      '기간 분석: 2026-10-02~2026-10-25. 요청 종료일은 10월 29일이었지만 실제 반환일을 확인하고 공통 종료일을 25일로 고정했다. 보고일 경계는 YouTube의 Pacific Time 기준이다.',
      'engagedViews는 API가 반환한 참여 조회수다. 본 보고서의 참여 조회수/조회수 비율은 관측 비율이며 쇼츠 피드 노출 대비 시청 선택률·완주율·고유 시청자 전환율로 바꿔 해석하지 않는다.',
      '평균 시청시간·비율은 API 반환값을 그대로 사용했다. 조회수×평균 시청시간으로 시청시간을 재계산하거나 단순 영상 평균으로 채널 평균을 만들지 않았다.',
      '유지율은 elapsedVideoTimeRatio 1% 간격의 표본이다. 약 30초 비교는 실제 표본 시간을 함께 표시했다. audienceWatchRatio는 재시청을 포함해 100%를 넘을 수 있으며 개별 시청자의 생존 확률로 단정하지 않는다.',
      '초기 성과는 게시일의 Pacific 날짜와 다음 이틀을 합친 3개 보고일이다. 각 영상의 게시 시각이 달라 정확한 72시간 길이는 같지 않다. 아직 세 보고일이 확보되지 않은 영상은 제외했다.',
      '총 31개 확장 요청 중 왕숙 교통 시차 쇼츠(ETXkCHF4Si0)의 유지율 1개만 HTTP 500으로 수집되지 않았다. 자동 재시도는 하지 않았고 원본 오류 상태를 보존했다. 나머지 확장 요청 30개는 성공했다.',
      '썸네일 노출수·CTR·쇼츠의 시청함/스와이프 비율은 이번 수집에서 확보하지 않았다. 카드 CTR·광고 노출수를 썸네일 지표로 대체하지 않았다. 검색 상위 25개 행은 전체 검색 유입이 아니다.',
      '조회수와 제목의 연관은 기술 통계다. 동일 시청자의 쇼츠→본편 이동, 업로드 시간의 인과 효과, 추천 시스템의 평가 원인은 이번 데이터만으로 식별하지 않았다.',
      '영상별 구독 증가 지표는 영상 시청 페이지 발생분만 포함한다. 기간 채널 구독 증가 12건과 현재 구독자 19명 및 영상별 증가 합계는 서로 다른 집계다.',
      '보고서는 소유자 Analytics를 포함하므로 로컬 보관한다. Claude 협업 자료에는 공개된 제목·누적 조회수·참고 영상 관찰·새 제작안만 전달하고 비공개 Analytics 응답은 제외한다.',
    ]
    titles={'eLF3-1ZaraQ':'창릉','T_GBxTRgRSc':'왕숙','XWAWnSrz7FE':'교산','a9pYQ9iSCBo':'광교·동탄'}
    palette=['#196f8a','#ed9949','#8b6ca8','#dd6571']

    def svg_retention():
        w,h=1000,360; l,t,pw,ph=72,30,870,260
        parts=[f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="본편별 구간 시청비율 곡선"><rect width="1000" height="360" fill="white"/>']
        for y in [0,25,50,75,100]:
            yy=t+ph*(1-y/100);parts.append(f'<path d="M{l} {yy}H{l+pw}" stroke="#e6ecf0"/><text x="{l-12}" y="{yy+5}" text-anchor="end" font-size="15" fill="#647586">{y}%</text>')
        for x in [0,25,50,75,100]:
            xx=l+pw*x/100;parts.append(f'<text x="{xx}" y="{t+ph+28}" text-anchor="middle" font-size="15" fill="#647586">{x}%</text>')
        for (vid,label),color in zip(titles.items(),palette):
            data=ext['retention_'+vid]['rows']; pts=' '.join(f"{l+pw*r['elapsedVideoTimeRatio']:.1f},{t+ph*(1-r['audienceWatchRatio']):.1f}" for r in data)
            parts.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="3"><title>{esc(label)}</title></polyline>')
        parts.append('<text x="510" y="345" text-anchor="middle" font-size="15" fill="#647586">영상 진행 위치 (%) · 각 영상의 실제 길이는 다름</text></svg>')
        return ''.join(parts)

    def bar_chart(items, unit):
        maximum=max(v for _,v in items) or 1
        return '<div class="bars">'+''.join(f'<div class="barrow"><span>{esc(label)}</span><div class="bartrack"><i style="width:{100*v/maximum:.2f}%"></i></div><strong>{v:,.0f}{unit}</strong></div>' for label,v in items)+'</div>'

    def video_table(ids):
        body=''
        for vid in ids:
            v=lookup[vid];m=metrics[vid];e=ext.get('early3_'+vid,{}).get('rows',[])
            early_views=num(sum(x['views'] for x in e)) if e else '—'
            body+=f'<tr><td><a href="{esc(v["url"])}">{esc(v["title"])}</a></td><td>{num(m["views"])}</td><td>{num(m["engagedViews"])}</td><td>{num(m["estimatedMinutesWatched"])}</td><td>{m["averageViewDuration"]}초</td><td>{m["averageViewPercentage"]:.1f}%</td><td>{m["subscribersGained"]}</td><td>{early_views}</td></tr>'
        return '<div class="tablewrap"><table><thead><tr><th>영상</th><th>조회</th><th>참여 조회</th><th>시청분</th><th>평균 시간</th><th>평균 비율</th><th>구독 증가</th><th>초기 3보고일 조회</th></tr></thead><tbody>'+body+'</tbody></table></div>'

    newest=[v for v in snapshot['videos'] if v['privacy']=='public' and v['id'] not in metrics]
    current_table='<div class="tablewrap"><table><thead><tr><th>평가 대기 영상</th><th>게시일 UTC</th><th>현재 누적 조회</th><th>기간 시청 지표</th></tr></thead><tbody>'+''.join(f'<tr><td><a href="{v["url"]}">{esc(v["title"])}</a></td><td>{v["published_at"][:10]}</td><td>{num(v["views"])}</td><td>처리된 기간 밖</td></tr>' for v in newest)+'</tbody></table></div>'
    traffic_labels={'YT_SEARCH':'YouTube 검색','SHORTS':'쇼츠 피드','SUBSCRIBER':'탐색 기능','RELATED_VIDEO':'추천 동영상','EXT_URL':'외부 링크','YT_CHANNEL':'채널 페이지'}
    traffic_charts=''
    for fmt,label in [('videoOnDemand','본편'),('shorts','쇼츠')]:
        subset=[r for r in ext['traffic_formats']['rows'] if r['creatorContentType']==fmt]
        traffic_charts+=f'<div class="panel"><h3>{label} · 유입별 시청시간</h3>'+bar_chart([(traffic_labels.get(r['insightTrafficSourceType'],r['insightTrafficSourceType']),r['estimatedMinutesWatched']) for r in sorted(subset,key=lambda r:r['estimatedMinutesWatched'],reverse=True)[:5]],'분')+'</div>'
    text_insights=''.join(f'<article class="insight"><span class="number">{n}</span><div><h3>{esc(title)}</h3><p>{esc(fact)}</p><p class="action"><b>실행</b> {esc(action)}</p></div></article>' for n,title,fact,action in insights)
    html_doc='''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>데이터로보는부동산 · 채널 분석</title><style>
    :root{--ink:#142c3c;--muted:#647586;--accent:#196f8a;--paper:#f3f6f8}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:17px/1.75 "Malgun Gothic",Arial,sans-serif}main{max-width:1160px;margin:auto;padding:40px 28px 80px}header{background:#142c3c;color:white;border-radius:26px;padding:46px;margin-bottom:24px}h1{font-size:38px;line-height:1.35;margin:12px 0 18px}header p{color:#d0e2ea;max-width:900px}.eyebrow{font-size:13px;letter-spacing:3px;color:#89d1d5}nav{display:flex;flex-wrap:wrap;gap:18px;margin:24px 0}a{color:var(--accent);text-decoration:none}nav a{background:white;padding:8px 15px;border-radius:99px}.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.card,.panel,section{background:white;border:1px solid #e1e8ed;border-radius:18px;padding:25px}.card strong{display:block;font-size:30px;margin:8px 0}.card small{color:var(--muted);font-size:12px;line-height:1.5;display:block}section{margin-top:25px}h2{font-size:27px;margin:0 0 18px}h3{font-size:21px;line-height:1.45;margin:0 0 12px}.lead{font-size:21px;font-weight:700}.note{background:#edf6f7;border-left:4px solid var(--accent);padding:16px 20px;font-size:15px}.insight{display:grid;grid-template-columns:46px 1fr;gap:20px;border-bottom:1px solid #e5ecef;padding:28px 0}.insight:last-child{border:0}.number{font-size:24px;color:#8ca8b4;font-weight:800}.action{color:#3b6478;font-size:15px}.two{display:grid;grid-template-columns:1fr 1fr;gap:18px}.panel{padding:20px}.bars{display:grid;gap:15px}.barrow{display:grid;grid-template-columns:110px 1fr 80px;gap:10px;align-items:center;font-size:13px}.bartrack{height:15px;background:#edf2f5;border-radius:4px;overflow:hidden}.bartrack i{display:block;height:100%;background:var(--accent)}.barrow strong{text-align:right}.tablewrap{overflow:auto}table{border-collapse:collapse;width:100%;font-size:13px;min-width:850px}th,td{text-align:right;padding:13px 9px;border-bottom:1px solid #e6ecf0}th:first-child,td:first-child{text-align:left;min-width:250px;max-width:440px}thead{background:#f2f7f9}td{vertical-align:top}svg{display:block;width:100%;height:auto}.legend{display:flex;flex-wrap:wrap;gap:20px;font-size:14px}.legend i{display:inline-block;width:12px;height:12px;margin-right:8px}.small{font-size:14px;color:var(--muted)}li{margin:10px 0}.pill{display:inline-block;color:#244e62;background:#eaf3f5;padding:4px 10px;border-radius:7px;font-size:13px}footer{font-size:13px;color:var(--muted);margin-top:30px}button{border:0;padding:9px 15px;border-radius:8px;cursor:pointer;background:#196f8a;color:white}details{margin:14px 0}summary{cursor:pointer;font-weight:bold}@media(max-width:760px){main{padding:15px}.cards,.two{grid-template-columns:1fr 1fr}header{padding:27px}h1{font-size:27px}.card{padding:17px}.card strong{font-size:25px}section{padding:20px}.insight{grid-template-columns:32px 1fr;gap:10px}.two{display:block}.panel{margin:12px 0}}@media print{body{background:white}main{max-width:none;padding:0}nav,button{display:none}section,.card{break-inside:avoid}header{color:#142c3c;background:#edf6f7}header p{color:#3b6478}}
    </style><main>'''
    html_doc+=f'<header><div class="eyebrow">CHANNEL RESEARCH · OWNER API</div><h1>조회수 다음에 봐야 할 것<br>데이터로보는부동산 채널 분석</h1><p>지역을 특정한 검색형 본편이 시간을 만들고, 한 가지 반문에 집중한 쇼츠가 다음 실험의 유력한 출발점이다.</p><span class="pill">추출 2026.10.29 00:04 KST</span> <span class="pill">공통 분석기간 10.02–10.25</span></header>'
    html_doc+='<nav>'+''.join(f'<a href="#{id}">{label}</a>' for id,label in [('insights','발견 8가지'),('performance','영상별 성과'),('traffic','유입'),('retention','이탈'),('actions','실행 순서'),('methods','수집·한계')])+'</nav>'
    html_doc+='<div class="cards">'+''.join(f'<div class="card"><span>{label}</span><strong>{val}</strong><small>{desc}</small></div>' for label,val,desc in cards)+'</div>'
    html_doc+='<section id="insights"><h2>지금 데이터가 말해 주는 것</h2><p class="note">최신 예산 본편과 매매·전세·월세편은 Analytics 처리 기간 뒤에 게시됐다. 이번 보고서의 강한 결론은 기존 지역 영상에 관한 것이며 새 주제의 성패 판정은 보류한다.</p>'+text_insights+'</section>'
    html_doc+='<section id="performance"><h2>본편과 쇼츠를 나눠 비교</h2><p class="small">2026.10.02–10.25 API 반환값 · 초기는 게시일 포함 3개 보고일 · 구독 증가는 영상 시청 페이지 발생분</p><h3>본편</h3>'+video_table(long_ids)+'<h3 style="margin-top:30px">쇼츠</h3>'+video_table(short_ids)+'<details><summary>처리 기간 밖의 최신 영상 · 현재 누적 스냅샷</summary>'+current_table+'</details></section>'
    html_doc+='<section id="traffic"><h2>어디에서 들어와 오래 봤나</h2><div class="two">'+traffic_charts+'</div><p class="small">SUBSCRIBER는 탐색 기능 분류 코드다. 이 행을 구독자만의 조회수로 읽지 않는다. 쇼츠 검색 시청시간 379분은 쇼츠 피드 292분보다 컸다. 검색형 쇼츠의 수명이 길 가능성은 후속 관찰할 가설이다.</p><h3 style="margin-top:25px">검색어 상위 10개 · 전체 형식</h3>'+bar_chart([(r['insightTrafficSourceDetail'],r['views']) for r in ext['search_terms']['rows'][:10]],'회')+'</section>'
    html_doc+='<section id="retention"><h2>본편의 시작을 먼저 고칠 근거</h2><p>광교·동탄은 약 19~32초 구간에서 시청 비율이 크게 내려갔다. 다른 세 본편보다 초기 곡선이 낮다. 실제 대사·화면을 대조할 우선 구간이다.</p>'+svg_retention()+'<div class="legend">'+''.join(f'<span><i style="background:{color}"></i>{label}</span>' for label,color in zip(titles.values(),palette))+'</div><p class="small">가로축은 각 영상 길이에 대한 비율이다. 같은 5%라도 실제 초는 다르다. 재시청·점프가 포함된 구간 재생 비율이며 완주자 비율이 아니다.</p></section>'
    html_doc+='<section id="actions"><h2>다음 작업에 반영할 순서</h2>'+''.join(f'<article class="insight"><span class="number">{i+1}</span><div><h3>{a}</h3><p><b>{b}</b></p><p>{c}</p><p class="action">측정: {d}</p></div></article>' for i,(a,b,c,d) in enumerate(actions))+'<p class="note">실험 목표: 한 편에서 해결할 질문을 줄이고, 계산·근거가 화면에서 실제로 변하게 만든다. 유지율과 참여 조회수의 개선 여부는 새 영상 데이터가 처리된 후 평가한다.</p></section>'
    html_doc+='<section id="methods"><h2>수집 범위와 해석 기준</h2><ol>'+''.join('<li>'+esc(s)+'</li>' for s in methods)+'</ol><h3>원본과 재현</h3><p><a href="../../analysis/youtube_channel_review_20261029/raw/extended_analytics.json">확장 API 응답</a> · <a href="../../analysis/youtube_channel_review_20261029/tables/videos_joined.csv">영상 통합 CSV</a> · <a href="../../analysis/youtube_channel_review_20261029/collection_manifest.json">수집 상태</a></p><p class="small">collect.py는 읽기 전용 재수집, build_report.py는 저장된 응답으로 보고서를 재생성한다. 온라인 값은 계속 변하므로 이 보고서는 저장된 추출본 기준이다.</p><h3>공식 정의</h3><p><a href="https://developers.google.com/youtube/analytics/metrics">Analytics 지표 정의</a> · <a href="https://developers.google.com/youtube/analytics/channel_reports">지원 채널 보고서</a> · <a href="https://developers.google.com/youtube/analytics/reference/reports/query">보고서 날짜·쿼리</a> · <a href="https://developers.google.com/youtube/analytics/dimensions">차원·유입 코드 정의</a> · <a href="https://developers.google.com/youtube/data/reference/rest/v3/videos">Data API 영상 통계</a></p></section><footer>데이터로보는부동산 · 소유자 채널 분석 · 2026-10-29 · 외부 라이브러리 없이 열리는 로컬 보고서</footer></main></html>'
    # Korean display units, not Japanese glyphs from internal labels.
    html_doc=html_doc.replace('秒','초')
    (REPORT / '보고서.html').write_text(html_doc,encoding='utf-8')
    md=['# 데이터로보는부동산 채널 분석','', '추출 2026-10-29 00:04 KST · 공통 기간 2026-10-02~10-25','', '**지역 검색형 본편이 시청시간을 만들고, 한 가지 반문에 집중한 쇼츠가 다음 실험의 출발점이다.**','']
    for n,title,fact,action in insights: md += [f'## {n}. {title}','',fact,'','실행: '+action,'']
    md += ['## 수집·해석 기준','']+['- '+s for s in methods]+['','## 파일','', '- 상세 차트·표: [보고서.html](보고서.html)','- 원본·CSV·재현 스크립트: `analysis/youtube_channel_review_20261029/`','','공식 출처: [지표](https://developers.google.com/youtube/analytics/metrics), [채널 보고서](https://developers.google.com/youtube/analytics/channel_reports), [쿼리](https://developers.google.com/youtube/analytics/reference/reports/query), [차원](https://developers.google.com/youtube/analytics/dimensions)']
    (REPORT / '보고서.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
    summary={'status':'report_built','snapshot_at':snapshot['fetched_at_kst'],'analytics_end':'2026-10-25','public_videos':19,'private_videos':2,'period_views':total['views'],'period_watch_minutes':total['estimatedMinutesWatched'],'long_search_watch_share_pct':pct(search_long['estimatedMinutesWatched'],long['estimatedMinutesWatched']),'report_html':str(REPORT/'보고서.html'),'report_md':str(REPORT/'보고서.md'),'report_requires_network':False,'external_private_analytics_transmitted':False}
    (BASE / 'report_manifest.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False))


if __name__=='__main__': main()
