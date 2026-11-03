from pathlib import Path
import json,subprocess,hashlib
from concurrent.futures import ThreadPoolExecutor
from PIL import Image,ImageDraw
E=Path(__file__).resolve().parent;EP=E.parent.parent;R=EP.parents[2];O=EP/'outputs/production-v6-preview';D=O/'patch_evidence_r3';D.mkdir(exist_ok=True);F=R/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe'
p=json.loads((O/'project_r3.json').read_text(encoding='utf-8'));a=json.loads((O/'rendered_project_r2.json').read_text(encoding='utf-8'));b=json.loads((O/'rendered_project_r3.json').read_text(encoding='utf-8'));assert len(a['visual_intervals'])==len(b['visual_intervals']);changed=[]
for old,new in zip(a['visual_intervals'],b['visual_intervals']):
 assert old['start_frame']==new['start_frame'] and old['end_frame']==new['end_frame'] and old['render_props']==new['render_props']
 if old['frame_file']!=new['frame_file']:changed.append([new['start_frame'],new['end_frame']])
events={}
def add(f,why):
 if 0<=f<p['duration_frames']:events.setdefault(f,[]).append(why)
for v in p['intervals']:
 if v['props'].get('cue')=='M000_C2' or v['props']['board']=='pair':
  for off in [0,15,29,v['duration_frames']-1]:add(v['start_frame']+off,v['unit'])
  add(v['start_frame']-1,'patch boundary before');add(v['end_frame'],'patch boundary after')
for f in [29,1725,20386,20832,21460]:add(f,'root required issue exact prior frame')
frames=sorted(events)
def one(item):
 i,f=item;z=subprocess.run([str(F),'-v','error','-y','-ss',f'{f/30:.9f}','-i',str(O/'changneung_full_v6_preview_r3.mp4'),'-an','-frames:v','1',str(D/f'{i:04d}.png')],stdout=subprocess.PIPE,stderr=subprocess.PIPE);assert z.returncode==0,z.stderr[-1000:]
with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(one,enumerate(frames,1)))
rows=[{'frame':f,'time_s':f/30,'file':str((D/f'{i:04d}.png').relative_to(O)).replace('\\','/'),'reasons':events[f]} for i,f in enumerate(frames,1)]
pages=[]
for page in range((len(rows)+11)//12):
 sheet=Image.new('RGB',(1920,1230),'#f6f4ef');draw=ImageDraw.Draw(sheet)
 for k,row in enumerate(rows[page*12:page*12+12]):
  x=(k%3)*640;y=(k//3)*307;sheet.paste(Image.open(O/row['file']).resize((544,306)),(x,y));draw.text((x+2,y+286),'frame '+str(row['frame']),fill='black')
 name=f'patch_contactsheet_r3_{page+1:02d}.jpg';sheet.save(O/name,quality=90);pages.append(name)
assert (O/'changneung_v6_preview_r3.srt').read_bytes()==(O/'changneung_v6_preview_r2.srt').read_bytes()
record={'issues':['QAV6-005','QAV6-006'],'mp4_sha256':hashlib.sha256((O/'changneung_full_v6_preview_r3.mp4').read_bytes()).hexdigest(),'all_timing_and_caption_props_unchanged':True,'unaffected_visual_files_identical':True,'changed_intervals':changed,'frames':rows,'contact_sheets':pages,'inherited_unaffected_qa':'cut_evidence_manifest_r2.json + independent QA r2 review','method':'accurate timestamp seeks at frame/30; actual r3 MP4 frames; all-stream decoder counts separate technical_r3.json','actual_listening':False,'continuous_human_playback':False}
(O/'patch_evidence_manifest_r3.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8');print(f'r3 {len(rows)} affected actual-MP4 evidence frames; unchanged SRT and other source states')
