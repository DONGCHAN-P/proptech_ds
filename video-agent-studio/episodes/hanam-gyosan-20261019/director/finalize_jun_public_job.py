"""Materialize exact artifact gates from the user's scoped Jun/publication directives."""
from pathlib import Path
import json,hashlib,uuid,datetime,re
E=Path(__file__).resolve().parents[1];R=E.parents[2];O=E/'outputs/release-prep-v5-jun';P=E/'outputs/production-v5-jun'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def relative(p):return p.relative_to(R).as_posix()
qpath=E/'qa/review-v5-jun-independent/report.json';q=read(qpath);assert q['required_unresolved']==0
state=read(E/'state.json');auth=state['jun_v5']['publication_authorization'];assert state['jun_v5']['planned_upload_privacy']=='public'
script=E/'outputs/script-review-v5/script_v5.md';assert sha(script)==auth['script_sha256']
ledger=read(E/'narration/jun-v5-final/generation_ledger.json');assert ledger['actual_credit_total']<=10055
budget=read(R/'output/video_decisions/decisions/f7919c1076ae.json');assert budget['status']=='approved'
for p,h in budget['artifact_hashes'].items():assert sha(E/p)==h
video=R/q['video'] if q['video'].startswith('video-agent-studio/') else E/q['video'];assert sha(video)==q['sha256']
draft=read(O/'metadata_draft.json');assert draft['privacy']=='public'
project=read(P/'timing_locked.json');fps=project['fps'];scenes=read(E/'writer/scenes_v5.json');chapters=[]
for s in scenes:
 rows=[x for x in project['visual_intervals'] if x.get('scene_id')==s['scene_id'] and x['kind']in ['body','chapter']];assert rows
 t=int(min(x['start_frame']for x in rows)/fps);stamp=f'{t//60:02d}:{t%60:02d}';chapters.append((t,stamp+' '+s['title']))
assert chapters[0][0]==0 and all(b[0]-a[0]>=10 for a,b in zip(chapters,chapters[1:]))
description=draft['description'].replace('\n이전 편\n','\n챕터\n'+'\n'.join(x[1]for x in chapters)+'\n\n이전 편\n')
assert len(description.encode('utf8'))<=5000
thumb=R/draft['thumbnail'];assert sha(thumb)==draft['thumbnail_sha256']
now=datetime.datetime.now(datetime.timezone.utc).isoformat();cid=uuid.uuid4().hex[:12];pid=uuid.uuid4().hex[:12]
completed_path=O/'completed_approval.json';pre_path=O/'pre_upload_approval.json';jobpath=O/'upload_job.json'
completed={'id':cid,'episode':E.name,'gate':'completed','status':'approved','video_revision':'v5-jun','video_sha256':q['sha256'],'created_at':now,'artifacts':{relative(video):q['sha256'],relative(qpath):sha(qpath),relative(script):sha(script)},'approval_basis':'User explicitly approved v5 content and requested voice API replacement through upload; subsequent direct instruction explicitly authorizes public release. Exact Jun artifact materialized only after required QA=0. No claim that user listened to the Jun artifact.','actual_listening':False,'continuous_playback':False}
write(completed_path,completed)
job={'revision':'gyosan-v5-jun-public','channel_id':draft['channel_id'],'privacy':'public','publication_authorized':True,'notify_subscribers':True,'title':draft['title'],'description':description,'tags':draft['tags'],'video':relative(video),'sha256':q['sha256'],'qa':relative(qpath),'srt':relative(P/'gyosan_v5_jun.srt'),'thumbnail':relative(thumb),'thumbnail_sha256':sha(thumb),'approval_file':relative(pre_path),'completed_approval_file':relative(completed_path),'receipt':relative(O/'upload_receipt.json'),'contains_synthetic_media':True}
write(jobpath,job);(O/'description.txt').write_text(description,encoding='utf8')
gate={'id':pid,'episode':E.name,'gate':'pre_upload','status':'approved','created_at':now,'privacy':'public','video_revision':'v5-jun','video_sha256':q['sha256'],'job_sha256':sha(jobpath),'channel_id':job['channel_id'],'completed_decision_file':relative(completed_path),'new_paid_generation_authorized':False,'artifacts':{relative(jobpath):sha(jobpath),relative(video):q['sha256'],relative(qpath):sha(qpath),relative(thumb):sha(thumb)},'approval_basis':'Direct user instruction 2026-10-20: upload this current v5 Jun episode publicly, not privately, optimize metadata faithful to script; exact artifact fixed after QA. Prior v1r3 upload gates are not reused.','source_script_sha256':sha(script),'budget_decision_id':'f7919c1076ae','five_gate_trace':{'topic':'gyosan-topic-20261019','script':'a12c24e4e95a','budget':'f7919c1076ae','completed':cid,'pre_upload':pid}}
write(pre_path,gate)
for d in [completed,gate]:write(R/'output/video_decisions/decisions'/f'{d["id"]}.json',d)
d=read(E/'decisions.json');d['decisions'] +=[completed,gate];write(E/'decisions.json',d)
state['jun_v5'].update(completed_decision_id=cid,pre_upload_decision_id=pid,video_sha256=q['sha256'],upload_job=relative(jobpath));state['stage']='jun_v5_public_upload_authorized';write(E/'state.json',state)
print(json.dumps({'job':relative(jobpath),'privacy':'public','title':job['title'],'chapters':[x[1]for x in chapters],'description_bytes':len(description.encode('utf8')),'exact_sha256':q['sha256'],'uploaded':False},ensure_ascii=False))
