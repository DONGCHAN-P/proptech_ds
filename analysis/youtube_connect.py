"""Connect a YouTube channel. Does not upload or publish videos."""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools/youtube_deps'))
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/youtube.upload',
          'https://www.googleapis.com/auth/youtube.readonly']
root = Path(__file__).resolve().parents[1]
client = root / 'config/youtube-client-secret.json'
token = root / 'config/youtube-token.json'
credentials = None
if token.exists():
    credentials = Credentials.from_authorized_user_file(str(token), SCOPES)
if credentials and credentials.expired and credentials.refresh_token:
    credentials.refresh(Request())
if not credentials or not credentials.valid:
    flow = InstalledAppFlow.from_client_secrets_file(str(client), SCOPES)
    credentials = flow.run_local_server(
        host='127.0.0.1', port=0, open_browser=True, timeout_seconds=300,
        authorization_prompt_message='Google sign-in opened. Select your channel account and approve access.',
        success_message='YouTube connection received. You can close this tab.')
token.write_text(credentials.to_json(), encoding='utf-8')
youtube = build('youtube', 'v3', credentials=credentials, cache_discovery=False)
result = youtube.channels().list(part='snippet', mine=True).execute()
channels = [{'id': c['id'], 'title': c['snippet']['title'],
             'custom_url': c['snippet'].get('customUrl', '')} for c in result.get('items', [])]
if len(channels) != 1:
    print(json.dumps({'status': 'channel_selection_required', 'channels': channels}, ensure_ascii=False))
    raise SystemExit(2)
config_path = root / 'config/youtube-upload.json'
config = json.loads(config_path.read_text(encoding='utf-8-sig'))
expected = config.get('channel_handle', '').lstrip('@')
channel = channels[0]
if channel['custom_url'].lstrip('@') != expected:
    print(json.dumps({'status': 'channel_mismatch', 'channel': channel}, ensure_ascii=False))
    raise SystemExit(3)
config.update(channel_id=channel['id'], channel_title=channel['title'],
              status='connected_awaiting_final_video')
config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': 'connected', 'channel': channel, 'uploaded': False}, ensure_ascii=False))
