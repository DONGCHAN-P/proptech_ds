from pathlib import Path
import sys,json,datetime
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'analysis'))
from upload_changneung_scheduled_v8 import service
O=ROOT/'video-agent-studio/episodes/hanam-gyosan-20261019/outputs/release-prep-v5-jun'
j=json.loads((O/'upload_job.json').read_text(encoding='utf8'));p=O/'upload_receipt.json';r=json.loads(p.read_text(encoding='utf8'));assert r.get('video_id')
y=service();items=y.videos().list(part='snippet,status,contentDetails,processingDetails',id=r['video_id']).execute(num_retries=0)['items'];assert len(items)==1
v=items[0];assert v['snippet']['channelId']==j['channel_id'] and v['status']['privacyStatus']=='public'
normalize=lambda s:s.replace('\r\n','\n').strip()
title_ok=v['snippet']['title']==j['title'];desc_ok=normalize(v['snippet']['description'])==normalize(j['description'])
r.update(verification=v,verified_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),metadata_verified=title_ok and desc_ok,metadata_comparison={'title_exact':title_ok,'description_lineend_outer_whitespace_normalized':desc_ok,'submitted_description_length':len(j['description']),'returned_description_length':len(v['snippet']['description'])});p.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'url':'https://youtu.be/'+r['video_id'],'privacy':v['status']['privacyStatus'],'processing':v.get('processingDetails',{}).get('processingStatus'),'definition':v.get('contentDetails',{}).get('definition'),'comparison':r['metadata_comparison']},ensure_ascii=False))
assert title_ok and desc_ok,'Metadata differs beyond line endings or outer whitespace'
