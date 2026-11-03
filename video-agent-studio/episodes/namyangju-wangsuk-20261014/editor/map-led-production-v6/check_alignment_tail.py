import json
from pathlib import Path
EP=Path(__file__).resolve().parents[2]
m=json.loads((EP/'narration/alignment_manifest_v2.json').read_text(encoding='utf-8'))
rows=[]
for c in m['chapters']:
    a=json.loads((EP/c['alignment_file']).read_text(encoding='utf-8'));a=a.get('alignment',a)
    over=[{'char':ch,'start':s,'end':e} for ch,s,e in zip(a['characters'],a['character_start_times_seconds'],a['character_end_times_seconds']) if e>c['pcm_duration_s']+.001]
    rows.append({'scene_id':c['scene_id'],'pcm_duration_s':c['pcm_duration_s'],'overrun':over,'only_punctuation_tail':all(not x['char'].isalnum() for x in over)})
Path(__file__).with_name('alignment_tail_check.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
print([(r['scene_id'],r['only_punctuation_tail'],len(r['overrun'])) for r in rows])
