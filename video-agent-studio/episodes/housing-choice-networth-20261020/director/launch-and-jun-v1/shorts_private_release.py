"""Reuse the proven private-only uploader with exact two-Shorts authority and media gates."""
import argparse,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;EP=HERE.parents[1];ROOT=EP.parents[2]
sys.path.insert(0,str(ROOT/'analysis'));import upload_gyosan_private_v1 as uploader
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
ap=argparse.ArgumentParser();ap.add_argument('action',choices=['validate','upload','verify']);ap.add_argument('--job',required=True);args=ap.parse_args()
path=(ROOT/args.job).resolve();assert path.is_relative_to(EP/'outputs/shorts-release-v2')
job=read(path);assert job['short_id'] in ['funnel','analysis']
uploader.EP=EP;uploader.OUT=path.parent;original=uploader.validate
def validate(p):
    current,video,gate=original(p)
    auth=read(ROOT/current['authorization']);assert auth['count']==2 and auth['visibility']=='private' and auth['youtube_upload_authorized']
    assert auth['new_ElevenLabs_credits_cap']==0 and auth['additional_cash_usd_cap']==0
    assert current['burned_in_captions_verified'] and uploader.sha(ROOT/current['subtitles'])==current['subtitles_sha256']
    completion=read(EP/'outputs/jun-release-v1/completion.json');assert completion['status']=='Jun_private_uploaded_verified_old_private_replaced'
    dual=read(ROOT/current['dual_review']);assert dual['video_sha256']==current['sha256'] and dual['subtitles_sha256']==current['subtitles_sha256']
    assert not dual['required_open'] and not dual['critical_open']
    for who in ['codex','claude']:
        entry=dual[who];assert entry['approved'] and uploader.sha(ROOT/entry['receipt'])==entry['receipt_sha256']
    assert gate['current_direct_user_authorization']==current['authorization']
    return current,video,gate
uploader.validate=validate;validate(path)
sys.argv=[sys.argv[0],args.action,'--job',args.job];uploader.main()
if args.action=='validate':raise SystemExit(0)
receipt_path=path.parent/'upload_receipt.json';record=read(receipt_path)
assert record['private_verified']
if args.action=='upload' and record['verification']['processingDetails']['processingStatus']=='succeeded' and not record.get('captions_uploaded'):
    youtube=uploader.service()
    assert not record.get('caption_insert_started'),'Prior caption insertion uncertain; reconcile before retry.'
    record['caption_insert_started']=True;uploader.save(receipt_path,record)
    from googleapiclient.http import MediaFileUpload
    result=youtube.captions().insert(part='snippet',body={'snippet':{'videoId':record['video_id'],'language':'ko','name':'한국어','isDraft':False}},media_body=MediaFileUpload(str(ROOT/job['subtitles']),mimetype='application/octet-stream')).execute(num_retries=0)
    record.update(captions_uploaded=True,caption_id=result['id'],caption_status=result.get('snippet',{}).get('status'));uploader.save(receipt_path,record)
if record.get('captions_uploaded'):
    rows=uploader.service().captions().list(part='snippet',videoId=record['video_id']).execute(num_retries=0)['items']
    row=next(x for x in rows if x['id']==record['caption_id']);assert row['snippet']['language']=='ko'
    record.update(caption_status=row['snippet']['status'],caption_serving_verified=row['snippet']['status']=='serving');uploader.save(receipt_path,record)
    assert record['caption_status']!='failed'
print(json.dumps({'id':job['short_id'],'url':record['url'],'private_verified':True,'processing':record['verification']['processingDetails']['processingStatus'],'caption_status':record.get('caption_status'),'caption_serving_verified':record.get('caption_serving_verified',False)}))
