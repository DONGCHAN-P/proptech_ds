"""One authorized main-video replacement. Stage, verify, publish, then delete exact old ID."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
from urllib.request import Request as URLRequest,urlopen
import argparse,hashlib,json,re,subprocess,sys

HERE=Path(__file__).resolve().parent;EP=HERE.parents[1];ROOT=EP.parents[2]
sys.path.insert(0,str(ROOT/'tools/youtube_deps'))
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

OLD='0495J7FMmCk';CHANNEL='UCr_mTC0x_Uobv6MrIsOkrXw'
SHORTS=['nYl1XSdyFAQ','DnCBj7voUyY']
EXPECTED='e0a84d5a5893193c7b50431c0c5b60adb279a7817bd4e970b0e04bfe32dcb561'
REC=HERE/'upload_receipt.json'
def now():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf8'))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def log(**d):print(json.dumps(d,ensure_ascii=False),flush=True)
def service():
    c=Credentials.from_authorized_user_file(str(ROOT/'config/youtube-token.json'))
    if c.expired:c.refresh(Request())
    y=build('youtube','v3',credentials=c,cache_discovery=False)
    ids=y.channels().list(part='id',mine=True).execute(num_retries=0).get('items',[])
    assert CHANNEL in [a['id'] for a in ids],'wrong_channel'
    return y
def get(y,vid,full=False):
    part='snippet,status,contentDetails,processingDetails'
    if full:part+=',statistics,paidProductPlacementDetails'
    vs=y.videos().list(part=part,id=vid).execute(num_retries=0).get('items',[])
    if not vs:return None
    v=vs[0];assert v['snippet']['channelId']==CHANNEL
    return v
def snippet(v):
    s=v['snippet'];return {k:s[k] for k in ['title','description','tags','categoryId','defaultLanguage','defaultAudioLanguage'] if k in s}
def inputs():
    job=read(HERE/'upload_job.json');auth=read(HERE/'authorization.json')
    assert job['old_video_id']==auth['delete_only_video_id']==OLD
    assert job['video_sha256']==auth['video_sha256']==EXPECTED
    assert sha(ROOT/job['video'])==EXPECTED and sha(ROOT/job['thumbnail'])==job['thumbnail_sha256']
    assert sha(ROOT/job['subtitles'])==job['subtitles_sha256']
    assert sha(HERE/'upload_job.json')==auth['upload_job_sha256']
    return job

def prepare(y):
    assert not (HERE/'upload_job.json').exists(),'existing_preparation_reuse_it'
    cfg=read(ROOT/'config/current_video.json');assert cfg['episode']==EP.name
    assert cfg['youtube_url']=='https://youtu.be/'+OLD
    video=ROOT/cfg['video'];subtitles=ROOT/cfg['subtitles'];thumb=ROOT/cfg['thumbnail']
    assert sha(video)==EXPECTED==cfg['sha256'] and sha(thumb)==cfg['thumbnail_sha256']
    prior_qa=read(EP/'outputs/jun-quality-v2/main/completion.json')
    assert prior_qa['video_sha256']==EXPECTED and prior_qa['whole_AV_decode']=='pass'
    probe=ROOT/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe'
    media=json.loads(subprocess.run([str(probe),'-v','error','-show_streams','-show_format','-of','json',str(video)],capture_output=True,check=True).stdout)
    duration=float(media['format']['duration']);assert abs(duration-714.8)<.1
    cues=re.findall(r'(\d\d):(\d\d):(\d\d),(\d{3})',subtitles.read_text(encoding='utf-8-sig'))
    assert cues and max(int(h)*3600+int(m)*60+int(s)+int(ms)/1000 for h,m,s,ms in cues)<=duration+.1
    old=get(y,OLD,full=True);assert old and old['snippet']['title'].startswith('현금 1억부터 5억까지')
    assert old['status']['privacyStatus']=='public'
    save(HERE/'old_video.before.json',old);save(HERE/'local_media_probe.json',media)
    tracks=y.captions().list(part='snippet',videoId=OLD).execute(num_retries=0).get('items',[])
    save(HERE/'old_captions.before.json',tracks)
    # Preserve comments as a local record; never repost another person's message.
    try:
        comments=y.commentThreads().list(part='snippet,replies',videoId=OLD,maxResults=100,textFormat='plainText').execute(num_retries=0)
        save(HERE/'old_comments.before.json',comments)
    except Exception as e:save(HERE/'old_comments.before.json',{'error_type':type(e).__name__})
    # Snapshot only this episode's promotional Shorts, for exact main-link replacement.
    short_records=[]
    for vid in SHORTS:
        v=get(y,vid);assert v
        short_records.append(v)
    save(HERE/'shorts.before.json',short_records)
    playlists=[]
    try:
        page=y.playlists().list(part='snippet',mine=True,maxResults=50).execute(num_retries=0)
        for pl in page.get('items',[]):
            items=y.playlistItems().list(part='snippet,status',playlistId=pl['id'],videoId=OLD,maxResults=50).execute(num_retries=0).get('items',[])
            for item in items:playlists.append({'playlist_id':pl['id'],'item':item})
        save(HERE/'playlists.before.json',{'memberships':playlists,'additional_playlists_page_present':bool(page.get('nextPageToken'))})
    except Exception as e:save(HERE/'playlists.before.json',{'memberships':playlists,'error_type':type(e).__name__})
    t=old['snippet'].get('thumbnails',{});u=(t.get('maxres') or t.get('standard') or t.get('high') or {}).get('url')
    if u:
        try:
            with urlopen(URLRequest(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=30) as response:(HERE/'old_thumbnail.before.jpg').write_bytes(response.read(5*1024*1024))
        except Exception as e:save(HERE/'thumbnail_backup_error.json',{'error_type':type(e).__name__})
    status={'privacyStatus':'private','selfDeclaredMadeForKids':old['status'].get('selfDeclaredMadeForKids',old['status'].get('madeForKids',False)),
            'containsSyntheticMedia':old['status'].get('containsSyntheticMedia',True)}
    for key in ['license','embeddable','publicStatsViewable']:
        if key in old['status']:status[key]=old['status'][key]
    body={'snippet':snippet(old),'status':status}
    if 'paidProductPlacementDetails' in old:body['paidProductPlacementDetails']=old['paidProductPlacementDetails']
    body['snippet'].setdefault('defaultLanguage','ko');body['snippet'].setdefault('defaultAudioLanguage','ko')
    assert len(body['snippet']['title'])<=100 and len(body['snippet']['description'].encode('utf8'))<=5000
    job={'old_video_id':OLD,'channel_id':CHANNEL,'video':video.relative_to(ROOT).as_posix(),'video_sha256':EXPECTED,
        'subtitles':subtitles.relative_to(ROOT).as_posix(),'subtitles_sha256':sha(subtitles),
        'thumbnail':thumb.relative_to(ROOT).as_posix(),'thumbnail_sha256':sha(thumb),
        'body':body,'notify_subscribers':True,'target_visibility':'public','duration':duration,
        'new_paid_generation':False,'caption_language':'ko','shorts_to_update':SHORTS,
        'execution_order':['private_upload','thumbnail_and_captions','HD_processing_and_caption_serving','publish_and_verify','repair_episode_links','delete_exact_old_video','verify_deletion']}
    save(HERE/'upload_job.json',job)
    save(HERE/'authorization.json',{'authorization':'direct_user_request','request':'효과 전혀 없어서 삭제하고 새로 업로드해줘',
        'context':'현금1억부터5억까지 얼마짜리집을살수있을까 본편. 최신 photo-v1-20261030 썸네일 사용. 기존 공개 상태를 계승해 새 ID로 즉시 공개.',
        'delete_only_video_id':OLD,'channel_id':CHANNEL,'video_sha256':EXPECTED,'upload_job_sha256':sha(HERE/'upload_job.json'),
        'upload_authorized':True,'public_authorized':True,'deletion_authorized':True,
        'delete_after_new_public_HD_captions_verified':True,'preserve_local_sources':True,'new_paid_calls':0,'created_at':now()})
    save(HERE/'current_video.before.json',cfg)
    log(phase='prepared',video_bytes=video.stat().st_size,duration=duration,old_id=OLD,caption_tracks=len(tracks),playlist_memberships=len(playlists),source_hash_verified=True)

def upload(y):
    job=inputs()
    if REC.exists():
        record=read(REC)
        assert record.get('video_id'),'ambiguous_prior_upload_do_not_duplicate'
        log(phase='reuse_existing_new_id',video_id=record['video_id']);return
    assert get(y,OLD),'old_video_missing_before_new_upload'
    record={'phase':'upload_started','started_at':now(),'sha256':EXPECTED,'job_sha256':sha(HERE/'upload_job.json'),'automatic_new_upload_retry':False}
    save(REC,record)
    part='snippet,status'+(',paidProductPlacementDetails' if 'paidProductPlacementDetails' in job['body'] else '')
    req=y.videos().insert(part=part,body=job['body'],notifySubscribers=True,
        media_body=MediaFileUpload(str(ROOT/job['video']),mimetype='video/mp4',chunksize=8*1024*1024,resumable=True))
    response=None
    try:
        while response is None:
            progress,response=req.next_chunk(num_retries=0)
            if progress:log(phase='uploading',percent=round(progress.progress()*100))
        assert response['id']!=OLD
        record.update(phase='uploaded',video_id=response['id'],uploaded_at=now());save(REC,record)
        log(phase='uploaded',new_id=response['id'])
    except Exception as e:
        record['error_type']=type(e).__name__;save(REC,record);raise

def decorate(y):
    job=inputs();r=read(REC);vid=r['video_id'];assert vid!=OLD
    v=get(y,vid);assert v and v['status']['privacyStatus']=='private'
    if not r.get('thumbnail_uploaded'):
        result=y.thumbnails().set(videoId=vid,media_body=MediaFileUpload(str(ROOT/job['thumbnail']),mimetype='image/png')).execute(num_retries=0)
        r['thumbnail_uploaded']=True;r['thumbnail_response']=result;save(REC,r)
    if not r.get('caption_id'):
        assert not r.get('caption_insert_started'),'ambiguous_caption_upload_inspect_before_retry'
        r['caption_insert_started']=True;save(REC,r)
        cap=y.captions().insert(part='snippet',body={'snippet':{'videoId':vid,'language':'ko','name':'한국어','isDraft':False}},
            media_body=MediaFileUpload(str(ROOT/job['subtitles']),mimetype='application/octet-stream',resumable=False)).execute(num_retries=0)
        r['caption_id']=cap['id'];save(REC,r)
    r['phase']='decorated';save(REC,r);log(phase='decorated',video_id=vid,thumbnail=True,captions=True)

def check(y):
    job=inputs();r=read(REC);v=get(y,r['video_id']);assert v
    for field in ['title','description']:assert v['snippet'][field]==job['body']['snippet'][field]
    assert v['status'].get('uploadStatus') not in ['failed','rejected','deleted']
    proc=v.get('processingDetails',{}).get('processingStatus')
    assert proc not in ['failed','terminated'],'new_video_processing_failed'
    caps=y.captions().list(part='snippet',videoId=r['video_id']).execute(num_retries=0).get('items',[])
    c=next((c for c in caps if c['id']==r.get('caption_id')),None)
    ready=proc=='succeeded' and v['contentDetails'].get('definition')=='hd' and c and c['snippet'].get('status')=='serving' and r.get('thumbnail_uploaded')
    r.update(processing=proc,definition=v['contentDetails'].get('definition'),caption_status=c['snippet'].get('status') if c else None,
             ready=bool(ready),last_verified_at=now(),verification=v)
    save(REC,r);save(HERE/'new_captions.json',caps)
    log(phase='checked',video_id=r['video_id'],ready=bool(ready),processing=proc,definition=r['definition'],caption_status=r['caption_status'],privacy=v['status']['privacyStatus'])
    return r

def publish(y):
    job=inputs();r=check(y);assert r['ready'],'new_video_not_ready_preserve_old'
    v=get(y,r['video_id']);assert v
    if v['status']['privacyStatus']!='public':
        assert v['status']['privacyStatus']=='private'
        status=dict(job['body']['status']);status['privacyStatus']='public'
        y.videos().update(part='status',body={'id':r['video_id'],'status':status}).execute(num_retries=0)
    v=get(y,r['video_id']);assert v['status']['privacyStatus']=='public'
    r.update(phase='public_verified',public_verified_at=now(),verification=v,url='https://youtu.be/'+r['video_id']);save(REC,r)
    log(phase='public_verified',new_id=r['video_id'],url=r['url'])

def repair_links(y):
    r=read(REC);assert r['phase']=='public_verified'
    changes=[]
    for old in read(HERE/'shorts.before.json'):
        current=get(y,old['id']);assert current
        desc=current['snippet']['description']
        if OLD in desc:
            newdesc=desc.replace(OLD,r['video_id']);s=snippet(current);s['description']=newdesc
            y.videos().update(part='snippet',body={'id':old['id'],'snippet':s}).execute(num_retries=0)
            verify=get(y,old['id']);assert verify['snippet']['description']==newdesc
            assert verify['snippet']['title']==current['snippet']['title'] and verify['status']['privacyStatus']==current['status']['privacyStatus']
            changes.append({'id':old['id'],'changed':True,'new_main_id':r['video_id']})
        else:changes.append({'id':old['id'],'changed':False,'old_url_absent':True})
    playlist_receipt=HERE/'playlist_updates.json';done=read(playlist_receipt) if playlist_receipt.exists() else []
    for membership in read(HERE/'playlists.before.json').get('memberships',[]):
        pid=membership['playlist_id']
        if any(d['playlist_id']==pid for d in done):continue
        existing=y.playlistItems().list(part='snippet',playlistId=pid,videoId=r['video_id'],maxResults=50).execute(num_retries=0).get('items',[])
        if not existing:
            item=y.playlistItems().insert(part='snippet',body={'snippet':{'playlistId':pid,'position':membership['item']['snippet']['position'],
                'resourceId':{'kind':'youtube#video','videoId':r['video_id']}}}).execute(num_retries=0)
            done.append({'playlist_id':pid,'item_id':item['id']});save(playlist_receipt,done)
    save(HERE/'link_updates.json',{'updated_at':now(),'shorts':changes,'native_related_video_ui':'not exposed by Data API; no native related-video verification claimed'})
    if not playlist_receipt.exists():save(playlist_receipt,done)
    log(phase='episode_links_updated',shorts=changes,playlist_count=len(done))

def delete_old(y):
    job=inputs();auth=read(HERE/'authorization.json');r=check(y)
    assert r['ready'] and r['verification']['status']['privacyStatus']=='public'
    assert r['video_id']!=OLD and auth['deletion_authorized'] and auth['delete_only_video_id']==OLD
    assert (HERE/'link_updates.json').exists()
    path=HERE/'deletion_receipt.json'
    old=get(y,OLD,full=True)
    if old is None:
        assert path.exists(),'old_missing_without_local_delete_record'
    else:
        assert old['snippet']['title']==job['body']['snippet']['title']
        save(HERE/'old_video.immediately_before_delete.json',old)
        save(path,{'phase':'delete_started','delete_only_video_id':OLD,'replacement_video_id':r['video_id'],'at':now(),'authorization':'authorization.json'})
        y.videos().delete(id=OLD).execute(num_retries=0)
        save(path,{'phase':'delete_response_received','delete_only_video_id':OLD,'replacement_video_id':r['video_id'],'at':now()})
    assert get(y,OLD) is None,'old_video_still_returned'
    v=get(y,r['video_id']);assert v and v['status']['privacyStatus']=='public'
    save(path,{'phase':'deleted_verified','deleted_video_id':OLD,'replacement_video_id':r['video_id'],'verified_at':now(),'local_sources_preserved':True})
    r.update(phase='replacement_complete',url='https://youtu.be/'+r['video_id'],old_deleted=True,final_verification=v,completed_at=now());save(REC,r)
    log(phase='replacement_complete',url=r['url'],deleted_old_id=OLD,local_video_preserved=True)

def final_check(y):
    from PIL import Image
    import numpy as np
    job=inputs();r=read(REC);assert r['phase']=='replacement_complete'
    old_fresh=y.videos().list(part='id',id=OLD,fields='items(id)').execute(num_retries=0)
    assert not old_fresh.get('items')
    r=check(y);assert r['ready'] and r['verification']['status']['privacyStatus']=='public'
    v=r['verification'];shorts=[]
    for vid in SHORTS:
        s=get(y,vid);assert s and r['video_id'] in s['snippet']['description'] and OLD not in s['snippet']['description']
        shorts.append({'id':vid,'title':s['snippet']['title'],'privacy':s['status']['privacyStatus'],'new_main_link_verified':True})
    thumbs=v['snippet']['thumbnails'];u=(thumbs.get('maxres') or thumbs.get('standard') or thumbs['high'])['url']
    with urlopen(URLRequest(u+'?rev='+job['thumbnail_sha256'][:12],headers={'User-Agent':'Mozilla/5.0','Cache-Control':'no-cache'}),timeout=30) as resp:
        (HERE/'new_thumbnail.served.jpg').write_bytes(resp.read(5*1024*1024))
    actual=np.asarray(Image.open(HERE/'new_thumbnail.served.jpg').convert('RGB').resize((128,72)),dtype=float)
    expected=np.asarray(Image.open(ROOT/job['thumbnail']).convert('RGB').resize((128,72)),dtype=float)
    err=float(np.abs(actual-expected).mean());assert err<8,'thumbnail_cdn_image_does_not_match'
    proof={'verified_at':now(),'old_id_absent':True,'new_id':r['video_id'],'new_public':True,'HD':r['definition']=='hd',
        'processing':r['processing'],'caption_status':r['caption_status'],'thumbnail_mean_absolute_error':err,'thumbnail_served_matches':True,
        'title_matches':v['snippet']['title']==job['body']['snippet']['title'],'description_matches':v['snippet']['description']==job['body']['snippet']['description'],
        'local_source_hashes_verified':True,'shorts':shorts}
    save(HERE/'final_readback.json',proof);log(phase='final_readback_passed',url=r['url'],old_deleted=True,HD=True,captions=r['caption_status'],thumbnail_image_match=True)

def confirm_delete(y):
    job=inputs();r=check(y);assert r['ready'] and r['verification']['status']['privacyStatus']=='public'
    receipt=read(HERE/'deletion_receipt.json')
    assert receipt['phase'] in ['delete_response_received','deleted_verified'] and receipt.get('delete_only_video_id',receipt.get('deleted_video_id'))==OLD
    # Read with a different projection after the successful DELETE response; never repeat the deletion.
    result=y.videos().list(part='snippet,status',id=OLD,fields='items(id,snippet(channelId),status(uploadStatus,privacyStatus))').execute(num_retries=0)
    save(HERE/'old_id_fresh_readback.json',{'at':now(),'response':result})
    if result.get('items'):
        log(phase='delete_response_received_readback_pending',old_id=OLD,delete_repeated=False);return
    v=get(y,r['video_id']);assert v and v['status']['privacyStatus']=='public'
    save(HERE/'deletion_receipt.json',{'phase':'deleted_verified','deleted_video_id':OLD,'replacement_video_id':r['video_id'],'verified_at':now(),'local_sources_preserved':True,'delete_repeated':False})
    r.update(phase='replacement_complete',url='https://youtu.be/'+r['video_id'],old_deleted=True,final_verification=v,completed_at=now());save(REC,r)
    save(HERE/'deletion_readback_resolution.json',{'resolved_at':now(),'initial_readback':'old metadata was returned immediately after successful DELETE','fresh_readback_old_items':0,'delete_repeated':False})
    log(phase='replacement_complete',url=r['url'],deleted_old_id=OLD,local_video_preserved=True)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['prepare','upload','decorate','check','publish','links','delete-old','confirm-delete','final-check']);args=ap.parse_args()
    try:globals()[{'links':'repair_links','delete-old':'delete_old','confirm-delete':'confirm_delete','final-check':'final_check'}.get(args.mode,args.mode)](service())
    except Exception as e:
        save(HERE/'last_error.json',{'mode':args.mode,'type':type(e).__name__,'http_status':getattr(getattr(e,'resp',None),'status',None),'at':now()})
        log(phase='error',mode=args.mode,error_type=type(e).__name__,http_status=getattr(getattr(e,'resp',None),'status',None));raise SystemExit(1)
if __name__=='__main__':main()
