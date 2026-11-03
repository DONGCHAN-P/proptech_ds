from pathlib import Path
import json,hashlib,datetime
EP=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
art={str(p.relative_to(EP)):sha(p)for p in [EP/'outputs/script_v1.md',EP/'writer/scenes_v1.json',EP/'narration/units.json',EP/'research/facts.json']}
request='사용자 2026-10-19 직접 지시: 창릉 최종 포맷 계승 교산 무료 TTS 제작·무료 검수 위임 및 YouTube 비공개 업로드. 유료 소스는 생성하지 않고 자료 준비 영역. 공개/유료 승인 아님.'
d={"episode_id":EP.name,"decision_source":"same conversation direct user instruction","request_scope":request,"decisions":[
 dict(id='gyosan-topic-20261019',gate='topic',status='approved_direct_user_request',scope='하남 교산 새 롱폼·창릉 최종 포맷',artifacts={'brief.json':sha(EP/'brief.json')}),
 dict(id='gyosan-script-v1-delegated',gate='script',status='approved_under_explicit_free_production_delegation',scope='현재 대본과 무료 검토 제작에 한정, 사실 오류/내용 변경은 버전 추적',artifacts=art),
 dict(id='gyosan-budget-zero',gate='budget',status='not_applicable_no_paid_generation',cash_cap=0,paid_api_calls=0,automatic_charge=False),
 dict(id='gyosan-completed-v1',gate='completed',status='pending_independent_qa',artifacts={}),
 dict(id='gyosan-private-v1',gate='pre_upload',status='authorized_private_only_subject_to_final_qa_and_hash_binding',visibility='private',public_authorized=False,artifacts={})]}
(EP/'decisions.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
s=json.loads((EP/'state.json').read_text(encoding='utf8'));s.update(stage='timing_locked_free_tts',script_revision='script-v1',audio_revision='heami-rate2-free-v1',duration_s=993.6,paid_api_calls=0,claude_collaboration_receipt='director/claude_receipt.json',facts_review='research/script_v1_fact_pass_receipt.json',gates={x['gate']:{k:v for k,v in x.items()if k not in ['gate','scope']}for x in d['decisions']});(EP/'state.json').write_text(json.dumps(s,ensure_ascii=False,indent=2),encoding='utf8')
print('Scoped gates bound to local script inputs; completion and private upload require exact final artifact QA')
