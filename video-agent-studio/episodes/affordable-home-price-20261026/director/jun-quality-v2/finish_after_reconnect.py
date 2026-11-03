"""One-shot authorized batch continuation after verified, user-completed OAuth."""
from pathlib import Path
import json,subprocess,time,os
from datetime import datetime,timezone
DIR=Path(__file__).resolve().parent;EP=DIR.parents[1];ROOT=EP.parents[2]
PY=ROOT/'tools/python311/python.exe'
STATUS=DIR/'auto_upload_after_reconnect_20261028.json';AUTH=DIR/'reconnect_status.json'
BATCH=EP/'outputs/jun-quality-v2/release/private-upload-20261028'
LOCK=DIR/'private_upload_continuation.lock'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def status(phase,**extra):
    d={'phase':phase,'updated_at':datetime.now(timezone.utc).isoformat(),'visibility':'private','episode_id':EP.name,**extra}
    STATUS.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(d,ensure_ascii=False),flush=True)
def run(script,*args):
    log=DIR/(Path(script).stem+'.continuation.log')
    with log.open('ab') as f:r=subprocess.run([str(PY),'-B','-X','utf8',str(ROOT/script),*args],stdout=f,stderr=subprocess.STDOUT,cwd=ROOT)
    if r.returncode:raise RuntimeError(Path(script).name+' failed; inspect local log before retry')
try:
    fd=os.open(LOCK,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.write(fd,str(os.getpid()).encode());os.close(fd)
except FileExistsError:
    raise SystemExit('Another continuation owns the batch; do not upload twice')
try:
    assert read(BATCH/'preflight.json')['status']=='passed'
    expected_link=read(AUTH)['local_sign_in_link']
    status('waiting_for_user_reconnect',local_sign_in_link=expected_link)
    deadline=time.monotonic()+900
    while time.monotonic()<deadline:
        a=read(AUTH)
        if a['status']=='connected':break
        if a['status'] in ['failed','declined','expired']:raise RuntimeError('User reconnect did not complete: '+a['status'])
        time.sleep(2)
    else:raise RuntimeError('Reconnect wait expired; no uploads started')
    assert a['channel_id']=='UCr_mTC0x_Uobv6MrIsOkrXw' and a['same_existing_scopes'] is True
    status('uploading_authorized_private_batch')
    uploader=(DIR/'upload_private_current.py').relative_to(ROOT).as_posix()
    run(uploader,'upload')
    status('verifying_processing_and_captions')
    for attempt in range(21):
        run(uploader,'verify')
        receipts=[read(BATCH/name/'upload_receipt.json') for name in ['main','promo','summary']]
        complete=all(r.get('private_verified') and r.get('verification',{}).get('processingDetails',{}).get('processingStatus')=='succeeded' and r.get('caption_serving_verified') for r in receipts)
        if complete:break
        if attempt<20:time.sleep(15)
    else:raise RuntimeError('Uploads exist, processing/captions need later verification; do not reupload')
    run((DIR/'finalize_private_uploads.py').relative_to(ROOT).as_posix())
    run('tools/refresh_video_shelf.py')
    report=read(BATCH/'completion.json')
    status('private_uploaded_verified',items=report['items'],new_uploads=3,public_release=False)
except Exception as exc:
    status('needs_attention',error_type=type(exc).__name__,reason=str(exc),upload_receipts=str(BATCH.relative_to(ROOT)))
    raise SystemExit(1)
finally:
    LOCK.unlink(missing_ok=True)
