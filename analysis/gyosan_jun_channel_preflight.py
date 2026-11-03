from pathlib import Path
import sys,json,datetime
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'analysis'))
from upload_changneung_scheduled_v8 import service,CHANNEL
y=service();items=y.channels().list(part='snippet',mine=True).execute(num_retries=0)['items'];assert len(items)==1 and items[0]['id']==CHANNEL
r={'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'requests':'GET channel only; OAuth refresh if required','channel_id':CHANNEL,'channel_title':items[0]['snippet']['title'],'public_upload_intended':True,'upload_performed':False}
p=ROOT/'video-agent-studio/episodes/hanam-gyosan-20261019/outputs/release-prep-v5-jun/channel_preflight.json';p.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(r,ensure_ascii=False))
