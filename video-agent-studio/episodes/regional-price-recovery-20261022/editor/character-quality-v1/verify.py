from pathlib import Path
import json,subprocess,hashlib,shutil,os
from PIL import Image,ImageDraw,ImageFont
EP=Path(__file__).resolve().parents[2]; OUT=EP/'outputs/character-quality-v1'
reuse=json.loads((EP/'outputs/literature-visual-v1/reused_assets.json').read_text('utf-8'))
ff=Path(reuse['ffmpeg']);probe=ff.with_name('ffprobe.exe')
video=OUT/'character_quality_sample_v3.mp4'
def run(args):
    return subprocess.run([str(ff),*args],capture_output=True,text=True,encoding='utf-8')
p=subprocess.run([str(probe),'-v','error','-show_streams','-show_format','-of','json',str(video)],check=True,capture_output=True,text=True)
meta=json.loads(p.stdout);(OUT/'checks/ffprobe.json').write_text(json.dumps(meta,indent=2),'utf-8')
decoded=run(['-v','error','-i',str(video),'-f','null','-'])
assert decoded.returncode==0,decoded.stderr
enc=OUT/'checks/encoded-v3';enc.mkdir(exist_ok=True)
times=[0,2,4.9,5.2,6,7,8,9,10,10.5,12,15.5,19.9]
for i,t in enumerate(times):
    result=run(['-v','error','-y','-ss',str(t),'-i',str(video),'-frames:v','1',str(enc/f'{i:02d}-{t}s.png')]);assert result.returncode==0,result.stderr
thumbs=Image.new('RGB',(1440,5*290),'#202427');draw=ImageDraw.Draw(thumbs)
for i,t in enumerate(times):
    im=Image.open(enc/f'{i:02d}-{t}s.png').convert('RGB');im.thumbnail((472,265))
    x=(i%3)*480;y=(i//3)*290
    thumbs.paste(im,(x,y+25));draw.text((x+8,y+5),f'{t}s',(255,255,255))
thumbs.save(enc/'contact.jpg',quality=90)
old=EP/'outputs/literature-visual-v1/previews/literature_visual_review_v1.mp4'
old_sha=hashlib.sha256(old.read_bytes()).hexdigest();assert old_sha=='da4490634c89cd371065bc293659e3a974a37a366766dd2902fb6319f76635ee'
script=EP/'outputs/literature-video-v1/내레이션_초안.md'
script_sha=hashlib.sha256(script.read_bytes()).hexdigest();assert script_sha=='5f40c29d4a3e0ef5255ade11eaa63cb04c8093e2c3d1d0296873126707a26d9b'
stream=next(x for x in meta['streams'] if x['codec_type']=='video')
assert (stream['width'],stream['height'],stream['r_frame_rate'],int(stream['nb_frames']))==(1920,1080,'30/1',600)
assert len(meta['streams'])==1
shelf=EP.parents[2]/'영상/지역별가격회복'
assert shelf.is_dir(),shelf
alias=shelf/'인물교체_20초_v3.mp4'; assert not alias.exists()
os.link(video,alias)
still=shelf/'인물교체_미리보기_v3.png';os.link(enc/'12-19.9s.png',still)
result={'status':'rendered_visual_prototype','video':str(video),'alias':str(alias),'still':str(still),'width':1920,'height':1080,'fps':30,'duration':20,'frames':600,'sha256':hashlib.sha256(video.read_bytes()).hexdigest(),'sampled_encoded_frames':len(times),'full_decode_exit_code':0,'voice':False,'paid_calls':0,'external_send':False,'continuous_playback':'unchecked','actual_listening':'not_applicable_silent','preserved_old_video_sha256':old_sha,'preserved_script_sha256':script_sha}
(OUT/'checks/verification-v3.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps(result,ensure_ascii=False))
