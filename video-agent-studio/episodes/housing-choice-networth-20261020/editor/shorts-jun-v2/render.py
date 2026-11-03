"""Render checked portrait Shorts locally; external release remains main-first. No TTS."""
import argparse,hashlib,json,os,re,shutil,subprocess
from datetime import datetime,timezone
from pathlib import Path
HERE=Path(__file__).resolve().parent;EP=HERE.parents[1];ROOT=EP.parents[2]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ap=argparse.ArgumentParser();ap.add_argument('--execute',action='store_true');a=ap.parse_args()
cli=shutil.which('hyperframes.cmd');assert cli and subprocess.check_output([cli,'--version'],text=True).strip()=='0.8.181'
ffmpeg=EP/'outputs/private-production-v1/media-bin/ffmpeg.exe'
ffprobe=ROOT/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe'
assert sha(ffmpeg)=='2ce797a0f88d7f067180338fb227f7b1928ea727bd9a4d7a1d022f7c52af71a3'
checks=read(HERE/'checks/summary.json');assert checks['status']=='pass'
auth=read(EP/'director/launch-and-jun-v1/shorts_authorization.json');assert auth['new_ElevenLabs_credits_cap']==0
env=os.environ.copy();env['PATH']=str(ffmpeg.parent)+os.pathsep+str(ffprobe.parent)+os.pathsep+env['PATH'];env['DO_NOT_TRACK']='1'
commands=[]
for ident in ['funnel','analysis']:
    folder=EP/'outputs/shorts-jun-v2'/ident;dest=folder/'renders';dest.mkdir(exist_ok=True)
    video=dest/f'housing_choice_{ident}_jun_v2.mp4';timing=read(folder/'timing.json')
    checked=next(r for r in checks['shorts'] if r['id']==ident)
    bounds=read(folder/'preview/bbox_report.json')
    assert sha(folder/'index.html')==checked['html_sha256']==bounds['html_sha256']
    assert bounds['status']=='source_preview_bbox_pass' and bounds['backward_seek_pixel_identical']
    assert sha(folder/'assets/narration.wav')==timing['audio_sha256'] and timing['new_TTS_calls']==0
    raw=dest/f'housing_choice_{ident}_jun_v2_raw.mp4'
    argv=[cli,'render','.', '--fps','30','--quality','delivery','--workers','4','--browser-gpu','--output',str(raw),'--frames-cache-dir',str(dest/'frames-cache')]
    commands.append({'id':ident,'cwd':str(folder),'argv':argv,'html_sha256':checked['html_sha256'],'target':str(video),'raw':str(raw)})
(HERE/'render_commands.json').write_text(json.dumps(commands,indent=2)+'\n',encoding='utf8')
if not a.execute:
    print(json.dumps({'status':'commands_prepared','new_TTS_calls':0}));raise SystemExit(0)
amendment=read(EP/'director/launch-and-jun-v1/local_render_sequence_amendment.json')
assert amendment['local_reversible_render_may_run_while_main_review_finishes'] is True
assert amendment['external_release_order']=='main_private_replacement_verified_then_two_Shorts_private'
rows=[]
for cmd in commands:
    folder=Path(cmd['cwd']);video=Path(cmd['target']);raw=Path(cmd['raw']);dest=video.parent
    assert not video.exists() and not raw.exists(),'Do not overwrite a previous render; inspect its receipt first.'
    log=dest/'render.log'
    print('Rendering '+cmd['id'],flush=True)
    with log.open('w',encoding='utf8') as f:p=subprocess.run(cmd['argv'],cwd=folder,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=900)
    assert p.returncode==0 and raw.is_file(),f'Render failed: {log}'
    signal=subprocess.run([str(ffmpeg),'-nostdin','-hide_banner','-i',str(raw),'-vn','-af','ebur128=peak=true','-f','null','NUL'],capture_output=True,text=True,encoding='utf8',timeout=120)
    assert signal.returncode==0
    (dest/'raw_audio_signal.log').write_text(signal.stderr,encoding='utf8')
    summary=signal.stderr[signal.stderr.rfind('Summary:'):]
    integrated=float(re.search(r'I:\s*([-\d.]+) LUFS',summary).group(1));peak=float(re.search(r'Peak:\s*([-\d.]+) dBFS',summary).group(1))
    gain=min(-17.2-integrated,-1.5-peak)
    mix=[str(ffmpeg),'-nostdin','-hide_banner','-v','error','-i',str(raw),'-map','0:v:0','-map','0:a:0','-c:v','copy','-af',f'volume={gain:.4f}dB','-c:a','aac','-b:a','192k','-movflags','+faststart','-n',str(video)]
    subprocess.run(mix,check=True,capture_output=True,timeout=120)
    info=json.loads(subprocess.check_output([str(ffprobe),'-v','error','-show_format','-show_streams','-of','json',str(video)]))
    v=next(s for s in info['streams'] if s['codec_type']=='video');audio=next(s for s in info['streams'] if s['codec_type']=='audio')
    assert (v['width'],v['height'],v['r_frame_rate'],v['codec_name'])==(1080,1920,'30/1','h264')
    assert audio['codec_name']=='aac'
    timing=read(folder/'timing.json');assert abs(float(info['format']['duration'])-timing['duration_s'])<.05
    with (dest/'full_decode.log').open('w',encoding='utf8') as f:d=subprocess.run([str(ffmpeg),'-nostdin','-v','error','-i',str(video),'-map','0:v:0','-map','0:a:0','-f','null','NUL'],stdout=f,stderr=subprocess.STDOUT,timeout=150)
    assert d.returncode==0 and not (dest/'full_decode.log').read_text().strip()
    row={'id':cmd['id'],'video':video.relative_to(ROOT).as_posix(),'video_sha256':sha(video),'bytes':video.stat().st_size,'duration_s':float(info['format']['duration']),'source_html_sha256':sha(folder/'index.html'),'audio_sha256':sha(folder/'assets/narration.wav'),'subtitles':(folder/'captions.srt').relative_to(ROOT).as_posix(),'subtitles_sha256':sha(folder/'captions.srt'),'full_AV_decode':True,'probe':info,'actual_listening':False,'continuous_playback':False,'status':'rendered_technical_only_final_media_review_pending','raw_video_sha256':sha(raw),'voice_gain_db':gain,'raw_integrated_LUFS':integrated,'raw_true_peak_dBFS':peak,'music_policy':'voice_only; no BGM','normalization_video_stream_copied':True}
    (dest/'render_receipt.json').write_text(json.dumps(row,indent=2)+'\n',encoding='utf8');rows.append(row)
    print(json.dumps({k:row[k] for k in ['id','video_sha256','duration_s','status']}),flush=True)
(HERE/'render_receipt.json').write_text(json.dumps({'shorts':rows,'new_TTS_calls':0,'extra_paid_credits':0,'at_utc':datetime.now(timezone.utc).isoformat()},indent=2)+'\n',encoding='utf8')
