"""승인 전 대본 패킷 생성. 이 파일의 부모 폴더 안에만 쓴다."""
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path

OUT = Path(__file__).resolve().parent
EP = OUT.parent.parent
REV = 'top20-8min-v2'
INPUTS = [
    'brief.json', 'state.json',
    'research/top20-8min-v2/top20.json',
    'research/top20-8min-v2/ranks01_10_facts.json',
    'research/top20-8min-v2/ranks11_20_facts.json',
    'research/top20-8min-v2/supplemental_facts.json',
    'visual/top20-8min-v2/maps/map_assets.json',
    'visual/top20-8min-v2/data_cards/data_card_assets.json',
]

def read(rel):
    return json.loads((EP / rel).read_text(encoding='utf-8-sig'))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

snapshots = {p: {'revision': REV, 'sha256': sha(EP / p)} for p in INPUTS}
top = read(INPUTS[2])
rows = {x['region_id']: x for x in top['regions']}
research = {}
registry = {}

def register(cid, statement, refs, status='verified', kind='reported_fact', **extra):
    registry[cid] = dict(claim_id=cid, statement=statement, status=status,
                         kind=kind, source_refs=refs, **extra)

for rel in INPUTS[3:6]:
    d = read(rel)
    for i, region in enumerate(d['regions']):
        rid = region['region_id']
        if 'count2023' in region:
            research[rid] = region
        facts = list(region.get('facts', []))
        for key in ['count2023', 'count2024', 'comparison']:
            f = region.get(key)
            if isinstance(f, dict) and f.get('claim_id'):
                facts.append(f)
        for f in facts:
            cid = f['claim_id']
            if cid in registry:
                continue
            urls = f.get('source_url', [])
            if isinstance(urls, str):
                urls = [urls]
            urls += [v['url'] for v in f.get('original_source', []) if v.get('url')]
            register(cid, f['statement'], [{
                'file': rel, 'selector': f'regions[region_id={rid}] claim_id={cid}',
                'original_source_ids': f.get('source_ids', [f['source_id']] if f.get('source_id') else []),
                'original_urls': list(dict.fromkeys(urls)),
                'evidence_location': f.get('evidence_location'),
                'reference_date': f.get('reference_date', f.get('reference_dates')),
            }], status=f.get('status', 'unverified'))

for rid, row in rows.items():
    for field, suffix in [('newlywed_couples', 'TOTAL'),
                          ('first_marriage_couples', 'FIRST'),
                          ('remarried_couples', 'REMARRIED')]:
        register(f'T2024-{rid}-{suffix}', f"{row['province']} {row['region']} {field}={row[field]}",
                 [{'file': INPUTS[2], 'selector': f'regions[region_id={rid}].{field}',
                   'original_urls': [row['source_url']], 'reference_date': '2024-11-01'}],
                 status='verified_input_reused', value=row[field], unit='쌍')

register('DEF-2024', '2024-11-01 기준, 혼인신고 후 5년 미경과·혼인 유지·부부 중 1명 이상 국내 거주, 초혼·재혼을 포함한 전체 수, 단위 쌍.',
         [{'file': INPUTS[3], 'selector': 'statistical_contract; regions[].comparison.population_definition'},
          {'file': INPUTS[4], 'selector': 'methods.statistic_definition'},
          {'file': INPUTS[2], 'selector': 'scope; statistic_reference_date; unit'}])
register('SCOPE-53', '2024 통계구역 수도권 53개 구 중 전체 수 상위 20곳의 내림차순이다.',
         [{'file': INPUTS[2], 'selector': 'scope; regions[].rank; regions[].scene_id'}])

def total(rid):
    return rows[rid]['newlywed_couples']

def diff(cid, a, b):
    value = total(a) - total(b)
    register(cid, f'{a}와 {b} 전체 수 차이 {value}쌍.', [], kind='direct_calculation',
             input_claim_ids=[f'T2024-{a}-TOTAL', f'T2024-{b}-TOTAL'],
             formula=f'{total(a)} - {total(b)}', result=value, unit='쌍')

for a, b in [('R19','R20'), ('R18','R19'), ('R17','R18'), ('R16','R17'), ('R15','R16'),
             ('R14','R15'), ('R12','R13'), ('R10','R11'), ('R06','R07'),
             ('R04','R05'), ('R02','R03'), ('R01','R02')]:
    diff(f'DIFF-{a}-{b}', a, b)

comparisons = {}
for rid, rec in research.items():
    raw = rec.get('count2023')
    old = raw.get('value') if isinstance(raw, dict) else raw
    now = total(rid)
    rate = None if old is None else (now - old) / old * 100
    comparisons[rid] = dict(count2023=old, count2024=now,
                           delta_couples=None if old is None else now-old,
                           change_rate_pct=rate,
                           display_rate_pct=None if rate is None else round(rate, 1))
    if old is not None:
        original = f'{rid}-COUNT2023' if int(rid[1:]) <= 10 else f'{rid}-C2023'
        register(f'CALC-{rid}-YOY', f'{old:,}쌍 → {now:,}쌍, {now-old:+,}쌍, {rate:+.1f}%.',
                 [], kind='direct_calculation',
                 input_claim_ids=[original, f'T2024-{rid}-TOTAL'],
                 formula=f'({now}-{old})/{old}*100', result=rate,
                 display_value=round(rate, 1), unit='%')
increased = [k for k,v in comparisons.items() if v['delta_couples'] is not None and v['delta_couples']>0]
decreased = [k for k,v in comparisons.items() if v['delta_couples'] is not None and v['delta_couples']<0]
province_counts = dict(Counter(x['province'] for x in top['regions']))
register('DIRECTION-19', '동일 범위 비교 가능 19곳 중 6곳 증가, 13곳 감소. 원미구 비교값 null.',
         [{'file': INPUTS[4], 'selector': 'regions[region_id=R20].comparison (not_comparable/null)'}],
         kind='direct_calculation', input_claim_ids=[f'CALC-{r}-YOY' for r in comparisons if r!='R20'],
         formula='비교 가능한 19개 지역의 2024 전체-2023 전체 부호를 집계',
         result={'increase': len(increased), 'decrease': len(decreased), 'R20': None})
register('PROVINCE-COUNTS', 'TOP20에 든 구 개수는 서울9·경기6·인천5.',
         [{'file': INPUTS[2], 'selector': 'regions[].province'}], kind='direct_calculation',
         formula='TOP20 행을 province별로 개수 집계', result=province_counts,
         unit='구 개수', denominator_note='가구 수·인구 대비 비중·집중도 계산 아님')
register('COMPOSITION-PAIR', '영통·권선의 전체 수는 59쌍 차이. 초혼은 영통이888쌍 많고 재혼은 권선이830쌍 많다.',
         [], kind='direct_calculation',
         input_claim_ids=['DIFF-R12-R13', 'T2024-R12-FIRST', 'T2024-R13-FIRST',
                          'T2024-R12-REMARRIED', 'T2024-R13-REMARRIED'],
         formula={'first': '7634-6746=888', 'remarried': '1563-733=830'},
         result={'total_difference': 59, 'first_difference': 888, 'remarried_difference': 830},
         note='초혼+재혼 합으로 전체 수를 재구성하지 않고 각 공표 열을 그대로 비교.')
