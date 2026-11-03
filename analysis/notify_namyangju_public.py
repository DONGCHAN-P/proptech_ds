import json,sys
from pathlib import Path
from datetime import datetime,timezone
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from notify import telegram
o=root/'video-agent-studio/episodes/namyangju-wangsuk-20261014/outputs/youtube-release-v15'
mode=sys.argv[1];marker=o/f'telegram_{mode}.json'
if marker.exists():print('Already notified');raise SystemExit
main=json.loads((o/'main_upload_receipt.json').read_text(encoding='utf-8'))
assert main['verification']['status']['privacyStatus']=='public'
if mode=='main':
 message=f"남양주 왕숙 v15 본편 공개 업로드 완료\nhttps://youtu.be/{main['video_id']}\n썸네일·검색용 제목/설명·11개 챕터·자료 출처를 적용했습니다. 현재 유튜브 화질 처리 중입니다.\n쇼츠 3편(철도/입주시차, 주변84㎡가격비교, 왕숙2 A3/A1)은 세로 편집·검수 후 차례로 공개하겠습니다."
else:
 rows=[]
 for p in sorted(o.glob('short_*_upload_receipt.json')):
  d=json.loads(p.read_text(encoding='utf-8'));assert d['verification']['status']['privacyStatus']=='public'
  rows.append(d['verification']['snippet']['title']+'\nhttps://youtube.com/shorts/'+d['video_id'])
 assert len(rows)==3
 message='남양주 왕숙 쇼츠 3편도 공개 업로드했습니다.\n\n'+'\n\n'.join(rows)+f"\n\n본편: https://youtu.be/{main['video_id']}\n기존 음성 활용으로 새 유료 생성 비용은 없습니다."
assert telegram.send(message,quiet=True)
marker.write_text(json.dumps({'sent_at':datetime.now(timezone.utc).isoformat(),'sent':True,'file_sent':False},indent=2),encoding='utf-8')
print('Telegram public release notification sent')
