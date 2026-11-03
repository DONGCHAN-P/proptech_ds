import json,re,hashlib
from pathlib import Path
q=Path(__file__).parent;ep=q.parents[1]
def read(p):return p.read_text(encoding='utf-8-sig')
def scenes(t):return {m.group(1):m.group(2).strip() for m in re.finditer(r'## (M\d+) ·[^\n]*\n\n### 낭독\n\n(.*?)\n\n### 화면 지시',t,re.S)}
a=ep/'outputs/script-review-v7/script_v7.md';b=ep/'outputs/script-review-v8/script_v8.md'
old=scenes(read(a));new=scenes(read(b));nums=lambda t:re.findall(r'\d[\d,.]*',t)
rows=[]
for k,t in new.items():
 rows.append({'scene_id':k,'numeric_tokens_unchanged':nums(t)==nums(old[k]),'chars':len(t),'sentences':len(re.findall(r'[.!?]',t)),'informal_ending_matches':re.findall(r'[^.!?\n]*(?:볼게요|할게요|했어요|이고요|였고요|있죠|이죠|겠죠|거든요|해요|예요)[.!?]',t)})
packet=json.loads(read(ep/'writer/revision-v8/narration_packet.json'))
r={'script_sha256':hashlib.sha256(b.read_bytes()).hexdigest(),'source_v7_sha256':hashlib.sha256(a.read_bytes()).hexdigest(),'scene_order':list(new),'all_numeric_tokens_unchanged':all(x['numeric_tokens_unchanged'] for x in rows),'M008_absent':'M008' not in new,'scene_checks':rows,'narration_chars':sum(len(x) for x in new.values()),'school_scene_character_fraction':len(new['M005'])/sum(len(x) for x in new.values()),'packet_estimated_final_seconds':packet.get('estimated_final_seconds'),'estimate_not_measured':True,'packet_keys':list(packet)}
(q/'script_audit.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(r,ensure_ascii=False))
