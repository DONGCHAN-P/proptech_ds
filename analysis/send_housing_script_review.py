from pathlib import Path
import sys,json,hashlib
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from notify.telegram import send_file
EP=ROOT/'video-agent-studio/episodes/housing-choice-networth-20261020'
file=ROOT/'영상/매매전월세/대본.md'
receipt=EP/'outputs/script-review-v1/telegram_delivery_receipt.json'
assert not receipt.exists(),'Prior delivery attempt exists; inspect before sending again'
digest=hashlib.sha256(file.read_bytes()).hexdigest()
qa=json.loads((EP/'qa/script-review/final_review.json').read_text(encoding='utf-8-sig'))
assert qa['checked_script_sha256']==digest
assert not qa['open_critical_required']
record={'phase':'sending','sha256':digest,'file':str(file.relative_to(ROOT)),'requested_by':'direct_user_script_file_delivery_request','started_at':datetime.now(timezone.utc).isoformat(),'script_approval_changed':False,'paid_budget_changed':False}
receipt.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
sent=send_file(file,caption='매매·전세·월세 비교 대본 v1 · 검토용 초안\n예상 13~16분. 같은 집·초기자금·월예산으로 비교합니다. 수치는 실제 과거 성과가 아닌 가정 기반 10년 계산입니다. 대본 승인·음성 및 영상 제작은 아직 진행하지 않았습니다.',quiet=True)
record.update(phase='sent' if sent else 'failed',sent=sent,finished_at=datetime.now(timezone.utc).isoformat())
receipt.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'sent':sent,'sha256':digest,'receipt':str(receipt.relative_to(ROOT))},ensure_ascii=False))
assert sent,'Telegram file delivery failed'
