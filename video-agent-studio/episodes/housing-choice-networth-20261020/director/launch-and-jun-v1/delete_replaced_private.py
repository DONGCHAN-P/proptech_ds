"""Delete only the specifically authorized old private upload after verified replacement."""
import argparse
import datetime as dt
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[5]
HERE=Path(__file__).resolve().parent
EP=HERE.parents[1]
sys.path.insert(0,str(ROOT/'analysis'))
import upload_gyosan_private_v1 as uploader

read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def local(value):
    p=(ROOT/value).resolve()
    assert p.is_relative_to(EP) and p.is_file()
    return p

ap=argparse.ArgumentParser()
ap.add_argument('--new-job',required=True)
ap.add_argument('--execute-authorized-delete',action='store_true')
args=ap.parse_args()
auth=read(HERE/'authorization.json')
assert auth['old_private_delete_authorized'] and auth['old_private_video_id']=='exEGpjcqdF0'
assert auth['youtube_upload_authorized'] and auth['youtube_visibility']=='private'
job_path=local(args.new_job);job=read(job_path)
assert job['authorization']==(HERE/'authorization.json').relative_to(ROOT).as_posix()
assert job['channel_id']==auth['channel_id'] and job['privacy']=='private'
assert uploader.sha(local(job['video']))==job['sha256']
record=read(job_path.parent/'upload_receipt.json')
new=record['video_id'];old=auth['old_private_video_id'];channel=auth['channel_id']
assert new!=old and new not in auth['protected_video_ids']
assert record['sha256']==job['sha256'] and record['private_verified']
assert record['captions_uploaded'] and record['caption_serving_verified']
dual=read(local(job['dual_review']))
assert dual['video_sha256']==job['sha256'] and not dual['required_open'] and not dual['critical_open']
for reviewer in ('codex','claude'):
    item=dual[reviewer]
    assert item['approved'] and item['video_sha256']==job['sha256']
    assert uploader.sha(local(item['receipt']))==item['receipt_sha256']
youtube=uploader.service()
channels=youtube.channels().list(part='snippet',mine=True).execute(num_retries=0)['items']
assert len(channels)==1 and channels[0]['id']==channel
items=youtube.videos().list(part='snippet,status,processingDetails',id=','.join([old,new])).execute(num_retries=0)['items']
byid={item['id']:item for item in items}
assert new in byid
replacement=byid[new]
assert replacement['snippet']['channelId']==channel and replacement['status']['privacyStatus']=='private'
assert replacement['snippet']['title']==job['title'] and not replacement['status'].get('publishAt')
assert replacement['processingDetails']['processingStatus']=='succeeded'
captions=youtube.captions().list(part='snippet',videoId=new).execute(num_retries=0)['items']
assert any(item['id']==record['caption_id'] and item['snippet']['language']=='ko' and item['snippet']['status']=='serving' for item in captions)
receipt=HERE/'old_private_deletion_receipt.json'
if old not in byid:
    assert receipt.exists(),'Old target absent before this tracked deletion; do not claim execution.'
    prior=read(receipt)
    assert prior['old_video_id']==old and prior['new_video_id']==new and prior['phase'] in ['deletion_started','delete_returned','deleted_verified']
    prior.update(phase='deleted_verified',old_video_absent_verified=True,verified_at_utc=dt.datetime.now(dt.timezone.utc).isoformat())
    save(receipt,prior)
    print(json.dumps({'old_video_id':old,'old_video_absent_verified':True,'new_url':record['url'],'duplicate_delete':False}))
    raise SystemExit(0)
target=byid[old]
assert target['snippet']['channelId']==channel and target['status']['privacyStatus']=='private'
assert not target['status'].get('publishAt')
original=read(HERE/'old_private_target_readonly.json')
assert target['snippet']['title']==original['title'] and original['video_id']==old
result={'old_video_id':old,'new_video_id':new,'new_url':record['url'],'channel_id':channel,
        'new_video_sha256':job['sha256'],'new_private_processed_caption_serving':True,
        'old_title':target['snippet']['title'],'old_privacy':'private',
        'authorization':job['authorization'],'phase':'ready_to_delete','local_files_deleted':0,
        'protected_video_ids':auth['protected_video_ids'],'at_utc':dt.datetime.now(dt.timezone.utc).isoformat()}
if not args.execute_authorized_delete:
    print(json.dumps(result,ensure_ascii=False));raise SystemExit(0)
assert not receipt.exists(),'Uncertain previous delete must be reconciled, not retried.'
result['phase']='deletion_started';save(receipt,result)
youtube.videos().delete(id=old).execute(num_retries=0)
result['phase']='delete_returned';save(receipt,result)
remaining=youtube.videos().list(part='id',id=old).execute(num_retries=0)['items']
assert remaining==[]
result.update(phase='deleted_verified',old_video_absent_verified=True,verified_at_utc=dt.datetime.now(dt.timezone.utc).isoformat())
save(receipt,result)
print(json.dumps({'old_video_id':old,'deleted_verified':True,'new_url':record['url'],'local_files_deleted':0},ensure_ascii=False))
