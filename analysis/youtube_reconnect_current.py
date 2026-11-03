"""Loopback OAuth repair using exactly the existing scopes and channel."""
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlsplit, parse_qs
from datetime import datetime, timezone
import html, json, secrets, sys, time, warnings

warnings.filterwarnings("ignore", category=FutureWarning)
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/youtube_deps"))
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
OUT = ROOT / "video-agent-studio/episodes/affordable-home-price-20261026/director/public-release-v5"
OUT.mkdir(exist_ok=True)
STATUS = OUT / "connection_status.json"
TOKEN = ROOT / "config/youtube-token.json"
old = json.loads(TOKEN.read_text(encoding="utf-8-sig"))
SCOPES = old["scopes"]
assert set(SCOPES) == {"https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.readonly", "https://www.googleapis.com/auth/youtube.force-ssl"}
EXPECTED = json.loads((ROOT / "config/youtube-upload.json").read_text(encoding="utf-8-sig"))["channel_id"]
flow = None
nonce = None
connected_at = None
status = {"status": "starting", "same_existing_scopes": True, "video_changes": 0}

def save(**updates):
    status.update(updates, updated_at=datetime.now(timezone.utc).isoformat())
    STATUS.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args): pass

    def reply(self, body, code=200):
        data = ("<!doctype html><meta charset='utf-8'><title>YouTube 연결</title><main style='max-width:760px;margin:64px auto;font:20px/1.7 sans-serif'>" + body + "</main>").encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        global flow, nonce, connected_at
        p = urlsplit(self.path)
        if p.path == "/health":
            self.reply("연결 도우미 실행 중 · " + html.escape(status["status"]))
            return
        if p.path in ("/help", "/") and not p.query:
            if status["status"] == "connected":
                self.reply("<h1>데이터로보는부동산 연결 완료</h1><p>이 창을 닫아도 됩니다. 앱에서 공개 업로드를 이어갑니다.</p>")
            else:
                detail = html.escape(status.get("user_message", ""))
                self.reply("<h1>YouTube 기존 계정 재연결</h1><p>‘데이터로보는부동산’ 채널을 선택해 주세요. 기존과 같은 YouTube 권한만 요청합니다.</p><p><a href='/start'>Google 로그인 열기</a></p><p>연결 확인 후 본편과 수정 쇼츠 두 편을 공개하고, 이번 편의 이전 비공개본을 정리합니다.</p><p>이 연결 단계 자체는 영상을 업로드·공개·삭제하지 않습니다.</p><p>" + detail + "</p>")
            return
        if p.path == "/start":
            flow = InstalledAppFlow.from_client_secrets_file(str(ROOT / "config/youtube-client-secret.json"), SCOPES)
            flow.redirect_uri = f"http://127.0.0.1:{server.server_port}/callback"
            nonce = secrets.token_urlsafe(32)
            url, _ = flow.authorization_url(access_type="offline", prompt="consent select_account", state=nonce)
            save(status="waiting_google_consent", user_message="")
            self.send_response(302)
            self.send_header("Location", url)
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            return
        if p.path != "/callback":
            self.reply("페이지를 찾을 수 없습니다.", 404)
            return
        q = parse_qs(p.query)
        if flow is None or not nonce or not secrets.compare_digest(q.get("state", [""])[0], nonce):
            self.reply("이 연결의 응답이 아닙니다. <a href='/help'>처음부터 다시 연결</a>", 400)
            return
        if q.get("error") or not q.get("code"):
            save(status="consent_not_completed", user_message="Google 연결이 완료되지 않았습니다. 다시 시도할 수 있습니다.")
            self.reply("연결이 완료되지 않았습니다. <a href='/help'>연결 페이지로 돌아가기</a>", 400)
            return
        stage = "token_exchange"
        try:
            flow.fetch_token(code=q["code"][0])
            credentials = flow.credentials
            stage = "scope_check"
            granted = set(credentials.granted_scopes or credentials.scopes or [])
            if not set(SCOPES).issubset(granted):
                save(status="missing_existing_scopes", failed_stage=stage, user_message="기존 YouTube 권한 일부가 선택되지 않았습니다. Google 권한 화면에서 기존 권한 항목을 모두 선택해 주세요.")
                self.reply("기존 권한이 모두 선택되지 않았습니다. <a href='/help'>다시 연결</a>", 400)
                return
            stage = "channel_check"
            youtube = build("youtube", "v3", credentials=credentials, cache_discovery=False)
            channels = youtube.channels().list(part="snippet", mine=True).execute(num_retries=0).get("items", [])
            if len(channels) != 1 or channels[0]["id"] != EXPECTED:
                names = ", ".join(c["snippet"]["title"] for c in channels) or "확인되는 채널 없음"
                save(status="channel_selection_needed", failed_stage=stage, observed_channels=[{"id": c["id"], "title": c["snippet"]["title"]} for c in channels], user_message="현재 인증된 채널: " + names + ". 데이터로보는부동산 채널로 다시 연결해 주세요.")
                self.reply("<h1>채널을 다시 선택해 주세요</h1><p>현재 인증된 채널: " + html.escape(names) + "</p><p>Google 계정 선택에서 데이터로보는부동산 채널을 선택해 주세요.</p><a href='/help'>다시 연결</a>", 400)
                return
            stage = "save_verified_credentials"
            assert credentials.refresh_token, "Refresh credential absent"
            backup = TOKEN.with_name("youtube-token.before-public-reconnect-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + ".json")
            backup.write_bytes(TOKEN.read_bytes())
            temporary = TOKEN.with_suffix(".verified.tmp")
            temporary.write_text(credentials.to_json(), encoding="utf-8")
            temporary.replace(TOKEN)
            connected_at = time.monotonic()
            save(status="connected", channel_id=EXPECTED, same_existing_scopes=True, user_message="")
            self.reply("<h1>데이터로보는부동산 연결 완료</h1><p>이 창을 닫아도 됩니다. 앱에서 공개 업로드를 이어갑니다.</p>")
            print(json.dumps({"status": "connected", "channel_id": EXPECTED, "video_changes": 0}), flush=True)
        except Exception as exc:
            save(status="connection_failed", failed_stage=stage, error_type=type(exc).__name__, user_message="계정 연결을 확인하지 못했습니다. 기존 인증 파일을 보존했습니다. 다시 시도할 수 있습니다.")
            self.reply("연결 확인에 실패했습니다. <a href='/help'>다시 연결</a>", 400)
            print(json.dumps({"status": "connection_failed", "stage": stage, "error_type": type(exc).__name__}), flush=True)

server = HTTPServer(("127.0.0.1", 0), Handler)
server.timeout = 1
link = f"http://127.0.0.1:{server.server_port}/help"
save(status="waiting_user_login", local_sign_in_link=link, expires_in_seconds=7200)
print(json.dumps({"local_sign_in_link": link, "same_existing_scopes": True}), flush=True)
deadline = time.monotonic() + 7200
while time.monotonic() < deadline and (connected_at is None or time.monotonic() - connected_at < 120):
    server.handle_request()
server.server_close()
if connected_at is None: save(status="expired")
