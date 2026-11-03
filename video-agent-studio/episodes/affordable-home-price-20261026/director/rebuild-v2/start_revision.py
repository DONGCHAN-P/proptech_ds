import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
EP = HERE.parents[1]
ROOT = EP.parents[2]
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,d): p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()

authority = {
    'request':'대본 클로드랑 논의해가며 고치고, 영상 퀄리티도 가이드에 맞게 어제 영상 검토했던 방식대로 검토해서 다시 만들어줘',
    'scope':'affordable_home_price_script_and_video_rebuild_v2',
    'Claude_authorized':'대본·집계된 공개 정책 및 가상 계산 사례·본 작업의 실제 영상 표본 화면·검수 결과를 기존 로그인 Claude Opus/max에 전달해 논의·검수',
    'excluded_egress':['자격증명','API 키','계정정보','개별 실거래','다른 업무 파일','음성 원본'],
    'paid_generation_authorized':False,'cash_cap_krw':0,'new_paid_voice_credit_cap':0,
    'free_tts_authorized':True,'paid_provider_fallback':False,
    'current_request_upload_execution':False,
    'previous_private_upload_authorization_preserved':'새 버전은 별도 완료·업로드 해시와 범위 확인 후 판단',
    'baseline_video':'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/jun-production-v1/renders/measured-jun-v1/housing_choice_jun_v1.mp4',
    'baseline_sha256':'136a20c43ba3a99a138ba7282c1fb1a8532fc3aa92695c57ca2f904d011b1079',
    'previous_video_sha256':'ad9df5989c019395e9ea9eb7877c81300cf78e9ab611536ebcc7431c8fc3609a',
    'recorded_at_utc':datetime.now(timezone.utc).isoformat()
}
save(HERE/'authorization.json',authority)
plan = {
    'request_type':'enhance_video','status':'executing_direct_user_rebuild_request',
    'design':'한 가구의 6억 집 매수 자금 흐름을 중심으로 초반 결론→현금·비용→은행 한도→월 예산→가격·정책 조건 변화→결론으로 구성',
    'approaches_considered':[
        {'approach':'기존45장면을 유지한 시각 패치','decision':'서술 지연·반복의 원인을 남기므로 제외'},
        {'approach':'검증된 수치·정책을 보존한 사례 중심 재구성','decision':'이번 요청에 맞춰 채택'}],
    'tasks':[
        {'id':'S1','owner':'writer + director/Claude','outputs':['writer/rebuild-v2/script_v3.md','writer/rebuild-v2/scenes_v3.json'],'gate':'초반 결론·가구A/B·기존 검증값 보존·Claude 필수 이슈0'},
        {'id':'S2','owner':'narration','outputs':['narration/rebuild-v2/final_timing.json'],'gate':'잠금SHA·실제 WordBoundary·문자/숫자/단위 보존·새 유료 호출0'},
        {'id':'S3','owner':'editor','outputs':['editor/rebuild-v2','outputs/rebuild-v2'],'gate':'세 대표 장면의 인코딩 비교와 가독성·순차 노출·겹침0'},
        {'id':'S4','owner':'independent QA + director/Claude','outputs':['qa/rebuild-v2','director/rebuild-v2/claude'],'gate':'전체 장면·컷·자막·ASR/신호 확인 범위별 판정; 미적 반복을 필수 검수'},
        {'id':'S5','owner':'director','outputs':['outputs/rebuild-v2/completion.json','config/video_shelf.json'],'gate':'정확한 해시·검수 범위·기존본 보존·로컬 검토본 연결'}],
    'review_focus':['단계별 정보가 발화 전에 전부 노출되지 않을 것','글자↔도형 충돌 포함','화면마다 핵심 결과와 조건의 위계','가구·대출상품·금리기간 불일치 방지','최신 Jun 게시본과 같은 메시지 유형별 실제 비교'],
    'voice':'무료 InJoon 0%로 검토본 제작; 새 유료 Jun은 별도 예산 범위 필요',
    'runtime':'기존 HyperFrames 0.8.181 재현 환경; usage status unknown',
    'preserve':['기존 MP4/원본 대본/정책·계산 원장/음성/브랜드/출처·승인·검수 기록'],
    'no_unrequested_remote_changes':True
}
save(HERE/'design_and_plan.json',plan)
p=read(ROOT/'video-agent-studio/templates/episode_preflight.json')
p.update(status='rebuild_v2_in_progress',episode_id=EP.name)
p['baseline'].update(previous_video=authority['baseline_video'],sha256=authority['baseline_sha256'],script_revision='housing_choice_v6',audio_revision='Jun eleven_v4')
p['story'].update(opening_question='내 돈 2억5천만원으로 감당할 집값은?',order=['answer_teaser','cash_costs','bank_limit','monthly_budget','6_9_12_price_cases','policy_products','newborn_reset','decision'])
p['representative_previews']=['six_eok_cash_flow','ltv_dsr_binding_limit','monthly_budget_price']
p['approvals']['topic']['status']='same_topic_user_authorized_rebuild'
p['approvals']['script']['status']='current_direct_user_iterative_rewrite_and_production_request_pending_exact_lock'
p['approvals']['budget'].update(status='free_only',credits_cap=0,cash_cap=0)
p['approvals']['completed']['status']='pending_new_version_QA'
p['approvals']['pre_upload']['status']='not_executed_for_rebuild_v2'
save(HERE/'episode_preflight.json',p)
state=read(EP/'state.json')
state['rebuild_v2']={'status':'script_rewrite_and_pipeline_preparation','authorization':str((HERE/'authorization.json').relative_to(ROOT)).replace('\\','/'),'plan':str((HERE/'design_and_plan.json').relative_to(ROOT)).replace('\\','/'),'previous_published_files_preserved':True,'paid_generation_calls':0,'new_version_QA':'pending'}
save(EP/'state.json',state)
print(json.dumps({'revision':'rebuild-v2','status':state['rebuild_v2']['status'],'paid_generation_calls':0}))
