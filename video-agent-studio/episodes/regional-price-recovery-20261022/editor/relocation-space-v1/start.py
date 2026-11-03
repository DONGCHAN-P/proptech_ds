from pathlib import Path
import json,shutil,datetime
EP=Path(__file__).resolve().parents[2];OUT=EP/'outputs/relocation-space-v1';D=EP/'director/household-space-v1'
path=EP/'state.json';state=json.loads(path.read_text('utf-8'));backup=OUT/'checks/state_before.json'
if not backup.exists():shutil.copy2(path,backup)
acceptance={'client_date':'2026-10-25','user_reply':'맘에들어 다음','accepted_scene':'L002-P2','accepted_revision':'household-space-v1','accepted_sample_sha256':'67851a459535ba6f93feba957aa28abfd0af615d20e7af7322d78aa71a38424a','scope':'acceptance of cutaway-house direction and proceed to next visual work','voice_generation':'still_on_hold','upload':'not_authorized'}
(D/'user_acceptance.json').write_text(json.dumps(acceptance,ensure_ascii=False,indent=2),'utf-8')
state['visual_quality_feedback']['status']='household_space_sample_accepted_by_user';state['visual_quality_feedback']['acceptance_record']='director/household-space-v1/user_acceptance.json'
state['active_visual_task']={'revision':'relocation-space-v1','scene_ids':['L004'],'scope':'complete reconstruction-relocation chapter visual revision','status':'production_in_progress','full_film_replaced':False}
state['stage']='literature_relocation_space_production_in_progress_narration_on_hold';state['updated_at']=datetime.datetime.now(datetime.timezone.utc).isoformat();state['updated_client_date']='2026-10-25';path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n','utf-8')
print(json.dumps({'accepted':'household-space-v1','next':'L004 full chapter','voice_still_on_hold':True}))