register('STOCK-MECHANISM', '해마다 새 혼인 진입, 혼인5년 경과에 따른 대상 이탈, 이동 등이 시점별 규모 변화에 함께 작용할 수 있다.',
         [{'file': INPUTS[3], 'selector': 'statistical_contract.stock_vs_flow; regions[].comparison.interpretation'},
          {'file': INPUTS[4], 'selector': 'methods.interpretation'}], kind='definition_based_interpretation')

scenes = []

def add(sid, title, message, lines, memo, rid=None, places=None, types=None, cards=None, purpose='explanation'):
    ss = []
    for i, (text, claims, kind) in enumerate(lines, 1):
        ss.append({'sentence_id': f'{sid}-{i:02}', 'text': text, 'claim_ids': claims,
                   'statement_type': kind})
    scenes.append(dict(scene_id=sid, region_id=rid, rank=None if rid is None else rows[rid]['rank'],
                       title=title, message=message, sentences=ss, screen_memo=memo,
                       requested_photo_places=places or [],
                       material_types=types or ['map','data_chart'],
                       visual_purpose=purpose, cards=cards or []))

def F(text, *claims): return text, list(claims), 'fact_or_calculation'
def Q(text, *claims): return text, list(claims), 'viewer_comparison_question'
def E(text, *claims): return text, list(claims), 'editorial_connection'

add('O001', '신혼부부는 어디에 많이 살까', '신혼부부 거주 규모를 질문한다', [
    Q('신혼부부가 많이 사는 수도권 지역, 어디가 떠오르세요?'),
    E('오늘은 수도권 53개 구 가운데 신혼부부가 많이 사는 스무 곳을, 20위부터 거꾸로 만나보겠습니다.', 'SCOPE-53'),
    E('이름만 줄 세우면 놓치는 게 있어요.'),
    E('바로 옆 순위의 차이가 겨우 열 쌍인 곳도 있고, 비슷한 규모인데 부부의 구성이 다른 곳도 있거든요.', 'DIFF-R10-R11','COMPOSITION-PAIR'),
    E('그 차이를 따라가면서, 우리에게 필요한 지역 비교 질문도 함께 찾아보죠.'),
], '수도권 지도에서 질문 제시 → 아직 순위를 밝히지 않은 20개 지역 윤곽. 열 쌍 차이는 숫자 10만 예고하고 지역명은 R10에서 공개.', types=['map','editorial_card'])

add('O002', '숫자의 기준', '2024년 당시 구역·전체 부부 수·단위 쌍을 정한다', [
    F('기준은 2024년 11월 1일, 당시 구역별로 집계한 거주 신혼부부 수입니다.', 'DEF-2024','SCOPE-53'),
    F('혼인신고 후 5년이 지나지 않았고, 혼인관계를 유지하면서 부부 중 적어도 한 명이 국내에 사는 부부가 대상이에요.', 'DEF-2024'),
    F('초혼과 재혼을 포함한 전체 수를 보며, 단위는 쌍입니다.', 'DEF-2024'),
    E('먼저 기준일에 얼마나 많이 살고 있었는지 보고, 중간중간 1년 사이의 변화도 짚어볼게요.', 'DEF-2024'),
], '2024.11.1 / 수도권 53개 구 / 신혼부부 전체 / 단위 쌍을 순차 강조. 혼인 후 5년 미경과는 짧은 가로 구간으로 설명.', types=['editorial_card','map'])

add('S003', '20위 부천시 원미구', '2024년 복원된 원미구부터 출발한다', [
    F('20위는 부천시 원미구, 7,365쌍입니다.', 'T2024-R20-TOTAL','SCOPE-53'),
    F('원미구는 2024년에 다시 설치된 구예요.', 'R20-F02'),
    F('중동신도시와 함께 조성된 부천중앙공원이 있는 지역이기도 하죠.', 'R20-F01'),
    E('오늘 순위의 출발점은 이 7천 쌍대 중반입니다.', 'T2024-R20-TOTAL'),
], 'MAP_R20에 20위와7,365쌍. 부천중앙공원은 확보된 실제 사진이 해당 장소일 때만 연결. 2023 비교 칸은 null 유지·낭독 생략.', rid='R20', places=['부천중앙공원'], types=['map','data_chart','real_photo'],cards=['RANK_GROUP_20_16'])
add('S004', '19위 서울 중랑구', '원미구와 중랑구는 182쌍 차이다', [
    F('서울 중랑구가 7,547쌍으로 19위입니다.', 'T2024-R19-TOTAL','SCOPE-53'),
    F('원미구보다 182쌍 많아요.', 'DIFF-R19-R20'),
    E('경기도 부천에서 서울 중랑으로 자리는 바뀌었지만, 거주 규모는 서로 가깝습니다.', 'DIFF-R19-R20'),
    E('이 정도 차이라면 등수만 기억하기보다, 두 지역을 같은 규모대에 놓고 보는 편이 이해하기 쉽겠죠.', 'DIFF-R19-R20'),
], 'R20·R19 두 지도 고정 비교와 182쌍 연결선. 중랑 실사는 장소 확인된 지역 전경을 짧게 사용하며 시설 효용 자막은 붙이지 않음.', rid='R19', places=['중랑구 내 촬영지 확인된 실제 전경'], types=['map','data_chart','real_photo'],cards=['RANK_GROUP_20_16'])
add('S005', '18위 용인시 기흥구', '수치가 가까워도 비교할 생활권은 달라진다', [
    F('18위는 용인시 기흥구, 7,686쌍이에요.', 'T2024-R18-TOTAL','SCOPE-53'),
    F('중랑구와의 차이는 139쌍입니다.', 'DIFF-R18-R19'),
    E('지금은 수가 가까운 지역들을 차례로 보고 있는 거예요.', 'T2024-R20-TOTAL','T2024-R18-TOTAL'),
    Q('이 목록에서 집을 알아볼 곳을 추린다면, 지역 이름 옆에 두 사람의 출퇴근 목적지를 먼저 적어볼 수 있겠죠.'),
], 'MAP_R18의 기흥구 윤곽과139쌍 차이. 기흥구 실제 전경은 위치를 떠올리는 분위기 자료로 사용. 미검증 통근 경로나 이동시간을 그리지 않음.', rid='R18', places=['기흥구 내 촬영지 확인된 실제 전경'], types=['map','data_chart','real_photo'],cards=['RANK_GROUP_20_16'])
add('S006', '17위 인천 연수구', '인천 연수구가 7천 쌍대 후반에 등장한다', [
    F('다음은 인천 연수구입니다.', 'SCOPE-53'),
    F('7,875쌍으로 17위예요.', 'T2024-R17-TOTAL','SCOPE-53'),
    F('기흥구보다 189쌍 더 많은데, 잠시 뒤 두 지역의 전년 변화도 나란히 볼게요.', 'DIFF-R17-R18'),
    E('같은 7천 쌍대 안에서도 부천, 서울, 용인, 인천이 차례로 등장하네요.', 'T2024-R20-TOTAL','T2024-R19-TOTAL','T2024-R18-TOTAL','T2024-R17-TOTAL'),
], 'MAP_R17·R18과189쌍 차이. 송도 센트럴파크 등 장소 확인된 연수구 실사는 분위기 컷으로만 연결. 20~17위의 시도색을 순차 표시.', rid='R17', places=['연수구 내 촬영지 확인된 실제 전경'], types=['map','data_chart','real_photo'],cards=['RANK_GROUP_20_16'])
add('S007', '16위 인천 남동구', '8천 쌍 직전인 남동구까지 첫 묶음을 닫는다', [
    F('16위 남동구는 7,997쌍, 8천 쌍 바로 아래입니다.', 'T2024-R16-TOTAL','SCOPE-53'),
    F('앞선 연수구보다 122쌍 많습니다.', 'DIFF-R16-R17'),
    F('남동구는 2023년 8,595쌍에서 598쌍 줄어, 감소율은 7.0퍼센트였어요.', 'CALC-R16-YOY'),
    E('여기까지 다섯 곳을 봤는데, 이번에는 순서에서 잠깐 벗어나 변화도 보겠습니다.'),
], 'MAP_R16·122쌍 차이 → 남동8,595→7,997 변화. 소래습지생태공원 등 확인된 실제 전경은 짧은 분위기 컷으로만 사용. 뒤이어 첫5개 막대를 모두 보여줌.', rid='R16', places=['남동구 내 촬영지 확인된 실제 전경'], types=['map','data_chart','real_photo'],cards=['RANK_GROUP_20_16'])
add('I001', '같은 출발점, 다른 변화', '규모와 전년 변화는 구분해서 읽는다', [
    F('방금 본 기흥구와 연수구는 2023년에 똑같이 7,797쌍이었어요.', 'R18-C2023','R17-C2023'),
    F('1년 뒤에는 기흥구가 111쌍 줄고, 연수구는 78쌍 늘었습니다.', 'CALC-R18-YOY','CALC-R17-YOY'),
    E('출발점이 같아도 다음 해의 방향은 달라질 수 있는 거죠.', 'CALC-R18-YOY','CALC-R17-YOY'),
    F('이번 스무 곳 가운데 같은 범위로 비교할 수 있는 열아홉 곳을 세면, 여섯 곳이 늘고 열세 곳이 줄었어요.', 'DIRECTION-19'),
    F('해마다 새로 혼인한 부부가 들어오고, 혼인 5년이 지난 부부는 집계 대상에서 빠지는 변화도 함께 생깁니다.', 'STOCK-MECHANISM'),
    E('그래서 현재 규모와 1년간의 변화는 따로 놓고 읽어야 해요.', 'DIRECTION-19','STOCK-MECHANISM'),
], '새 비교 도표 제안: 동일한7,797에서 기흥7,686·연수7,875로 갈라지는 두 선. 뒤이어 증가6·감소13을 지역개수로 표시. 원미의2023 칸은 빈값으로 보존.', types=['data_chart'])

