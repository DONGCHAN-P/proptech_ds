import pathlib,json,subprocess,hashlib,sys
from PIL import Image,ImageDraw,ImageChops,ImageStat
r=pathlib.Path(__file__).resolve().parents[2];out=r/'qa/rail-route-proof-v1/frames';out.mkdir(exist_ok=True)
ff=pathlib.Path('C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin/ffmpeg.exe')
v=r/'outputs/rail-route-proof-v1/namyangju_rail-route-proof_v1.mp4'
meta=json.loads(subprocess.check_output([str(ff.with_name('ffprobe.exe')),'-v','error','-show_streams','-show_format','-of','json',str(v)]))
times=[.2,3.5,6,9,14,16,19,23,27,29.8,30.2,31.2,32.2,33.8,34.8,36.2,37.2,38.2,39.8,40.5,50,60.8,61.2,62.2,63.8,65.2,67.2,68.2,72,79.8]
for i,t in enumerate(times):subprocess.run([str(ff),'-v','error','-y','-ss',str(t),'-i',str(v),'-frames:v','1',str(out/f'{i:02}.png')],check=True)
for group in range((len(times)+7)//8):
 b=Image.new('RGB',(1280,1560),'white');dr=ImageDraw.Draw(b)
 for i,t in enumerate(times[group*8:group*8+8]):
  im=Image.open(out/f'{group*8+i:02}.png');im.thumbnail((640,360));x=i%2*640;y=i//2*390;b.paste(im,(x,y+25));dr.text((x+5,y+5),f'{t:.2f}s',fill='black')
 b.save(out/f'sheet_{group}.jpg')
changes=[]
for ia,ib in [(2,3),(5,6),(11,12),(13,14),(15,16),(23,24),(25,26)]:
 a=Image.open(out/f'{ia:02}.png').convert('RGB').crop((80,200,1400,850));b=Image.open(out/f'{ib:02}.png').convert('RGB').crop((80,200,1400,850));changes.append({'times':[times[ia],times[ib]],'image_area_mean_abs_rgb':ImageStat.Stat(ImageChops.difference(a,b)).mean})
decode=subprocess.run([str(ff),'-v','error','-i',str(v),'-f','null','-'],capture_output=True,text=True)
data={'mp4':str(v),'sha256':hashlib.sha256(v.read_bytes()).hexdigest(),'ffprobe':meta,'sample_times':times,'motion_image_area_changes':changes,'whole_decode_exit':decode.returncode,'decode_errors':decode.stderr,'actual_listening':False,'continuous_playback':False}
(out.parent/'technical_and_samples.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'duration':meta['format']['duration'],'size':meta['format']['size'],'frames':len(times),'decode_exit':decode.returncode,'sha256':data['sha256']}))
