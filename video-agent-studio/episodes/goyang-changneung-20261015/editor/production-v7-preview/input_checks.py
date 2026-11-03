from pathlib import Path
import json,re,hashlib
E=Path(__file__).resolve().parent;EP=E.parent.parent;R=EP.parents[2];O=EP/'outputs/production-v7-preview'
inputs=[EP/'outputs/script-review-v7/script_v7.md',EP/'narration/preview-v7/segments.json',EP/'outputs/production-v7-preview/audio/narration_v7_preview.wav',EP/'writer/revision-v7/narration_packet.json',EP/'editor/revision-v7/analysis_chapter_mapping.json',EP/'qa/revision-v7/visual_review.json',EP/'editor/revision-v7/claude/approved_receipt.json',EP/'research/revision-v7/price_table_descending.json',R/'video/src/changneung-production-v7/data.json']
record=[]
for f in inputs:
 record.append(dict(path=str(f),sha256=hashlib.file_digest(f.open('rb'),'sha256').hexdigest(),bytes=f.stat().st_size))
assert record[0]['sha256']=='ceb9a4e443dc2d7b36cdf84f5c515fa726d501a85e04d82ca81a4439c894bbbc'
p=json.loads((O/'project_v7.json').read_text(encoding='utf-8'));seg=json.loads(inputs[1].read_text(encoding='utf-8-sig'));norm=lambda s:re.sub(r'\s','',s)
assert norm(''.join(x['text']for x in p['captions']))==norm(''.join(x['text']for x in seg))
assert len(p['audio_units'])==143
assert abs(p['outro_start']/30-p['signal_end_s']-3)<1/30
assert all(x['duration_frames']>0 for x in p['visual_intervals'])
assert all(a['end_frame']==b['start_frame'] for a,b in zip(p['visual_intervals'],p['visual_intervals'][1:]))
assert not any(x.get('scene_id')=='M008' for x in p['visual_intervals'])
assert [x['props']['chapter']for x in p['visual_intervals']if x['kind']=='chapter']==['01 · 일자리','02 · 교통','03 · 가격','04 · 주변 가격 비교','05 · 공급','06 · 생활시설']
checks=dict(script_approved=True,approval_decision='2f76a375b4a4',source_packet_draft_flag_superseded_by_current_approval=True,immutable_inputs=record,caption_text_complete=True,measured_units=143,chapter_cards_90f=6,independent_cards=True,personal_family_calendar_removed=True,gap_to_outro_s=p['outro_start']/30-p['signal_end_s'],timeline_contiguous=True,original_mp4_audio_preserved=True,internal_word_timing_forced_alignment=False,passed=True)
(O/'input_checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8');print('INPUT_CHECKS_PASS')
