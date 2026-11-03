import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
EP = Path(__file__).resolve().parents[2]
HERE = Path(__file__).parent
preflight = json.loads((ROOT/'video-agent-studio/templates/episode_preflight.json').read_text(encoding='utf-8'))
current = json.loads((ROOT/'config/current_video.json').read_text(encoding='utf-8'))
preflight.update(status='production_authorized_checks_pending', episode_id=EP.name)
preflight['baseline'].update(previous_video=current['video'], current_video='outputs/integrated-review-v1/housing_choice_review_v1.mp4',
                            sha256=current['sha256'], script_revision='script-cost-wording-v3', audio_revision='free_tts_pending')
for key in ('topic', 'script', 'budget', 'completed', 'pre_upload'):
    preflight['approvals'][key].update(decision_id='direct-user-20261026-two-episode-private-production',
                                      status='authorized_subject_to_current_version_dual_review')
preflight['approvals']['budget'].update(cash_cap=0, credits_cap=0)
preflight['approvals']['pre_upload']['visibility'] = 'private'
preflight['story'].update(opening_question='같은 집에 살아도 주거 방식에 따라 남는 자산이 달라지는 이유',
                          previous_episode_reference='하남 교산', next_episode_promise='감당 가능한 매매 가격 계산',
                          order=['choice','assumptions','initial_funding','monthly_cashflow','principal_and_deposit',
                                 'investment_return','networth','sensitivity','execution','affordable_purchase'])
preflight['story']['each_section_answers'] = ['비교 조건','자금의 흐름','순자산에 남는 효과','선택이 달라지는 조건']
preflight['representative_previews'] = ['opening_three_households','upfront_costs','regional_growth_intervals',
                                       'mortgage_principal','networth_sensitivity','closing_budget_bridge']
preflight['facts_required'] = ['model_accounting','same_monthly_budget','growth_periods_and_method',
                              'fixed_rent_and_deposit','cost_assumption_categories','leverage_and_opinion_scope']
preflight['change_control']['superseded_rules'] = ['free TTS explicitly authorized; paid Jun generation remains unauthorized',
    'conditional private upload authorized in current direct user instruction']
(HERE/'episode_preflight.json').write_text(json.dumps(preflight,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
inputs = [EP/'outputs/cost-wording-v3/script_cost_v3.md', EP/'outputs/integrated-review-v1/assembly.json',
          EP/'outputs/motion-v1/framework.py', EP/'outputs/motion-v1/chapters.py',
          ROOT/'config/channel_style_tokens.json', ROOT/'config/current_video.json']
manifest = {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
(HERE/'baseline_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
state_path=EP/'state.json'
state=json.loads(state_path.read_text(encoding='utf-8'))
state.update(stage='private_production_script_and_tools_review', budget_status='cash_0_free_tts_only',
             pre_upload_status='private_upload_authorized_after_dual_qa',
             production_authorization=(HERE/'authorization.json').relative_to(ROOT).as_posix(),
             production_plan=(HERE/'plan.md').relative_to(ROOT).as_posix())
state['free_tts_production']={'authorization':'direct_user_20261026','status':'tool_probe_and_script_review',
    'replaces_prior_hold_for_free_tts':True,'paid_jun_generation':'not_authorized',
    'qa':'Codex_and_Claude_required','next_episode':'affordable-home-price_after_first_private_upload'}
state_path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'baseline_inputs':len(manifest),'preflight':'created','private_upload':'conditional_authorized','cash_krw':0}))
