"""User-clicked loopback OAuth entry. Same existing scopes/channel; no uploads."""
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlsplit, parse_qs
from datetime import datetime,timezone
import json,sys,time,secrets,html
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/youtube_deps'))
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
SCOPES=['https://www.googleapis.com/auth/youtube.upload','https://www.googleapis.com/auth/youtube.readonly','https://www.googleapis.com/auth/youtube.force-ssl']
OUT=ROOT/'video-agent-studio/episodes/affordable-home-price-20261026/director/jun-quality-v2'
STATUS=OUT/'reconnect_status.json'
old=json.loads((ROOT/'config/youtube-token.json').read_text(encoding='utf-8'))
assert set(SCOPES)==set(old['scopes']),'Never expand existing scope'
expected=json.loads((ROOT/'config/youtube-upload.json').read_text(encoding='utf-8-sig'))['channel_id']
flow=InstalledAppFlow.from_client_secrets_file(str(ROOT/'config/youtube-client-secret.json'),SCOPES)
complete=False
def save(d):STATUS.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass # OAuth query values must never appear in logs.
    def reply(self,code,body):
        data=('<!doctype html><meta charset="utf-8"><title>YouTube 재연결</title><main style="max-width:700px;margin:70px auto;font:20px/1.7 sans-serif">'+body+'</main>').encode('utf-8')
        self.send_response(code);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
    def do_GET(self):
        global complete
        parsed=urlsplit(self.path)
        if parsed.path=='/start':
            self.send_response(302);self.send_header('Location',auth_url);self.send_header('Cache-Control','no-store');self.end_headers();return
        if parsed.path=='/help':
            self.reply(200,'<h1>YouTube 계정 재연결</h1><p>기존 데이터로보는부동산 채널 계정으로 로그인합니다. 기존과 같은 YouTube 권한만 사용합니다.</p><p><a href="/start">Google 로그인 열기</a></p><p>연결 후 준비된 본편·쇼츠 두 편의 비공개 업로드를 이어갑니다.</p>');return
        if parsed.path!='/':self.reply(404,'페이지를 찾을 수 없습니다.');return
        q=parse_qs(parsed.query)
        if not q.get('state') or not secrets.compare_digest(q['state'][0],oauth_state):
            self.reply(400,'이 연결의 인증 응답이 아닙니다. 처음 제공한 연결 링크에서 다시 시작하세요.');return
        if q.get('error'):
            save({'status':'declined','error':'oauth_consent_not_completed','new_video_uploads':0});self.reply(400,'연결이 완료되지 않았습니다. 앱으로 돌아가 알려주세요.');complete=True;return
        if not q.get('code'):self.reply(400,'인증 응답이 없습니다.');return
        try:
            flow.fetch_token(code=q['code'][0])
            creds=flow.credentials
            assert creds.has_scopes(SCOPES),'Required existing scopes missing'
            y=build('youtube','v3',credentials=creds,cache_discovery=False)
            channels=y.channels().list(part='snippet',mine=True).execute(num_retries=0).get('items',[])
            assert len(channels)==1 and channels[0]['id']==expected,'Channel mismatch'
            token=ROOT/'config/youtube-token.json'
            backup=ROOT/'config'/('youtube-token.before-reconnect-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.json')
            backup.write_bytes(token.read_bytes());token.write_text(creds.to_json(),encoding='utf-8')
            save({'status':'connected','channel_id':expected,'same_existing_scopes':True,'new_video_uploads':0,'verified_at':datetime.now(timezone.utc).isoformat()})
            self.reply(200,'<h1>유튜브 연결 완료</h1><p>이 창을 닫아도 됩니다. 준비된 세 영상의 비공개 업로드를 이어갑니다.</p>')
            print(json.dumps({'connected':True,'channel_id':expected,'new_scope_grants':0,'uploads_in_auth_step':0}),flush=True)
        except Exception as exc:
            # Do not expose token exchange URLs/codes or credential-bearing exceptions.
            save({'status':'failed','error_type':type(exc).__name__,'new_video_uploads':0})
            self.reply(400,'계정 연결을 확인하지 못했습니다. 기존 연결 파일은 채널 확인에 성공한 경우에만 교체됩니다. 앱으로 돌아가 알려주세요.')
            print(json.dumps({'connected':False,'error_type':type(exc).__name__}),flush=True)
        complete=True
server=HTTPServer(('127.0.0.1',0),Handler);port=server.server_address[1];server.timeout=1
flow.redirect_uri=f'http://127.0.0.1:{port}/'
auth_url,oauth_state=flow.authorization_url(access_type='offline',prompt='consent')
start_url=f'http://127.0.0.1:{port}/help'
save({'status':'waiting_user_login','local_sign_in_link':start_url,'expires_after_seconds':900,'same_existing_scopes':True,'new_video_uploads':0})
print(json.dumps({'local_sign_in_link':start_url,'valid_for_minutes':15,'same_existing_scopes':True}),flush=True)
deadline=time.monotonic()+900
while not complete and time.monotonic()<deadline:server.handle_request()
server.server_close()
if not complete:save({'status':'expired','new_video_uploads':0});print('Local sign-in link expired.',flush=True)
raise SystemExit(0 if json.loads(STATUS.read_text(encoding='utf-8')).get('status')=='connected' else 2)
