from pathlib import Path
import json,hashlib,subprocess,re
from PIL import Image,ImageDraw
P=Path(__file__).parent;E=P.parents[1];R=E.parents[2];O=E/'outputs/production-v5-jun';V=O/'gyosan_v5_jun.mp4';FF=R/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe'
sha=hashlib.sha256(V.read_bytes()).hexdigest();assert sha=='13abf7fc0b873036ad72c0b578251cb08e64ef514ecfe09fa636e26905ed214e'
d=json.loads((O/'representative_timestamps.json').read_text(encoding='utf8'));samples=d['samples']
cues=json.loads((O/'caption_cues.json').read_text(encoding='utf8'));proj=json.loads((O/'rendered_project.json').read_text(encoding='utf8'));units=proj['audio_units'];old=json.loads((E/'outputs/production-v5/caption_cues.json').read_text(encoding='utf8'))
norm=lambda s:re.sub(r'\s+','',s)
assert len(cues)==len(units)==261
assert [norm(x['text']) for x in cues]==[norm(x['text']) for x in old]
assert all(x['start_frame']<=x['speech_start_frame']<x['speech_end_frame']<=x['end_frame'] for x in cues)
assert all(a['end_frame']<=b['start_frame'] for a,b in zip(cues,cues[1:]))
for x in cues:
 if any(t in norm(x['text']) for t in ['4억9,764','5억7,167','494만4천','688만8천','5억7,855']):
  f=(x['start_frame']+x['end_frame'])//2;samples.append({'time_s':f/30,'label':'price '+x['text'],'kind':'key_numeric'})
for i,x in enumerate(samples):
 q=P/f'jun_{i:02}.png';subprocess.run([str(FF),'-v','error','-ss',str(x['time_s']),'-i',str(V),'-frames:v','1','-y',str(q)],check=True,capture_output=True);x['independent_file']=str(q)
for start in range(0,len(samples),8):
 s=Image.new('RGB',(1280,1536),'#eee');draw=ImageDraw.Draw(s)
 for j,x in enumerate(samples[start:start+8]):
  im=Image.open(x['independent_file']);im.thumbnail((640,360));xx=(j%2)*640;y=(j//2)*384;s.paste(im,(xx,y+24));draw.text((xx+4,y+4),f"{start+j} {x['time_s']:.3f}s {x['kind']}",fill='black')
 s.save(P/f'jun_sheet_{start//8+1}.jpg',quality=92)
assert hashlib.sha256(V.read_bytes()).hexdigest()==sha
(P/'encoded_manifest.json').write_text(json.dumps({'sha256':sha,'bytes':V.stat().st_size,'samples':samples,'count':len(samples),'stable_before_after':True,'cue_checks':{'261_original_text_identical':True,'all_cues_contain_aligned_speech':True,'no_caption_overlap':True},'seek_limit':'absolute frame correspondence not guaranteed'},ensure_ascii=False,indent=2),encoding='utf8')
print('stable sha; sample count',len(samples),'cue checks passed')
