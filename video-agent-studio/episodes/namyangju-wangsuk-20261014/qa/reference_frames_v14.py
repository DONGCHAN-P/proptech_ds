import pathlib,subprocess,json
from PIL import Image,ImageDraw
r=pathlib.Path(__file__).resolve().parent.parent
repo=r.parents[2];out=r/'qa/reference_v14';out.mkdir(exist_ok=True)
ff='C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin/ffmpeg.exe'
video=repo/'video/out/newtown-v14-release.mp4'
times=[65,145,185,198,218,250,326,545]
board=Image.new('RGB',(1280,1560),'white');draw=ImageDraw.Draw(board)
for i,t in enumerate(times):
 p=out/f'v14_{t}.png';subprocess.run([ff,'-v','error','-y','-ss',str(t),'-i',str(video),'-frames:v','1',str(p)],check=True)
 im=Image.open(p);im.thumbnail((640,360));x=i%2*640;y=i//2*390;board.paste(im,(x,y+25));draw.text((x+10,y+5),f'actual v14 {t}s',fill='black')
board.save(out/'reference_sheet.jpg')
(out/'coverage.json').write_text(json.dumps({'input':str(video),'times_seconds':times,'coverage':'sampled_frames_only_not_listening_or_continuous_playback'}),encoding='utf-8')
print('8 actual v14 frames extracted')
