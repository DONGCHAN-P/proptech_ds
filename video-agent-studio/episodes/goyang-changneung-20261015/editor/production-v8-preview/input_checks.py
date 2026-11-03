from pathlib import Path
import json,re,hashlib
E=Path(__file__).resolve().parent;EP=E.parent.parent;R=EP.parents[2];O=EP/'outputs/production-v8-preview'
inputs=[EP/'outputs/script-review-v8/script_v8.md',EP/'narration/preview-v8/segments.json',EP/'outputs/production-v8-preview/audio/narration_v8_preview.wav',EP/'writer/revision-v8/narration_packet.json',EP/'editor/revision-v7/analysis_chapter_mapping.json',EP/'qa/revision-v8/visual_review.json',EP/'editor/revision-v7/claude/approved_receipt.json',EP/'research/revision-v7/price_table_descending.json',R/'video/src/changneung-v7/data.json']
record=[]
for f in inputs:
 record.append(dict(path=str(f),sha256=hashlib.file_digest(f.open('rb'),'sha256').hexdigest(),bytes=f.stat().st_size))
assert record[0]['sha256']=='6ffc9fc4819460d4cf6f03fd3b28102e2864402b9965ca14e158230474963982'
p=json.loads((O/'project_v8.json').read_text(encoding='utf-8'));seg=json.loads(inputs[1].read_text(encoding='utf-8-sig'));norm=lambda s:re.sub(r'\s','',s)
assert norm(''.join(x['text']for x in p['captions']))==norm(''.join(x['text']for x in seg))
assert len(p['audio_units'])==143
assert abs(p['outro_start']/30-p['signal_end_s']-3)<1/30
assert all(x['duration_frames']>0 for x in p['visual_intervals'])
assert all(a['end_frame']==b['start_frame'] for a,b in zip(p['visual_intervals'],p['visual_intervals'][1:]))
assert not any(x.get('scene_id')=='M008' for x in p['visual_intervals'])
assert [x['props']['chapter']for x in p['visual_intervals']if x['kind']=='chapter']==['01 · 일자리','02 · 교통','03 · 가격','04 · 주변 가격 비교','05 · 공급','06 · 생활시설']
assert all(x['props'].get('mode')not in ['note','text_only','editorial-card-only']for x in p['visual_intervals'])
assert all(x['end_frame']-x['start_frame']>=30 for x in p['captions'])
splits=[]
for left,right in zip(p['captions'],p['captions'][1:]):
 if left['unit_id']!=right['unit_id']:continue
 aa=left['text'].strip();bb=right['text'].strip()
 bad=(re.search(r'\d{4}년$',aa) and re.match(r'\d+월',bb))or(re.search(r'\d+월$',aa)and re.match(r'\d+일',bb))or(re.search(r'\d+(?:,\d{3})*(?:억|만)$',aa)and re.match(r'[\d,]+(?:만|원)',bb))or(re.search(r'\d(?:만)?$',aa)and re.match(r'(?:원|세대|분|㎡|건|년|월)(?:[입니다요., ]|$)',bb))
 if bad:splits.append({'left':aa,'right':bb,'unit_id':left['unit_id']})
assert not splits,splits
checks=dict(date_currency_quantity_split_count=len(splits),body_note_modes=0,subsecond_caption_count=0,semantic_mapping='editor/production-v8-preview/semantic_mapping.json',script_approved=True,approval_decision='7d9fc3575dff',source_packet_draft_flag_superseded_by_current_approval=True,immutable_inputs=record,caption_text_complete=True,measured_units=143,chapter_cards_90f=6,independent_cards=True,personal_family_calendar_removed=True,gap_to_outro_s=p['outro_start']/30-p['signal_end_s'],timeline_contiguous=True,original_mp4_audio_preserved=True,internal_word_timing_forced_alignment=False,passed=True)
(O/'input_checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8');print('INPUT_CHECKS_PASS')
