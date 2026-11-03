"""Apply only the user-requested typography correction to the scheduled video."""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EP=ROOT/'video-agent-studio/episodes/goyang-changneung-20261015'
OUT=EP/'outputs/thumbnail-series-v2'
VIDEO='eLF3-1ZaraQ'
CHANNEL='UCr_mTC0x_Uobv6MrIsOkrXw'
sys.path.insert(0,str(ROOT/'tools/youtube_deps'))

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    image=OUT/'thumbnail.png';digest=hashlib.sha256(image.read_bytes()).hexdigest()
    approval=read(OUT/'scoped_approval.json')
    assert approval['status']=='approved' and approval['scope']=='thumbnail_typography_only'
    assert approval['video_id']==VIDEO and approval['thumbnail_sha256']==digest
    assert image.stat().st_size<2*1024*1024
    c=Credentials.from_authorized_user_file(str(ROOT/'config/youtube-token.json'))
    if c.expired:c.refresh(Request())
    y=build('youtube','v3',credentials=c,cache_discovery=False)
    before=y.videos().list(part='snippet,status',id=VIDEO).execute()['items'][0]
    assert before['snippet']['channelId']==CHANNEL
    record=dict(video_id=VIDEO,thumbnail_sha256=digest,decision_id=approval['id'],
        scope='thumbnail_typography_only',before=before,started_at=datetime.now(timezone.utc).isoformat())
    save(OUT/'update_receipt.json',record)
    result=y.thumbnails().set(videoId=VIDEO,media_body=MediaFileUpload(str(image),mimetype='image/png')).execute(num_retries=0)
    after=y.videos().list(part='snippet,status',id=VIDEO).execute()['items'][0]
    assert before['status']==after['status'],'Video status changed unexpectedly'
    for key in ['title','description','tags']:
        assert before['snippet'].get(key)==after['snippet'].get(key),key
    record.update(status='updated_and_metadata_preserved',thumbnail_response=result,after=after,
        verified_at=datetime.now(timezone.utc).isoformat())
    save(OUT/'update_receipt.json',record)
    print(json.dumps(dict(video_id=VIDEO,status=record['status'],publish_at=after['status'].get('publishAt'),
        privacy=after['status']['privacyStatus']),ensure_ascii=False))

if __name__=='__main__':main()
