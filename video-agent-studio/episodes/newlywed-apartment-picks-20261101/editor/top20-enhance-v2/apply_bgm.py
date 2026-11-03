"""Reuse untouched Thinking Music and canonically carve against each new voice.
No generation/download. Root full tracks already include exactly one end hold.
"""
from pathlib import Path
import hashlib,json,os,re,subprocess,time
H=Path(__file__).resolve().parent;E=H.parents[1];R=E.parents[2]
FF=R/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
CORE=R/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/audio-deps'
CARVE=Path('C:/Users/e2ken/.agents/skills/hyperframes-audio/scripts/carve.mjs')
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
env={**os.environ,'DO_NOT_TRACK':'1','HYPERFRAMES_NO_UPDATE_CHECK':'1','PATH':str(FF.parent)+';'+os.environ['PATH']}
manifest=read(R/'video-agent-studio/episodes/affordable-home-price-20261026/director/production-v1/media_assets.json')
ref=next(v for v in manifest['assets'] if v['asset_id']=='existing_channel_bgm');src=R/ref['path'];assert sha(src)==ref['sha256']
lock=read(E/'director/top20-enhance-v2/locked_timing.json');assert lock['timing_locked'];receipts=[]
assert read(H/'timeline_resolved.json')['duration_s']==lock['duration_s'],'Build with the enhanced timing before mixing'
for kind in ['main']:
 P=H/'main' if kind=='main' else H/'shorts'/kind;file=P/'index.html';original=file.read_text(encoding='utf-8')
 duration=lock['duration_s'] if kind=='main' else read(P/'clip_contract.json')['duration_s']
 bed=P/'assets/thinking_music_loop_raw.wav'
 # Zero the source bed around embedded-brand slots so their existing soundtrack stays singular.
 filters=['afade=t=in:st=0:d=1.0']
 if kind=='main':
  intro=next(v for v in lock['brand_visuals'] if 'intro' in v['id']);outro=next(v for v in lock['brand_visuals'] if 'outro' in v['id']);b=intro['start_s'];e=b+intro['duration_s'];o=outro['start_s']
  gain=f"if(lt(t,{b}),min(1,max(0,({b}-t)/0.15)),if(lt(t,{e}),0,min(1,max(0,(t-{e})/0.15))))"
  filters += [f"volume='{gain}':eval=frame",f'afade=t=out:st={o-1.4}:d=1.4']
 else:filters += [f'afade=t=out:st={duration-1.0}:d=1.0']
 command=[str(FF),'-v','error','-y','-stream_loop','-1','-i',str(src),'-t',str(duration),'-af',','.join(filters),'-ar','48000','-ac','2','-c:a','pcm_s16le',str(bed)]
 rr=subprocess.run(command,capture_output=True,env=env);assert rr.returncode==0,rr.stderr.decode('utf-8','replace')
 # Replace our own previous bed if rerun. Effects are derived afresh from this voice.
 original=re.sub(r'<audio\b[^>]*id="channel-bgm"[^>]*></audio>','',original)
 element=f'<audio id="channel-bgm" class="clip" src="assets/thinking_music_loop_raw.wav" data-start="0" data-duration="{duration}" data-volume="0.045" data-track-index="5" data-track-kind="music"></audio>'
 original=original.replace('</div><script>window.__timelines',element+'</div><script>window.__timelines')
 file.write_text(original,encoding='utf-8')
 log=H/'evidence'/f'canonical-carve-{kind}.log';cmd=['node',str(CARVE),'--comp',str(file),'--core',str(CORE),'--bed','channel-bgm','--voice','main-narration','--strength','0.8']
 start=time.time();r=subprocess.run(cmd,capture_output=True,env=env,cwd=P);log.write_bytes(r.stdout);Path(str(log)+'.stderr.log').write_bytes(r.stderr)
 if r.returncode:
  file.write_text(re.sub(r'<audio\b[^>]*id="channel-bgm"[^>]*></audio>','',original),encoding='utf-8')
  raise RuntimeError(f'canonical carve {kind} failed: {r.stderr.decode("utf-8","replace")[-1500:]}')
 cooked=file.read_text(encoding='utf-8');assert 'data-fx-carve=' in cooked and 'data-fx-chain=' in cooked and 'data-automation=' in cooked
 receipts.append({'target':kind,'canonical_script':str(CARVE),'script_sha256':sha(CARVE),'core_dir':str(CORE),'core_package':read(CORE/'node_modules/@hyperframes/core/package.json')['version'],'voice_sha256':sha(P/'assets/narration.wav'),'music_source_sha256':sha(src),'music_bed_sha256':sha(bed),'render_html_sha256':sha(file),'command':cmd,'preprocess_command':command,'strength':.8,'track_volume':.045,'exit_code':r.returncode,'elapsed_s':time.time()-start,'log':str(log),'actual_listening':False})
 print(json.dumps({'target':kind,'canonical_carve':'applied','elapsed_s':round(time.time()-start,2)}),flush=True)
save(H/'audio_carve_receipt.json',receipts);save(H/'music_credit.json',ref['license'])
issue=H/'issue_A001_canonical_carve.json'
if issue.exists():
 j=read(issue);j.update(status='resolved',resolution='canonical script succeeded on enhanced main using existing core; no new install/API',evidence='audio_carve_receipt.json');save(issue,j)
