"""Read-only inspection of the exact old upload requested for replacement."""
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'analysis'))
import upload_gyosan_private_v1 as uploader

CHANNEL = 'UCr_mTC0x_Uobv6MrIsOkrXw'
TARGET = 'exEGpjcqdF0'

youtube = uploader.service()
channels = youtube.channels().list(part='snippet', mine=True).execute(num_retries=0)['items']
assert len(channels) == 1 and channels[0]['id'] == CHANNEL
items = youtube.videos().list(part='snippet,status,processingDetails', id=TARGET).execute(num_retries=0)['items']
assert len(items) == 1 and items[0]['id'] == TARGET
video = items[0]
assert video['snippet']['channelId'] == CHANNEL
assert video['status']['privacyStatus'] == 'private'
result = {
    'checked_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
    'mode': 'read_only',
    'video_id': TARGET,
    'channel_id': CHANNEL,
    'title': video['snippet']['title'],
    'privacy': video['status']['privacyStatus'],
    'publish_at': video['status'].get('publishAt'),
    'processing': video.get('processingDetails', {}).get('processingStatus'),
    'deletion_executed': False,
    'replacement_condition': 'new Jun private upload processed and Korean captions serving before deleting this target',
    'other_video_ids_touched': []
}
(OUT / 'old_private_target_readonly.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
print(json.dumps(result, ensure_ascii=False))
