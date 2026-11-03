import pathlib,json,subprocess,hashlib
from PIL import Image,ImageDraw
root=pathlib.Path(__file__).resolve().parent.parent
out=root/'qa/video_v1';out.mkdir(exist_ok=True)
ff=pathlib.Path('C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin/ffmpeg.exe')
video=root/'editor/render_v1/namyangju-wangsuk_v1.mp4'
probe=json.loads(subprocess.check_output([str(ff.with_name('ffprobe.exe')),'-v','error','-show_streams','-show_format','-of','json',str(video)]))
(out/'ffprobe.json').write_text(json.dumps(probe,indent=2),encoding='utf-8')
sha=hashlib.sha256(video.read_bytes()).hexdigest()
decoded=subprocess.run([str(ff),'-v','error','-i',str(video),'-f','null','-'],capture_output=True,text=True)
(out/'decode.json').write_text(json.dumps({'sha256':sha,'size':video.stat().st_size,'returncode':decoded.returncode,'stderr':decoded.stderr,'continuous_playback':False,'listening':False},indent=2),encoding='utf-8')
timing=json.loads((root/'editor/render_v1/timing_actual.json').read_text(encoding='utf-8'))
captions=json.loads((root/'editor/render_v1/caption_estimates.json').read_text(encoding='utf-8'))
samples=[]
for scene in timing:
 sid=scene['scene_id'];start=scene['start_s'];dur=scene['end_s']-start
 samples += [(sid+'_head',start+.2),(sid+'_mid',start+dur*.5),(sid+'_tail',scene['end_s']-.2)]
 longest=max(captions[sid],key=lambda c:len(c['text']))
 samples.append((sid+'_longcaption',start+(longest['start_s']+longest['end_s'])/2))
 if sid=='S003':samples += [(sid+'_map1',start+dur*.48),(sid+'_map2',start+dur*.82)]
 if sid=='S002':samples += [(sid+'_regional',start+dur*.18)]
for name,t in samples:
 subprocess.run([str(ff),'-v','error','-y','-ss',str(t),'-i',str(video),'-frames:v','1',str(out/(name+'.png'))],check=True)
(out/'samples.json').write_text(json.dumps([{'name':n,'time_s':t}for n,t in samples],indent=2),encoding='utf-8')
for group in ('head','mid','tail','longcaption'):
 selected=[(n,t)for n,t in samples if n.endswith('_'+group)]
 board=Image.new('RGB',(1280,4*390),'white');draw=ImageDraw.Draw(board)
 for i,(name,t)in enumerate(selected):
  img=Image.open(out/(name+'.png'));img.thumbnail((640,360));x=(i%2)*640;y=(i//2)*390
  board.paste(img,(x,y+25));draw.text((x+10,y+5),f'{name} {t:.2f}s',fill='black')
 board.save(out/(group+'_sheet.jpg'))
print(json.dumps({'sha256':sha,'decode_exit':decoded.returncode,'samples':len(samples),'duration':probe['format']['duration']}))
