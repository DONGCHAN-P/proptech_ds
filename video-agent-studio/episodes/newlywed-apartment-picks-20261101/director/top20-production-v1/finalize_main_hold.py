"""Hold the final narrated visual during E001; copy audio without re-encoding it."""
from pathlib import Path
import hashlib,json,math,subprocess

ROOT=Path(__file__).resolve().parents[5]
EP=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
H=EP/'editor/top20-production-v1'
FF=ROOT/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
FP=ROOT/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def probe(p):
    q=subprocess.run([str(FP),'-v','error','-show_streams','-show_format','-of','json',str(p)],capture_output=True,check=True)
    return json.loads(q.stdout)
def audio_hash(p):
    q=subprocess.run([str(FF),'-v','error','-i',str(p),'-map','0:a:0','-vn','-c:a','copy','-f','adts','pipe:1'],capture_output=True,check=True)
    return hashlib.sha256(q.stdout).hexdigest()

def main():
    source_receipt=H/'render_receipt_main_v3.json';r=read(source_receipt)
    assert r.get('full_decode_passed') and r.get('output_sha256')
    src=Path(r['output']);assert sha(src)==r['output_sha256']
    dst=src.with_name('top20_main_free_v5.mp4');assert not dst.exists()
    t=read(HERE/'locked_timing.json');scene=next(s for s in t['scenes'] if s['scene_id']=='E001')
    first=math.ceil(scene['start_s']*30-1e-7);end=math.ceil(scene['end_s']*30-1e-7);hold=end-first
    assert 0<hold<120
    # The held frame is the last C001 frame, after speech, with its viewer-facing title.
    graph=(f'[0:v]split=3[a][b][c];[a]trim=end_frame={first},setpts=PTS-STARTPTS[pre];'
      f'[b]trim=start_frame={first-1}:end_frame={first},setpts=PTS-STARTPTS,tpad=stop={hold-1}:stop_mode=clone,setpts=N/(30*TB)[hold];'
      f'[c]trim=start_frame={end},setpts=PTS-STARTPTS[post];[pre][hold][post]concat=n=3:v=1:a=0[video]')
    cmd=[str(FF),'-hide_banner','-loglevel','error','-i',str(src),'-filter_complex',graph,'-map','[video]','-map','0:a:0',
      '-c:v','libx264','-crf','14','-preset','fast','-threads','4','-pix_fmt','yuv420p','-r','30','-fps_mode','cfr','-c:a','copy','-movflags','+faststart',str(dst)]
    log=HERE/'evidence/finalize-main-hold.log';log.parent.mkdir(exist_ok=True)
    save(HERE/'main_hold_plan.json',{'input':str(src),'input_sha256':sha(src),'output':str(dst),'freeze_source_frame':first-1,
      'replace_start_frame':first,'replace_end_frame_exclusive':end,'held_frames':hold,'reason':'Continue final narrated closing state during silent hold; remove E001 production-only title',
      'audio_stream_copy':True,'speech_and_data_unchanged':True,'ffmpeg_filter':graph})
    with log.open('wb') as stream:run=subprocess.run(cmd,stdout=stream,stderr=stream)
    assert run.returncode==0,str(log)
    before,after=probe(src),probe(dst)
    bv=next(x for x in before['streams'] if x['codec_type']=='video');av=next(x for x in after['streams'] if x['codec_type']=='video')
    assert av['r_frame_rate']=='30/1' and (av['width'],av['height'])==(1920,1080)
    assert av.get('nb_frames')==bv.get('nb_frames')
    assert abs(float(after['format']['duration'])-float(before['format']['duration']))<.04
    ah=audio_hash(src);assert audio_hash(dst)==ah,'Audio payload changed unexpectedly'
    decoded=subprocess.run([str(FF),'-v','error','-xerror','-i',str(dst),'-f','null','-'],capture_output=True)
    assert decoded.returncode==0,decoded.stderr.decode(errors='replace')[-400:]
    rec={**r,'output':str(dst),'output_sha256':sha(dst),'bytes':dst.stat().st_size,'probe':after,'full_decode_passed':True,
      'status':'encoded_ready_for_independent_QA','hyperframes_base_receipt':str(source_receipt),'hyperframes_base_sha256':sha(src),
      'postprocess':'frame-accurate final-state hold during E001 only; video CRF14; audio stream copy',
      'held_frame_range':[first,end],'audio_payload_sha256':ah,'audio_payload_unchanged':True,
      'actual_listening':False,'continuous_playback':False}
    for key in ['decoded_frame_manifest','decoded_frame_count']:rec.pop(key,None)
    save(H/'render_receipt_main_v5.json',rec)
    print(json.dumps({'output':str(dst),'sha256':rec['output_sha256'],'duration_s':after['format']['duration'],'held_frames':hold,'audio_identical':True},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
