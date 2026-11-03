import pathlib,json,subprocess,hashlib
from PIL import Image,ImageDraw
p=pathlib.Path(__file__).parent;e=p.parents[1];out=p/'proof_frames';out.mkdir(exist_ok=True);v=e/'outputs/video-review-v6/map-led_v6_intro-proof.mp4';ff=pathlib.Path('C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin/ffmpeg.exe');meta=json.loads(subprocess.check_output([str(ff.with_name('ffprobe.exe')),'-v','error','-show_streams','-show_format','-of','json',str(v)]));times=[.2,1.2,3,10,21,22.4,23,30,40,66.9,70,70.5,80,89]
for i,t in enumerate(times):subprocess.run([str(ff),'-v','error','-y','-ss',str(t),'-i',str(v),'-frames:v','1',str(out/f'{i:02}.png')],check=True)
for g in range(2):
 b=Image.new('RGB',(1280,1600),'white');d=ImageDraw.Draw(b)
 for j,t in enumerate(times[g*8:g*8+8]):
  a=Image.open(out/f'{g*8+j:02}.png');a.thumbnail((640,360));x=j%2*640;y=j//2*400;b.paste(a,(x,y+25));d.text((x,y),str(t),fill='black')
 b.save(out/f'sheet{g}.jpg')
(p/'proof_technical.json').write_text(json.dumps({'sha256':hashlib.sha256(v.read_bytes()).hexdigest(),'metadata':meta,'sample_times_s':times,'continuous_playback':False,'actual_listening':False},indent=2),encoding='utf-8');print(meta['format']['duration'])
