import json, re, pathlib, hashlib
e=pathlib.Path(__file__).resolve().parents[2]
r=json.loads((e/'research/commute-v6/route_observations.json').read_text(encoding='utf8'))
assert len(r['observations'])==15
assert len({(x['block'],x['destination']) for x in r['observations']})==15
assert all(any('오전 8:00' in c for c in x['context']) and any('10월 19일' in c for c in x['context']) for x in r['observations'])
p=e/'outputs/script-review-v6/script_v6.md'
s=p.read_text(encoding='utf8')
assert len(re.findall(r'^## M[0-9]+',s,re.M))==10
v=json.loads((p.parent/'validation.json').read_text(encoding='utf8'))
assert hashlib.sha256(p.read_bytes()).hexdigest()==v['script_sha256']
assert '2022년 8월 시행 공개 시각표의 아침 열차 사례' not in s
state=json.loads((e/'state.json').read_text(encoding='utf8'))
assert state['draft_script_revision']=='script-v6' and state['voice_generation_hold']
print('PASS: 15 unique weekday-08:00 routes, 10 chapters, script hash, replacement, unpaid review state')
