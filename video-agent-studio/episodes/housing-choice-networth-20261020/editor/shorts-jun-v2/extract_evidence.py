"""Decode actual Shorts scene/caption/boundary samples, and measure the final audio."""
import hashlib,json,math,subprocess
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).resolve().parent;EP=HERE.parents[1];ROOT=EP.parents[2]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ffmpeg=EP/'outputs/private-production-v1/media-bin/ffmpeg.exe'
results=[]
for ident in ['funnel','analysis']:
    folder=EP/'outputs/shorts-jun-v2'/ident
    receipt=read(folder/'renders/render_receipt.json');video=ROOT/receipt['video']
    assert sha(video)==receipt['video_sha256']
    timing=read(folder/'timing.json');scenes=read(folder/'scenes.json')['scenes']
    dest=folder/'renders/encoded-evidence';dest.mkdir(exist_ok=True)
    frames={};last=round(timing['duration_s']*30)-1
    def sample(time,role,scene):
        frame=min(last,max(0,math.floor(time*30+1e-6)))
        row=frames.setdefault(frame,{'frame':frame,'time_s':frame/30,'roles':[]})
        row['roles'].append({'role':role,'scene':scene})
    for s in scenes:
        sample((s['start_s']+s['end_s'])/2,'scene_representative',s['id'])
        sample(s['start_s']+1/30,'scene_entry',s['id'])
        sample(s['end_s']-1/30,'scene_exit',s['id'])
    for q in timing['cues']:
        sample((q['start_s']+q['end_s'])/2,'caption_midpoint',q['id'])
    for a in read(folder/'anchor_audit.json')['anchors']:
        sample(a['time_s']+.7,'spoken_anchor_settled',a['literal'])
    for x in [.1,1.5,2.8]:sample(timing['last_speech_end_s']+x,'post_speech_hold','CTA')
    ordered=[frames[k] for k in sorted(frames)]
    target=dest/'frame_%04d.png'
    assert not (dest/'frame_0001.png').exists(),'Preserve extracted evidence; inspect its manifest before rerun.'
    select='+'.join(f'eq(n,{r["frame"]})' for r in ordered)
    argv=[str(ffmpeg),'-nostdin','-hide_banner','-v','error','-i',str(video),'-vf',f'select={select}','-fps_mode','vfr','-an','-n',str(target)]
    # Escape select commas at ffmpeg filtergraph level (argv transport is not shell parsing).
    argv[argv.index('-vf')+1]=argv[argv.index('-vf')+1].replace(',',r'\,')
    p=subprocess.run(argv,capture_output=True,text=True,encoding='utf8',timeout=120)
    (dest/'extract_stderr.log').write_text(p.stderr,encoding='utf8');assert p.returncode==0,p.stderr[-2000:]
    for i,row in enumerate(ordered,1):
        file=dest/f'frame_{i:04d}.png'
        with Image.open(file) as im:assert im.size==(1080,1920)
        row.update(path=file.relative_to(ROOT).as_posix(),sha256=sha(file))
    reps=[r for r in ordered if any(x['role']=='scene_representative' for x in r['roles'])]
    sheets=[];font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
    for start in range(0,len(reps),6):
        batch=reps[start:start+6];sheet=Image.new('RGB',(1080,1320),'#d8e0dc');draw=ImageDraw.Draw(sheet)
        for i,row in enumerate(batch):
            x=i%3*360;y=i//3*660
            with Image.open(ROOT/row['path']) as im:sheet.paste(im.resize((360,640),Image.Resampling.LANCZOS),(x,y))
            label=next(x['scene'] for x in row['roles'] if x['role']=='scene_representative')
            draw.text((x+8,y+640),f'{label} {row["time_s"]:.2f}s',font=font,fill='#173348')
        path=dest/f'contact_{start//6+1:02}.png';sheet.save(path)
        sheets.append({'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path),'frames':[r['frame'] for r in batch]})
    signal=dest/'signal.log'
    with signal.open('w',encoding='utf8') as f:p=subprocess.run([str(ffmpeg),'-nostdin','-hide_banner','-i',str(video),'-vn','-af','volumedetect,ebur128=peak=true','-f','null','NUL'],stdout=f,stderr=subprocess.STDOUT,timeout=120)
    assert p.returncode==0
    data={'id':ident,'video_sha256':receipt['video_sha256'],'subtitles_sha256':receipt['subtitles_sha256'],'actual_encoded_frames':ordered,'scene_contact_sheets':sheets,'sample_count':len(ordered),'signal_log':signal.relative_to(ROOT).as_posix(),'signal_log_sha256':sha(signal),'status':'extracted_not_visually_reviewed','actual_listening':False,'continuous_playback':False}
    (dest/'manifest.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    results.append({'id':ident,'samples':len(ordered),'sheets':len(sheets),'video_sha256':receipt['video_sha256']})
print(json.dumps(results))
