import json,hashlib
from pathlib import Path
ep=Path('video-agent-studio/episodes/goyang-changneung-20261015')
p=ep/'outputs/production-v3/changneung_full_v3.mp4';assert p.stat().st_size>1000000
lock=json.loads((ep/'editor/production-v3/timing_lock_v3.json').read_text(encoding='utf-8'))
state_path=ep/'state.json';s=json.loads(state_path.read_text(encoding='utf-8'))
s.update(stage='final_QA_v3',render_started=True,render_revision='production-v3',video_path='outputs/production-v3/changneung_full_v3.mp4',actual_video_duration_seconds=lock['duration_s'],rendered_video_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),active_tasks=['independent_final_QA_v3'],pending_gate=None)
state_path.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'stage':s['stage'],'sha256':s['rendered_video_sha256']}))
