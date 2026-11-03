from pathlib import Path
import subprocess,json,hashlib
EP=Path(__file__).resolve().parents[2];E=EP/'editor/locator-timeline-v14';O=EP/'outputs/locator-timeline-v14';ROOT=EP.parents[2]
B=Path('C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin');F=str(B/'ffmpeg.exe');P=str(B/'ffprobe.exe')
def run(a):subprocess.run([F,'-v','error','-y']+a,check=True)
segments=[(O/'namyangju_v14_review_00-12m01s.mp4',21636),(O/'new_closing_v14_video.mp4',5717),(EP/'outputs/caption-station-v13/brand_outro_v13_no_caption.mp4',300)]
normalized=[]
for i,(src,n) in enumerate(segments):
 target=E/f'full_segment_{i}.mp4';run(['-i',str(src),'-map','0:v:0','-c','copy','-video_track_timescale','90000',str(target)]);normalized.append((target,n))
listing=E/'full_concat.ffconcat';listing.write_text('ffconcat version 1.0\n'+''.join(f"file '{p.as_posix()}'\nduration {n/30:.9f}\n" for p,n in normalized),encoding='utf-8')
target=O/'namyangju_locator_timeline_full_v14.mp4';run(['-f','concat','-safe','0','-i',str(listing),'-i',str(O/'full_v14_audio.m4a'),'-map','0:v:0','-map','1:a:0','-c','copy','-t',str(27653/30),'-movflags','+faststart',str(target)])
probe=json.loads(subprocess.check_output([P,'-v','error','-show_streams','-show_format','-of','json',str(target)]));vs=next(s for s in probe['streams'] if s['codec_type']=='video');assert int(vs['nb_frames'])==27653
run(['-i',str(target),'-f','null','-'])
shots=json.loads((O/'closing_shot_manifest.json').read_text(encoding='utf-8'));boundaries=[21636,27353]+[s['from_frame'] for s in shots]
frames=sorted({0,44,45,916,917,1066,1067,27652,*[n+d for n in boundaries for d in [-2,-1,0,1,2] if 0<=n+d<27653],*[s['from_frame']+s['duration_frames']//2 for s in shots]})
select='+'.join(f'eq(n\\,{f})' for f in frames)
run(['-i',str(target),'-vf','select='+select,'-vsync','0',str(O/'full_selected_%03d.png')])
for i,f in enumerate(frames,1):(O/f'full_selected_{i:03}.png').replace(O/f'actual_full_{f}.png')
audio=subprocess.run([F,'-hide_banner','-i',str(target),'-vn','-af','astats=metadata=0:reset=0','-f','null','-'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',errors='replace');assert audio.returncode==0
(O/'final_audio_astats.txt').write_text(audio.stderr,encoding='utf-8')
r={'file':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'video_frames':27653,'duration_s':27653/30,'whole_decode_passed':True,'probe':probe,'closing_boundaries_frames':boundaries,'actual_boundary_frames':frames,'caption_count':301,'captionbox_excluded_ranges':[[0,45],[917,1067],[27353,27653]],'prefix_content_preserved_frames':[0,21636],'audio':'original prefix PCM preserved exactly; new M008/M009; existing brand outro; final AAC reencoded','actual_listening':False,'continuous_playback':False}
(O/'technical_full_v14.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print(json.dumps({k:r[k] for k in ['file','sha256','video_frames']}))
