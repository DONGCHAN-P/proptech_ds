from pathlib import Path
import subprocess,json,hashlib
EP=Path(__file__).resolve().parents[2];E=EP/'editor/caption-station-v13';O=EP/'outputs/caption-station-v13'
B=Path('C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin');F=str(B/'ffmpeg.exe');BASE=EP/'outputs/video-review-v8/namyangju-landuse_full_v8.mp4'
def run(args):subprocess.run([F,'-v','error','-y']+args,check=True)
run(['-ss',str(15758/30),'-i',str(BASE),'-an','-frames:v','10662','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-video_track_timescale','90000',str(E/'rear_unchanged_v8.mp4')])
for name,src in [('front',O/'caption-station_v13_front.mp4'),('outro',O/'brand_outro_v13_no_caption.mp4'),('bridge',O/'caption-station_v13_bridge_video.mp4')]:run(['-i',str(src),'-map','0:v:0','-c','copy','-video_track_timescale','90000',str(E/f'{name}_video.mp4')])
parts=[E/'front_video.mp4',E/'bridge_video.mp4',E/'rear_unchanged_v8.mp4',E/'outro_video.mp4'];lengths=[15750,8,10662,300];listing=E/'concat_full.ffconcat';listing.write_text('ffconcat version 1.0\n'+''.join(f"file '{p.as_posix()}'\nduration {n/30:.9f}\n" for p,n in zip(parts,lengths)),encoding='utf-8')
target=O/'caption-station_v13_full.mp4';run(['-f','concat','-safe','0','-i',str(listing),'-i',str(BASE),'-map','0:v:0','-map','1:a:0','-c','copy','-t','890.688','-movflags','+faststart',str(target)])
probe=json.loads(subprocess.check_output([str(B/'ffprobe.exe'),'-v','error','-show_streams','-show_format','-of','json',str(target)]));assert int(next(s['nb_frames'] for s in probe['streams'] if s['codec_type']=='video'))==26720
run(['-i',str(target),'-f','null','-'])
def packets(p):return [x['data_hash'] for x in json.loads(subprocess.check_output([str(B/'ffprobe.exe'),'-v','error','-select_streams','a','-show_packets','-show_data_hash','sha256','-show_entries','packet=data_hash','-of','json',str(p)]))['packets']]
a,b=packets(BASE),packets(target);assert a==b
r={'file':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'video_frames':26720,'video_duration_s':26720/30,'probe':probe,'whole_decode_passed':True,'original_full_aac_packets_equal':True,'audio_packets_checked':len(a),'rear_content_unchanged_range_frames':[15758,26420],'bridge_hold_range_frames':[15750,15758],'no_caption_brand_ranges_frames':[[0,45],[917,1067],[26420,26720]],'front_visual_revision_range_frames':[0,15750],'rear_new_editorial_work':False,'actual_listening':False,'continuous_playback':False}
(O/'technical_full.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print(json.dumps({'sha256':r['sha256'],'frames':26720,'aac_equal':True}))
