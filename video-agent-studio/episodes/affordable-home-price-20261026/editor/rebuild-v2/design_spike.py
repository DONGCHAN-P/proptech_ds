"""Authorized silent 9s specimens; provisional synthetic clocks, never narration."""
import json
import math
import os
import subprocess
import sys
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pipeline as p
from graphics import make


def main():
    run=p.owned(p.OUT/'design-spike-v1')
    resume='--resume-failed-render' in sys.argv
    if run.exists() and not resume:raise ValueError('Preserve existing spike; use an explicit new version')
    packet=p.read(p.EP/'research/verified_case_packet.json')
    titles={'funding_waterfall':'6억원 집에 추가로 필요한 현금','ltv_dsr':'집값 기준과 소득 기준 중 낮은 한도','monthly_budget':'월 상환예산에서 다시 정하는 집값'}
    cli=p.cli_path();env=p.ENV
    rows=p.read(run/'input_manifest.json')['scenes'] if resume else []
    for kind in ([] if resume else p.KINDS):
        graphic=make(kind,packet);n=len(graphic['stages'])
        # The final information settles before 7.5s; minimum 1.2s read hold.
        times=[.4+i*(6.4/(n-1)) for i in range(n)]
        beats=[{**s,'start_s':t,'end_s':t+.65,'anchor':None,'cue_ids':[],'timing_basis':'synthetic_design_clock_not_actual_cue'} for s,t in zip(graphic['stages'],times)]
        folder=run/'scenes'/kind
        duration=p.emit_project(folder,{'id':kind,'title':titles[kind]},{'duration_s':9,'last_speech_end_s':None,'cues':[],'audio_path':None},graphic,beats,'검증 자금계획 사례 · 2026.10.26 · 서울 84㎡ · 조건부 계획값',template=True)
        model=p.read(folder/'scene.json');model.update(provisional_design_only=True,actual_cue_timing=False,actual_script_used=False,actual_audio_used=False,design_clock_seconds=times)
        p.dump(folder/'scene.json',model)
        rows.append({'kind':kind,'folder':str(folder),'duration_s':duration,'timing_basis':'synthetic_design_clock_not_actual_cue','html_sha256':p.sha(folder/'index.html'),'provisional_design_only':True})
    if not resume:
        p.dump(run/'input_manifest.json',{'provisional_design_only':True,'script_lock':None,'audio':None,'research':p.pin(p.EP/'research/verified_case_packet.json'),'code':[p.pin(p.HERE/n) for n in ['pipeline.py','graphics.py','runtime.js','shell.css','design_spike.py','verify_templates.cjs']],'scenes':rows})
        subprocess.run(['node',str(p.HERE/'verify_templates.cjs'),str(run)],check=True,env=env)
    for row in rows:
        folder=Path(row['folder']);kind=row['kind'];model=p.read(folder/'scene.json')
        if p.sha(folder/'index.html')!=row['html_sha256']:raise ValueError('Frozen spike source changed')
        times=sorted({0,8.8}|{max(0,b['start_s']-1/30) for b in model['beats']}|{b['start_s']+.55 for b in model['beats']})
        argv=[cli,'check','.','--json','--at',','.join(map(str,times)),'--timeout','10000']
        previous_check={}
        if resume and (folder/'check.log').is_file():
            log_text=(folder/'check.log').read_text(encoding='utf8')
            start=log_text.find('{\n')
            if start>=0:previous_check=json.JSONDecoder().raw_decode(log_text[start:])[0]
        if previous_check.get('ok') is not True:
            with (folder/'check.log').open('w',encoding='utf8') as log:
                check=subprocess.run(argv,cwd=folder,env=env,stdout=log,stderr=subprocess.STDOUT)
            if check.returncode:raise ValueError('Source CLI check failed: '+str(folder/'check.log'))
        final=run/(kind+'.mp4')
        render=[cli,'render','.','--fps','30','--format','mp4','--quality','looks','--workers','2','--browser-gpu','--output',str(final),'--frames-cache-dir',str(run/'frame-cache'/kind)]
        with (folder/'render.log').open('w',encoding='utf8') as log:
            result=subprocess.run(render,cwd=folder,env=env,stdout=log,stderr=subprocess.STDOUT)
        if result.returncode:raise ValueError('Spike render failed: '+str(folder/'render.log'))
        info=p.probe(final);video=next(s for s in info['streams'] if s['codec_type']=='video')
        if any(s['codec_type']=='audio' for s in info['streams']):raise ValueError('Spike must be silent with no audio stream')
        if (video['width'],video['height'],video['r_frame_rate'])!=(1920,1080,'30/1') or abs(float(info['format']['duration'])-9)>.04:raise ValueError('Unexpected spike encoding')
        decode=[str(p.FFMPEG),'-v','error','-xerror','-i',str(final),'-f','null','-']
        subprocess.run(decode,check=True,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        frames=sorted({min(269,round(t*30)) for t in times});dest=folder/'encoded';dest.mkdir()
        select='+'.join(f'eq(n\\,{n})' for n in frames)
        extract=[str(p.FFMPEG),'-n','-v','error','-i',str(final),'-vf','select='+select,'-fps_mode','passthrough',str(dest/'frame-%03d.png')]
        subprocess.run(extract,check=True,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        images=sorted(dest.glob('frame-*.png'))
        if len(images)!=len(frames):raise ValueError('Encoded frame count mismatch')
        row.update(mp4=p.pin(final),probe=info,AV_decode='pass',audio_streams=0,frame_evidence=[{'frame_index':n,'pts_s':n/30,'path':str(f),'sha256':p.sha(f),'manual_viewed':False} for n,f in zip(frames,images)],commands=[argv,render,decode,extract],source_QA='geometry+seek+CLI pass',actual_cue_timing=False)
        print(json.dumps({'kind':kind,'status':'silent_design_spike_encoded','provisional_design_only':True}),flush=True)
    receipt={'status':'three_silent_prototypes_encoded_visual_review_pending','provisional_design_only':True,'duration_each_s':9,'width':1920,'height':1080,'fps':30,'scenes':rows,'actual_script_approval':False,'actual_audio':False,'actual_cue_timing':False,'actual_listening':False,'continuous_playback':False,'full_film_rendered':False,'independent_measured_representative_gate':'still_pending_actual_voice'}
    p.dump(run/'render_receipt.json',receipt)
    print(json.dumps({'status':receipt['status'],'MP4s':3,'provisional_design_only':True}))


if __name__=='__main__':
    try:main()
    except Exception as e:
        p.dump(p.OUT/'design-spike-v1/failure_receipt.json',{'status':'failed','error':str(e),'provisional_design_only':True,'full_film_rendered':False})
        raise
