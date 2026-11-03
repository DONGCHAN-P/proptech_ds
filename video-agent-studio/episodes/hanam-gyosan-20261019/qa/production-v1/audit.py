from pathlib import Path
import json,hashlib,wave,numpy as np,re
Q=Path(__file__).resolve().parent;EP=Q.parents[1];O=EP/'outputs/production-v1'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
p=read(O/'project.json');s=read(EP/'writer/scenes_v1.json');f=read(EP/'research/facts.json');r=read(EP/'research/script_v1_fact_pass_receipt.json');ids={x['claim_id']for x in f['facts']}
missing=[(x['scene_id'],c)for x in s for u in x['units']for c in u['claim_ids']if c not in ids]
digest=lambda x:hashlib.file_digest(x.open('rb'),'sha256').hexdigest()
unchanged={str(Path(x).name):digest(Path(x))==h for x,h in r['input_hashes'].items() if Path(x).name!='scenes_v1.json'}
g=read(O/'layout_guard.json');a=p['audio_units'];body=[x for x in p['visual_intervals']if x['kind']=='body'and x['props'].get('caption')]
caption_bounds=[]
for u in a:
 xs=[x for x in body if x['unit_id']==u['unit_id']];caption_bounds.append({'unit_id':u['unit_id'],'start_match':min(x['start_frame']for x in xs)==u['start_frame'],'end_match':max(x['end_frame']for x in xs)==u['end_frame']})
with wave.open(str(Path(a[-1]['audio_path'])),'rb')as w:
 data=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2');sr=w.getframerate();ch=w.getnchannels();nz=np.where(abs(data)>100)[0];last_activity=(nz[-1]+1)/sr/ch if len(nz)else None
with wave.open(str(O/'full_mix.wav'),'rb')as w:
 mix=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2');peak=int(np.max(np.abs(mix.astype(np.int32))))
out={'independent_reference_audit':{'unchanged_script_and_facts':unchanged,'missing_claim_ids':missing,'note':'scenes references corrected, wording facts receipt inherited only for unchanged narration MD and facts'},'layout':{'checks':len(g['checks']),'failed':sum(not x['passed']for x in g['checks']),'overlaps':sum(len(x['overlaps'])for x in g['checks']),'text_overflow':sum(len(x['textOverflow'])for x in g['checks']),'svg_clipped':sum(len(x['svgClipped'])for x in g['checks'])},'captions':{'cues':len(body),'units':len(a),'unit_boundary_failures':[x for x in caption_bounds if not(x['start_match']and x['end_match'])],'internal_word_alignment':'estimated_not_listened'},'audio':{'source_last_activity_relative_s':last_activity,'source_last_activity_global_s':a[-1]['start_frame']/30+last_activity,'last_pcm_end_s':a[-1]['end_frame']/30,'last_caption_end_s':body[-1]['end_frame']/30,'outro_start_s':p['outro_start']/30,'gap_s':(p['outro_start']-a[-1]['end_frame'])/30,'master_peak_int16':peak,'actual_listening':False},'continuous_playback':False,'real_device':False}
(Q/'audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(out,ensure_ascii=False))

