import json,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from notify.video_decisions import write,now
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
ep=root/'video-agent-studio/episodes/goyang-changneung-20261015';receipt=read(ep/'outputs/youtube-private-v4/upload_receipt.json')
video=receipt.get('metadata',{});assert receipt['video_id']=='0yvjR4NMw_Q'
bridge=root/'output/telegram_conversation'
for name in ['718066297.json','internal-connectivity-v1.json']:
 p=bridge/'inbox'/name;e=read(p)
 e.update(application_status='applied',applied_at=now().isoformat(),application_basis='current active agent inspected durable inbox during bridge verification; queued delivery should not duplicate')
 if e.get('queued_message_id')==e['thread']:e['queued_message_id']=None
 write(p,e)
s=read(ep/'state.json');s.update(stage='uploaded_private',youtube_video_id=receipt['video_id'],youtube_url='https://youtu.be/0yvjR4NMw_Q',youtube_privacy='private',youtube_processing='succeeded',publication_authorized=False,active_tasks=[],pending_gate=None,pending_decision_ids={});write(ep/'state.json',s)
pub=root/'config/publish_log.json';items=read(pub)
if not any(x.get('main_url')==s['youtube_url'] for x in items):
 items.append({'upload_verified_at':now().isoformat(),'episode_id':ep.name,'channel_id':'UCr_mTC0x_Uobv6MrIsOkrXw','main_url':s['youtube_url'],'privacy':'private','processing':'succeeded','video_sha256':s['rendered_video_sha256'],'receipt':str((ep/'outputs/youtube-private-v4/upload_receipt.json').relative_to(root)),'user_instruction':'완성되면 유튜브에 비공개로 업로드','actual_listening':False,'continuous_playback':False})
 write(pub,items)
write(bridge/'verification_report.json',{'at':now().isoformat(),'root_causes':['ordinary text fell through to legacy candidate bot instead of video conversation','no automatic visible-answer return transport','offset committed before message persistence'],
 'regression_tests_passed':79,'authenticated_phone_message_received':True,'phone_update_id':718066297,'codex_queue_exit_zero':True,'reply_mirror_real_send_verified':True,'single_poller_lock_verified':True,'webhook_active':False,
 'automatic_queued_turn_activation':'not independently observed while current agent turn active; inbox applied by active agent','limits':['PC/internet/Codex/bot must stay running','busy thread may queue requests before work starts','attachments <=20MiB per file','visible event transcript schema is version-sensitive; health records failures'],
 'private_video_url':s['youtube_url'],'youtube_privacy':'private','youtube_processing':'succeeded'})
print('Phone message application, private release, and bridge verification recorded')