add('S008', '15위 서울 구로구', '남동구와 19쌍 차이로 8천 쌍을 넘는다', [
    F('15위는 서울 구로구, 8,016쌍입니다.', 'T2024-R15-TOTAL','SCOPE-53'),
    F('남동구와는 겨우 19쌍 차이로, 여기서 8천 쌍을 넘어요.', 'DIFF-R15-R16','T2024-R15-TOTAL'),
    F('구로동과 금천구 가산동에 걸친 산업지역이 G밸리죠.', 'R15-F01'),
    Q('직장 주변을 관심 있게 본다면, 구 이름에 더해 실제 근무지와 주거지를 함께 놓고 비교해보세요.'),
], 'MAP_R15·R16과19쌍 차이 강조. G밸리 자료는 구로·가산에 걸친 범위를 명시한 원자료만 사용. 신도림 사진에 G밸리 자막 부착 금지.', rid='R15', places=['구로구 구로동 G밸리 구간'], types=['map','data_chart','real_photo'],cards=['RANK_GROUP_15_11'])
add('S009', '14위 서울 은평구', '숫자에서 실제 동네 질문으로 연결한다', [
    F('14위 은평구에는 8,267쌍이 살고 있습니다.', 'T2024-R14-TOTAL','SCOPE-53'),
    F('구로구보다 251쌍 많아요.', 'DIFF-R14-R15'),
    F('은평한옥마을은 이 구의 진관동에 있습니다.', 'R14-F02'),
    Q('관심 지역이 생겼다면, 지역 전체 이름에서 한 걸음 더 들어가 어느 동네를 볼지도 정해보면 좋겠죠.'),
], 'MAP_R14와 은평한옥마을 실사. 관광지 사진은 장소 설명·분위기에 한정하고 일반 주거 대표 사진으로 취급하지 않음.', rid='R14', places=['은평한옥마을'], types=['map','data_chart','real_photo'],cards=['RANK_GROUP_15_11'])
add('S010', '13위 수원시 권선구', '권선·영통을 나란히 비교할 기준을 만든다', [
    F('13위는 수원시 권선구, 8,329쌍입니다.', 'T2024-R13-TOTAL','SCOPE-53'),
    E('다음 지역도 같은 수원이라 두 곳을 나란히 보겠습니다.', 'SCOPE-53'),
    F('권선구는 2023년 8,792쌍에서 463쌍 줄어, 감소율은 5.3퍼센트였습니다.', 'CALC-R13-YOY'),
    E('현재의 크기와 그사이 달라진 정도를 같이 적어두면 비교할 때 도움이 되겠죠.', 'CALC-R13-YOY'),
], 'MAP_R13의 권선 윤곽과8,792→8,329. 다음 영통 장면까지 같은 막대축을 유지하고 실제 전경은 위치 소개의 분위기 자료로 한정.', rid='R13', places=['권선구 내 촬영지 확인된 실제 전경'], types=['map','data_chart','real_photo'],cards=['RANK_GROUP_15_11'])
add('S011', '12위 수원시 영통구', '권선·영통 전체 수는 59쌍 차이다', [
    F('12위는 수원시 영통구, 8,388쌍이에요.', 'T2024-R12-TOTAL','SCOPE-53'),
    F('바로 앞 권선구와는 59쌍 차이입니다.', 'DIFF-R12-R13'),
    E('같은 도시 안에서 신혼부부 전체 수가 아주 가까운 두 구를 만난 셈이죠.', 'DIFF-R12-R13'),
    E('잠시 뒤에 이 숫자 안에 담긴 부부의 구성도 나눠볼게요.', 'COMPOSITION-PAIR'),
], 'MAP_R12·R13을 나란히 고정하고8,329→8,388 차이59만 강조. 시설 사진 낭독을 추가하지 않고 비교 화면을 충분히 유지.', rid='R12', places=['영통구 내 촬영지 확인된 주거 전경'], types=['map','data_chart','real_photo'],cards=['RANK_GROUP_15_11'])
add('S012', '11위 서울 노원구', '상위10위 경계의 작은 차이를 예고한다', [
    F('11위는 서울 노원구로, 8,473쌍입니다.', 'T2024-R11-TOTAL','SCOPE-53'),
    F('화랑대 철도공원 안에는 전시실과 야외무대를 갖춘 경춘선숲길 갤러리가 있어요.', 'R11-F01'),
    E('이제 상위 열 곳을 앞두고 있습니다.'),
    E('등수로는 경계가 딱 나뉘지만, 다음 지역과의 숫자 차이를 눈여겨봐 주세요.', 'DIFF-R10-R11'),
], 'MAP_R11 → 경춘선숲길 갤러리 실사. 순위 카드11위 막대 끝에10위 자리만 예고. 이탈리아 모형 건축물을 실제 노원 전경으로 사용 금지.', rid='R11', places=['화랑대 철도공원 내 경춘선숲길 갤러리'], types=['map','data_chart','real_photo'],cards=['RANK_GROUP_15_11'])
add('I002', '비슷한 전체, 다른 구성', '영통·권선의 초혼과 재혼 수를 각각 비교한다', [
    E('그전에, 방금 본 수원의 두 구를 한 번 더 보죠.'),
    F('전체 수 차이는 59쌍이었는데, 초혼 부부는 영통구 7,634쌍, 권선구 6,746쌍입니다.', 'DIFF-R12-R13','T2024-R12-FIRST','T2024-R13-FIRST'),
    F('초혼만 놓으면 영통구가 888쌍 더 많아요.', 'COMPOSITION-PAIR'),
    F('재혼 부부는 영통구 733쌍, 권선구 1,563쌍으로 방향이 바뀝니다.', 'T2024-R12-REMARRIED','T2024-R13-REMARRIED'),
    F('이번에는 권선구가 830쌍 더 많습니다.', 'COMPOSITION-PAIR'),
    E('전체 규모가 비슷해도 통계에 담긴 부부의 구성은 이렇게 달라집니다.', 'COMPOSITION-PAIR'),
    E('지역을 이해할 때 전체 수와 그 안의 구성을 함께 살펴볼 이유예요.', 'COMPOSITION-PAIR'),
], 'NEWLYWED_COMPOSITION의 원값 검토 후 영통·권선 행만 확대. 전체/초혼/재혼은 독립 막대3쌍으로 제시하고 초혼+재혼 누적합을 전체와 같게 맞추지 않음.', types=['data_chart'],cards=['NEWLYWED_COMPOSITION'])

