from pathlib import Path
import json,re,hashlib,wave,math,numpy as np
E=Path(__file__).resolve().parent;EP=E.parent.parent;R=EP.parents[2];O=EP/'outputs/production-v8-jun';O.mkdir(exist_ok=True)
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
old=read(EP/'narration/preview-v8/segments.json');base=read(EP/'outputs/production-v8-labels/rendered_project_v8.json');packet=read(EP/'writer/revision-v8/narration_packet.json')
diff=read(EP/'outputs/production-v8-labels/affected_ranges.json')['caption_diff'];undiff={x['after']:x['before'] for x in diff}
intervals=[];audio=[];scenes=[];mapping=[];cursor=0;intro=None
def norm(t):return re.sub(r'\s','',t)
for scene in packet['scenes']:
 s=scene['scene_id'];us=[x for x in old if x['scene_id']==s];a=read(EP/f'narration/jun-v8-final/{s}.alignment.json');text=''.join(a['characters']);assert text==scene['text']
 positions=[];pos=0
 for u in us:
  i=text.index(u['text'],pos);assert not text[pos:i].strip();positions.append(i);pos=i+len(u['text'])
 assert not text[pos:].strip()
 # Preserve approved visual meaning using exact approved sentence equality, never unit-number inference.
 card=next((x for x in base['visual_intervals'] if x['unit_id']==s+'_chapter'),None)
 if card:intervals.append(dict(start_frame=cursor,end_frame=cursor+90,duration_frames=90,props=card['props'],kind='chapter',unit_id=s+'_chapter'));cursor+=90
 scenes.append(dict(scene_id=s,start_frame=cursor,chapter=card['props'].get('chapter') if card else None))
 wav=O/f'audio/{s}.wav'
 with wave.open(str(wav),'rb') as w:
  sr=w.getframerate();raw=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2');duration=len(raw)/sr
 signal=np.flatnonzero(np.abs(raw.astype(np.int32))>32768*10**(-60/20));last_signal=(int(signal[-1])+1)/sr if len(signal) else 0
 for k,u in enumerate(us):
  sa=0 if k==0 else a['character_start_times_seconds'][positions[k]];sb=duration if k==len(us)-1 else a['character_start_times_seconds'][positions[k+1]]
  if s=='M000' and k==4:
   intro=cursor;intervals.append(dict(start_frame=cursor,end_frame=cursor+150,duration_frames=150,props={},kind='intro',unit_id='brand_intro'));cursor+=150
  start=cursor;end=start+round(sb*30)-round(sa*30);assert end>start
  audio.append(dict(unit_id=u['unit_id'],audio_path=str(wav),start_frame=start,end_frame=end,original_start_s=sa,original_end_s=sb))
  rows=[]
  for x in base['visual_intervals']:
   if x.get('unit_id')!=u['unit_id']:continue
   props=dict(x['props']);props.pop('motionFrame',None)
   if rows and props==rows[-1]:continue
   rows.append(props)
  assert rows
  assert norm(''.join(undiff.get(x['caption'],x['caption']) for x in rows))==norm(u['text']),u['unit_id']
  # Find each displayed meaning clause in source and map its onset to API character timing.
  offset=positions[k];cuts=[start]
  for q in rows[:-1]:
   original=undiff.get(q['caption'],q['caption']);needle=norm(original);got='';j=offset
   while len(got)<len(needle):
    if not text[j].isspace():got+=text[j]
    j+=1
   assert got==needle;offset=j
   while offset<len(text) and text[offset].isspace():offset+=1
   cuts.append(max(start,min(end, start+round((a['character_start_times_seconds'][offset]-sa)*30))))
  cuts.append(end)
  pending=[dict(start_frame=cuts[j],end_frame=cuts[j+1],duration_frames=cuts[j+1]-cuts[j],props=q,kind='body',unit_id=u['unit_id'],scene_id=s,timing_basis='ElevenLabs original character alignment, frame rounded') for j,q in enumerate(rows)]
  while len(pending)>1 and any(x['duration_frames']<30 for x in pending):
   j=next(i for i,x in enumerate(pending) if x['duration_frames']<30);left=max(0,j-1);x,y=pending[left:left+2];x['end_frame']=y['end_frame'];x['duration_frames']=x['end_frame']-x['start_frame'];x['props']['caption']+=' '+y['props']['caption'];pending.pop(left+1)
  assert all(x['duration_frames']>=30 for x in pending)
  intervals+=pending;mapping.append(dict(scene_id=s,unit_id=u['unit_id'],exact_source_text=u['text'],source_char_start=positions[k],source_char_end=positions[k]+len(u['text']),audio_start_s=sa,audio_end_s=sb,new_start_frame=start,new_end_frame=end))
  if k==len(us)-1:signal_end=start/30+last_signal-round(sa*30)/30
  cursor=end
outro=max(cursor,math.ceil((signal_end+3)*30));hold=next(x for x in base['visual_intervals'] if x['unit_id']=='last_hold');props=dict(hold['props']);props.pop('motionFrame',None)
intervals+=[dict(start_frame=cursor,end_frame=outro,duration_frames=outro-cursor,kind='body',unit_id='last_hold',props=props),dict(start_frame=outro,end_frame=outro+300,duration_frames=300,kind='outro',unit_id='brand_outro',props={})]
captions=[dict(start_frame=x['start_frame'],end_frame=x['end_frame'],text=x['props']['caption'],unit_id=x['unit_id']) for x in intervals if x['kind']=='body' and x['props'].get('caption')]
p=dict(revision='production-v8-jun',fps=30,duration_frames=outro+300,intro_at=intro,outro_start=outro,signal_end_s=signal_end,audio_units=audio,visual_intervals=intervals,captions=captions,scenes=scenes,audio_revision='audio-v8-jun',internal_caption_alignment='ElevenLabs original character alignment; semantic phrase boundaries; frame rounding and >=1s merges',script_sha256=hashlib.sha256((EP/'outputs/script-review-v8/script_v8.md').read_bytes()).hexdigest())
(O/'project_v8_jun.json').write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf-8');(E/'semantic_alignment.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2),encoding='utf-8')
(O/'captions.json').write_text(json.dumps([dict(text=x['text'],startMs=x['start_frame']/30*1000,endMs=x['end_frame']/30*1000,timestampMs=None,confidence=None)for x in captions],ensure_ascii=False,indent=2),encoding='utf-8')
def ts(f):
 ms=round(f/30*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
(O/'changneung_v8_jun.srt').write_text('\n\n'.join(f'{i+1}\n{ts(x["start_frame"])} --> {ts(x["end_frame"])}\n{x["text"]}'for i,x in enumerate(captions))+'\n',encoding='utf-8')
(O/'scene_proposal.json').write_text(json.dumps(dict(scenes=scenes,duration_frames=outro+300,outro_start=outro,speech_signal_end_s=signal_end),ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(frames=p['duration_frames'],captions=len(captions),signal_end_s=signal_end)))
