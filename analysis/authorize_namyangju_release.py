"""Record separate completed and pre-upload gates from explicit current user directions."""
import sys,json,hashlib
from pathlib import Path
from datetime import datetime,timezone
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from notify.video_decisions import create,write
e=root/'video-agent-studio/episodes/namyangju-wangsuk-20261014'
o=e/'outputs/youtube-release-v15';o.mkdir(exist_ok=True)
now=datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
mode=sys.argv[1];jobpath=Path(sys.argv[2]).resolve();job=read(jobpath)
assert job['privacy']=='public' and job['publication_authorized']
artifacts={str(jobpath.relative_to(root)):sha(jobpath)}
for key in ['video','thumbnail','qa_file']:
 if job.get(key):p=root/job[key];artifacts[p.relative_to(root).as_posix()]=sha(p)
q=read(root/job['qa_file']);assert q['required_open_count']==0 and q['local_review_ready'] is True
assert sha(root/job['video'])==job['sha256']
dec=read(e/'decisions.json')
if mode=='main':
 p=root/'output/video_decisions/decisions/4b8219ae2886.json';d=read(p)
 for name,digest in d['artifacts'].items():assert sha(e/name)==digest
 d.update(status='approved',resolved_at=now,approval_source='direct_current_user_message',approval_text='오케이 검수 완료 이거 업로드하자.',publication_authorized=False)
 write(p,d)
 for i,x in enumerate(dec['decisions']):
  if x.get('id')==d['id']:dec['decisions'][i]=d
else:
 d=create(e.name,'completed','사용자 지시로 v15 원음에서 파생 편집한 독립 쇼츠: '+job['title'])
 d.update(status='approved',resolved_at=now,approval_source='direct_current_user_delegated_edit_and_publication',approval_text='이전과 마찬가지로 쇼츠도 인기있을만한거 혹은 내용이 단독으로 의미있을만한거 잘라서 같이 올려줘. 공개로 그냥 업로드해버리자',artifacts=artifacts,qa_required_open_count=0)
 write(root/'output/video_decisions/decisions'/f"{d['id']}.json",d);dec['decisions'].append(d)
gate=create(e.name,'pre_upload','공개 업로드: '+job['title'])
gate.update(status='approved',privacy='public',artifacts=artifacts,version=job['version'],publication_authorized=True,resolved_at=now,approval_source='explicit_direct_user_publication_instruction',approval_text='공개로 그냥 업로드해버리자',completed_decision_id=d['id'],five_gates_preserved=True,scope='Only exact listed artifact hashes and metadata; no future episode authorization')
gp=root/job['approval_file'];write(gp,gate);write(root/'output/video_decisions/decisions'/f"{gate['id']}.json",gate)
dec['decisions'].append(gate);write(e/'decisions.json',dec)
s=read(e/'state.json');s.update(stage='public_release_in_progress',publication_authorized=True,publication_scope='v15 main and independently reviewed source-derived shorts per direct user instruction',pending_gate=None,active_tasks=['public_release','shorts_production_and_QA'],latest_pre_upload_decision=gate['id']);write(e/'state.json',s)
print(json.dumps({'completed_decision':d['id'],'pre_upload_decision':gate['id'],'privacy':'public'},ensure_ascii=False))