add('S013', '10위 인천 미추홀구', '노원과 열 쌍 차이로10위에 들어온다', [
    F('10위는 인천 미추홀구, 8,483쌍입니다.', 'T2024-R10-TOTAL','SCOPE-53'),
    F('11위 노원구와 불과 열 쌍 차이예요.', 'DIFF-R10-R11'),
    E('순위 한 칸이 실제 규모에서는 이만큼 가까울 수도 있습니다.', 'DIFF-R10-R11'),
    F('그런데 전년보다 노원구는 3.8퍼센트 줄었고, 미추홀구는 5.2퍼센트 늘었어요.', 'CALC-R11-YOY','CALC-R10-YOY'),
    E('현재 수가 거의 같아도, 1년 사이에 움직인 방향은 서로 달랐습니다.', 'CALC-R11-YOY','CALC-R10-YOY'),
], 'MAP_R10·R11 두 막대를 동일축으로 놓고8,483-8,473=10 표시 → 노원-3.8%·미추홀+5.2%를 독립 변화 도표로 비교. 지역 전경에 인과 자막을 붙이지 않음.', rid='R10', places=['미추홀구 내 촬영지 확인된 실제 전경'], types=['map','data_chart','real_photo'],cards=['RANK_GROUP_10_6'])
add('S014', '9위 성남시 분당구', '분당 내 확인된 창업지원시설을 사례로 쓴다', [
    F('9위는 성남시 분당구, 8,587쌍입니다.', 'T2024-R09-TOTAL','SCOPE-53'),
    F('분당구 삼평동에는 창업지원시설인 판교 스타트업 캠퍼스가 있어요.', 'R09-F02'),
    E('앞서 구로에서는 산업지역을, 여기서는 창업지원시설을 짚어봤습니다.', 'R15-F01','R09-F02'),
    Q('업무 환경이 관심 요소라면, 내 근무지가 정확히 어디인지와 살 집까지의 동선을 추가로 비교해보세요.'),
], 'MAP_R09와 스타트업 캠퍼스의 공식 위치 원문. 삼평동 해당 시설 사진만 요청. 판교제2테크노밸리 전경으로 시설 소재지 설명 대체 금지.', rid='R09', places=['판교 스타트업 캠퍼스, 분당구 판교로289번길20'], types=['map','data_chart','real_photo'],cards=['RANK_GROUP_10_6'])
add('S015', '8위 서울 영등포구', '9천 쌍대로 올라간다', [
    F('8위 서울 영등포구부터는 9천 쌍대입니다.', 'T2024-R08-TOTAL','SCOPE-53'),
    F('전체 수는 9,036쌍이에요.', 'T2024-R08-TOTAL'),
    F('2023년 9,014쌍과 비교하면 22쌍 늘어, 변화율은 0.2퍼센트입니다.', 'CALC-R08-YOY'),
    E('이번에는 전년과 거의 비슷한 규모를 유지한 지역을 만났네요.', 'CALC-R08-YOY'),
], 'MAP_R08과9천 기준선 →9,014·9,036 두 막대. 영등포 실제 전경은 분위기 컷으로만 사용. 금융 일자리 수·출퇴근시간은 화면에도 추가하지 않음.', rid='R08', places=['영등포구 내 촬영지 확인된 실제 전경'], types=['map','data_chart','real_photo'],cards=['RANK_GROUP_10_6'])
add('S016', '7위 서울 강동구', '가까운 순위에서 보이는 생활환경 사례', [
    F('7위 강동구는 9,287쌍입니다.', 'T2024-R07-TOTAL','SCOPE-53'),
    F('둔촌동 일자산 자연공원에는 잔디광장과 놀이터, 운동시설이 있어요.', 'R07-F01'),
    E('앞선 영등포의 숫자에 이어, 이곳의 실제 생활 공간도 잠깐 떠올려볼 수 있겠죠.'),
    E('그리고 바로 다음 6위와는 숫자 차이가 다시 작아집니다.', 'DIFF-R06-R07'),
], 'MAP_R07 → 일자산 자연공원 해당 시설 실사. 반복 줌 없이 구 지도 고정. 다음 강남과34쌍 차이를 담을 비교 영역 확보.', rid='R07', places=['둔촌동 일자산 자연공원'], types=['map','data_chart','real_photo'],cards=['RANK_GROUP_10_6'])
add('S017', '6위 서울 강남구', '강동과34쌍 차이지만 전년 변화도 함께 본다', [
    F('6위는 강남구, 9,321쌍입니다.', 'T2024-R06-TOTAL','SCOPE-53'),
    F('강동구보다 34쌍 많아요.', 'DIFF-R06-R07'),
    F('그런데 전년을 보면 8,523쌍에서 798쌍 늘었고, 증가율은 9.4퍼센트입니다.', 'CALC-R06-YOY'),
    E('2024년의 순위 옆에 1년간의 변화를 붙이면, 같은 지역도 다른 면이 보이는 거죠.', 'CALC-R06-YOY'),
], 'MAP_R06·R07의34쌍 차이 → 강남8,523→9,321 독립 변화 막대. 증가율9.4%는 직접 계산값으로 출처 기록. 공원 연혁 낭독 생략.', rid='R06', places=['강남구 내 촬영지 확인된 실제 전경'], types=['map','data_chart','real_photo'],cards=['RANK_GROUP_10_6'])
add('I003', '세 시도의 서로 다른 지역들', 'TOP20에 든 구는 서울9·경기6·인천5곳이다', [
    E('상위 다섯 곳으로 가기 전에, 스무 곳의 지도를 한 번 펼쳐볼까요?'),
    F('이번 TOP20에 든 구의 개수는 서울 아홉 곳, 경기 여섯 곳, 인천 다섯 곳입니다.', 'PROVINCE-COUNTS'),
    E('세 시도의 여러 지역이 같은 목록에 들어와 있어요.', 'PROVINCE-COUNTS'),
    Q('그럼 우리 부부는 이 중 어디를 더 자세히 비교해볼까요?'),
    Q('두 사람의 직장 위치, 예산, 필요한 집 크기를 함께 놓으면 조사할 질문을 좁혀갈 수 있습니다.'),
    E('이제 1만 쌍을 넘는 상위 다섯 곳으로 가보죠.', 'SCOPE-53','T2024-R05-TOTAL'),
], 'TOP20_PROVINCE_COUNTS와20개 구 경계 지도 병렬.9·6·5는 구 개수만 표시하며 인구·가구 비중처럼 원형 점유율로 표시하지 않음.', types=['map','data_chart'],cards=['TOP20_PROVINCE_COUNTS'])

