from pathlib import Path
import json,hashlib,subprocess,time
HERE=Path(__file__).resolve().parent;EP=HERE.parents[2];ROOT=EP.parents[2]
OUT=EP/'outputs/jun-quality-v2/main'
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=OUT/'affordable_home_price_jun_quality_v2.mp4';target=OUT/'affordable_home_price_jun_quality_v3.mp4'
patch=HERE/'patch-S18/S18_corrected_v1.mp4'
audio=EP/'outputs/jun-user-script-v1/full-film-v1/affordable_price_jun_user_script_v2.mp4'
assert load(HERE/'render_receipt.json')['exit_code']==0
p=load(HERE/'patch-S18/receipt.json');assert p['exit_code']==0
assert sha(patch)==p['patch_sha256']
assert not target.exists()
f0=p['frame_start'];f1=f0+p['frame_count']
filters=f'[0:v]split=2[a][b];[a]trim=end_frame={f0},setpts=PTS-STARTPTS[first];[b]trim=start_frame={f1},setpts=PTS-STARTPTS[last];[1:v]trim=end_frame={p["frame_count"]},setpts=PTS-STARTPTS[patch];[first][patch][last]concat=n=3:v=1:a=0,setsar=1[v]'
FF=ROOT/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
cmd=[str(FF),'-v','error','-n','-i',str(source),'-i',str(patch),'-i',str(audio),'-filter_complex',filters,'-map','[v]','-map','2:a:0','-c:v','h264_nvenc','-preset','p5','-rc','constqp','-qp','14','-pix_fmt','yuv420p','-r','30','-c:a','copy','-t','714.8','-movflags','+faststart',str(target)]
started=time.time();r=subprocess.run(cmd,capture_output=True);(HERE/'patch-S18/concat.log').write_bytes(r.stderr)
record={'status':'corrected' if r.returncode==0 else 'failed','exit_code':r.returncode,'command':cmd,'elapsed_s':time.time()-started,'issue_id':'JQV2-N01','patch_frame_start':f0,'patch_frame_end_exclusive':f1,'patch_frames':p['frame_count'],'rendered_source_sha256':sha(source),'patch_sha256':sha(patch),'corrected_S18_source_sha256':p['corrected_source_sha256'],'audio_source_sha256':sha(audio),'audio_mode':'AAC stream copy from approved baseline; no speech edits or regeneration','final_video':str(target)}
if target.exists():record['final_sha256']=sha(target)
(HERE/'patch-S18/final_correction_receipt.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in record.items() if k!='command'}));raise SystemExit(r.returncode)
