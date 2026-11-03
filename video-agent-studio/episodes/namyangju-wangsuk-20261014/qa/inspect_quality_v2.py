import pathlib,sys,json,subprocess,hashlib
from PIL import Image,ImageDraw,ImageChops,ImageStat
r=pathlib.Path(__file__).resolve().parent.parent
repo=r.parents[2]
video=pathlib.Path(sys.argv[1]);scope=sys.argv[2] if len(sys.argv)>2 else 'proof'
out=r/'qa'/('quality_'+scope+'_v2');out.mkdir(exist_ok=True)
ff=pathlib.Path('C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin/ffmpeg.exe')
meta=json.loads(subprocess.check_output([str(ff.with_name('ffprobe.exe')),'-v','error','-show_streams','-show_format','-of','json',str(video)]))
duration=float(meta['format']['duration']);project=json.loads((repo/'video/src/namyangju-v2/project.json').read_text(encoding='utf-8'))
samples=[];motions=[]
def extract(name,t):
 p=out/(name+'.png');subprocess.run([str(ff),'-v','error','-y','-ss',str(t),'-i',str(video),'-frames:v','1',str(p)],check=True);return p
for shot in project['shots']:
 start=shot['from']/30;end=(shot['from']+shot['frames'])/30
 if start>=duration-.05:continue
 end=min(end,duration-.06);t=start+(end-start)*.5
 p=extract(shot['shot_id']+'_mid',t);samples.append({'shot_id':shot['shot_id'],'type':shot['type'],'asset_request':shot['asset_request'],'time_s':t,'purpose':shot['purpose'],'file':str(p.relative_to(r))})
 if end-start>2:
  ta=start+.1;tb=min(start+1.5,end-.1)
  pa=extract(shot['shot_id']+'_a',ta);pb=extract(shot['shot_id']+'_b',tb)
  a=Image.open(pa).convert('RGB').crop((96,190,1824,825));b=Image.open(pb).convert('RGB').crop((96,190,1824,825))
  diff=ImageChops.difference(a,b);motions.append({'shot_id':shot['shot_id'],'times':[ta,tb],'image_area_mean_abs_rgb':ImageStat.Stat(diff).mean,'region':'x96..1824 y190..825 excludes caption and topheader','interpretation':'difference evidence only; semantic/functional motion requires visual review'})
for group in range((len(samples)+7)//8):
 board=Image.new('RGB',(1280,1560),'white');draw=ImageDraw.Draw(board)
 for i,s in enumerate(samples[group*8:group*8+8]):
  im=Image.open(r/s['file']);im.thumbnail((640,360));x=i%2*640;y=i//2*390;board.paste(im,(x,y+25));draw.text((x+5,y+5),f"{s['shot_id']} {s['type']} {s['time_s']:.2f}s",fill='black')
 board.save(out/f'shots_{group}.jpg')
(out/'inspection_data.json').write_text(json.dumps({'video':str(video),'sha256':hashlib.sha256(video.read_bytes()).hexdigest(),'ffprobe':meta,'samples':samples,'motion_evidence':motions,'actual_listening':False,'continuous_playback':False},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'scope':scope,'duration':duration,'shots':len(samples),'motion_pairs':len(motions)}))
