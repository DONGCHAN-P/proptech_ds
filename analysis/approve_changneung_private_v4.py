import sys,json,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from notify.video_decisions import create,write,now
ep=root/'video-agent-studio/episodes/goyang-changneung-20261015';out=ep/'outputs/youtube-private-v4'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
job=out/'upload_job.json';j=read(job);vh=j['sha256'];jh=hashlib.sha256(job.read_bytes()).hexdigest()
assert vh=='2fe7362fcbe46e45f69f411a5bbf02391c56610a39bf9cbb5aea9105fdf564e0' and j['privacy']=='private'
dec=read(ep/'decisions.json')
cp=root/'output/video_decisions/decisions/21dc8fc431f3.json';c=read(cp)
c.update(status='approved',response={'source':'direct_user_chat','at':now().isoformat(),'note':'완성되면 유튜브에 비공개로 업로드해줘. 현재 전달된 v4r2에 한정.'});write(cp,c)
for x in dec['decisions']:
 if x['id']==c['id']:x.update(c)
d=create(ep.name,'pre_upload','창릉 최종 v4r2를 데이터로보는부동산 채널에 비공개 업로드. 공개 전환·다른 영상 변경은 포함하지 않음.')
d.update(status='approved',privacy='private',channel_id=j['channel_id'],video_sha256=vh,job_sha256=jh,decision_id=d['id'],artifact_hashes={j['video']:vh,str(job.relative_to(root)):jh},response={'source':'direct_user_chat','at':now().isoformat(),'note':'완성되면 유튜브에 비공개로 업로드해줘'})
write(root/'output/video_decisions/decisions'/f"{d['id']}.json",d);dec['decisions'].append(d);write(ep/'decisions.json',dec);write(out/'private_upload_approval.json',d)
s=read(ep/'state.json');s.update(stage='uploading_private_v4',pending_gate=None,pending_decision_ids={},pre_upload_decision_id=d['id'],upload_authorized=True,authorized_privacy='private',publication_authorized=False);write(ep/'state.json',s)
p=read(ep/'preflight.json');p['approvals']['completed'].update(status='approved',decision_id=c['id']);p['approvals']['pre_upload'].update(status='approved',decision_id=d['id'],privacy='private',artifact_hashes=d['artifact_hashes']);write(ep/'preflight.json',p)
print(str(out/'private_upload_approval.json'))
