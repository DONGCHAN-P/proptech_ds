from pathlib import Path
import json,subprocess,hashlib,os,re,math
from PIL import Image,ImageDraw
EP=Path(__file__).resolve().parents[2];ROOT=EP.parents[2];OUT=EP/'outputs/relocation-space-v1';P=OUT/'project'
reuse=json.loads((EP/'outputs/literature-visual-v1/reused_assets.json').read_text('utf-8'));ff=Path(reuse['ffmpeg']);probe=ff.with_name('ffprobe.exe');video=OUT/'relocation_space_chapter_v1.mp4'
timing=json.loads((P/'timing.json').read_text('utf-8'));D=timing['duration']
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def run(args):return subprocess.run([str(ff),*args],capture_output=True,text=True,encoding='utf-8')
meta=json.loads(subprocess.run([str(probe),'-v','error','-show_streams','-show_format','-of','json',str(video)],check=True,capture_output=True,text=True).stdout)
(OUT/'checks/ffprobe.json').write_text(json.dumps(meta,indent=2),'utf-8')
decode=run(['-v','error','-i',str(video),'-f','null','-']);assert decode.returncode==0,decode.stderr
stream=next(s for s in meta['streams'] if s['codec_type']=='video')
assert (stream['width'],stream['height'],stream['r_frame_rate'],int(stream['nb_frames']))==(1920,1080,'30/1',round(D*30))
assert len(meta['streams'])==1
norm=lambda s:re.sub(r'\s+','',s)
for beat in timing['beats']:
    text=' '.join(c['text'] for c in timing['captions'] if c['beat_id']==beat['id'])
    assert norm(text)==norm(beat['display_text']),beat['id']
for i,cue in enumerate(timing['captions']):
    assert 0<=cue['start']<cue['end']<=D
    if i:assert cue['start']>=timing['captions'][i-1]['end']-1e-7
protected={
 EP/'outputs/literature-visual-v1/previews/literature_visual_review_v1.mp4':'da4490634c89cd371065bc293659e3a974a37a366766dd2902fb6319f76635ee',
 EP/'outputs/literature-video-v1/내레이션_초안.md':'5f40c29d4a3e0ef5255ade11eaa63cb04c8093e2c3d1d0296873126707a26d9b',
 EP/'outputs/household-space-v1/household_space_sample_v1.mp4':'67851a459535ba6f93feba957aa28abfd0af615d20e7af7322d78aa71a38424a'}
for path,sha in protected.items():assert digest(path)==sha,path
times=[0,3.5,9.5,12.3,13.6,16,22,24.15,24.2333,27,35,38.6333,38.7,41,47,53,56.5,56.5667,60,68,72.5333,72.6,76,83,85.6,86.4]
enc=OUT/'checks/encoded';enc.mkdir(exist_ok=True);frames=[]
for i,t in enumerate(times):
    path=enc/f'frame-{i:02d}-{t}s.png';r=run(['-v','error','-y','-ss',str(t),'-i',str(video),'-frames:v','1',str(path)]);assert r.returncode==0,r.stderr
    frames.append({'time':t,'file':path.relative_to(ROOT).as_posix()})
for page in range(math.ceil(len(frames)/12)):
    rows=frames[page*12:(page+1)*12];sheet=Image.new('RGB',(1440,math.ceil(len(rows)/3)*290),'#202427');draw=ImageDraw.Draw(sheet)
    for i,row in enumerate(rows):
        im=Image.open(ROOT/row['file']).convert('RGB');im.thumbnail((472,265));x=i%3*480;y=i//3*290;sheet.paste(im,(x,y+25));draw.text((x+8,y+5),f"{row['time']}s",(255,255,255))
    sheet.save(enc/f'contact-{page+1}.jpg',quality=90)
def stamp(t):
    ms=round(t*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000);return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'
srt='\n\n'.join(f"{i+1}\n{stamp(c['start'])} --> {stamp(c['end'])}\n{c['text']}" for i,c in enumerate(timing['captions']))+'\n'
(OUT/'relocation_space_v1_provisional.srt').write_text(srt,'utf-8')
alias=ROOT/'영상/지역별가격회복/재건축이주_검토본_v1.mp4'
if alias.exists():assert os.path.samefile(video,alias)
else:os.link(video,alias)
still=alias.with_name('재건축이주_미리보기_v1.png')
if still.exists():assert os.path.samefile(enc/'frame-06-22s.png',still)
else:os.link(enc/'frame-06-22s.png',still)
result={'status':'complete_chapter_visual_review_rendered','scene_id':'L004','video':video.relative_to(ROOT).as_posix(),'alias':str(alias),'still':str(still),'sha256':digest(video),'width':1920,'height':1080,'fps':30,'duration':float(meta['format']['duration']),'frames':int(stream['nb_frames']),'caption_cues':len(timing['captions']),'full_caption_reconstruction_verified':True,'provisional_timing':True,'human_animation':False,'new_paid_media_calls':0,'voice':False,'external_send':False,'continuous_playback':'unchecked','full_decode_exit_code':0,'sampled_encoded_frames':len(frames),'frame_evidence':frames,'protected_files_unchanged':{p.relative_to(ROOT).as_posix():s for p,s in protected.items()}}
(OUT/'checks/verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ('frame_evidence','protected_files_unchanged')},ensure_ascii=False))
