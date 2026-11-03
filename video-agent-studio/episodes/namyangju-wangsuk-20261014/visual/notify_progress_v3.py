import sys,json
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8');sys.path.insert(0,'C:/projects/realestate_reco')
from notify import telegram as tg
sent=tg.send('남양주 영상 제작 진행 중입니다. 공식 왕숙1·2 계획도와 실제 지리 데이터 기반 지역지도를 확보했고, 음성 생성과 편집을 진행하고 있습니다.',quiet=True)
Path(__file__).with_name('notification_v3.json').write_text(json.dumps({'message_type':'short_status_text_only','sent':sent},ensure_ascii=False,indent=2),'utf-8')
print({'sent':sent})
