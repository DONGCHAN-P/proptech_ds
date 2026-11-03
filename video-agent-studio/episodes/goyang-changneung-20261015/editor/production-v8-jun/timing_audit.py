from pathlib import Path
import json,re
E=Path(__file__).resolve().parent;EP=E.parent.parent;O=EP/'outputs/production-v8-jun'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
p=read(O/'project_v8_jun.json');m=read(E/'semantic_alignment.json');diff=read(EP/'outputs/production-v8-labels/affected_ranges.json')['caption_diff'];back={x['after']:x['before']for x in diff};rows=[]
for u in m:
 a=read(EP/f'narration/jun-v8-final/{u["scene_id"]}.alignment.json');text=''.join(a['characters']);pos=u['source_char_start'];caps=[x for x in p['captions']if x['unit_id']==u['unit_id']]
 for j,c in enumerate(caps):
  needle=re.sub(r'\s','',back.get(c['text'],c['text']));acc='';start=pos
  while len(acc)<len(needle):
   if not text[pos].isspace():acc+=text[pos]
   pos+=1
  assert acc==needle
  expected=u['new_start_frame']/30 if j==0 else u['new_start_frame']/30+a['character_start_times_seconds'][start]-u['audio_start_s'];residual=c['start_frame']/30-expected;assert abs(residual)<=1/30+1e-8
  rows.append(dict(unit_id=u['unit_id'],text=c['text'],source_character_start=start,source_character_end_exclusive=pos,caption_start_frame=c['start_frame'],source_onset_on_timeline_s=expected,residual_s=residual))
  while pos<len(text)and text[pos].isspace():pos+=1
r=dict(method='Exact approved semantic clauses matched to provider original character alignment; first clause clamped to allocated PCM unit start; no text-weight time scaling',cues=rows,caption_count=len(rows),maximum_internal_onset_rounding_error_s=max(abs(x['residual_s'])for x in rows),minimum_caption_frames=min(x['end_frame']-x['start_frame']for x in p['captions']),last_signal_dbfs=-60,last_signal_s=p['signal_end_s'],outro_start_s=p['outro_start']/30,gap_s=p['outro_start']/30-p['signal_end_s'],old_timestamps_used=False)
(O/'timing_audit.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print('TIMING_AUDIT_PASS '+str(len(rows)))
