from pathlib import Path
import json,subprocess,psutil,sys
E=Path(__file__).resolve().parent;EP=E.parent.parent;R=EP.parents[2];O=EP/'outputs/production-v7-preview';python=R/'tools/python311/python.exe'
renderers=[]
for p in psutil.process_iter(['name']):
 try:
  if p.info['name']=='node.exe' and any('production-v7-preview/render.cjs' in a for a in p.cmdline()):renderers.append(p)
 except psutil.Error:pass
assert len(renderers)<=1
if renderers:
 print('Waiting on existing renderer process completion event',flush=True);renderers[0].wait(timeout=1800)
assert(O/'rendered_project_v7.json').is_file()
p=json.loads((O/'rendered_project_v7.json').read_text(encoding='utf-8'));inputs=[O/'rendered_project_v7.json',O/'render_receipt.json',O/'audio/narration_v7_preview.wav',O/'brand_intro_clean_v7.mp4',O/'brand_outro_clean_v7.mp4',R/'video/public/changneung-v3/data_city_ambient_v1.wav',E/'assemble.py',E/'evidence.py',E/'handoff.py',R/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe',R/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe']+[Path(x)for x in sorted({x['source_file']for x in p['visual_intervals']})]
job=dict(task_id='changneung-v7-preview-assemble-verify',inputs=list(map(str,inputs)),outputs=list(map(str,[O/'changneung_full_v7_preview.mp4',O/'technical_v7.json',O/'evidence_manifest.json',O/'delivery_manifest.json'])),steps=[dict(argv=[str(python),'-X','utf8',str(E/name)])for name in ['assemble.py','evidence.py','handoff.py']]);spec=E/'finish_job.json';spec.write_text(json.dumps(job,ensure_ascii=False,indent=2),encoding='utf-8');z=subprocess.run([str(python),'-X','utf8',str(R/'analysis/video_task_runner.py'),str(spec),'--jobs-dir',str(E/'cache/jobs')]);sys.exit(z.returncode)
