"""Upload only the exact enhanced main authorized in the latest user request.
Reuse the tested private uploader, Korean-caption handling and existing OAuth.
No new TTS, paid service, publishing, scheduling, deletion or duplicate upload.
"""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import argparse,hashlib,importlib.util,json,sys

D=Path(__file__).resolve().parent;E=D.parents[1];R=E.parents[2]
O=E/'outputs/top20-enhance-v2';U=D/'uploads/main'
sys.path.insert(0,str(R/'analysis'))
import upload_gyosan_private_v1 as base
base.EP=E
spec=importlib.util.spec_from_file_location('top20_prior_private_helpers',E/'director/top20-production-v1/upload_private.py')
helpers=importlib.util.module_from_spec(spec);spec.loader.exec_module(helpers)
base.EP=E

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,j):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rel(p):return Path(p).resolve().relative_to(R).as_posix()
def local(s):
 p=(R/s).resolve();assert p.is_relative_to(E.resolve()) and p.is_file();return p
def now():return datetime.now(timezone(timedelta(hours=9))).isoformat()

def prepare():
 assert not(U/'upload_receipt.json').exists(),'Existing upload receipt: verify/resume its exact job, never prepare over it'
 c=read(O/'completion.json');video=local(c['video']);q=read(local(c['qa']));m=read(O/'metadata.json')
 assert sha(video)==c['video_sha256']==q['video_sha256']=='12b2221c246c1a10fb6e2c92750fbb4ca4d40b2195b721bef0afa2ee56bf28f5'
 assert q['critical_open']==q['required_open']==0 and q['full_decode'] is True
 assert 480<c['duration_s']<550
 assert sha(local(c['qa']))==c['qa_sha256']
 subs=local(c['subtitles']);sv=read(O/'subtitle_verification.json');assert sha(subs)==sv['sha256'] and sv['sentences']==113
 assert 0<len(m['title'])<=100 and len(m['description'].encode('utf-8'))<=5000
 audio=read(D/'locked_timing.json');assert audio['voice']=='ko-KR-InJoonNeural' and audio['paid_api_calls']==0
 assert sha(Path(audio['audio_file']))==audio['audio_sha256']
 thumb=E/'outputs/top20-production-v1/thumbnail/TH001_신혼부부_수도권TOP20_v2_1280x720.png'
 assert sha(thumb)=='d669526af8537c36aeade8a35f79731fd5158b78dad723bad6d86c416c4a85bd'
 auth={'source':'latest explicit user instruction','request':'완성된거 무료 TTS 작업해서 유튜브 비공개업로드해줘','revision':'top20-enhance-v2',
  'private_upload_authorized':True,'public_publication_authorized':False,'delete_existing_videos':False,
  'new_paid_generation_authorized':False,'cash_cap_krw':0,'video_sha256':sha(video),'channel_id':base.CHANNEL,
  'voice':'already completed free Microsoft Edge InJoon narration, all113sentences','at':now(),
  'qa_scope':'scoped visual/technical review; actual listening/continuous playback and Claude review not performed'}
 save(D/'upload_authorization.json',auth)
 save(U/'qa_gate.json',{'status':'passed_with_limits','checked_revision':sha(video),'required_open':[],'critical_open':[],
  'source_review':c['qa'],'source_review_sha256':sha(local(c['qa'])),'actual_listening':False,'continuous_playback':False})
 save(U/'completed_decision.json',{'id':'enhanced-main-completed','gate':'completed','status':'approved','video_sha256':sha(video),
  'basis':'Current explicit user instruction to upload the completed enhanced review copy','authorization':rel(D/'upload_authorization.json')})
 job={'id':'enhanced-main','channel_id':base.CHANNEL,'privacy':'private','video':c['video'],'sha256':sha(video),
  'title':m['title'],'description':m['description'],'tags':m.get('tags',[]),'qa':rel(U/'qa_gate.json'),
  'approval_file':rel(U/'pre_upload.json'),'authorization':rel(D/'upload_authorization.json'),
  'subtitles':rel(subs),'subtitles_sha256':sha(subs),'thumbnail':rel(thumb),'thumbnail_sha256':sha(thumb),'notify_subscribers':False}
 save(U/'upload_job.json',job)
 save(U/'pre_upload.json',{'id':'enhanced-main-private-upload','gate':'pre_upload','status':'approved','video_sha256':sha(video),
  'job_sha256':sha(U/'upload_job.json'),'channel_id':base.CHANNEL,'privacy':'private','new_paid_generation_authorized':False,
  'completed_decision_file':rel(U/'completed_decision.json'),'basis':'Latest explicit user request; no additional approval needed','at':now()})
 base.validate(U/'upload_job.json')
 save(O/'upload_release_manifest.json',{'revision':'top20-enhance-v2','privacy':'private','channel_id':base.CHANNEL,
  'video':job['video'],'video_sha256':job['sha256'],'subtitles':job['subtitles'],'subtitles_sha256':job['subtitles_sha256'],
  'thumbnail':job['thumbnail'],'thumbnail_sha256':job['thumbnail_sha256'],'metadata':rel(O/'metadata.json'),
  'qa':c['qa'],'qa_sha256':sha(local(c['qa'])),'job':rel(U/'upload_job.json'),'job_sha256':sha(U/'upload_job.json'),
  'authorization':rel(D/'upload_authorization.json'),'actual_listening':False,'continuous_playback':False,'new_paid_generation':False})
 print(json.dumps({'local_preflight':'passed','duration_s':c['duration_s'],'voice':audio['voice'],'items':1,'privacy':'private','new_uploads':0},ensure_ascii=False))

def verify_metadata(y):
 rp=U/'upload_receipt.json';rec=read(rp);job=read(U/'upload_job.json');base.verify(y,rp,rec,job);rec=read(rp)
 item=rec['verification'];assert item['snippet']['title']==job['title']
 assert item['snippet']['description'].rstrip()==job['description'].rstrip()
 assert not item['status'].get('publishAt')
 rec.update(metadata_verified=True,exact_source_sha256=job['sha256'],metadata_verified_at=now())
 save(rp,rec)
 print(json.dumps({'video_id':rec['video_id'],'privacy':item['status']['privacyStatus'],
  'processing':item.get('processingDetails',{}).get('processingStatus'),'thumbnail_uploaded':rec.get('thumbnail_uploaded',False),
  'manual_korean_captions':[t['snippet'].get('status')for t in rec.get('caption_tracks',[])if t['snippet'].get('language')=='ko' and t['snippet'].get('name')=='한국어'],
  'metadata_verified':True},ensure_ascii=False))

def main():
 ap=argparse.ArgumentParser();ap.add_argument('action',choices=['prepare','connection','upload','verify']);a=ap.parse_args()
 if a.action=='prepare':prepare();return
 if a.action=='connection':
  y=base.service();items=y.channels().list(part='snippet',mine=True).execute(num_retries=0).get('items',[])
  assert any(i['id']==base.CHANNEL for i in items),'Connected channel differs from authorized target'
  print(json.dumps({'connection':'verified','channel_id':base.CHANNEL,'channel_title':next(i['snippet']['title']for i in items if i['id']==base.CHANNEL)},ensure_ascii=False));return
 base.validate(U/'upload_job.json')
 sys.argv=['existing_private_uploader',a.action,'--job',rel(U/'upload_job.json')]
 base.main()
 y=base.service();helpers.extras(y,U);verify_metadata(y)

if __name__=='__main__':main()
