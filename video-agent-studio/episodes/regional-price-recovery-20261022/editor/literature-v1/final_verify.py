from pathlib import Path
import json,hashlib,zipfile,os
EP=Path(__file__).resolve().parents[2];ROOT=EP.parents[2];OUT=EP/'outputs/literature-visual-v1';D=EP/'director/literature-visual-v1'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for data in iter(lambda:f.read(4*1024*1024),b''):h.update(data)
    return h.hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
M=read(OUT/'delivery_manifest.json');state=read(EP/'state.json');QA=read(ROOT/M['qa']);shelf=read(ROOT/'config/video_shelf.json');entry=next(e for e in shelf['entries'] if e['workspace']==EP.relative_to(ROOT).as_posix())
assert QA['summary']['critical_open']==0 and QA['summary']['required_open']==0 and QA['video_sha256']==M['video_sha256']
for a in M['artifacts']:assert (ROOT/a['path']).stat().st_size==a['bytes'] and sha(ROOT/a['path'])==a['sha256']
aliases=['논문영상_검토본.mp4','검토영상.mp4','논문영상_프로젝트.zip','논문영상_검토안내.md','대본.md','논문영상_자막_임시.srt']
for alias in aliases:assert os.path.samefile(ROOT/shelf['shelf']/entry['name']/alias,ROOT/entry['files'][alias])
with zipfile.ZipFile(OUT/'논문영상_프로젝트_v1.zip') as z:assert z.testzip() is None;zip_count=len(z.infolist())
for name,digest in read(D/'protected.json').items():assert sha(ROOT/name)==digest
assert state['budget_status']=='voice_generation_deferred_by_user' and state['script_sha256']==M['script_sha256'] and state['production_render']['video_sha256']==M['video_sha256']
proof={'status':'verified_local_visual_review','video_sha256':M['video_sha256'],'duration':M['duration'],'artifacts_verified':len(M['artifacts']),'aliases_verified':len(aliases),'zip_files':zip_count,'zip_integrity':'pass','original_inputs_preserved':True,'qa_required_open':0,'qa_recommended_open':QA['summary']['recommended_open'],'voice_generation_calls':0,'external_delivery_sent':False,'actual_listening':False,'continuous_playback':False}
(D/'final_verification.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(proof,ensure_ascii=False))
