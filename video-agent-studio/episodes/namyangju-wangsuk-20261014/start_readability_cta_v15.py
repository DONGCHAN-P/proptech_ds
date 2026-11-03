from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,math,sys
e=Path(__file__).resolve().parent;repo=e.parents[2];sys.path.insert(0,str(repo))
from notify.video_decisions import create,write
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
folder=e/'outputs/story-review-v8';folder.mkdir(exist_ok=True)
out=e/'outputs/readability-cta-v15';out.mkdir(exist_ok=True)
cta='영상이 만족스러웠다면 구독과 좋아요 버튼 한번씩 눌러주시면 감사하겠습니다. 시청해주셔서 대단히 감사합니다.'
target=folder/'M010_cta.txt'
assert not target.exists(),'Existing CTA version; inspect instead of duplicating decisions'
target.write_bytes(cta.encode('utf-8'))
old=(e/'outputs/story-review-v7/script_v7.md').read_text(encoding='utf-8')
new_section='''## M010 — 구독·좋아요와 시청 감사

### 내레이션

'''+cta+'''

### 화면 지시

기존 M009의 “다음 편 창릉도 같은 지도와 달력으로 비교하겠습니다.” 뒤에 그대로 연결한다. 기존 음성과 자막 301개는 유지한다. 구독·좋아요 텍스트와 🔔·👍 이모지를 발화에 맞춰 작게 진입시킨 뒤 안정적으로 유지한다. 지도 확대·축소나 빠른 화면 삽입은 추가하지 않는다. 의미 단위 자막과 본문 흰 박스를 유지한다. 마지막 실제 대사가 끝난 뒤 정확히 3초 동안 CTA 화면을 유지하고, 그 뒤 기존 10초 브랜드 아웃트로를 시작한다. 발화가 없는 3초와 브랜드 아웃트로에는 빈 자막 흰 박스를 숨긴다. 기존 음악은 잔잔하게 이어서 갑작스러운 전환을 완화하며 새 유료 음악·이미지 생성은 없다.

'''
text=old.replace('새 내레이션이 끝나면 기존 10초 channel-outro-v2.mp4를 붙이고 기존 BGM과 중복하지 않게 페이드한다.','M009 다음에 사용자 지정 M010 구독·좋아요·감사 멘트를 연결하고, M010의 실제 발화 끝에서 3초를 유지한 뒤 기존 10초 channel-outro-v2.mp4를 붙인다. 기존 BGM과 중복하지 않게 페이드한다.')
text=text.replace('## 근거·추정 경계',new_section+'## 근거·추정 경계')
text+='\n## v15 화면 보완\n\n모든 시간축의 글자·외곽선 상하좌우 여백을 확보한다. 일자리 구간에도 좌측 단일 왕숙1 전체 계획도와 상세 영역을 표시한다. 왕숙역 설명 동안 왕숙1 남측 계획판, 일패역 설명부터 왕숙2 계획판을 사용한다. 남부 학교·공원 인출선은 겹치지 않게 배치한다. 기존 버전은 보존한다.\n'
(folder/'script_v8.md').write_bytes(text.encode('utf-8'))
count=len(cta);reserve=math.ceil(count*.2);cap=count+reserve
manifest={'revision':'script-v8-user-literal-CTA','script_path':'outputs/story-review-v8/script_v8.md','source_script_sha256':sha(folder/'script_v8.md'),'previous_script_sha256':sha(e/'outputs/story-review-v7/script_v7.md'),'changed_audio_scene_ids':['M010'],'text_path':'outputs/story-review-v8/M010_cta.txt','text_sha256':sha(target),'characters':count,'correction_reserve':reserve,'submitted_character_hard_cap':cap,'actual_credit_hard_cap':cap,'additional_cash_usd_cap':0,'automatic_retry':False,'new_paid_images':False,'voice':'existing Jun/eleven_v4','reuse':'all existing M000..M009 narration including M007B and all301 existing captions','post_speech_hold_seconds':3,'brand_outro_seconds':10}
write(folder/'manifest.json',manifest)
receipt={'source':'direct_user_revision_request','recorded_at':datetime.now(timezone.utc).isoformat(),'literal_text':cta,'literal_text_user_supplied':True,'additional_voice_budget_explicitly_allowed':True,'scope':'only user supplied newCTA; existing voice reused; included credits and cash0/no topup/overage/retry','script_sha256':manifest['source_script_sha256'],'conservative_hard_cap':cap}
write(folder/'direct_approval_receipt.json',receipt)
script=create(e.name,'script',f"User explicitly requested literal M010 CTA appended after existing v7 M009; no other spoken text change. script-v8 SHA256 {manifest['source_script_sha256']}; TXT SHA256 {manifest['text_sha256']}; {count} chars. 3s hold after actual speech then existing10s brand outro. Script scope only, no upload.")
budget=create(e.name,'budget',f"Direct user explicitly allowed budget for only the literal added CTA. Exact script SHA256 {manifest['source_script_sha256']}, TXT SHA256 {manifest['text_sha256']}. Jun/eleven_v4 {count} initial chars+{reserve} correction reserve, submitted-char AND actual-credit caps {cap}. Included credit only/additional cashUSD0; verify fresh balance/rates/overage-off before POST. No automatic retries/topups/overage/new paid images. Does not inherit previous unused reserves.")
for d in [script,budget]:
 d.update(status='approved',direct_user_confirmation=receipt)
 write(repo/'output/video_decisions/decisions'/f"{d['id']}.json",d)
