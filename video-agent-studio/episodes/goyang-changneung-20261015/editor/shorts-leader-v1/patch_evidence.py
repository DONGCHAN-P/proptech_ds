import pathlib,json,subprocess,itertools,re
from PIL import Image,ImageDraw
R=pathlib.Path.cwd();ep=R/'video-agent-studio/episodes/goyang-changneung-20261015';ed=ep/'editor/shorts-leader-v1';out=ep/'outputs/shorts-leader-v1';ff=R/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe';v=out/'changneung_leader_short_v1.mp4';frames=[281,282,307,336,337,575,576,605,635,636,997,998,999,1020,1073,1074,1170,1265,1266,1270]
rows=[]
for f in frames:
 p=out/f'patch_f{f:04}.png';subprocess.run([str(ff),'-y','-v','error','-ss',str(f/30),'-i',str(v),'-frames:v','1',str(p)],check=True,capture_output=True);rows.append({'frame':f,'time_s':f/30,'path':str(p)})
im=Image.new('RGB',(360*5,660*4),'white');d=ImageDraw.Draw(im)
for i,row in enumerate(rows):
 x=i%5*360;y=i//5*660;im.paste(Image.open(row['path']).resize((360,640)),(x,y));d.text((x+5,y+644),f"f{row['frame']} / {row['time_s']:.3f}s",fill='black')
im.save(out/'patch_contactsheet.png');(out/'patch_evidence.json').write_text(json.dumps({'samples':rows,'scope':'actual decoded final MP4 samples; not continuous playback'},indent=2),encoding='utf8')
b=json.loads((ed/'layout_bounds.json').read_text(encoding='utf8'));coll=[]
for frame in set(x['frame'] for x in b['elements']):
 for a,z in itertools.combinations([x for x in b['elements'] if x['frame']==frame],2):
  A=a['bbox'];B=z['bbox'];dx=min(A[2],B[2])-max(A[0],B[0]);dy=min(A[3],B[3])-max(A[1],B[1])
  if dx>1 and dy>1:coll.append({'frame':frame,'first':a['id'],'second':z['id']})
(ed/'text_overlap_validation.json').write_text(json.dumps({'collisions':coll,'passed':not coll,'frames':34},indent=2),encoding='utf8')
data=json.loads((R/'video/src/changneung-shorts-leader-v1/data.json').read_text(encoding='utf8'));checks=[]
for c in data['clips']:
 cap=[x for x in data['captions'] if x['unit_id']==c['unit_id']];norm=lambda s:re.sub(r'\s+','',s);checks.append({'unit_id':c['unit_id'],'complete_exact_semantic_text':norm(''.join(x['text'] for x in cap))==norm(c['text']),'caption_count':len(cap),'within_audio_handles':all(x['start']>=c['clip_start'] and x['end']<=c['clip_end']+.001 for x in cap),'minimum_caption_s':min(x['end']-x['start'] for x in cap)})
(ed/'caption_validation.json').write_text(json.dumps({'checks':checks,'all_passed':all(x['complete_exact_semantic_text'] and x['within_audio_handles'] and x['minimum_caption_s']>=1 for x in checks),'timing_basis':'provider original-character timestamps; no listening assertion'},ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'patch_samples':len(frames),'text_collisions':len(coll),'caption_checks':len(checks)}))
