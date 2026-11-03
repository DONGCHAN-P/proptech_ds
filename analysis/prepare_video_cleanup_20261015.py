import json,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[1];o=root/'output/cleanup-20261015'
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
paths=[root/'video-agent-studio/guides/제작_기본가이드.md',root/'video-agent-studio/guides/사용자_피드백_이력.md',root/'video-agent-studio/templates/episode_preflight.json']
for p in paths:assert p.is_file() and p.stat().st_size>2000
json.loads(paths[2].read_text(encoding='utf-8'))
ledger=paths[1].read_text(encoding='utf-8');assert 'W62' in ledger and 'G28' in ledger
write(o/'guide_complete.json',{'completed':True,'basis':'root reviewed guide and feedback scope, role handoff complete, JSON validated','files':[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths]})
plan=json.loads((o/'deletion_candidates.json').read_text(encoding='utf-8'))
prefixes=['video-agent-studio/episodes/namyangju-wangsuk-20261014/','video/out/','video/public/','video/build/','video/.remotion/','.remotion/']
selected=[x for x in plan['files'] if any(x['relativePath'].startswith(p) for p in prefixes)]
excluded=[x for x in plan['files'] if x not in selected]
write(o/'deletion_approved_video.json',{'root':str(root),'require_guide_complete':True,'scope':'only audited video intermediates; unrelated application bytecode excluded','files':selected,'bytes':sum(x['bytes'] for x in selected)})
write(o/'nonvideo_candidates_not_selected.json',{'reason':'Unrelated application bytecode outside video cleanup scope; kept','files':excluded})
print(json.dumps({'selected_files':len(selected),'bytes':sum(x['bytes'] for x in selected),'outside_video_scope_kept':len(excluded)}))