write(folder/'approval_decisions.json',{'script':script,'budget':budget})
audio=e/'narration/cta-v8';audio.mkdir(exist_ok=True)
write(audio/'authorization.json',{'root_execution_authorized':True,'source_script_path':manifest['script_path'],'source_script_sha256':manifest['source_script_sha256'],'text_path':manifest['text_path'],'text_sha256':manifest['text_sha256'],'script_decision_id':script['id'],'budget_decision_id':budget['id'],'characters':count,'submitted_character_hard_cap':cap,'actual_credit_hard_cap':cap,'additional_cash_usd_cap':0,'automatic_retry':False,'post_speech_hold_s':3})
prior=repo/'output/video_decisions/decisions/5f63c4d38f07.json';prev=read(prior)
prev.update(status='revision_requested',direct_feedback_scope='v15 timeline clipping, jobs locator, station inset timing, south leader-line declutter and literal endingCTA +3s hold',direct_feedback_at=receipt['recorded_at']);write(prior,prev)
p=e/'decisions.json';d=read(p)
for x in d['decisions']:
 if x.get('id')==prev['id']:x.update(prev)
d['decisions'] += [script,budget];write(p,d)
p=e/'state.json';s=read(p)
s.update(stage='v15_readability_station_and_CTA_production',script_revision='script-v8-user-literal-CTA',script_path=manifest['script_path'],script_sha256=manifest['source_script_sha256'],script_approved=True,budget_approved=True,script_approval_decision=script['id'],budget_approval_decision=budget['id'],budget_revision='budget-v8-literal-CTA',new_paid_generation_authorized=True,pending_gate=None,pending_decision_ids={},active_tasks=['editor_readability_cta_v15','narration_cta_v8','qa_readability_cta_v15'],publication_authorized=False)
s['current_review_render_status']='v14_revision_requested_v15_in_progress';write(p,s)
write(out/'revision_brief.json',{'base_video':'outputs/locator-timeline-v14/namyangju_locator_timeline_full_v14.mp4','base_sha256':'ba5bcfdc625f3c15b3f13548f43696e6f7d8b0579c8f8374d46df7d2083966f1','source':'direct_user_revision_request','changes':['global timeline glyph/stroke clipping fix','M002 left W1 whole-plan locator','M003 correct W1 before Ilpae narration, then W2 inset','South school/park labels and crossed leader lines at13:21','user literalCTA+subscribe/like icon motion+3s after actual speech before existing brandoutro'],'narration_manifest':'outputs/story-review-v8/manifest.json','preserve':'all v14 outputs, all prior spoken text and301 caption units, no mapzoom/transient inserts','approval_gates':['topic','script','budget','completed','pre_upload'],'publication_authorized':False})
print(json.dumps({'new_chars':count,'reserve':reserve,'credit_cap':cap,'script_decision':script['id'],'budget_decision':budget['id'],'script_sha256':manifest['source_script_sha256']}))
