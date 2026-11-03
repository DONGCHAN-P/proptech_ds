from pathlib import Path
import json,sys
e=Path(__file__).resolve().parent;sys.path.insert(0,str(e.parents[2]))
from notify import telegram
out=e/'outputs/video-review-v8'
d=json.loads((out/'completed_decision.json').read_text(encoding='utf-8'))
sent=telegram.send('왕숙 전체본 v8 렌더·독립 검수·납품 ZIP 정리가 완료됐습니다. 14분50.67초/1080p30, 새 벡터 인트로·전편 연결·구독 안내·기존 인트로/아웃트로 복원·전체 지도 수정이 반영됐습니다.\n영상: '+str(out/'namyangju-landuse_full_v8.mp4')+'\nZIP: '+str(out/'namyangju-landuse_full_v8_delivery.zip')+'\n77개 실제 프레임과 전체26720프레임 흰자막바 확인, 필수 미해결0건. 실제청취·연속재생 미확인. 새음성94크레딧, 추가결제0원.\n이 완성본 검토 승인: /approve '+d['id']+'\n수정: /revise '+d['id']+' 수정내용\n업로드·공개 승인은 별도입니다.',quiet=True)
(out/'telegram_ready_receipt.json').write_text(json.dumps({'text_sent':sent,'file_sent':False,'completed_decision_id':d['id']},indent=2),encoding='utf-8')
print(json.dumps({'text_sent':sent,'file_sent':False}))
