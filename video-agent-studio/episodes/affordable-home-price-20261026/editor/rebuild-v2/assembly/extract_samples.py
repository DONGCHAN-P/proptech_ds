"""Extract actual encoded segment midpoints and each cut's adjacent frames.

Produces an exact sequential frame-index map with continuous-playback/listening
explicitly false. It is a sampled visual receipt, never a subjective approval.
"""
import json
import subprocess
import sys
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
import assemble as a


def extract(edl_path,movie,folder):
    from PIL import Image,ImageDraw,ImageFont
    plan=a.read(edl_path);folder=a.owned(folder)
    folder.mkdir(parents=True,exist_ok=True)
    requested={}
    def add(frame,reason):
        requested.setdefault(frame,[]).append(reason)
    for s in plan['segments']:
        add((s['start_frame']+s['end_frame']-1)//2,s['id']+' midpoint')
    for left,right in zip(plan['segments'],plan['segments'][1:]):
        cut=right['start_frame']
        for d in [-1,0,1]:add(cut+d,f'{left["id"]}->{right["id"]} cut{d:+}')
    frames=sorted(requested)
    expression='+'.join(f'eq(n,{n})' for n in frames)
    output=folder/'frame-%04d.jpg'
    a.run('encoded-sampled-frames',[str(a.FF),'-hide_banner','-v','error','-n','-i',str(movie),'-map','0:v:0','-vf',f'select={expression.replace(",",chr(92)+",")}', '-fps_mode','passthrough','-q:v','2',str(output)],[movie,edl_path],[folder/f'frame-{i:04}.jpg' for i in range(1,len(frames)+1)])
    font=ImageFont.truetype(str(a.FONT),16)
    rows=[]
    for i,frame in enumerate(frames,1):
        f=folder/f'frame-{i:04}.jpg'
        rows.append(dict(index=i,frame=frame,PTS_s=frame/30,reasons=requested[frame],file=a.pin(f),manual_viewed=False))
    for offset in range(0,len(rows),24):
        subset=rows[offset:offset+24];sheet=Image.new('RGB',(1280,math_ceil(len(subset)/4)*205),(255,255,255));draw=ImageDraw.Draw(sheet)
        for j,row in enumerate(subset):
            im=Image.open(row['file']['path']).convert('RGB');im.thumbnail((320,180));x=(j%4)*320;y=(j//4)*205
            sheet.paste(im,(x,y));draw.text((x+4,y+182),f"f{row['frame']} {row['reasons'][0]}",font=font,fill=(0,0,0))
        sheet.save(a.owned(folder/f'contact-{offset//24+1:02}.jpg'),quality=92)
    a.dump(folder/'frame_index.json',dict(mp4=a.pin(movie),edl=a.pin(edl_path),fps=30,frames=rows,source='actual encoded MP4, one sequential decode with select(n)',actual_listening=False,continuous_playback=False,all_frames_manually_viewed=False))
    print(json.dumps(dict(frames=len(rows),segments=len(plan['segments']),cuts=len(plan['segments'])-1,folder=str(folder)),ensure_ascii=False))


def math_ceil(x):
    return int(-(-x//1))


if __name__=='__main__':
    extract(a.OUT/'global_edl.json',a.OUT/'affordable_home_price_rebuild_r2_v1.mp4',a.OUT/'sampled_frames')