add('S018', '5위 인천 부평구', '1만 쌍을 넘으며 규모와 증가를 함께 소개한다', [
    F('5위 인천 부평구는 1만 204쌍입니다.', 'T2024-R05-TOTAL','SCOPE-53'),
    F('2023년 9,901쌍에서 303쌍 늘어, 증가율은 3.1퍼센트예요.', 'CALC-R05-YOY'),
    F('부평문화의거리는 지하상가와 전통시장 등 주변 상권이 연결되는 보행 중심 공간입니다.', 'R05-F02'),
    Q('관심이 있다면 집에서 장보는 곳까지 어떤 동선을 비교할지 질문을 더해보세요.'),
], 'MAP_R05에1만 기준선과303쌍 증가. 부평문화의거리 실사는 정확한 장소 캡션과 함께 사용하고 공원 사진으로 상권 설명 대체 금지.', rid='R05', places=['부평문화의거리'], types=['map','data_chart','real_photo'],cards=['RANK_GROUP_5_1'])
add('S019', '4위 서울 강서구', '부평보다520쌍 많은 서울 강서구', [
    F('4위는 서울 강서구, 1만 724쌍입니다.', 'T2024-R04-TOTAL','SCOPE-53'),
    F('부평구보다 520쌍 많아요.', 'DIFF-R04-R05'),
    F('강서구 마곡동로의 서울식물원에는 열대와 지중해 기후를 주제로 한 온실 전시가 있습니다.', 'R04-F01'),
    E('지역을 떠올릴 구체적인 장소를 지도 위에 하나씩 놓고 있는 셈이죠.'),
], 'MAP_R04에서 서울 강서구 확인 후 서울식물원 온실 사진. 부산 강서와 혼동 금지. 현재 지도에 시설 핀을 추가하려면 실제 좌표 확인 필요.', rid='R04', places=['서울식물원 온실'], types=['map','data_chart','real_photo'],cards=['RANK_GROUP_5_1'])
add('S020', '3위 고양시 덕양구', '1만1천 쌍대로 올라가며 실제 상업시설을 짚는다', [
    F('3위는 고양시 덕양구, 1만 1,452쌍이에요.', 'T2024-R03-TOTAL','SCOPE-53'),
    F('스타필드 고양도 덕양구에 있으며, 공식 주소는 고양대로 1955입니다.', 'R03-F03'),
    Q('이런 상업시설이 관심 요소라면, 실제 거주 후보지에서 어떻게 오갈지를 추가로 비교해볼 수 있겠죠.'),
    E('이제 남은 두 지역과 얼마나 차이가 나는지 보겠습니다.'),
], 'MAP_R03 → 스타필드 고양 공식 주소 행·해당 점포 실사. 기존qualified 공원2개는 미채택. 사진 권리·촬영지 확인은 visual 인계.', rid='R03', places=['스타필드 고양, 덕양구 고양대로1955'], types=['map','data_chart','real_photo'],cards=['RANK_GROUP_5_1'])
add('S021', '2위 서울 송파구', '덕양과300쌍 차이로2위다', [
    F('2위는 서울 송파구, 1만 1,752쌍입니다.', 'T2024-R02-TOTAL','SCOPE-53'),
    F('3위 덕양구보다 정확히 300쌍 많아요.', 'DIFF-R02-R03'),
    F('송파의 석촌호수는 동호와 서호, 산책로가 있는 도심 호수공원입니다.', 'R02-F01'),
    E('두 지역의 전체 수는 가까운데, 다음 1위와는 간격이 더 벌어집니다.', 'DIFF-R02-R03','DIFF-R01-R02'),
], 'MAP_R02·R03과300쌍 차이. 석촌호수 실제 사진 뒤 동일 막대축을 유지해1위 간격을 예고.', rid='R02', places=['석촌호수'], types=['map','data_chart','real_photo'],cards=['RANK_GROUP_5_1'])
add('S022', '1위 인천 옛 서구', '1위의 큰 규모와 감소를 동시에 읽는다', [
    F('1위는 2024년 당시 인천 서구, 1만 5,737쌍입니다.', 'T2024-R01-TOTAL','SCOPE-53'),
    F('송파구보다 3,985쌍 많습니다.', 'DIFF-R01-R02'),
    F('이때의 서구는 현재 서해구와 검단구를 합친 범위예요.', 'R01-ADM'),
    F('청라호수공원도 이 구역 안의 실제 생활 여가 공간 중 하나입니다.', 'R01-F01','R01-ADM'),
    F('다만 1년 전 1만 5,941쌍과 비교하면 204쌍, 1.3퍼센트 줄었어요.', 'CALC-R01-YOY'),
    E('가장 큰 거주 규모와, 전년보다 줄었다는 변화가 한 지역에 함께 나타납니다.', 'T2024-R01-TOTAL','SCOPE-53','CALC-R01-YOY'),
], 'MAP_R01의2024 옛 서구 경계를 기본으로 유지. 현재 서해+검단은 명칭 연결만 제안하고 새 경계 폴리곤을 임의 작성하지 않음.1위 막대 뒤15,941→15,737 독립 비교.', rid='R01', places=['청라호수공원'], types=['map','data_chart','real_photo'],cards=['RANK_GROUP_5_1'])
add('C001', '순위에서 비교 질문으로', '규모·변화·구성을 지역 비교의 출발점으로 삼는다', [
    E('오늘 순위를 읽는 데 필요한 세 가지가 모였네요.'),
    F('강남구는 9.4퍼센트 늘었고, 규모 1위인 옛 서구는 1.3퍼센트 줄었습니다.', 'CALC-R06-YOY','CALC-R01-YOY','SCOPE-53'),
    E('얼마나 많이 사는지와 얼마나 늘었는지는 따로 봐야 해요.', 'CALC-R06-YOY','CALC-R01-YOY'),
    E('수원의 두 구처럼 전체가 가까워도 부부의 구성은 다를 수 있었죠.', 'COMPOSITION-PAIR'),
    Q('눈에 들어온 지역이 있다면, 두 사람의 직장과 예산, 필요한 집 크기를 옆에 적어보세요.'),
    E('그 지역에서 무엇을 더 알아봐야 할지, 이제 질문이 좀 더 구체적으로 보일 겁니다.'),
], '강남+9.4%·옛 서구-1.3%를 나란히 보이고 영통·권선 구성 비교를 짧게 회수. 마지막은 실제 수도권 지도에 비교 질문3개만 남김.', types=['data_chart','map'])
add('E001', '마지막 발화 뒤 여백', '마지막 발화 이후3초를 남긴다', [],
    'C001의 마지막 지도 화면 유지3초. 신규 CTA 발화 없음. 실제 음성 정렬 뒤 마지막 발화+3초로 재산정.', types=['map'], purpose='breathing_room')

