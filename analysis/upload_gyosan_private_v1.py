"""Upload an exact approved Gyosan review artifact as private only.

No paid generation, scheduled/public release, automatic retry or duplicate upload.
Job and gate files are prepared by the video director after the final QA pass.
"""
import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EP = ROOT / 'video-agent-studio/episodes/hanam-gyosan-20261019'
OUT = EP / 'outputs/release-prep-v1'
sys.path.insert(0, str(ROOT / 'analysis'))
from upload_changneung_scheduled_v8 import CHANNEL, service


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def local_file(relative):
    path = (ROOT / relative).resolve()
    assert path.is_relative_to(ROOT), 'File must remain inside workspace'
    assert path.is_file(), 'Required artifact missing'
    return path


def validate(job_path):
    job = read(job_path)
    assert job['channel_id'] == CHANNEL and job['privacy'] == 'private'
    assert not job.get('publish_at') and not job.get('publishAt'), 'Scheduling is not authorized'
    video = local_file(job['video'])
    assert video.is_relative_to(EP.resolve()) and sha(video) == job['sha256']
    qa_path = local_file(job['qa'])
    qa = read(qa_path)
    assert qa['checked_revision'] == job['sha256']
    assert qa.get('required_unresolved', qa.get('required_open')) == []
    assert not qa.get('critical_open', [])
    assert qa.get('status') in ['passed', 'passed_with_limits']
    assert 0 < len(job['title']) <= 100
    assert len(job['description'].encode('utf-8')) <= 5000
    gate = read(local_file(job['approval_file']))
    assert gate['gate'] == 'pre_upload' and gate['status'] == 'approved'
    assert gate['video_sha256'] == job['sha256'] and gate['job_sha256'] == sha(job_path)
    assert gate['channel_id'] == CHANNEL and gate['privacy'] == 'private'
    assert not gate.get('publish_at') and not gate.get('publishAt')
    completed = read(local_file(gate['completed_decision_file']))
    assert completed['gate'] == 'completed' and completed['status'] == 'approved'
    assert completed['video_sha256'] == job['sha256']
    assert gate.get('new_paid_generation_authorized') is False
    if job.get('thumbnail'):
        thumbnail = local_file(job['thumbnail'])
        assert sha(thumbnail) == job['thumbnail_sha256']
        assert thumbnail.stat().st_size < 2 * 1024 * 1024
    return job, video, gate


def verify(youtube, receipt_path, record, job):
    assert record.get('video_id'), 'Prior upload uncertain: do not retry or upload duplicate'
    assert record['sha256'] == job['sha256']
    items = youtube.videos().list(
        part='snippet,status,contentDetails,processingDetails', id=record['video_id']
    ).execute(num_retries=0)['items']
    assert len(items) == 1
    video = items[0]
    assert video['snippet']['channelId'] == CHANNEL
    assert video['status']['privacyStatus'] == 'private'
    assert not video['status'].get('publishAt'), 'Unexpected publication schedule'
    record.update(
        verification=video, private_verified=True,
        verified_at=datetime.now(timezone.utc).isoformat(),
        url='https://youtu.be/' + record['video_id'],
    )
    save(receipt_path, record)
    print(json.dumps({
        'url': record['url'], 'privacy': 'private',
        'processing': video.get('processingDetails', {}).get('processingStatus'),
    }, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['validate', 'upload', 'verify'])
    parser.add_argument('--job', default=str((OUT / 'upload_job.json').relative_to(ROOT)))
    args = parser.parse_args()
    job_path = local_file(args.job)
    job, video, gate = validate(job_path)
    if args.action == 'validate':
        print(json.dumps({'local_validation': 'passed', 'sha256': job['sha256'], 'privacy': 'private'}))
        return
    youtube = service()
    receipt_path = job_path.parent / 'upload_receipt.json'
    if receipt_path.exists():
        verify(youtube, receipt_path, read(receipt_path), job)
        return
    assert args.action == 'upload', 'Receipt missing: nothing to verify'
    from googleapiclient.http import MediaFileUpload
    record = {
        'phase': 'upload_started', 'sha256': job['sha256'],
        'job_sha256': sha(job_path), 'decision_id': gate['id'],
        'started_at': datetime.now(timezone.utc).isoformat(),
        'privacy': 'private', 'new_paid_generation': False,
    }
    save(receipt_path, record)
    body = {
        'snippet': {
            'title': job['title'], 'description': job['description'],
            'tags': job.get('tags', []), 'categoryId': '27',
            'defaultLanguage': 'ko', 'defaultAudioLanguage': 'ko',
        },
        'status': {
            'privacyStatus': 'private', 'selfDeclaredMadeForKids': False,
            'containsSyntheticMedia': True,
        },
    }
    request = youtube.videos().insert(
        part='snippet,status', body=body, notifySubscribers=False,
        media_body=MediaFileUpload(str(video), mimetype='video/mp4', chunksize=8*1024*1024, resumable=True),
    )
    response = None
    while response is None:
        progress, response = request.next_chunk(num_retries=0)
        if progress:
            print('Upload', round(progress.progress() * 100), '%', flush=True)
    record.update(phase='uploaded', video_id=response['id'])
    save(receipt_path, record)
    if job.get('thumbnail'):
        youtube.thumbnails().set(
            videoId=response['id'], media_body=MediaFileUpload(str(local_file(job['thumbnail'])), mimetype='image/png')
        ).execute(num_retries=0)
        record['thumbnail_uploaded'] = True
        save(receipt_path, record)
    verify(youtube, receipt_path, record, job)


if __name__ == '__main__':
    main()
