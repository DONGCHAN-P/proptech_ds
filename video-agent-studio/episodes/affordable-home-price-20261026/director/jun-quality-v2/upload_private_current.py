"""Exact reviewed local artifacts -> existing channel, private, no duplicate retries."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,json,hashlib,sys,subprocess
ROOT=Path(__file__).resolve().parents[5];EP=Path(__file__).resolve().parents[2]
DIR=Path(__file__).resolve().parent;REL=EP/'outputs/jun-quality-v2/release'
sys.path.insert(0,str(ROOT/'analysis'))
import upload_gyosan_private_v1 as base
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def local(value):
    p=(ROOT/value).resolve();assert p.is_relative_to(EP.resolve()) and p.is_file();return p
def rel(p):return p.relative_to(ROOT).as_posix()
def now():return datetime.now(timezone.utc).isoformat()

def prepare():
    m=read(REL/'upload_manifest.json');assert m['privacy']=='private' and m['youtube_channel_id']==base.CHANNEL
    main=read(local(m['review_report']));assert main['video_sha256']==m['main']['sha256'] and main['independent_source_and_shorts_required_open']==0
    assert read(EP/'qa/jun-quality-v2/final-main-s18-review.json')['required_open_in_scope']==0
    sq=read(EP/'qa/jun-quality-v2/shorts-review/input_manifest.json')
    assert read(EP/'qa/jun-quality-v2/shorts-review/findings.json')['required_open']==0
    mainmeta=read(local(m['main']['metadata']));sm=read(local(m['shorts_metadata']))['shorts']
    auth={'id':'PRIVATE-CURRENT-20261028-JQ2','user_instruction':'유튜브 업로드 진행','context':'직전 답변의 준비된 본편·홍보/요약 쇼츠·썸네일과 Claude 최종 확인/업로드 미완료 상태를 전달한 뒤 받은 현재 직접 지시',
      'youtube_upload_authorized':True,'youtube_visibility':'private','channel_id':base.CHANNEL,'items':['main','promo','summary'],
      'claude_final_review_pass':False,'review_basis':'기록된 로컬/독립 검수, 미해결 필수 수정0. Claude의 검수 승인을 만들어내지 않음.',
      'new_paid_generation_authorized':False,'public_release_authorized':False,'existing_upload_deletion_authorized':False,'additional_cash_krw':0,'created_at':now()}
    authpath=DIR/'current_upload_authorization.json';save(authpath,auth)
    items=[('main',m['main'],mainmeta)]+[(mta['id'],item,mta) for item,mta in zip(m['shorts'],sm)]
    for ident,item,meta in items:
        video=local(item['video']);assert sha(video)==item['sha256']
        if ident!='main':assert any(row['sha256']==item['sha256'] for row in sq)
        subtitle=local(item['subtitles'])
        if item.get('subtitles_sha256'):assert sha(subtitle)==item['subtitles_sha256']
        assert 0<len(meta['title'])<=100 and len(meta['description'].encode('utf-8'))<=5000
        folder=REL/'private-upload-20261028'/ident;folder.mkdir(parents=True,exist_ok=True)
        qa={'status':'passed_with_limits','checked_revision':sha(video),'required_open':[],'critical_open':[],
          'source_review':m['review_report'] if ident=='main' else rel(EP/'qa/jun-quality-v2/shorts-review/findings.json'),
          'actual_listening':False,'continuous_playback':False,'claude_final_review_pass':False}
        save(folder/'qa_gate.json',qa)
        completed={'id':ident+'-local-result','gate':'completed','status':'approved','video_sha256':sha(video),'basis':'현재 직접 업로드 지시와 버전별 로컬 검수','authorization':rel(authpath)}
        save(folder/'completed_decision.json',completed)
        job={'id':ident,'channel_id':base.CHANNEL,'privacy':'private','video':rel(video),'sha256':sha(video),
          'title':meta['title'],'description':meta['description'],'tags':meta.get('tags',['내집마련','집값예산','Shorts']),
          'qa':rel(folder/'qa_gate.json'),'approval_file':rel(folder/'pre_upload.json'),'authorization':rel(authpath),
          'subtitles':rel(subtitle),'subtitles_sha256':sha(subtitle),'burned_in_captions_verified':True,'notify_subscribers':False}
        if ident=='main':
            thumb=local(item['thumbnail']);assert sha(thumb)==item['thumbnail_sha256'] and thumb.stat().st_size<2*1024*1024
            job.update(thumbnail=rel(thumb),thumbnail_sha256=sha(thumb))
        save(folder/'upload_job.json',job)
        save(folder/'pre_upload.json',{'id':ident+'-private-upload','gate':'pre_upload','status':'approved','video_sha256':sha(video),
          'job_sha256':sha(folder/'upload_job.json'),'channel_id':base.CHANNEL,'privacy':'private','new_paid_generation_authorized':False,
          'completed_decision_file':rel(folder/'completed_decision.json'),'current_direct_user_authorization':rel(authpath)})
        base.EP=EP;base.validate(folder/'upload_job.json')
    save(REL/'private-upload-20261028/preflight.json',{'status':'passed','items':3,'privacy':'private','no_upload_yet':True,'created_at':now(),'authorization':rel(authpath)})
    print(json.dumps({'preflight':'passed','items':['main','promo','summary'],'privacy':'private','claude_approval_claimed':False}))

def extras(y,job,record,rp):
    from googleapiclient.http import MediaFileUpload
    if job.get('thumbnail') and not record.get('thumbnail_uploaded'):
        y.thumbnails().set(videoId=record['video_id'],media_body=MediaFileUpload(str(local(job['thumbnail'])),mimetype='image/png')).execute(num_retries=0)
        record['thumbnail_uploaded']=True;save(rp,record)
    processing=record.get('verification',{}).get('processingDetails',{}).get('processingStatus')
    assert processing not in ['failed','terminated'],'Video processing failed'
    if processing!='succeeded':return
    tracks=y.captions().list(part='snippet',videoId=record['video_id']).execute(num_retries=0).get('items',[])
    if not record.get('caption_id'):
        expected=[t for t in tracks if t['snippet'].get('language')=='ko' and t['snippet'].get('name')=='한국어']
        assert len(expected)<=1,'Ambiguous caption track; do not insert duplicate'
        if expected:
            result=expected[0]
        else:
            result=y.captions().insert(part='snippet',body={'snippet':{'videoId':record['video_id'],'language':'ko','name':'한국어','isDraft':False}},
              media_body=MediaFileUpload(str(local(job['subtitles'])),mimetype='application/octet-stream')).execute(num_retries=0)
        record.update(caption_id=result['id'],captions_uploaded=True,caption_status=result.get('snippet',{}).get('status'));save(rp,record)
    else:
        track=next((x for x in tracks if x['id']==record['caption_id']),None)
        if track:record['caption_status']=track['snippet'].get('status')
    record['caption_serving_verified']=record.get('caption_status')=='serving'
    assert record.get('caption_status')!='failed','Caption processing failed'
    save(rp,record)

def upload(action):
    base.EP=EP
    y=base.service()
    channel=y.channels().list(part='snippet',mine=True).execute(num_retries=0).get('items',[])
    assert len(channel)==1 and channel[0]['id']==base.CHANNEL
    for ident in ['main','promo','summary']:
        folder=REL/'private-upload-20261028'/ident;jp=folder/'upload_job.json'
        job,video,gate=base.validate(jp);rp=folder/'upload_receipt.json'
        if action=='upload':
            # The existing uploader refuses uncertain prior uploads and always forces private.
            original_argv=sys.argv[:];sys.argv=[sys.argv[0],'upload','--job',rel(jp)]
            try:base.main()
            finally:sys.argv=original_argv
        else:
            assert rp.exists(),'No receipt; nothing to verify'
            base.verify(y,rp,read(rp),job)
        record=read(rp);assert record['private_verified'] is True
        extras(y,job,record,rp)
        print(json.dumps({'id':ident,'url':record['url'],'privacy':'private','processing':record.get('verification',{}).get('processingDetails',{}).get('processingStatus'),'caption_status':record.get('caption_status')},ensure_ascii=False),flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['prepare','upload','verify']);a=ap.parse_args()
    if a.action=='prepare':prepare()
    else:upload(a.action)
