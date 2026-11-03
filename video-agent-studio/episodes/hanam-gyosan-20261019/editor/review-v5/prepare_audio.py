from pathlib import Path
import json,re,hashlib
E=Path(__file__).resolve().parent;EP=E.parents[1];O=EP/'outputs/production-v5';units=json.loads((EP/'narration/units_v5.json').read_text(encoding='utf8'))
def number(n):
 n=int(n)
 if n==0:return '영'
 digits='영일이삼사오육칠팔구';out=[]
 for big,name in [(100000000,'억'),(10000,'만'),(1,'')]:
  part=n//big;n%=big
  if not part:continue
  s=''
  for base,label in [(1000,'천'),(100,'백'),(10,'십'),(1,'')]:
   v=part//base;part%=base
   if v:s+=('' if v==1 and base>1 else digits[v])+label
  out.append(s+name)
 return ' '.join(out)
def spoken(s):
 for a,b in [('KT클라우드','케이티 클라우드'),('KT자산운용','케이티 자산운용'),('51A','오십일 에이'),('59A','오십구 에이'),('A-2','에이 투'),('A2','에이 투'),('C-2','씨 투'),('C2','씨 투'),('B-2','비 투'),('B2','비 투'),('AI','에이아이'),('SPC','에스피씨'),('LH','엘에이치'),('㎡','제곱미터'),('%','퍼센트')]:s=s.replace(a,b)
 s=re.sub(r'\d[\d,]*(?:\.\d+)?',lambda m:number(m[0].replace(',','').split('.')[0])+(' 점 '+' '.join('영일이삼사오육칠팔구'[int(c)] for c in m[0].split('.')[1]) if '.' in m[0] else ''),s)
 return s
def split(s):
 # 문장, 쉼표 뒤의 호흡, 긴 연결절을 우선하며 숫자·명칭 내부는 자르지 않는다.
 a=re.split(r'(?<=[.!?])\s+|(?<=[,，])\s+',s);out=[]
 for t in a:
  if len(t)>64:
   bits=re.split(r'(?<=이고)\s+|(?<=하며)\s+|(?<=하면)\s+|(?<=지만)\s+|(?<=반면)\s+|(?<=따라)\s+|(?<=대신)\s+|(?<=위해)\s+',t)
   if len(bits)==1:bits=[t]
   out.extend(x.strip() for x in bits if x.strip())
  elif t.strip():out.append(t.strip())
 return out
out=[]
for u in units:
 for i,t in enumerate(split(u['text']),1):
  uid=f"{u['unit_id']}_p{i:02}";out.append(dict(u,parent_unit_id=u['unit_id'],unit_id=uid,file=uid+'.wav',text=t,spoken_text=spoken(t),status='prepared_for_free_heami'))
norm=lambda s:re.sub(r'\s+','',s)
assert norm(''.join(u['text'] for u in units))==norm(''.join(u['text'] for u in out))
(E/'units_prepared.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
manifest=dict(source='narration/units_v5.json',source_sha256=hashlib.file_digest((EP/'narration/units_v5.json').open('rb'),'sha256').hexdigest(),approved_unit_count=len(units),generated_phrase_count=len(out),engine='Windows SAPI COM Microsoft Heami Desktop',rate=2,paid_api_calls=0,original_text_preserved=True,caption_timing_basis='Each generated phrase WAV has its own measured PCM duration; long phrase internal cues explicitly estimated if required')
(E/'audio_input_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(manifest,ensure_ascii=False))
