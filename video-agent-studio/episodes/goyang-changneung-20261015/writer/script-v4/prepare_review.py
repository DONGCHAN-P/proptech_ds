from pathlib import Path
import re,json,hashlib
ep=Path(__file__).resolve().parents[2]
src=Path(__file__).with_name('script_v4.md')
t=src.read_text(encoding='utf-8')
trim={
'역 이름이 같다고 모든 블록의 역 접근이 같아지는 것은 아닙니다.':'',
'이 질문에 답하면서 각 권역을 읽으면 단지 이름과 점만 볼 때보다 선택의 차이가 드러납니다.':'세 질문으로 각 권역의 차이를 읽겠습니다.',
'어느 블록이 출근에 더 유리한지까지 정해 주지는 않습니다. 교대까지의 시간을 강남역까지의 시간으로 읽어서도 안 됩니다.':'교대까지의 시간을 강남역까지의 시간으로 읽지는 않겠습니다.',
'목적역 이름을 아는 데서 끝내지 않고 첫 구간과 마지막 환승까지 이어 보는 것이 핵심입니다.':'첫 구간과 마지막 환승까지 이어 보는 것이 핵심입니다.',
'번호와 연결 지점을 화면에 놓겠습니다. 이 노선들은 주변 생활권의 현재 연결을 이해하는 근거이며 새 단지 현관 앞 정류장을 뜻하지는 않습니다.':'주변 생활권의 연결 지점과 노선번호를 화면에 놓겠습니다.',
'발표된 노선이 있다는 이유로 첫 출근부터 그 철도를 탄다고 계산하지 않는 것이죠.':'',
'이 차액은 미래 시세 프리미엄이나 지금 살 수 있는 매물의 가격 차이가 아닙니다.':'',
'이 달력의 장점은 분명하지만 학교 배정과 개교 확정까지 뜻하는 표시는 아닙니다.':'학교 목표와 실제 배정·개교 확정은 구분하겠습니다.',
'학교 부지가 가까이 있다는 것과 입주 때 그 학교를 이용한다는 것은 다릅니다. 학령기 자녀가 있는 가구에게는 이 차이가 후보를 고르는 중요한 기준입니다.':'학령기 자녀가 있다면 학교 부지보다 실제 개교 시점을 먼저 보셔야 합니다.',
'지역 이름만으로 모두 비싸거나 모두 역에 가깝다고 묶을 수 없는 이유입니다.':'지역 이름보다 개별 단지를 봐야 하는 이유입니다.',
'오늘 이 표에서 기억할 것은 여섯 숫자 전부가 아닙니다.':'',
'신축을 기다릴 이유는 기존 대안을 함께 놓았을 때 더 분명해집니다.':'',
'그동안 필요한 주거비와 이용할 출근길을 더하면 공고가격만 볼 때 놓쳤던 비용이 드러납니다.':'그 사이 주거비와 출근길을 더하면 공고가격 밖의 비용이 드러납니다.',
'같은 삼년이어도 시작하는 사건이 다릅니다.':'',
'같은 3년이어도 시작하는 사건이 다릅니다.':'',
'학교 일정과 초기 학생 배치가 확인되면 평가를 다시 할 부분입니다.':'',
}
for a,b in trim.items():t=t.replace(a,b)
pairs={
'삼송이차아이파크':'삼송2차아이파크','삼송원흥역센트럴푸르지오':'삼송원흥역센트럴푸르지오','지축역중흥 에스클래스 북한산파크뷰':'지축역중흥 S-클래스 북한산파크뷰',
'에스파이브':'S5','에스쓰리':'S3','에스포':'S4','에스원':'S1','엘에이치':'LH','엘엑스':'LX','디엠씨':'DMC','지티엑스 에이':'GTX-A',
'이천이십오년 십이월':'2025년 12월','이천이십육년 구월 말':'2026년 9월 말','이천이십육년 삼분기':'2026년 3분기','이천이십이년 팔월':'2022년 8월','이천이십팔년 일월':'2028년 1월','이천이십구년 오월':'2029년 5월','이천삼십년 삼월':'2030년 3월','이천삼십일년 십이월':'2031년 12월','이천삼십년':'2030년','이천이십팔년':'2028년','같은 해 삼월':'같은 해 3월',
'약 칠억 칠천칠백만 원':'약 7억 7,700만 원','팔억 칠천삼백만 원':'8억 7,300만 원','칠억 구천만 원':'7억 9,000만 원','약 구천칠백만 원':'약 9,700만 원','약 팔천삼백만 원':'약 8,300만 원',
'팔십사 제곱미터대':'84㎡대','팔십삼 이상 팔십오 제곱미터 미만':'83㎡ 이상 85㎡ 미만','오층 이상':'5층 이상','삼백여 기업':'300여 기업','삼백 곳':'300곳','일곱 시부터 아홉 시':'7시부터 9시','약 이십사분':'약 24분','약 이십팔분':'약 28분','약 사십구분':'약 49분','종로삼가':'종로3가','오호선':'5호선','삼호선':'3호선','육호선':'6호선','칠칠이팔 번':'7728번','가칭 오유치원':'가칭 5유치원','오초등학교':'5초등학교','가칭 칠유치원':'가칭 7유치원','칠초등학교':'7초등학교','가칭 육유치원':'가칭 6유치원','육초등학교':'6초등학교','삼년':'3년',
'구억 이천만 원':'9억 2,000만 원','팔억 오천만 원':'8억 5,000만 원','칠억 사천오백만 원':'7억 4,500만 원','팔억 삼천칠백오십만 원':'8억 3,750만 원','십일억 이천칠백오십만 원':'11억 2,750만 원','팔억 사천오백만 원':'8억 4,500만 원','칠억대 중반':'7억대 중반','팔억대':'8억대','칠억대':'7억대','십일억대':'11억대'
}
for a,b in sorted(pairs.items(),key=lambda x:-len(x[0])):t=t.replace(a,b)
t=re.sub(r'[ \t]+\n','\n',t)
t=re.sub(r'\n[ \t]+','\n',t)
t=re.sub(r' {2,}',' ',t)
t=t.replace('낭독의 영문·숫자는 발음용 표현을 쓰되 자막은','검토 낭독문은 영문·숫자를 정상 표기로 쓰며, 추후 음성 발음사전과 분리한다. 자막은')
t=t.replace('S5는 중앙 서측에서 이른 입주를 예정한 곳, S1은 서측의 별도 권역, S4는 원흥 기존 생활권과 맞닿는 쪽입니다.','S5는 비교 세 후보 중 이른 입주를 예정한 곳, S1은 공원·학교 배치를 함께 볼 곳, S4는 원흥 기존 생활권과의 접점을 살펴볼 곳입니다.')
t=t.replace('S1의 배치와 자신의 입주 일정','S1의 배치와 자신의 입주 일정')
src.write_text(t,encoding='utf-8')
scenes=[]
basis=json.loads((ep/'writer/script-v3/claim_basis.json').read_text(encoding='utf-8'))
lookup={x['claim_id']:x for s in basis['scenes'] for x in s['claims']}
addendum=json.loads((ep/'research/script-v4-addendum/facts_addendum.json').read_text(encoding='utf-8'))
lookup.update({x['claim_id']:x for x in addendum['facts']})
for m in re.finditer(r'^## (M\d+) · (.*?)\n\n### 낭독\n\n(.*?)\n\n### 화면 지시\n\n(.*?)\n\nclaim_ids: (.*?)\n자료 유형: (.*?)(?=\n\n## |\Z)',t,re.M|re.S):
 sid,title,narr,visual,ids,kinds=m.groups(); ids=[x.strip() for x in ids.split(',')]
 scenes.append(dict(scene_id=sid,title=title,narration_text=narr,visual_direction=visual,claim_ids=ids,asset_types=[x.strip() for x in kinds.split(',')],estimated_duration_seconds=round(len(narr)/7.8,1),timing_basis='estimate; new audio not generated'))
