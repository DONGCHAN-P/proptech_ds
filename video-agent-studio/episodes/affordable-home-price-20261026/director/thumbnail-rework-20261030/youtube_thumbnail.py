"""Read current thumbnail, then replace only that thumbnail on the exact public video."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
from urllib.request import Request,urlopen
import argparse,hashlib,json,sys
HERE=Path(__file__).resolve().parent;EP=HERE.parents[1];ROOT=EP.parents[2];OUT=EP/'outputs/thumbnail-rework-20261030'
sys.path.insert(0,str(ROOT/'tools/youtube_deps'))
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as AuthRequest
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
VIDEO='0495J7FMmCk';CHANNEL='UCr_mTC0x_Uobv6MrIsOkrXw'
def save(name,d):(HERE/name).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def service():
    c=Credentials.from_authorized_user_file(str(ROOT/'config/youtube-token.json'))
    if c.expired:c.refresh(AuthRequest())
    return build('youtube','v3',credentials=c,cache_discovery=False)
def read(y):
    d=y.videos().list(part='snippet,status,statistics,contentDetails',id=VIDEO).execute(num_retries=0)
    assert len(d.get('items',[]))==1
    v=d['items'][0];assert v['id']==VIDEO and v['snippet']['channelId']==CHANNEL
    assert v['snippet']['title'].startswith('현금 1억부터 5억까지')
    return v
def download(url,path):
    with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0','Cache-Control':'no-cache'}),timeout=30) as r:path.write_bytes(r.read(5*1024*1024))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['read','apply','verify']);args=ap.parse_args()
    y=service();v=read(y);now=datetime.now(timezone.utc).isoformat()
    if args.mode=='read':
        assert not (HERE/'before_api.json').exists(),'baseline_exists_do_not_overwrite'
        save('before_api.json',{'captured_at_utc':now,'video':v,'CTR':'user_reported; not independently measured'})
        t=v['snippet']['thumbnails'];url=(t.get('maxres') or t.get('standard') or t['high'])['url']
        download(url,OUT/'previous_thumbnail_live.jpg')
        save('before_thumbnail.json',{'url':url,'local_sha256':sha(OUT/'previous_thumbnail_live.jpg')})
        print(json.dumps({'phase':'baseline_saved','video_id':VIDEO,'title':v['snippet']['title'],'privacy':v['status']['privacyStatus'],'views':v.get('statistics',{}).get('viewCount')} ,ensure_ascii=False));return
    file=OUT/'TH001_affordable_photo_v1.png';image_sha=sha(file)
    if args.mode=='apply':
        assert (HERE/'before_api.json').exists()
        qa=json.loads((EP/'visual/thumbnail-rework-20261030/review/review.json').read_text(encoding='utf8'))
        checked=qa['checked_sha256']
        if isinstance(checked,dict):checked=checked.get(file.as_posix())
        assert qa['critical_open']==qa['required_open']==0 and checked==image_sha
        assert not (HERE/'replace_receipt.json').exists(),'already_set_use_verify_mode'
        assert file.stat().st_size<2*1024*1024
        auth={'authorization':'direct_current_user_request','request':'기존 방식으로 이 영상 썸네일 변경','video_id':VIDEO,'new_thumbnail_sha256':image_sha,'only_thumbnails_set':True,'prior_asset_preserved':True}
        save('authorization.json',auth)
        response=y.thumbnails().set(videoId=VIDEO,media_body=MediaFileUpload(str(file),mimetype='image/png',resumable=False)).execute(num_retries=0)
        save('replace_receipt.json',{'phase':'thumbnail_set_accepted','changed_at_utc':now,'changed_at_kst':datetime.now(timezone(timedelta(hours=9))).isoformat(),'video_id':VIDEO,'file_sha256':image_sha,'response':response})
        print(json.dumps({'phase':'thumbnail_set_accepted','video_id':VIDEO,'sha256':image_sha}));return
    receipt=json.loads((HERE/'replace_receipt.json').read_text(encoding='utf8'))
    assert receipt['file_sha256']==image_sha
    old=json.loads((HERE/'before_api.json').read_text(encoding='utf8'))['video']
    for field in ['title','description','channelId']:assert old['snippet'][field]==v['snippet'][field]
    assert old['status']['privacyStatus']==v['status']['privacyStatus']
    t=v['snippet']['thumbnails'];url=(t.get('maxres') or t.get('standard') or t['high'])['url']
    download(url+'?thumb_rev='+image_sha[:12],OUT/'thumbnail_served_after.jpg')
    save('after_api.json',{'captured_at_utc':now,'video':v,'title_description_privacy_unchanged':True})
    print(json.dumps({'phase':'metadata_and_served_image_fetched','video_id':VIDEO,'privacy':v['status']['privacyStatus'],'url':'https://youtu.be/'+VIDEO,'title_description_unchanged':True},ensure_ascii=False))
if __name__=='__main__':main()
