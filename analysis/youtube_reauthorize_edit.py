"""User-run OAuth consent for editing; does not edit or publish videos."""
from pathlib import Path
import sys,json
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/youtube_deps'))
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES=['https://www.googleapis.com/auth/youtube.upload','https://www.googleapis.com/auth/youtube.readonly','https://www.googleapis.com/auth/youtube.force-ssl']
def main():
    flow=InstalledAppFlow.from_client_secrets_file(str(ROOT/'config/youtube-client-secret.json'),SCOPES)
    credentials=flow.run_local_server(host='127.0.0.1',port=0,open_browser=True,timeout_seconds=300,prompt='consent',authorization_prompt_message='Google consent opened in your normal browser. No videos will be changed by this connection step.',success_message='YouTube connection received. You may close this tab.')
    assert credentials.has_scopes(SCOPES),'Required edit scope was not granted; old connection preserved'
    y=build('youtube','v3',credentials=credentials,cache_discovery=False)
    channels=y.channels().list(part='snippet',mine=True).execute(num_retries=0)['items']
    expected=json.loads((ROOT/'config/youtube-upload.json').read_text(encoding='utf-8-sig'))['channel_id']
    assert len(channels)==1 and channels[0]['id']==expected,'Wrong channel; old token preserved'
    token=ROOT/'config/youtube-token.json'
    if token.exists():
        backup=ROOT/'config'/('youtube-token.before-edit-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.json')
        backup.write_bytes(token.read_bytes())
    token.write_text(credentials.to_json(),encoding='utf-8')
    print(json.dumps({'connected':True,'channel_id':expected,'edit_scope_granted':True,'video_changes':0}))
if __name__=='__main__':main()
