"""Replace defensive presentation with explicit editorial criteria, preserving facts."""
from pathlib import Path
import json,re,hashlib,uuid
EP=Path(__file__).resolve().parents[1];OUT=EP/'outputs/script-review-v3';OUT.mkdir(exist_ok=True)
R={
'단순히 유명한 단지를 고르기보다, 어떤 사람들이 이 가격에 집을 사려 할지 살펴보겠습니다.':'저는 이 가격에 집을 살 사람이 누구인지, 그 사람들이 이 단지를 선택할 이유가 무엇인지에 초점을 맞추겠습니다.',
'지금 보는 색은 실제 건물이 아니라 주택, 일자리를 위한 시설, 공원과 학교가 들어설 땅을 구분한 것입니다.':'계획도의 색을 따라 주택, 일자리를 위한 시설, 공원과 학교가 들어설 위치를 보겠습니다.',
'주택 수가 많다는 사실보다 중요한 것은 이 집들이 어떤 교통과 생활 기반을 나누어 이용하느냐입니다.':'저는 이 집들이 어떤 교통과 생활시설을 함께 이용하게 되는지를 중요하게 보겠습니다.',
'녹지가 넓어도 단지마다 공원까지의 거리는 다릅니다. 기업이나 업무시설이 들어설 땅이 있다고 이미 일자리가 생긴 것은 아닙니다.':'공원은 각 단지에서 얼마나 가깝게 이용할 수 있는지, 일자리는 기업이 언제 실제로 들어오는지를 기준으로 보겠습니다.',
'이렇게 세 구역으로 나누는 것은 설명을 위한 것이며, 공식 행정구역이나 집값 순위를 뜻하지는 않습니다.':'이 영상에서는 생활 여건을 비교하기 위해 교산을 북부·중앙·남부 세 구역으로 나누겠습니다.',
'교산 안에 들어올 기업만 볼 것이 아니라, 밖으로 출근하는 사람에게 어떤 대안이 되는지 함께 보겠습니다.':'교산 안에 들어올 기업과 기존 직장으로 출퇴근할 사람들을 함께 살펴보겠습니다.',
'이곳 주민이 가장 많이 출근하는 곳이라는 뜻은 아닙니다. 이동 방향과 교통편이 어떻게 다른지 비교하기 위해 골랐습니다.':'세 지역은 이동 방향과 이용할 교통편을 비교하기 위한 목적지로 골랐습니다.',
'판교는 서울 도심과 다른 남쪽 방향이므로 철도 기대만으로 같은 출근권이라고 묶기 어렵습니다.':'남쪽의 판교로 출근한다면, 잠실·강남 방향과 나누어 이동 경로와 환승을 살펴보겠습니다.',
'이 차이를 먼저 이해해야 교산 전체가 모든 직장인에게 똑같이 가깝다는 오해를 줄일 수 있습니다.':'저는 직장이 어디에 있느냐에 따라 교산 안에서도 유리한 위치가 달라진다고 보고, 목적지별로 단지를 비교하겠습니다.',
'이 면적은 기업이 실제로 입주해서 고용을 만든 숫자와는 다릅니다.':'이곳은 기업과 업무시설을 위한 계획 용지입니다. 앞으로 어떤 기업이 들어오고 얼마나 많은 일자리가 생기는지 살펴보겠습니다.',
'출입구가 확정된 것처럼 단지 앞에 작은 점을 찍는 대신 공식 노선도에서 확인되는 연결을 보여드리겠습니다.':'현재 공개된 공식 노선도를 따라 오금에서 교산을 거쳐 하남시청으로 이어지는 연결을 살펴보겠습니다.',
'공사 도면을 만들고 있다는 것은 사업이 진행 중이라는 뜻이며, 2032년은 확정 개통일이 아닌 목표입니다.':'현재는 구체적인 공사 도면을 만드는 단계입니다. 개통 목표인 2032년을 기준으로 입주 시점과 비교하겠습니다.',
'단지를 비교할 때에는 지도에서 가까워 보이는지만 볼 것이 아니라, 큰 도로를 건너는지, 정류장이 어느 방향에 있는지, 어디서 갈아타는지 함께 확인해야 합니다.':'저는 단지에서 큰 도로를 건너는지, 정류장이 어느 방향에 있는지, 어디서 갈아타는지를 함께 보겠습니다.',
'사전청약 때의 추정 분양가가 아니라 2025년 본청약 공고에서 확인한 특정 타입과 층의 공급금액입니다.':'가격 기준은 2025년 본청약 공고에 나온 주택형과 층별 공급금액입니다.',
'현재 새로 접수하는 청약표나 교산 전체 평균 가격이라는 뜻은 아닙니다.':'당시 A2를 분양받을 때 필요한 금액을 다른 단지와 비교할 출발점으로 삼겠습니다.',
'다른 유상옵션과 취득세 등은 이 합계에 들어 있지 않습니다.':'실제 예산을 잡을 때는 이 합계에 다른 유상옵션과 취득세 등을 추가해야 합니다.',
'여기서 중요한 것은 약 5억원대라는 앞자리보다 전용면적입니다.':'저는 약 5억원대라는 가격을 전용면적과 함께 보겠습니다.',
'교산 59㎡의 공고금액과 주변 84㎡의 실거래를 그대로 빼서 차익이라고 말하면 서로 다른 상품을 비교하게 됩니다.':'교산 59㎡와 주변 84㎡를 비교할 때는, 같은 예산으로 새집을 선택할지 더 넓은 기존 집을 선택할지에 초점을 맞추겠습니다.',
'학교가 모든 가구의 첫 번째 기준은 아니지만, 공원과 상권, 일상 동선이 함께 갖춰지는지는 넓은 수요에 영향을 줍니다.':'저는 공원과 상권, 일상에서 자주 오가는 길을 먼저 보겠습니다. 학교는 자녀가 있는 가구의 수요를 함께 살펴볼 요소입니다.',
'화면의 초등학교 예정 부지라는 표기는 아직 학교 이름이나 개교 월이 확정되었다는 뜻이 아닙니다.':'화면에는 초등학교가 들어설 예정 부지를 표시했습니다. 학교 이름과 개교 시점은 추후 발표되는 내용을 기준으로 확인하겠습니다.',
'입주와 학교 준비가 같은 날 끝나는 것으로 계산하기보다 공고에 적힌 연결 방식을 확인하는 것이 정확합니다.':'자녀가 있는 가구라면 입주 초기 어느 학교로 배정되는지를 함께 보겠습니다.',
'하지만 이것을 모든 아파트와 상가의 완공일로 바꾸면 안 됩니다.':'아파트 입주와 상가가 문을 여는 시점은 각각의 일정을 따라 살펴보겠습니다.',
'두 기간을 단순히 입주 예정일에 더해서 자유롭게 팔 수 있는 날짜를 계산하지 않겠습니다.':'집을 팔 수 있는 시점을 판단할 때는 전매제한과 거주의무가 각각 언제 시작되고 끝나는지 따로 확인해야 합니다.',
'교산의 가격 성장성을 볼 때에도 도시 완성 효과뿐 아니라 그 시점의 새 공급과 거래 가능한 물량을 함께 살펴볼 필요가 있습니다.':'저는 교산의 시설이 갖춰지는 속도와 그때 새로 공급되거나 거래 가능한 집의 수를 함께 보겠습니다.',
'한 건의 최고가를 단지 전체 시세처럼 보여드리는 방식은 아닙니다.':'여러 거래를 가격순으로 놓았을 때 가운데에 있는 값인 중위값과, 계산에 쓴 거래건수를 함께 보겠습니다.',
'이 표는 지금 집주인이 내놓은 가격이 아니라, 같은 기간에 같은 면적과 층 조건으로 실제 거래된 가격을 모아 계산한 결과입니다.':'이 표는 같은 기간에 같은 면적과 층 조건으로 실제 거래된 가격을 모아 계산한 결과입니다. 현재 매도 호가는 별도로 확인해야 합니다.',
'A2의 59㎡ 공고금액을 이 84㎡ 가격에 바로 맞추면 안 되는 이유도 이제 분명해집니다.':'A2의 59㎡와 기존 단지의 84㎡는 가격과 함께 면적, 입주 후 누릴 편의까지 나란히 비교하겠습니다.',
'따라서 교산의 메리트는 주변 단지보다 숫자가 낮다는 사실만으로 완성되지 않습니다.':'저는 교산의 가격과 면적, 기다려야 하는 시간을 함께 비교해 선택할 이유를 찾겠습니다.',
'다만 현재 공개된 자료만으로는 역 출입구의 정확한 위치와 모든 단지의 분양가를 같은 기준으로 비교하기 어렵습니다.':'후보를 고르는 기준은 중심 상권과 역까지의 이동 편의입니다. 역 출입구 위치와 각 단지의 분양가가 공개되면 이 기준에 맞춰 다시 비교하겠습니다.',
'C2와 B2 모두 실제 분양가와 상품, 역 출입구까지의 동선을 확인한 뒤 판단을 좁혀야 합니다. 민간분양 계획이라는 이유만으로 이미 거래할 수 있는 입주 단지라고 보는 것은 아닙니다.':'C2와 B2는 앞으로 민간분양이 계획된 후보입니다. 실제 분양가와 면적 구성, 역 출입구까지의 이동 경로가 공개되면 두 단지를 비교하겠습니다.',
'A2는 교산의 모든 면적을 대표하는 대장이라기보다, 처음 집을 살 때의 가격과 기존 하남의 교통·상권을 얼마나 편하게 이용할 수 있는지 비교하는 기준 단지로 보겠습니다.':'저는 A2를 처음 집을 살 때의 가격과 기존 하남의 교통·상권을 얼마나 편하게 이용할 수 있는지 비교하는 기준 단지로 보겠습니다.',
'이 경우에는 색칠된 자족용지의 크기보다 기업 입주와 일상 이동이 확인되는 단계가 중요합니다.':'남쪽 지역에서는 기업이 실제로 입주하는 시점과 집에서 직장·공원으로 오가는 편의를 중요하게 보겠습니다.',
'이것은 확정 가격 순위가 아니라 추가 자료가 나왔을 때 먼저 검토할 순서입니다.':'앞으로 새 자료가 나오면 이 순서대로 후보를 다시 검토하겠습니다.',
'입주와 지구 조성, 철도 목표도 같은 날짜가 아니었습니다.':'입주 예정일과 지구 조성 일정, 철도 개통 목표를 각각의 시간표에 놓고 비교했습니다.',
'이 세 가지를 구분하면 막연히 가깝다거나 싸다는 인상보다 선택의 기준이 분명해집니다.':'제가 교산을 고르는 기준은 실제로 지불할 가격, 그 가격에 누릴 생활 편의, 그리고 기다려야 하는 시간입니다.'
}
script=(EP/'outputs/script-review-v2/script_v2.md').read_text(encoding='utf8')
scenes=json.loads((EP/'writer/scenes_v2.json').read_text(encoding='utf8'));units=json.loads((EP/'narration/units_v2.json').read_text(encoding='utf8'));original=json.loads(json.dumps(units))
changes=[]
for old,new in R.items():
 assert old in script,old
 script=script.replace(old,new);ids=[]
 for s in scenes:
  for u in s['units']:
   if old in u['text']:u['text']=u['text'].replace(old,new)
 for u in units:
  if old in u['text']:
   u['text']=u['text'].replace(old,new);say=u['text']
   for a,b in [('GTX-D','지티엑스 디'),('GTX','지티엑스'),('A-2','에이 투'),('A2','에이 투'),('A-3','에이 쓰리'),('A3','에이 쓰리'),('LH','엘에이치'),('DMC','디엠씨'),('㎡','제곱미터'),('5호선','오호선'),('3호선','삼호선'),('9호선','구호선')]:say=say.replace(a,b)
   u['spoken_text']=say;ids.append(u['unit_id'])
 assert ids,old
 # Presentation may repeat A2/C2/B2 names, but factual amounts/dates stay identical.
 changes.append({'unit_ids':ids,'before':old,'after':new})
