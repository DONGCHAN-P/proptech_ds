from pathlib import Path
import json,re,hashlib,uuid,datetime
E=Path(__file__).resolve().parents[1];O=E/'outputs/script-review-v5';O.mkdir(exist_ok=True)
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
scenes=json.loads((E/'writer/scenes_v4.json').read_text(encoding='utf8'));units=json.loads((E/'narration/units_v4.json').read_text(encoding='utf8'));script=(E/'outputs/script-review-v4/script_v4.md').read_text(encoding='utf8')
replacements={
'저는 서울과의 거리, 집값, 실제로 누릴 생활 편의를 함께 보겠습니다.':'서울과의 거리, 집값, 실제로 누릴 생활 편의를 함께 살펴보겠습니다.',
'저는 이 가격에 집을 살 사람이 누구인지, 그 사람들이 이 단지를 선택할 이유가 무엇인지에 초점을 맞추겠습니다.':'이 가격대의 주택을 찾는 수요와 단지별 선택 요인에 초점을 맞추겠습니다.',
'저는 이 집들이 어떤 교통과 생활시설을 함께 이용하게 되는지를 중요하게 보겠습니다.':'주택과 연결되는 교통·생활시설은 입지를 평가하는 핵심 기준입니다.',
'저는 직장이 어디에 있느냐에 따라 교산 안에서도 유리한 위치가 달라진다고 보고, 목적지별로 단지를 비교하겠습니다.':'직장 위치에 따라 교산 안에서도 유리한 입지가 달라지므로, 목적지별로 단지를 비교하겠습니다.',
'저는 이 두 사업을 교산 안의 일자리를 늘릴 후보로 보겠습니다.':'두 사업은 교산 내부의 일자리 기반을 확대할 계획으로 살펴보겠습니다.',
'저는 단지에서 큰 도로를 건너는지, 정류장이 어느 방향에 있는지, 어디서 갈아타는지를 함께 보겠습니다.':'단지와 정류장 사이의 도로 횡단, 정류장 방향, 환승 위치를 함께 확인하겠습니다.',
'저는 약 5억원대라는 가격을 전용면적과 함께 보겠습니다.':'약 5억원대라는 가격은 전용면적과 함께 비교해야 합니다.',
'저는 공원과 상권, 일상에서 자주 오가는 길을 먼저 보겠습니다.':'생활 편의는 공원과 상권, 일상적인 이동 동선을 중심으로 살펴보겠습니다.',
'저는 이 사업을 교산 주변의 상업·업무 기반이 늘어날 후보로 보겠습니다.':'이 사업은 교산 주변의 상업·업무 기반을 확대할 계획으로 함께 살펴보겠습니다.',
'저는 전체 주택 계획을 단지별 입주와 거래 가능 시점으로 나누어 보겠습니다.':'전체 주택 계획은 단지별 입주와 거래 가능 시점으로 나누어 살펴보겠습니다.',
'저는 교산의 시설이 갖춰지는 속도와 그때 새로 공급되거나 거래 가능한 집의 수를 함께 보겠습니다.':'공급 여건은 시설이 갖춰지는 속도와 시기별 신규 공급·거래 가능 물량을 함께 보겠습니다.',
'저는 교산의 가격과 면적, 기다려야 하는 시간을 함께 비교해 선택할 이유를 찾겠습니다.':'교산의 가격 경쟁력은 면적과 생활 기반이 갖춰지는 시간까지 함께 비교해 판단하겠습니다.',
'저는 대장 후보의 입지 장점과 실제 매입가격을 함께 비교해 투자 매력을 판단하겠습니다.':'대장 후보의 투자 매력은 입지 장점과 실제 매입가격을 함께 비교해 판단하겠습니다.',
'저는 A2를 처음 집을 살 때의 가격과 기존 하남의 교통·상권을 얼마나 편하게 이용할 수 있는지 비교하는 기준 단지로 보겠습니다.':'A2는 초기 구입 부담과 기존 하남의 교통·상권 접근성을 비교하는 기준 단지로 살펴보겠습니다.',
'제가 교산을 고르는 기준은 실제로 지불할 가격, 그 가격에 누릴 생활 편의, 그리고 기다려야 하는 시간입니다.':'교산의 주거·투자 가치를 비교하는 기준은 실제 구입 비용, 생활 편의, 시설이 갖춰지는 시점입니다.'}
titles={'M000':'하남 교산','M001':'전체 토지계획','M002':'1. 일자리','M003':'2. 교통','M004':'3. 가격','M005':'4. 생활시설','M006':'5. 공급','M007':'6. 주변 시세','M008':'7. 대장 후보','M009':'정리'}
changes=[]
for a,b in replacements.items():
 assert a in script,a
 script=script.replace(a,b)
 ids=[]
 for s in scenes:
  for u in s['units']:u['text']=u['text'].replace(a,b)
 for u in units:
  if a in u['text']:u['text']=u['text'].replace(a,b);u['spoken_text']=None;ids.append(u['unit_id'])
 changes.append({'before':a,'after':b,'unit_ids':ids})
