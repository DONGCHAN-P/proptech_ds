import sys,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'tools/youtube_deps'))
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
c=Credentials.from_authorized_user_file(str(root/'config/youtube-token.json'))
if c.expired:
 c.refresh(Request());(root/'config/youtube-token.json').write_text(c.to_json(),encoding='utf-8')
y=build('youtube','v3',credentials=c,cache_discovery=False)
ch=y.channels().list(part='snippet,contentDetails,statistics',mine=True).execute()['items']
assert len(ch)==1 and ch[0]['id']=='UCr_mTC0x_Uobv6MrIsOkrXw'
p=y.playlistItems().list(part='snippet,contentDetails',playlistId=ch[0]['contentDetails']['relatedPlaylists']['uploads'],maxResults=15).execute()
ids=','.join(a['contentDetails']['videoId'] for a in p['items'])
v=y.videos().list(part='snippet,status,contentDetails',id=ids).execute()
out=root/'video-agent-studio/episodes/namyangju-wangsuk-20261014/outputs/youtube-release-v15'
out.mkdir(parents=True,exist_ok=True)
(out/'channel_inventory.json').write_text(json.dumps({'channel':ch,'videos':v},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'channel':ch[0]['snippet']['title'],'videos':[{'id':a['id'],'title':a['snippet']['title'],'privacy':a['status']['privacyStatus']} for a in v['items']]},ensure_ascii=False))
