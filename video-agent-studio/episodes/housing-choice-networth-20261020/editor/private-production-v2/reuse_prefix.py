"""Reuse completed v5 chapter MP4s only after exact render-input byte comparison."""
import hashlib,json,os
from pathlib import Path
HERE=Path(__file__).resolve().parent;EP=HERE.parents[1]
OLD=EP/'outputs/private-production-v1';OUT=EP/'outputs/private-production-v2'
SOURCE=OLD/'renders/measured-v5';DEST=OUT/'renders/measured-v6'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def dump(p,r):p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
DEST.mkdir(parents=True,exist_ok=True)
commands=read(HERE/'render_commands.json')['chapter_commands'];rows=[]
for n in [1,2,3]:
    chapter=f'ch{n:02d}';source=SOURCE/f'{chapter}.mp4';target=DEST/source.name
    receipt_path=SOURCE/f'{chapter}.receipt.json';prior=read(receipt_path)
    assert sha(source)==prior['output_sha256']
    proofs={}
    files=['index.html','timing.json','anchor_audit.json','hyperframes.json','package.json']
    files += [p.relative_to(OLD/chapter).as_posix() for p in (OLD/chapter/'assets').rglob('*') if p.is_file()]
    for rel in files:
        a,b=OLD/chapter/rel,OUT/chapter/rel
        assert sha(a)==sha(b),f'Changed chapter input prevents reuse: {chapter}/{rel}'
        proofs[rel]=sha(b)
    argv=prior['argv']
    assert argv[argv.index('--quality')+1]=='delivery' and argv[argv.index('--fps')+1]=='30'
    assert argv[argv.index('--workers')+1]=='4' and '--browser-gpu' in argv
    if not target.exists():os.link(source,target)
    assert sha(target)==prior['output_sha256']
    current=next(c for c in commands if c['chapter']==n)
    receipt={**prior,'file':str(target),'argv':current['argv'],'reused_completed_render':True,
             'reuse_source':str(source),'reuse_source_receipt_sha256':sha(receipt_path),
             'rendered_argv':prior['argv'],'reuse_basis':'exact HTML, cues/anchors/scenes, narration/BGM, image/font/GSAP, pinned CLI and encoding settings; only version output/cache paths differ',
             'input_file_sha256':proofs,'link_method':'hardlink; preserved source is never modified'}
    dump(DEST/f'{chapter}.receipt.json',receipt)
    rows.append({'chapter':n,'file':str(target),'output_sha256':sha(target),'html_sha256':proofs['index.html'],'input_files_checked':len(proofs),'receipt_sha256':sha(DEST/f'{chapter}.receipt.json')})
dump(HERE/'prefix_reuse_receipt.json',{'status':'exact_input_and_MP4_SHA_reuse_pass','chapters':rows,'v1_preserved':True,'new_renders':0})
print(json.dumps({'status':'exact_input_and_MP4_SHA_reuse_pass','chapters':[r['chapter'] for r in rows]}))
