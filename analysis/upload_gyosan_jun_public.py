"""Publish exact approved Gyosan Jun artifact; verify five scoped gates and no duplicate insert."""
import sys,json,hashlib,time
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'tools/youtube_deps'))
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
jp=Path(sys.argv[1]);j=json.loads(jp.read_text(encoding='utf-8'))
assert j['publication_authorized'] is True and j['privacy']=='public'
assert j['channel_id']=='UCr_mTC0x_Uobv6MrIsOkrXw'
assert not j.get('publish_at') and not j.get('publishAt')
qa=json.loads((root/j['qa']).read_text(encoding='utf8'))
assert qa['required_unresolved']==0 and qa['sha256']==j['sha256']
completed=json.loads((root/j['completed_approval_file']).read_text(encoding='utf8'))
assert completed['gate']=='completed' and completed['status']=='approved' and completed['video_sha256']==j['sha256']
for name,digest in completed['artifacts'].items():assert sha(root/name)==digest
budget=json.loads((root/'output/video_decisions/decisions/f7919c1076ae.json').read_text(encoding='utf8'))
assert budget['gate']=='budget' and budget['status']=='approved'
assert budget['included_credit_cap']==10055 and budget['additional_cash_usd_cap']==0
for name,digest in budget['artifact_hashes'].items():assert sha(root/'video-agent-studio/episodes/hanam-gyosan-20261019'/name)==digest
gate=json.loads((root/j['approval_file']).read_text(encoding='utf-8'))
assert gate['gate']=='pre_upload' and gate['status']=='approved' and gate['privacy']=='public'
assert gate['video_sha256']==j['sha256'] and gate['job_sha256']==sha(jp)
for name,digest in gate['artifacts'].items():assert sha(root/name)==digest,name
v=root/j['video'];assert sha(v)==j['sha256']
assert len(j['title'])<=100 and len(j['description'].encode())<=5000
c=Credentials.from_authorized_user_file(str(root/'config/youtube-token.json'))
if c.expired:
 c.refresh(Request());(root/'config/youtube-token.json').write_text(c.to_json(),encoding='utf-8')
y=build('youtube','v3',credentials=c,cache_discovery=False)
ch=y.channels().list(part='snippet',mine=True).execute()['items']
assert len(ch)==1 and ch[0]['id']==j['channel_id']
rp=root/j['receipt']
if rp.exists():
 r=json.loads(rp.read_text(encoding='utf-8'));assert r.get('video_id') and r['sha256']==j['sha256'],'Uncertain attempt; inspect before retrying'
else:
 r={'phase':'upload_started','sha256':j['sha256'],'job_sha256':sha(jp),'job':str(jp),'privacy_requested':'public'};save(rp,r)
 body={'snippet':{'title':j['title'],'description':j['description'],'tags':j.get('tags',[]),'categoryId':'27','defaultLanguage':'ko','defaultAudioLanguage':'ko'},'status':{'privacyStatus':'public','selfDeclaredMadeForKids':False,'containsSyntheticMedia':True}}
 req=y.videos().insert(part='snippet,status',body=body,notifySubscribers=j.get('notify_subscribers',False),media_body=MediaFileUpload(str(v),mimetype='video/mp4',chunksize=8*1024*1024,resumable=True))
 result=None
 while result is None:
  progress,result=req.next_chunk(num_retries=0)
  if progress:print('Upload',round(progress.progress()*100),'%',flush=True)
 r.update(video_id=result['id'],phase='uploaded',metadata=result);save(rp,r)
if j.get('thumbnail') and not r.get('thumbnail'):
 try:
  y.thumbnails().set(videoId=r['video_id'],media_body=MediaFileUpload(str(root/j['thumbnail']),mimetype='image/png')).execute();r['thumbnail']='uploaded'
 except HttpError as ex:r['thumbnail']={'status':ex.resp.status,'reason':ex._get_reason()}
 save(rp,r)
for i in range(5):
 items=y.videos().list(part='snippet,status,contentDetails,processingDetails',id=r['video_id']).execute()['items']
 if items:
  assert items[0]['snippet']['channelId']==j['channel_id'] and items[0]['status']['privacyStatus']=='public'
  r['verification']=items[0];save(rp,r)
  status=items[0].get('processingDetails',{}).get('processingStatus')
  print('Processing',status,flush=True)
  if status in ['succeeded','failed','terminated']:break
 time.sleep(5)
print(json.dumps({'url':'https://youtu.be/'+r['video_id'],'privacy':r.get('verification',{}).get('status',{}).get('privacyStatus'),'processing':r.get('verification',{}).get('processingDetails',{}).get('processingStatus'),'thumbnail':r.get('thumbnail')},ensure_ascii=False))
