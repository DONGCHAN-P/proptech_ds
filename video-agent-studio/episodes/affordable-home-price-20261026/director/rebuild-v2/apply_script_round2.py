"""Preserve v3 and apply the actual Claude review as a new frozen revision."""
import json,hashlib,re
from pathlib import Path
D=Path(__file__).resolve().parent
old=D/'frozen-script-v3';out=D/'frozen-script-v3-r2';out.mkdir(exist_ok=False)
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
d=read(old/'scenes_v3.json');review=read(D/'claude/script-v3-round1/review.json')
assert review['artifact_sha256']==sha(old/'script_v3.md')
sc={q['id']:q for q in d['scenes']};changes=[]
for issue in review['required_issues']:
 sid=issue['id'];text=issue['replacement'].split('「',1)[-1] if False else issue['replacement']
 text=text.split('"',1)[1].rsplit('"',1)[0]
 changes.append({'id':sid,'before':sc[sid]['narration'],'after':text,'basis':'Claude required'})
 sc[sid]['narration']=text
sc['R014']['beats'][-1]['anchor']='큰 쪽 하나만'
sc['R014']['beats'][1]['action']='출산가구 감면 상한을 하나씩 표시한다.'
sc['R014']['visual_notes']='최대 감면액과 적용 대상 선택을 순차 표시한다. 세부 자격과 추징 요건의 출처는 소스 기록에 보존한다. 감면 후 미산출 세액은 만들지 않는다.'
sc['R010']['visual_notes']='이 장면은 공제 적용 결과를 표시한다. 다음 R011에서 보증 승인으로 공제를 보완한 경우로 전환한다. 기존 임차인·선순위 권리 없음. 세금과 공제는 별개 영역에 표시한다.'
edits={
 'R007': [('A에게 신용대출 같은 기존 부채가 생기면, 이 예산 중 주택대출에 쓸 수 있는 몫도 줄어듭니다.','신용대출의 원리금도 이 상환 예산에 함께 들어갑니다.')],
 'R008': [('금리가 유지되면 매달 같은 원금과 이자 합계액을 갚는 방식입니다. ','')],
 'R011': [('이 대출을 연 4%, 30년 원리금균등으로 갚으면','금리가 유지되는 동안 매달 같은 원금과 이자 합계액을 갚는 원리금균등 방식입니다. 이 대출을 연 4%, 30년으로 갚으면')],
 'R020': [('B는 기존 신혼 합산소득 기준 안에서 신청합니다.','B는 부부합산 소득 8천만 원으로 신혼 소득 기준 안에서 신청합니다.')],
 'R022': [('이 정책상품의 신규대출은 규제 DSR 예외 틀에서 해당 DTI와 신용, 보증 조건을 심사합니다.','정책대출은 DSR 규제의 예외지만 DTI와 신용·보증은 심사합니다.')]
}
for sid,pairs in edits.items():
 before=sc[sid]['narration']
 for a,b in pairs:
  assert a in sc[sid]['narration'];sc[sid]['narration']=sc[sid]['narration'].replace(a,b)
 changes.append({'id':sid,'before':before,'after':sc[sid]['narration'],'basis':'Claude recommendation'})
sc['R007']['beats'][-1]['anchor']='신용대출의 원리금'
sc['R007']['beats'][-1]['action']='전체 대출 원리금이 같은 연간 예산에 포함됨을 짧은 연결선으로 표시한다. 새 부채 금액을 만들지 않는다.'
sc['R032']['visual_notes']=read(D/'visual_overrides.json')['overrides'][0]['replacement'] if False else 'R031의 A 월 예산 비교를 이어받아, 두 가격의 최초 대출원금을 고정한 4%·6% 신규 360개월 비교로 전환. 5년 경과 후 잔액을 쓰지 않는다. 숫자는 발화 순서에 맞춰 생성한다.'
for s in d['scenes']:
 last=-1
 for b in s['beats']:
  assert s['narration'].count(b['anchor'])==1,(s['id'],b['anchor'])
  pos=s['narration'].index(b['anchor']);assert pos>last;last=pos
d['revision']='script-v3-r2';save(out/'scenes_v3_r2.json',d)
md='---\ntitle: 내 돈 2억5천만원, 감당 가능한 집값은?\nepisode_id: affordable-home-price-20261026\nversion: script-v3-r2\npolicy_as_of: 2026-10-26\ntiming_basis: free TTS 전 실제시간 미측정\n---\n'
for c in d['chapters']:
 md+='\n## '+str(c['id'])+'. '+c['title']+'\n'
 for s in d['scenes']:
  if s['chapter']==c['id']:md+='\n### '+s['id']+' · '+s['title']+'\n\n'+s['narration']+'\n'
(out/'script_v3_r2.md').write_text(md,encoding='utf-8')
save(out/'changes.json',{'previous_script_sha256':sha(old/'script_v3.md'),'script_sha256':sha(out/'script_v3_r2.md'),'scenes_sha256':sha(out/'scenes_v3_r2.json'),'required_addressed':['R010','R014'],'changes':changes,'numeric_values_changed':False,'notes':['R032 stale direction removed; no voice numeric changes.','R001/R029 and R030 use consistent bank/cash vs monthly-goal colours.','R014 detail eligibility remains original source/revision notes.']})
print(json.dumps({'script_sha256':sha(out/'script_v3_r2.md'),'scenes_sha256':sha(out/'scenes_v3_r2.json'),'scene_count':len(d['scenes'])}))
