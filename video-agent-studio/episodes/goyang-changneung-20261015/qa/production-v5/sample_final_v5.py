from pathlib import Path
import argparse,json,subprocess,hashlib
from PIL import Image,ImageDraw
Q=Path(__file__).resolve().parent;EP=Q.parents[1];ROOT=EP.parents[2];O=EP/'outputs/production-v5';F=ROOT/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe'
ap=argparse.ArgumentParser();ap.add_argument('file');args=ap.parse_args();movie=Path(args.file)
p=json.loads((O/'rendered_project_v5.json').read_text('utf8'));N=p['duration_frames'];wanted={0,612,613,762,763,764,765,23747,23748,23749,23750,23839,23840,23841,24139}
for s in p['shots']:
 wanted.add((s['start_frame']+s['end_frame'])//2)
 for d in [-1,0,1]:wanted.add(max(0,min(N-1,s['start_frame']+d)))
for c in p['captions']:wanted.add((c['start_frame']+c['end_frame'])//2)
m=json.loads((O/'cue_focus_matrix_v5.json').read_text('utf8'))
for c in m['cue_rows']:
 for e in c['entity_events']:
  if e.get('start_frame') is not None:
   wanted.update([max(0,e['start_frame']-1),e['start_frame']])
for v in p['visual_intervals']:
 if v.get('motion') and v['render_props'].get('motionFrame') in [0,1,6,12,18,23,24]:wanted.add(v['start_frame'])
wanted.update([17180,17181,17305,17306,17311,17590,17591])
out=Q/'encoded_frames';out.mkdir(exist_ok=True);sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();before=sha(movie)
proc=subprocess.Popen([str(F),'-v','error','-i',str(movie),'-an','-vf','scale=640:360','-fps_mode','passthrough','-c:v','mjpeg','-q:v','2','-f','image2pipe','pipe:1'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
buf=b'';n=0
while chunk:=proc.stdout.read(1024*1024):
 buf+=chunk
 while True:
  a=buf.find(b'\xff\xd8');b=buf.find(b'\xff\xd9',max(a,0))
  if a<0 or b<0:break
  if n in wanted:(out/f'frame_{n:06}.jpg').write_bytes(buf[a:b+2])
  n+=1;buf=buf[b+2:]
stderr=proc.stderr.read().decode(errors='replace');code=proc.wait();frames=sorted(wanted)
for start in range(0,len(frames),18):
 batch=frames[start:start+18];canvas=Image.new('RGB',(1920,((len(batch)+2)//3)*380),'#ddd');draw=ImageDraw.Draw(canvas)
 for i,f in enumerate(batch):
  x=i%3*640;y=i//3*380;canvas.paste(Image.open(out/f'frame_{f:06}.jpg'),(x,y+20));draw.text((x+4,y+3),f'frame {f} | {f/30:.3f}s',fill='black')
 canvas.save(Q/f'encoded_contact_{start//18+1:02}.jpg')
record={'file':str(movie.resolve()),'sha256_before':before,'sha256_after':sha(movie),'decoded_output_frames':n,'exit_code':code,'stderr':stderr,'selected_count':len(frames),'frames':frames,'method':'전구간 MJPEG 출력의 전역순번 직접계수. 필터 내부 n 미사용. 640x360 표본이미지. 실제 연속 재생/청취 아님.','actual_listening':False,'continuous_playback':False}
(Q/'encoded_frame_manifest.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),'utf8');print(json.dumps({k:v for k,v in record.items() if k!='frames'},ensure_ascii=False),flush=True)
