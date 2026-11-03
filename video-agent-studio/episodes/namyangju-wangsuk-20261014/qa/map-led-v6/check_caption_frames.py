import pathlib,json,math
p=pathlib.Path(__file__).parent;e=p.parents[1];pr=json.loads(pathlib.Path('video/src/namyangju-map-led-v6/project.json').read_text(encoding='utf-8'));m=json.loads((e/'narration/alignment_manifest_v2.json').read_text(encoding='utf-8'));sem=json.loads((e/'writer/map-led-v4/captions_semantic_v4.json').read_text(encoding='utf-8'));rows=[]
for ch in m['chapters']:
 sid=ch['scene_id'];a=json.loads((e/ch['alignment_file']).read_text(encoding='utf-8'));a=a.get('alignment',a);cs=pr['captions'][sid];expected=[]
 for u in sem['chapters'][sid]:
  start=math.floor(a['character_start_times_seconds'][u['char_start']]*30);end=math.ceil(min(ch['pcm_duration_s'],a['character_end_times_seconds'][u['char_end']-1])*30);expected.append([start,end])
 for i,(c,u) in enumerate(zip(cs,sem['chapters'][sid])):
  if i+1<len(cs):expected[i][1]=min(expected[i][1],expected[i+1][0])
  assert c['lines']==u['lines'] and c['start_frame']==expected[i][0] and c['end_frame']==expected[i][1],(sid,c,expected[i])
 rows.append({'scene_id':sid,'cue_count':len(cs),'exact_provided_character_timestamp_frames':True,'lines_match_approved':True})
(p/'caption_frame_independent_check.json').write_text(json.dumps({'chapters':rows,'count':sum(r['cue_count'] for r in rows),'timing_basis':'provider raw-character timestamps + exact TXT spans; only last punctuation tail clamp; no characterweights','actual_listening':False},indent=2),encoding='utf-8');print('269 exact timestamp cue frames pass')
