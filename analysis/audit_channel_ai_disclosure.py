"""Read-only inventory for individual AI disclosure assessments."""
from pathlib import Path
import sys,json
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'analysis'))
from upload_changneung_scheduled_v8 import service
out=ROOT/'output/youtube_ai_disclosure/per_video_review_20261020';out.mkdir(parents=True,exist_ok=True)
y=service()
channel=y.channels().list(part='contentDetails,snippet',mine=True).execute(num_retries=0)['items']
assert len(channel)==1 and channel[0]['id']=='UCr_mTC0x_Uobv6MrIsOkrXw'
ids=[];page=None
while True:
    result=y.playlistItems().list(part='contentDetails',playlistId=channel[0]['contentDetails']['relatedPlaylists']['uploads'],maxResults=50,pageToken=page).execute(num_retries=0)
    ids.extend(item['contentDetails']['videoId'] for item in result.get('items',[]))
    page=result.get('nextPageToken')
    if not page:break
videos=[]
for start in range(0,len(ids),50):
    videos.extend(y.videos().list(part='snippet,status,contentDetails',id=','.join(ids[start:start+50])).execute(num_retries=0)['items'])
data={'read_only':True,'fetched_at':datetime.now(timezone.utc).isoformat(),'channel_id':channel[0]['id'],'videos':videos}
(out/'inventory.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps([{'id':v['id'],'title':v['snippet']['title'],'privacy':v['status']['privacyStatus'],'ai':v['status'].get('containsSyntheticMedia'),'duration':v['contentDetails']['duration']} for v in videos],ensure_ascii=False))
