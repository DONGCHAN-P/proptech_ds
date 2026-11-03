from pathlib import Path
import json,wave,math,re,hashlib
EP=Path(__file__).resolve().parents[1];O=EP/'outputs/production-v1';N=EP/'narration';units=json.loads((N/'units.json').read_text(encoding='utf8'));scenes=json.loads((EP/'writer/scenes_v1.json').read_text(encoding='utf8'));sceneinfo={s['scene_id']:s for s in scenes};intervals=[];audio=[];cues=[];cursor=0;last=None;intro_at=None
def put(kind,n,props,uid,sid):
 global cursor
 intervals.append(dict(kind=kind,start_frame=cursor,end_frame=cursor+n,duration_frames=n,props=props,unit_id=uid,scene_id=sid));cursor+=n
def chunks(text):
 a=re.split(r'(?<=[,，])\s+|(?<=습니다.)\s+|(?<=입니다.)\s+',text);out=[]
 for t in a:
  if len(t)>58:
   bits=re.split(r'(?<=고)\s+|(?<=며)\s+|(?<=면)\s+|(?<=에서)\s+',t);cur=''
   for b in bits:
    if cur and len(cur)+len(b)>58:out.append(cur);cur=b
    else:cur=(cur+' '+b).strip()
   if cur:out.append(cur)
  elif t:out.append(t)
 return out or [text]
for i,u in enumerate(units):
 s=sceneinfo[u['scene_id']]
 if u['scene_id']!=last:
  if s.get('chapter'):put('chapter',90,dict(mode='chapter',title=s['title'],active=s['chapter']),u['scene_id']+'_chapter',u['scene_id'])
  last=u['scene_id']
 if i==3:
  intro_at=cursor;put('intro',150,{},'brand_intro','brand')
 f=O/'audio'/u['file']
 with wave.open(str(f),'rb')as w:duration=w.getnframes()/w.getframerate();params=w.getparams()
 n=math.ceil(duration*30);start=cursor;end=start+n
 audio.append(dict(**u,audio_path=str(f.resolve()),start_frame=start,end_frame=end,duration_s=duration,timing_basis='PCM file duration semantic unit; internal caption split estimated'))
 parts=chunks(u['text']);weights=[len(re.sub(r'\s','',x))for x in parts];pos=start
 for j,t in enumerate(parts):
  ce=end if j==len(parts)-1 else start+round(n*sum(weights[:j+1])/sum(weights));props={**u['visual'],'title':u['visual'].get('title',s['title']),'caption':t,'source':u['visual'].get('source',s.get('source','공식 자료 · 조회 2026.10.19'))}
  put('body',ce-pos,props,u['unit_id'],u['scene_id']);cues.append(dict(start_frame=pos,end_frame=ce,text=t,unit_id=u['unit_id']));pos=ce
assert intro_at is not None
lastprops={**intervals[-1]['props'],'caption':'','hideCaption':True};put('body',90,lastprops,'CTA_hold','ending');outro_start=cursor;put('outro',300,{},'brand_outro','brand')
project=dict(episode_id=EP.name,fps=30,width=1920,height=1080,duration_frames=cursor,intro_at=intro_at,outro_start=outro_start,audio_units=audio,visual_intervals=intervals,paid_api_calls=0,continuous_playback=False,actual_listening=False)
(O/'project.json').write_text(json.dumps(project,ensure_ascii=False,indent=2),encoding='utf8')
(N/'segments.json').write_text(json.dumps(audio,ensure_ascii=False,indent=2),encoding='utf8')
def stamp(n):
 ms=round(n/30*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
(O/'gyosan_v1.srt').write_text('\n\n'.join(f'{i+1}\n{stamp(c["start_frame"])} --> {stamp(c["end_frame"])}\n{c["text"]}'for i,c in enumerate(cues))+'\n',encoding='utf8')
print(json.dumps(dict(duration_s=cursor/30,units=len(audio),cues=len(cues),ten_minutes=cursor>=18000)))
