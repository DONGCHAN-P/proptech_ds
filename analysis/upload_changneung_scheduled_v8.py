"""Upload only the exact approved Jun release and verify its scheduled publication."""
import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EP=ROOT/'video-agent-studio/episodes/goyang-changneung-20261015'
OUT=EP/'outputs/release-prep-v8-jun'
CHANNEL='UCr_mTC0x_Uobv6MrIsOkrXw'
PUBLISH='2026-10-19T08:30:00Z'
sys.path.insert(0,str(ROOT/'tools/youtube_deps'))

def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,d): p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def service():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    c=Credentials.from_authorized_user_file(str(ROOT/'config/youtube-token.json'))
    if c.expired:c.refresh(Request())
    assert 'https://www.googleapis.com/auth/youtube.upload' in (c.scopes or [])
    y=build('youtube','v3',credentials=c,cache_discovery=False)
    ch=y.channels().list(part='snippet',mine=True).execute()['items']
    assert len(ch)==1 and ch[0]['id']==CHANNEL
    return y

def verify(y,record):
    v=y.videos().list(part='snippet,status,contentDetails,processingDetails',id=record['video_id']).execute()['items']
    assert len(v)==1 and v[0]['snippet']['channelId']==CHANNEL
    status=v[0]['status']
    assert status['privacyStatus']=='private' and status.get('publishAt')==PUBLISH
    record.update(verification=v[0],verified_at=datetime.now(timezone.utc).isoformat(),scheduled_verified=True)
    save(OUT/'upload_receipt.json',record)
    print(json.dumps(dict(video_id=record['video_id'],url='https://youtu.be/'+record['video_id'],
        privacy=status['privacyStatus'],publish_at=status['publishAt'],
        processing=v[0].get('processingDetails',{}).get('processingStatus')),ensure_ascii=False))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['upload','verify']);ap.add_argument('--approval-file')
    args=ap.parse_args();jp=OUT/'upload_job.json';job=read(jp)
    assert job['channel_id']==CHANNEL and job['privacy']=='private' and job['publish_at']==PUBLISH
    assert datetime.fromisoformat(PUBLISH.replace('Z','+00:00'))>datetime.now(timezone.utc), 'Requested release time has passed; do not publish immediately'
    video=ROOT/job['video'];assert sha(video)==job['sha256']
    qa=read(ROOT/job['qa']);assert qa['checked_revision']==job['sha256']
    assert qa.get('required_unresolved',qa.get('required_open'))==[]
    assert len(job['title'])<=100 and len(job['description'].encode('utf-8'))<=5000
    thumbnail=ROOT/job['thumbnail']
    assert sha(thumbnail)==job['thumbnail_sha256'] and thumbnail.stat().st_size<2*1024*1024
    y=service();rp=OUT/'upload_receipt.json'
    if args.action=='verify':verify(y,read(rp));return
    assert args.approval_file,'Exact pre_upload approval required'
    gate=read(ROOT/args.approval_file)
    assert gate['gate']=='pre_upload' and gate['status']=='approved'
    assert gate['video_sha256']==job['sha256'] and gate['job_sha256']==sha(jp)
    assert gate['publish_at']==PUBLISH and gate['channel_id']==CHANNEL
    completed=read(ROOT/gate['completed_decision_file'])
    assert completed['gate']=='completed' and completed['status']=='approved'
    assert completed['video_sha256']==job['sha256']
    if rp.exists():
        record=read(rp);assert record.get('video_id') and record['sha256']==job['sha256'],'Uncertain prior upload: no duplicate retry'
        verify(y,record);return
    from googleapiclient.http import MediaFileUpload
    record=dict(phase='upload_started',sha256=job['sha256'],job_sha256=sha(jp),
        decision_id=gate['id'],started_at=datetime.now(timezone.utc).isoformat(),publish_at=PUBLISH)
    save(rp,record)
    body={'snippet':{'title':job['title'],'description':job['description'],'tags':job['tags'],
        'categoryId':'27','defaultLanguage':'ko','defaultAudioLanguage':'ko'},
        'status':{'privacyStatus':'private','publishAt':PUBLISH,'selfDeclaredMadeForKids':False,'containsSyntheticMedia':True}}
    request=y.videos().insert(part='snippet,status',body=body,notifySubscribers=True,
        media_body=MediaFileUpload(str(video),mimetype='video/mp4',chunksize=8*1024*1024,resumable=True))
    response=None
    while response is None:
        progress,response=request.next_chunk(num_retries=0)
        if progress:print('Upload',round(progress.progress()*100),'%',flush=True)
    record.update(phase='uploaded',video_id=response['id']);save(rp,record)
    y.thumbnails().set(videoId=response['id'],media_body=MediaFileUpload(str(thumbnail),mimetype='image/png')).execute(num_retries=0)
    record['thumbnail_uploaded']=True;save(rp,record);verify(y,record)

if __name__=='__main__':main()
