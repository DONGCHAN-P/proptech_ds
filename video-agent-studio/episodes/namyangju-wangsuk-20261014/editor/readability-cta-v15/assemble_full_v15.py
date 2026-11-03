from pathlib import Path
import subprocess,json,hashlib
EP=Path(__file__).resolve().parents[2];E=EP/'editor/readability-cta-v15';O=EP/'outputs/readability-cta-v15';V14=EP/'outputs/locator-timeline-v14';B=Path('C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin');F=str(B/'ffmpeg.exe');P=str(B/'ffprobe.exe');BASE=V14/'namyangju_locator_timeline_full_v14.mp4'
def run(args):subprocess.run([F,'-v','error','-y']+args,check=True)
def hashes(p):return [x['data_hash'] for x in json.loads(subprocess.check_output([P,'-v','error','-select_streams','v:0','-show_packets','-show_data_hash','sha256','-show_entries','packet=data_hash','-of','json',str(p)]))['packets']]
base_hashes=hashes(BASE);reuse=[];preserved=[]
for name,start,end,source in [('unchanged_lead',0,2407,EP/'editor/locator-timeline-v14/unchanged_lead_2407f.mp4'),('unchanged_price',15758,18648,V14/'region_prices_v14_M007.mp4')]:
 target=E/(name+'.mp4');same=source.exists() and hashes(source)==base_hashes[start:end]
 if same:run(['-i',str(source),'-map','0:v:0','-c','copy','-video_track_timescale','90000',str(target)])
 else:run(['-ss',str(start/30),'-i',str(BASE),'-an','-frames:v',str(end-start),'-c:v','libx264','-crf','18','-preset','fast','-pix_fmt','yuv420p',str(target)])
 reuse.append({'range':[start,end],'video_payload_exact_reused':same,'source':str(source)});preserved.append(target)
segments=[(preserved[0],2407),(O/'JobsDatesV14_video.mp4',2535),(O/'RailDatesV14_video.mp4',3248),(O/'detail_v15_video.mp4',7568),(preserved[1],2890),(O/'outside_v15_video.mp4',2988),(O/'closing_v15_video.mp4',5717),(O/'CTA_v15_video.mp4',306),(EP/'outputs/caption-station-v13/brand_outro_v13_no_caption.mp4',300)]
assert sum(n for p,n in segments)==27959
normalized=[]
for i,(src,n) in enumerate(segments):
 dst=E/f'full_segment_{i}.mp4';run(['-i',str(src),'-map','0:v:0','-c','copy','-video_track_timescale','90000',str(dst)]);normalized.append((dst,n))
listing=E/'full_v15_concat.ffconcat';listing.write_text('ffconcat version 1.0\n'+''.join(f"file '{p.as_posix()}'\nduration {n/30:.9f}\n" for p,n in normalized),encoding='utf-8')
target=O/'namyangju_readability_cta_full_v15.mp4';run(['-f','concat','-safe','0','-i',str(listing),'-i',str(O/'full_v15_audio.m4a'),'-map','0:v:0','-map','1:a:0','-c','copy','-t',str(27959/30),'-movflags','+faststart',str(target)])
probe=json.loads(subprocess.check_output([P,'-v','error','-show_streams','-show_format','-of','json',str(target)]));v=next(x for x in probe['streams'] if x['codec_type']=='video');assert int(v['nb_frames'])==27959
run(['-i',str(target),'-f','null','-'])
boundaries=[2407,4942,8190,15758,18648,21636,27353,27659];frames=sorted({0,44,45,916,917,1066,1067,2640,4950,5640,5641,5642,5643,24030,27569,27576,27577,27658,27958,*[b+d for b in boundaries for d in [-2,-1,0,1,2]],*[27353+f for f in [49,50,55,56,68,180,223,224,305]]})
expr='+'.join(f'eq(n\\,{f})' for f in frames);run(['-i',str(target),'-vf','select='+expr,'-vsync','0',str(O/'selected_full_%03d.png')])
for i,f in enumerate(frames,1):(O/f'selected_full_{i:03}.png').replace(O/f'actual_full_{f}.png')
audio=subprocess.run([F,'-hide_banner','-i',str(target),'-vn','-af','astats=metadata=0:reset=0','-f','null','-'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',errors='replace');assert audio.returncode==0;(O/'final_audio_astats.txt').write_text(audio.stderr,encoding='utf-8')
r={'file':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'video_frames':27959,'duration_s':27959/30,'whole_decode_passed':True,'probe':probe,'assembly_boundaries':boundaries,'original_video_reuse':reuse,'caption_count':305,'original_301_captions_unchanged':True,'new_CTA_captions':4,'CTA_frame_range':[27353,27659],'provider_last_spoken_end_frame':27569,'hold_to_outro_frames':90,'outro_frame_range':[27659,27959],'captionbox_excluded_ranges':[[0,45],[917,1067],[27577,27959]],'actual_frames':frames,'actual_listening':False,'continuous_playback':False,'audio':'canonical v14 decoded PCM0..27353 exactly reused; M010 full7.44s plus2.76s tail and existing10s brand; finalAAC reencoded'}
(O/'technical_full_v15.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print(json.dumps({k:r[k] for k in ['file','sha256','video_frames']}))
