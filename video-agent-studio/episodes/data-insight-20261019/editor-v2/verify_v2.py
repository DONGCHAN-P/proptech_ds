import pathlib,json,subprocess,hashlib
from PIL import Image,ImageDraw
EP=pathlib.Path(__file__).resolve().parents[1];ROOT=EP.parents[2]
bin=ROOT/'video/node_modules/@remotion/compositor-win32-x64-msvc';out=EP/'outputs/v2/data_insight_30s_v2.mp4';ed=EP/'editor-v2';frames=ed/'frames';frames.mkdir(exist_ok=True)
p=subprocess.run([str(bin/'ffprobe.exe'),'-v','error','-count_frames','-show_streams','-show_format','-of','json',str(out)],capture_output=True,text=True,check=True)
probe=json.loads(p.stdout);(ed/'ffprobe.json').write_text(p.stdout,encoding='utf8')
v=next(s for s in probe['streams'] if s['codec_type']=='video');a=next(s for s in probe['streams'] if s['codec_type']=='audio')
assert (v['width'],v['height'],v['avg_frame_rate'],int(v['nb_frames']),int(v['nb_read_frames']))==(1920,1080,'30/1',900,900)
assert float(v['duration'])==30 and out.stat().st_size<50_000_000
with (ed/'decode.log').open('wb') as log:subprocess.run([str(bin/'ffmpeg.exe'),'-v','error','-i',str(out),'-map','0:v:0','-map','0:a:0','-c:v','rawvideo','-c:a','pcm_s16le','-f','null','-'],stdout=log,stderr=subprocess.STDOUT,check=True)
assert (ed/'decode.log').stat().st_size==0
sample=sorted(set([0,45,89,90,120,149,150,165,179,180,225,269,270,300,314,315,345,389,390,410,445,458,459,470,479,480,505,524,525,545,569,570,600,644,645,660,719,720,745,764,765,785,809,810,855,899]))
for f in sample:subprocess.run([str(bin/'ffmpeg.exe'),'-v','error','-y','-ss',str(f/30),'-i',str(out),'-frames:v','1',str(frames/f'f{f:03}.jpg')],check=True)
contact=Image.new('RGB',(1920,1520),'#ddd');draw=ImageDraw.Draw(contact)
for i,f in enumerate([45,120,225,300,345,445,470,545,600,660,785,855]):
 im=Image.open(frames/f'f{f:03}.jpg');im.thumbnail((640,360));x=i%3*640;y=i//3*380;contact.paste(im,(x,y));draw.text((x+10,y+362),f'{f/30:.2f}s / frame{f}',fill='black')
contact.save(ed/'final_contact.jpg')
r={'status':'technical_pass','duration':probe['format']['duration'],'video_duration':v['duration'],'resolution':[1920,1080],'fps':30,'frames':900,'nb_read_frames':900,'audio_codec':a['codec_name'],'bytes':out.stat().st_size,'under50MB':True,'decode_errors':0,'sampled_frames':sample,'continuous_playback':False,'actual_listening':False,'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}
(ed/'technical_verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(r))
