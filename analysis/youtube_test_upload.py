"""Upload only the approved five-second channel intro as a private test."""
import json
import sys
import time
import hashlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools/youtube_deps'))
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

root = Path(__file__).resolve().parents[1]
config = json.loads((root / 'config/youtube-upload.json').read_text(encoding='utf-8'))
credentials = Credentials.from_authorized_user_file(str(root / 'config/youtube-token.json'))
if credentials.expired:
    credentials.refresh(Request())
    (root / 'config/youtube-token.json').write_text(credentials.to_json(), encoding='utf-8')
youtube = build('youtube', 'v3', credentials=credentials, cache_discovery=False)
channel = youtube.channels().list(part='snippet', mine=True).execute()['items']
assert len(channel) == 1 and channel[0]['id'] == config['channel_id'], 'Wrong channel'
video = root / 'video/out/channel-intro-v2.mp4'
assert video.exists() and video.stat().st_size < 10_000_000
log = root / 'video/out/youtube-test-upload.json'
if log.exists():
    record = json.loads(log.read_text(encoding='utf-8'))
    assert record.get('video_id'), 'Prior attempt uncertain; inspect channel before another upload'
    print('Existing upload reused; no duplicate created')
else:
    record = {'phase': 'upload_started', 'channel_id': config['channel_id'],
              'file': str(video.relative_to(root)),
              'sha256': hashlib.sha256(video.read_bytes()).hexdigest()}
    log.write_text(json.dumps(record, indent=2), encoding='utf-8')
    body = {
        'snippet': {'title': '[업로드 테스트] 채널 공통 인트로 v2 · 5초',
                    'description': 'YouTube API 연결과 영상 처리 확인용 비공개 테스트입니다.\n'
                                   'AI로 생성한 가상의 도심 풍경이며 실제 특정 지역 촬영물이 아닙니다.\n'
                                   '사운드는 직접 합성한 짧은 사운드 로고입니다. 본편 영상이 아닙니다.',
                    'categoryId': '22', 'defaultLanguage': 'ko'},
        'status': {'privacyStatus': 'private', 'selfDeclaredMadeForKids': False,
                   'containsSyntheticMedia': True}}
    request = youtube.videos().insert(part='snippet,status', body=body,
        notifySubscribers=False,
        media_body=MediaFileUpload(str(video), mimetype='video/mp4', resumable=True))
    response = None
    while response is None:
        progress, response = request.next_chunk(num_retries=0)
    record.update(video_id=response['id'], phase='uploaded', metadata=response)
    log.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
thumbnail = root / 'video/out/channel-brand-v2-qa/test-thumbnail.jpg'
if not record.get('thumbnail_result') and thumbnail.exists():
    try:
        youtube.thumbnails().set(videoId=record['video_id'],
            media_body=MediaFileUpload(str(thumbnail), mimetype='image/jpeg')).execute()
        record['thumbnail_result'] = 'uploaded'
    except HttpError as e:
        record['thumbnail_result'] = {'http_status': e.resp.status, 'reason': e._get_reason()}
for attempt in range(12):
    items = youtube.videos().list(part='snippet,status,contentDetails,processingDetails',
                                  id=record['video_id']).execute().get('items', [])
    if items:
        record['verification'] = items[0]
        log.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
        processing = items[0].get('processingDetails', {}).get('processingStatus')
        print('Processing:', processing, flush=True)
        if processing in ['succeeded', 'failed', 'terminated']:
            break
    time.sleep(10)
print(json.dumps({'video_url': 'https://youtu.be/' + record['video_id'],
                  'studio_url': 'https://studio.youtube.com/video/' + record['video_id'] + '/edit',
                  'thumbnail': record.get('thumbnail_result'),
                  'status': record.get('verification', {}).get('status')}, ensure_ascii=False))
