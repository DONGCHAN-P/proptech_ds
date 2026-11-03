"""Read published video's current thumbnail and download control evidence only."""
import sys,json,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'tools/youtube_deps'))
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import requests
c=Credentials.from_authorized_user_file(str(root/'config/youtube-token.json'))
if c.expired:
 c.refresh(Request());(root/'config/youtube-token.json').write_text(c.to_json(),encoding='utf-8')
y=build('youtube','v3',credentials=c,cache_discovery=False)
ch=y.channels().list(part='snippet',mine=True).execute()['items'];assert len(ch)==1 and ch[0]['id']=='UCr_mTC0x_Uobv6MrIsOkrXw'
v=y.videos().list(part='snippet,status',id='T_GBxTRgRSc').execute()['items'][0]
assert v['snippet']['channelId']==ch[0]['id'] and v['status']['privacyStatus']=='public'
thumbs=v['snippet']['thumbnails'];thumb=next(thumbs[k] for k in ['maxres','standard','high','medium','default'] if k in thumbs)
assert thumb['url'].startswith('https://i.ytimg.com/')
r=requests.get(thumb['url'],timeout=30);r.raise_for_status()
o=root/'video-agent-studio/episodes/namyangju-wangsuk-20261014/outputs/thumbnail-ab-v1'
(o/'A_live_evidence.jpg').write_bytes(r.content)
(o/'published_video_snapshot.json').write_text(json.dumps({'video':v,'downloaded_thumbnail_url':thumb['url'],'evidence_sha256':hashlib.sha256(r.content).hexdigest(),'read_only':True},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'video_id':v['id'],'title':v['snippet']['title'],'privacy':v['status']['privacyStatus'],'evidence_bytes':len(r.content),'test_started':False},ensure_ascii=False))
