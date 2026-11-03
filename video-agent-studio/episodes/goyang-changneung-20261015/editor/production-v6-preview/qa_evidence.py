from pathlib import Path
import json,subprocess,hashlib
from PIL import Image,ImageDraw
E=Path(__file__).resolve().parent;EP=E.parent.parent;R=EP.parents[2];O=EP/'outputs/production-v6-preview';D=O/'cut_evidence';D.mkdir(exist_ok=True)
F=R/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe';p=json.loads((O/'project.json').read_text(encoding='utf-8'));events={};cuts=[]
def add(f,reason):
 f=max(0,min(f,p['duration_frames']-1));events.setdefault(f,[]).append(reason)
last=None
for v in p['intervals']:
 key=json.dumps({k:x for k,x in v['props'].items() if k!='caption'},sort_keys=True)
 if key!=last:
  label=f"{v['scene_id']}:{v['unit']}:{v['props'].get('board')}:{v['props'].get('focus',v['props'].get('cue',''))}"
  cuts.append({'start_frame':v['start_frame'],'label':label,'props':v['props']})
  for offset in [-1,0,15,29]:add(v['start_frame']+offset,'visual change '+label)
 last=key
 if v['unit'] in ['M002_009.wav','M002_010.wav','M002_014.wav','M004_004.wav','M006_003.wav','M007_005.wav','M007_007.wav','M007_010.wav']:add(v['start_frame']+min(40,v['duration_frames']//2),'semantic caption '+v['unit'])
for f in [p['intro_at']-1,p['intro_at'],p['intro_at']+149,p['intro_at']+150,p['intro_at']+151,p['speech_end_frame']-1,p['speech_end_frame'],p['outro_start']-1,p['outro_start'],p['outro_start']+1,p['duration_frames']-1]:add(f,'brand/hold boundary')
frames=sorted(events);expr='+'.join(f'eq(n,{f})' for f in frames);cmd=[str(F),'-v','error','-y','-i',str(O/'changneung_full_v6_preview.mp4'),'-an','-vf',f"select='{expr}'",'-fps_mode','passthrough',str(D/'%04d.png')]
subprocess.run(cmd,check=True)
rows=[]
for i,f in enumerate(frames,1):
 file=D/f'{i:04d}.png';assert file.is_file();rows.append({'file':str(file.relative_to(O)).replace('\\','/'),'frame':f,'time_s':f/30,'reasons':events[f]})
pages=[]
for page in range((len(cuts)+11)//12):
 sheet=Image.new('RGB',(1920,1230),'#f6f4ef');draw=ImageDraw.Draw(sheet)
 for k,c in enumerate(cuts[page*12:page*12+12]):
  f=min(frames,key=lambda f:abs(f-(c['start_frame']+29)));idx=frames.index(f)+1;im=Image.open(D/f'{idx:04d}.png').resize((640,360));x=(k%3)*640;y=(k//3)*307;im=im.resize((544,306));sheet.paste(im,(x,y));draw.text((x+2,y+286),f"frame {f} {c['label'][:60]}",fill='black')
 name=f'cut_contactsheet_{page+1:02d}.jpg';sheet.save(O/name,quality=90);pages.append(name)
manifest={'mp4_sha256':hashlib.sha256((O/'changneung_full_v6_preview.mp4').read_bytes()).hexdigest(),'method':'continuous decode, ffmpeg select global frame n, passthrough output sequence mapped to sorted manifest','representative_cut_count':len(cuts),'extracted_frame_count':len(rows),'cuts':cuts,'frames':rows,'contact_sheets':pages,'actual_listening':False,'continuous_human_playback':False}
(O/'cut_evidence_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');print(f'QA evidence {len(cuts)} visual changes, {len(rows)} actual MP4 frames')
