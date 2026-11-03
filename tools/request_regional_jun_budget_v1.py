"""Create and optionally deliver the exact Jun credit proposal; no synthesis."""
from pathlib import Path
import json
import sys
import os
import datetime as dt
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from notify import video_decisions,telegram as tg
EP=ROOT/'video-agent-studio/episodes/regional-price-recovery-20261022'
OUT=EP/'outputs/production-v1-budget'
def read(p): return json.loads(p.read_text(encoding='utf8'))
def write(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
b=read(OUT/'budget_proposal.json')
assert b['account_checks_passed'] and b['cap_fits_included'] and b['additional_cash_usd_cap']==0
p=OUT/'budget_decision.json'
if p.exists(): d=read(p)
else:
    d=video_decisions.create(EP.name,'budget',f"지역별가격회복 v3 Jun 음성: 본문 {b['input_characters']}자, 수정 포함 {b['included_credit_cap']}크레딧 한도, 추가 결제0·충전없음·자동재시도없음. script SHA256 {b['script_sha256']}")
    d.update(artifact_hashes={'script_v3.md':b['script_sha256'],'narration_manifest':b['narration_manifest_sha256']},included_credit_cap=b['included_credit_cap'],additional_cash_usd_cap=0,automatic_retry=False)
    video_decisions.write(video_decisions.STORE/'decisions'/f"{d['id']}.json",d);write(p,d)
state=read(EP/'state.json');state.update(budget_status='awaiting_5807_included_credit_cap_approval',budget_decision_id=d['id']);write(EP/'state.json',state)
receipt=OUT/'telegram_budget_receipt.json'
if '--send' in sys.argv and not (receipt.exists() and read(receipt).get('ok')):
    token,cid=tg.creds();uid=os.environ.get('TELEGRAM_USER_ID','').strip() or(cid if cid.isdigit() else '')
    assert token and cid.isdigit() and cid==uid
    c=tg._post('getChat',token,data={'chat_id':cid})
    assert c.get('ok') and c['result']['type']=='private' and str(c['result']['id'])==cid
    text=(f"지역별 영상 v3 제작 착수 · Jun 음성 예산 확인\n대본 승인 반영, 차트·편집 구성 준비 중입니다.\n본문 {b['input_characters']:,}크레딧 예상, 수정 여유 포함 최대 {b['included_credit_cap']:,}크레딧. 현재 포함 잔여 {b['included_remaining']:,}. 추가 결제0원·충전없음·자동재시도없음. 로컬 렌더, 신규 유료 이미지/음악없음.\nAGENTS.md의 유료 생성 전 예산·상한 확인 규칙에 따른 요청입니다.\n예산 결정 ID: {d['id']}\n승인: /approve {d['id']}\n보류·수정: /revise {d['id']} 내용\n이 승인은 음성 크레딧 사용만 해당하며 업로드 승인은 별도입니다.")
    r=tg._post('sendMessage',token,data={'chat_id':cid,'text':text},timeout=30)
    safe={'ok':bool(r.get('ok')),'message_id':(r.get('result')or{}).get('message_id'),'at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'decision_id':d['id'],'private_recipient_verified':True}
    write(receipt,safe);assert safe['ok']
print(json.dumps({'budget_decision_id':d['id'],'credit_cap':b['included_credit_cap'],'cash_cap':0,'telegram_sent':receipt.exists() and read(receipt).get('ok')},ensure_ascii=False))
