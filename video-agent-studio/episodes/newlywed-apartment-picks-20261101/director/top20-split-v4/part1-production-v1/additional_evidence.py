"""Actual encoded final states for every price comparison and both brand midpoints."""
from pathlib import Path
import hashlib,json,subprocess
from PIL import Image,ImageDraw,ImageFont
D=Path(__file__).resolve().parent;E=D.parents[2];R=E.parents[2]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    t=read(D/'locked_timing.json');r=read(D/'render_receipt_v4.json');video=Path(r['output']);assert sha(video)==r['output_sha256']
    folder=E/'qa/top20-split-v4/part1-production-v1/v4/additional_encoded_frames';folder.mkdir(parents=True,exist_ok=True)
    samples=[]
    for s in t['scenes']:
        if not s.get('region_id'):continue
        p=next(v for v in s['sentences']if v['map_phase']=='price_selected')
        samples.append({'scene_id':s['scene_id'],'purpose':'price_final','time_s':p['end_s']-.08})
    for b in t['brand_inserts']:samples.append({'scene_id':'BRAND','purpose':b['kind']+'_midpoint','time_s':b['start_s']+b['duration_s']/2})
    ff=R/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
    for i,s in enumerate(samples):
        dest=folder/f"{i:02d}_{s['scene_id']}_{s['purpose']}.jpg"
        run=subprocess.run([str(ff),'-v','error','-y','-ss',str(s['time_s']),'-i',str(video),'-frames:v','1','-q:v','2',str(dest)],capture_output=True)
        assert run.returncode==0 and dest.exists();s.update(file=str(dest),sha256=sha(dest))
    im=Image.new('RGB',(1440,1188),'#e7e9ea');draw=ImageDraw.Draw(im);font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18)
    for i,s in enumerate(samples):
        x=i%3*480;y=i//3*297;p=Image.open(s['file']).convert('RGB');p.thumbnail((480,270));im.paste(p,(x,y));draw.text((x+5,y+273),f"{i:02d} {s['time_s']:.2f}s {s['scene_id']} {s['purpose']}",font=font,fill='#173348')
    contact=folder.parent/'price_final_contact.jpg';im.save(contact,quality=94)
    (folder.parent/'additional_encoded_manifest.json').write_text(json.dumps({'video':str(video),'video_sha256':sha(video),'frames':samples,'contact_sheet':str(contact),'actual_listening':False,'continuous_playback':False},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'additional_frames':len(samples),'contact':str(contact)},ensure_ascii=False))
if __name__=='__main__':main()
