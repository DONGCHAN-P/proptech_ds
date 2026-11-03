import csv,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
EP=Path(__file__).resolve().parents[1]
source=ROOT/'analysis/housing_growth_2006/full_transactions_v1/quarterly_all_valid_transactions.csv'
rows=list(csv.DictReader(source.open(encoding='utf-8-sig')))
regions=['서울','경기','인천','부산','대구','대전']
selected=[]
for row in rows:
 if row['region'] in regions:
  selected.append({'region':row['region'],'quarter':row['quarter'],'median_manwon':float(row['area84_85_median_deal_amount_manwon']),'n':int(row['area84_85_n'])})
lookup={(r['region'],r['quarter']):r for r in selected}
gap=lambda q:lookup['서울',q]['median_manwon']-lookup['경기',q]['median_manwon']
facts={'source':str(source.relative_to(ROOT)),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'measure':'분기별 전용면적 84㎡ 이상 85㎡ 미만 아파트 유효 거래금액의 중위값, 만원','regions':regions,'period':['2006Q1','2026Q2'],'rows':len(selected),'area84_sample_total':sum(r['n'] for r in selected),'min_region_quarter_n':min(r['n'] for r in selected),'latest_n':sum(lookup[r,'2026Q2']['n'] for r in regions),'gap_seoul_gyeonggi_manwon':{'2006Q1':gap('2006Q1'),'2026Q2':gap('2026Q2')},'endpoints':[lookup[r,q] for q in ['2006Q1','2026Q2'] for r in regions],'interpretation':'지역마다 거래된 단지·연식·입지의 구성이 바뀌는 거래가격 수준 비교. 동일 아파트 보유수익률이나 동일품질 가격지수로 해석하지 않는다. 명목 가격. 캐시 종료 2026-06-30. 대구 군위 제외. 세종은 초기 행정경계/표본 문제로 이번 장기 비교에서 제외.'}
(EP/'research/facts.json').write_text(json.dumps(facts,ensure_ascii=False,indent=2),encoding='utf-8')
(EP/'research/chart_data.json').write_text(json.dumps({'facts':facts,'observations':selected},ensure_ascii=False),encoding='utf-8')
with (EP/'research/chart_data.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(selected[0]));w.writeheader();w.writerows(selected)
packet='''한국 부동산 데이터 채널의 새 쇼츠를 함께 기획하자. 기존 로그인 구독 기반 Claude에게 요청하는 제한된 기획 검토다. 도구를 호출하거나 외부 자료를 임의로 확인하지 말고 아래 공개/집계 자료만으로 비판적으로 논의해줘. 새 유료 API, 이미지/음성 생성, 게시 권한은 없다. 한국어로 2000자 안팎으로 답하되 너무 긴 설명은 피한다.

사용자: 네 쇼츠를 참고해서 비슷한 유형을 만들고, 주제는 적절히 선택해서 Claude와 논의한 뒤 제작. 중간 승인 질문 없이 끝까지 진행.

실제로 추출한 프레임 19장을 내가 확인한 관찰(너는 원영상을 직접 본 것은 아니다):
1 UguOzeTENco, 20초: 검정 바탕 MSFT 10년 적립 시뮬레이션. 고정 제목, 노란 날짜 진행 막대, 선/면 차트가 시간에 따라 전개되고 하단 투자금/평가액이 계속 바뀐다. 종료에 최종 수치 유지.
2 rMKZ1AYdS78, 5초: 도시 야경 배경, 대학 순위 두 열. 첫 프레임부터 전체 표가 완성돼 있고 마지막도 거의 같다. 작은 글씨를 읽으려고 다시 볼 수 있지만 모바일 정보량 과다.
3 Kmfn_lWwfUQ, 26초: 월별 가로막대 순위 경쟁. 색/사진별 개체 정체성은 유지하고 순위와 날짜가 바뀐다. 순위 교차 때 일부 라벨이 겹치는 문제도 보인다.
4 xrPYY7tQvG8, 5초: 부자 순위 15줄+지역 인물, 발사체 사진 배경. 완성 표 유지형. 큰 숫자와 소유 대상을 빠르게 연결한다.
참고물의 원본 프레임·음원·사진은 결과물에 재사용하지 않고 구성만 배운다. 실제 청취는 아직 하지 않았다.

채널의 공개 정보: 창릉/왕숙의 구체적 지역 비교 본편과 신도시 쇼츠가 올라와 있다. 최근 감당 가능한 집값/매매·전세·월세도 제작했다. 비공개 Analytics 데이터는 이 전달문에 포함하지 않는다.

다섯 후보:
A 현금1~5억이면 살 수 있는 집값 순위. 기존 음성 재사용 가능하지만 개인별 대출 조건을 짧게 담기 어렵다.
B 전용84~85㎡ 실거래 중위가격 6지역, 2006Q1~2026Q2 가로막대 타임랩스. 같은 면적대의 지역차를 보여주고 마지막 서울-경기 가격차를 비교.
C 2021고점 대비 회복률 순위. 큰 발견은 쉽지만 기준분기와 지역별 실제 고점이 달라 비교 설명이 늘어난다.
D 2006년부터 실거래 건수 순위. 데이터는 충분하지만 거래량이 가격과 다르다는 연결이 필요하다.
E 대출 월납입금 비교 5초 표. 실용적이지만 고정표만 보여주는 장면으로 끝날 위험.

내 추천 B: 사용자 보유 실거래를 쓰고, 6개 지역만 크게 보여주며, 날짜와 순위가 살아 움직이는 약26~30초 데이터 쇼츠. 내레이션 없이 원본 제작 BGM/효과음과 큰 화면 문구. 화면의 통계 정의·기간·출처는 정확하게 제시하고 '공식지수아님' 같은 부정형 푸터는 쓰지 않는다. 2026Q2 종점은 고정된 캐시 기준이며 최신 현재 시세처럼 말하지 않는다. 같은 면적대라도 거래 구성은 달라질 수 있으므로 설명문에 방법을 충분히 남긴다.

검증된 집계 팩트:
'''+json.dumps(facts,ensure_ascii=False)+'\n\n논의할 것: 1 후보별 비교 후 한 주제 선택/수정 2 제목·훅과 최종 남길 인사이트 3 과장/통계 오해를 막는 구체적 문구 4 28초 내외 시간별 구성과 읽는 시간 5 순위 교차 라벨 겹침·UI 안전영역·끝부분 잘림을 막는 설계. 단순 칭찬 말고 가장 약한 점을 지적하고 보완해줘.'
assert len(packet)<8000
folder=EP/'collaboration';folder.mkdir(exist_ok=True)
(folder/'concept_packet.txt').write_text(packet,encoding='utf-8')
print(json.dumps({'rows':len(selected),'sample_n':facts['area84_sample_total'],'min_n':facts['min_region_quarter_n'],'packet_chars':len(packet),'endpoints':facts['endpoints']},ensure_ascii=False))
