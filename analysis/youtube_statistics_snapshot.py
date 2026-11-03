"""Read-only channel/video statistics snapshot; never uploads or changes videos."""
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/youtube_deps'))
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def duration_seconds(value):
    match = re.fullmatch(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', value)
    return sum(int(x or 0) * factor for x, factor in zip(match.groups(), [3600, 60, 1])) if match else None

def number(data, name):
    return int(data[name]) if name in data else None

def main():
    token_path = ROOT / 'config/youtube-token.json'
    config = read(ROOT / 'config/youtube-upload.json')
    token_data = read(token_path)
    credentials = Credentials.from_authorized_user_file(str(token_path))
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        token_path.write_text(credentials.to_json(), encoding='utf-8')
    if not credentials.valid:
        raise RuntimeError('YouTube connection requires renewed sign-in; no browser opened.')
    youtube = build('youtube', 'v3', credentials=credentials, cache_discovery=False)
    response = youtube.channels().list(part='snippet,statistics,contentDetails', mine=True).execute()
    channels = response.get('items', [])
    assert len(channels) == 1 and channels[0]['id'] == config['channel_id'], 'Authenticated channel mismatch'
    channel = channels[0]
    playlist = channel['contentDetails']['relatedPlaylists']['uploads']
    ids, page = [], None
    while True:
        result = youtube.playlistItems().list(part='contentDetails', playlistId=playlist, maxResults=50, pageToken=page).execute()
        ids.extend(x['contentDetails']['videoId'] for x in result.get('items', []))
        page = result.get('nextPageToken')
        if not page:
            break
    videos = []
    for start in range(0, len(ids), 50):
        result = youtube.videos().list(part='snippet,statistics,status,contentDetails', id=','.join(ids[start:start + 50]), maxResults=50).execute()
        for item in result.get('items', []):
            stats = item.get('statistics', {})
            videos.append({
                'id': item['id'], 'title': item['snippet']['title'],
                'published_at': item['snippet'].get('publishedAt'),
                'privacy': item['status']['privacyStatus'],
                'duration_s': duration_seconds(item['contentDetails']['duration']),
                'views': number(stats, 'viewCount'), 'likes': number(stats, 'likeCount'),
                'comments': number(stats, 'commentCount'),
                'url': 'https://youtu.be/' + item['id'],
            })
    videos.sort(key=lambda v: v['views'] or 0, reverse=True)
    timestamp = datetime.now(timezone(timedelta(hours=9)))
    stats = channel['statistics']
    analytics_scope = 'https://www.googleapis.com/auth/yt-analytics.readonly'
    snapshot = {
        'fetched_at_kst': timestamp.isoformat(), 'source': 'YouTube Data API v3',
        'channel': {'id': channel['id'], 'title': channel['snippet']['title'],
                    'views': number(stats, 'viewCount'), 'subscribers': number(stats, 'subscriberCount'),
                    'subscriber_count_hidden': stats.get('hiddenSubscriberCount'),
                    'video_count_api': number(stats, 'videoCount')},
        'videos_returned': len(videos), 'videos': videos,
        'analytics': {'declared_analytics_scope_present': analytics_scope in token_data.get('scopes', []),
                      'api_access_tested': False,
                      'note': 'Saved scope metadata alone does not establish Analytics API access; use youtube_analytics_snapshot.py to test.',
                      'required_scope': analytics_scope,
                      'not_retrieved': ['watch_time', 'average_view_duration', 'retention', 'traffic_sources', 'impressions_or_ctr']},
        'notes': ['Snapshot cumulative counts, not date-range analytics.',
                  'Owner upload playlist includes private/unlisted videos; channel count and views need not equal listed totals.',
                  'Missing metric fields remain null, not inferred zero.',
                  'No video publishing, metadata or thumbnail changes.'],
    }
    out = ROOT / 'output/youtube_statistics' / timestamp.strftime('%Y%m%d_%H%M%S')
    out.mkdir(parents=True, exist_ok=True)
    path = out / 'snapshot.json'
    path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'snapshot_file': str(path), **snapshot}, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    try:
        main()
    except HttpError as error:
        print(json.dumps({'error': 'youtube_api_error', 'http_status': error.resp.status}, ensure_ascii=False))
        raise SystemExit(2)
