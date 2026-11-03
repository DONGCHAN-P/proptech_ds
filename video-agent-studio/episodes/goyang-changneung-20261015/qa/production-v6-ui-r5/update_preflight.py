from pathlib import Path
import json
q=Path('video-agent-studio/episodes/goyang-changneung-20261015/qa/production-v6-ui-r5');p=q/'findings.json';fs=json.loads(p.read_text(encoding='utf-8-sig'))
for f in fs:
 if f['issue_id'] in ['QAR5-001','QAR5-003']:f['status']='fixed_representative_verified_pending_mp4';f['evidence']+='; updated proof actual view confirms overlap removed/date margin restored'
 if f['issue_id']=='QAR5-002':f['status']='fixed_project_verified_pending_mp4';f['evidence']+='; updated172cues protected-boundary scan0 and normalized unit text all equal'
p.write_text(json.dumps(fs,ensure_ascii=False,indent=2),encoding='utf-8')
