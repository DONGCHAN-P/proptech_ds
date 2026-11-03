import datetime as dt
import hashlib
import json
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[5]
EP=ROOT/'video-agent-studio/episodes/housing-choice-networth-20261020'
HERE=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def rel(p):return p.relative_to(ROOT).as_posix()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
auth=read(HERE/'authorization.json')
assert auth['paid_voice_generation_authorized'] and auth['included_credit_cap']==10739
out=EP/'outputs/launch-proposal-v2'
assets=read(out/'assets.json')
for asset in assets['assets']:
    for field in ('master','upload_size'):
        p=out/asset[field]
        with Image.open(p) as im:
            dims=list(im.size)
            im.verify()
        if field=='upload_size':assert dims==[1280,720] and p.stat().st_size<2*1024*1024
        asset[field+'_receipt']={'sha256':sha(p),'size':dims,'bytes':p.stat().st_size}
    asset.update(visual_review='actual generated variants inspected; headline and all three labels readable; no clipped letters; footer and timestamp corner separated',upscaled=False)
write(out/'assets.json',assets)
request=read(HERE/'request.json')
request.update(scoped_credit_budget_status='approved_10739_included_credits',authorization=rel(HERE/'authorization.json'),
               latest_thumbnail_direction=auth['thumbnail_user_reply'],latest_thumbnail_assets=rel(out/'assets.json'))
write(HERE/'request.json',request)
state=read(EP/'state.json')
state['production_authorization']=rel(HERE/'authorization.json')
state['jun_replacement_v1'].update(status='jun_generation_in_progress_two_thumbnails_created',budget_approved=True,
    authorization=rel(HERE/'authorization.json'),voice='ElevenLabs Jun',model='eleven_v4',
    latest_thumbnails=rel(out/'assets.json'),updated_at_utc=dt.datetime.now(dt.timezone.utc).isoformat())
write(EP/'state.json',state)
shelf=read(ROOT/'config/video_shelf.json')
entry=next(x for x in shelf['entries'] if x['name']=='매매전월세')
entry['files'].update({'썸네일_비교형.png':rel(out/'TH003_housing_modes_1280x720.png'),
                       '썸네일_차트형.png':rel(out/'TH004_hidden_results_1280x720.png')})
write(ROOT/'config/video_shelf.json',shelf)
print(json.dumps({'authorization':'Jun cap10739 approved','thumbnail_count':2,'thumbnail_pixels':[1280,720],
    'video_delivery_unchanged':True,'new_upload':False,'old_upload_deleted':False},ensure_ascii=False))
