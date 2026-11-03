import sys,json
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8');sys.path.insert(0,'C:/projects/realestate_reco')
from notify import telegram as tg
sent=tg.send('남양주 실제 사진 6장과 지역 지도 데이터를 확보했습니다. 전편과 이어지는 AI 개념 장면도 준비해, 지도 이동·사진·도표를 섞는 구성으로 편집을 보강하고 있습니다.',quiet=True)
Path(__file__).with_name('notification_v4.json').write_text(json.dumps({'message_type':'short_status_text_only','sent':sent},ensure_ascii=False,indent=2),'utf-8');print({'sent':sent})