def join_text(scene):
    return '\n'.join(x['text'] for x in scene['sentences'])

spoken = '\n\n'.join(join_text(x) for x in scenes if x['sentences'])
char_with_spaces = len(re.sub(r'\s+', ' ', spoken).strip())
char_without_spaces = len(re.sub(r'\s+', '', spoken))

# 음성 미확정.477초를 문장량에 비례해 배분하고 마지막 무발화3초를 둔다.
active = [s for s in scenes if s['sentences']]
weights = [len(re.sub(r'\s+', ' ', join_text(s)).strip()) for s in active]
raw_seconds = [477*n/sum(weights) for n in weights]
seconds = [int(n) for n in raw_seconds]
for i in sorted(range(len(seconds)), key=lambda i: raw_seconds[i]-seconds[i], reverse=True)[:477-sum(seconds)]:
    seconds[i] += 1
tick = 0
for s, duration in zip(active, seconds):
    s['start_s'] = tick
    s['end_s'] = tick + duration
    s['duration_s'] = duration
    tick += duration
scenes[-1].update(start_s=477, end_s=480, duration_s=3)

maps = read(INPUTS[6])
cards = read(INPUTS[7])
asset_registry = {a['asset_id']: a for a in maps['assets']+cards['assets']}
sentence_map = []
for s in scenes:
    s['narration_text'] = join_text(s)
    s['claim_ids'] = list(dict.fromkeys(c for line in s['sentences'] for c in line['claim_ids']))
    s['asset_ids'] = ([f"MAP_{s['region_id']}"] if s['region_id'] else []) + s['cards']
    s['script_revision'] = REV
    s['audio_revision'] = None
    s['timing_basis'] = 'estimate_text_length_allocation_not_audio_aligned'
    s['timing_status'] = 'provisional_audio_unconfirmed'
    s['status'] = 'proposed_pending_user_script_approval'
    s['asset_status'] = 'map_and_cards_manifest_read_photo_selection_pending'
    s['map_requirements'] = {
        'region_ids': [s['region_id']] if s['region_id'] else [],
        'boundary_reference': '2024년 통계구역',
        'precise_pins': '공식 주소만으로 정밀 핀 생성 금지; 좌표 확인 후 visual이 제안',
    }
    s['photo_requirements'] = [dict(request_id=f"PHOTO_REQ_{s['scene_id']}_{i+1}",
        place_name=p, asset_id=None, status='visual_owner_selection_pending',
        purpose='설명: 문장에 나온 실제 장소·기능 확인' if not ('전경' in p) else '분위기: 해당 구의 실제 전경',
        constraints='장소·촬영시점·권리·픽셀 확인 후 채택; 정밀 동선·선택 이유·구 전체 대표성의 근거로 확대하지 않음')
        for i,p in enumerate(s['requested_photo_places'])]
    for line in s['sentences']:
        sentence_map.append(dict(**line, scene_id=s['scene_id'], region_id=s['region_id'],
            raw_source_claim_ids=line['claim_ids'], map_requirement=s['map_requirements'],
            photo_requirements=s['photo_requirements'] if any('-F' in c for c in line['claim_ids']) else [],
            visual_anchor=line['text'], visual_action=s['screen_memo'],
            asset_ids=s['asset_ids'], material_types=s['material_types'],
            evidence_scope='제공된 조사 산출물의 verified 사실·지정2024입력·직접계산. 원문 재열람/사진 픽셀 검토는 이 writer 작업에서 미수행.'))

dictionary = {
    'TOP20': '톱 트웬티(제목 표시), 낭독에서는 스무 곳',
    '2024년 11월 1일': '이천이십사 년 십일 월 일 일',
    '2023년': '이천이십삼 년',
    '53개 구': '쉰세 개 구',
    '1만 204쌍': '일만 이백사 쌍',
    '1만 724쌍': '일만 칠백이십사 쌍',
    '1만 1,452쌍': '일만 천사백오십이 쌍',
    '1만 1,752쌍': '일만 천칠백오십이 쌍',
    '1만 5,737쌍': '일만 오천칠백삼십칠 쌍',
    '1만 5,941쌍': '일만 오천구백사십일 쌍',
    '9.4퍼센트': '구 점 사 퍼센트',
    '1.3퍼센트': '일 점 삼 퍼센트',
    '3.1퍼센트': '삼 점 일 퍼센트',
    '7.0퍼센트': '칠 점 영 퍼센트',
    '5.3퍼센트': '오 점 삼 퍼센트',
    '3.8퍼센트': '삼 점 팔 퍼센트',
    '5.2퍼센트': '오 점 이 퍼센트',
    '0.2퍼센트': '영 점 이 퍼센트',
    '고양대로 1955': '고양대로 천구백오십오',
    'G밸리': '지 밸리',
    '원미구': '원미구', '미추홀구': '미추홀구',
    '서해구': '서해구', '검단구': '검단구',
    '서수원칠보체육관': '서수원 / 칠보 / 체육관(기관명은 한 덩어리로 표시)',
}
emphasis = ['전체 수', '단위는 쌍', '당시 구역', '열 쌍 차이', '59쌍',
            '초혼', '재혼', '여섯 곳', '열세 곳', '9.4퍼센트', '1.3퍼센트',
            '현재 서해구와 검단구를 합친 범위']

proposal = {
    'schema_version':'1.0', 'episode_id':EP.name, 'revision':REV,
    'owner':'writer', 'title':'신혼부부가 많이 사는 수도권 TOP20',
    'status':'review_draft_pending_new_user_script_approval',
    'input_versions':snapshots, 'target_duration_s':480, 'total_estimated_duration_s':480,
    'timing_basis':'estimate_text_length_allocation_not_audio_aligned',
    'audio_confirmed':False, 'audio_revision':None, 'timing_locked':False,
    'duration_is_actual':False,
    'duration_method':'낭독문 문자량에 비례해477초 배분, 마지막 무발화3초. 실제 호흡·숫자 읽기·오디오 길이 미측정.',
    'scene_id_policy':'R20~R01의 입력 scene_id=S003~S022 유지; 서두O001/O002, 인사이트I001~I003, 맺음C001, 여백E001 별도제안.',
    'shared_scenes_action':'총괄 병합 제안만; 현 공통 scenes.json의 planning-v1을 직접 수정하지 않음.',
    'pronunciation_dictionary':dictionary, 'emphasis_words':emphasis,
    'scenes':scenes,
}

