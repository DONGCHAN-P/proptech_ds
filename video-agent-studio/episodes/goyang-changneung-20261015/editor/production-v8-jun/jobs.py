from pathlib import Path
import json,sys
E=Path(__file__).resolve().parent;EP=E.parent.parent;R=EP.parents[2];O=EP/'outputs/production-v8-jun';py=R/'tools/python311/python.exe'
stage=sys.argv[1]
sources=list((R/'video/src/changneung-production-v8-jun').glob('*'))+list((R/'video/src/changneung-production-v8-labels-base').glob('*'))
sources +=[p for p in (EP/'editor/production-v8-labels/public').rglob('*')if p.is_file()]
sources +=[p for p in (R/'video-agent-studio/assets/chapter-backgrounds/v1').rglob('*')if p.is_file()]
inputs=[E/'input_provenance.json',EP/'outputs/production-v8-labels/rendered_project_v8.json']
if stage=='timeline':
 inputs +=[E/'timeline.py',EP/'writer/revision-v8/narration_packet.json',EP/'narration/preview-v8/segments.json',EP/'outputs/production-v8-labels/affected_ranges.json',EP/'outputs/script-review-v8/script_v8.md']+list((EP/'narration/jun-v8-final').glob('M*.alignment.json'))+list((O/'audio').glob('M*.wav'))
 outputs=[O/x for x in ['project_v8_jun.json','captions.json','changneung_v8_jun.srt','scene_proposal.json']]+[E/'semantic_alignment.json'];argv=[str(py),'-X','utf8',str(E/'timeline.py')]
elif stage in ['preflight','render']:
 inputs +=sources+[E/'render.cjs',O/'project_v8_jun.json',R/'video/package-lock.json'];outputs=[O/'layout_guard.json']if stage=='preflight'else[O/'rendered_project_v8_jun.json',O/'render_receipt.json'];argv=['node',str(E/'render.cjs'),'--preflight-only' if stage=='preflight'else '--resume']
elif stage=='assembly':
 p=json.loads((O/'rendered_project_v8_jun.json').read_text(encoding='utf-8'));inputs +=[E/'assemble.py',O/'rendered_project_v8_jun.json']+[Path(x)for x in sorted({x['source_file']for x in p['visual_intervals']})]+list((O/'audio').glob('M*.wav'))+[EP/'outputs/production-v7-preview'/x for x in ['brand_intro_clean_v7.mp4','brand_outro_clean_v7.mp4']]+[R/'video/public/changneung-v3/data_city_ambient_v1.wav',R/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe',R/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe'];outputs=[O/'changneung_full_v8_jun.mp4',O/'technical_v8_jun.json'];argv=[str(py),'-X','utf8',str(E/'assemble.py')]
elif stage=='evidence':
 inputs +=[E/'evidence.py',O/'project_v8_jun.json',O/'changneung_full_v8_jun.mp4'];outputs=[O/'evidence_manifest.json'];argv=[str(py),'-X','utf8',str(E/'evidence.py')]
else:raise ValueError(stage)
job=dict(task_id='changneung-v8-jun-'+stage,inputs=list(map(str,inputs)),outputs=list(map(str,outputs)),steps=[dict(argv=argv)])
dest=E/(stage+'_job.json');dest.write_text(json.dumps(job,ensure_ascii=False,indent=2),encoding='utf-8');print(dest)
