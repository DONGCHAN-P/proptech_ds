"""Export and verify the revised main's exact authored subtitle cues."""
from pathlib import Path
import hashlib,json,re
D=Path(__file__).resolve().parent;E=D.parents[1]
H=E/'editor/top20-enhance-v2';O=E/'outputs/top20-enhance-v2'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(s):return re.sub(r'\s|[.,?!·]','',s)
def stamp(t):
 n=round(t*1000);h,n=divmod(n,3600000);m,n=divmod(n,60000);s,ms=divmod(n,1000)
 return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'
sp=read(D/'scene_proposals_v5.json');mapping=H/'main/caption_mapping.json';cues=read(mapping)['cues']
sentences={x['sentence_id']:x['text']for s in sp['scenes']for x in s['sentences']}
assert len(sentences)==113
for sid,text in sentences.items():assert norm(''.join(c['text']for c in cues if c['sentence_id']==sid))==norm(text),sid
assert set(c['sentence_id']for c in cues)==set(sentences)
lines=[]
for i,c in enumerate(cues):
 assert c['end_s']>c['start_s']>=0
 if i:assert c['start_s']>=cues[i-1]['end_s']-.001
 lines.append(f'{i+1}\n{stamp(c["start_s"])} --> {stamp(c["end_s"])}\n{c["text"]}\n')
O.mkdir(exist_ok=True,parents=True);p=O/'자막.srt';p.write_text('\n'.join(lines),encoding='utf-8')
receipt={'status':'all113sentences_exactly_preserved_and_ordered','file':str(p),'sha256':sha(p),'caption_mapping_sha256':sha(mapping),'cue_count':len(cues),'sentences':113,'last_cue_end_s':cues[-1]['end_s'],'actual_listening':False}
(O/'subtitle_verification.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(receipt,ensure_ascii=False))
