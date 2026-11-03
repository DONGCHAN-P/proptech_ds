from pathlib import Path
import json,re,hashlib
EP=Path(__file__).resolve().parents[2];OUT=EP/'outputs/literature-visual-v1';T=json.loads((OUT/'project/timing.json').read_text(encoding='utf8'))
compact=lambda s:re.sub(r'\s+','',s)
checked=[]
for scene in T['scenes']:
    for beat in scene['beats']:
        cues=[c for c in T['captions'] if c['beat_id']==beat['id']]
        assert compact(' '.join(c['text'] for c in cues))==compact(beat['display_text']),beat['id']
        assert abs(cues[0]['start']-scene['start']-beat['start'])<.001
        assert abs(cues[-1]['end']-scene['start']-beat['end'])<.001
        assert all(c['end']>c['start'] for c in cues)
        assert all(abs(a['end']-b['start'])<.001 for a,b in zip(cues,cues[1:]))
        checked.append(beat['id'])
assert all(a['end']<=b['start']+.001 for a,b in zip(T['captions'],T['captions'][1:]))
assert abs(T['body_duration']-T['captions'][-1]['end']-3)<.001
script=EP/'outputs/literature-video-v1/내레이션_초안.md';assert hashlib.sha256(script.read_bytes()).hexdigest()==T['script_sha256']
record={'paragraphs':len(checked),'captions':len(T['captions']),'script_sha256':T['script_sha256'],'display_paragraph_reconstruction':'pass_with_explicit_display_mapping','caption_intervals':'positive_contiguous_per_paragraph_and_nonoverlapping','shortest_caption_seconds':min(c['end']-c['start'] for c in T['captions']),'provisional_timing':True,'actual_speech_alignment_verified':False,'last_caption_plus_hold_equals_body_end':True,'checked_beat_ids':checked}
(OUT/'checks/caption_integrity.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in record.items() if k!='checked_beat_ids'},ensure_ascii=False))
