"""Apply the owner's scoped request to the channel AI disclosure setting."""
from pathlib import Path
import sys, json
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'analysis'))
from upload_changneung_scheduled_v8 import service

OUT = ROOT/'output/youtube_ai_disclosure/718066305'
OUT.mkdir(parents=True, exist_ok=True)
record_path = OUT/'result.json'
y = service()
config = json.loads((ROOT/'config/youtube-upload.json').read_text(encoding='utf-8-sig'))
channels = y.channels().list(part='contentDetails', mine=True).execute(num_retries=0)['items']
assert len(channels) == 1 and channels[0]['id'] == config['channel_id']
playlist = channels[0]['contentDetails']['relatedPlaylists']['uploads']
ids, page = [], None
while True:
    result = y.playlistItems().list(part='contentDetails', playlistId=playlist, maxResults=50, pageToken=page).execute(num_retries=0)
    ids += [v['contentDetails']['videoId'] for v in result.get('items', [])]
    page = result.get('nextPageToken')
    if not page:
        break
record = {'event':718066305, 'channel_id':config['channel_id'], 'started_at':datetime.now(timezone.utc).isoformat(), 'videos':[]}
def save():
    record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
save()
keys = ('privacyStatus','license','embeddable','publicStatsViewable','selfDeclaredMadeForKids','publishAt')
for video_id in dict.fromkeys(ids):
    before = y.videos().list(part='snippet,status', id=video_id).execute(num_retries=0)['items'][0]
    assert before['snippet']['channelId'] == config['channel_id']
    row = {'id':video_id, 'title':before['snippet']['title'], 'before_status':before['status']}
    record['videos'].append(row)
    save()
    try:
        if before['status'].get('containsSyntheticMedia') is not False:
            status = {k:before['status'][k] for k in keys if k in before['status']}
            status['containsSyntheticMedia'] = False
            y.videos().update(part='status', body={'id':video_id, 'status':status}).execute(num_retries=0)
            row['action'] = 'updated'
        else:
            row['action'] = 'already_false'
        after = y.videos().list(part='snippet,status', id=video_id).execute(num_retries=0)['items'][0]
        row['after_status'] = after['status']
        row['verified_false'] = after['status'].get('containsSyntheticMedia') is False
        row['metadata_preserved'] = all(after['snippet'].get(k)==before['snippet'].get(k) for k in ('title','description','tags')) and all(after['status'].get(k)==before['status'].get(k) for k in keys)
    except Exception as exc:
        row['error_type'] = type(exc).__name__
        row['http_status'] = getattr(getattr(exc,'resp',None),'status',None)
    save()
record['finished_at'] = datetime.now(timezone.utc).isoformat()
record['verified_false_count'] = sum(v.get('verified_false',False) for v in record['videos'])
record['failed_count'] = sum(not v.get('verified_false',False) or not v.get('metadata_preserved',False) for v in record['videos'])
save()
print(json.dumps({'total':len(record['videos']), 'verified_false':record['verified_false_count'], 'failed':record['failed_count'], 'record':str(record_path)},ensure_ascii=False))
