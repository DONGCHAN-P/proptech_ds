from pathlib import Path
import json,hashlib,zipfile
EP=Path(__file__).resolve().parents[2];O=EP/'outputs/stable-maps-v11'
assert (O/'completed_decision.json').exists(),'director final gate required before delivery ZIP'
files=[p for p in O.iterdir() if p.is_file() and p.suffix in ['.json','.md','.srt'] and p.name not in ['package_integrity.json','delivery_manifest.json']]
files+=[O/'stable-maps_v11_front.mp4']
manifest={p.name:{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in files}
(O/'delivery_manifest.json').write_text(json.dumps({'files':manifest,'separate_rail_clip_excluded_from_zip':True},ensure_ascii=False,indent=2),encoding='utf-8')
files=[p for p in files if p.name!='delivery_manifest.json']+[O/'delivery_manifest.json']
z=O/'stable-maps_v11_front_delivery.zip'
with zipfile.ZipFile(z,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as f:
 for p in files:f.write(p,p.name)
with zipfile.ZipFile(z) as f:assert f.testzip() is None;count=len(f.infolist())
r={'zip':str(z),'sha256':hashlib.sha256(z.read_bytes()).hexdigest(),'bytes':z.stat().st_size,'entries':count,'crc_passed':True,'includes_self':False}
(O/'package_integrity.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print(json.dumps(r))
