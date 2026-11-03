"""Assemble existing brand/music around the new silent body; no narration calls."""
from pathlib import Path
import subprocess,json,hashlib,sys
EP=Path(__file__).resolve().parents[2];ROOT=EP.parents[2];OUT=EP/'outputs/literature-visual-v1';P=OUT/'project'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
    return h.hexdigest()
M=read(OUT/'reused_assets.json');T=read(P/'timing.json');ff=M['ffmpeg'];fp=M['ffprobe'];A={a['asset_id']:a for a in M['assets']}
def probe(p):return json.loads(subprocess.check_output([fp,'-v','error','-show_streams','-show_format','-of','json',str(p)],text=True,encoding='utf8'))
body=OUT/'previews/literature_visual_body_v1.mp4';dest=OUT/'previews/literature_visual_review_v1.mp4'
assert body.exists() and not dest.exists(),'Preserve existing output; a new version is needed to replace it'
assets=[]
for name in ['channel_brand_intro_clean_v7','channel_brand_outro_clean_v7','existing_channel_bgm']:
    a=A[name];path=ROOT/a['actual_file'];assert sha(path)==a['sha256'];assets.append(path)
intro,outro,music=assets;bprobe=probe(body);bv=next(s for s in bprobe['streams'] if s['codec_type']=='video');assert (bv['width'],bv['height'],bv['avg_frame_rate'])==(1920,1080,'30/1');assert not any(s['codec_type']=='audio' for s in bprobe['streams']);assert abs(float(bv['duration'])-T['body_duration'])<.04
duration=T['body_duration'];frames=round(duration*30)
filters=(f'[0:v]fps=30,trim=end_frame=150,setpts=PTS-STARTPTS,setsar=1,format=yuv420p[v0];[1:v]fps=30,trim=end_frame={frames},setpts=PTS-STARTPTS,setsar=1,format=yuv420p[v1];[2:v]fps=30,trim=end_frame=300,setpts=PTS-STARTPTS,setsar=1,format=yuv420p[v2];'
 '[0:a]atrim=end=5,asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo[a0];'
 f'[3:a]atrim=end={duration:.6f},asetpts=PTS-STARTPTS,volume=0.20,afade=t=in:st=0:d=0.35,afade=t=out:st={duration-.75:.6f}:d=0.75,aformat=sample_rates=48000:channel_layouts=stereo[a1];'
 '[2:a]atrim=end=10,asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo[a2];[v0][a0][v1][a1][v2][a2]concat=n=3:v=1:a=1[v][a]')
cmd=[ff,'-y','-i',str(intro),'-i',str(body),'-i',str(outro),'-stream_loop','-1','-i',str(music),'-filter_complex',filters,'-map','[v]','-map','[a]','-c:v','libx264','-preset','veryfast','-crf','16','-c:a','aac','-b:a','192k','-metadata','title=논문 인용형 화면 검토본 v1','-metadata','comment=visual review only; no narration; provisional text timing; user voice hold preserved','-movflags','+faststart',str(dest)]
with (OUT/'checks/assembly.log').open('w',encoding='utf8') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
assert r.returncode==0,'See assembly.log'
final=probe(dest);v=next(s for s in final['streams'] if s['codec_type']=='video');assert abs(float(v['duration'])-T['total_duration'])<.05
receipt={'status':'assembled_pending_encoded_QA','path':dest.relative_to(ROOT).as_posix(),'sha256':sha(dest),'bytes':dest.stat().st_size,'duration':float(final['format']['duration']),'video_duration':float(v['duration']),'fps':v['avg_frame_rate'],'resolution':[v['width'],v['height']],'frames':int(v['nb_frames']),'provisional_timing':True,'timing_locked':False,'narration_present':False,'paid_generation_calls':0,'voice_generation_calls':0,'script_sha256':T['script_sha256'],'bgm_only':True,'body_bgm_gain':.2,'bgm_credit':A['existing_channel_bgm']['license'],'brand_sources':[{k:A[n][k] for k in ('actual_file','sha256')} for n in ('channel_brand_intro_clean_v7','channel_brand_outro_clean_v7')],'actual_listening':False,'continuous_playback':False,'ffprobe':final}
dump(OUT/'checks/assembly_receipt.json',receipt)
print(json.dumps({k:receipt[k] for k in ['status','path','sha256','bytes','duration','frames','narration_present']},ensure_ascii=False))
