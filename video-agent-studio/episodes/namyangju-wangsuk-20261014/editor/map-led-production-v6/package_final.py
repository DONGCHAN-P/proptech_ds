import json,hashlib,zipfile,shutil
from pathlib import Path
E=Path(__file__).resolve().parents[2];O=E/'outputs/video-review-v6';H=Path(__file__).parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
review=E/'qa/map-led-v6/final_review.json'
assert review.exists(),'Independent final review not ready'
assert (O/'completed_decision.json').exists(),'Root completed decision not ready; do not package incomplete delivery'
review_data=json.loads(review.read_text(encoding='utf-8'))
assert review_data['local_review_ready'] and review_data['required_open_count']==0
assert review_data['sha256']==sha(O/'namyangju-map-led_v6.mp4')
assert sha(review)==sha(O/'qa_final_review.json')
shutil.copy2(H/'placement_guide.md',O/'placement_guide.md')
files=[O/n for n in ['namyangju-map-led_v6.mp4','namyangju-map-led_v6.srt','captions.json','semantic_captions.json','scene_shot_manifest.json','source_license_manifest.json','project_source_hashes.json','music_mix_schedule.json','audio_cost_ledger.json','README.md','qa_final_review.json','qa_handoff.json','completed_decision.json','placement_guide.md','지역_상세지도와_의미단위_자막.md']]
files+=[O/'technical_qa/encoded_check.json',O/'technical_qa/audio_astats.txt']
assert all(p.exists() for p in files)
index={'scope':'core delivery; MP4, subtitles, timing/source/music/cost/QA/decision/guide; working proof/source preview frames and full raw production assets excluded','files':[dict(path=str(p.relative_to(O)).replace('\\','/'),size=p.stat().st_size,sha256=sha(p)) for p in files]}
(O/'zip_contents.json').write_text(json.dumps(index,ensure_ascii=False,indent=2),encoding='utf-8');files.append(O/'zip_contents.json')
z=O/'namyangju-map-led_v6_delivery.zip'
with zipfile.ZipFile(z,'w',compression=zipfile.ZIP_STORED,allowZip64=True) as a:
 for p in files:a.write(p,str(p.relative_to(O)))
with zipfile.ZipFile(z) as a:assert a.testzip() is None
delivery={'status':'rendered_technical_and_sampled_independent_review_complete','mp4':dict(file='namyangju-map-led_v6.mp4',sha256=sha(O/'namyangju-map-led_v6.mp4')),'zip':dict(file=z.name,bytes=z.stat().st_size,sha256=sha(z),entries=len(files),integrity_test='pass',compression='stored; no MP4 re-encoding'),'actual_listening':False,'continuous_playback':False,'uploaded':False,'external_file_transmission':False}
(O/'delivery_manifest.json').write_text(json.dumps(delivery,ensure_ascii=False,indent=2),encoding='utf-8')
(H/'handoff.json').write_text(json.dumps({'revision':'map-led-production-v6-final','outputs':str(O),'delivery':delivery,'inputs':{'script_revision':'script-v4-hook-outside','audio_revision':'audio-v2','source_script_sha256':'d816c5ba4341ddaafd4f3f3db6585873a519e1577d865dbf332d183925d4c2da'},'validated':['whole MP4 decode','1080p30 H264/AAC','269 exact-span semantic captions','48 contiguous shots','11 PCM-preserving narration sequences','independent sampled review','ZIP CRC integrity'],'open_checks':['actual listening and continuous playback not performed','user final review / pre-upload decision handled by director'],'next_owner':'video_director'},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(delivery))
