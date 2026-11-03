"""Send the user's reviewed HTML report through the existing private Telegram bot."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from notify import telegram as TG

OUT=ROOT/'reports/regional_growth_report_v1'
manifest=json.loads((OUT/'source_manifest.json').read_text(encoding='utf8'))
report=OUT/manifest['report']
digest=hashlib.sha256(report.read_bytes()).hexdigest()
assert digest==manifest['sha256']
release=json.loads((OUT/'qa/release_checks.json').read_text(encoding='utf8'))
assert release['status']=='pass' and release['report_sha256']==digest
receipt_path=ROOT/'output/telegram_deliveries/regional_growth_report_v1.json'
if receipt_path.exists():
    existing=json.loads(receipt_path.read_text(encoding='utf8'))
    if existing.get('ok') and existing.get('report_sha256')==digest:
        print(json.dumps({'status':'already_sent','message_id':existing['message_id']}))
        raise SystemExit(0)

bridge=json.loads((ROOT/'config/video_telegram_bridge.json').read_text(encoding='utf8'))
assert bridge.get('private_chat_only') is True
token,chat_id=TG.creds()
if not token or not chat_id:
    print(json.dumps({'ok':False,'reason':'telegram_credentials_unavailable'}))
    raise SystemExit(1)
expected_user=os.getenv(bridge.get('sender_user_id_env','TELEGRAM_USER_ID'),'').strip()
if expected_user and expected_user!=chat_id:
    print(json.dumps({'ok':False,'reason':'configured_private_recipient_mismatch'}))
    raise SystemExit(1)
chat=TG._post('getChat',token,data={'chat_id':chat_id})
if not chat.get('ok') or chat.get('result',{}).get('type')!='private':
    print(json.dumps({'ok':False,'reason':'private_recipient_verification_failed','api_code':chat.get('code')}))
    raise SystemExit(1)

caption=('지역별 집값 상승·고점 회복 분석 보고서 v1\n'
         '서울·경기·인천·부산·대구·대전·세종 / 2026년 2분기까지\n\n'
         '장기·최근 꺾은선, 3·5·10년 연복리, 고점 회복, 표본 민감도, 연 2% 가정의 타당성, 자료·방법·출처를 담았습니다.\n'
         '자체 지표 기반 탐색 자료이며 공식 지수 대조는 남아 있습니다. 경기 회복 판정은 표본 기준에 민감하고 광주는 자료 미확보로 제외했습니다.\n\n'
         'HTML 파일을 다운로드해 브라우저로 열면 인터넷 연결 없이 볼 수 있습니다.')
assert len(caption)<=1024
with report.open('rb') as handle:
    response=TG._post('sendDocument',token,data={'chat_id':chat_id,'caption':caption},
                      files={'document':(report.name,handle,'text/html')},timeout=60)
receipt_path.parent.mkdir(parents=True,exist_ok=True)
if not response.get('ok'):
    failure={'ok':False,'api_code':response.get('code'),'error':TG.mask(response.get('error','send_failed'),token),
             'report_sha256':digest,'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    receipt_path.write_text(json.dumps(failure,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(failure,ensure_ascii=False))
    raise SystemExit(1)
message=response['result']
document=message.get('document',{})
receipt={'ok':True,'message_id':message['message_id'],'telegram_date':message.get('date'),
         'file_name':document.get('file_name',report.name),'sent_bytes':document.get('file_size'),
         'local_bytes':report.stat().st_size,'report':report.relative_to(ROOT).as_posix(),'report_sha256':digest,
         'private_recipient_verified':True,'sent_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'authorization':'Direct user request: 완성되면 텔래그램으로 보내줘'}
receipt_path.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'ok':True,'message_id':receipt['message_id'],'file_name':receipt['file_name'],'bytes':receipt['local_bytes']},ensure_ascii=False))
