"""Director-owned episode state for the regional script draft, no approval implied."""
from pathlib import Path
import datetime as dt
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
EP = ROOT / 'video-agent-studio/episodes/regional-price-recovery-20261022'
OUT = EP / 'outputs/script-review-v2'
NOW = dt.datetime.now(dt.timezone.utc).isoformat()

def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

def write(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

qa = read(EP / 'qa/script-v2/findings.json')
# An independent QA report must exist; its meaning is checked by the director.
script_hash = sha(OUT / 'script_v2.md')
claude = read(OUT/'collaboration/claude_execution_receipt.json')
claude_ok = claude.get('exit_code') == 0 and not claude.get('is_error') and any('claude-opus' in key for key in claude.get('actual_model_usage',{})) and claude.get('draft_characters',0)>300
claude_status = 'editorial_review_completed' if claude_ok else 'authorized_attempt_failed_no_generated_review'
final_qa_path=EP/'qa/script-v2/claude_recheck.json'
final_qa=read(final_qa_path)
assert final_qa.get('current_script_sha256')==script_hash,'Final QA must refer to current script'
assert final_qa.get('required_open_issue_count')==0,'Required script issues remain open'
state = read(EP / 'state.json')
state.update(stage='script_v2_review_draft', script_status='codex_draft_v2_with_claude_editorial_review_not_user_approved' if claude_ok else 'codex_draft_v2_independent_qa_reviewed_not_user_approved', script_revision='v2', script_file=(OUT/'script_v2.md').relative_to(ROOT).as_posix(), script_sha256=script_hash, research_status='7region_custom_price_index_and_2official_descriptive_factor_examples; causal_tests_and_official_index_crosscheck_pending', updated_at=NOW, claude_collaboration={'requested_model': 'opus', 'requested_effort': 'max', 'cli_subscription_reported': 'pro', 'status': claude_status, 'payload_authorized': True, 'actual_generated_text': claude_ok, 'actual_model_usage':claude.get('actual_model_usage',{}),'receipt': (OUT/'collaboration/claude_execution_receipt.json').relative_to(ROOT).as_posix()}, audio_status='not_generated_for_v2', timing_locked=False, budget_status='no_paid_voice_image_video_generation_authorized', pre_upload_status='not_authorized', qa_file=(EP/'qa/script-v2/findings.json').relative_to(ROOT).as_posix())
state['qa_file']=final_qa_path.relative_to(ROOT).as_posix()
state['qa_history']=['qa/script-v2/findings.json','qa/script-v2/recheck.json','qa/script-v2/claude_recheck.json']
write(EP/'state.json', state)
decisions = read(EP/'decisions.json')
entries = [
 {'id':'regional-script-v2-20261022','status':'authorized_draft_scope_only','basis':'Latest direct user request: regional video script; use Claude maximum setting too','scope':'Preserve v1. Create v2 regional script, visual plan and independent factual QA. Codex owns final integration; external Claude has no file or shell tools.','version':'v2','script_sha256':script_hash,'created_at':NOW},
 {'id':'regional-claude-payload-v2-20261022','status':'explicitly_authorized','basis':'User answered: 집계 수치와 대본 전달 승인','prior_block_resolved':'Automatic review initially rejected external transfer pending explicit payload/destination permission; user subsequently provided that permission.','reviewable_payload':['outputs/script-review-v2/collaboration/verified_facts.json','outputs/script-review-v2/script_v2_codex_before_qa.md'],'scope':'Only aggregate statistics and draft script to Claude Opus effort=max; no individual trades or credentials.','execution_status':claude_status,'created_at':NOW},
 {'id':'regional-stage-boundaries-v2-20261022','status':'retained','scope':'Draft delivered is not script approval, paid-generation budget approval, finished video approval or upload permission. Public-release official-index crosscheck and factor causal tests remain separate.','created_at':NOW},
]
existing = {x['id'] for x in decisions['decisions']}
decisions['decisions'] += [x for x in entries if x['id'] not in existing]
write(EP/'decisions.json', decisions)
baseline = read(ROOT/'config/current_video.json')
pre = read(ROOT/'video-agent-studio/templates/episode_preflight.json')
pre.update(episode_id=EP.name, status='script_v2_preflight_filled_not_production_approval', updated_at=NOW)
pre['baseline'].update(previous_video=baseline, current_video=None, script_revision='v2', audio_revision=None)
pre['approvals']['topic'].update(decision_id='regional-research-script-20261022',status='authorized_research_and_draft_topic')
pre['approvals']['script'].update(status='draft_submitted_not_approved',artifact_hashes={'script_v2.md':script_hash})
for gate in ('budget','completed','pre_upload'):
    pre['approvals'][gate]['status']='not_authorized_or_not_reached'
pre['story'].update(opening_question='집값 다 올랐다는데, 왜 내 지역은 아직일까?', previous_episode_reference='교산편 이후 독립 지역 데이터 분석; 기존 주거 방식 비교의 앞단', next_episode_promise='고점 이후 공급·준공 후 미분양과 회복 속도의 관계 검증', order=[s['scene_id'] for s in read(EP/'scenes.json')['scenes']], each_section_answers=['reference_point','observed_path','recovery_distance','sample_limits'],candidate_scope='not_applicable_no_complex_investment_ranking')
pre['representative_previews']=['7region_peak_chart','gyeonggi_threshold_change','sejong_period_window','supply_and_migration_source']
pre['facts_required']=['period_reference_peak_and_endpoint','same_complex_area_matching_and_cancelled_deal_filters','sample_count_and_sensitivity','sejong_start_and_gwangju_missing','price_vs_ownership_return','descriptive_factor_scope_and_source','official_index_crosscheck_before_public_release']
pre['change_control'].update(changed_scene_ids=[f'S{i:03}' for i in range(1,13)],single_timing_lock=None,package_frozen_before_hash=True)
pre['qa'].update(actual_listening_performed=False,continuous_playback_performed=False,evidence_paths=['qa/script-v2/findings.json','qa/script-v2/recheck.json','qa/script-v2/claude_recheck.json','outputs/script-review-v2/package_checks.json','research/script-v2-factors/verified_examples.json'],required_open_issues='Draft fixes closed as final scoped QA records; official-index public-release crosscheck remains open; no audio/video QA claimed')
write(EP/'episode_preflight_v2.json',pre)

source_root='analysis/housing_growth_2006/regional_expansion_v1/'
scene_claims={
'S001':'기본표본 서울 고점대비+27.15%, 대구-17.75%;2026Q2',
'S002':'100→80→96 수학 예시와 2020~2022 최대분기 고점 정의',
'S003':'7개 지역의 각 기준 고점 대비 위치; 경기 민감도 인접 표시',
'S004':'서울·인천 낙폭/반등/회복; 서울2024Q3 첫 재도달',
'S005':'경기 최소거래2/3/5기준 -4.08/-0.58/+5.24%, 기준고점도 다름',
'S006':'부산·대구 관측저점2025Q2, 낙폭·반등·고점거리',
'S007':'대전·세종의 낙폭/반등/고점거리; 서로 다른 순서',
'S008':'동일종점2026Q2; 3/5/10년 시작점2023/2021/2016Q2; 세종·대구 CAGR',
'S009':'여섯 지역2006Q1·세종2015Q1 연속 자료; 공통2015기준;10년2016Q2시작',
'S010':'공표 전체주택 준공·국내순이동 예시, 가격 인과관계는 미검증',
'S011':'동일단지면적 분기매칭, 서울최소43·세종35단지, 광주미확보',
'S012':'앞선 관측 결과의 회수;2%는 다음편 시나리오이며 미래추정 아님',
}
claimmap={'script_revision':'v2','script_sha256':script_hash,'claims':[{'claim_id':'RPR-'+sid,'scene_id':sid,'statement':statement,'status':'verified_math' if sid=='S002' else 'qualified_custom_index_observation' if sid!='S010' else 'verified_descriptive_only_causal_hypotheses_unverified','sources':[source_root+'results.json',source_root+'quarterly_index.csv'] if sid not in ('S005','S010') else [source_root+'sensitivity.csv'] if sid=='S005' else ['video-agent-studio/episodes/regional-price-recovery-20261022/research/script-v2-factors/verified_examples.json'],'reference_date':'2026Q2 price endpoint; external factors use separately specified2023/2024/2025years','checked_at':NOW} for sid,statement in scene_claims.items()]}
claimmap['claims'].append({'claim_id':'METHOD-V2','status':'qualified','statement':'Exploratory own index, not official or forecast; changing sample; no floor/renovation control. All main links >=30complexes.','sources':[source_root+'results.json',source_root+'analysis_coverage.csv','analysis/housing_growth_2006/regional_expansion_v1.py']})
write(OUT/'claim_map_v2.json',claimmap)

cfg=read(ROOT/'config/video_shelf.json')
entry=next(x for x in cfg['entries'] if x['name']=='지역별가격회복')
entry['status']='대본 v2 · Codex 작성/Claude Opus max 편집 검토·수치 검수 · 12장면 화면설계 · 사용자 검토 초안 · 음성·영상 미제작. 대본보기.html은 이전 v1.' if claude_ok else '대본 v2 · Codex 검토 초안/수치 검수 · 12장면 화면설계 · Claude 승인 후 호출 실패 · 음성·영상 미제작. 대본보기.html은 이전 v1.'
entry['files'].update({'대본.md':(OUT/'script_v2.md').relative_to(ROOT).as_posix(),'낭독대본.txt':(OUT/'narration_v2.txt').relative_to(ROOT).as_posix(),'화면설계.md':(OUT/'visual_storyboard.md').relative_to(ROOT).as_posix(),'수치근거.md':(OUT/'수치와_자료근거.md').relative_to(ROOT).as_posix(),'클로드협업.md':(OUT/'클로드_협업상태.md').relative_to(ROOT).as_posix(),'이전대본_v1.md':(EP/'writer/script_v1.md').relative_to(ROOT).as_posix()})
if claude_ok:
    entry['files']['클로드검토.md']=(OUT/'claude_editorial_review_v2.md').relative_to(ROOT).as_posix()
write(ROOT/'config/video_shelf.json',cfg)
print(json.dumps({'script_sha256':script_hash,'state':'review_draft_not_approved','claude':claude_status,'shelf_entry':'지역별가격회복'},ensure_ascii=False))
