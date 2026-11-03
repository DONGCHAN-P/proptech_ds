from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib
e=Path(__file__).resolve().parent;sys.path.insert(0,str(e.parents[2]))
from notify import telegram
p=e/'outputs/readability-cta-v15/telegram_progress_front.json';assert not p.exists()
message='남양주 v15 중간 진행: 일자리 구간 왼쪽 전체지도와 시간축 여백을 수정했고, 실제 렌더에서 확인했습니다. 왕숙역 설명에는 왕숙1 남측 지도를, 3분8초의 일패역 설명부터 왕숙2 지도를 보여주도록 실제 전환 프레임도 검수했습니다. 뒤쪽 시간축·학교 인출선과 추가 마무리 멘트/구독·좋아요 모션을 연결 중입니다. 추가 음성은59자·24포함크레딧 사용, 추가 결제0원입니다. 전체본은 말끝3초 뒤 기존 아웃트로를 연결해 약15분32초가 됩니다. 최종 파일 검수가 끝나면 경로와 완료 검토 안내를 보내겠습니다.'
assert telegram.send(message,quiet=True),'Telegram send failed'
p.write_text(json.dumps({'sent_at':datetime.now(timezone.utc).isoformat(),'message_sent':True,'file_sent':False,'message_sha256':hashlib.sha256(message.encode()).hexdigest(),'scope':'jobs/rail actual partial QA and ongoing full assembly'},ensure_ascii=False,indent=2),encoding='utf-8')
print('v15 inspected front progress text sent.')
