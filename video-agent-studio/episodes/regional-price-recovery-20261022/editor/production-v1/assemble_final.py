"""Later assembly only. Guard actual Jun lock; retain approved brand frame counts.
No render is performed merely by importing this file. No provider or upload calls.
"""
import argparse, hashlib, json, math, subprocess
from pathlib import Path
ED=Path(__file__).resolve().parent;EP=ED.parent.parent;REPO=EP.parents[2];OUT=EP/'outputs/production-v1-jun'
SHA='99b40e8730ee0f8fdf74402cffbe04b5b418540344e6d2a7175e6a01c3054664'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def resolve(p):
    p=Path(p);return p if p.is_absolute() else REPO/p
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--body',required=True);ap.add_argument('--output',default=str(OUT/'previews/assembled_actual_jun_v1.mp4'));args=ap.parse_args()
    t=read(OUT/'project/timing_resolved.json');assert t['timing_locked'] is True and t['script_sha256']==SHA,'Actual approved Jun timing lock required'
    m=read(OUT/'reusable_assets/manifest.json');assets={a['asset_id']:a for a in m['assets']}
    paths=[]
    for name in ['channel_brand_intro_clean_v7','channel_brand_outro_clean_v7']:
        a=assets[name];p=resolve(a['actual_file']);assert sha(p)==a['sha256'];paths.append(p)
    ff=m['ffmpeg'];probe=m['ffprobe'];body=resolve(args.body);assert body.is_file()
    info=json.loads(subprocess.check_output([probe,'-v','error','-show_streams','-show_format','-of','json',str(body)],text=True,encoding='utf-8'))
    assert any(x['codec_type']=='audio' for x in info['streams']),'Actual narrated body must contain audio'
    end=t['last_spoken_end']+3;frames=math.ceil(end*30-1e-6);holdend=frames/30
    assert float(info['format']['duration'])<=holdend+.034,'PCM tail exceeds speech+3s: director decision required; do not trim silently'
    # Brand container lengths 5.013/10.005 are audio tails, video counts are 150/300.
    filt=f'[0:v]fps=30,trim=end_frame=150,setpts=PTS-STARTPTS,format=yuv420p[v0];[0:a]atrim=end=5,asetpts=PTS-STARTPTS[a0];[1:v]fps=30,tpad=stop_mode=clone:stop_duration=3,trim=end_frame={frames},setpts=PTS-STARTPTS,format=yuv420p[v1];[1:a]apad=whole_dur={holdend:.8f},atrim=end={holdend:.8f},asetpts=PTS-STARTPTS[a1];[2:v]fps=30,trim=end_frame=300,setpts=PTS-STARTPTS,format=yuv420p[v2];[2:a]atrim=end=10,asetpts=PTS-STARTPTS[a2];[v0][a0][v1][a1][v2][a2]concat=n=3:v=1:a=1[v][a]'
    dest=Path(args.output).resolve();assert dest.is_relative_to(OUT/'previews'),'Output must stay in owned previews'
    assert not dest.exists(),'Choose a new version; preserve existing render'
    cmd=[ff,'-y','-i',str(paths[0]),'-i',str(body),'-i',str(paths[1]),'-filter_complex',filt,'-map','[v]','-map','[a]','-c:v','libx264','-crf','16','-preset','medium','-c:a','aac','-b:a','192k','-movflags','+faststart',str(dest)]
    record={'status':'prepared','command':cmd,'timing_sha256':sha(OUT/'project/timing_resolved.json'),'body_sha256':sha(body),'intro_frames':150,'outro_frames':300,'last_spoken_end':t['last_spoken_end'],'outro_final_start':5+holdend,'rounding_gap_seconds':holdend-t['last_spoken_end'],'bgm_body_mix':'not added here; director must supply approved mixed body and verify carve/listening before release'}
    log=OUT/'checks/assembly_receipt.json';log.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    proc=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace');(OUT/'checks/assembly.log').write_text(proc.stderr,encoding='utf-8');assert proc.returncode==0
    record.update(status='rendered_not_release_approved',output_sha256=sha(dest));log.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__':main()
