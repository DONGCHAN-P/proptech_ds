from pathlib import Path
import subprocess,json,hashlib,sys
ROOT=Path(__file__).resolve().parents[5]
EP=Path(__file__).resolve().parents[2]
OWN=Path(__file__).resolve().parent
OUT=EP/'outputs/map-focus-v10'
BIN=Path('C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin')
FF=str(BIN/'ffmpeg.exe');FP=str(BIN/'ffprobe.exe')
BASE=ROOT/'video/public/namyangju-map-focus-v10/base_v8.mp4'
parts=[OWN/'prefix_0_165.mp4']
for i in [1,2,3]:
 src=OUT/f'map-focus_v10_{i}.mp4';assert src.exists()
 dst=OWN/f'part{i}_video_only.mp4'
 subprocess.run([FF,'-v','error','-i',str(src),'-map','0:v:0','-c:v','copy','-an','-y',str(dst)],check=True)
 parts.append(dst)
listing=OWN/'concat_video.ffconcat'
listing.write_text('ffconcat version 1.0\n'+''.join(f"file '{p.as_posix()}'\nduration {d}\n" for p,d in zip(parts,[165,108,96,156])),encoding='utf-8')
dest=OUT/'map-focus_v10_front.mp4'
subprocess.run([FF,'-v','warning','-f','concat','-safe','0','-i',str(listing),'-i',str(BASE),'-map','0:v:0','-map','1:a:0','-c','copy','-t','525','-movflags','+faststart','-y',str(dest)],check=True)
def packets(p):
 data=json.loads(subprocess.check_output([FP,'-v','error','-select_streams','a:0','-read_intervals','0%525','-show_packets','-show_entries','packet=data_hash','-show_data_hash','sha256','-of','json',str(p)]))
 return [x['data_hash'] for x in data['packets']]
a=packets(BASE);b=packets(dest)
assert b==a[:len(b)],'Final AAC packets differ from original master prefix'
record={'method':'video-only streamcopy concat of original prefix and 3 reviewed parts; original master AAC streamcopy','interval_s':[0,525],'expected_video_frames':15750,'audio_packets_identical_to_master_prefix':True,'audio_packets_checked':len(b),'source_parts':[str(p) for p in parts],'new_body_render_after_525':False,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()}
(OUT/'assembly_manifest.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
subprocess.run([sys.executable,str(OWN/'check_and_notify.py'),'front'],check=True,cwd=ROOT)
print(json.dumps({'front_complete':True,'audio_preserved':True,'sha256':record['sha256']}))
