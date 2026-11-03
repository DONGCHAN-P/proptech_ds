"""Send only the scoped review deliverables to the existing verified private chat."""
from pathlib import Path
import argparse, datetime as dt, hashlib, json, os, sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from notify import telegram as tg
EP=ROOT/'video-agent-studio/episodes/regional-price-recovery-20261022'
DEST=EP/'director/production-v1/delivery'
RECEIPT=ROOT/'output/telegram_deliveries/regional_full_visual_review_v1.json'

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb')as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
    return h.hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--video',help='Optional explicitly labelled smaller Telegram review copy')
    args=ap.parse_args();m=read(DEST/'delivery_manifest.json');archive=read(DEST/'archive_manifest.json')
    assert m['required_open']==0 and m['voice_generated']is False and m['timing_locked']is False
    for p,meta in m['files'].items():assert sha(ROOT/p)==meta['sha256'],p
    assert sha(ROOT/m['video']['path'])==m['video']['sha256']
    video=(ROOT/args.video).resolve()if args.video else ROOT/m['video']['path'];video.relative_to(EP)
    if args.video:
        copy=read(DEST/'telegram_copy_manifest.json')
        assert copy['path']==video.relative_to(ROOT).as_posix()and copy['sha256']==sha(video)
        assert copy['master_sha256']==m['video']['sha256']and copy['full_decode']=='pass'
    assert video.stat().st_size<=48_000_000,'Prepare a labelled review copy below the bot limit'
    packet=ROOT/archive['path'];assert sha(packet)==archive['sha256']
    config=read(ROOT/'config/video_telegram_bridge.json');assert config['private_chat_only']
    token,cid=tg.creds();expected=os.environ.get('TELEGRAM_USER_ID','').strip()or(cid if cid.isdigit()else'')
    assert token and cid.isdigit()and cid==expected
    chat=tg._post('getChat',token,data={'chat_id':cid})
    assert chat.get('ok')and chat['result']['type']=='private'and str(chat['result']['id'])==cid
    if RECEIPT.exists():
        old=read(RECEIPT)
        if old.get('ok'):
            assert old['master_sha256']==m['video']['sha256'];print(json.dumps({'ok':True,'already_delivered':True}));return
        assert old.get('status')not in ['request_started','delivery_uncertain'],'Avoid duplicate sends after an uncertain delivery'
    record={'at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'status':'request_started','ok':False,
        'private_recipient_verified':True,'master_sha256':m['video']['sha256'],'voice_generated':False,'timing_locked':False,'items':[]}
    RECEIPT.parent.mkdir(parents=True,exist_ok=True);write(RECEIPT,record)
    duration=round(m['video']['duration']);minutes,seconds=divmod(duration,60)
    quality='텔레그램 용량에 맞춘 축소 검토용 사본입니다. 원본은 로컬1080p30으로 보존했습니다.'if args.video else '1080p·30fps 원본 검토 파일입니다.'
    caption=(f'지역별 가격 회복 · 전체 화면 검토본 v1\n{minutes}분 {seconds}초 · 12장면·39문단\n'
        '요청하신 대로 음성 생성은 보류했습니다. 차트·자막·기존 채널 브랜드와 BGM으로 구성했으며 길이는 임시값입니다.\n'
        f'{quality}\n'
        '실제 인코딩 표본·경계 프레임과 전체 디코드를 검사했습니다. 연속 재생·실제 청취·모바일 재생은 미검수입니다.\n'
        'Thinking Music by Kevin MacLeod | incompetech.com | CC BY4.0\nhttps://creativecommons.org/licenses/by/4.0/')
    for p,text in [(video,caption),(packet,'검토안내·임시 자막·승인 대본 v3·수치 자료·출처/권리·검수 기록입니다. 음성 보류 상태를 유지하며 외부 게시를 실행하지 않았습니다.')]:
        with p.open('rb')as stream:
            response=tg._post('sendDocument',token,data={'chat_id':cid,'caption':text},files={'document':(p.name,stream,'application/octet-stream')},timeout=55)
        result=response.get('result')or{}
        item={'filename':p.name,'bytes':p.stat().st_size,'sha256':sha(p),'ok':bool(response.get('ok')),'message_id':result.get('message_id')}
        if not item['ok']:
            item['error']=tg.mask(response.get('error','Unknown'),token)
            record['items'].append(item);record['status']='delivery_uncertain';write(RECEIPT,record)
            print(json.dumps({'ok':False,'status':record['status'],'error':item['error']},ensure_ascii=False));raise SystemExit(1)
        record['items'].append(item);write(RECEIPT,record)
        print(json.dumps({'sent':p.name,'message_id':item['message_id']}),flush=True)
    record.update(ok=True,status='delivered_full_visual_review_voice_deferred');write(RECEIPT,record)
    state=read(EP/'state.json');state['production_review_telegram_receipt']=RECEIPT.relative_to(ROOT).as_posix();write(EP/'state.json',state)
    print(json.dumps({'ok':True,'files':len(record['items']),'status':record['status']}))

if __name__=='__main__':main()
