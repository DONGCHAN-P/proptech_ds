"""Deliver this frozen draft only to the configured, verified own private chat."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import os
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from notify import telegram as tg

OUT=ROOT/'video-agent-studio/episodes/regional-price-recovery-20261022/outputs/script-review-v2'
RECEIPT=ROOT/'output/telegram_deliveries/regional_script_v2.json'
if RECEIPT.exists() and json.loads(RECEIPT.read_text(encoding='utf8')).get('ok'):
    print(json.dumps({'ok':True,'already_delivered':True,'receipt':str(RECEIPT)},ensure_ascii=False))
    raise SystemExit(0)
checks=json.loads((OUT/'package_checks.json').read_text(encoding='utf8'))
state=json.loads((OUT.parent.parent/'state.json').read_text(encoding='utf8'))
claude_ok=state.get('claude_collaboration',{}).get('actual_generated_text',False)
for rel, meta in checks['files'].items():
    path=ROOT/rel
    assert hashlib.sha256(path.read_bytes()).hexdigest()==meta['sha256'],rel
archive=OUT/'지역별_영상대본_v2.zip'
files={
    '지역별_영상대본_v2.md':OUT/'script_v2.md',
    '낭독대본_v2.txt':OUT/'narration_v2.txt',
    '자료화면_설계_v2.md':OUT/'visual_storyboard.md',
    '수치와_자료근거.md':OUT/'수치와_자료근거.md',
    '클로드_협업상태.md':OUT/'클로드_협업상태.md',
}
if claude_ok:
    files['클로드_편집검토.md']=OUT/'claude_editorial_review_v2.md'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
    for name,path in files.items():
        z.write(path,name)
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    assert set(z.namelist())==set(files)
    for name,path in files.items():
        assert z.read(name)==path.read_bytes()
token,cid=tg.creds()
expected_user=os.environ.get('TELEGRAM_USER_ID','').strip() or (cid if cid.isdigit() else '')
assert token and cid and cid.isdigit() and cid==expected_user,'Private recipient not configured/verified'
chat=tg._post('getChat',token,data={'chat_id':cid})
assert chat.get('ok') and chat['result'].get('type')=='private' and str(chat['result']['id'])==cid,'Recipient verification failed'
caption=('지역별 영상 대본 v2 검토 초안\n'
         '집값 다 올랐다는데, 왜 내 지역은 아직일까?\n'
         '7개 지역의 고점·반등·회복 / 3·5·10년 비교 / 공급·순이동 예시\n'
         '대본·낭독본·문단별 자료화면 설계·수치 근거를 담았습니다. 음성·영상은 아직 제작하지 않았습니다.\n'
         + ('Codex 작성·통합 + Claude Opus(max) 편집 검토 + 독립 수치 검수 반영본입니다.' if claude_ok else 'Codex 작성·독립 수치 검수본입니다. 승인 후 Claude 호출도 실패하여 실제 Claude 검토는 포함하지 않았습니다.'))
with archive.open('rb') as f:
    response=tg._post('sendDocument',token,data={'chat_id':cid,'caption':caption},files={'document':(archive.name,f,'application/zip')},timeout=45)
message=response.get('result') or {}
record={'at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'ok':bool(response.get('ok')),'private_recipient_verified':True,'filename':archive.name,'bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'message_id':message.get('message_id'),'document_file_name':(message.get('document') or {}).get('file_name'),'script_sha256':hashlib.sha256((OUT/'script_v2.md').read_bytes()).hexdigest(),'status':'review_draft_not_approved','claude_status':state.get('claude_collaboration',{}).get('status')}
if not record['ok']:
    record['error']=tg.mask(response.get('error','Unknown error'),token)
RECEIPT.parent.mkdir(parents=True,exist_ok=True)
RECEIPT.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(record,ensure_ascii=False,indent=2))
raise SystemExit(0 if record['ok'] else 1)
