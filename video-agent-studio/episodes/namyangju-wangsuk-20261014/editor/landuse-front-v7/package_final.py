import json,hashlib,zipfile,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[5];E=R/'video-agent-studio/episodes/namyangju-wangsuk-20261014';H=Path(__file__).parent;O=E/'outputs/front-review-v7'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
review=E/'qa/landuse-front-v7/final_review.json';assert review.exists(),'Final independent review not ready'
assert (O/'completed_decision.json').exists(),'Director completed gate record not ready'
qa=read(review);video=O/'namyangju-landuse_front_v7.mp4'
assert qa.get('local_review_ready') is True and qa.get('required_open_count')==0
assert qa['sha256']==sha(video)
shutil.copy2(review,O/'qa_final_review.json');shutil.copy2(H/'placement_guide.md',O/'placement_guide.md')
sources=[R/'video/src/NamyangjuLanduseV7.tsx',*sorted((R/'video/src/namyangju-landuse-v7').glob('*'))]
save(O/'project_source_hashes.json',[{'path':str(p.relative_to(R)).replace('\\','/'),'sha256':sha(p)} for p in sources if p.is_file()])
names=['namyangju-landuse_front_v7.mp4','namyangju-landuse_front_v7.srt','captions.json','scene_camera_manifest.json','source_manifest.json','research_source_rights.json','visual_asset_manifest.json','woori_group_ci_source.json','woori_group_ci_official.png','label_patch_manifest.json','project_source_hashes.json','placement_guide.md','지역_상세지도와_의미단위_자막.md','qa_final_review.json','completed_decision.json','README.md','technical_qa/encoded_check.json']
files=[O/n for n in names];assert all(p.exists() for p in files)
save(O/'zip_contents.json',{'scope':'front-only core delivery; no previous full video, prepatch original, preview stills, raw PDFs or raw HTML','files':[{'path':str(p.relative_to(O)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':sha(p)} for p in files]});files.append(O/'zip_contents.json')
z=O/'namyangju-landuse_front_v7_delivery.zip'
with zipfile.ZipFile(z,'w',compression=zipfile.ZIP_STORED,allowZip64=True) as a:
 for p in files:a.write(p,str(p.relative_to(O)))
with zipfile.ZipFile(z) as a:assert a.testzip() is None
manifest={'status':'front_local_review_ready','video':{'file':video.name,'bytes':video.stat().st_size,'sha256':sha(video),'frames':13087,'fps':30,'duration_s':13087/30},'zip':{'file':z.name,'bytes':z.stat().st_size,'sha256':sha(z),'entries':len(files),'integrity':'CRC pass; stored; MP4 not re-encoded for ZIP'},'front_only':True,'full14minute_merge':False,'new_paid_calls':0,'actual_listening':False,'continuous_playback':False,'upload_or_external_file_send':False}
save(O/'delivery_manifest.json',manifest);save(H/'handoff.json',{'revision':'landuse-front-v7-final','inputs':{'script':'script-v4-hook-outside','audio':'audio-v2 unchanged6chapters','source_script_sha256':'d816c5ba4341ddaafd4f3f3db6585873a519e1577d865dbf332d183925d4c2da'},'outputs':str(O),'delivery':manifest,'validated':['whole decode','13,087video frames 1080p30/AAC','pre/post label-fix AAC packet hashes identical','map ROI patch exactly8804..9305; original preserved','independent final QA and persistent white bar checks','ZIP CRC'],'open_checks':['actual listening/continuous playback not performed','user review and any full merge handled by director'],'next_owner':'video_director'})
print(json.dumps(manifest))
