from pathlib import Path
import hashlib,json,zipfile
r=Path(__file__).resolve().parents[2];o=r/'outputs/video-review-v8';v=o/'namyangju-landuse_full_v8.mp4';qa=json.loads((o/'qa_final_review.json').read_text(encoding='utf-8'));actual=hashlib.sha256(v.read_bytes()).hexdigest();assert qa['required_open_count']==0 and qa['local_review_ready'];assert qa['sha256']==actual
assert (o/'completed_decision.json').exists(),'Root exact-artifact decision must exist before final package'
exclude={'scenes_before_final_timing.json','delivery_manifest.json','zip_contents.json'}
files=[p for p in o.iterdir() if p.is_file() and (p.suffix in ['.json','.md','.srt'] or p==v) and p.name not in exclude and not p.name.startswith('source_')]
manifest={'revision':'landuse-full-v8-final','mp4_sha256':actual,'files':[{'file':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(files)],'publication_authorized':False}
(o/'delivery_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');files.append(o/'delivery_manifest.json')
z=o/'namyangju-landuse_full_v8_delivery.zip'
with zipfile.ZipFile(z,'w',compression=zipfile.ZIP_STORED,allowZip64=True) as f:
 for p in sorted(files):f.write(p,p.name)
with zipfile.ZipFile(z) as f:assert f.testzip() is None;names=f.namelist()
d={'file':z.name,'bytes':z.stat().st_size,'sha256':hashlib.sha256(z.read_bytes()).hexdigest(),'crc_test':'passed','entries':names,'source_mp4_preserved':True,'archive_excludes_itself':True}
(o/'zip_contents.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:d[k] for k in ['file','bytes','sha256','crc_test']},indent=2))
