import json,sys
from pathlib import Path
from datetime import datetime,timezone
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from notify import telegram
o=root/'video-agent-studio/episodes/namyangju-wangsuk-20261014/outputs/thumbnail-ab-v1'
p=o/'telegram_delivery.json';r=json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}
def save():p.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
if not r.get('file_sent'):
 assert telegram.send_file(o/'B_ai_city_test.jpg',caption='왕숙 썸네일 B안 · 신도시 분석 시리즈 · AI 개념 도시',quiet=True)
 r['file_sent']=True;save()
if not r.get('message_sent'):
 assert telegram.send(f'''왕숙 새 썸네일 B안을 만들었습니다. 광교·동탄 편처럼 왼쪽 큰 지역명과 오른쪽 도시 야경을 연결했습니다.

현재 썸네일 A는 보존했고 공개 이미지와 대조했습니다. 새 B는 업로드용579KB JPEG로 준비했습니다.
공식 A/B 테스트는 YouTube Studio에서 썸네일만 비교하도록 준비했지만, 이 대화에 연결된 브라우저가 없어 아직 등록하지 못했습니다. 영상 제목/설명/기존 썸네일은 그대로입니다.

Studio: https://studio.youtube.com/video/T_GBxTRgRSc/edit
등록파일 A: {o / 'A_plan_control.jpg'}
등록파일 B: {o / 'B_ai_city_test.jpg'}
로그인된 브라우저 연결이 되면 기존 A와 새 B 두 장으로 테스트 등록을 마무리할 수 있습니다.''',quiet=True)
 r.update(message_sent=True,sent_at=datetime.now(timezone.utc).isoformat(),test_started=False);save()
print('Generated B thumbnail and accurate pending-test status delivered to Telegram')
