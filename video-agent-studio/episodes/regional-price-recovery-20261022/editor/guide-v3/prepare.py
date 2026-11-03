from pathlib import Path
import json,shutil,hashlib
from PIL import Image
EP=Path(__file__).resolve().parents[2];OUT=EP/'outputs/guide-v3';P=OUT/'project';ROOT=EP.parents[2]
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2),'utf-8')
for d in [P/'assets/fonts',P/'assets/images',P/'compositions',OUT/'checks',EP/'director/guide-v3']:d.mkdir(parents=True,exist_ok=True)
old=EP/'outputs/readable-video-v2/project'
for f in ['Pretendard-Bold.woff2','Pretendard-Regular.woff2']:shutil.copy2(old/'assets/fonts'/f,P/'assets/fonts'/f)
for f in ['gsap.min.js','references.json','floorplan59.png','floorplan_facts.json','apartment-0.svg','apartment-1.svg','apartment-2.svg']:shutil.copy2(old/'assets'/f,P/'assets'/f)
assets=json.loads((EP/'visual/guide-v3/generated_assets.json').read_text('utf-8'))['assets']
for a in assets:
    src=Path(a['generated_file']);assert src.exists(),src
    dest=P/'assets/images'/f'{a["id"]}.png';shutil.copy2(src,dest)
    with Image.open(dest) as im:a['resolution']=list(im.size)
    a.update(local_file=str(dest),sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),original_preserved=True)
chap=json.loads((EP/'visual/guide-v3/chapter_assets.json').read_text('utf-8'))['chapters']
new={'L002':'chapter_households','L003':'chapter_space','L004':'chapter_relocation','L008':'chapter_analysis'}
for c in chap:
    if c['scene_id'] in new:
        aid=new[c['scene_id']];a=next(a for a in assets if a['id']==aid);c.update(image_file=a['local_file'],status='ready',generator='built_in_image_gen',asset_id=aid,source_manifest=str(EP/'visual/guide-v3/generated_assets.json'))
    else:
        src=Path(c['image_file']);dest=P/'assets/images'/f'chapter_{c["scene_id"]}.png';shutil.copy2(src,dest);c.update(image_file=str(dest),asset_id=f'chapter_{c["scene_id"]}',status='ready',original_file=str(src))
    c['sha256']=hashlib.sha256(Path(c['image_file']).read_bytes()).hexdigest()
assert len(set(c['sha256'] for c in chap))==8
dump(OUT/'assets.json',{'generated':assets,'chapters':chap,'new_images_count':9,'reused_chapter_images_count':4,'generator':'built_in_image_gen','image_generation_billing':'not_queried_no_external_paid_media_API','voice_generated':False,'external_send':False})
shutil.copy2(EP/'writer/guide-v3/semantic_units.json',OUT/'semantic_units.json')
shutil.copy2(EP/'outputs/readable-video-v2/인용자료.md',OUT/'인용자료.md')
shutil.copy2(EP/'writer/guide-v3/script.md',OUT/'의미단위_대본과_표기표.md')
dump(OUT/'image_prompts.json',{a['id']:a['prompt'] for a in assets})
print(json.dumps({'new_images':len(assets),'unique_chapter_images':len(chap),'project':str(P)},ensure_ascii=False))