used = set(c for s in scenes for c in s['claim_ids'])
def expand_claim(cid):
    obj = registry[cid]
    for dep in obj.get('input_claim_ids',[]):
        if dep not in used:
            used.add(dep)
            expand_claim(dep)
for cid in list(used): expand_claim(cid)
def resolve_sources(cid, trail=None):
    trail = set() if trail is None else trail
    assert cid not in trail, f'순환 claim 의존성: {cid}'
    obj = registry[cid]
    sources = [{'raw_claim_id':cid, **ref} for ref in obj['source_refs']]
    for dep in obj.get('input_claim_ids', []):
        sources.extend(resolve_sources(dep, trail | {cid}))
    unique = {json.dumps(v, ensure_ascii=False, sort_keys=True):v for v in sources}
    return list(unique.values())
for line in sentence_map:
    evidence = [ref for cid in line['claim_ids'] for ref in resolve_sources(cid)]
    line['source_evidence'] = list({json.dumps(v,ensure_ascii=False,sort_keys=True):v for v in evidence}.values())
    line['resolved_raw_source_claim_ids'] = list(dict.fromkeys(x['raw_claim_id'] for x in evidence))
claim_map = {
    'episode_id':EP.name, 'revision':REV, 'status':'pending_user_script_approval',
    'input_versions':snapshots,
    'verification_boundary':'원자료 웹/PDF 원문 재검수 아님. 기존 독립QA 2024값 재사용, 조사팩의verified 자료·2023전사값 사용.19지역 변화는 writer 재계산.',
    'claims':[registry[c] for c in sorted(used)], 'sentences':sentence_map,
    'comparisons_2023_2024':comparisons,
    'derived_summary':{'increase_region_ids':increased,'decrease_region_ids':decreased,
                       'unavailable_region_ids':['R20'], 'province_region_counts':province_counts},
    'qualified_excluded_claim_ids':[c for c,r in registry.items() if r['status']=='qualified'],
    'supplemental_facts_used':['R03-F03','R09-F02'],
    'unused_price_context':{'read_for_script':False,'used':False,'reason':'이번 편은 순위·규모·변화·구성 중심.2026.4~9 실거래 분포 낭독 생략.'},
    'media_review':{'photos_pixels_inspected_by_writer':False,'map_pixels_inspected_by_writer':False,
                    'manifest_read_only':True,'photo_owner':'visual','actual_photo_asset_id_bound':False},
}

def stamp(n): return f'{n//60:02}:{n%60:02}'
md = ['# 신혼부부가 많이 사는 수도권 TOP20', '',
      '> 새 대본 사용자 승인 대기 · top20-8min-v2 검토 초안',
      '> 목표 8분. 아래 시간표는 합계480초의 estimate이며 실제 오디오 기반으로 확정하지 않았습니다.',
      f'> 낭독문 {char_with_spaces:,}자(공백 포함·줄바꿈을 한 칸으로 정규화), {char_without_spaces:,}자(공백 제외). 제목·장면명·화면 메모 제외.', '',
      '## 낭독', '']
for s in scenes:
    if s['sentences']:
        label = f" / {s['region_id']}" if s['region_id'] else ''
        md += [f"### {s['scene_id']}{label} · {s['title']}", '', s['narration_text'], '']
md += ['## 화면 메모 — 낭독하지 않음', '',
       '지도·데이터카드의 manifest를 읽었으며 픽셀·실사 파일·이용권을 이 작업에서 재검수하지 않았습니다. 사진은 visual의 최종 선택과 장소·권리 확인 후 연결합니다.', '',
       '| 장면 | 잠정 구간 | 핵심 메시지·화면 |', '|---|---|---|']
for s in scenes:
    md.append(f"| {s['scene_id']} | {stamp(s['start_s'])}–{stamp(s['end_s'])} estimate | {s['message']} — {s['screen_memo']} |")
md += ['', '## narration 인계 — 낭독하지 않음', '',
       '음성 선택·생성은 미실행입니다. 새 대본 승인 후 낭독 사전을 적용하고 실제 음성 길이로 타임록을 다시 제안합니다.', '',
       '| 표기 | 읽기 |', '|---|---|']
md += [f'| {k} | {v} |' for k,v in dictionary.items()]
md += ['', '강조어: ' + ' / '.join(emphasis), '',
       '숫자는 단위와 함께 끊습니다. 20→1 순위를 건너뛰지 않으며, 퍼센트 앞의 증가·감소 방향을 보호합니다. 지명은 검증된 표기를 유지합니다.', '',
       '## 검토 범위 — 낭독하지 않음', '',
       '- 대본 검토용 산출물이며 사용자 새 대본 승인은 아직 없습니다.',
       '- 실제 오디오 생성·청취·연속 재생·렌더·유료 생성·외부 Claude 전송·업로드는 수행하지 않았습니다.',
       '- 2024 전체 값은 지정 검수 입력을 재사용했습니다. 2023 값은 조사팀의 원문 텍스트 전사에 근거하며 원표 페이지 화상 대조·독립QA는 다음 담당 확인 대상입니다.',
       '- 덕양의 기존 qualified 공원 설명과 분당의 qualified 공원 설명은 쓰지 않았습니다. 보강한 R03-F03·R09-F02의 verified 위치·기능만 반영했습니다.',
       '- 가구 수 분모를 이용한 비중·집중도, 선택 이유·순유입·가격 원인·인기도·매물 추천으로 해석하지 않았습니다.',
       '- 원미구의 2023 값·변화율은 null로 보존했습니다. 가격 자료는 본문에 사용하지 않았습니다.', '']

OUT.mkdir(parents=True, exist_ok=True)
written = []
def write_json(name, obj):
    path = OUT / name
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    written.append(path)
(OUT/'script_v2.md').write_text('\n'.join(md), encoding='utf-8')
written.append(OUT/'script_v2.md')
write_json('scene_proposals.json', proposal)
write_json('claim_map.json', claim_map)

issues = {
    'issue_id':'TOP20V2-REVIEW', 'revision':REV, 'status':'proposed_for_director',
    'delivery_method':'직접 에이전트 메시지 도구 없음; 로컬 제안 파일로 인계',
    'items':[
      {'scene_ids':[s['scene_id'] for s in scenes], 'problem':'새 대본 승인·독립 검수 대기',
       'evidence':'script_v2.md 및 claim_map.json; 2023 PDF 텍스트 전사값의 페이지 화상 대조는 조사팀 미완료 기록',
       'proposal':'총괄→독립QA에 숫자·원표·qualified 제외·구성 비교를 확인시킨 뒤 이 버전의 대본을 사용자에게 전달',
       'impact':'새 대본 승인 전 오디오·렌더 시작 불가', 'next_role':'director/qa'},
      {'scene_ids':['I001','I002','S007','S010','S013','S015','S017','S018','S022','C001'], 'problem':'새 비교 도표·기존 구성카드의 해당 행 확인 필요',
       'evidence':'직접계산은 claim_map.json에 원값·식 기록. 현재6장 카드 중 I001·YOY 전용카드는 없음',
       'proposal':'visual이 기존 채널 문법으로 동일기준선/독립막대 비교를 제안; 초혼+재혼 합으로 전체 재구성 금지',
       'impact':'기존20지도·6카드의 재생성을 요구하지 않음; 새 분석 컷만 준비', 'next_role':'visual'},
      {'scene_ids':[s['scene_id'] for s in scenes if s['photo_requirements']],
       'problem':'장소를 말하는 문장과 실제 사진의 위치·권리를 연결해야 함',
       'evidence':'scene_proposals.json의photo_requirements; 사진 픽셀·권리 미검수',
       'proposal':'공원/시설명이 낭독되는 컷은 정확한 장소만 연결. 미확보 시 공식 원문 해당 행+검증된 구 경계 지도로 대체하고 정밀 핀은 좌표 확인 후 제안',
       'impact':'사진 명세 확정 후 claim_map의사진asset_id 연결. 전체 대본 반복 검수 불필요', 'next_role':'visual'},
    ],
}
write_json('issue_TOP20V2_REVIEW.json', issues)

