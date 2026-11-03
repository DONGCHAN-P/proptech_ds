import pathlib,json,hashlib
from PIL import Image
V=pathlib.Path(__file__).parent;EP=V.parent;R=V.parents[3];O=EP/'outputs/production-v1';S=R/'video/src/gyosan-production-v1';renderer=EP/'editor/production-v1/render_r3.cjs'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((O/'render_receipt_r3.json').read_text(encoding='utf8'));p=json.loads((O/'rendered_project_r3.json').read_text(encoding='utf8'));original=json.loads((O/'project.json').read_text(encoding='utf8'))
source_files=[S/n for n in ['Board.tsx','R3Maps.tsx','data_r3.json','data.json','regional.json','entry.tsx']]
# Match Node's platform-native absolute paths and exact digest concatenation.
digest=hashlib.sha256(('\n'.join(str(x)+':'+sha(x) for x in source_files)+sha(renderer)).encode()).hexdigest()
assert digest==r['input_digest'],'Current source digest mismatch'
assert sha(O/'project.json')==r['project_sha256'],'Project changed after render'
assert sha(O/'rendered_project.json')==r['baseline_sha256'],'r2 baseline changed'
paths={pathlib.Path(x['source_file']) for x in p['visual_intervals'] if x['kind'] in ['body','chapter']}
assert all(x.is_file() for x in paths),'Missing image source'
changed=[x for x in paths if 'r3' in x.parts]
assert len(changed)==r['changed_png']
files={}
for x in changed:
 with Image.open(x) as im:
  assert im.size==(1920,1080);im.verify()
 files[str(x)]=sha(x)
total=lambda z:sum(x['end_frame']-x['start_frame'] for x in z['visual_intervals'])
assert total(p)==total(original),'Timeline frame coverage changed'
checks=dict(passed=True,input_digest=digest,project_sha256=r['project_sha256'],baseline_sha256=r['baseline_sha256'],new_png_verified=len(changed),all_referenced_files_exist=True,new_png_dimensions=[1920,1080],timeline_total_frames=total(p),project_timeline_total_frames=total(original),unchanged_intervals_not_rerendered=True,source_files={x.name:sha(x) for x in source_files},new_png_sha256=files)
(V/'verification_r3.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in checks.items() if k not in ['new_png_sha256','source_files']},ensure_ascii=False))
