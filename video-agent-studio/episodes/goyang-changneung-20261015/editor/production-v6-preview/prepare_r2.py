from pathlib import Path
import json,wave,numpy as np
E=Path(__file__).resolve().parent;EP=E.parent.parent;O=EP/'outputs/production-v6-preview'
p=json.loads((O/'rendered_project.json').read_text(encoding='utf-8'));units=json.loads((EP/'narration/preview-v6/segments.json').read_text(encoding='utf-8'));last=units[-1]
with wave.open(last['audio_path'],'rb') as w:
 sr=w.getframerate();a=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(float)/32768
signal_index=int(np.where(np.abs(a)>.006)[0][-1])+1
signal_global_s=last['start_s']+signal_index/sr+5
signal_frame=round(signal_global_s*30);new_outro=signal_frame+90;delta=p['outro_start']-new_outro
assert delta==25,(delta,signal_frame)
p['revision']='production-v6-preview-r2';p['outro_start']-=delta;p['duration_frames']-=delta;p['signal_end_frame']=signal_frame;p['hold_frames_after_file_end']=90-delta
for rows in [p['intervals'],p['visual_intervals']]:
 for v in rows:
  if v['scene_id']=='CTA_HOLD':v['start_frame']=signal_frame;v['end_frame']=new_outro;v['duration_frames']=90
  elif v['start_frame']<signal_frame<v['end_frame']:v['end_frame']=signal_frame;v['duration_frames']=signal_frame-v['start_frame']
(O/'rendered_project_r2.json').write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf-8');(O/'project_r2.json').write_text(json.dumps({k:v for k,v in p.items() if k!='visual_intervals'},ensure_ascii=False,indent=2),encoding='utf-8')
evidence={'basis':'last PCM sample with absolute amplitude >0.006 (-44.44dBFS), not actual listening','threshold':.006,'last_unit_file':last['file'],'sample_rate':sr,'last_active_sample_exclusive':signal_index,'tail_s':(len(a)-signal_index)/sr,'signal_global_s':signal_global_s,'signal_end_frame':signal_frame,'outro_start_frame':new_outro,'signal_end_to_outro_frames':90,'voice_file_end_frame':p['speech_end_frame'],'preserved_pcm_tail':True,'hold_after_file_end_frames':90-delta,'delta_frames_from_r1':delta,'duration_frames':p['duration_frames']}
(O/'cta_signal_r2.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
src=(E/'assemble.py').read_text(encoding='utf-8').replace("cache/assembly'","cache/assembly_r2'").replace("rendered_project.json'","rendered_project_r2.json'").replace("full_mix.m4a'","full_mix_r2.m4a'").replace("changneung_full_v6_preview.mp4'","changneung_full_v6_preview_r2.mp4'").replace("technical.json'","technical_r2.json'").replace("final_proofs'","final_proofs_r2'").replace("'hold_frames':90","'hold_frames':65,'signal_end_frame':p['signal_end_frame'],'signal_basis':'PCM abs>0.006; see cta_signal_r2.json'")
src=src.replace("gain[outro_at:]=0;mix+=music*gain[:,None]","gain[outro_at:]=0;gain[max(0,split-48000):split]*=np.linspace(1,0,min(48000,split));gain[max(0,outro_at-72000):outro_at]*=np.linspace(1,0,min(72000,outro_at));mix+=music*gain[:,None]")
src=src.replace("def pcm(src):return np.frombuffer(ff(['-i',src,'-f','f32le','-ac','2','-ar','48000','pipe:1']),dtype=np.float32).reshape(-1,2).copy()", "def pcm(src):\n import io\n data=ff(['-i',src,'-f','wav','-c:a','pcm_s16le','-ac','2','-ar','48000','pipe:1'])\n with wave.open(io.BytesIO(data),'rb') as w:\n  assert w.getnchannels()==2 and w.getframerate()==48000\n  return np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(np.float32).reshape(-1,2)/32768")
src=src.replace("'-b:a','192k',O/'full_mix_r2.m4a'","'-b:a','192k','-f','mp4',O/'full_mix_r2.m4a'")
src=src.replace("'-vf','fps=30,format=yuv420p'","'-r','30','-pix_fmt','yuv420p'")
src=src.replace("ff(['-i',out,'-f','null','-'])","pass # full stream decode is performed by verify_r2.py with ffprobe -count_frames")
src=src.replace("'decode_exit_code':0","'decode_exit_code':None,'decode_deferred_to':'verify_r2.py'")
(E/'assemble_r2.py').write_text(src,encoding='utf-8');print(f'r2: {p["duration_frames"]} frames, signal-to-outro90f, file-end hold65f')
