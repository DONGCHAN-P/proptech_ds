"""Reproducible local checks, sequential one-worker HF renders and encoded proofs."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import build as b
WORKERS=2


def run(argv, logbase):
    logbase=b.owned(logbase)
    logbase.parent.mkdir(parents=True,exist_ok=True)
    with logbase.with_suffix('.stdout.log').open('wb')as out,logbase.with_suffix('.stderr.log').open('wb')as err:
        environment=b.env()
        environment['PATH']=str(b.FF.parent)+';'+str(b.FP.parent)+';'+environment.get('PATH','')
        p=subprocess.run(argv,cwd=b.ROOT,env=environment,stdout=out,stderr=err,creationflags=b.NO_WINDOW)
    return p.returncode


def frozen(project):
    m=b.read(project/'input_manifest.json')
    for r in m['inputs']:
        if b.sha(r['path'])!=r['sha256']:raise ValueError(f'Frozen input changed: {r["path"]}')
    for r in m['project_files']:
        if b.sha(project/r['path'])!=r['sha256']:raise ValueError(f'Frozen render source changed: {r["path"]}')
    return m


def check(project):
    m=frozen(project)
    lock=b.read(b.D/'shorts'/m['short_id']/'locked_timing.json')
    last_end=max(s['end_s']for s in lock['sentences'])
    times=[last_end-.1,last_end+.1,(m['total_frames']-1)/30]
    aa=b.read(project/'price_anchor_audit.json')
    argv=['npx.cmd','--no-install','hyperframes','check',str(project),'--at',','.join(f'{t:.6f}'for t in times),'--json','--snapshots','--timeout','30000']
    code=run(argv,project/'logs/hf_check')
    raw=(project/'logs/hf_check.stdout.log').read_text(encoding='utf-8-sig')
    result=json.loads(raw[raw.find('{'):])
    b.save(project/'hf_check.json',{'argv':argv,'exit_code':code,'result':result})
    summary={'short_id':m['short_id'],'hf_check_ok':result.get('ok'),'browserSkipped':result.get('browserSkipped'),
             'sections':{k:{x:result[k].get(x)for x in ['ok','errorCount','warningCount','samples']}for k in ['lint','runtime','layout','motion','contrast']}}
    print(json.dumps(summary,ensure_ascii=False),flush=True)
    if code or not result.get('ok')or result.get('browserSkipped'):raise RuntimeError('HF check failed; see hf_check.json')
    return summary


def render(project):
    m=frozen(project)
    check=b.read(project/'hf_check.json')
    measure=b.read(project/'source_measurement_receipt.json')
    if not check['result'].get('ok')or not measure['passed']:raise ValueError('Required source checks not passed')
    output=b.owned(b.OUT/b.FILENAMES[m['short_id']])
    output.parent.mkdir(parents=True,exist_ok=True)
    if output.exists():raise ValueError('Preserve existing MP4; use a versioned filename')
    argv=['npx.cmd','--no-install','hyperframes','render',str(project),'--workers',str(WORKERS),'--quality','delivery','--fps','30','--output',str(output)]
    started=datetime.now(timezone.utc).isoformat()
    print(json.dumps({'status':'render_started','short_id':m['short_id'],'output':str(output),'workers':WORKERS},ensure_ascii=False),flush=True)
    code=run(argv,project/'logs/render')
    if code or not output.exists()or not output.stat().st_size:
        b.save(project/'render_failed.json',{'argv':argv,'exit_code':code,'output':str(output),'started_utc':started})
        raise RuntimeError('Render failed; inspect preserved logs')
    frozen(project)
    receipt={'status':'render_created_technical_verification_pending','short_id':m['short_id'],'argv':argv,'exit_code':code,
             'started_utc':started,'ended_utc':datetime.now(timezone.utc).isoformat(),'project':str(project),'video':str(output),'video_sha256':b.sha(output),
             'video_bytes':output.stat().st_size,'lock_sha256':m['lock_sha256'],'master_audio_sha256':m['master_audio_sha256'],
             'input_manifest':str(project/'input_manifest.json'),'input_manifest_sha256':b.sha(project/'input_manifest.json'),
             'runner_sha256':b.sha(__file__),'hf_version':'0.8.181','workers':WORKERS,'local_only':True,'paid_or_TTS_or_API_calls':0,
             'actual_listening':False,'continuous_playback':False}
    b.save(project/'render_receipt.json',receipt)
    print(json.dumps({'status':'render_created','short_id':m['short_id'],'video':str(output),'video_sha256':receipt['video_sha256']},ensure_ascii=False),flush=True)


def verify(project):
    m=frozen(project)
    receipt=b.read(project/'render_receipt.json')
    video=Path(receipt['video'])
    if b.sha(video)!=receipt['video_sha256']:raise ValueError('MP4 changed')
    argv=[str(b.FP),'-v','error','-show_streams','-show_format','-of','json',str(video)]
    raw=subprocess.check_output(argv,creationflags=b.NO_WINDOW)
    info=json.loads(raw)
    b.save(project/'ffprobe.json',info)
    picture=next(s for s in info['streams']if s['codec_type']=='video')
    sound=next(s for s in info['streams']if s['codec_type']=='audio')
    duration=float(info['format']['duration'])
    checks={'width':picture['width']==1080,'height':picture['height']==1920,'fps':picture['r_frame_rate']=='30/1',
            'sar':picture.get('sample_aspect_ratio')=='1:1','rotation':not any(x.get('rotation',0)for x in picture.get('side_data_list',[])),
            'duration':abs(duration-m['total_s'])<=1/30+.003,'frames':int(picture['nb_frames'])==m['total_frames'],
            'audio':sound.get('sample_rate')=='48000'and sound.get('channels')==2,'native_duration_under_180s':duration<180}
    decode=[str(b.FF),'-v','error','-i',str(video),'-map','0:v:0','-map','0:a:0','-f','null','-']
    code=run(decode,project/'logs/decode')
    checks['full_av_decode']=code==0 and not(project/'logs/decode.stderr.log').read_text(encoding='utf-8-sig').strip()
    # Compare AAC decoded sound with the frozen source by aligned PCM correlation.
    import numpy as np
    def pcm(path):
        data=subprocess.check_output([str(b.FF),'-v','error','-i',str(path),'-map','0:a:0','-ac','1','-ar','12000','-f','f32le','-'],creationflags=b.NO_WINDOW)
        return np.frombuffer(data,dtype='<f4')
    source=pcm(project/'assets/master_audio.wav');encoded=pcm(video);n=min(len(source),len(encoded))
    correlation=float(np.corrcoef(source[:n],encoded[:n])[0,1])
    checks['audio_matches_locked_master']=correlation>.98
    audio={'master_audio_sha256':m['master_audio_sha256'],'decoded_pcm_correlation':correlation,'sample_rate_for_comparison':12000,
           'comparison':'mono downmix of delivered AAC and frozen 48k stereo master; exact duration/alignment; no audible/naturalness judgment',
           'source_peak':float(np.max(np.abs(source))),'encoded_peak':float(np.max(np.abs(encoded))),'encoded_rms':float(np.sqrt(np.mean(encoded**2)))}
    b.save(project/'audio_integrity.json',audio)
    sample=[];anchors=b.read(project/'price_anchor_audit.json')
    for s in b.read(project/'storyboard.json')['scenes']:
        aa=[r['target_s']for r in anchors if r['scene_id']==s['scene_id']]
        sample.append((s['composition_id'],max(aa)+.5 if aa else (s['start_s']+s['end_s'])/2))
        if s['kind']=='region':sample.append((s['composition_id']+'-photo',s['start_s']+.2))
    sample.extend([('last-spoken-end',m['total_s']-1.1),('last-frame',(m['total_frames']-1)/30)])
    for i,a in enumerate(anchors):
        sample.extend([(f'price-{i:02d}-before',max(0,(int(a['target_s']*30)-1)/30)),(f'price-{i:02d}-after',(int(a['target_s']*30)+2)/30)])
    frames=[]
    for label,t in sample:
        dest=b.owned(project/'encoded_proofs'/f'{label}.png');dest.parent.mkdir(parents=True,exist_ok=True)
        cmd=[str(b.FF),'-v','error','-ss',f'{t:.9f}','-i',str(video),'-frames:v','1','-y',str(dest)]
        subprocess.run(cmd,check=True,creationflags=b.NO_WINDOW)
        frames.append({'label':label,'time_s':t,'frame':str(dest),'sha256':b.sha(dest)})
    b.save(project/'encoded_proofs.json',frames)
    technical={'status':'technical_checks_passed'if all(checks.values())else'technical_check_failed','short_id':m['short_id'],'checks':checks,'duration_s':duration,
               'frames':picture['nb_frames'],'video_sha256':receipt['video_sha256'],'master_audio_sha256':m['master_audio_sha256'],'audio_integrity':audio,
               'ffprobe':str(project/'ffprobe.json'),'decode_argv':decode,'decode_exit_code':code,'proof_frames':len(frames),
               'actual_listening':False,'continuous_playback':False,'independent_QA':'parent to assign; technical pass is not audiovisual QA approval'}
    b.save(project/'technical_check.json',technical)
    receipt['status']=technical['status'];receipt['technical_check']=str(project/'technical_check.json');b.save(project/'render_receipt.json',receipt)
    print(json.dumps({'short_id':m['short_id'],'status':technical['status'],'duration_s':duration,'checks':checks,'audio_correlation':correlation,'proof_frames':len(frames)},ensure_ascii=False),flush=True)
    if not all(checks.values()):raise RuntimeError('Technical check failed')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['check','render','verify','deliver']);p.add_argument('--version',default='native-v2');p.add_argument('--short',choices=b.IDS);p.add_argument('--skip-promo',action='store_true');a=p.parse_args()
    for sid in ([a.short]if a.short else b.IDS[1:]if a.skip_promo else b.IDS):
        project=b.HERE/a.version/sid
        if a.action=='deliver':render(project);verify(project)
        else:{'check':check,'render':render,'verify':verify}[a.action](project)
