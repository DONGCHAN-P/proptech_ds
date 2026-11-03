from pathlib import Path
import json,math,subprocess,io,wave,hashlib
E=Path(__file__).resolve().parent;EP=E.parents[1];R=EP.parents[2];O=EP/'outputs/production-v5-jun';N=EP/'narration/jun-v5-final';F=R/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe'
read=lambda f:json.loads(f.read_text(encoding='utf8'))
def save(f,x):f.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf8')
def sha(f):return hashlib.file_digest(f.open('rb'),'sha256').hexdigest()
def pcm_samples(f):
 z=subprocess.run([str(F),'-v','error','-i',str(f),'-f','wav','-c:a','pcm_s16le','-ac','2','-ar','48000','pipe:1'],capture_output=True);assert not z.returncode,z.stderr
 with wave.open(io.BytesIO(z.stdout),'rb') as w:return len(w.readframes(w.getnframes()))//4
def main():
 baseline=read(EP/'outputs/production-v5/rendered_project.json');raw=read(N/'segments.json');segs=raw if isinstance(raw,list) else raw.get('segments',raw.get('units',raw.get('phrases')));assert isinstance(segs,list)
 by={s['unit_id']:s for s in segs};old=baseline['audio_units'];assert set(by)=={u['unit_id'] for u in old}
 out=[];units=[];tracks=[];cues=[];scenes=[];cursor=0;intro_at=None
 groups={u['unit_id']:[x for x in baseline['visual_intervals'] if x['unit_id']==u['unit_id']] for u in old}
 def append(kind,start,end,props,uid,sid,source=None):
  assert end>start
  x=dict(kind=kind,start_frame=start,end_frame=end,duration_frames=end-start,props=props,unit_id=uid,scene_id=sid)
  if source:x['source_file']=source
  out.append(x)
 def visual(u,a,b):
  rows=groups[u['unit_id']];moving=[x for x in rows if x['duration_frames']==1];n=b-a
  if not moving:append('body',a,b,rows[-1]['props'],u['unit_id'],u['scene_id'],rows[-1]['source_file']);return
  count=min(len(moving),n-1)
  for i in range(count):
   x=moving[round(i*(len(moving)-1)/max(1,count-1))];append('body',a+i,a+i+1,x['props'],u['unit_id'],u['scene_id'],x['source_file'])
  append('body',a+count,b,rows[-1]['props'],u['unit_id'],u['scene_id'],rows[-1]['source_file'])
 for sid in dict.fromkeys(u['scene_id'] for u in old):
  us=[u for u in old if u['scene_id']==sid]
  chapter=next((x for x in baseline['visual_intervals'] if x['scene_id']==sid and x['kind']=='chapter'),None)
  if chapter:append('chapter',cursor,cursor+90,chapter['props'],chapter['unit_id'],sid,chapter['source_file']);cursor+=90
  start=cursor;f=O/'audio'/f'{sid}.wav';assert f.exists();samples=pcm_samples(f);length=math.ceil(samples/1600);cut=None;cut_sample=None
  if sid=='M000':
   boundary=next(i for i,u in enumerate(us) if u['parent_unit_id']=='M000_v4_004');prev=by[us[boundary-1]['unit_id']];nxt=by[us[boundary]['unit_id']]
   lo=prev['scene_local_end_s'];hi=nxt['scene_local_start_s'];assert hi>=lo
   cut_sample=round((lo+hi)/2*48000);cut=round(cut_sample/1600);intro_at=start+cut
   append('intro',intro_at,intro_at+150,{},'brand_intro','brand')
   tracks.extend([dict(scene_id=sid,audio_path=str(f),input_sample_start=0,input_sample_end=cut_sample,start_frame=start,start_sample=start*1600),dict(scene_id=sid,audio_path=str(f),input_sample_start=cut_sample,input_sample_end=samples,start_frame=start+cut+150,start_sample=(start+150)*1600+cut_sample)])
  else:tracks.append(dict(scene_id=sid,audio_path=str(f),input_sample_start=0,input_sample_end=samples,start_frame=start))
  def mapped(t,end=False):
   after=cut_sample is not None and (t*48000>cut_sample if end else t*48000>=cut_sample)
   return start+math.floor(t*30)+(150 if after else 0)
  starts=[mapped(by[u['unit_id']]['scene_local_start_s']) for u in us];starts[0]=start
  if cut is not None:starts[boundary]=intro_at+150
  end=start+length+(150 if cut is not None else 0)
  for i,u in enumerate(us):
   s=by[u['unit_id']];a=starts[i];b=starts[i+1] if i+1<len(us) else end
   if cut is not None and i+1==boundary:b=intro_at
   assert a<b,(u['unit_id'],a,b)
   visual(u,a,b);props=groups[u['unit_id']][-1]['props']
   units.append(dict(u,audio_path=str(f),file=f.name,spoken_text=u['text'],status='aligned_Jun',duration_s=s['scene_local_end_s']-s['scene_local_start_s'],start_frame=mapped(s['scene_local_start_s']),end_frame=mapped(s['scene_local_end_s'],end=True),scene_local_start_s=s['scene_local_start_s'],scene_local_end_s=s['scene_local_end_s'],source_character_start=s['source_character_start'],source_character_end_exclusive=s['source_character_end_exclusive'],timing_basis='Jun original character alignment; no Heami timing reused'))
   cues.append(dict(unit_id=u['unit_id'],start_frame=a,end_frame=b,text=props['caption'],speech_start_frame=mapped(s['scene_local_start_s']),speech_end_frame=mapped(s['scene_local_end_s'],end=True)))
  scenes.append(dict(scene_id=sid,audio_path=str(f),sha256=sha(f),pcm_samples_48000_stereo=samples,duration_s=samples/48000,start_frame=start,end_frame=end,intro_cut_source_frame=cut,intro_cut_source_sample=cut_sample));cursor=end
 narration_end=cursor;hold=next(x for x in baseline['visual_intervals'] if x['unit_id']=='CTA_hold');append('body',cursor,cursor+90,hold['props'],'CTA_hold','ending',hold['source_file']);cursor+=90;outro_start=cursor;append('outro',cursor,cursor+300,{},'brand_outro','brand');cursor+=300
 out.sort(key=lambda x:x['start_frame']);assert out[0]['start_frame']==0 and all(a['end_frame']==b['start_frame'] for a,b in zip(out,out[1:]));assert sum(x['duration_frames'] for x in out)==cursor
 p=dict(baseline,revision='script-v5-Jun-exact-character-alignment',duration_frames=cursor,intro_at=intro_at,outro_start=outro_start,narration_end_frame=narration_end,audio_units=units,narration_tracks=tracks,visual_intervals=out)
 save(O/'rendered_project.json',p);save(O/'timing_locked.json',p);save(O/'caption_cues.json',cues);save(E/'scene_timing.json',scenes)
 def stamp(n):
  ms=round(n/30*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
 (O/'gyosan_v5_jun.srt').write_text('\n\n'.join(f'{i+1}\n{stamp(c["start_frame"])} --> {stamp(c["end_frame"])}\n{c["text"]}' for i,c in enumerate(cues))+'\n',encoding='utf8')
 save(E/'timing_verification.json',dict(passed=True,phrase_count=len(units),scene_count=len(scenes),duration_s=cursor/30,all_full_pcm_samples_preserved=True,brand_intro_frames=150,brand_outro_frames=300,cta_hold_frames=90,png_render_calls=0,reused_source_pngs=len({x['source_file'] for x in out if 'source_file' in x}),alignment_input=str(N/'segments.json'),alignment_sha256=sha(N/'segments.json'),actual_listening=False,continuous_playback=False))
 print(json.dumps(dict(duration_s=cursor/30,phrases=len(units),scenes=len(scenes),render_calls=0)))
if __name__=='__main__':main()
