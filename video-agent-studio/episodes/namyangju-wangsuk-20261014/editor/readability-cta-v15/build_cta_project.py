from pathlib import Path
import json,math,hashlib
EP=Path(__file__).resolve().parents[2];ROOT=EP.parents[2];O=EP/'outputs/readability-cta-v15';N=EP/'narration/cta-v8'
p=json.loads((ROOT/'video/src/namyangju-v14/project_v14.json').read_text(encoding='utf-8'));p['revision']='readability-cta-v15';p['script_revision']='script-v8-user-literal-CTA';p['duration_frames']=27959;p['audio_revision']='v14-preserved+cta-v8'
raw=json.loads((N/'M010.captions_timed.json').read_text(encoding='utf-8'));p['captions']['M010']=[{**c,'start_frame':math.floor(c['start_s']*30+1e-7),'end_frame':math.ceil(c['end_s']*30-1e-7)} for c in raw['cues']]
a=N/'M010.mp3';(ROOT/'video/public/namyangju-v15/M010_cta.mp3').write_bytes(a.read_bytes());p['narration'].append({'scene_id':'M010','file':'namyangju-v15/M010_cta.mp3','from_frame':27353,'duration_frames':224,'sha256':hashlib.sha256(a.read_bytes()).hexdigest(),'script_revision':'script-v8-user-literal-CTA','audio_revision':'cta-v8'})
(ROOT/'video/src/namyangju-v15/project_v15.json').write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf-8')
flat=[]
for n in p['narration']:
 for c in p['captions'][n['scene_id']]:flat.append({'scene_id':n['scene_id'],'from_frame':n['from_frame']+c['start_frame'],'to_frame':n['from_frame']+c['end_frame'],'lines':c['lines']})
assert len(flat)==305
def stamp(ms):h=ms//3600000;ms%=3600000;m=ms//60000;ms%=60000;return f'{h:02}:{m:02}:{ms//1000:02},{ms%1000:03}'
srt='\n\n'.join(f"{i+1}\n{stamp(round(c['from_frame']/30*1000))} --> {stamp(round(c['to_frame']/30*1000))}\n"+'\n'.join(c['lines']) for i,c in enumerate(flat))+'\n'
(O/'namyangju_readability_cta_full_v15.srt').write_text(srt,encoding='utf-8');(O/'timed_captions_v15.json').write_text(json.dumps(flat,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'caption_count':305,'video_frames':27959}))