for s in scenes:
 old=s['title'];new=titles[s['scene_id']];script=script.replace('## '+s['scene_id']+' · '+old,'## '+s['scene_id']+' · '+new);s['title']=new;s['script_revision']='v5'
 for u in units:
  if u['scene_id']==s['scene_id']:u['title']=new
script=script.replace('대본 v4','대본 v5').replace('narration/units_v4.json','narration/units_v5.json')
for s in scenes:
 actual=script.split('## '+s['scene_id']+' · ',1)[1].split('### 낭독',1)[1].split('### 화면 지시',1)[0].strip();assert actual=='\n'.join(u['text']for u in s['units'])
assert not re.search(r'제가|저는','\n'.join(u['text']for u in units))
def nums(x):return re.findall(r'\d+(?:[.,]\d+)*',x)
old=json.loads((E/'narration/units_v4.json').read_text(encoding='utf8'));assert nums(''.join(u['text']for u in old))==nums(''.join(u['text']for u in units))
(O/'script_v5.md').write_text(script,encoding='utf8');dump(E/'writer/scenes_v5.json',scenes);dump(E/'narration/units_v5.json',units);dump(O/'changes.json',changes)
dump(O/'verification.json',{'first_person_remaining':0,'numeric_facts_preserved':True,'script_scenes_consistent':True,'changed_passages':len(changes),'titles':titles,'audio_video_reflected':False})
approval={'id':uuid.uuid4().hex[:12],'gate':'script','episode':E.name,'status':'approved_for_requested_editorial_revision','artifact_hashes':{'outputs/script-review-v5/script_v5.md':hashlib.sha256((O/'script_v5.md').read_bytes()).hexdigest()},'approval_basis':'Direct user feedback 2026-10-20: simplify headings to numbered topics and remove personal home-buying voice; existing instruction to proceed with production.','paid_generation_authorized':False,'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
d=json.loads((E/'decisions.json').read_text(encoding='utf8'));d['decisions'].append(approval);dump(E/'decisions.json',d);dump(O/'script_approval.json',approval)
s=json.loads((E/'state.json').read_text(encoding='utf8'));s['stage']='production_v5_in_progress';s['script_language_revision']={'revision':'script-v5-neutral-titles','script':'outputs/script-review-v5/script_v5.md','script_sha256':approval['artifact_hashes']['outputs/script-review-v5/script_v5.md'],'decision_id':approval['id'],'status':'approved_for_requested_editorial_revision','audio_reflected':False,'video_reflected':False,'paid_calls':0};dump(E/'state.json',s)
(O/'수정내역.md').write_text('# 대본 v5 수정\n\n소제목을 번호와 주제만 남기도록 정리했습니다. 15개 문장의 1인칭 표현을 주거·투자 가치 비교 기준을 설명하는 중립적 표현으로 수정했습니다. 사실·숫자·대장 후보 및 자료화면 구성은 유지했습니다.\n',encoding='utf8')
print(json.dumps({'changed_passages':len(changes),'numeric_facts_preserved':True,'first_person_remaining':0}))
