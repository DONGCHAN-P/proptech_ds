"""Record verified private delivery and send exactly one requested Telegram message."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import argparse,hashlib,json,os,subprocess,sys

D=Path(__file__).resolve().parent;E=D.parents[1];R=E.parents[2];O=E/'outputs/top20-enhance-v2';U=D/'uploads/main'
sys.path.insert(0,str(R))
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,j):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rel(p):return Path(p).resolve().relative_to(R).as_posix()
def now():return datetime.now(timezone(timedelta(hours=9))).isoformat()

def verified():
 rec=read(U/'upload_receipt.json');job=read(U/'upload_job.json');v=rec['verification']
 assert rec['sha256']==job['sha256']==sha(R/job['video'])
 assert rec['private_verified'] and v['status']['privacyStatus']=='private' and not v['status'].get('publishAt')
 assert v['processingDetails']['processingStatus']=='succeeded'
 assert v['snippet']['channelId']==job['channel_id'] and rec.get('metadata_verified')
 assert rec.get('thumbnail_uploaded')
 tracks=[t for t in rec.get('caption_tracks',[])if t['snippet'].get('language')=='ko' and t['snippet'].get('name')=='한국어']
 assert len(tracks)==1 and tracks[0]['snippet']['status']=='serving'
 return rec,job

def record():
 rec,job=verified();url='https://youtu.be/'+rec['video_id'];c=read(O/'completion.json')
 if not(O/'local_completion_before_upload.json').exists():save(O/'local_completion_before_upload.json',c)
 c.update(status='enhanced_main_private_upload_verified',new_upload=True,video_id=rec['video_id'],youtube_url=url,privacy='private',processing='succeeded',
  captions='Korean manual caption serving',thumbnail_uploaded=True,upload_receipt=rel(U/'upload_receipt.json'),upload_receipt_sha256=sha(U/'upload_receipt.json'),verified_at=now())
 save(O/'completion.json',c)
 release=read(O/'upload_release_manifest.json');release.update(video_id=rec['video_id'],youtube_url=url,private_verified=True,processing='succeeded',caption_serving=True,upload_receipt=rel(U/'upload_receipt.json'));save(O/'upload_release_manifest.json',release)
 meta=read(O/'metadata.json');meta.update(privacy='private',upload_performed_this_revision=True,video_id=rec['video_id'],youtube_url=url);save(O/'metadata.json',meta)
 st=read(E/'state.json');st.update(phase='enhanced_main_private_upload_verified',publication_status='private',youtube_video_id=rec['video_id'],youtube_url=url,
  private_upload_authorization=rel(D/'upload_authorization.json'),release_manifest=rel(O/'upload_release_manifest.json'),updated_at=now());save(E/'state.json',st)
 report=f'''# TOP20 수정본 비공개 업로드 결과

- 영상: [{job['title']}]({url})
- 길이: 8분 48초 / 1920×1080 / 30fps
- 음성: 무료 Microsoft Edge InJoon, 본편 전체와 추가 분석 적용
- 상태: 비공개 · 유튜브 처리 완료 · 예약 공개 없음
- 한국어 자막: 직접 업로드한 자막 serving
- 썸네일·제목·설명·출처·12개 챕터: 적용 확인
- 업로드 원본 SHA256: `{job['sha256']}`

이전 비공개 본편 OR60umks6ac과 쇼츠 hM9KATRSQHA·wuDWyIMLe3Y는 보존했습니다.

검수 범위는 화면·수치·자막·전체 디코드이며, 실제 청취·연속 재생·Claude 검수는 미실시입니다.

자세한 영수증: `director/top20-enhance-v2/uploads/main/upload_receipt.json`
'''
 (O/'업로드결과.md').write_text(report,encoding='utf-8')
 p=O/'개선내용.md';text=p.read_text(encoding='utf-8');old='이번 수정본은 로컬 제작 결과입니다. 업로드 결과 문서는 기존 비공개 영상 세 편의 기록을 가리킵니다.'
 text=text.replace(old,f'새 수정본은 비공개 업로드를 완료했습니다: {url} . 현재 업로드 결과 문서는 이 8분48초 수정본을 가리킵니다.')
 p.write_text(text,encoding='utf-8')
 cfg=R/'config/video_shelf.json';s=read(cfg);entry=next(x for x in s['entries']if x['name']=='신혼부부_지역별아파트')
 entry['status']='본편 비주얼·정보 보강 8분48초 무료TTS 비공개 업로드 완료 · 한국어 자막·썸네일 확인. 기존 비공개본·쇼츠 보존.'
 entry['files']['이전_업로드결과.md']=rel(E/'outputs/top20-production-v1/업로드결과.md');entry['files']['업로드결과.md']=rel(O/'업로드결과.md');save(cfg,s)
 p=subprocess.run([str(R/'tools/python311/python.exe'),'-X','utf8',str(R/'tools/refresh_video_shelf.py')],cwd=R,capture_output=True,text=True,encoding='utf-8');assert p.returncode==0,p.stderr
 (D/'upload_shelf_refresh.log').write_text(p.stdout,encoding='utf-8')
 assert os.path.samefile(R/'영상/신혼부부_지역별아파트/영상.mp4',R/job['video'])
 d=read(E/'decisions.json')
 if not any(x.get('id')=='D022'for x in d['decisions']):
  d['decisions'].append({'id':'D022','revision':'top20-enhance-v2','choice':'latest user authorizes private upload of enhanced free-TTS main; one Telegram notification after verified completion',
   'authorization':rel(D/'upload_authorization.json'),'video_id':rec['video_id'],'privacy':'private','status':'uploaded_verified','source_requests':['완성된거 무료 TTS 작업해서 유튜브 비공개업로드해줘','올리면 텔레그램 메시지 하나 보내줘']})
 save(E/'decisions.json',d)
 print(json.dumps({'status':c['status'],'url':url,'privacy':'private','captions':'serving','thumbnail':True,'new_paid_generation':False},ensure_ascii=False))

def notify():
 rec,job=verified();marker=D/'telegram_notification.json'
 if marker.exists():
  prev=read(marker);assert prev.get('sent')is True,'An earlier send is uncertain; do not duplicate it'
  assert prev['video_id']==rec['video_id'];print(json.dumps({'telegram':'already_sent','video_id':rec['video_id']}));return
 from notify import telegram
 cfg=read(R/'config/video_telegram_bridge.json');tok,cid=telegram.creds();assert tok and cid,'Configured Telegram credentials missing'
 assert cfg.get('private_chat_only')is True
 # sender_user_id_env gates inbound approval commands. Outbound notifications
 # use the user's established TELEGRAM_CHAT_ID, as notify.telegram.send does.
 sender=os.getenv(cfg['sender_user_id_env'],'').strip()
 if sender:assert str(cid)==sender,'Configured personal sender/chat differs'
 chat=telegram._post('getChat',tok,data={'chat_id':cid})
 assert chat.get('ok')and chat['result'].get('type')=='private'and str(chat['result']['id'])==str(cid)
 message=f"신혼부부 TOP20 수정본 비공개 업로드 완료\n\n8분 48초 · 무료 InJoon 음성\nhttps://youtu.be/{rec['video_id']}\n\n한국어 자막·썸네일·12개 챕터를 반영했습니다.\n7:09부터 초혼 기준의 지역 순위 비교가 추가됐습니다."
 save(marker,{'status':'send_started','sent':False,'video_id':rec['video_id'],'message':message,'at':now(),
  'authorization':'올리면 텔레그램 메시지 하나 보내줘','recipient':'existing configured personal private chat','automatic_retry':False})
 result=telegram._post('sendMessage',tok,data={'chat_id':cid,'text':message,'disable_web_page_preview':'true'})
 if not result.get('ok'):
  save(marker,{'status':'send_failed_or_uncertain','sent':False,'video_id':rec['video_id'],'at':now(),'error':telegram.mask(telegram.explain(result),tok),'automatic_retry':False})
  raise RuntimeError('Telegram send failed or uncertain; safe receipt stored')
 save(marker,{'status':'sent','sent':True,'video_id':rec['video_id'],'message':message,'message_id':result['result']['message_id'],
  'recipient':'existing configured personal private chat','at':now(),'automatic_retry':False})
 c=read(O/'completion.json');c.update(telegram_notification_sent=True,telegram_receipt=rel(marker));save(O/'completion.json',c)
 print(json.dumps({'telegram':'sent_once','video_id':rec['video_id'],'message_id':result['result']['message_id']},ensure_ascii=False))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['record','notify']);a=p.parse_args()
 record()if a.action=='record'else notify()
