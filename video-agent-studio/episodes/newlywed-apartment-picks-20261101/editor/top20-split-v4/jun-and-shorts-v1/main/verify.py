"""Local HF checks and encoded-frame evidence; never claims listening/playback."""
import argparse
import json
import math
import os
import re
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import conform as c


def environment():
    return {**os.environ,'DO_NOT_TRACK':'1','HYPERFRAMES_NO_UPDATE_CHECK':'1',
            'HYPERFRAMES_NO_AUTO_INSTALL':'1','HYPERFRAMES_FFMPEG_PATH':str(c.FF),
            'HYPERFRAMES_FFPROBE_PATH':str(c.FP),
            'HYPERFRAMES_EXTRACT_CACHE_DIR':str(c.HERE/'.cache/extract'),
            'XDG_CACHE_HOME':str(c.HERE/'.cache'),'XDG_STATE_HOME':str(c.HERE/'.state')}


def hf_check(project,times):
    command=['npx.cmd','--no-install','hyperframes','check',str(project),'--at',
             ','.join(f'{t:.6f}'for t in times),'--json','--snapshots','--timeout','20000']
    p=subprocess.run(command,cwd=c.ROOT,env=environment(),capture_output=True,creationflags=c.NO_WINDOW)
    stdout=p.stdout.decode('utf-8-sig',errors='replace')
    stderr=p.stderr.decode('utf-8-sig',errors='replace')
    c.write(project/'logs/hf_check.stdout.json',stdout)
    c.write(project/'logs/hf_check.stderr.log',stderr)
    start=stdout.find('{')
    result=json.loads(stdout[start:])
    if p.returncode or not result.get('ok') or result.get('browserSkipped'):
        raise RuntimeError(f'HyperFrames check failed: {project}')
    c.save(project/'hf_check.json',{'command':command,'exit_code':p.returncode,'result':result})
    return result


def extract(video,folder,times):
    result=[]
    folder=c.owned(folder);folder.mkdir(parents=True,exist_ok=True)
    for label,t in times:
        dest=c.owned(folder/f'{label}.jpg')
        if not dest.exists():
            subprocess.run([str(c.FF),'-v','error','-ss',f'{t:.9f}','-i',str(video),
                            '-frames:v','1','-q:v','2',str(dest)],check=True,creationflags=c.NO_WINDOW)
        result.append({'label':label,'time_s':t,'frame':str(dest),'sha256':c.sha(dest)})
    return result


def diagnostics(d):
    a=d['source_to_target_anchors'];rates=[]
    for l,r in zip(a,a[1:]):
        dt=r['target_s']-l['target_s'];ds=r['source_s']-l['source_s']
        if dt>0:
            rates.append({'source_rate':ds/dt,'target_duration_s':dt,
                          'source_duration_s':ds,'left':l,'right':r})
    report={'lock_sha256':c.sha(c.LOCK),'anchors':len(a),'anchors_dropped':0,
            'anchor_policy':'All parent float anchors retained. Only raster picture selection is quantized to 30fps.',
            'frame_sampling':'floor(source_s*30), never look ahead',
            'minimum_rate_interval':min(rates,key=lambda x:x['source_rate']),
            'maximum_rate_interval':max(rates,key=lambda x:x['source_rate']),
            'sub_frame_intervals':sum(r['target_duration_s']<1/c.FPS for r in rates),
            'rate_limit_applied':False,'caption_timing_from_parent_unchanged':True}
    c.save(c.HERE/'jun-v1/anchor_diagnostics.json',report)
    return report


def proofs(version):
    d=c.read(c.LOCK);info=c.check_contract(d)
    folder=c.HERE/(version+'-proofs')
    proof=c.read(folder/'proofs.json')
    if proof['lock_sha256']!=c.sha(c.LOCK):
        raise ValueError('Proof lock version changed')
    results=[]
    for row in proof['proofs']:
        name,a,b=row['name'],row['start_s'],row['end_s']
        project=folder/name;dur=b-a
        times=[.5,dur*.5,max(.1,dur-.1)]
        if name=='question_brand':
            times=[2.,d['brand_intro']['start_s']+2.]
        results.append({'name':name,'hf_check_ok':hf_check(project,times)['ok'],
                        'frames':extract(row['video'],project/'evidence',[(f'frame_{i}',t)for i,t in enumerate(times)])})
    c.save(folder/'verification.json',{'lock_sha256':c.sha(c.LOCK),'results':results,
        'actual_listening':False,'continuous_playback':False})
    diagnostics(d)
    print(json.dumps({'status':'proof_hf_checks_and_frames_ready','verification':str(folder/'verification.json')},ensure_ascii=False),flush=True)


def full(version):
    d=c.read(c.LOCK);info=c.check_contract(d)
    folder=c.HERE/version;project=folder/'project'
    r=c.read(folder/'render_receipt.json')
    if r['lock_sha256']!=c.sha(c.LOCK) or r['video_sha256']!=c.sha(r['video']):
        raise ValueError('Final artifact/lock changed')
    checkpoints=[('hook',2.),('brand_intro',d['brand_intro']['start_s']+2.),
                 ('criteria',next(x for x in d['main_sentences']if x['sentence_id']=='P01-CRITERIA-01')['start_s']+2.),
                 ('last_voice',d['last_spoken_end_s']-.2),
                 ('natural_tail',d['last_spoken_end_s']+1.),
                 ('brand_outro',d['brand_outro']['start_s']+5.),
                 ('last_frame',(r['frames']-1)/c.FPS)]
    for p in c.read(c.TRANSITIONS)['photos']:
        checkpoints.append((f'R{p["rank"]}_photo',info['warp'].target_at(p['final_start_s'])+1.))
        checkpoints.append((f'R{p["rank"]}_map',info['warp'].target_at(p['final_end_s'])+.25))
    price_ids={r['sentence_id']for r in c.read(c.EPISODE/'editor/top20-split-v4/part1-production-v1/final-v3/price_audit.json')}
    for sentence in d['main_sentences']:
        if sentence['sentence_id'] not in price_ids:
            continue
        seen=set()
        for word in sentence['words']:
            text=word.get('display_text','')
            if re.search(r'\d.*(?:억|만원|억원|원)',text) and text not in seen:
                seen.add(text)
                checkpoints.append((sentence['sentence_id']+f'_price_{len(seen)}',word['start_s']+.35))
    hf=hf_check(project,[t for label,t in checkpoints if label in ('hook','brand_intro','criteria','R20_map','natural_tail','brand_outro')])
    frames=extract(r['video'],folder/'encoded_frames',checkpoints)
    c.save(folder/'verification.json',{'status':'automated_checks_passed_frames_for_review',
        'lock_sha256':c.sha(c.LOCK),'video_sha256':r['video_sha256'],'hf_check_ok':hf['ok'],
        'frames':frames,'actual_listening':False,'continuous_playback':False,
        'independent_qa':'parent_to_assign','probe_and_decode_receipt':str(folder/'render_receipt.json')})
    print(json.dumps({'status':'final_frames_ready','frame_count':len(frames),'verification':str(folder/'verification.json')},ensure_ascii=False),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['proofs','full']);p.add_argument('--version',default='jun-v1')
    a=p.parse_args()
    (proofs if a.action=='proofs'else full)(a.version)
