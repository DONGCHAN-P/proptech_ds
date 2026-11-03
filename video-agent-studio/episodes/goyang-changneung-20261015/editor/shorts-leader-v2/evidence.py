import pathlib,json,subprocess,itertools,re
from PIL import Image,ImageDraw
R=pathlib.Path.cwd();ep=R/'video-agent-studio/episodes/goyang-changneung-20261015';ed=ep/'editor/shorts-leader-v2';out=ep/'outputs/shorts-leader-v2';v=out/'changneung_leader_short_v2.mp4';ff=R/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe';frames=[281,282,307,336,337,575,576,605,635,636,997,998,999,1020,1073,1074,1170,1265,1266,1270];rows=[]
for f in frames:
 p=out/f'check_f{f:04}.png';subprocess.run([str(ff),'-y','-v','error','-ss',str(f/30),'-i',str(v),'-frames:v','1',str(p)],check=True,capture_output=True);rows.append({'frame':f,'time_s':f/30,'path':str(p)})
im=Image.new('RGB',(360*5,660*4),'white');d=ImageDraw.Draw(im)
for i,row in enumerate(rows):
 x=i%5*360;y=i//5*660;im.paste(Image.open(row['path']).resize((360,640)),(x,y));d.text((x+5,y+644),f"f{row['frame']} / {row['time_s']:.3f}s",fill='black')
im.save(out/'regression_contactsheet.png');(out/'regression_evidence.json').write_text(json.dumps({'samples':rows,'scope':'actual decoded final MP4 samples; not continuous playback'},indent=2),encoding='utf8')
# Native YouTube internal masks, with tall-phone contain/cover inspection. No tablet universal claim.
proof=Image.new('RGB',(360*3,670*3),'white');reports=[]
for i,sec in enumerate([7,13,39]):
 base=Image.open(out/f'encoded-{sec:02}.png')
 for j,(w,h,fit) in enumerate([(360,640,'native'),(390,844,'contain'),(390,844,'cover')]):
  sc=(max if fit=='cover' else min)(w/1080,h/1920);dx=(w-1080*sc)/2;dy=(h-1920*sc)/2;im=Image.new('RGB',(w,h), '#192b3b');res=base.resize((round(1080*sc),round(1920*sc)));im.paste(res,(round(dx),round(dy)));ov=Image.new('RGBA',(w,h));d=ImageDraw.Draw(ov);d.rectangle((0,0,w,h*240/1920),fill=(190,30,30,95));d.rectangle((0,h*1400/1920,w,h),fill=(190,30,30,95));d.rectangle((w*900/1080,0,w,h),fill=(190,30,30,95));im=Image.alpha_composite(im.convert('RGBA'),ov).convert('RGB');im.thumbnail((350,640));proof.paste(im,(j*360+(360-im.width)//2,i*670+23));ImageDraw.Draw(proof).text((j*360+4,i*670+4),f'{sec}s {w}x{h} {fit}',fill='black');reports.append({'scene_seconds':sec,'viewport':[w,h],'fit':fit,'scope':'internal YouTube masks, decoded final frame'})
proof.save(out/'native_youtube_ui_proof.png');(out/'native_ui_scope.json').write_text(json.dumps({'profile':'youtube_portrait_full_frame_v2','cases':reports,'excluded':['wide tablet cover','cross-platform universal clearance','real device playback'],'model_only':True},indent=2),encoding='utf8')
# Updated complete final nine-scene sheet.
im=Image.new('RGB',(1080,1980),'white');d=ImageDraw.Draw(im)
for i,sec in enumerate([1,7,13,18,24,29,34,39,43]):
 x=i%3*360;y=i//3*660;im.paste(Image.open(out/f'encoded-{sec:02}.png').resize((360,640)),(x,y));d.text((x+5,y+644),f'{sec}s',fill='black')
im.save(out/'encoded_contactsheet.png')
b=json.loads((ed/'layout_bounds.json').read_text(encoding='utf8'));coll=[]
for frame in set(x['frame'] for x in b['elements']):
 for a,z in itertools.combinations([x for x in b['elements'] if x['frame']==frame],2):
  A=a['bbox'];B=z['bbox'];dx=min(A[2],B[2])-max(A[0],B[0]);dy=min(A[3],B[3])-max(A[1],B[1])
  if dx>1 and dy>1:coll.append({'frame':frame,'first':a['id'],'second':z['id']})
(ed/'text_overlap_validation.json').write_text(json.dumps({'collisions':coll,'passed':not coll,'frames':34},indent=2),encoding='utf8');print(json.dumps({'regression_samples':len(frames),'text_collisions':len(coll),'native_ui_previews':9}))
