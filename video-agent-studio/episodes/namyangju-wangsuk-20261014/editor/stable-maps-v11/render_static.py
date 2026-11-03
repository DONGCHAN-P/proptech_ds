from pathlib import Path
import subprocess,json,hashlib,sys
ROOT=Path(__file__).resolve().parents[5]; EP=Path(__file__).resolve().parents[2]
OUT=EP/'outputs/stable-maps-v11'
BIN=Path('C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin')
BASE=EP/'outputs/video-review-v8/namyangju-landuse_full_v8.mp4'
stage=sys.argv[1] if len(sys.argv)>1 else 'rail'
start,end=(165,273) if stage=='rail' else (0,525)
schedule=[('rail',0,108)] if stage=='rail' else [('pair',58.333333,76.833333),('jobs',76.833333,164.733333),('rail',164.733333,273),('price',273,343),('life',343,525)]
args=[str(BIN/'ffmpeg.exe'),'-y','-ss',str(start),'-i',str(BASE)]
for kind,a,b in schedule:args+=['-loop','1','-i',str(OUT/f'plate_{kind}.png')]
filters=[]
for i,(_,a,b) in enumerate(schedule,1):
 filters.append(f'[{i}:v]crop=1920:920:0:0,format=yuv420p[p{i}]')
 filters.append(f'[{"0:v" if i==1 else "v"+str(i-1)}][p{i}]overlay=0:0:enable=\'gte(t,{a})*lt(t,{b})\':shortest=1[v{i}]')
target=OUT/f'stable-maps_v11_{stage}.mp4'
args+=['-filter_complex',';'.join(filters),'-map',f'[v{len(schedule)}]','-map','0:a:0','-frames:v',str((end-start)*30),'-t',str(end-start),'-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','copy','-movflags','+faststart',str(target)]
(OUT/f'render_command_{stage}.json').write_text(json.dumps(args,indent=2),encoding='utf-8')
subprocess.run(args,check=True)
probe=json.loads(subprocess.check_output([str(BIN/'ffprobe.exe'),'-v','error','-show_streams','-show_format','-of','json',str(target)]))
v=next(s for s in probe['streams'] if s['codec_type']=='video');assert int(v['nb_frames'])==(end-start)*30
subprocess.run([str(BIN/'ffmpeg.exe'),'-v','error','-i',str(target),'-f','null','-'],check=True)
sha=hashlib.sha256(target.read_bytes()).hexdigest()
(OUT/f'technical_{stage}.json').write_text(json.dumps({'sha256':sha,'original_interval_s':[start,end],'static_schedule':schedule,'probe':probe,'whole_decode_passed':True,'actual_listening':False,'continuous_playback':False},indent=2),encoding='utf-8')
print(json.dumps({'file':str(target),'sha256':sha,'whole_decode_passed':True}))
