from pathlib import Path
import json,subprocess,hashlib
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent;E=P.parent.parent;O=E/'outputs/full-short-v1';B=Path('C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin');v=O/'capital_10eok_2006-2026_v1.mp4';timeline=json.loads((O/'timeline.json').read_text(encoding='utf8'));year_frame={}
for s in timeline['segments']:
 if s['year'] not in year_frame:year_frame[s['year']]=s['start_frame']+s['frames']//2
frames=sorted(set(year_frame.values())|{0,89,90,134,135,989,990,1109,1110,1199});expr='+'.join(f'eq(n\\,{n})' for n in frames);subprocess.run([str(B/'ffmpeg.exe'),'-v','error','-y','-i',str(v),'-vf','select='+expr,'-fps_mode','vfr','-frames:v',str(len(frames)),str(O/'encoded_%03d.png')],check=True);files={f:O/f'encoded_{i:03d}.png' for i,f in enumerate(frames,1)}
for y in [2006,2025,2026]:
 im=Image.open(files[year_frame[y]]);im.resize((375,667),Image.Resampling.LANCZOS).save(O/f'phone375_{y}.png')
# Header-only contact sheet supports annual counter/trend inspection; map views are separate full PNGs.
canvas=Image.new('RGB',(1800,900),'#030914')
for i,y in enumerate(range(2006,2027)):
 im=Image.open(files[year_frame[y]]).crop((40,260,960,755)).resize((300,161),Image.Resampling.LANCZOS);canvas.paste(im,((i%6)*300,(i//6)*220))
canvas.save(O/'annual_encoded_headers.png');samples=[{'frame':f,'time_s':f/30,'file':files[f].name,'sha256':hashlib.sha256(files[f].read_bytes()).hexdigest()} for f in frames];(O/'encoded_samples.json').write_text(json.dumps({'video_sha256':hashlib.sha256(v.read_bytes()).hexdigest(),'year_frame':year_frame,'samples':samples,'actual_continuous_playback':False,'actual_audio_listening':False},ensure_ascii=False,indent=2),encoding='utf8')
# Scan every decoded low-resolution frame for blank header flashes while retaining intentional navy backgrounds.
cmd=[str(B/'ffmpeg.exe'),'-v','error','-i',str(v),'-vf','scale=108:192,format=gray','-f','rawvideo','-pix_fmt','gray','pipe:1'];proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE);measure=[];size=108*192
while True:
 b=proc.stdout.read(size)
 if not b:break
 assert len(b)==size
 roi=[b[yy*108+xx] for yy in range(26,75) for xx in range(4,96)];measure.append(sum(z>48 for z in roi))
err=proc.stderr.read();code=proc.wait();assert code==0 and not err and len(measure)==1200 and min(measure)>50
(O/'all_frame_header_scan.json').write_text(json.dumps({'frames_scanned':len(measure),'scale':[108,192],'roi_native_approx':[40,260,960,750],'min_bright_pixels':min(measure),'max_bright_pixels':max(measure),'blank_header_frames':[],'method':'Each decoded frame has nonempty title/year/counter ROI. This detects blank flashes, not an actual human continuous watch.','decode_exit_code':code},indent=2),encoding='utf8');print({'samples':len(samples),'years':len(year_frame),'frames_scanned':len(measure),'min_header_bright_pixels':min(measure)})
