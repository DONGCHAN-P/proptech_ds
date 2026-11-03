import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/youtube_deps'))
from google.auth.transport.requests import AuthorizedSession
from google.oauth2.credentials import Credentials

session = AuthorizedSession(Credentials.from_authorized_user_file(str(ROOT / 'config/youtube-token.json')))
config = json.loads((ROOT / 'config/youtube-upload.json').read_text(encoding='utf-8-sig'))
channel = session.get('https://www.googleapis.com/youtube/v3/channels', params={'mine': 'true', 'part': 'id'}, timeout=30)
channel.raise_for_status()
assert [x['id'] for x in channel.json()['items']] == [config['channel_id']]
current = datetime.now(timezone(timedelta(hours=9)))
reports = []
for metrics in ['views', 'views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage', 'subscribersGained,subscribersLost', 'likes,comments,shares']:
    params = {'ids': 'channel==MINE', 'startDate': (current.date()-timedelta(days=6)).isoformat(), 'endDate': current.date().isoformat(), 'metrics': metrics, 'dimensions': 'day', 'sort': 'day'}
    response = session.get('https://youtubeanalytics.googleapis.com/v2/reports', params=params, timeout=45)
    data = response.json()
    columns = [x['name'] for x in data.get('columnHeaders', [])]
    rows = [dict(zip(columns, row)) for row in data.get('rows', [])]
    reports.append({'metrics': metrics, 'http_status': response.status_code, 'last_returned_day': max((x['day'] for x in rows), default=None), 'rows': rows})
result = {'checked_at_kst': current.isoformat(), 'reports': reports}
out = ROOT / 'output/youtube_statistics' / current.strftime('%Y%m%d_%H%M%S_freshness')
out.mkdir(parents=True, exist_ok=True)
(out/'freshness_check.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps(result, ensure_ascii=False, indent=2))
