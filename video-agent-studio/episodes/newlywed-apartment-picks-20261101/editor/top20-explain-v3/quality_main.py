"""전체 실측HTML 자동검사·대표PNG. MP4 렌더와 실제 청취는 부모 담당입니다."""
from pathlib import Path
import argparse,json,os,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from main_contract import H,R,read,sha,save

ap=argparse.ArgumentParser();ap.add_argument('--project',required=True);args=ap.parse_args();P=Path(args.project).resolve()
if not P.is_relative_to(H/'main'):raise ValueError('v3 main 프로젝트만 허용')
B=read(P/'build_receipt.json');T=read(P/'timeline_resolved.json');ph=read(P/'phase_audit.json');freeze=read(P/'source_freeze.json');inputs=read(P/'input_freeze.json')
assert B['scene_count']==26 and B['sentence_count']==133 and B['timing_locked']
assert T['duration_s']>480
assert all(sha(P/v['path'])==v['sha256']for v in freeze['files'])
assert all(sha(v['path'])==v['sha256']for v in inputs['inputs'])
times=[(s['start_s']+s['end_s'])/2 for s in T['scenes']]
by_id={s['scene_id']:s for s in T['scenes']}
for p in ph:times.extend([by_id[p['scene_id']]['start_s']+p['switch_s']-.04,by_id[p['scene_id']]['start_s']+p['switch_s']+.04])
for b in T['inserts']:times.extend([b['start_s']+.04,b['start_s']+b['duration_s']-.04])
times.extend([T['last_speech_end_s']+.04,T['duration_s']-.04]);times=sorted(set(round(v,6)for v in times))
O=H/'production'/('quality-'+B['version']);O.mkdir(parents=True,exist_ok=True)
FF=R/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe';FP=R/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe'
env={**os.environ,'DO_NOT_TRACK':'1','HYPERFRAMES_NO_UPDATE_CHECK':'1','HYPERFRAMES_NO_AUTO_INSTALL':'1','HYPERFRAMES_FFMPEG_PATH':str(FF),'HYPERFRAMES_FFPROBE_PATH':str(FP),'HYPERFRAMES_EXTRACT_CACHE_DIR':str(H/'production/extract-cache'),'PATH':str(FF.parent)+';'+str(FP.parent)+';'+os.environ['PATH']}
argv=['npx.cmd','--no-install','hyperframes','check',str(P),'--at',','.join(map(str,times)),'--json','--snapshots','--timeout','20000']
with (O/'check.json').open('wb') as out,(O/'check.stderr.log').open('wb')as err:result=subprocess.run(argv,env=env,stdout=out,stderr=err)
C=read(O/'check.json');status='passed' if result.returncode==0 and C['ok'] and not C.get('browserSkipped')else'failed'
save(O/'quality_receipt.json',{'status':status,'scope':'전체26장면 중앙·20지역가격전환직전직후·브랜드경계·마지막3초 실제브라우저 자동검사','samples':times,'sample_count':len(times),'lint':C.get('lint'),'runtime':C.get('runtime'),'layout':C.get('layout'),'contrast':C.get('contrast'),'command':argv,'actual_listening_performed':False,'continuous_playback_performed':False,'mp4_rendered':False})
print(json.dumps({'status':status,'samples':len(times),'layout_findings':C.get('layout',{}).get('totalIssueCount'),'result':str(O/'quality_receipt.json')},ensure_ascii=False),flush=True)
if status!='passed':raise SystemExit(1)
shots=[(s['start_s']+s['end_s'])/2 for s in T['scenes']]
shots.extend(by_id[p['scene_id']]['start_s']+(p['switch_s']+by_id[p['scene_id']]['duration_s'])/2 for p in ph)
shots.extend(b['start_s']+b['duration_s']/2 for b in T['inserts'])
snapshot=['npx.cmd','--no-install','hyperframes','snapshot',str(P),'--at',','.join(str(round(v,6))for v in sorted(shots)),'--no-end','--describe','false','--output',str(O/'png'),'--timeout','20000']
if (O/'png').exists():raise ValueError('기존 검수PNG 보존: 새 버전으로 실행하십시오.')
with (O/'snapshot.log').open('wb')as out,(O/'snapshot.stderr.log').open('wb')as err:r=subprocess.run(snapshot,env=env,stdout=out,stderr=err)
assert r.returncode==0 and len(list((O/'png').glob('frame*.png')))==len(shots)
save(O/'snapshot_receipt.json',{'status':'passed','png_count':len(shots),'times':sorted(shots),'command':snapshot,'scope':'HTML 렌더 표본PNG; MP4 디코드 프레임 아님','actual_listening_performed':False})
print(json.dumps({'snapshots':len(shots),'path':str(O/'png')},ensure_ascii=False),flush=True)
