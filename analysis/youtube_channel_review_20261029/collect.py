"""Owner-authorized, read-only YouTube channel research. No secrets in output."""
import csv
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tools/youtube_deps'))
from google.auth.transport.requests import AuthorizedSession
from google.oauth2.credentials import Credentials


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    source = ROOT / 'output/youtube_statistics/20261029_000423/snapshot.json'
    initial = ROOT / 'output/youtube_statistics/20261029_000424_analytics/analytics_snapshot.json'
    snapshot = json.loads(source.read_text(encoding='utf-8'))
    base = json.loads(initial.read_text(encoding='utf-8'))
    save(OUT / 'raw/data_api_snapshot.json', snapshot)
    save(OUT / 'raw/initial_analytics.json', base)
    credentials = Credentials.from_authorized_user_file(str(ROOT / 'config/youtube-token.json'))
    session = AuthorizedSession(credentials)
    identity = session.get('https://www.googleapis.com/youtube/v3/channels', params={'part': 'id', 'mine': 'true'}, timeout=30)
    assert identity.ok and [v['id'] for v in identity.json()['items']] == [snapshot['channel']['id']]
    start, end = '2026-10-02', base['last_returned_day']
    reports = {}

    def query(name, metrics='views,engagedViews,estimatedMinutesWatched', **options):
        params = {'ids': 'channel==MINE', 'startDate': start, 'endDate': end, 'metrics': metrics, **options}
        response = session.get('https://youtubeanalytics.googleapis.com/v2/reports', params=params, timeout=45)
        payload = response.json()
        record = {'request': params, 'http_status': response.status_code}
        if response.ok:
            headers = payload.get('columnHeaders', [])
            record.update(column_headers=headers, rows=[dict(zip([c['name'] for c in headers], r)) for r in payload.get('rows', [])])
        else:
            err = payload.get('error', {})
            record.update(error_status=err.get('status'), message=err.get('message'))
        reports[name] = record
        save(OUT / 'raw/extended_analytics.json', {'start': start, 'end': end, 'reports': reports})
        print(json.dumps({'report': name, 'status': response.status_code, 'rows': len(record.get('rows', []))}, ensure_ascii=False), flush=True)
        return record

    query('daily_views_latest', metrics='views', dimensions='day', sort='day', endDate='2026-10-29', maxResults=200)
    query('daily_watch_latest', metrics='estimatedMinutesWatched,averageViewDuration,averageViewPercentage', dimensions='day', sort='day', endDate='2026-10-29', maxResults=200)
    query('formats', metrics='views,engagedViews,estimatedMinutesWatched,averageViewDuration,averageViewPercentage', dimensions='creatorContentType')
    query('video_engaged', metrics='views,engagedViews,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,subscribersGained,subscribersLost,shares', dimensions='video', sort='-estimatedMinutesWatched', maxResults=200)
    query('traffic', dimensions='insightTrafficSourceType', sort='-views', maxResults=100)
    query('traffic_formats', dimensions='insightTrafficSourceType,creatorContentType', sort='-views', maxResults=100)
    query('devices', dimensions='deviceType,creatorContentType', sort='-views', maxResults=100)
    query('search_terms', dimensions='insightTrafficSourceDetail', filters='insightTrafficSourceType==YT_SEARCH', sort='-views', maxResults=25)
    query('suggested_videos', dimensions='insightTrafficSourceDetail', filters='insightTrafficSourceType==RELATED_VIDEO', sort='-views', maxResults=25)
    public = [v for v in snapshot['videos'] if v['privacy'] == 'public']
    for video in public:
        vid = video['id']
        # Publish-day plus next two report calendar days; not a literal 72-hour cohort.
        from zoneinfo import ZoneInfo
        published_day = datetime.fromisoformat(video['published_at'].replace('Z', '+00:00')).astimezone(ZoneInfo('America/Los_Angeles')).date()
        if (published_day + timedelta(days=2)).isoformat() <= end:
            query('early3_' + vid, metrics='views,engagedViews,estimatedMinutesWatched,averageViewDuration,averageViewPercentage', dimensions='day', filters='video==' + vid, sort='day', startDate=published_day.isoformat(), endDate=(published_day+timedelta(days=2)).isoformat(), maxResults=3)
    retention_ids = ['eLF3-1ZaraQ', 'T_GBxTRgRSc', 'XWAWnSrz7FE', 'a9pYQ9iSCBo', 'dIcVPPvpJVM', '8shvS0--yBQ', 'nfeT2nfDeS4', '7rRKo08NvWc', 'ETXkCHF4Si0']
    for vid in retention_ids:
        query('retention_' + vid, metrics='audienceWatchRatio,relativeRetentionPerformance', dimensions='elapsedVideoTimeRatio', filters='video==' + vid, sort='elapsedVideoTimeRatio', maxResults=200)
    fetched = datetime.now(timezone(timedelta(hours=9))).isoformat()
    save(OUT / 'collection_manifest.json', {'fetched_at_kst': fetched, 'channel_id': snapshot['channel']['id'], 'range_start': start, 'coherent_end_date': end, 'snapshot_fetched_at': snapshot['fetched_at_kst'], 'read_only': True, 'api_reports': len(reports), 'failures': {k:v for k,v in reports.items() if v['http_status'] != 200}, 'external_transmission': 'Google owner-channel read-only API requests only; credentials excluded from artifacts'})
    for name, report in reports.items():
        rows = report.get('rows', [])
        if rows:
            dest = OUT / 'tables' / (name + '.csv')
            dest.parent.mkdir(exist_ok=True)
            with dest.open('w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)


if __name__ == '__main__':
    main()
