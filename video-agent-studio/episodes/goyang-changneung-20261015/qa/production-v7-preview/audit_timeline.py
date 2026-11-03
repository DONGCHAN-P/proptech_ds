import json,hashlib,wave,re,collections
from pathlib import Path
q=Path(__file__).parent; ep=q.parents[1]; out=ep/'outputs/production-v7-preview'
def rd(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def norm(s):return re.sub(r'[^가-힣A-Za-z0-9]','',s)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
p=rd(out/'project_v7.json'); seg=rd(ep/'narration/preview-v7/segments.json'); hand=rd(ep/'editor/production-v7-preview/handoff.json')
errors=[]; durations=[]
for x in hand['inputs']+hand['artifacts']:
 f=Path(x['path'])
 if f.exists() and sha(f)!=x['sha256']: errors.append(['hash',str(f)])
by={x['unit_id']:x for x in seg}
for u in p['audio_units']:
 s=by[u['unit_id']]
 with wave.open(u['audio_path']) as w: d=w.getnframes()/w.getframerate()
 delta=(u['end_frame']-u['start_frame'])/30-d
 durations.append({'unit':u['unit_id'],'pcm_s':d,'frames':u['end_frame']-u['start_frame'],'delta_s':delta})
 if abs(d-s['duration_s'])>0.00001 or abs(delta)>1/30+0.00001:errors.append(['duration',u['unit_id'],d,delta])
 caps=[x for x in p['captions'] if x['unit_id']==u['unit_id']]
 if norm(''.join(x['text'] for x in caps))!=norm(s['text']):errors.append(['caption_text',u['unit_id']])
 if not caps or caps[0]['start_frame']!=u['start_frame'] or caps[-1]['end_frame']>u['end_frame']:errors.append(['caption_bounds',u['unit_id']])
 for a,b in zip(caps,caps[1:]):
  if a['end_frame']!=b['start_frame']:errors.append(['caption_gap',u['unit_id']])
intervals=p['visual_intervals']
for a,b in zip(intervals,intervals[1:]):
 if a['end_frame']!=b['start_frame']:errors.append(['visual_gap',a['start_frame'],b['start_frame']])
cards=[x for x in intervals if x['kind']=='chapter']
for c in cards:
 if c['duration_frames']!=90:errors.append(['card',c])
split_suspects=[]
for a,b in zip(p['captions'],p['captions'][1:]):
 if a['unit_id']!=b['unit_id']:continue
 left=a['text'].rstrip();right=b['text'].lstrip()
 if (re.search(r'\d$',left) and re.match(r'(년|월|일|억|만|원|분|세대|층|㎡|제곱)',right)) or (re.search(r'\d년$',left) and re.match(r'\d+월',right)) or re.search(r'S-?$',left) and re.match(r'\d',right):split_suspects.append([a,b])
assert p['script_sha256']=='ceb9a4e443dc2d7b36cdf84f5c515fa726d501a85e04d82ca81a4439c894bbbc'
e=rd(out/'evidence_manifest.json')
result={'errors':errors,'numeric_date_unit_split_suspects':split_suspects,'audio_units':len(durations),'max_rounding_error_s':max(abs(x['delta_s']) for x in durations),'unit_duration_checks':durations,'chapter_cards':cards,'scene_order':[x['scene_id'] for x in p['scenes']],'caption_count':len(p['captions']),'minimum_caption_s':min((x['end_frame']-x['start_frame'])/30 for x in p['captions']),'caption_under_1s':[{**x,'s':(x['end_frame']-x['start_frame'])/30} for x in p['captions'] if x['end_frame']-x['start_frame']<30],'visual_intervals':len(intervals),'evidence_keys':list(e),'final_sha256':sha(out/'changneung_full_v7_preview.mp4'),'signal_to_outro_s':p['outro_start']/30-p['signal_end_s'],'internal_alignment':'PCM units measured; inside-unit caption/focus estimates, not forced alignment'}
(q/'timeline_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ['unit_duration_checks','chapter_cards']},ensure_ascii=False))
