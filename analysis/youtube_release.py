"""Upload an explicitly approved release job, with duplicate protection."""
import json,sys,time,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'tools/youtube_deps'))
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
job=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
assert job.get('publication_authorized') is True
assert job['privacy'] in ['public','private','unlisted']
assert len(job['title'])<=100 and len(job['description'].encode('utf-8'))<=5000
credentials=Credentials.from_authorized_user_file(str(root/'config/youtube-token.json'))
if credentials.expired:
    credentials.refresh(Request())
    (root/'config/youtube-token.json').write_text(credentials.to_json(),encoding='utf-8')
y=build('youtube','v3',credentials=credentials,cache_discovery=False)
channel=y.channels().list(part='snippet',mine=True).execute()['items']
assert len(channel)==1 and channel[0]['id']==job['channel_id'],'Channel mismatch'
record_path=root/job['receipt'];record_path.parent.mkdir(parents=True,exist_ok=True)
video=root/job['video'];digest=hashlib.sha256(video.read_bytes()).hexdigest()
if record_path.exists():
    record=json.loads(record_path.read_text(encoding='utf-8'))
    assert record.get('video_id') and record['sha256']==digest,'Uncertain previous attempt: do not duplicate'
else:
    record={'phase':'upload_started','sha256':digest,'job':str(sys.argv[1]),'requested_privacy':job['privacy']}
    record_path.write_text(json.dumps(record,indent=2),encoding='utf-8')
    body={'snippet':{'title':job['title'],'description':job['description'],'categoryId':'22','defaultLanguage':'ko'},
          'status':{'privacyStatus':job['privacy'],'selfDeclaredMadeForKids':False,'containsSyntheticMedia':True}}
    request=y.videos().insert(part='snippet,status',body=body,notifySubscribers=False,
        media_body=MediaFileUpload(str(video),mimetype='video/mp4',chunksize=8*1024*1024,resumable=True))
    response=None
    while response is None:
        progress,response=request.next_chunk(num_retries=0)
        if progress:print('Upload',round(progress.progress()*100),'%',flush=True)
    record.update(video_id=response['id'],metadata=response,phase='uploaded')
    record_path.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
if job.get('thumbnail') and not record.get('thumbnail'):
    try:
        y.thumbnails().set(videoId=record['video_id'],media_body=MediaFileUpload(str(root/job['thumbnail']),mimetype='image/jpeg')).execute()
        record['thumbnail']='uploaded'
    except HttpError as e:record['thumbnail']={'status':e.resp.status,'reason':e._get_reason()}
for n in range(20):
    result=y.videos().list(part='snippet,status,contentDetails,processingDetails',id=record['video_id']).execute()['items']
    if result:
        record['verification']=result[0];record_path.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
        status=result[0].get('processingDetails',{}).get('processingStatus')
        print('Processing',status,flush=True)
        if status in ['succeeded','failed','terminated']:break
    time.sleep(10)
print(json.dumps({'url':'https://youtu.be/'+record['video_id'],'privacy':record.get('verification',{}).get('status',{}).get('privacyStatus'),'thumbnail':record.get('thumbnail'),'processing':status},ensure_ascii=False))