assert [s['region_id'] for s in scenes if s['region_id']] == [f'R{n:02}' for n in range(20,0,-1)]
assert len({s['scene_id'] for s in scenes}) == len(scenes)
assert all(s['scene_id']==rows[s['region_id']]['scene_id'] for s in scenes if s['region_id'])
assert all(registry[c]['status'] in ['verified','verified_input_reused'] for s in scenes for c in s['claim_ids'])
assert all(c in registry for c in used)
assert sum(s['duration_s'] for s in scenes)==480
assert all(a['end_s']==b['start_s'] for a,b in zip(scenes,scenes[1:]))
assert len(increased)==6 and len(decreased)==13 and comparisons['R20']['count2023'] is None
assert province_counts=={'인천':5, '서울':9, '경기':6}
assert char_with_spaces >= 3800 and char_with_spaces <= 4300, char_with_spaces
assert all(asset in asset_registry for s in scenes for asset in s['asset_ids'])
assert all((EP/asset_registry[a]['actual_file']).exists() for s in scenes for a in s['asset_ids'])
assert not any(w in spoken for w in ['아닙니다','공식지수','AI 개념','순유입','인기도','집값 상승','추천 순위'])
assert not any(c in used for c in claim_map['qualified_excluded_claim_ids'])
value_checks = []
for s in scenes:
    if s['region_id']:
        r=rows[s['region_id']]
        protected = f"{r['newlywed_couples']:,}쌍"
        if r['newlywed_couples']>=10000:
            n=r['newlywed_couples']; protected=f"{n//10000}만 {n%10000:,}쌍"
        assert protected in s['narration_text'], (s['scene_id'],protected)
        value_checks.append({'region_id':r['region_id'],'scene_id':s['scene_id'],
                             'rank':r['rank'],'count':r['newlywed_couples'],'spoken_exact_match':True})
receipt = {
    'revision':REV,'scope':'writer 자체 정합성 점검',
    'narration_characters':{'with_spaces_normalized':char_with_spaces,'without_whitespace':char_without_spaces,
                            'method':'낭독문만 연결, 줄바꿈 등 연속 공백을1칸 정규화. 장면명·제목·화면메모 제외'},
    'rank_order_complete_20_to_1':True,'missing_rank_ids':[],'duplicate_rank_ids':[],
    'seed_scene_ids_preserved':True,'unique_scene_ids':True,'count2024_checks':value_checks,
    'all_used_factual_claim_statuses_accepted':True,'qualified_claims_used':[],
    'comparison_regions':19,'increased':6,'decreased':13,'wonmi_2023':None,
    'gangnam_yoy':comparisons['R06'],'old_seogu_yoy':comparisons['R01'],
    'province_region_counts':province_counts,
    'duration_sum_s':480,'continuous_estimate_schedule':True,'audio_aligned':False,
    'existing_map_card_paths_exist':True,
    'file_scope':'writer/top20-8min-v2 안에만 작성',
    'shared_state_scenes_decisions_written':False,'previous_script_written':False,
    'independent_qa_performed':False,'actual_listening_performed':False,
    'continuous_playback_performed':False,'render_created':False,
    'paid_api_used':False,'external_claude_transfer_performed':False,'upload_performed':False,
    'input_versions':snapshots,
}
write_json('verification.json',receipt)
handoff = {
    'task_id':'writer-top20-8min-v2', 'role':'writer',
    'status':'review_draft_complete_pending_user_script_approval_and_independent_QA',
    'summary':'20→1위 20개 지역 검토 초안' +
              f'. 낭독문 {char_with_spaces}자(공백 포함), {char_without_spaces}자(공백 제외). 총480초는 estimate이며 오디오 미확정. 19지역 변화=6증가13감소, 원미2023=null. 서울9·경기6·인천5. 보강verified2개 반영. 새 대본 승인 대기.',
    'input_revisions':snapshots,
    'authoring_source':{'path':Path(__file__).relative_to(EP).as_posix(),'sha256':sha(Path(__file__))},
    'outputs':[{'path':p.relative_to(EP).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in written],
    'affected_scene_ids':[s['scene_id'] for s in scenes],
    'checks':[
       {'check':'낭독문자수·순위20개누락/중복·장면시드·2024값20개·19지역재계산·qualified제외·480초합계',
        'result':'passed_local_consistency','evidence':'writer/top20-8min-v2/verification.json'},
       {'check':'사용자 새 대본 승인','result':'pending','evidence':None},
       {'check':'독립QA·2023원표화상·사진장소/권리·실제오디오정렬','result':'not_performed_by_writer','evidence':'writer/top20-8min-v2/issue_TOP20V2_REVIEW.json'},
    ],
    'narration_character_count':receipt['narration_characters'],
    'rank_validation':{'expected':20,'observed':20,'missing':[],'duplicates':[],'count2024_exact_matches':20},
    'audio_and_timing':{'estimated_total_s':480,'actual_duration_s':None,'timing_locked':False,'audio_created':False},
    'approval_status':{'script':'pending_new_user_approval','approval_id':None},
    'open_issue_ids':['TOP20V2-REVIEW'],
    'unresolved':['사용자 새 대본 승인','독립QA 및2023원표화상 대조','장소별 사진선택/권리 및지도·카드 픽셀 확인','음성선택·승인 후 실제길이/정렬'],
    'next_role':'director → qa(대본/계산) → 사용자 script 결정; 승인 후 visual/narration',
    'common_scene_proposal':'scene_proposals.json만 병합 제안; 공통파일 및기존writer/대본초안_v1.md 미수정',
    'authorization':{'audio':False,'paid_generation':False,'external_claude_transfer':False,'render':False,'upload':False},
    'skills_applied':['hyperframes-creative/references/narration.md (문체·숫자읽기만; 제작/CLI 미실행)'],
    'created_at':datetime.now(timezone(timedelta(hours=9))).isoformat(),
}
write_json('handoff.json',handoff)
for p in written:
    if p.suffix=='.json': json.loads(p.read_text(encoding='utf-8'))
print(json.dumps({'status':'written_and_local_consistency_checked','narration_with_spaces':char_with_spaces,
                  'narration_without_spaces':char_without_spaces,'ranks':20,'scenes':len(scenes),
                  'duration_s_estimate':480,'outputs':[p.name for p in written]},ensure_ascii=False))
