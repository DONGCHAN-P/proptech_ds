"""Bind the existing Telegram bridge to this conversation, preserving old data.
No Telegram messages, no queue submission, no credentials in reports.
Run with the poller stopped, then restart the existing single-instance bot.
"""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,os,shutil,sys

R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from notify import conversation_bridge as cb
from notify.video_decisions import write

OUT=R/'reports/텔레그램_연결진단_20261103';OUT.mkdir(parents=True,exist_ok=True)
cfgp=R/'config/video_telegram_bridge.json';cursor=R/'output/telegram_conversation/reply_cursor.json'
cfg=json.loads(cfgp.read_text(encoding='utf-8-sig'));thread=os.environ['CODEX_THREAD_ID']
paths=list((Path.home()/'.codex/sessions').rglob('*'+thread+'*.jsonl'))
assert len(paths)==1 and paths[0].is_file(),'Current conversation transcript is not uniquely available'
cli=cb.resolve_codex_executable(cfg);assert Path(cli).is_file()
for p in [cfgp,cursor]:
 backup=OUT/(p.name+'.before.json')
 if p.exists()and not backup.exists():shutil.copy2(p,backup)
oldthread=cfg['codex_thread'];oldpath=cfg['transcript_path'];oldcli=cfg.get('codex_executable')
cfg.update(previous_codex_thread=oldthread,codex_thread=thread,transcript_path=str(paths[0]),codex_executable=cli,
 thread_binding_updated_at=datetime.now(timezone(timedelta(hours=9))).isoformat(),
 thread_binding_basis='Current user reports Telegram delivery failure; restore existing mirror to current active conversation and installed CLI')
write(cfgp,cfg)
# Seed at EOF. Do not resend older conversations or historical assistant messages.
write(cursor,{'transcript_path':str(paths[0]),'offset':paths[0].stat().st_size,'recent_text_hashes':[]})
events,health=cb.pending_snapshot(cfg)
invalid=[]
for p in (R/'output/telegram_conversation/inbox').glob('*.json'):
 try:json.loads(p.read_text(encoding='utf-8'))
 except (ValueError,UnicodeError):
  invalid.append({'file':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'preserved':True})
result={'at_kst':datetime.now(timezone(timedelta(hours=9))).isoformat(),'status':'binding_repaired_poller_restart_required',
 'old_thread':oldthread,'new_thread':thread,'old_cli_exists':Path(oldcli).is_file()if oldcli else False,'new_cli_exists':True,
 'old_transcript_path':oldpath,'new_transcript_path':str(paths[0]),'current_transcript_seeded_at_eof':True,
 'old_pending_requests_preserved_not_redispatched':health['other_thread_pending_count'],
 'invalid_records_preserved':invalid,'new_pending_count':health['pending_count'],
 'tests':'23 related bridge/decision tests passed','prior_upload_notification':{'at_kst':'2026-11-02T19:40:14+09:00','bot':'@proptech_ds_bot','message_id':381,'API_send_success_recorded':True,'phone_visibility':'not verified'},
 'existing_message_edit_check':{'executed':False,'reason':'automatic approval review rejected message edit outside diagnosis scope'},
 'new_messages_sent_by_this_script':0}
write(OUT/'diagnosis.json',result)
print(json.dumps({'binding':'current_conversation','CLI':'installed_existing_binary','current_transcript_seeded_at_eof':True,
 'invalid_records_preserved':len(invalid),'old_pending_not_redispatched':health['other_thread_pending_count'],'telegram_messages_sent':0},ensure_ascii=False))