script=script.replace('대본 v2','대본 v3').replace('narration/units_v2.json','narration/units_v3.json')
oldtitle='3. 가격 · 사전청약이 아닌 본청약 사례';newtitle='3. 가격 · 본청약 공고로 보는 실제 부담'
script=script.replace(oldtitle,newtitle)
for row in scenes+units:
 if row.get('title')==oldtitle:row['title']=newtitle
(OUT/'script_v3.md').write_text(script,encoding='utf8')
(EP/'writer/scenes_v3.json').write_text(json.dumps(scenes,ensure_ascii=False,indent=2),encoding='utf8')
(EP/'narration/units_v3.json').write_text(json.dumps(units,ensure_ascii=False,indent=2),encoding='utf8')
(OUT/'changes.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2),encoding='utf8')
assert [x['unit_id'] for x in units]==[x['unit_id'] for x in original]
assert [x['claim_ids'] for x in units]==[x['claim_ids'] for x in original]
bad=[u['unit_id'] for u in units if re.search(r'아니|오해|뜻은|뜻하지|말하면',u['text'])]
assert not bad,bad
# Ignore repeated block/type identifiers when comparing numeric facts.
def facts(text):return re.findall(r'\d+(?:[.,]\d+)*',re.sub(r'(?<![A-Za-z0-9])(?:A|B|C)\d+(?![A-Za-z0-9])','',text))
assert facts('\n'.join(u['text'] for u in original))==facts('\n'.join(u['text'] for u in units))
receipt={'replacements':len(changes),'units':len(units),'fact_numbers_and_claims_preserved':True,'defensive_phrasing_check':bad,'audio_reflected':False,'video_reflected':False,'paid_calls':0}
(OUT/'verification.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(receipt))
