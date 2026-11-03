import pathlib,json,hashlib,re
R=pathlib.Path.cwd();ep=R/'video-agent-studio/episodes/goyang-changneung-20261015';ed=ep/'editor/shorts-leader-v1';p=R/'video/src/changneung-shorts-leader-v1/data.json';d=json.loads(p.read_text(encoding='utf8'));repls={'새 단지가 들어서는 후보입니다.':'새 단지가 들어서는\n후보입니다.','세 후보 중 상승률이 가장 높다는':'세 후보 중 상승률이\n가장 높다는'}
for c in d['captions']:c['text']=repls.get(c['text'],c['text'])
p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8');p=ep/'outputs/shorts-leader-v1/changneung_leader_short_v1.srt';s=p.read_text(encoding='utf8')
for a,b in repls.items():s=s.replace(a,b)
p.write_text(s,encoding='utf8');p=ed/'inputs_manifest.json';d=json.loads(p.read_text(encoding='utf8'));d['files']={x:hashlib.sha256(pathlib.Path(x).read_bytes()).hexdigest() for x in d['files']};p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8');p=ed/'render_job.json';d=json.loads(p.read_text(encoding='utf8'));d['task_id']='changneung-short-leader-v1-final2';d['steps'][0]['argv']=[x.replace('--concurrency=4','--concurrency=8') for x in d['steps'][0]['argv']];p.write_text(json.dumps(d,indent=2),encoding='utf8')