plain='\n\n'.join(f"[{s['scene_id']}] {s['title']}\n\n{s['narration_text']}" for s in scenes)+'\n'
out=ep/'outputs/script-review-v4';out.mkdir(parents=True,exist_ok=True)
(out/'script_v4.md').write_text(t,encoding='utf-8')
(out/'narration_v4.txt').write_text(plain,encoding='utf-8')
(src.parent/'scene_proposals.json').write_text(json.dumps({'revision':'script-v4','status':'draft_review','timing_locked':False,'scenes':scenes},ensure_ascii=False,indent=2),encoding='utf-8')
mapping={'revision':'script-v4','source_revision':'script-v3','scope':'existing verified claims inherited; writer did not reverify original sources','scenes':[{'scene_id':s['scene_id'],'claims':[lookup.get(i,{'claim_id':i,'status':'mapping_missing'}) for i in s['claim_ids']]} for s in scenes],'derived_arithmetic':{'S4_minus_S5_krw':873329000-776598000,'S4_minus_S1_krw':873329000-790380000,'basis':'existing same stated specific84 type/floor base+balcony public notice examples; not transaction or future premium'}}
(src.parent/'claim_mapping.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'scenes':len(scenes),'narration_characters_including_spaces':sum(len(s['narration_text']) for s in scenes),'missing_claim_ids':[x['claim_id'] for s in mapping['scenes'] for x in s['claims'] if x.get('status')=='mapping_missing']},ensure_ascii=False))
