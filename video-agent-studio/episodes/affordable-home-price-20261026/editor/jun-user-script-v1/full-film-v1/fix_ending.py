"""Apply the source-QA ending-caption fix to the captured candidate.

Only the empty S31 caption zone is painted during the unvoiced hold. The AAC
stream is copied verbatim. Native graphics/audio/source alignment stay preserved.
"""
from pathlib import Path
import json,subprocess,math,hashlib,time
HERE=Path(__file__).resolve().parent;EP=HERE.parents[2];ROOT=EP.parents[2]
OUT=EP/'outputs/jun-user-script-v1/full-film-v1'
FF=ROOT/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
source=OUT/'affordable_price_jun_user_script_v1.mp4'
target=OUT/'affordable_price_jun_user_script_v2.mp4'
schedule=json.loads((HERE/'schedule.json').read_text(encoding='utf-8'))
first=math.ceil(schedule['last_speech_end']*30-1e-8)
last=round(next(p['start'] for p in schedule['placements'] if p['id']=='brand_outro')*30)
vf=f"drawbox=x=96:y=876:w=1728:h=124:color=0xf6f4ef:t=fill:enable='gte(n,{first})*lt(n,{last})'"
args=[str(FF),'-hide_banner','-loglevel','warning','-n','-i',str(source),'-vf',vf,'-map','0:v:0','-map','0:a:0','-c:v','h264_nvenc','-preset','p5','-rc','constqp','-qp','14','-profile:v','high','-pix_fmt','yuv420p','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-c:a','copy','-movflags','+faststart',str(target)]
t=time.monotonic();r=subprocess.run(args,capture_output=True)
(HERE/'ending_fix.stderr.log').write_bytes(r.stderr)
if r.returncode:
    print('Ending fix failed:',r.returncode,r.stderr.decode('utf-8','replace')[-1800:]);raise SystemExit(r.returncode)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
receipt={'issue_id':'JUS1-SRC-001','status':'ending_caption_zone_corrected_pending_encoded_QA','source':str(source),'source_sha256':sha(source),'output':str(target),'output_sha256':sha(target),'ffmpeg_sha256':sha(FF),'filter':vf,'first_affected_frame':first,'end_frame_exclusive':last,'actual_defect_interval_s':[schedule['last_speech_end'],702.0333333333333],'blank_hold_interval_s':[first/30,last/30],'audio_codec_mode':'copy','audio_reencoded':False,'whole_video_reencoded':True,'encoder':'h264_nvenc constqp14 presetp5','elapsed_s':time.monotonic()-t,'actual_listening':False,'continuous_playback':False,'argv':args}
(HERE/'ending_fix_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':receipt['status'],'seconds':receipt['elapsed_s'],'output':str(target)}))
