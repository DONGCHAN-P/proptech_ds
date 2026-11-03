from pathlib import Path
import json,hashlib,zipfile
EP=Path(__file__).resolve().parents[2]
O=EP/'outputs/map-focus-v10'
q=json.loads((O/'qa_front_review.json').read_text(encoding='utf-8'))
v=O/'map-focus_v10_front.mp4';sha=hashlib.sha256(v.read_bytes()).hexdigest()
assert q['required_open_count']==0 and q['local_review_ready'] and q['sha256']==sha
assert (O/'completed_decision.json').exists(),'New exact front decision from director is required'
names=['map-focus_v10_front.mp4','map-focus_v10_front.srt','README.md','placement_guide.md','anchors.json','regional_registration_evidence.json','research_facts.json','reused_landuse_rights.json','assembly_manifest.json','technical_front.json','captions_front.json','source_hashes.json','qa_front_review.json','qa_handoff.json','completed_decision.json','handoff.json']
names += [f'telegram_receipt_{k}.json' for k in ['1','2','3','front']]
assert all((O/n).exists() for n in names)
manifest={'revision':'map-focus-v10-label-fixed','scope_s':[0,525],'front_sha256':sha,'files':[{'file':n,'bytes':(O/n).stat().st_size,'sha256':hashlib.sha256((O/n).read_bytes()).hexdigest()} for n in names],'excluded':'separate part videos remain available in output folder; old before_labelfix preserved in editor','file_transmitted':False,'publication_authorized':False}
(O/'delivery_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');names.append('delivery_manifest.json')
z=O/'map-focus_v10_front_delivery.zip'
with zipfile.ZipFile(z,'w',compression=zipfile.ZIP_STORED,allowZip64=True) as f:
 for n in names:f.write(O/n,n)
with zipfile.ZipFile(z) as f:assert f.testzip() is None
record={'file':z.name,'bytes':z.stat().st_size,'sha256':hashlib.sha256(z.read_bytes()).hexdigest(),'crc_test':'passed','entries':names,'excluded_itself':True}
(O/'zip_contents.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(record,ensure_ascii=False))
