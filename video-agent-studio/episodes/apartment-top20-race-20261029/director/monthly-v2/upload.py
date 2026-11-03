"""Explicitly authorized single upload + future public schedule. No duplicate-upload retry."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,sys
HERE=Path(__file__).resolve().parent;EP=HERE.parents[1];ROOT=EP.parents[2]
sys.path.insert(0,str(ROOT/'tools/youtube_deps'))
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
CHANNEL='UCr_mTC0x_Uobv6MrIsOkrXw'
PUBLISH='2026-10-29T12:00:00Z'
RECEIPT=HERE/'upload_receipt.json'

def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def service():
    c=Credentials.from_authorized_user_file(str(ROOT/'config/youtube-token.json'))
    if c.expired:c.refresh(Request())
    y=build('youtube','v3',credentials=c,cache_discovery=False)
    channels=y.channels().list(part='id',mine=True).execute(num_retries=0)
    assert CHANNEL in [a['id'] for a in channels.get('items',[])],'wrong_channel'
    return y

def verify(y,video_id,job,receipt):
    d=y.videos().list(part='snippet,status,contentDetails,processingDetails',id=video_id).execute(num_retries=0)
    assert len(d.get('items',[]))==1,'uploaded_video_not_found'
    v=d['items'][0];s=v['status']
    assert v['snippet']['channelId']==CHANNEL and v['snippet']['title']==job['body']['snippet']['title']
    assert s['privacyStatus']=='private' and s.get('publishAt')==PUBLISH,'schedule_not_confirmed'
    assert s.get('uploadStatus') not in ['failed','rejected','deleted']
    receipt.update(phase='scheduled_verified',video_id=video_id,youtube_url='https://youtube.com/shorts/'+video_id,
        verified_at_utc=datetime.now(timezone.utc).isoformat(),status=s,content_details=v.get('contentDetails'),processing_details=v.get('processingDetails'))
    save(RECEIPT,receipt)
    print(json.dumps({'phase':receipt['phase'],'url':receipt['youtube_url'],'publishAt':s['publishAt'],'privacyStatus':s['privacyStatus'],'processing':v.get('processingDetails',{}).get('processingStatus')},ensure_ascii=False))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--verify-only',action='store_true');args=ap.parse_args()
    jobpath=HERE/'upload_job.json';job=json.loads(jobpath.read_text(encoding='utf8'))
    auth=json.loads((HERE/'authorization.json').read_text(encoding='utf8'))
    video=ROOT/job['video'];assert sha(video)==job['video_sha256']==auth['video_sha256']
    assert sha(jobpath)==auth['upload_job_sha256'] and auth['authorization']=='direct_user_request'
    qa=json.loads((EP/'qa/monthly-v2/independent/findings.json').read_text(encoding='utf8'))
    assert qa['verdict']['critical_open']==0 and qa['verdict']['required_open']==0
    assert qa['artifact']['sha256']==job['video_sha256']
    receipt=json.loads(RECEIPT.read_text(encoding='utf8')) if RECEIPT.exists() else {}
    if receipt.get('video_id'):
        assert receipt['video_sha256']==job['video_sha256']
        return verify(service(),receipt['video_id'],job,receipt)
    assert not args.verify_only,'no_existing_video_id'
    assert not receipt,'prior_ambiguous_upload_attempt_do_not_duplicate'
    assert datetime.now(timezone.utc)<datetime.fromisoformat(PUBLISH.replace('Z','+00:00')),'publish_time_has_passed'
    assert len(job['body']['snippet']['title'])<=100 and len(job['body']['snippet']['description'].encode())<=5000
    y=service()
    receipt={'phase':'upload_started','video_sha256':job['video_sha256'],'job_sha256':sha(jobpath),
             'started_at_utc':datetime.now(timezone.utc).isoformat(),'automatic_new_upload_retry':False}
    save(RECEIPT,receipt)
    try:
        req=y.videos().insert(part='snippet,status',body=job['body'],notifySubscribers=True,
            media_body=MediaFileUpload(str(video),chunksize=8*1024*1024,resumable=True))
        response=None
        while response is None:
            status,response=req.next_chunk(num_retries=0)
            if status:print(json.dumps({'uploaded_percent':round(status.progress()*100)}),flush=True)
        receipt.update(phase='uploaded',video_id=response['id']);save(RECEIPT,receipt)
        # A thumbnail error must never trigger a second video upload.
        cover=ROOT/job['cover']
        try:
            y.thumbnails().set(videoId=response['id'],media_body=MediaFileUpload(str(cover),mimetype='image/png',resumable=False)).execute(num_retries=0)
            receipt['thumbnail_status']='set'
        except Exception as exc:
            receipt['thumbnail_status']='not_set';receipt['thumbnail_error_type']=type(exc).__name__
        save(RECEIPT,receipt);verify(y,response['id'],job,receipt)
    except Exception as exc:
        receipt['error_type']=type(exc).__name__;save(RECEIPT,receipt)
        print(json.dumps({'phase':receipt['phase'],'error_type':type(exc).__name__,'video_id':receipt.get('video_id'),'automatic_retry':False}));raise SystemExit(1)

if __name__=='__main__':main()
