import json,pathlib,shutil
EP=pathlib.Path(__file__).resolve().parents[1];ROOT=EP.parents[2]
pub=ROOT/'video/public/data-insight-v1'
for name in ['office.mp4','pantry.mp4','team.mp4']:
 p=EP/'visual'/name
 assert p.is_file(),f'Not ready: {p}'
 shutil.copy2(p,pub/name)
node='C:/Program Files/nodejs/node.exe'
py=str(ROOT/'tools/python311/python.exe')
entry=ROOT/'video/src/data-insight-v1/entry.tsx'
inputs=list((ROOT/'video/src/data-insight-v1').glob('*'))+list(pub.glob('*'))+[EP/'scenes.json',EP/'script_v1_1.md',EP/'editor/verify.py',ROOT/'video/package-lock.json',ROOT/'video/remotion.config.ts']
job={'task_id':'data-insight-v1-final','inputs':[str(x) for x in inputs],'outputs':[str(EP/'outputs/v1/data_insight_30s_v1.mp4'),str(EP/'editor/technical_verification.json')],'steps':[
 {'argv':[node,str(ROOT/'video/node_modules/@remotion/cli/remotion-cli.js'),'render',str(entry),'DataInsightV1',str(EP/'outputs/v1/data_insight_30s_v1.mp4'),'--codec=h264','--crf=17','--concurrency=4','--log=error'],'cwd':str(ROOT/'video')},
 {'argv':[py,'-X','utf8',str(EP/'editor/verify.py')],'cwd':str(ROOT)}]}
(EP/'editor/render_job.json').write_text(json.dumps(job,ensure_ascii=False,indent=2),encoding='utf8')
print('Final job ready: 900 frames, original procedural BGM, stream/decode checks and cut frames.')
