"""Send only the reviewed v2 deliverable to the user's configured Telegram.
Explicit authorization: latest direct user request. No receiver or webhook change.
"""
from pathlib import Path
import sys,json,hashlib
EP=Path(__file__).resolve().parent;ROOT=EP.parents[2];sys.path.insert(0,str(ROOT))
from notify import telegram

movie=EP/'outputs/v2/data_insight_30s_v2.mp4'
receipt=EP/'outputs/v2/telegram_receipt.json'
assert movie.is_file(),'Final v2 MP4 missing'
sha=hashlib.sha256(movie.read_bytes()).hexdigest()
manifest=json.loads((EP/'outputs/v2/delivery_manifest.json').read_text(encoding='utf8'))
assert manifest['sha256']==sha,'Deliverable changed after final verification'
if receipt.exists():
 prev=json.loads(receipt.read_text(encoding='utf8'))
 if prev.get('status')=='sent' and prev.get('local_sha256')==sha:
  print(json.dumps({'status':'already_sent','message_id':prev['message_id']}));raise SystemExit()
qa=json.loads((EP/'qa-v2/findings.json').read_text(encoding='utf8'))
issues=qa if isinstance(qa,list) else qa.get('findings',qa.get('issues',[]))
assert not [x for x in issues if x.get('severity') in ['critical','required'] and not x.get('status','').startswith('closed')], 'Open required QA issue'
assert movie.stat().st_size<49*1024*1024,'File exceeds Telegram delivery size limit'
tok,cid=telegram.creds()
if not tok or not cid:raise SystemExit('Configured Telegram credentials missing')
configured_chat=None
for line in (ROOT/'.env').read_text(encoding='utf-8-sig').splitlines():
 if line.strip().startswith('TELEGRAM_CHAT_ID') and '=' in line:
  configured_chat=line.split('=',1)[1].strip().strip('\"').strip("'")
if configured_chat:assert cid==configured_chat,'Recipient differs from current workspace configuration'
caption='Data Insight 30초 수정본 v2\n사람이 모니터·노트북·휴대폰을 확인하는 장면으로 수정했습니다. 업무 UI는 기기의 실제 화면 안에 원근·움직임을 맞춰 합성했습니다.\n한글 별도 합성 · 무대사/BGM · 1920×1080/30fps\n검수: 장면·경계 프레임/화면 합성/한글/기술 디코드 확인. 연속 재생·실제 음악 청취는 미실시입니다.\n인물은 AI 재현이며 실제 직원 촬영이 아닙니다.'
with movie.open('rb') as fh:
 res=telegram._post('sendDocument',tok,data={'chat_id':cid,'caption':caption},files={'document':('Data_Insight_30s_v2.mp4',fh,'video/mp4')},timeout=300)
if not res.get('ok'):
 safe={'status':'failed','local_sha256':sha,'reason':telegram.explain(res)}
 receipt.write_text(json.dumps(safe,ensure_ascii=False,indent=2),encoding='utf8')
 print(json.dumps(safe,ensure_ascii=False));raise SystemExit(1)
message=res['result'];doc=message.get('document',{})
record=dict(status='sent',version='v2',method='sendDocument',message_id=message['message_id'],date=message.get('date'),file_name=doc.get('file_name'),remote_file_size=doc.get('file_size'),local_file_size=movie.stat().st_size,local_sha256=sha,recipient='existing configured TELEGRAM_CHAT_ID',authorization='latest direct user request: 작업결과 텔레그램으로 보내줘')
receipt.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'status':'sent','message_id':record['message_id'],'bytes':record['remote_file_size']}))
