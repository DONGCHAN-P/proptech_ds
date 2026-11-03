"""Deliver the reviewed silent working preview, never label it a completed film."""
from pathlib import Path
import datetime as dt,hashlib,json,os,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from notify import telegram as tg
EP=ROOT/'video-agent-studio/episodes/regional-price-recovery-20261022'
OUT=EP/'outputs/production-v1-jun';RECEIPT=ROOT/'output/telegram_deliveries/regional_motion_preview_v2.json'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks=read(OUT/'prep_package_checks.json');video=ROOT/checks['video']['path']
assert checks['required_open']==0 and not checks['voice_generated'] and not checks['timing_locked']
for p,m in checks['files'].items():assert sha(ROOT/p)==m['sha256'],p
assert sha(video)==checks['video']['sha256']
if RECEIPT.exists()and read(RECEIPT).get('ok'):
    assert read(RECEIPT)['sha256']==sha(video)
    print(json.dumps({'ok':True,'already_delivered':True}));raise SystemExit(0)
cfg=read(ROOT/'config/video_telegram_bridge.json');assert cfg['private_chat_only']
token,cid=tg.creds();expected=os.environ.get('TELEGRAM_USER_ID','').strip()or(cid if cid.isdigit()else'')
assert token and cid.isdigit()and cid==expected
chat=tg._post('getChat',token,data={'chat_id':cid})
assert chat.get('ok')and chat['result']['type']=='private'and str(chat['result']['id'])==cid
caption=('지역별 회복 영상 · 수정 모션 시안 v2\n24초·무음·1080p/30fps. 전체 본편의 실제 음성·길이는 아직 확정 전입니다.\n'
'①2006년 이후 지역별 흐름 ②인천의 31분기 회복 구간 ③전체 거래가격과 조건을 맞춘 지수 비교\n'
'12장면·39문단 편집 구성을 준비했고, 인천 지수 기준값과 회복일 라벨을 수정해 검수했습니다.\n'
'Jun 음성 예산은 최대5,807 포함 크레딧·추가 결제0원으로 확인 요청 중입니다. 결정 ID: 5fe307eed02c. 대본 v3 승인과 별도이며 업로드는 실행하지 않습니다.')
with video.open('rb')as f:
    response=tg._post('sendVideo',token,data={'chat_id':cid,'caption':caption,'supports_streaming':'true','duration':'24','width':'1920','height':'1080'},files={'video':(video.name,f,'video/mp4')},timeout=45)
msg=response.get('result')or{}
record={'at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'ok':bool(response.get('ok')),
 'private_recipient_verified':True,'message_id':msg.get('message_id'),'filename':video.name,'bytes':video.stat().st_size,
 'sha256':sha(video),'status':'silent_working_preview_not_completed_film','voice_generated':False,'timing_locked':False}
if not record['ok']:record['error']=tg.mask(response.get('error','Unknown error'),token)
RECEIPT.parent.mkdir(parents=True,exist_ok=True);RECEIPT.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
if record['ok']:
    state=read(EP/'state.json');state['production_preview_telegram_receipt']=RECEIPT.relative_to(ROOT).as_posix()
    (EP/'state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(record,ensure_ascii=False));raise SystemExit(0 if record['ok'] else 1)
