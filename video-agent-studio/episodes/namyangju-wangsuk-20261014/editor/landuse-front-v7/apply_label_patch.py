import json,subprocess,hashlib,shutil
from pathlib import Path
E=Path(__file__).resolve().parents[2];H=Path(__file__).parent;O=E/'outputs/front-review-v7';Q=O/'technical_qa';Q.mkdir(exist_ok=True)
B=Path('C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin');ff=str(B/'ffmpeg.exe')
final=O/'namyangju-landuse_front_v7.mp4';original=H/'namyangju-landuse_front_v7_prepatch_preserved.mp4';plate=O/'source_9000.png'
assert E.resolve() in original.resolve().parents and E.resolve() in final.resolve().parents
assert plate.exists()
if not original.exists():
 assert final.exists();shutil.move(str(final),str(original))
def run(args):return subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
# Switch between half-frame timestamps, avoiding exact-frame floating point boundaries.
fc="[1:v]crop=1430:650:80:190[patch];[0:v][patch]overlay=80:190:enable='between(t,293.45,310.183333333)':shortest=1[v]"
cmd=[ff,'-hide_banner','-y','-i',str(original),'-loop','1','-framerate','30','-i',str(plate),'-filter_complex',fc,'-map','[v]','-map','0:a:0','-c:v','libx264','-crf','18','-preset','fast','-pix_fmt','yuv420p','-fps_mode','passthrough','-c:a','copy','-movflags','+faststart',str(final)]
r=run(cmd);(H/'label_patch_ffmpeg.log').write_text(r.stderr,encoding='utf-8');assert r.returncode==0,r.stderr[-2000:]
probe=run([str(B/'ffprobe.exe'),'-v','error','-show_streams','-of','json',str(final)]);assert probe.returncode==0;streams=json.loads(probe.stdout)['streams'];v=next(s for s in streams if s['codec_type']=='video');assert int(v['nb_frames'])==13087 and v['r_frame_rate']=='30/1'
def ah(p):
 r=run([ff,'-v','error','-i',str(p),'-map','0:a:0','-c','copy','-f','hash','-hash','sha256','-']);assert r.returncode==0;return r.stdout.strip()
before_audio=ah(original);after_audio=ah(final);assert before_audio==after_audio,'AAC packet hash differs'
frames=[8803,8804,9000,9305,9306]
for label,p in [('prepatch',original),('patched',final)]:
 for f in frames:
  r=run([ff,'-v','error','-ss',str(f/30),'-i',str(p),'-frames:v','1','-y',str(Q/f'{label}_{f}.png')]);assert r.returncode==0
record={'scope':'native map ROI only; no intentional header/caption/notes/audio edits','map_roi_xywh':[80,190,1430,650],'target_frames_inclusive':[8804,9305],'enable_t_half_frame_thresholds':[293.45,310.183333333],'original_preserved':str(original.relative_to(E)),'original_sha256':sha(original),'final_sha256':sha(final),'patch_still':str(plate.relative_to(E)),'patch_still_sha256':sha(plate),'video_reencoded':'libx264 CRF18 presetfast; full frame re-encoded, overlay content limited to map ROI','audio':'AAC encoded packets copied unchanged','aac_packet_hash':after_audio,'frames':13087,'fps':30,'command':cmd,'boundary_frames_extracted':frames,'independent_boundary_review':'pending'}
(O/'label_patch_manifest.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'patch':'complete','sha256':record['final_sha256'],'aac_packet_copy_identical':True,'video_frames':13087}))
