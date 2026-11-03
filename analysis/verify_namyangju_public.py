import sys,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'tools/youtube_deps'))
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
c=Credentials.from_authorized_user_file(str(root/'config/youtube-token.json'))
if c.expired:
 c.refresh(Request());(root/'config/youtube-token.json').write_text(c.to_json(),encoding='utf-8')
y=build('youtube','v3',credentials=c,cache_discovery=False)
o=root/'video-agent-studio/episodes/namyangju-wangsuk-20261014/outputs/youtube-release-v15'
rows=[]
for p in sorted(o.glob('*upload_receipt.json')):
 d=json.loads(p.read_text(encoding='utf-8'))
 if not d.get('video_id'):continue
 a=y.videos().list(part='snippet,status,contentDetails,processingDetails',id=d['video_id']).execute()['items']
 assert len(a)==1
 d['verification']=a[0];p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
 rows.append({'receipt':p.name,'id':d['video_id'],'privacy':a[0]['status']['privacyStatus'],'processing':a[0].get('processingDetails',{}).get('processingStatus'),'definition':a[0]['contentDetails'].get('definition'),'title':a[0]['snippet']['title']})
(o/'public_verification.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(rows,ensure_ascii=False))
