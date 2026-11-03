from pathlib import Path
import subprocess,json,hashlib
EP=Path(__file__).resolve().parents[2];E=EP/'editor/minimal-v12';O=EP/'outputs/minimal-v12'
B=Path('C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin');F=str(B/'ffmpeg.exe');BASE=EP/'outputs/map-focus-v10/map-focus_v10_front.mp4'
def run(args):subprocess.run([F,'-v','error','-y']+args,check=True)
parts=[]
for name,start,end in [('prefix',0,1898),('unchanged_jobs',2678,4950)]:
 p=E/f'{name}.mp4';run(['-ss',str(start/30),'-i',str(BASE),'-an','-frames:v',str(end-start),'-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-video_track_timescale','90000',str(p)])
for name in ['navigation','body']:
 p=E/f'{name}.mp4';run(['-i',str(O/f'minimal_v12_{name}_video.mp4'),'-map','0:v:0','-c','copy','-video_track_timescale','90000',str(p)])
parts=[E/'prefix.mp4',E/'navigation.mp4',E/'unchanged_jobs.mp4',E/'body.mp4']
lst=E/'concat.ffconcat';lst.write_text('\n'.join("file '"+str(p.resolve()).replace('\\','/')+"'" for p in parts),encoding='utf-8')
target=O/'minimal_v12_front.mp4';run(['-f','concat','-safe','0','-i',str(lst),'-i',str(BASE),'-map','0:v:0','-map','1:a:0','-c','copy','-t','525','-movflags','+faststart',str(target)])
probe=json.loads(subprocess.check_output([str(B/'ffprobe.exe'),'-v','error','-show_streams','-show_format','-of','json',str(target)]));vs=next(x for x in probe['streams'] if x['codec_type']=='video');assert int(vs['nb_frames'])==15750
run(['-i',str(target),'-f','null','-'])
sha=hashlib.sha256(target.read_bytes()).hexdigest();r={'file':str(target),'sha256':sha,'video_frames':15750,'duration_s':525,'probe':probe,'whole_decode_passed':True,'base':'map-focus_v10_front.mp4','base_sha256':hashlib.sha256(BASE.read_bytes()).hexdigest(),'changed_intervals_frames':[[1898,2678],[4950,15750]],'actual_listening':False,'continuous_playback':False}
(O/'technical_front.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print(json.dumps({'sha256':sha,'frames':15750}))
