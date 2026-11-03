from pathlib import Path
import json
E=Path(__file__).resolve().parent;EP=E.parents[1];O=EP/'outputs/production-v5'
p=json.loads((O/'project.json').read_text(encoding='utf8'));sc={s['scene_id']:s for s in json.loads((EP/'writer/scenes_v5.json').read_text(encoding='utf8'))}
for x in p['visual_intervals']:
 if x['scene_id'] in sc:x['props']['title']=sc[x['scene_id']]['title']
(O/'project.json').write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf8')
s=(E/'render.cjs').read_text(encoding='utf8')
a=s.index('const reps=new Map();');b=s.index('const clean=q=>')
s=s[:a]+s[b:]
s=s.replace("path.join(O,'rendered_project.json');const baseline=process.argv.includes('--reuse-baseline')&&fs.existsSync(baselineFile)?JSON.parse(fs.readFileSync(baselineFile)):null", "path.join(EP,'outputs/production-v4/rendered_project.json');const baseline=JSON.parse(fs.readFileSync(baselineFile))")
s=s.replace("x.source_file&&unchanged.has(x.props?.reviewKind||x.props?.mode)","x.source_file")
s=s.replace("const prior=unchanged.has(props.reviewKind||props.mode)?reusable.get(JSON.stringify(props)):null", "const prior=reusable.get(JSON.stringify(props))")
(E/'render_delta.cjs').write_text(s,encoding='utf8')
