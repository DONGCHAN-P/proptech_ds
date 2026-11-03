import json,hashlib,math
from pathlib import Path
root=Path(__file__).resolve().parents[1];ep=root/'video-agent-studio/episodes/goyang-changneung-20261015'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
m=read(ep/'narration/audio-v3/alignment_manifest_v3.json');t=read(ep/'narration/audio-v3/timing_proposals_v3.json');ledger=read(ep/'narration/audio-v3/generation_ledger_v3.json')
assert len(m['chapters'])==10 and all(r['status']=='complete' for r in ledger['requests'])
assert ledger['actual_credit_total']<=7661
fps=30;segments=[];chapters=[];cursor=0
def push(kind,n,**fields):
 global cursor
 row={'kind':kind,'start_frame':cursor,'duration_frames':n,'end_frame':cursor+n,**fields};segments.append(row);cursor+=n;return row
for i,(a,b) in enumerate(zip(m['chapters'],t['scenes'])):
 assert a['scene_id']==b['scene_id'] and sha(ep/a['file'])==a['sha256']
 start=cursor
 common={'scene_id':a['scene_id'],'audio_file':a['file'],'audio_sha256':a['sha256'],'alignment_file':a['alignment_file'],'caption_cues_file':b['caption_cues_file']}
 if i==0:
  alignment=read(ep/a['alignment_file']);text=''.join(alignment['characters']);split=text.index('\n');j=split+1
  while text[j].isspace():j+=1
  end=max(alignment['character_end_times_seconds'][:split]);nxt=alignment['character_start_times_seconds'][j]
  cut_frame=round(((end+nxt)/2)*fps);cut_s=cut_frame/fps
  assert end<=cut_s<=nxt,(end,cut_s,nxt)
  push('narration',cut_frame,audio_start_s=0,audio_end_s=cut_s,**common)
  push('brand_intro',150,file='outputs/editor-preflight-v1/brand_intro_generic_v1.mp4',captions_visible=False)
  push('narration',math.ceil((a['pcm_duration_s']-cut_s)*fps-1e-7),audio_start_s=cut_s,audio_end_s=a['pcm_duration_s'],**common)
  mapping={'split_source_s':cut_s,'brand_insert_frames':150}
 else:
  push('narration',math.ceil(a['pcm_duration_s']*fps-1e-7),audio_start_s=0,audio_end_s=a['pcm_duration_s'],**common);mapping={}
 chapters.append({'scene_id':a['scene_id'],'start_frame':start,'end_frame':cursor,'pcm_duration_s':a['pcm_duration_s'],'provider_last_spoken_end_s':b['provider_last_spoken_end_s'],**mapping})
last=chapters[-1];last_spoken_frame=last['start_frame']+math.ceil(last['provider_last_spoken_end_s']*fps-1e-7)
outro_start=last_spoken_frame+90
assert outro_start>=cursor
push('cta_silent_hold',outro_start-cursor,scene_id='M009',captions_visible=False)
push('brand_outro',300,file='outputs/editor-preflight-v1/brand_outro_generic_v1.mp4',captions_visible=False)
lock={'revision':'timing-lock-v3','script_revision':'script-v3','audio_revision':'audio-v3','source_script_sha256':m['source_script_sha256'],'fps':fps,'width':1920,'height':1080,'duration_frames':cursor,'duration_s':cursor/fps,'chapters':chapters,'segments':segments,'last_provider_spoken_frame':last_spoken_frame,'outro_start_frame':outro_start,'outro_gap_frames':90,'timing_basis':'decoded PCM, same source audio preserved, per-segment frame ceiling, provider original-character speech end; not actual listening','actual_listening':False,'continuous_playback':False}
out=ep/'editor/production-v3';out.mkdir(parents=True,exist_ok=True);write(out/'timing_lock_v3.json',lock)
sc=read(ep/'scenes.json')
for s,c in zip(sc['scenes'],chapters):s.update(start_s=c['start_frame']/fps,end_s=c['end_frame']/fps,start_frame=c['start_frame'],end_frame=c['end_frame'],audio_revision='audio-v3',timing_basis=lock['timing_basis'],status='timing_locked')
sc.update(timing_status='locked_from_actual_audio_v3',status='editor_production',revision='script-v3-timing-lock-v3');write(ep/'scenes.json',sc)
s=read(ep/'state.json');s.update(stage='editor_production_v3',audio_revision='audio-v3',actual_voice_credits_used=ledger['actual_credit_total'],timing_revision='timing-lock-v3',active_tasks=['editor_production_v3','final_QA_when_render_ready']);write(ep/'state.json',s)
print(json.dumps({'frames':cursor,'duration_s':cursor/fps,'hook_cut_s':chapters[0]['split_source_s'],'outro_gap_frames':90,'credits':ledger['actual_credit_total']}))
