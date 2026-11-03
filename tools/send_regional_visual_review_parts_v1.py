"""Deliver smaller parts as a distinct fallback, preserving the uncertain attempt."""
from pathlib import Path
import datetime as dt,hashlib,json,os,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from notify import telegram as tg
EP=ROOT/'video-agent-studio/episodes/regional-price-recovery-20261022'
D=EP/'director/production-v1/delivery'
P=ROOT/'output/telegram_deliveries/regional_full_visual_review_v1_parts.json'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def clock(t):
    t=int(t);return f'{t//60:02d}:{t%60:02d}'
master=read(D/'delivery_manifest.json');split=read(D/'telegram_parts_v1/manifest.json');archive=read(D/'archive_manifest.json')
assert master['required_open']==0 and not master['voice_generated']and not master['timing_locked']
assert master['video']['sha256']==split['master_sha256']==sha(ROOT/master['video']['path'])
assert read(ROOT/'output/video_decisions/decisions/5fe307eed02c.json')['resolution']=='deferred_by_user'
assert read(ROOT/'output/telegram_deliveries/regional_full_visual_review_v1.json')['status']=='delivery_uncertain'
assert read(ROOT/'config/video_telegram_bridge.json')['private_chat_only']
token,cid=tg.creds();expected=os.environ.get('TELEGRAM_USER_ID','').strip()or(cid if cid.isdigit()else'')
assert token and cid.isdigit()and cid==expected
chat=tg._post('getChat',token,data={'chat_id':cid});assert chat.get('ok')and chat['result']['type']=='private'and str(chat['result']['id'])==cid
if P.exists():
    prior=read(P)
    if prior.get('ok'):
        assert prior['master_sha256']==split['master_sha256'];print(json.dumps({'ok':True,'already_delivered':True}));raise SystemExit(0)
    raise RuntimeError('Inspect partial delivery before repeating this fallback')
items=[(archive,'지역별 회복 · 전체 화면 검토본 v1 자료\n단일 영상 전송이 시간 초과되어 작은720p 파일4개로 나누어 전달합니다. 로컬1080p 원본을 보존했습니다.\n14분15.7초·12장면39문단. 음성 생성은 보류했고 기존BGM·임시 자막 타이밍을 사용했습니다.\n표본169프레임·원해상도20장 검수, 필수0건·권장1건. 연속 재생·실제 청취·모바일 재생은 미검수입니다. 검토 안내·장면 시간표·대본·출처·임시자막·검수 기록을 동봉합니다.')]
for i,item in enumerate(split['parts']):
    assert item['full_decode']=='pass'and sha(ROOT/item['path'])==item['sha256']
    caption=(f'지역별 회복 · 검토 영상 {i+1}/4\n전체 위치 {clock(item["global_video_start"])}–{clock(item["global_video_end"])} ·720p30 검토 사본\n'
        '음성 생성 보류·기존BGM·임시 자막 시점입니다.\n'
        'Thinking Music by Kevin MacLeod | incompetech.com | CC BY4.0\nhttps://creativecommons.org/licenses/by/4.0/')
    items.append((item,caption))
record={'at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'ok':False,'status':'request_started',
    'private_recipient_verified':True,'master_sha256':split['master_sha256'],'voice_generated':False,'timing_locked':False,
    'previous_uncertain_attempt_preserved':True,'items':[]};write(P,record)
for meta,caption in items:
    p=ROOT/meta['path'];assert sha(p)==meta['sha256']
    record['current_file']=p.name;write(P,record)
    with p.open('rb')as stream:
        response=tg._post('sendDocument',token,data={'chat_id':cid,'caption':caption},files={'document':(p.name,stream,'application/octet-stream')},timeout=180)
    item={'filename':p.name,'bytes':p.stat().st_size,'sha256':meta['sha256'],'ok':bool(response.get('ok')),'message_id':(response.get('result')or{}).get('message_id')}
    if not item['ok']:item['error']=tg.mask(response.get('error','Unknown'),token)
    record['items'].append(item);write(P,record)
    print(json.dumps(item,ensure_ascii=False),flush=True)
    if not item['ok']:
        record['status']='delivery_uncertain';write(P,record);raise SystemExit(1)
record.update(ok=True,status='delivered_four_part_visual_review_voice_deferred');record.pop('current_file',None);write(P,record)
state=read(EP/'state.json');state.update(production_review_telegram_receipt=P.relative_to(ROOT).as_posix(),
    production_review_telegram_format='four720p30parts; native1080p local master preserved');write(EP/'state.json',state)
print(json.dumps({'ok':True,'files':len(items),'status':record['status']}))
