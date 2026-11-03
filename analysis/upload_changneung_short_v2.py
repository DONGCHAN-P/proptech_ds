"""Exact user-authorized Shorts scheduled release; no automatic retry."""
import sys, json, hashlib, argparse
from pathlib import Path
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'analysis'))
from upload_changneung_scheduled_v8 import service, CHANNEL, PUBLISH
EP=ROOT/'video-agent-studio/episodes/goyang-changneung-20261015'
OUT=EP/'outputs/shorts-release-v2'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['upload','verify']);a=ap.parse_args()
    job=read(OUT/'upload_job.json'); gate=read(ROOT/job['approval_file'])
    assert gate['status']=='approved' and gate['gate']=='pre_upload'
    assert gate['job_sha256']==sha(OUT/'upload_job.json') and gate['video_sha256']==job['sha256']
    video=ROOT/job['video'];assert sha(video)==job['sha256']
    qa=read(ROOT/job['qa']);assert qa['checked_revision']==job['sha256'] and not qa['required_unresolved']
    assert datetime.fromisoformat(PUBLISH.replace('Z','+00:00'))>datetime.now(timezone.utc)
    y=service();rp=OUT/'upload_receipt.json'
    if a.action=='upload' and not rp.exists():
        from googleapiclient.http import MediaFileUpload
        record={'phase':'upload_started','sha256':job['sha256'],'job_sha256':sha(OUT/'upload_job.json'),'started_at':datetime.now(timezone.utc).isoformat()};save(rp,record)
        body={'snippet':{'title':job['title'],'description':job['description'],'tags':job['tags'],'categoryId':'27','defaultLanguage':'ko','defaultAudioLanguage':'ko'},'status':{'privacyStatus':'private','publishAt':PUBLISH,'selfDeclaredMadeForKids':False,'containsSyntheticMedia':True}}
        request=y.videos().insert(part='snippet,status',body=body,notifySubscribers=True,media_body=MediaFileUpload(str(video),mimetype='video/mp4',resumable=True,chunksize=8*1024*1024))
        response=None
        while response is None:
            progress,response=request.next_chunk(num_retries=0)
        record.update(phase='uploaded',video_id=response['id']);save(rp,record)
    record=read(rp);assert record.get('video_id'),'Prior upload uncertain; no duplicate retry'
    v=y.videos().list(part='snippet,status,contentDetails,processingDetails',id=record['video_id']).execute(num_retries=0)['items'][0]
    assert v['snippet']['channelId']==CHANNEL and v['status']['privacyStatus']=='private' and v['status']['publishAt']==PUBLISH
    record.update(verification=v,scheduled_verified=True,verified_at=datetime.now(timezone.utc).isoformat(),url='https://youtu.be/'+record['video_id']);save(rp,record)
    print(json.dumps({'url':record['url'],'publish_at':PUBLISH,'privacy':v['status']['privacyStatus'],'processing':v.get('processingDetails',{}).get('processingStatus')},ensure_ascii=False))
if __name__=='__main__':main()
