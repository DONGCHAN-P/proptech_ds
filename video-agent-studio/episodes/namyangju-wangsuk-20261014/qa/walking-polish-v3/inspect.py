import pathlib,json,subprocess,hashlib
from PIL import Image,ImageDraw
p=pathlib.Path(__file__).parent;e=p.parents[1];out=p/'frames';out.mkdir(exist_ok=True)
ff=pathlib.Path('C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin/ffmpeg.exe')
v=e/'outputs/rail-route-proof-v3/namyangju_rail-route-proof_v3.mp4'
meta=json.loads(subprocess.check_output([str(ff.with_name('ffprobe.exe')),'-v','error','-show_streams','-show_format','-of','json',str(v)]))
times=[31.5,31.65,32.7,33,33.2,36.7,37,37.15,38.2,38.4,68,68.15,69.2,69.4,52]
for i,t in enumerate(times):subprocess.run([str(ff),'-v','error','-y','-ss',str(t),'-i',str(v),'-frames:v','1',str(out/f'{i:02}.png')],check=True)
for g in range(2):
 b=Image.new('RGB',(1440,1280),'white');d=ImageDraw.Draw(b)
 for j,t in enumerate(times[g*8:g*8+8]):
  a=Image.open(out/f'{g*8+j:02}.png');a.thumbnail((720,405));x=j%2*720;y=j//2*320;a.thumbnail((560,300));b.paste(a,(x,y+20));d.text((x,y),f'{t}s',fill='black')
 b.save(out/f'sheet{g}.jpg')
(p/'technical_and_samples.json').write_text(json.dumps({'sha256':hashlib.sha256(v.read_bytes()).hexdigest(),'metadata':meta,'sample_times_s':times,'actual_listening':False,'continuous_playback':False},ensure_ascii=False,indent=2),encoding='utf-8')
print(meta['format']['duration'],meta['format']['size'])
