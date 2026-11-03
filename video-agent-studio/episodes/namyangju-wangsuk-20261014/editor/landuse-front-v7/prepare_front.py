import json
from pathlib import Path
R=Path(__file__).resolve().parents[5];H=Path(__file__).parent
p=json.loads((R/'video/src/namyangju-map-led-v6/project.json').read_text(encoding='utf-8'));END=13087
p.update(revision='landuse-front-v7',duration_frames=END,board_assets_ready=False)
p['scenes']=[s for s in p['scenes'] if s['from_frame']<END]
p['narration']=[n for n in p['narration'] if n['from_frame']<END]
p['music_regions']=[r for r in p['music_regions'] if r['from_frame']<END]
(R/'video/src/namyangju-landuse-v7/project.json').write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf-8')
gaps=[]
for n in p['narration']:
 cs=p['captions'][n['scene_id']]
 for a,b in zip(cs,cs[1:]):
  if a['end_frame']<b['start_frame']:gaps.append({'scene_id':n['scene_id'],'global_start_frame':n['from_frame']+a['end_frame'],'global_end_frame':n['from_frame']+b['start_frame'],'frames':b['start_frame']-a['end_frame']})
rootcause={'old_renderer':'NamyangjuMapLedV6.tsx Captions: return c ? white_box : null','caption_blink':'Provider-aligned semantic cues contain natural inter-cue silence; hiding whole container during gaps makes white box blink. Per-chapter mounting also omits lead-in.','fixed_renderer':'PersistentCaptions always mounts one global constant-height white container; only its text changes or is cleared. No caption timing or approved text changed.','front_end_frame':END,'front_duration_s':END/30,'cue_gap_count':len(gaps),'example_gaps':gaps[:10],'repeated_zoom':'v6 lock_timeline camera_keys resets every shot from overview to focused points; each semantic cut repeats same map movement. v7 camera will be continuous/held per board and reveal only message-related layers.','bad_context':'v6 MapStage uses official guide points without landuse boundaries; CandidateContext replaces landuse with compass relation boxes. Both are removed from active v7 board scenes.','visual_assets_status':'awaiting verified rights and plan plate/camera interface from visual/research peers'}
(H/'root_cause.json').write_text(json.dumps(rootcause,ensure_ascii=False,indent=2),encoding='utf-8');print('front',END,'frames; natural cue gaps',len(gaps))
