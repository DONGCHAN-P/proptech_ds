from pathlib import Path
import json,subprocess,hashlib
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/youtube_ai_disclosure/per_video_review_20261020/shorts';OUT.mkdir(parents=True,exist_ok=True)
FF=ROOT/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe';FP=FF.with_name('ffprobe.exe')
jobs=[
('ACJcKe1Xs2c','video-agent-studio/episodes/hanam-gyosan-20261019/outputs/shorts-release-v1/upload_job.json'),
('nfeT2nfDeS4','video-agent-studio/episodes/goyang-changneung-20261015/outputs/shorts-release-v2/upload_job.json'),
('ETXkCHF4Si0','video-agent-studio/episodes/namyangju-wangsuk-20261014/outputs/youtube-release-v15/short_01_rail_job.json'),
('cY451x1_Fz4','video-agent-studio/episodes/namyangju-wangsuk-20261014/outputs/youtube-release-v15/short_02_price_job.json'),
('Hz45kCsuuvo','video-agent-studio/episodes/namyangju-wangsuk-20261014/outputs/youtube-release-v15/short_03_choice_job.json'),
('JgOoB_-3XnI','video/out/release-v14/dongtan-gap-job.json'),
('7rRKo08NvWc','video/out/release-v14/five-questions-job.json'),
('dIcVPPvpJVM','video/out/release-v14/gtx-alone-job.json')]
catalog=[]
for ident,jp in jobs:
    job=json.loads((ROOT/jp).read_text(encoding='utf-8-sig'));video=ROOT/job['video']
    h=hashlib.sha256(video.read_bytes()).hexdigest()
    assert not job.get('sha256') or h==job['sha256']
    probe=json.loads(subprocess.check_output([str(FP),'-v','error','-show_format','-of','json',str(video)]))
    duration=float(probe['format']['duration'])
    times=[.5,duration/3,2*duration/3,duration-.5]
    sheet=Image.new('RGB',(4*270,510),'white');draw=ImageDraw.Draw(sheet)
    for i,t in enumerate(times):
        p=OUT/f'{ident}-{i}.png'
        subprocess.run([str(FF),'-v','error','-y','-ss',str(t),'-i',str(video),'-frames:v','1',str(p)],check=True)
        im=Image.open(p);im.thumbnail((270,480));sheet.paste(im,(i*270,22));draw.text((i*270+4,4),f'{t:.2f}s',fill='black')
    sp=OUT/f'{ident}-sheet.jpg';sheet.save(sp)
    catalog.append({'id':ident,'job':jp,'video':job['video'],'title':job['title'],'sha256':h,'sampled_seconds':times,'sheet':str(sp.relative_to(ROOT)).replace('\\','/')})
(OUT/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'videos':len(catalog),'frames':len(catalog)*4,'catalog':str(OUT/'catalog.json')},ensure_ascii=False))
