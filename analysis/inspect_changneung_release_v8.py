"""Read-only account check for the requested Changneung scheduled release."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools/youtube_deps'))
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

def main():
    c=Credentials.from_authorized_user_file(str(ROOT/'config/youtube-token.json'))
    if c.expired: c.refresh(Request())
    y=build('youtube','v3',credentials=c,cache_discovery=False)
    ch=y.channels().list(part='snippet',mine=True).execute()['items']
    assert len(ch)==1 and ch[0]['id']=='UCr_mTC0x_Uobv6MrIsOkrXw'
    videos=y.videos().list(part='snippet,status',id='0yvjR4NMw_Q').execute().get('items',[])
    d=dict(checked_at=datetime.now(timezone.utc).isoformat(),channel_id=ch[0]['id'],
        channel_title=ch[0]['snippet']['title'],scopes=sorted(c.scopes or []),
        upload_scope_present='https://www.googleapis.com/auth/youtube.upload' in (c.scopes or []),
        old_private_video=[dict(id=v['id'],title=v['snippet']['title'],privacy=v['status']['privacyStatus']) for v in videos],
        mutations=0,publish_at_utc_requested='2026-10-19T08:30:00Z')
    p=ROOT/'video-agent-studio/episodes/goyang-changneung-20261015/outputs/release-prep-v8-jun/account_preflight.json'
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:d[k] for k in ['channel_title','upload_scope_present','old_private_video','mutations']},ensure_ascii=False))

if __name__=='__main__':
    try: main()
    except Exception as exc:
        print(json.dumps({'status':'failed','error_type':type(exc).__name__}))
        sys.exit(1)
