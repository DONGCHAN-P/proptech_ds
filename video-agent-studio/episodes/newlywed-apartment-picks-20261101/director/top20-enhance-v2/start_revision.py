"""Record this authorized enhancement without altering the previous release."""
from pathlib import Path
import copy, datetime, hashlib, json

HERE=Path(__file__).resolve().parent
EP=HERE.parents[1]
ROOT=EP.parents[2]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,j):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

state=read(EP/'state.json')
previous=HERE/'previous_state.json'
if not previous.exists():save(previous,state)
save(HERE/'authorization.json',{
 'user_request':'영상 비주얼적인 퀄리티 올리는 작업을 진행해주고, 본편 길이를 8분 넘기도록 정보 제공하는 부분을 더해줘',
 'scope':'enhance existing main; additional factual explanation and matching visuals; local revised deliverables',
 'voice':'same previously selected free Edge InJoon voice for additions; original audio preserved',
 'paid_generation_authorized':False,'cash_cap_krw':0,'new_upload_or_delete_this_revision':False,
 'previous_main':state['video'],'previous_main_sha256':state['video_sha256'],
 'previous_uploads_preserved':[state['youtube_video_id']]+[s['video_id']for s in state['shorts']],
 'date_kst':'2026-11-02'})
pre=read(ROOT/'video-agent-studio/templates/episode_preflight.json')
pre.update(status='enhancement_in_progress',episode_id=EP.name,revision='top20-enhance-v2',
 input_contract={'narration_mode':'free TTS addition, reuse prior narration','original_user_script':str(EP/'director/top20-production-v1/script_v4.md'),'original_user_script_sha256':sha(EP/'director/top20-production-v1/script_v4.md'),'original_user_audio':state['timing'],'timing_basis':'actual PCM sample counts plus provider word boundaries','episode_specific_choices':['main only; original20region ranks preserved','more than480seconds through new information','same channel tokens'],'superseded_historical_defaults':['new paid Jun not selected']},
 baseline={'previous_video':state['video'],'sha256':state['video_sha256'],'script_revision':'v4','audio_revision':state['audio_revision'],'brand_intro':'clean v7 5seconds','brand_outro':'clean v7 10seconds','bgm':'existing Thinking Music CC BY4.0'},
 current_user_authorization=str(HERE/'authorization.json'),actual_listening=False,continuous_playback=False)
save(HERE/'episode_preflight.json',pre)
state.update(phase='enhancement_visual_and_new_information',active_revision='top20-enhance-v2',
 enhancement_plan=str(HERE/'제작계획.md'),updated_at=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat())
save(EP/'state.json',state)
d=read(EP/'decisions.json')
if not any(x.get('id')=='D020'for x in d['decisions']):
 d['decisions'].append({'id':'D020','choice':'enhance main visual hierarchy and add verified analytical content >480seconds; keep original voice and prior uploads','basis':'latest explicit user request 2026-11-02','revision':'top20-enhance-v2','owner':'director','authorization':'director/top20-enhance-v2/authorization.json'})
save(EP/'decisions.json',d)
print(json.dumps({'revision':'top20-enhance-v2','baseline_duration_s':state['actual_video_duration_s'],'paid_budget':0,'prior_uploads_preserved':3}))
