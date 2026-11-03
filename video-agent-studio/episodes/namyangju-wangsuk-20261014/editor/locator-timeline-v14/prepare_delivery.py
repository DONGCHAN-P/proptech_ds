from pathlib import Path
import json,hashlib,shutil
EP=Path(__file__).resolve().parents[2];ROOT=EP.parents[2];O=EP/'outputs/locator-timeline-v14';S=O/'sources';S.mkdir(exist_ok=True)
inputs=[EP/'timing_lock_v14.json',EP/'outputs/story-review-v7/manifest.json',EP/'narration/region-leaders-v7/alignment_manifest.json',EP/'research/region-leaders-v14/price_map.json',EP/'research/region-leaders-v14/locator_transform.json',EP/'research/region-leaders-v14/w1_middle_geometry.json',EP/'research/region-leaders-v14/north_closing_map.json',EP/'research/landuse-v7/source_rights.json',EP/'research/ilpae-v13/joint_geometry.json']
records=[]
for p in inputs:
 if p.exists():
  target=S/p.name;shutil.copy2(p,target);records.append({'source':str(p.relative_to(ROOT)),'delivery':str(target.relative_to(O)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
guide=ROOT/'video-agent-studio/guides';shutil.copy2(next(guide.glob('*.md')),O/'map_caption_guide.md')
sourcefiles=list((ROOT/'video/src/namyangju-v14').glob('*.tsx'))+list((ROOT/'video/src/namyangju-v14').glob('*.json'))+list((ROOT/'video/public/namyangju-v14').glob('*.json'))
manifest={'revision':'locator-timeline-v14','source_script_sha256':'6ce6fefb6cbd439b7073091a0107ec65261ba8638aeeb0f339369c0e68640737','source_records':records,'editor_source_files':[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sourcefiles],'rights_notes':['Whole landuse locator and native detail are own factual reconstructions from verified official source-native coordinates; no implied permission to redistribute cropped official source raster.','OSM geographic geometry attribution preserved.','Company CI and existing brand/music provenance reused from prior episode verified assets; no new paid image/video generation.'],'caption_policy':'301 semantic cues; first9 chapters original captions/times unchanged; new72 from exact raw character alignment; punctuation-only terminal clamp documented by narration','audio_policy':'prefix decoded PCM samples exactly reused; new2 narration chapters and existing brand audio concatenated sample-exact; final AAC reencoded','cash_new_payment':0,'new_narration_included_credits':616,'actual_listening':False,'continuous_playback':False}
(O/'source_manifest_v14.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'source_records':len(records),'source_files':len(sourcefiles)}))
