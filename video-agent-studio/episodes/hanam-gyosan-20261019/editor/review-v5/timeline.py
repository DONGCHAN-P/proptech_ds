from pathlib import Path
import json,wave,math,re,hashlib,unicodedata
E=Path(__file__).resolve().parent;EP=E.parents[1];O=EP/'outputs/production-v5';units=json.loads((E/'units_prepared.json').read_text(encoding='utf8'));scenes=json.loads((EP/'writer/scenes_v5.json').read_text(encoding='utf8'));info={s['scene_id']:s for s in scenes};intervals=[];audio=[];cues=[];cursor=0;last=None;intro_at=None
def width(s):return sum(1 if unicodedata.east_asian_width(c) in 'WF' else .34 if c.isspace() else .56 for c in s)
def wrap(s):
 if width(s)<=34:return s
 protected=[(m.start(),m.end()) for m in re.finditer(r'\d{4}년\s+\d{1,2}월(?:\s+\d{1,2}일)?|\d+층\s+이상|전용\s+\d+(?:\.\d+)?㎡',s)]
 cand=[m.start() for m in re.finditer(r'\s+',s) if not any(a<m.start()<b for a,b in protected)]
 if not cand:return s
 n=min(cand,key=lambda n:max(width(s[:n]),width(s[n:]))+abs(width(s[:n])-width(s[n:]))*.05)
 return s[:n].rstrip()+'\n'+s[n:].lstrip()
def put(kind,n,props,uid,sid):
 global cursor
 intervals.append(dict(kind=kind,start_frame=cursor,end_frame=cursor+n,duration_frames=n,props=props,unit_id=uid,scene_id=sid));cursor+=n
for u in units:
 s=info[u['scene_id']]
 if u['scene_id']!=last:
  if s.get('chapter'):put('chapter',90,dict(mode='chapter',title=s['title'],active=s['chapter']),u['scene_id']+'_chapter',u['scene_id'])
  last=u['scene_id']
 if u['parent_unit_id']=='M000_v4_004' and intro_at is None:
  intro_at=cursor;put('intro',150,{},'brand_intro','brand')
 f=O/'audio'/u['file']
 with wave.open(str(f),'rb') as w:duration=w.getnframes()/w.getframerate();assert w.getnframes()>0
 n=math.ceil(duration*30);start=cursor
 audio.append(dict(u,audio_path=str(f.resolve()),start_frame=start,end_frame=start+n,duration_s=duration,timing_basis='Actual PCM phrase WAV duration; one phrase caption per newly generated file'))
 props={**u['visual'],'title':u['visual'].get('title',s['title']),'caption':wrap(u['text']),'source':u['visual'].get('source',s.get('source','공식 자료 · 조회2026.10.20')),'parent_unit_id':u['parent_unit_id'],'phrase_text':u['text']}
 put('body',n,props,u['unit_id'],u['scene_id']);cues.append(dict(start_frame=start,end_frame=cursor,text=props['caption'],unit_id=u['unit_id'],parent_unit_id=u['parent_unit_id']))
lastprops={**intervals[-1]['props'],'caption':'','hideCaption':True};put('body',90,lastprops,'CTA_hold','ending');outro_start=cursor;put('outro',300,{},'brand_outro','brand')
project=dict(episode_id=EP.name,revision='script-v5-free-heami',fps=30,width=1920,height=1080,duration_frames=cursor,intro_at=intro_at,outro_start=outro_start,audio_units=audio,visual_intervals=intervals,paid_api_calls=0,continuous_playback=False,actual_listening=False)
(O/'timing_locked.json').write_text(json.dumps(project,ensure_ascii=False,indent=2),encoding='utf8');(O/'caption_cues.json').write_text(json.dumps(cues,ensure_ascii=False,indent=2),encoding='utf8')
captions=[dict(text=c['text'],startMs=c['start_frame']/30*1000,endMs=c['end_frame']/30*1000,timestampMs=None,confidence=None) for c in cues];(O/'captions_remotion.json').write_text(json.dumps(captions,ensure_ascii=False,indent=2),encoding='utf8')
def stamp(n):
 ms=round(n/30*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
(O/'gyosan_v5.srt').write_text('\n\n'.join(f'{i+1}\n{stamp(c["start_frame"])} --> {stamp(c["end_frame"])}\n{c["text"]}' for i,c in enumerate(cues))+'\n',encoding='utf8')
norm=lambda s:re.sub(r'\s+','',s)
assert norm(''.join(c['text'] for c in cues))==norm(''.join(u['text'] for u in units));assert intro_at is not None
(E/'timing_verification.json').write_text(json.dumps(dict(passed=True,phrase_wav_count=len(audio),caption_count=len(cues),original_text_preserved=True,duration_s=cursor/30,voice_end_frame=audio[-1]['end_frame'],cta_hold_frames=outro_start-audio[-1]['end_frame'],brand_intro_frames=150,brand_outro_frames=300,audio_stream_sha256={u['file']:hashlib.file_digest(Path(u['audio_path']).open('rb'),'sha256').hexdigest() for u in audio},max_caption_line_width_em=max(width(line) for c in cues for line in c['text'].splitlines())),ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(dict(duration_s=cursor/30,phrase_wavs=len(audio),cues=len(cues),cta_hold_frames=90)))
