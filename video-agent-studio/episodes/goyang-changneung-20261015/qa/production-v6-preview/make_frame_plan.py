from pathlib import Path
import json
E=Path('video-agent-studio/episodes/goyang-changneung-20261015'); q=E/'qa/production-v6-preview';p=json.loads((E/'outputs/production-v6-preview/project.json').read_text(encoding='utf-8'))
frames={}
def add(f,why):
 if 0<=f<p['duration_frames']:frames.setdefault(f,[]).append(why)
for s in p['scenes']:
 add((s['start_frame']+s['end_frame'])//2,s['scene_id']+' midpoint')
 for f in (s['start_frame'],s['end_frame']):
  for d in (-1,0,1):add(f+d,s['scene_id']+' scene boundary')
prev=None
for i in p['intervals']:
 key=i['board_key']
 if key!=prev:
  for d in (-1,0,1):add(i['start_frame']+d,i['scene_id']+' board boundary '+key)
  add(min(i['end_frame']-1,i['start_frame']+60),i['scene_id']+' stable board '+key)
 prev=key
for f in (p['intro_at'],p['intro_at']+p['intro_frames'],p['speech_end_frame'],p['outro_start'],p['duration_frames']-1):
 for d in (-1,0,1):add(f+d,'brand/hold boundary')
for i in p['intervals']:
 c=i['props'].get('caption','')
 if any(x in c for x in ('8억 7,300만','8억 5,000만','8억 3,800만')):add((i['start_frame']+i['end_frame'])//2,'QAV6-002 fix '+c)
(q/'frame_plan.json').write_text(json.dumps([{'frame':f,'time_s':f/30,'reason':why} for f,why in sorted(frames.items())],ensure_ascii=False,indent=2),encoding='utf-8')
print('Exact encoded-frame plan:',len(frames))
