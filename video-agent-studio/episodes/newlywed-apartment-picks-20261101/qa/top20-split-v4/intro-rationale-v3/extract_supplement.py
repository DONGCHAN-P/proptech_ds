"""Extract only missing exact cut/watchlist samples, separate from parent-owned frames."""
import pathlib,json,subprocess,hashlib,sys
Q=pathlib.Path(__file__).resolve().parent;E=Q.parents[2];ROOT=E.parents[2]
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'video-agent-studio/episodes/housing-choice-networth-20261020/qa/private-production-v1/asr/deps'))
from PIL import Image,ImageDraw,ImageFont
FF=ROOT/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
V=E/'outputs/top20-split-v4/intro-rationale-v3/part1_intro_revised_v2.mp4';dest=Q/'independent_frames_v2';dest.mkdir(exist_ok=True)
samples=[]
for label,b in [('brand_in',4.946190476),('brand_out',9.946190476),('data_in',16.186931217),('roadmap_in',33.548042328),('method_in',39.927671958),('bridge_in',45.131375661)]:
    frame=int(b*30+0.999999)
    samples.extend([(label+'_before',(frame-1)/30),(label+'_after',frame/30)])
samples.extend([('transient_sort_1',26.859),('transient_sort_2',27.164),('body_cut_after',48.5)])
rows=[]
for i,(label,t) in enumerate(samples):
    p=dest/f'{i:02d}_{label}.jpg'
    r=subprocess.run([str(FF),'-v','error','-ss',str(t),'-i',str(V),'-frames:v','1','-q:v','2',str(p)],capture_output=True)
    assert r.returncode==0,r.stderr
    rows.append(dict(purpose=label,time_s=t,file=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
contact=Image.new('RGB',(1600,4*249),'#d8dde2');draw=ImageDraw.Draw(contact);font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',16)
for i,r in enumerate(rows):
    im=Image.open(r['file']);im.thumbnail((400,225));x=(i%4)*400;y=(i//4)*249
    contact.paste(im,(x,y));draw.text((x+3,y+226),f"{i:02d} {r['time_s']:.3f}s {r['purpose']}",font=font,fill='black')
cp=dest/'contact_boundaries.jpg';contact.save(cp,quality=94)
(Q/'independent_frames_v2_manifest.json').write_text(json.dumps(dict(video=str(V),video_sha256=hashlib.sha256(V.read_bytes()).hexdigest(),frames=rows,contact=str(cp),reason='exact new-scene cut boundaries and two HF overlap watchlist times absent from parent49-frame set; no body/ASR duplication'),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(frames=len(rows),contact=str(cp)),ensure_ascii=False))
