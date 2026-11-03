"""Add the verified newly uploaded main ID before creating the two Shorts uploads."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[5]
EP=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
OUT=EP/'outputs/top20-production-v1'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
r=read(HERE/'uploads/main/upload_receipt.json')
assert r['verification']['status']['privacyStatus']=='private'
url='https://youtu.be/'+r['video_id']
manifest=read(OUT/'release_manifest.json')
for kind in ['promo','analysis']:
    assert not (HERE/'uploads'/kind/'upload_receipt.json').exists()
    p=OUT/'metadata'/(kind+'.json');meta=read(p)
    if url not in meta['description']:meta['description']='본편: '+url+'\n\n'+meta['description']
    meta.update(main_video_link_pending=False,main_video_id=r['video_id'],main_video_url=url,description_utf8_bytes=len(meta['description'].encode('utf-8')))
    assert meta['description_utf8_bytes']<=5000
    save(p,meta);(OUT/'metadata'/(kind+'_설명.txt')).write_text(meta['description'],encoding='utf-8')
    item=next(x for x in manifest['items'] if x['id']==kind)
    item['metadata_sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
save(OUT/'release_manifest.json',manifest)
print(json.dumps({'shorts_linked_to_private_main':url,'native_related_video_setting_applied':False},ensure_ascii=False))
