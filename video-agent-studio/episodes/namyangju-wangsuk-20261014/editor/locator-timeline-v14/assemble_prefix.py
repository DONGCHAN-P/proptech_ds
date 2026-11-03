from pathlib import Path
import subprocess,json,hashlib
EP=Path(__file__).resolve().parents[2];E=EP/'editor/locator-timeline-v14';O=EP/'outputs/locator-timeline-v14'
B=Path('C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin');F=str(B/'ffmpeg.exe');P=str(B/'ffprobe.exe');base=EP/'outputs/caption-station-v13/caption-station_v13_full.mp4'
def run(a):subprocess.run([F,'-v','error','-y']+a,check=True)
prefix=E/'unchanged_lead_2407f.mp4'
run(['-i',str(base),'-an','-frames:v','2407','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-video_track_timescale','90000',str(prefix)])
segments=[(prefix,2407),(O/'JobsDatesV14_video.mp4',2535),(O/'RailDatesV14_video.mp4',3248),(O/'landuse_locator_timeline_v14_video.mp4',7568),(O/'region_prices_v14_M007.mp4',2890),(O/'OutsideDatesV14_video.mp4',2988)]
normalized=[]
for i,(src,n) in enumerate(segments):
 dst=E/f'prefix_segment_{i}.mp4';run(['-i',str(src),'-map','0:v:0','-c','copy','-video_track_timescale','90000',str(dst)]);normalized.append((dst,n))
listing=E/'prefix_concat.ffconcat';listing.write_text('ffconcat version 1.0\n'+''.join(f"file '{p.as_posix()}'\nduration {n/30:.9f}\n" for p,n in normalized),encoding='utf-8')
target=O/'namyangju_v14_review_00-12m01s.mp4'
run(['-f','concat','-safe','0','-i',str(listing),'-i',str(base),'-map','0:v:0','-map','1:a:0','-c','copy','-t','721.2','-movflags','+faststart',str(target)])
probe=json.loads(subprocess.check_output([P,'-v','error','-show_streams','-show_format','-of','json',str(target)]));v=next(x for x in probe['streams'] if x['codec_type']=='video');assert int(v['nb_frames'])==21636
run(['-i',str(target),'-f','null','-'])
for f in [0,44,45,916,917,1066,1067,2406,2407,2408,4941,4942,4943,8189,8190,8191,15757,15758,15759,18647,18648,18649,21635]:run(['-i',str(target),'-vf',f'select=eq(n\,{f})','-frames:v','1',str(O/f'actual_prefix_{f}.png')])
r={'file':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'video_frames':21636,'duration_s':721.2,'whole_decode_passed':True,'probe':probe,'assembly_boundaries_frames':[2407,4942,8190,15758,18648],'audio':'single original v13 AAC stream trimmed once at721.2; no individual clip AAC concat','scope':'review prefix only; M008/M009 new narration pending approval; no old closing delivered as final','actual_listening':False,'continuous_playback':False}
(O/'technical_prefix.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print(json.dumps({k:r[k] for k in ['file','sha256','video_frames']}))
