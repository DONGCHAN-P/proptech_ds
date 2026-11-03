"""Choose complete sentence cuts in measured quiet gaps of the locked WAV.
No word/character proportional source cuts, no synthesis. Listening is external.
"""
from pathlib import Path
import argparse,audioop,hashlib,json,wave
H=Path(__file__).resolve().parent;E=H.parents[1]
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
ap=argparse.ArgumentParser();ap.add_argument('--timing',required=True);a=ap.parse_args();T=read(a.timing)
assert T['timing_locked'];src=Path(T['audio_file']);assert hashlib.sha256(src.read_bytes()).hexdigest()==T['audio_sha256']
plan=read(E/'director/top20-production-v1/shorts_story_plan.json');sentences={}
for sc in T['scenes']:
 ss=sc.get('sentence_times',[])
 for i,st in enumerate(ss):sentences[st['sentence_id']]={'text':st['text'],'speech_start':sc['start_s']+st['start_s'],'speech_end':sc['start_s']+st['end_s'],'before':sc['start_s']+(ss[i-1]['end_s'] if i else 0),'after':sc['start_s']+ss[i+1]['start_s'] if i+1<len(ss) else sc['end_s']}
w=wave.open(str(src),'rb');sr=w.getframerate();sw=w.getsampwidth();ch=w.getnchannels()
assert sw==2,'Quiet-gap detector expects provided 16-bit PCM master'
def quiet_mid(lo,hi,default):
 lo=max(0,lo);hi=max(lo,hi);count=max(0,round((hi-lo)*sr));w.setpos(round(lo*sr));data=w.readframes(count);step=max(1,round(sr*.01))*ch*sw
 runs=[];begin=None
 for k in range(0,len(data),step):
  chunk=data[k:k+step];quiet=audioop.rms(chunk,sw)<=65
  if quiet and begin is None:begin=k
  if not quiet and begin is not None:runs.append((begin,k));begin=None
 if begin is not None:runs.append((begin,len(data)))
 runs=[r for r in runs if (r[1]-r[0])/(sr*ch*sw)>=.04]
 if not runs:return default,{'quiet_gap_detected':False,'search':[lo,hi]}
 run=max(runs,key=lambda r:r[1]-r[0]);b=lo+run[0]/(sr*ch*sw);e=lo+run[1]/(sr*ch*sw)
 return (b+e)/2,{'quiet_gap_detected':True,'quiet_span_s':[b,e],'threshold_rms_16bit':65,'window_ms':10}
items=[]
for item in plan['items']:
 clips=[]
 for sid in item['sentence_ids']:
  s=sentences[sid];b,qb=quiet_mid(max(s['before'],s['speech_start']-.30),s['speech_start'],max(s['before'],s['speech_start']-.07))
  e,qe=quiet_mid(s['speech_end'],min(s['after'],s['speech_end']+.36),min(s['after'],s['speech_end']+.12))
  assert b<=s['speech_start'] and e>=s['speech_end']
  clips.append({'sentence_id':sid,'source_start_s':b,'source_end_s':e,'source_speech_start_s':s['speech_start'],'source_speech_end_s':s['speech_end'],'start_boundary':qb,'end_boundary':qe})
 last=clips[-1];tail=last['source_end_s']-last['source_speech_end_s'];duration=sum(c['source_end_s']-c['source_start_s'] for c in clips)+3-tail
 items.append({'id':item['id'],'clips':clips,'last_speech_tail_already_counted_s':tail,'additional_final_hold_s':3-tail,'duration_s':duration})
result={'timing_locked':True,'audio_sha256':T['audio_sha256'],'source_timing':a.timing,'source_audio':str(src),'basis':'complete provider sentence boundaries expanded to measured waveform silence midpoints','actual_listening':False,'note':'Quiet-gap measurements support consonant preservation; not phoneme/listening verification. Final source speech endpoint +3s counts included clip tail once.','items':items}
(H/'shorts_clips_locked.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps([{'id':i['id'],'duration_s':i['duration_s'],'all_quiet_boundaries':all(c['start_boundary']['quiet_gap_detected'] and c['end_boundary']['quiet_gap_detected'] for c in i['clips'])} for i in items]))
