"""기존 Thinking Music과 canonical carve를 새 복제본에 적용합니다. 부모 실행용입니다."""
from pathlib import Path
import argparse,json,os,re,shutil,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from main_contract import H,R,read,sha,save
ap=argparse.ArgumentParser();ap.add_argument('--project',required=True);ap.add_argument('--version',required=True);a=ap.parse_args();P=Path(a.project).resolve()
if not P.is_relative_to(H/'main')or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,40}',a.version):raise ValueError('담당폴더의 새 버전을 지정하십시오.')
D=H/'main'/a.version
if D.exists():raise FileExistsError('기존 프로젝트 보존: 새 BGM 버전명을 사용하십시오.')
assert all(sha(P/v['path'])==v['sha256']for v in read(P/'source_freeze.json')['files'])
FF=R/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe';CORE=R/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/audio-deps';CARVE=Path('C:/Users/e2ken/.agents/skills/hyperframes-audio/scripts/carve.mjs')
manifest=R/'video-agent-studio/episodes/affordable-home-price-20261026/director/production-v1/media_assets.json';ref=next(v for v in read(manifest)['assets']if v['asset_id']=='existing_channel_bgm');music=R/ref['path'];assert sha(music)==ref['sha256']and CARVE.exists()
shutil.copytree(P,D,ignore=shutil.ignore_patterns('.hyperframes','.thumbnails'));T=read(D/'timeline_resolved.json');total=T['duration_s'];intro=next(v for v in T['inserts']if v['kind']=='intro');outro=next(v for v in T['inserts']if v['kind']=='outro');b=intro['start_s'];e=b+intro['duration_s'];o=outro['start_s']
bed=D/'assets/thinking_music_loop_raw.wav';gain=f'if(lt(t,{b}),min(1,max(0,({b}-t)/0.15)),if(lt(t,{e}),0,min(1,max(0,(t-{e})/0.15))))'
filters=['afade=t=in:st=0:d=1.0',f"volume='{gain}':eval=frame",f'afade=t=out:st={o-1.4}:d=1.4']
cmd=[str(FF),'-v','error','-y','-stream_loop','-1','-i',str(music),'-t',str(total),'-af',','.join(filters),'-ar','48000','-ac','2','-c:a','pcm_s16le',str(bed)];subprocess.run(cmd,check=True)
index=D/'index.html';text=index.read_text(encoding='utf-8');assert 'id="main-narration"'in text and all(f'id="brand-{k}"'in text and f'brand_{k}.mp4" muted'in text for k in ['intro','outro'])
track=f'<audio id="channel-bgm" class="clip" src="assets/thinking_music_loop_raw.wav" data-start="0" data-duration="{total:.9f}" data-volume="0.045" data-track-index="5" data-track-kind="music"></audio>'
index.write_text(text.replace('</div><script>window.__timelines',track+'</div><script>window.__timelines'),encoding='utf-8')
O=H/'production'/('mix-'+a.version);O.mkdir(exist_ok=True);carve=['node',str(CARVE),'--comp',str(index),'--core',str(CORE),'--bed','channel-bgm','--voice','main-narration','--strength','0.8']
env={**os.environ,'DO_NOT_TRACK':'1','HYPERFRAMES_NO_UPDATE_CHECK':'1','HYPERFRAMES_FFMPEG_PATH':str(FF),'PATH':str(FF.parent)+';'+os.environ['PATH']}
with(O/'carve.log').open('wb')as stdout,(O/'carve.stderr.log').open('wb')as stderr:r=subprocess.run(carve,cwd=D,env=env,stdout=stdout,stderr=stderr)
if r.returncode:raise RuntimeError('carve 실패. 원본 프로젝트는 보존되며 새 복제본과 로그를 확인하십시오.')
text=index.read_text(encoding='utf-8');assert all(k in text for k in ['data-fx-carve=','data-fx-chain=','data-automation='])
B=read(D/'build_receipt.json');B.update(project=str(D),version=a.version,status='음악적용_재검수대기');save(D/'build_receipt.json',B)
F=read(D/'input_freeze.json');F['inputs']+=[{'path':str(p),'sha256':sha(p)}for p in [music,manifest,CARVE,Path(__file__)]];save(D/'input_freeze.json',F)
save(D/'music_credit.json',ref['license']);save(O/'mix_receipt.json',{'status':'applied_needs_quality_and_listening','source_project':str(P),'project':str(D),'preprocess_command':cmd,'carve_command':carve,'music_sha256':sha(music),'bed_sha256':sha(bed),'voice_sha256':sha(D/'assets/narration.wav'),'brand_video_muted':True,'no_new_audio_tail':True,'actual_listening_performed':False})
save(D/'source_freeze.json',{'files':[{'path':str(p.relative_to(D)).replace('\\','/'),'sha256':sha(p)}for p in sorted(D.rglob('*'))if p.is_file()and'.hyperframes'not in p.parts and p.name!='source_freeze.json'],'timing_locked':True})
print(json.dumps({'project':str(D),'next':'quality_main.py --project 이 새 프로젝트; 실제 청취는 부모/QA','render_executed':False},ensure_ascii=False))
