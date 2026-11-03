"""Extract only from exact delivered MP4; no audio or video changes."""
import sys,subprocess,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
sys.path.insert(0,str(Path(__file__).resolve().parent))
import build_ui as u
def run(sid):
    p=u.H/sid;r=u.b.read(p/'render_receipt.json');assert u.b.sha(r['video'])==r['video_sha256']
    sources=u.b.read(u.H/'representative_proofs.json');sb=u.b.read(p/'storyboard.json');lock=u.b.read(u.D/'shorts'/sid/'locked_timing.json')
    frames=[]
    for x in [x for x in sources if x['short_id']==sid]:
        dest=p/'encoded_representatives'/f'{x["kind"]}.png';dest.parent.mkdir(exist_ok=True)
        subprocess.run([str(u.b.FF),'-v','error','-ss',f'{x["time_s"]:.9f}','-i',r['video'],'-frames:v','1','-y',str(dest)],check=True,creationflags=u.b.NO_WINDOW)
        frames.append(dict(label=x['kind'],time_s=x['time_s'],path=str(dest),sha256=u.b.sha(dest)))
    for i,s in enumerate(sb['scenes']):
        if i==0:continue
        for off in [-1/30,0,.1,.2,.35,.5]:
            t=s['start_s']+off;dest=p/'encoded_representatives'/f'transition-{i:02d}-{off:.3f}.jpg'
            subprocess.run([str(u.b.FF),'-v','error','-ss',f'{t:.9f}','-i',r['video'],'-frames:v','1','-q:v','2','-y',str(dest)],check=True,creationflags=u.b.NO_WINDOW)
            frames.append(dict(label=f'transition-{i:02d}',offset_s=off,time_s=t,path=str(dest),sha256=u.b.sha(dest)))
    # No-caption intervals include first frame, every real cue gap, last spoken end and last frame.
    gaps=[('last-frame',(lock['total_frames']-1)/30),('last-spoken-end',max(s['end_s']for s in lock['sentences']))]
    for i,(a,b)in enumerate(zip(lock['captions'],lock['captions'][1:])):
        if b['start_s']-a['end_s']>.04:gaps.append((f'caption-gap-{i:02d}',(a['end_s']+b['start_s'])/2))
    for label,t in gaps:
        dest=p/'encoded_representatives'/f'{label}.jpg'
        subprocess.run([str(u.b.FF),'-v','error','-ss',f'{t:.9f}','-i',r['video'],'-frames:v','1','-q:v','2','-y',str(dest)],check=True,creationflags=u.b.NO_WINDOW)
        frames.append(dict(label=label,time_s=t,path=str(dest),sha256=u.b.sha(dest)))
    font=ImageFont.truetype(str(p/'assets/Pretendard-Regular.ttf'),17)
    for name,items in [('representatives',frames[:6]),('transitions',[x for x in frames if 'offset_s'in x])]:
        cols=6;rows=(len(items)+cols-1)//cols;board=Image.new('RGB',(270*cols,522*rows),(246,244,239));draw=ImageDraw.Draw(board)
        for i,x in enumerate(items):
            xx=i%cols*270;yy=i//cols*522;im=Image.open(x['path']).convert('RGB').resize((270,480));board.paste(im,(xx,yy));draw.text((xx+5,yy+482),f'{x["label"]}\n{x["time_s"]:.3f}s',font=font,fill=(20,46,66))
        board.save(p/f'encoded_{name}_board.jpg',quality=94)
    u.save(p/'encoded_representatives.json',dict(video=r['video'],video_sha256=r['video_sha256'],scope='exact MP4-decoded stills only; continuous playback/listening not performed',frames=frames))
    print(json.dumps(dict(short_id=sid,video_sha256=r['video_sha256'],encoded_board=str(p/'encoded_representatives_board.jpg'),transition_board=str(p/'encoded_transitions_board.jpg'),frames=len(frames)),ensure_ascii=False),flush=True)
if __name__=='__main__':
    for sid in sys.argv[1:]or u.IDS:run(sid)
