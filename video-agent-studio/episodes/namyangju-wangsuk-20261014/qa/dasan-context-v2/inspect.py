import pathlib,json,subprocess,hashlib
from PIL import Image,ImageDraw,ImageChops,ImageStat
r=pathlib.Path(__file__).resolve().parents[2];out=r/'qa/dasan-context-v2/frames';out.mkdir(exist_ok=True)
ff=pathlib.Path('C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin/ffmpeg.exe')
v=r/'outputs/rail-route-proof-v2/namyangju_rail-route-proof_v2.mp4'
meta=json.loads(subprocess.check_output([str(ff.with_name('ffprobe.exe')),'-v','error','-show_streams','-show_format','-of','json',str(v)]))
times=[40.2,40.4,41,46,52,60,60.9,61.1,23,68]
for i,t in enumerate(times):subprocess.run([str(ff),'-v','error','-y','-ss',str(t),'-i',str(v),'-frames:v','1',str(out/f'{i:02}.png')],check=True)
for group in range(2):
 b=Image.new('RGB',(1280,1560),'white');dr=ImageDraw.Draw(b)
 for i,t in enumerate(times[group*8:group*8+8]):
  im=Image.open(out/f'{group*8+i:02}.png');im.thumbnail((640,360));x=i%2*640;y=i//2*390;b.paste(im,(x,y+25));dr.text((x+5,y+5),f'{t:.2f}s',fill='black')
 b.save(out/f'sheet_{group}.jpg')
comparisons=[]
for index,old in [(8,r/'qa/rail-route-proof-v1/frames/07.png'),(9,r/'qa/rail-route-proof-v1/frames/v1b_68.png')]:
 a=Image.open(out/f'{index:02}.png').convert('RGB');b=Image.open(old).convert('RGB');comparisons.append({'time_s':times[index],'mean_abs_rgb':ImageStat.Stat(ImageChops.difference(a,b)).mean,'identical_pixels':a.tobytes()==b.tobytes()})
data={'file':str(v),'sha256':hashlib.sha256(v.read_bytes()).hexdigest(),'ffprobe':meta,'sample_times':times,'unchanged_frame_comparisons':comparisons,'continuous_playback':False,'actual_listening':False}
(out.parent/'technical_and_samples.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'sha256':data['sha256'],'duration':meta['format']['duration'],'size':meta['format']['size'],'unchanged':comparisons}))
