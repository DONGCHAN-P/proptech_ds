from pathlib import Path
import json,subprocess,hashlib,re
from PIL import Image,ImageDraw
E=Path(__file__).resolve().parent;EP=E.parent.parent;R=EP.parents[2];O=EP/'outputs/production-v8-labels';F=R/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe';old=EP/'outputs/production-v8-preview';video=O/'changneung_full_v8_labels.mp4';D=O/'encoded_evidence';D.mkdir(exist_ok=True);p=json.loads((O/'rendered_project_v8.json').read_text());a=json.loads((E/'affected.json').read_text());frames=set();reps={}
for x in a:
 k=x['props']['mode']+x['props'].get('active','')
 reps[k]=x['start_frame']
for x in a:
 if x['props'].get('motionFrame') in [0,15,30,44]:frames.add(x['start_frame'])
for g in json.loads((O/'affected_ranges.json').read_text())['ranges']:
 for f in [g['start_frame']-1,g['start_frame'],g['end_frame']-1,g['end_frame']]:frames.add(f)
frames.update(reps.values());rows=[]
for f in sorted(frames):
 dest=D/f'f{f:05}.png';subprocess.run([str(F),'-v','error','-y','-ss',str(f/30),'-i',str(video),'-frames:v','1',str(dest)],check=True);rows.append(dict(frame=f,time_s=f/30,path=str(dest)))
for n in range(0,len(rows),12):
 sub=rows[n:n+12];im=Image.new('RGB',(1280,390*((len(sub)+1)//2)),'white');draw=ImageDraw.Draw(im)
 for i,x in enumerate(sub):im.paste(Image.open(x['path']).resize((640,360)),((i%2)*640,(i//2)*390));draw.text(((i%2)*640+5,(i//2)*390+362),str(x['frame']),fill='black')
 im.save(D/f'sheet_{n//12+1:02}.jpg')
for k,f in reps.items():Image.open(D/f'f{f:05}.png').resize((512,288)).save(D/(k+'_mobile.png'))
h=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();snap=json.loads((E/'input_snapshot.json').read_text());assert all(h(Path(x['path']))==x['sha256']for x in snap)
s0=(old/'changneung_v8_preview.srt').read_text();s1=(O/'changneung_v8_labels.srt').read_text();assert re.findall(r'\d\d:\d\d:\d\d,\d{3} --> .*',s0)==re.findall(r'\d\d:\d\d:\d\d,\d{3} --> .*',s1)
# Raw copied AAC stream must be byte-identical, independent of MP4 container metadata.
def audiohash(v):
 z=subprocess.run([str(F),'-v','error','-i',str(v),'-map','0:a:0','-c:a','copy','-f','adts','pipe:1'],capture_output=True,check=True);return hashlib.sha256(z.stdout).hexdigest()
ah0=audiohash(old/'changneung_full_v8_preview.mp4');ah1=audiohash(video);assert ah0==ah1
record=dict(final_sha256=h(video),samples=rows,mobile=list(map(str,D.glob('*mobile.png'))),original_inputs_unchanged=True,aac_stream_sha256=ah1,audio_bitstream_identical=True,caption_timestamps_identical=True,caption_cues=213,scope='Affected intervals and boundaries only; unchanged-region v8 QA inherited. No actual listening or continuous playback.');(O/'evidence_manifest.json').write_text(json.dumps(record,indent=2),encoding='utf-8');print('LABEL_EVIDENCE_VERIFIED',len(rows),flush=True)
