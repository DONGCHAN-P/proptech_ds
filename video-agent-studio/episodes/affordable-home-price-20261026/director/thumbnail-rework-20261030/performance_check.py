"""Read-only evidence for whether a fresh upload is warranted; no video mutation."""
from pathlib import Path
from datetime import datetime,timezone
import json,sys
HERE=Path(__file__).resolve().parent;EP=HERE.parents[1];ROOT=EP.parents[2]
sys.path.insert(0,str(ROOT/'tools/youtube_deps'))
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
c=Credentials.from_authorized_user_file(str(ROOT/'config/youtube-token.json'))
if c.expired:c.refresh(Request())
y=build('youtube','v3',credentials=c,cache_discovery=False)
v=y.videos().list(part='snippet,statistics,status,contentDetails',id='0495J7FMmCk').execute(num_retries=0)['items'][0]
assert v['snippet']['channelId']=='UCr_mTC0x_Uobv6MrIsOkrXw'
report={'checked_at_utc':datetime.now(timezone.utc).isoformat(),'video_id':v['id'],'published_at':v['snippet']['publishedAt'],'statistics':v['statistics'],'privacy':v['status']['privacyStatus'],'duration':v['contentDetails']['duration'],'reports':{}}
try:
    a=build('youtubeAnalytics','v2',credentials=c,cache_discovery=False)
    for key,dimensions in [('daily','day'),('traffic','insightTrafficSourceType')]:
        try:
            d=a.reports().query(ids='channel==MINE',startDate='2026-10-28',endDate='2026-10-30',filters='video==0495J7FMmCk',metrics='views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage',dimensions=dimensions).execute(num_retries=0)
            report['reports'][key]=d
        except Exception as e:report['reports'][key]={'error_type':type(e).__name__,'http_status':getattr(getattr(e,'resp',None),'status',None)}
except Exception as e:report['analytics_error_type']=type(e).__name__
report['thumbnail_ctr']='not_collected; views alone do not establish impression volume or CTR'
(HERE/'performance_check_20261030.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=False))
