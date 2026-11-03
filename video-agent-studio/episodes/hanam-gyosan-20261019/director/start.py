from pathlib import Path
import json,hashlib
EP=Path(__file__).resolve().parents[1];R=EP.parents[2]
def write(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf8')
brief=dict(episode_id=EP.name,request_type='new_video',topic='하남 교산',format_reference='goyang-changneung-20261015/outputs/production-v8-jun',target_duration_min=10,voice='Microsoft Heami Desktop local free review TTS',paid_api_cap=0,upload_visibility='private',user_request='창릉 최종 포맷과 최대한 동일, Claude 협업, 무료 TTS, 비용 필요한 부분은 자료 준비 영역으로 남기고 비공개 업로드',style=['합니다체','가격성장 요인과 권역별 대장 후보','전체 토지계획→일자리→교통→가격→생활시설→공급→대안→후보','고정 상세지도+좌측 전체 locator','출처는 흰 자막 아래','숫자 영문 원표기','챕터 AI 배경 재사용','클린 인트로 아웃트로 및 3초 마무리'],security='Never print credentials; no paid generation')
write(EP/'brief.json',brief)
write(EP/'state.json',dict(episode_id=EP.name,stage='research_in_progress',execution_allowed=True,reference_only=False,budget=dict(cash_cap=0,paid_api_calls=0),authorization=dict(user_delegated_free_production_and_review=True,private_upload_requested=True,public_upload_authorized=False),gates={k:dict(status='scope_to_be_bound_to_artifacts') for k in ['topic','script','budget','completed','pre_upload']}))
pre=json.loads((R/'video-agent-studio/templates/episode_preflight.json').read_text(encoding='utf8'))
pre.update(episode_id=EP.name,status='active_preflight')
pre['baseline'].update(previous_video='goyang-changneung-20261015',current_video='outputs/production-v8-jun/changneung_full_v8_jun.mp4',sha256='d36d8f70e406d928a1eb7041f4d1c9c4c1873747430d3c12a6f4c7fd99d98642',script_revision='script-v8',audio_revision='local-free-tts-new-for-gyosan')
write(EP/'director/episode_preflight.json',pre)
write(EP/'decisions.json',dict(episode_id=EP.name,decisions=[],delegated_scope='Free production and review with private upload only; artifacts must be attached to the five gates before transition',paid_budget=0))
print('episode initialized')
