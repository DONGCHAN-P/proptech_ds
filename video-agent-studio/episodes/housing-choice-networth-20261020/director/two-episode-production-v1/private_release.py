"""Reuse the existing private uploader with exact-version dual-review gates."""
import argparse
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[5]
EP=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'analysis'))
import upload_gyosan_private_v1 as uploader


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def local(value):
    p=(ROOT/value).resolve()
    assert p.is_relative_to(ROOT) and p.is_file()
    return p


def verify_captions(youtube, receipt_path, record):
    if not record.get('captions_uploaded'):
        return
    items=youtube.captions().list(part='snippet',videoId=record['video_id']).execute(num_retries=0).get('items',[])
    matches=[item for item in items if item['id']==record['caption_id']]
    if not matches:
        print(json.dumps({'captions':'awaiting_caption_track_listing'}))
        return
    assert len(matches)==1 and matches[0]['snippet']['language']=='ko'
    snippet=matches[0]['snippet']
    record.update(caption_status=snippet.get('status'),caption_verification=snippet,
                  caption_serving_verified=snippet.get('status')=='serving')
    uploader.save(receipt_path,record)
    print(json.dumps({'caption_track_verified':True,'caption_status':record['caption_status']}))
    assert snippet.get('status')!='failed','YouTube caption processing failed; keep release incomplete.'


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('action',choices=['probe','validate','upload','verify'])
    ap.add_argument('--job')
    args=ap.parse_args()
    if args.action=='probe':
        youtube=uploader.service()
        items=youtube.channels().list(part='snippet',mine=True).execute(num_retries=0)['items']
        assert len(items)==1 and items[0]['id']==uploader.CHANNEL
        result={'authenticated_channel_verified':True,'channel_title':items[0]['snippet']['title'],
                'private_upload_scope':'existing OAuth','uploads_performed':0}
        target=Path(__file__).parent/'youtube_channel_probe.json'
        target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(result,ensure_ascii=False))
        return
    assert args.job, 'Exact approved job required.'
    job_path=local(args.job)
    job=read(job_path)
    episode=(ROOT/job['episode_root']).resolve()
    assert episode.is_relative_to(ROOT/'video-agent-studio/episodes')
    uploader.EP=episode
    uploader.OUT=job_path.parent
    original_validate=uploader.validate

    def validate(path):
        current,video,gate=original_validate(path)
        assert current['privacy']=='private' and current['burned_in_captions_verified'] is True
        authorization=read(local(current['authorization']))
        assert authorization['youtube_upload_authorized'] and authorization['youtube_visibility']=='private'
        assert authorization['paid_voice_generation_authorized'] is False
        assert gate['current_direct_user_authorization']==current['authorization']
        dual=read(local(current['dual_review']))
        assert dual['video_sha256']==current['sha256']
        assert dual['required_open']==[] and dual['critical_open']==[]
        for reviewer in ('codex','claude'):
            review=dual[reviewer]
            assert review['approved'] is True and review['video_sha256']==current['sha256']
            assert uploader.sha(local(review['receipt']))==review['receipt_sha256']
        caption=local(current['subtitles'])
        assert uploader.sha(caption)==current['subtitles_sha256']==dual['subtitles_sha256']
        return current,video,gate

    uploader.validate=validate
    validate(job_path)
    # Original code forces private, no schedule, no subscriber notification and no duplicate upload.
    sys.argv=[sys.argv[0],args.action,'--job',args.job]
    uploader.main()
    if args.action=='verify':
        receipt_path=job_path.parent/'upload_receipt.json'
        verify_captions(uploader.service(),receipt_path,read(receipt_path))
        return
    if args.action!='upload':
        return
    receipt_path=job_path.parent/'upload_receipt.json'
    record=read(receipt_path)
    assert record.get('video_id') and record['private_verified'] is True
    processing=record.get('verification',{}).get('processingDetails',{}).get('processingStatus')
    if processing!='succeeded':
        record['captions_phase']='waiting_for_video_processing'
        uploader.save(receipt_path,record)
        print(json.dumps({'private_upload_verified':True,'processing':processing,
                          'captions':'deferred_until_processing_succeeds','duplicate_upload':False}))
        return
    if not record.get('captions_uploaded'):
        from googleapiclient.http import MediaFileUpload
        youtube=uploader.service()
        result=youtube.captions().insert(part='snippet',body={'snippet':{
            'videoId':record['video_id'],'language':'ko','name':'한국어','isDraft':False}},
            media_body=MediaFileUpload(str(local(job['subtitles'])),mimetype='application/octet-stream')
        ).execute(num_retries=0)
        record.update(captions_uploaded=True,caption_id=result['id'],caption_status=result.get('snippet',{}).get('status'))
        uploader.save(receipt_path,record)
        uploader.verify(youtube,receipt_path,record,job)
    verify_captions(uploader.service(),receipt_path,read(receipt_path))


if __name__=='__main__':
    main()
