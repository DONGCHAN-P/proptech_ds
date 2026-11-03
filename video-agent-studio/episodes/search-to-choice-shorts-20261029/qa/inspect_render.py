import argparse,hashlib,json,subprocess,wave
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
EP=Path(__file__).resolve().parents[1];ROOT=EP.parents[2]
FF=ROOT/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
PROBE=ROOT/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe'
ap=argparse.ArgumentParser();ap.add_argument('--version',default='v1');args=ap.parse_args()
VIDEO=EP/f'outputs/regional_gap_84m2_{args.version}.mp4'
OUT=EP/('qa/encoded' if args.version=='v1' else 'qa/encoded_'+args.version);OUT.mkdir(parents=True,exist_ok=True)
raw=subprocess.run([str(PROBE),'-v','error','-show_streams','-show_format','-of','json',str(VIDEO)],capture_output=True,check=True).stdout
probe=json.loads(raw);(OUT/'ffprobe.json').write_text(json.dumps(probe,indent=2),encoding='utf-8')
decode=subprocess.run([str(FF),'-v','error','-i',str(VIDEO),'-f','null','-'],capture_output=True)
times=[0,2.4,7,12,18,19,22.966667,23,23.033333,25.966667,26,29.966667]
paths=[]
for i,t in enumerate(times):
 p=OUT/f'frame_{i:02d}_{t:.3f}.png';subprocess.run([str(FF),'-hide_banner','-loglevel','error','-y','-ss',str(t),'-i',str(VIDEO),'-frames:v','1',str(p)],check=True);paths.append(p)
cols=4;w,h=216,416;sheet=Image.new('RGB',(cols*w,h*3),(220,227,229));draw=ImageDraw.Draw(sheet)
for i,(p,t) in enumerate(zip(paths,times)):
 x=i%cols*w;y=i//cols*h;im=Image.open(p).resize((216,384),Image.Resampling.LANCZOS);sheet.paste(im,(x,y+32));draw.text((x+7,y+10),f'{t:.3f}s - encoded',fill=(0,0,0))
sheet.save(OUT/'contact_mobile.png')
cover=Image.open(paths[0]);cover.save(EP/'outputs/cover.png')
# Full-frame statistical decode detects an empty plate/black flash across all 900 frames.
decoded=subprocess.run([str(FF),'-hide_banner','-loglevel','error','-i',str(VIDEO),'-vf','scale=108:192,format=gray','-f','rawvideo','-'],capture_output=True,check=True).stdout
gray=np.frombuffer(decoded,dtype=np.uint8).reshape(-1,192,108)
active_std=gray[:,26:136,14:84].std(axis=(1,2));delta=np.abs(np.diff(gray.astype(np.int16),axis=0)).mean(axis=(1,2))
audio_path=OUT/'audio_analysis.wav';subprocess.run([str(FF),'-hide_banner','-loglevel','error','-y','-i',str(VIDEO),'-vn','-ac','2','-ar','48000','-c:a','pcm_s16le',str(audio_path)],check=True)
with wave.open(str(audio_path),'rb') as f:rate=f.getframerate();samples=np.frombuffer(f.readframes(f.getnframes()),dtype='<i2').reshape(-1,2)/32768
blocks=[]
for sec in range(30):
 a=samples[sec*rate:min((sec+1)*rate,len(samples))];blocks.append({'second':sec,'rms_dbfs':float(20*np.log10(max(np.sqrt(np.mean(a*a)),1e-12)))})
result={'file':str(VIDEO),'sha256':hashlib.sha256(VIDEO.read_bytes()).hexdigest(),'bytes':VIDEO.stat().st_size,'duration_s':float(probe['format']['duration']),'video':[{k:s.get(k) for k in ['codec_name','width','height','r_frame_rate','nb_frames','sample_aspect_ratio','pix_fmt']} for s in probe['streams'] if s['codec_type']=='video'],'audio':[{k:s.get(k) for k in ['codec_name','sample_rate','channels','duration']} for s in probe['streams'] if s['codec_type']=='audio'],'decode_exit':decode.returncode,'decode_errors':decode.stderr.decode('utf-8','replace')[:500],'decoded_frames':len(gray),'min_critical_region_std':float(active_std.min()),'potential_blank_frame_count':int((active_std<5).sum()),'timelapse_nonzero_delta_frames':int((delta[72:569]>.01).sum()),'audio_peak_dbfs':float(20*np.log10(max(np.max(np.abs(samples)),1e-12))),'audio_clipped_samples':int((np.abs(samples)>=.999).sum()),'audio_blocks':blocks,'sample_times':times,'actual_listening_performed':False,'continuous_playback_performed':False,'verification_scope':'full decode/audio numerical measures + sampled encoded frames; not continuous audiovisual viewing'}
(OUT/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ['audio_blocks','sample_times']},ensure_ascii=False))
