import json,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from notify.video_decisions import write,now
from notify import conversation_bridge as cb
p=root/'config/video_telegram_bridge.json';cfg=json.loads(p.read_text(encoding='utf-8-sig'))
transcript=Path('C:/Users/e2ken/.codex/sessions/2026/10/14/rollout-2026-10-14T19-40-52-01a13a00-2b87-7460-b2c7-1ac1332bacf9.jsonl')
assert transcript.exists() and cfg['codex_thread'] in transcript.name
cfg.update(conversation_enabled=True,mirror_enabled=True,transcript_path=str(transcript),
           conversation_mode='ordinary_text_and_attachments_to_bound_thread',
           reply_transport='visible_events_local_transcript',conversation_enabled_at=now().isoformat())
for scope in ['conversation_progress','conversation_replies']:
 if scope not in cfg['notification_preference']['scope']:cfg['notification_preference']['scope'].append(scope)
write(p,cfg)
cb.mirror_once(cfg)
print('Enabled ordinary messages + visible replies for current bound thread, no historical backlog')
