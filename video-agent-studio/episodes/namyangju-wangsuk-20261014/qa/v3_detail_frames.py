import pathlib,json,subprocess
from PIL import Image,ImageDraw
r=pathlib.Path(__file__).resolve().parent.parent;repo=r.parents[2];out=r/'qa/quality_v3_details';out.mkdir(exist_ok=True)
ff='C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin/ffmpeg.exe'
v=r/'editor/render_v3/namyangju-wangsuk_v3.mp4';d=json.loads((repo/'video/src/namyangju-v2/project.json').read_text(encoding='utf-8'))
samples=[]
for c in d['chapters'][1:]:
 t=c['from']/30;samples += [(c['scene_id']+'_before',t-.1),(c['scene_id']+'_after',t+.1)]
for c in d['chapters']:
 cap=max(d['captions'][c['scene_id']],key=lambda x:len(x['text']));samples.append((c['scene_id']+'_max_caption',c['start_s']+(cap['start_s']+cap['end_s'])/2))
s=next(x for x in d['shots'] if x['shot_id']=='V2-056')
for p in (.15,.5,.85):samples.append((f'supply_{p}',(s['from']+s['frames']*p)/30))
for name,t in samples:subprocess.run([ff,'-v','error','-y','-ss',str(t),'-i',str(v),'-frames:v','1',str(out/(name+'.png'))],check=True)
for group in range((len(samples)+7)//8):
 b=Image.new('RGB',(1280,1560),'white');dr=ImageDraw.Draw(b)
 for i,(n,t)in enumerate(samples[group*8:group*8+8]):
  im=Image.open(out/(n+'.png'));im.thumbnail((640,360));x=i%2*640;y=i//2*390;b.paste(im,(x,y+25));dr.text((x+5,y+5),f'{n} {t:.2f}s',fill='black')
 b.save(out/f'details_{group}.jpg')
(out/'coverage.json').write_text(json.dumps([{'name':n,'time_s':t}for n,t in samples]),encoding='utf-8')
print(len(samples))
