from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,math
e=Path(__file__).resolve().parent;repo=e.parents[2]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
h=read(e/'narration/region-leaders-v7/handoff.json')
assert h['actual_credit_total']==616 and h['submitted_character_total']==1541 and h['requests']==2 and h['retries']==0
assert h['source_script_sha256']==sha(e/'outputs/story-review-v7/script_v7.md')
base=read(repo/'video/src/namyangju-landuse-v8/project_final.json')
chapters=[]
for x in base['narration']:
 if x['scene_id'] not in ['M008','M009']:
  chapters.append({'scene_id':x['scene_id'],'from_frame':x['from_frame'],'duration_frames':x['duration_frames'],'to_frame':x['from_frame']+x['duration_frames'],'audio_sha256':x['sha256'],'audio_revision':x['audio_revision'],'preserved':True})
cursor=21636
for x in h['chapters']:
 assert sha(e/x['file'])==x['sha256']
 frames=math.ceil(x['pcm_duration_s']*30-1e-8);assert frames==x['frames_30fps']
 chapters.append({'scene_id':x['scene_id'],'from_frame':cursor,'duration_frames':frames,'to_frame':cursor+frames,'pcm_duration_s':x['pcm_duration_s'],'audio_file':x['file'],'audio_sha256':x['sha256'],'captions_file':x['captions_file'],'audio_revision':'region-leaders-v7','preserved':False})
 cursor+=frames
assert cursor==27353
lock={'revision':'locator-timeline-v14','script_revision':'script-v7-region-leaders','script_sha256':h['source_script_sha256'],'locked_at':datetime.now(timezone.utc).isoformat(),'timing_basis':'new audio decoded PCM ceil30fps; unchanged prefix actual v13/project_final frame positions','fps':30,'unchanged_prefix_frame_range':[0,21636],'chapters':chapters,'brand_intro':{'from_frame':917,'duration_frames':150},'brand_outro':{'from_frame':cursor,'duration_frames':300},'caption_panel_excluded_frames':[[0,45],[917,1067],[cursor,cursor+300]],'duration_frames':cursor+300,'duration_s':(cursor+300)/30,'new_voice_credits':616,'additional_cash_usd':0,'actual_listening':False}
save(e/'timing_lock_v14.json',lock)
p=e/'scenes.json';s=read(p)
backup=e/'scenes_before_v14.json'
if not backup.exists():save(backup,s)
byid={x['scene_id']:x for x in chapters};newby={x['scene_id']:x for x in h['chapters']}
for x in s['scenes']:
 ident=x['scene_id'];t=byid[ident]
 x.update(start_frame=0 if ident=='M000' else t['from_frame'],end_frame=t['to_frame'],narration_start_frame=t['from_frame'],narration_end_frame=t['to_frame'],script_revision='script-v7-region-leaders',audio_revision=t['audio_revision'],audio_sha256=t['audio_sha256'],timing_basis=lock['timing_basis'],status='timing_locked_render_in_progress')
 x['start_s']=x['start_frame']/30;x['end_s']=x['end_frame']/30
 x['start']=x['start_s'];x['end']=x['end_s']
 for key in ['narration_relative_start_s','narration_relative_end_s']:x.pop(key,None)
 if ident=='M000':
  x.update(audio_file='narration/series-hook-v6/M000.mp3',alignment_file='narration/series-hook-v6/M000.alignment.json',pcm_duration_s=29.04)
 if ident in newby:
  a=newby[ident]
  x.update(narration_text=(e/f'outputs/story-review-v7/{ident}.txt').read_text(encoding='utf-8'),audio_file=a['file'],alignment_file=a['alignment_file'],pcm_duration_s=a['pcm_duration_s'],caption_units=62 if ident=='M008' else 10,visual_instruction='outputs/story-review-v7/script_v7.md; stable relevant whole-plan locator, regional comparison and horizontal dates; no zoom/flash')
  x['title']='지도 분석으로 고른 권역별 대장 후보' if ident=='M008' else '내 생활에서 우선순위가 바뀌는 조건'
  x['message']='북부B1/B2 공동·남부B17·왕숙2A3, A1은 조건부 경쟁 후보; 제한 충족 뒤 일반매매시장 비교'
  x['claim_ids']=['V14-W1-B1','V14-W1-B2','V14-W1-B17','V14-W2-A1','V14-W2-A3']
 s['caption_panel_excluded_frames']=lock['caption_panel_excluded_frames']
s.update(revision='scenes-v14-script-v7-timing-locked',status='timing_locked_render_in_progress',source_script='outputs/story-review-v7/script_v7.md',audio_revision='series-hook-v6+audio-v2-preserved-prefix+region-leaders-v7',duration_frames=lock['duration_frames'],planned_video_duration_s=lock['duration_s'],actual_video_timing='timing_lock_v14.json',timing_lock='timing_lock_v14.json',brand_intro=lock['brand_intro'],brand_outro=lock['brand_outro'],outro_tail_frames=300,visual_revision_target='locator-timeline-v14',visual_revision_scope='whole-plan locators, horizontal date timelines, dual station comparison maps, new ordinary-market regional closing')
s['actual_narration_duration_s']=sum(x['pcm_duration_s'] for x in s['scenes'])
save(p,s)
p=e/'state.json';state=read(p)
state.update(stage='v14_full_render_production',audio_revision=s['audio_revision'],timing_lock='timing_lock_v14.json',actual_video_duration_seconds=lock['duration_s'],new_voice_credits=616,new_voice_submitted_characters=1541,additional_cash_usd=0,new_paid_generation_authorized=False,active_tasks=['editor_full_v14','qa_full_v14'],pending_gate=None,pending_decision_ids={})
save(p,state)
print(json.dumps({'M008':[21636,26592],'M009':[26592,27353],'outro':[27353,27653],'duration_frames':27653,'duration_s':lock['duration_s'],'credits':616}))
