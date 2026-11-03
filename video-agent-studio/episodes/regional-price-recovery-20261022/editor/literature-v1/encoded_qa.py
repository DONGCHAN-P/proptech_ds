"""Decode final MP4 and save evidence at each paragraph and scene seam."""
from pathlib import Path
import json,subprocess,math
from PIL import Image,ImageDraw,ImageFont
EP=Path(__file__).resolve().parents[2];ROOT=EP.parents[2];OUT=EP/'outputs/literature-visual-v1';Q=OUT/'checks/encoded';Q.mkdir(exist_ok=True);F=Q/'frames';F.mkdir(exist_ok=True)
T=json.loads((OUT/'project/timing.json').read_text(encoding='utf8'));M=json.loads((OUT/'reused_assets.json').read_text(encoding='utf8'));R=json.loads((OUT/'checks/assembly_receipt.json').read_text(encoding='utf8'));ff=M['ffmpeg'];video=ROOT/R['path']
points={}
for scene in T['scenes']:
    start=5+scene['start']
    for delta in [-1/30,0,1/30,1.5,3,4]:
        if start+delta>=0:points[round((start+delta)*30)]=scene['scene_id']+'-seam'
    for beat in scene['beats']:
        for frac in [.20,.75]:points[round((start+beat['start']+beat['duration']*frac)*30)]=beat['id']+f'-{frac}'
for t in [0,2,5,T['story_end']+5,T['story_end']+6.5,T['story_end']+8,T['total_duration']-1]:points[round(t*30)]='brand-or-end'
def balanced_sum(terms):
    if len(terms)==1:return terms[0]
    mid=len(terms)//2
    return '('+balanced_sum(terms[:mid])+'+'+balanced_sum(terms[mid:])+')'
ordered=sorted(points);expr=balanced_sum([f'eq(n,{n})' for n in ordered])
cmd=[ff,'-y','-v','error','-i',str(video),'-vf',f"select='{expr}'",'-fps_mode','passthrough','-frames:v',str(len(ordered)),str(F/'frame-%03d.png')]
with (Q/'extract.log').open('w',encoding='utf8') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
assert r.returncode==0;files=sorted(F.glob('frame-*.png'));assert len(files)==len(ordered),(len(files),len(ordered))
mapping=[{'file':p.relative_to(ROOT).as_posix(),'frame':n,'time':n/30,'label':points[n]} for p,n in zip(files,ordered)]
decode=[ff,'-v','error','-i',str(video),'-map','0:v:0','-an','-f','null','-']
with (Q/'decode.log').open('w',encoding='utf8') as f:result=subprocess.run(decode,stdout=f,stderr=subprocess.STDOUT)
assert result.returncode==0
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',19);sheets=[]
for batch in range(math.ceil(len(files)/16)):
    group=files[batch*16:(batch+1)*16];sheet=Image.new('RGB',(1920,4*300),(235,235,230));d=ImageDraw.Draw(sheet)
    for i,p in enumerate(group):
        im=Image.open(p).convert('RGB');im.thumbnail((480,270));x=(i%4)*480;y=(i//4)*300;sheet.paste(im,(x,y));row=mapping[batch*16+i];d.text((x+10,y+273),f'{row["time"]:.3f}s  {row["label"]}',fill=(20,40,55),font=font)
    path=Q/f'contact-{batch:02d}.jpg';sheet.save(path,quality=92);sheets.append(path.relative_to(ROOT).as_posix())
receipt={'video_sha256':R['sha256'],'video':R['path'],'total_frames':R['frames'],'decoded_successfully':True,'full_decode_exit_code':result.returncode,'evidence_frame_count':len(files),'frames':mapping,'contact_sheets':sheets,'actual_listening':False,'continuous_playback':False,'coverage':'every scene seams and two samples per narration paragraph; sparse motion samples, not continuous playback'}
(Q/'evidence.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({'decoded_successfully':True,'frames':len(files),'sheets':len(sheets),'video_sha256':R['sha256']}))
