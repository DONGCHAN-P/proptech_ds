from pathlib import Path
import subprocess,json,hashlib
EP=Path(__file__).resolve().parents[2];E=EP/'editor/caption-station-v13';O=EP/'outputs/caption-station-v13'
B=Path('C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin');F=str(B/'ffmpeg.exe');BASE=EP/'outputs/minimal-v12/minimal_v12_front.mp4'
def run(args):subprocess.run([F,'-v','error','-y']+args,check=True)
for name,start,end in [('hook',45,917),('after_brand',1067,1898),('jobs',2678,4942)]:
 run(['-ss',str(start/30),'-i',str(BASE),'-an','-frames:v',str(end-start),'-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-video_track_timescale','90000',str(E/f'{name}.mp4')])
for name,src in [('lead',O/'caption-station_v13_lead_video.mp4'),('brand',O/'brand_intro_v13_no_caption.mp4'),('navigation',O/'caption-station_v13_navigation_video.mp4'),('body',O/'caption-station_v13_body_video.mp4')]:
 run(['-i',str(src),'-map','0:v:0','-c','copy','-video_track_timescale','90000',str(E/f'{name}.mp4')])
names=['lead','hook','brand','after_brand','navigation','jobs','body'];lengths=[45,872,150,831,780,2264,10808]
listing=E/'concat_front.ffconcat';listing.write_text('ffconcat version 1.0\n'+''.join(f"file '{(E/(name+'.mp4')).as_posix()}'\nduration {n/30:.9f}\n" for name,n in zip(names,lengths)),encoding='utf-8')
target=O/'caption-station_v13_front.mp4';run(['-f','concat','-safe','0','-i',str(listing),'-i',str(BASE),'-map','0:v:0','-map','1:a:0','-c','copy','-t','525','-movflags','+faststart',str(target)])
probe=json.loads(subprocess.check_output([str(B/'ffprobe.exe'),'-v','error','-show_streams','-show_format','-of','json',str(target)]));vs=next(x for x in probe['streams'] if x['codec_type']=='video');assert int(vs['nb_frames'])==15750
run(['-i',str(target),'-f','null','-'])
r={'file':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'video_frames':15750,'duration_s':525,'probe':probe,'whole_decode_passed':True,'brand_no_box_ranges_frames':[[0,45],[917,1067]],'removed_legacy_range':[4942,4950],'visual_cue_gap_hold':True,'actual_listening':False,'continuous_playback':False}
(O/'technical_front.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print(json.dumps({'sha256':r['sha256'],'frames':15750}))
