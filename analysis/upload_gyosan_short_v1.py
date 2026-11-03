"""Upload only the exact reviewed Gyosan Short with five scoped gate records."""
from pathlib import Path
import sys, json, hashlib, argparse
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'analysis'))
from upload_changneung_scheduled_v8 import service
OUT = ROOT/'video-agent-studio/episodes/hanam-gyosan-20261019/outputs/shorts-release-v1'

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))
def save(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['upload','verify'])
    args = parser.parse_args()
    job_path = OUT/'upload_job.json'
    job = read(job_path)
    assert job['channel_id'] == 'UCr_mTC0x_Uobv6MrIsOkrXw'
    assert job['privacy'] == 'public'
    video = ROOT/job['video']
    assert sha(video) == job['sha256']
    qa = read(ROOT/job['qa'])
    assert qa['sha256'] == job['sha256'] and qa['required_unresolved'] == 0
    for name in ('topic','script','budget','completed','pre_upload'):
        gate = read(ROOT/job['gates'][name])
        assert gate['gate'] == name and gate['video_sha256'] == job['sha256']
        assert gate['status'] in ('approved','not_applicable_no_new_paid_generation')
        for path, digest in gate['artifacts'].items():
            assert sha(ROOT/path) == digest, path
        if name == 'pre_upload':
            assert gate['job_sha256'] == sha(job_path)
    assert len(job['title']) <= 100 and len(job['description'].encode('utf-8')) < 5000
    y = service()
    channels = y.channels().list(part='id', mine=True).execute(num_retries=0)['items']
    assert len(channels) == 1 and channels[0]['id'] == job['channel_id']
    receipt_path = OUT/'upload_receipt.json'
    if args.action == 'upload' and not receipt_path.exists():
        from googleapiclient.http import MediaFileUpload
        receipt = {'phase':'upload_started','sha256':job['sha256'], 'job_sha256':sha(job_path), 'started_at':datetime.now(timezone.utc).isoformat()}
        save(receipt_path, receipt)
        body = {
            'snippet': {'title':job['title'], 'description':job['description'], 'tags':job['tags'], 'categoryId':'27', 'defaultLanguage':'ko', 'defaultAudioLanguage':'ko'},
            'status': {'privacyStatus':'public','selfDeclaredMadeForKids':False,'containsSyntheticMedia':job['contains_synthetic_media']}
        }
        request = y.videos().insert(part='snippet,status', body=body, notifySubscribers=True, media_body=MediaFileUpload(str(video), mimetype='video/mp4', resumable=True, chunksize=8*1024*1024))
        response = None
        while response is None:
            progress, response = request.next_chunk(num_retries=0)
        receipt.update(phase='uploaded', video_id=response['id'])
        save(receipt_path, receipt)
    receipt = read(receipt_path)
    assert receipt.get('video_id') and receipt['sha256'] == job['sha256'], 'Uncertain upload; do not duplicate'
    video_data = y.videos().list(part='snippet,status,contentDetails,processingDetails', id=receipt['video_id']).execute(num_retries=0)['items'][0]
    assert video_data['snippet']['channelId'] == job['channel_id']
    assert video_data['status']['privacyStatus'] == 'public'
    assert video_data['snippet']['title'] == job['title']
    assert video_data['snippet']['description'].strip().replace('\r\n','\n') == job['description'].strip().replace('\r\n','\n')
    receipt.update(verification=video_data, verified_at=datetime.now(timezone.utc).isoformat(), url='https://www.youtube.com/shorts/'+receipt['video_id'])
    save(receipt_path, receipt)
    print(json.dumps({'url':receipt['url'], 'privacy':video_data['status']['privacyStatus'], 'processing':video_data.get('processingDetails',{}).get('processingStatus')},ensure_ascii=False))

if __name__ == '__main__':
    main()
