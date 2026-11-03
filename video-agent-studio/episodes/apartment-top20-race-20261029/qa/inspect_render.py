import hashlib,json,subprocess,wave
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
EP=Path(__file__).resolve().parents[1];ROOT=EP.parents[2]
FF=ROOT/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe';PROBE=ROOT/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe'
VIDEO=EP/'outputs/apartment_top20_race_v1.mp4';OUT=EP/'qa/encoded';OUT.mkdir(parents=True,exist_ok=True)
timing=json.loads((EP/'editor/timing.json').read_text(encoding='utf-8'));data=json.loads((EP/'research/data.json').read_text(encoding='utf-8'));duration=timing['duration']
probe=json.loads(subprocess.run([str(PROBE),'-v','error','-show_streams','-show_format','-of','json',str(VIDEO)],capture_output=True,check=True).stdout)
(OUT/'ffprobe.json').write_text(json.dumps(probe,indent=2),encoding='utf-8')
decode=subprocess.run([str(FF),'-v','error','-i',str(VIDEO),'-f','null','-'],capture_output=True)
times=[0,1.8,10,20,30,40,timing['race_end'],duration-4,duration-1/30]
proof={}
for period in ['2016Q3','2023Q3','2026Q2']:
 i=next(i for i,f in enumerate(data['frames']) if f['period']==period);seg=next(s for s in timing['segments'] if s['i']==i)
 selected=[seg['start']-1/30,seg['start']+.08,seg['start']+.17,seg['transition_end']+.033333]
 proof[period]=selected;times+=selected
times=sorted(set(round(t,6) for t in times));paths=[]
for i,t in enumerate(times):
 p=OUT/f'frame_{i:02d}_{t:.3f}.png';subprocess.run([str(FF),'-hide_banner','-loglevel','error','-y','-ss',str(t),'-i',str(VIDEO),'-frames:v','1',str(p)],check=True);paths.append(p)
cols=4;w,h=216,412;sheet=Image.new('RGB',(cols*w,h*((len(paths)+cols-1)//cols)),(220,227,229));draw=ImageDraw.Draw(sheet)
for i,(p,t) in enumerate(zip(paths,times)):
 x=i%cols*w;y=i//cols*h;sheet.paste(Image.open(p).resize((216,384),Image.Resampling.LANCZOS),(x,y+28));draw.text((x+7,y+8),f'{t:.3f}s - encoded',fill=(0,0,0))
sheet.save(OUT/'contact_mobile.png')
for period,ts in proof.items():
 s=Image.new('RGB',(864,412),(220,227,229));d=ImageDraw.Draw(s)
 for i,t in enumerate(ts):
  p=paths[times.index(round(t,6))];s.paste(Image.open(p).resize((216,384),Image.Resampling.LANCZOS),(i*216,28));d.text((i*216+5,8),f'{period}: {t:.3f}s',fill=(0,0,0))
 s.save(OUT/f'motion_{period}.png')
Image.open(paths[0]).save(EP/'outputs/cover.png')
raw=subprocess.run([str(FF),'-hide_banner','-loglevel','error','-i',str(VIDEO),'-vf','scale=108:192,format=gray','-f','rawvideo','-'],capture_output=True,check=True).stdout
gray=np.frombuffer(raw,dtype=np.uint8).reshape(-1,192,108);std=gray[:,26:136,14:84].std(axis=(1,2));delta=np.abs(np.diff(gray.astype(np.int16),axis=0)).mean(axis=(1,2))
audio=OUT/'audio_analysis.wav';subprocess.run([str(FF),'-hide_banner','-loglevel','error','-y','-i',str(VIDEO),'-vn','-ac','2','-ar','48000','-c:a','pcm_s16le',str(audio)],check=True)
with wave.open(str(audio),'rb') as f:rate=f.getframerate();samples=np.frombuffer(f.readframes(f.getnframes()),dtype='<i2').reshape(-1,2)/32768
blocks=[]
for second in range(int(duration)):
 a=samples[second*rate:min((second+1)*rate,len(samples))];blocks.append({'second':second,'rms_dbfs':float(20*np.log10(max(np.sqrt(np.mean(a*a)),1e-12)))})
v=next(s for s in probe['streams'] if s['codec_type']=='video');a=next(s for s in probe['streams'] if s['codec_type']=='audio')
verification={'file':str(VIDEO),'sha256':hashlib.sha256(VIDEO.read_bytes()).hexdigest(),'bytes':VIDEO.stat().st_size,'duration_s':float(probe['format']['duration']),'width':v['width'],'height':v['height'],'fps':v['r_frame_rate'],'frames':v.get('nb_frames'),'video_codec':v['codec_name'],'audio_codec':a['codec_name'],'sample_rate':a['sample_rate'],'channels':a['channels'],'decode_exit':decode.returncode,'decode_errors':decode.stderr.decode('utf-8','replace')[:500],'decoded_frames':len(gray),'potential_blank_frames':int((std<5).sum()),'minimum_critical_region_std':float(std.min()),'changed_frame_pairs':int((delta>.01).sum()),'audio_peak_dbfs':float(20*np.log10(max(np.max(np.abs(samples)),1e-12))),'audio_clipped_samples':int((np.abs(samples)>=.999).sum()),'audio_blocks':blocks,'sample_times':times,'motion_proof_intervals':proof,'actual_listening_performed':False,'continuous_playback_performed':False,'actual_device_playback_performed':False}
(OUT/'verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in verification.items() if k not in ['audio_blocks','sample_times','motion_proof_intervals']},ensure_ascii=False))
