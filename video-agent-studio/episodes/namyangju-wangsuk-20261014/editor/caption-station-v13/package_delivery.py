from pathlib import Path
import json,hashlib,zipfile
EP=Path(__file__).resolve().parents[2];O=EP/'outputs/caption-station-v13';assert (O/'completed_decision.json').exists()
files=[p for p in O.iterdir() if p.is_file() and p.suffix in ['.json','.md','.srt'] and p.name not in ['delivery_manifest.json','package_integrity.json']]+[O/'caption-station_v13_full.mp4',O/'brand_intro_v13_no_caption.mp4',O/'brand_outro_v13_no_caption.mp4']
outside=[O/'caption-station_v13_front.mp4']
info=lambda p:{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
(O/'delivery_manifest.json').write_text(json.dumps({'files':{p.name:info(p) for p in files},'separate_files_available_outside_zip':{p.name:info(p) for p in outside},'raw_sources_and_intermediate_clips_excluded':True},ensure_ascii=False,indent=2),encoding='utf-8');files+=[O/'delivery_manifest.json'];z=O/'caption-station_v13_delivery.zip'
with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
 for p in files:archive.write(p,p.name)
with zipfile.ZipFile(z) as archive:assert archive.testzip() is None;count=len(archive.infolist())
r={'zip':str(z),'sha256':hashlib.sha256(z.read_bytes()).hexdigest(),'bytes':z.stat().st_size,'entries':count,'crc_passed':True,'includes_self':False};(O/'package_integrity.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print(json.dumps(r))
