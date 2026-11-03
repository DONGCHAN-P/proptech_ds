from pathlib import Path
import json,re,hashlib,wave
EP=Path('video-agent-studio/episodes/goyang-changneung-20261015'); Q=EP/'qa/production-v6-preview'
p=json.loads((EP/'outputs/production-v6-preview/project.json').read_text(encoding='utf-8'))
s=json.loads((EP/'narration/preview-v6/segments.json').read_text(encoding='utf-8'))
issues=[]
for a,b in zip(p['intervals'],p['intervals'][1:]):
 if a['unit']!=b['unit']:continue
 x=a['props'].get('caption','');y=b['props'].get('caption','')
 if re.search(r'[0-9][0-9,]*(?:억|만|천)?$',x) and re.match(r'(?:[0-9,]+|원|분|세대|년|월|㎡)',y):
  issues.append({'scene_id':a['scene_id'],'timecode':a['end_frame']/30,'before':x,'after':y})
summary={'revision':p['revision'],'script_sha256':hashlib.sha256((EP/'outputs/script-review-v6/script_v6.md').read_bytes()).hexdigest(),'script_hash_matches_approval':hashlib.sha256((EP/'outputs/script-review-v6/script_v6.md').read_bytes()).hexdigest()=='0c94b0c1547b6abd2968c6de622fbf9793cd7cd0e4ab7415664e4701fe162fc1','duration_s':p['duration_frames']/30,'intro_s':p['intro_frames']/30,'outro_s':p['outro_frames']/30,'hold_s':(p['outro_start']-p['speech_end_frame'])/30,'unit_count':len(s),'caption_count':len(p['intervals']),'numeric_boundary_candidates':issues,'actual_listening':False,'continuous_playback':False,'mp4_frame_inspection':'pending render','caption_internal_timing':'proportional estimate; not measured word alignment','source_review':'script-v6 and commute-v6 report read; immutable source full re-research excluded'}
(Q/'input_review.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False))
