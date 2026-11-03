from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys
D=Path(__file__).resolve().parent;E=D.parents[1];R=E.parents[2]
sys.path.insert(0,str(R))
from notify.video_decisions import write
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def main():
    state=read(E/'state.json')
    if not (D/'prior_state.json').exists():write(D/'prior_state.json',state)
    gatepath=R/'output/video_decisions/decisions/688275b5a6ee.json'
    gate=read(gatepath)
    assert gate['episode']==E.name and gate['gate']=='completed'
    gate.update(status='revision_requested',revision_requested_at=datetime.now(timezone.utc).isoformat(),response={'source':'direct_user_instruction_current_conversation','scope':'two videos 20-11 and10-1; expanded regional explanation; per-complex pricecoloredpoints; schools/shopping/subwaymap; explainlegendinintro','new_revision':'top20-split-v4'})
    write(gatepath,gate)
    state.update(active_revision='top20-split-v4',phase='split_v4_research_script_map_prototypes',pending_decision_id=None,active_request='director/top20-split-v4/제작설계.md',active_upload_authorized=False,updated_at=datetime.now(timezone.utc).isoformat(),active_approval_status={'topic':'approved_by_direct_user_two_part_revision','script':'new_split_scripts_not_yet_submitted','budget':'free_only_cash_cap_0_krw','completed':'prior_v3_revision_requested','pre_upload':'not_requested_new_revision'})
    write(E/'state.json',state)
    pre=read(R/'video-agent-studio/templates/episode_preflight.json')
    pre.update(status='applied_for_split_v4',episode_id=E.name,revision='top20-split-v4',execution_mode='local_due_inherited_subagent_model_capacity',script_gate_required_before_new_narration=True)
    pre['input_contract'].update(narration_mode='free_InJoon_selected_previous_user',proposed_script_changes='two standalone parts with expanded per-region explanations and price/amenity map introduction',timing_basis='not_locked_new_voice_not_generated',episode_specific_choices=['20-11/10-1 split','common pricelegend','83-85m2 median May-Oct2026','no newpaidcalls or externalfileexports'])
    pre['baseline'].update(current_video='outputs/top20-explain-v3/main/top20_v6_free_v1.mp4',sha256='80b7cd14b0fa15de21a696796b2a996f0fa47e29ad02ab067ab8ca20448220d1',script_revision='v6')
    write(D/'episode_preflight.json',pre)
    write(D/'decisions.json',{'revision':'top20-split-v4','user_changes':['split20-11and10-1','longerregionalexplanation','pricebinsandcomplexpoints','school/commerce/subwaycontext','introductionexplainsmap'],'producer_choices':{'price_bins_eok':[0,5,7,10,15,20],'point_statistic':'May-Oct2026 83-85m2 complex median','scope':'observedtransactionsandverifiedcoords','style':'channelpalette,stableoverviewpluslivingareadetail'},'cash_cap_krw':0,'new_paid_generation_authorized':False,'external_file_export_authorized':False,'upload_authorized':False,'prior_v3_completed_gate':'revision_requested:688275b5a6ee','native_agents':'both attempts returned model capacity; local work continues without model override'})
    print('split v4 scoped revision recorded')
if __name__=='__main__':main()
