from pathlib import Path
import json,html
R=Path.cwd();E=R/'video-agent-studio/episodes/housing-choice-networth-20261020';O=E/'outputs/review-v2';A=O/'assets';A.mkdir(parents=True,exist_ok=True)
icons={'house':'<path d="M18 54 64 17l46 37M29 49v60h70V49M52 109V73h25v36"/>','receipt':'<path d="M32 15h64v98l-10-7-11 7-11-7-11 7-10-7-11 7ZM46 39h36M46 57h36M46 75h22"/>','key':'<circle cx="43" cy="45" r="24"/><path d="m60 62 44 44m-19-19 12-12m-2 22 12-12"/>','wallet':'<rect x="15" y="34" width="98" height="72" rx="13"/><path d="M22 34V22h72v12M86 61h27v25H86Z"/><circle cx="96" cy="74" r="2"/>','investment':'<path d="M20 106h90M27 95V70h16v25M55 95V50h16v45M83 95V28h16v67M23 49l32-20 18 5 27-22"/>','tools':'<path d="m23 106 55-55M78 51a25 25 0 0 0 29-32L90 36l-16-4-4-16a25 25 0 0 0-1 31l-55 55Z"/>'}
for n,body in icons.items():(A/f'{n}.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><rect width="128" height="128" rx="24" fill="#ecebe4"/><g fill="none" stroke="#286cda" stroke-width="6" stroke-linecap="round" stroke-linejoin="round">'+body+'</g></svg>',encoding='utf8')
notes='''# 비용과 투자수익 설명 보강안 v2

## 600만원의 성격
기존 600만원은 개별 비용을 합산한 금액이 아니라 모형 작성자가 둔 가정값이었다. 실제 거래비용으로 설명하면 안 된다. 기존 100만원 계약비용, 소유자 월30만원·임차인 월5만원 역시 가정 묶음이다.

## 낭독 교체안
집을 살 때는 집값 외의 비용도 들어갑니다. 일반 취득세율이 적용되고 별도 감면을 받지 않는 6억원, 전용면적 85제곱미터 이하 주택을 예로 들겠습니다. 취득세 1%는 600만원, 지방교육세 0.1%는 60만원입니다. 중개보수는 상한 0.4%로 계산하면 240만원이고 실제 금액은 그 안에서 협의합니다. 중개업자의 과세유형에 따라 부가가치세도 달라질 수 있습니다. 10% 부가세를 적용하는 예에서는 24만원이 더해집니다. 이 네 항목만 합하면 924만원입니다. 등기 관련 비용과 국민주택채권 할인비용, 대출 관련 비용은 별도로 확인해야 합니다.

처음의 600만원은 이런 항목을 합친 총거래비용이 아니므로, 최종 계산에서는 비용을 항목별로 확정한 뒤 결과를 다시 계산하겠습니다. 생애최초 등 감면이나 주택 수·면적·취득시점 조건이 달라지면 세금도 달라집니다.

매달 30만원과 5만원도 실제 모든 가구가 내는 고정 비용은 아닙니다. 소유자가 부담하는 세금과 수선, 임차인의 보증료와 계약 관련 비용을 단순화한 가정입니다. 공통 관리비는 같은 생활비로 처리합니다. 실제 계산은 소유자와 임차인이 다르게 부담하는 항목만 나누어 넣겠습니다.

## 비용 검증 목록
- 매매: 취득세·지방교육세·농어촌특별세 적용 여부, 감면, 중개보수·부가세, 등기·채권 할인·대출 인지/설정비. 설정비는 실제 부담주체 구분.
- 전세: 보증료는 보증기관·상품·기간·보증금으로 산정. 중개보수는 거래금액과 해당 시점 조례로 산정. 갱신주기를 10년 내내 비용0으로 둘지 명시.
- 월세: 중개보수 거래금액은 보증금+월세×100(별도 예외구간 존재). 전세와 같은 계약비100만원을 자동 적용하지 않음.
- 월30만원·5만원은 가정으로 표기하고 상하 범위 민감도 비교. 재산세는 매매가의 단순 비율로 단정하지 않음.
- 기존 모형의 청산비 집값1%·금융자산0.5%는 실제 양도세·ETF세금이 아닌 가정값. 기본 계속거주 결과와 구분.

## 수익률 낭독안
국내에서 원화로 거래하는 TIGER 미국S&P500을 기준으로 살펴보겠습니다. 분배금을 다시 투자했다고 가정한 세전 순자산가치 수익률을 사용하며, 이 상품에 이미 반영된 환율 효과를 다시 더하지 않습니다. 2025년 말까지 최근 3년의 누적수익률은 113.94%, 연복리로 약28.85%입니다. 최근5년 누적은157.02%, 연복리는 약20.78%입니다. 과거의 실제 수익률이며 앞으로의 수익률 가정과는 구분합니다.
이 상품은 2020년 상장되어10년과20년 실적이 없습니다. 장기 지수 성과를 사용할 때는 ETF 실제 성과와 다른 자료임을 표시하겠습니다. 집값도2006년부터2025년까지는19년이므로20년으로 부르지 않겠습니다.

## 화면 보강
장식용 이모지는 작은 보조 요소로 사용한다. 핵심 금융 개념은 SVG 아이콘으로 고정해 운영체제별 이모지 모양 차이를 피한다.
- 출발 자금: 집·열쇠·투자계좌 아이콘에 돈이 나뉘어 들어감.
- 거래 비용: 영수증 조각이 취득세·교육세·중개보수·기타비용으로 펼쳐짐. 미확정액은 빈칸으로 유지.
- 매월 흐름: 지갑에서 주거비와 투자로 화살표 분기.
- 원금·보증금: 열쇠/반환 화살표와 부채 잔액 막대.
- 월 유지비: 수선 도구·고지서 아이콘. 본문 차트·자막·출처 영역은 가리지 않음.
- 투자: 작은 그래프 조각으로 가격·분배금·환율을 구분. 상승 화살표를 확정 수익의 상징으로 사용하지 않음.

상태: 대본 삽입안과 시각 소스 준비. 기존 MP4는 변경 전 버전이며 비용 재산정·전체 대본 수치 일괄 갱신·음성 정렬·렌더가 남아 있다.
'''
(O/'cost_and_return_revisions.md').write_text(notes,encoding='utf8')
preview='<!doctype html><meta charset="utf-8"><title>Housing choice v2 검토</title><style>body{max-width:1000px;margin:30px auto;background:#f6f4ef;color:#173348;font-family:Malgun Gothic;line-height:1.8}img{width:100px;margin:20px}pre{white-space:pre-wrap;font:inherit}</style><h1>비용 설명·시각 소스 v2</h1>'+''.join(f'<img src="assets/{n}.svg" title="{n}">' for n in icons)+'<pre>'+html.escape(notes)+'</pre>'
(O/'review.html').write_text(preview,encoding='utf8')
jsondata={'cost_6000000':'unsupported lump-sum assumption; not itemized total','example_tax_6000000':6000000,'example_education_tax':600000,'example_brokerage_cap':2400000,'example_vat_if_10pct':240000,'subtotal_excluding_registration_bonds_loan_costs':9240000,'sources':['https://etax.seoul.go.kr/taxpay/AcqutaxCalcAction.view?gl_gubun=g&gnb_id=0610&lnb_id=0610','https://imap.incheon.go.kr/sgp/por/info/brokerage.do','https://www.tigeretf.com/ko/product/search/detail/index.do?ksdFund=KR7360750004'],'render_status':'assets_and_revision_proposal_only','requires_recalculation':True}
(O/'revision_manifest.json').write_text(json.dumps(jsondata,ensure_ascii=False,indent=2),encoding='utf8');print('created 6 SVG assets, revision script, preview, manifest')
