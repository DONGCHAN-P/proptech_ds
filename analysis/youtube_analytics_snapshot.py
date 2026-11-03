"""Read-only Analytics reports. Access is tested by the API, not inferred from saved scopes."""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/youtube_deps'))
from google.auth.transport.requests import AuthorizedSession
from google.oauth2.credentials import Credentials

def main():
    config = json.loads((ROOT / 'config/youtube-upload.json').read_text(encoding='utf-8-sig'))
    credentials = Credentials.from_authorized_user_file(str(ROOT / 'config/youtube-token.json'))
    session = AuthorizedSession(credentials)
    channel_response = session.get('https://www.googleapis.com/youtube/v3/channels', params={'part': 'snippet', 'mine': 'true'}, timeout=30)
    channel_response.raise_for_status()
    channels = channel_response.json().get('items', [])
    assert len(channels) == 1 and channels[0]['id'] == config['channel_id'], 'Channel mismatch'
    current = datetime.now(timezone(timedelta(hours=9)))
    start = (current.date() - timedelta(days=27)).isoformat()
    end = current.date().isoformat()
    metrics = 'views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,subscribersGained,subscribersLost,likes,comments,shares'

    def query(name, **options):
        params = {'ids': 'channel==MINE', 'startDate': start, 'endDate': end, 'metrics': metrics, **options}
        response = session.get('https://youtubeanalytics.googleapis.com/v2/reports', params=params, timeout=60)
        payload = response.json()
        if not response.ok:
            error = payload.get('error', {})
            return {'name': name, 'http_status': response.status_code, 'error_status': error.get('status'), 'message': error.get('message'), 'request': params}
        columns = [c['name'] for c in payload.get('columnHeaders', [])]
        return {'name': name, 'http_status': response.status_code, 'request': params,
                'column_headers': payload.get('columnHeaders', []),
                'rows': [dict(zip(columns, row)) for row in payload.get('rows', [])]}

    reports = {
        'totals': query('totals'),
        'daily': query('daily', dimensions='day', sort='day', maxResults=200),
        'videos': query('videos', dimensions='video', sort='-estimatedMinutesWatched', maxResults=200),
    }
    days = [row['day'] for row in reports['daily'].get('rows', [])]
    result = {'fetched_at_kst': current.isoformat(), 'channel_id': channels[0]['id'],
              'channel_title': channels[0]['snippet']['title'],
              'requested_start_date': start, 'requested_end_date': end,
              'last_returned_day': max(days) if days else None,
              'api': 'YouTube Analytics API v2', 'reports': reports,
              'notes': ['API reports are subject to processing delays; requested end date is not proof of complete data through that day.',
                        'Date ranges use YouTube report day boundaries, not a conversion of Korean calendar days.',
                        'No upload, metadata, thumbnail or channel settings changed.',
                        'Successful API access overrides the earlier saved-scope-only assessment.']}
    out = ROOT / 'output/youtube_statistics' / current.strftime('%Y%m%d_%H%M%S_analytics')
    out.mkdir(parents=True, exist_ok=True)
    path = out / 'analytics_snapshot.json'
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'snapshot_file': str(path), **result}, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
