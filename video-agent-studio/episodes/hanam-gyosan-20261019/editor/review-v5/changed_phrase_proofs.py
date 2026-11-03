from pathlib import Path
import json,subprocess,hashlib
from PIL import Image,ImageDraw
E=Path(__file__).resolve().parent;EP=E.parents[1];R=EP.parents[2];O=EP/'outputs/production-v5';V=O/'gyosan_review_v5_free_tts.mp4';F=R/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe'
read=lambda f:json.loads(f.read_text(encoding='utf8'))
p=read(O/'rendered_project.json');reuse=read(E/'audio_reuse.json');new={r['unit_id'] for r in reuse if not r['reused']};d=read(O/'changed_timestamps.json');D=O/'changed_proofs';rows=[]
for u in p['audio_units']:
 if u['unit_id'] not in new:continue
 n=(u['start_frame']+u['end_frame'])//2;f=D/(u['unit_id']+'_new.wav_mid.png');z=subprocess.run([str(F),'-v','error','-y','-ss',str(n/30),'-i',str(V),'-frames:v','1',str(f)],capture_output=True);assert not z.returncode,z.stderr
 rows.append(dict(frame_requested=n,time_s=n/30,file=str(f),kind='new_spoken_phrase_mid',unit_id=u['unit_id'],text=u['text']))
d['samples']=[r for r in d['samples'] if r['kind']!='new_spoken_phrase_mid']+rows;(O/'changed_timestamps.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
sheet=Image.new('RGB',(1600,250*((len(rows)+3)//4)),'#ddd');draw=ImageDraw.Draw(sheet)
for i,r in enumerate(rows):
 im=Image.open(r['file']);im.thumbnail((400,225));x=i%4*400;y=i//4*250;sheet.paste(im,(x,y));draw.text((x+4,y+229),r['unit_id'],fill='black')
sheet.save(D/'new_spoken_phrases.jpg',quality=92)
print(json.dumps(dict(new_phrase_samples=len(rows),all_samples=len(d['samples']))))
