import pathlib,json,subprocess,hashlib,sys
from PIL import Image,ImageDraw
p=pathlib.Path(__file__).parent;e=p.parents[1];v=pathlib.Path(sys.argv[1]);out=p/'full_frames';out.mkdir(exist_ok=True);pr=json.loads(pathlib.Path('video/src/namyangju-map-led-v6/project.json').read_text(encoding='utf-8'));ff=pathlib.Path('C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin/ffmpeg.exe');meta=json.loads(subprocess.check_output([str(ff.with_name('ffprobe.exe')),'-v','error','-show_streams','-show_format','-of','json',str(v)]));samples=[]
for shot in pr['scenes']:samples.append({'tag':shot['shot_id'],'frame':shot['from_frame']+shot['duration_frames']//2,'basis':'shot_midpoint'})
extra=[('rail_final',7160),('outsideprice',18850),('outsidegyosan',19800),('B17',21750),('A3',24300),('tailvoice_end',26020),('tailnear_end',26285)]
for n in pr['narration']:
 if n['scene_id'] in ['M001','M003','M007B','M008','M009']:
  for delta in [-2,2]:extra.append((n['scene_id']+f'_boundary{delta}',n['from_frame']+delta))
long=[]
for n in pr['narration']:
 for c in pr['captions'][n['scene_id']]:
  long.append((max(map(len,c['lines'])),n['from_frame']+(c['start_frame']+c['end_frame'])//2,c['id'],c['lines']))
  joined=''.join(c['lines'])
  for phrase in ['8만 114세대','4억 9천304만 원','7억 7천만 원','2029년 3월']:
   if phrase in joined and not any(tag=='quantity_'+phrase for tag,fr in extra):extra.append(('quantity_'+phrase,n['from_frame']+(c['start_frame']+c['end_frame'])//2))
for _,frame,cid,lines in sorted(long,reverse=True)[:8]:extra.append((cid,frame))
for tag,frame in extra:samples.append({'tag':tag,'frame':frame,'basis':'boundary/numeric-long/fixed-check'})
for i,s in enumerate(samples):
 name=f'{i:02}_{s["tag"]}.png';s['file']=name;subprocess.run([str(ff),'-v','error','-y','-ss',str(s['frame']/30),'-i',str(v),'-frames:v','1',str(out/name)],check=True)
for g in range((len(samples)+7)//8):
 b=Image.new('RGB',(1280,1560),'white');d=ImageDraw.Draw(b)
 for j,s in enumerate(samples[g*8:g*8+8]):
  a=Image.open(out/s['file']);a.thumbnail((640,360));x=j%2*640;y=j//2*390;b.paste(a,(x,y+25));d.text((x,y),f'{s["tag"]} @ {s["frame"]/30:.3f}s',fill='black')
 b.save(out/f'board_{g:02}.jpg')
r={'file':str(v),'sha256':hashlib.sha256(v.read_bytes()).hexdigest(),'metadata':meta,'samples':samples,'actual_listening':False,'continuous_playback':False,'longest_caption_samples':sorted(long,reverse=True)[:8]};(p/'full_technical_and_samples.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print(len(samples),r['sha256'],meta['format']['duration'])
