from pathlib import Path
import json,hashlib
EP=Path(__file__).resolve().parents[1];O=EP/'outputs/production-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=json.loads((O/'project.json').read_text(encoding='utf8'));src=json.loads((EP/'writer/scenes_v1.json').read_text(encoding='utf8'));rows=[]
for s in src:
 us=[u for u in p['audio_units']if u['scene_id']==s['scene_id']]
 rows.append(dict(scene_id=s['scene_id'],message=s['title'],narration_text=' '.join(u['text']for u in s['units']),claim_ids=sorted({c for u in s['units']for c in u['claim_ids']}),asset_ids=[s['visual']['mode']],script_revision='script-v1',audio_revision='heami-rate2-free-v1',start=us[0]['start_frame']/30,end=us[-1]['end_frame']/30,timing_basis='Measured per-unit PCM sample duration; timeline placement on 30fps grid',status='rendered_pending_independent_qa'))
(EP/'scenes.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
rendered=O/('rendered_project_r3.json'if (O/'rendered_project_r3.json').exists()else'rendered_project.json')
record=dict(episode_id=EP.name,voice='Microsoft Heami Desktop local rate2',paid_generation_calls=0,new_paid_generation=False,extra_cash=0,source_audio_preserved='outputs/production-v1/audio-rate0',units=len(p['audio_units']),duration_s=p['duration_frames']/30,caption_count=233,timing_basis='Per-unit PCM duration, internal caption splits weighted estimation not forced alignment',outro_gap_s=3,actual_listening=False,continuous_playback=False,reference='Changneung production-v8-jun',claude_receipt='director/claude_receipt.json',fact_receipts=['research/script_v1_fact_pass_receipt.json','director/script_ref_resolution.json'],artifacts={str(x.relative_to(EP)):sha(x)for x in [O/'project.json',rendered,O/'gyosan_v1.srt',EP/'outputs/script_v1.md',EP/'writer/scenes_v1.json']})
if (O/'technical.json').exists():
 t=json.loads((O/'technical.json').read_text(encoding='utf8'));record.update(video=t['file'],video_sha256=t['sha256'],bytes=t['bytes'],decode_exit_code=t['decode_exit_code'])
(O/'delivery_manifest.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8');print('records updated')
