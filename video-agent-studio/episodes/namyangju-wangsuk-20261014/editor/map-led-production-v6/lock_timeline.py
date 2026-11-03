import json,math,shutil,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[5]; E=R/'video-agent-studio/episodes/namyangju-wangsuk-20261014'; H=Path(__file__).parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
p=read(R/'video/src/namyangju-map-led-v6/project.json'); m=read(E/'narration/alignment_manifest_v2.json'); shots=read(H/'shot_templates.json')['shots']; story={s['scene_id']:s for s in read(E/'writer/map-led-v4/scene_plan.json')['scenes']}; caps=read(H/'aligned_captions.json')['chapters']
start=45;p['narration']=[];p['scenes']=[];p['captions']=caps
for c in m['chapters']:
 sid=c['scene_id']; dur=math.ceil(c['pcm_duration_s']*30); src=E/c['file']; dest=R/'video/public/namyangju-map-led-v6'/src.name;shutil.copy2(src,dest)
 assert hashlib.sha256(dest.read_bytes()).hexdigest()==c['sha256']
 p['narration'].append(dict(scene_id=sid,file='namyangju-map-led-v6/'+src.name,from_frame=start,duration_frames=dur,sha256=c['sha256'],script_revision=m['script_revision'],audio_revision='audio-v2'))
 alignment=read(E/c['alignment_file']);a=alignment.get('alignment',alignment); ss=[x.copy() for x in shots if x['scene_id']==sid]
 cuts=[0]+[math.floor(a['character_start_times_seconds'][x['char_start']]*30) for x in ss[1:]]+[dur]
 for i,s in enumerate(ss):
  s.update(from_frame=start+cuts[i],duration_frames=cuts[i+1]-cuts[i],title=story[sid]['title'],message=story[sid]['message'],timing_basis='exact approved TXT character anchor mapped to provider raw timestamps')
  if sid=='M000':s['kind']='intro_hook';s['from_frame']=0;s['duration_frames']+=45
  if sid=='M007B' and s['kind']!='outside_price_comparison':s['kind']='outside_locator';s['message']='교산' if '교산' in s['purpose'] else '창릉'
  if s['kind']=='official_plan':
   # District follows the exact spoken substring, never modulo asset assignment.
   text=''.join(a['characters'][s['char_start']:s['char_end']]); w2='왕숙2' in text and '왕숙1' not in text;s['district']='왕숙2' if w2 else '왕숙1';s['asset_ids']=['PLAN_W2_ORIGINAL' if w2 else 'PLAN_W1_ORIGINAL']
  if s['focus_ids']:
   pts=[b for b in p['map']['block_points'] if b['id'] in s['focus_ids']];span=max(b['lat'] for b in pts)-min(b['lat'] for b in pts)
   zoom=min(2.5,.12/max(.001,span))
   s['camera_keys']=[dict(at=0,focus_ids=[],zoom=1),dict(at=.08,focus_ids=s['focus_ids'],zoom=zoom)]
  p['scenes'].append(s)
 start+=dur
p['duration_frames']=start+270;p['scenes'][-1]['duration_frames']+=270
p.update(revision='map-led-production-v6-timing-locked',timing_locked=True,audio_revision='audio-v2')
last=p['narration'][-1];p['music_regions']=[dict(id='intro-music',from_frame=0,duration_frames=p['narration'][0]['from_frame']+p['narration'][0]['duration_frames'],source_offset_frames=0,gain=.55,duck_gain=.18,fade_in_frames=20,fade_out_frames=60,voice_ranges=[[45,45+p['narration'][0]['duration_frames']]]),dict(id='outro-music',from_frame=last['from_frame'],duration_frames=last['duration_frames']+270,source_offset_frames=960,gain=.48,duck_gain=.18,fade_in_frames=30,fade_out_frames=75,voice_ranges=[[0,last['duration_frames']]])]
save(R/'video/src/namyangju-map-led-v6/project.json',p);save(H/'timing_lock.json',{'source_script_sha256':m['source_script_sha256'],'duration_frames':p['duration_frames'],'narration':p['narration'],'shots':p['scenes'],'music_regions':p['music_regions'],'tail_s':9,'lead_s':1.5,'listening':'not performed'})
def stamp(f):
 ms=round(f/30*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
out=[]; flat=[]
for n in p['narration']:
 for c in caps[n['scene_id']]:
  s=n['from_frame']+c['start_frame'];e=n['from_frame']+c['end_frame'];out.append(f'{len(out)+1}\n{stamp(s)} --> {stamp(e)}\n'+ '\n'.join(c['lines'])+'\n');flat.append(dict(text='\n'.join(c['lines']),startMs=round(s/30*1000),endMs=round(e/30*1000),timestampMs=None,confidence=None))
O=E/'outputs/video-review-v6';O.mkdir(exist_ok=True);(O/'namyangju-map-led_v6.srt').write_text('\n'.join(out),encoding='utf-8');save(O/'captions.json',flat)
print('locked',p['duration_frames'],'frames',len(p['scenes']),'shots',len(flat),'cues')
