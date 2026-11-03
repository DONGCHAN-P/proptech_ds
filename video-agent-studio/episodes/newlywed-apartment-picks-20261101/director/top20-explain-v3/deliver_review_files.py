"""Deliver requested revision review files to the existing private Telegram chat.

Conversation text is mirrored by the running bridge; this sends documents only.
Each exact file is attempted once. No polling, retries, other recipients or video upload.
"""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys
D=Path(__file__).resolve().parent; E=D.parents[1]; R=E.parents[2]
sys.path.insert(0,str(R))
from notify import telegram
from notify.video_decisions import write

def main():
    preference=json.loads((D/'file_delivery_status.json').read_text(encoding='utf-8'))
    if not preference.get('telegram_files_authorized'):
        raise SystemExit('Local-only review selected; file transmission is not authorized')
    decision=json.loads((D/'script_decision.json').read_text(encoding='utf-8'))
    allowed={'대본_v6.md','지역별_가격기준표.md','대표화면.jpg'}; results=[]
    dest=D/'file_delivery'; dest.mkdir(exist_ok=True)
    for artifact in decision['artifacts']:
        path=R/artifact['path']
        if path.name not in allowed:continue
        digest=hashlib.sha256(path.read_bytes()).hexdigest();assert digest==artifact['sha256']
        receipt=dest/(path.stem+'.json')
        if receipt.exists():
            old=json.loads(receipt.read_text(encoding='utf-8'))
            assert old['sha256']==digest and old['status']=='accepted','No automatic file resend'
            results.append(old);continue
        record={'path':artifact['path'],'sha256':digest,'script_gate_id':decision['id'],
                'scope':'requested TOP20 revision review documents in the existing authenticated private conversation',
                'transport':'existing Telegram Bot API sendDocument','status':'started',
                'automatic_retry':False,'started_at':datetime.now(timezone.utc).isoformat()}
        write(receipt,record)
        try:
            ok=telegram.send_file(path,caption='TOP20 v6 · '+path.name,quiet=True)
        except Exception as exc:
            record.update(status='failed',error_type=type(exc).__name__);write(receipt,record)
            raise SystemExit('Document delivery failed; no automatic retry')
        record.update(status='accepted' if ok else 'failed',finished_at=datetime.now(timezone.utc).isoformat())
        write(receipt,record); results.append(record)
        if not ok:raise SystemExit('Document delivery not accepted; no automatic retry')
    print(json.dumps({'documents':len(results),'accepted':sum(r['status']=='accepted'for r in results),
                      'duplicate_plain_text_messages_sent':0,'automatic_retry':False},ensure_ascii=False))
if __name__=='__main__':main()
