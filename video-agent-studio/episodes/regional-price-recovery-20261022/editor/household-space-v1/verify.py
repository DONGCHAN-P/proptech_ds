from pathlib import Path
import json,subprocess,hashlib,os,re
from PIL import Image,ImageDraw
EP=Path(__file__).resolve().parents[2];OUT=EP/'outputs/household-space-v1';ROOT=EP.parents[2]
reuse=json.loads((EP/'outputs/literature-visual-v1/reused_assets.json').read_text('utf-8'))
ff=Path(reuse['ffmpeg']);probe=ff.with_name('ffprobe.exe');video=OUT/'household_space_sample_v1.mp4'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(args):return subprocess.run([str(ff),*args],capture_output=True,text=True,encoding='utf-8')
p=subprocess.run([str(probe),'-v','error','-show_streams','-show_format','-of','json',str(video)],check=True,capture_output=True,text=True)
meta=json.loads(p.stdout);(OUT/'checks/ffprobe.json').write_text(json.dumps(meta,indent=2),'utf-8')
decoded=run(['-v','error','-i',str(video),'-f','null','-']);assert decoded.returncode==0,decoded.stderr
enc=OUT/'checks/encoded';enc.mkdir(exist_ok=True)
times=[0,2,4.5,4.6,5.7,6.0,6.5,7.0,7.5,7.8,8.1,8.3,8.7,10.3,12,15.2,19.9]
frames=[]
for i,t in enumerate(times):
    path=enc/f'frame-{i:02d}-{t}s.png'
    r=run(['-v','error','-y','-ss',str(t),'-i',str(video),'-frames:v','1',str(path)]);assert r.returncode==0,r.stderr
    frames.append({'time':t,'frame':round(t*30),'file':str(path.relative_to(ROOT).as_posix())})
sheet=Image.new('RGB',(1440,6*290),'#202427');draw=ImageDraw.Draw(sheet)
for i,row in enumerate(frames):
    im=Image.open(ROOT/row['file']).convert('RGB');im.thumbnail((472,265));x=i%3*480;y=i//3*290
    sheet.paste(im,(x,y+25));draw.text((x+8,y+5),f"{row['time']}s",(255,255,255))
sheet.save(enc/'contact.jpg',quality=90)
protected={
 EP/'outputs/literature-visual-v1/previews/literature_visual_review_v1.mp4':'da4490634c89cd371065bc293659e3a974a37a366766dd2902fb6319f76635ee',
 EP/'outputs/literature-video-v1/내레이션_초안.md':'5f40c29d4a3e0ef5255ade11eaa63cb04c8093e2c3d1d0296873126707a26d9b',
 EP/'outputs/character-quality-v1/character_quality_sample_v3.mp4':'700f3b5bd1c29bdf171194bc54ae6ce0e3bc507c4a7f69d7b3ef2f66ce41e669',
}
for path,sha in protected.items():assert digest(path)==sha,path
stream=next(s for s in meta['streams'] if s['codec_type']=='video')
assert (stream['width'],stream['height'],stream['r_frame_rate'],int(stream['nb_frames']))==(1920,1080,'30/1',600)
assert len(meta['streams'])==1
provenance=json.loads((OUT/'project/assets/provenance.json').read_text('utf-8'))
script=re.sub(r'\s+','',(EP/'outputs/literature-video-v1/내레이션_초안.md').read_text('utf-8'))
for cue in provenance['captions']:assert re.sub(r'\s+','',cue['text']) in script,cue['text']
source=(OUT/'project/compositions/home-space.html').read_text('utf-8')
assert 'lottie' not in source.lower() and 'household-characters' not in source
assert 'clock.t<8.2' in source
alias=ROOT/'영상/지역별가격회복/집공간_교체시안_v1.mp4';assert not alias.exists();os.link(video,alias)
still=alias.with_name('집공간_미리보기_v1.png');os.link(enc/'frame-16-19.9s.png',still)
result={'status':'local_direction_sample_rendered','video':str(video.relative_to(ROOT).as_posix()),'alias':str(alias),'still':str(still),'width':1920,'height':1080,'fps':30,'duration':20,'frames':600,'sha256':digest(video),'sampled_encoded_frames':len(frames),'frame_evidence':frames,'full_decode_exit_code':0,'human_animation':False,'voice':False,'new_paid_media_calls':0,'external_send':False,'continuous_playback':'unchecked','protected_files_unchanged':{str(path.relative_to(ROOT).as_posix()):sha for path,sha in protected.items()},'approved_caption_text_verified':True}
(OUT/'checks/verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ('frame_evidence','protected_files_unchanged')},ensure_ascii=False))
