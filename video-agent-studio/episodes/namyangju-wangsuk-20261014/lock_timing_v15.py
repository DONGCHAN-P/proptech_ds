from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,math
e=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
h=read(e/'narration/cta-v8/handoff.json');m=read(e/'outputs/story-review-v8/manifest.json')
assert h['source_script_sha256']==m['source_script_sha256']==sha(e/m['script_path'])
assert sha(e/h['file'])==h['sha256'] and h['actual_credits']==24 and h['submitted_characters']==59
assert h['post_requests']==1 and h['retries']==0 and h['pcm_duration_s']==7.44 and h['actual_speech_end_s']==7.2
base=read(e/'timing_lock_v14.json');start=base['brand_outro']['from_frame'];assert start==27353
spoken_end=start+round(h['actual_speech_end_s']*30)
outro=spoken_end+90;end=outro+300
assert outro==27659 and end==27959
lock={**base,'revision':'readability-cta-v15','script_revision':'script-v8-user-literal-CTA','script_sha256':m['source_script_sha256'],'locked_at':datetime.now(timezone.utc).isoformat(),'unchanged_audio_prefix_frame_range':[0,27353],'unchanged_existing_caption_count':301,'new_caption_count':4,'total_caption_count':305,'brand_outro':{'from_frame':outro,'duration_frames':300},'duration_frames':end,'duration_s':end/30,'new_voice_credits':24,'additional_cash_usd':0,'caption_panel_excluded_frames':[[0,45],[917,1067],[start+h['frames_30fps'],end]],'post_speech_hold':{'from_frame':spoken_end,'to_frame':outro,'duration_frames':90,'basis':'provider original alignment last spoken alphanumeric character end; not actual listening','spoken_end_relative_s':7.2,'complete_PCM_retained_s':7.44,'PCM_tail_within_hold_s':0.24,'additional_silence_after_PCM_s':2.76,'no_speech_trimmed':True},'audio_total_samples_48000':end*1600}
lock['chapters']=base['chapters']+[{'scene_id':'M010','from_frame':start,'to_frame':start+h['frames_30fps'],'duration_frames':h['frames_30fps'],'pcm_duration_s':7.44,'last_spoken_end_frame':spoken_end,'audio_file':h['file'],'audio_sha256':h['sha256'],'captions_file':h['captions_file'],'audio_revision':'cta-v8','preserved':False,'visual_end_frame':outro}]
save(e/'timing_lock_v15.json',lock)
p=e/'scenes.json';s=read(p)
backup=e/'scenes_before_v15.json'
if not backup.exists():save(backup,s)
s.update(revision='scenes-v15-script-v8-timing-locked',status='timing_locked_render_in_progress',source_script=m['script_path'],audio_revision='v14-all-audio-preserved+cta-v8',timing_lock='timing_lock_v15.json',actual_video_timing='timing_lock_v15.json',duration_frames=end,planned_video_duration_s=end/30,brand_outro=lock['brand_outro'],caption_panel_excluded_frames=lock['caption_panel_excluded_frames'],visual_revision_target='readability-cta-v15',visual_revision_scope='global timeline clipping, jobs locator, Wangsuk/Ilpae inset narrative switch, south label leaders, literal CTA icon motion and3s speech-end hold',caption_count=305)
for x in s['scenes']:x['script_revision']='script-v8-user-literal-CTA'
s['scenes'].append({'scene_id':'M010','title':'구독·좋아요와 시청 감사','message':'사용자 지정 마무리 멘트와 절제된 아이콘 모션 뒤 3초 유지','narration_text':(e/m['text_path']).read_text(encoding='utf-8'),'claim_ids':[],'material_types':['vector_motion','narration'],'asset_ids':['SUBSCRIBE_EMOJI','LIKE_EMOJI'],'script_revision':'script-v8-user-literal-CTA','audio_revision':'cta-v8','audio_file':h['file'],'audio_sha256':h['sha256'],'alignment_file':h['alignment_file'],'pcm_duration_s':7.44,'start_frame':start,'end_frame':outro,'narration_start_frame':start,'narration_end_frame':start+h['frames_30fps'],'last_spoken_end_frame':spoken_end,'start_s':start/30,'end_s':outro/30,'fps':30,'caption_units':4,'timing_basis':'decoded PCM plus provider last spoken character end; 90-frame post-speech hold','status':'timing_locked_render_in_progress','visual_instruction':'User literal CTA with 🔔/👍 restrained entrance and hold; no mapzoom; hide empty caption box afterM010PCM; brand starts3s after final spoken character'})
save(p,s)
p=e/'state.json';s=read(p)
s.update(stage='v15_visual_render_production',audio_revision='v14-all-audio-preserved+cta-v8',timing_lock='timing_lock_v15.json',actual_video_duration_seconds=end/30,new_voice_credits=24,new_voice_submitted_characters=59,new_paid_generation_authorized=False,additional_cash_usd=0,active_tasks=['editor_readability_cta_v15','qa_readability_cta_v15'],caption_count=305)
save(p,s)
print(json.dumps({'CTA_start_frame':start,'last_spoken_end_frame':spoken_end,'outro':[outro,end],'duration_frames':end,'duration_s':end/30,'PCM_tail_preserved':True,'credits':24}))
