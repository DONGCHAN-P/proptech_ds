"""Correct a single verified complex-name typo in the published description."""
import sys,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'tools/youtube_deps'))
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
c=Credentials.from_authorized_user_file(str(root/'config/youtube-token.json'))
if c.expired:c.refresh(Request());(root/'config/youtube-token.json').write_text(c.to_json(),encoding='utf-8')
y=build('youtube','v3',credentials=c,cache_discovery=False)
o=root/'video-agent-studio/episodes/namyangju-wangsuk-20261014/outputs/youtube-release-v15'
receipt=json.loads((o/'main_upload_receipt.json').read_text(encoding='utf-8'));vid=receipt['video_id']
v=y.videos().list(part='snippet',id=vid).execute()['items'][0]
s=v['snippet'];old=s['description'];new=old.replace('별내자이스타','별내자이더스타')
if new!=old:
 snippet={k:s[k] for k in ['title','categoryId','tags','defaultLanguage','defaultAudioLanguage'] if k in s};snippet['description']=new
 response=y.videos().update(part='snippet',body={'id':vid,'snippet':snippet}).execute()
 assert response['snippet']['description']==new
 (o/'description_name_correction.json').write_text(json.dumps({'video_id':vid,'old':'별내자이스타','new':'별내자이더스타','basis':'research/alternatives-v5/raw_verified_rows.json verified source complex name','description':new},ensure_ascii=False,indent=2),encoding='utf-8')
 print('Published description complex name corrected')
else:print('Description already correct')
