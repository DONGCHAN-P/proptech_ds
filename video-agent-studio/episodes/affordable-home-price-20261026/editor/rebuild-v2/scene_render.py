"""Exact locked-r2 / native WordBoundary scene production. No synthesis or assembly."""
import argparse
import json
import math
import re
import subprocess
import sys
import wave
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pipeline as p
from voice_adapter import normalize_payload
from frozen_graphics import make_scene
from graphics import Drawing


# Opening context is separate from the unchanged writer beats. No result is
# pre-revealed; these are known inputs or the subject/definition being spoken.
OPENINGS={
 'R001':['보유자금','2억5천만원','집값의 범위'],
 'R002':['가구의 현금','매달 쓸 예산','대출 조건'],
 'R003':['보유현금 2억5천만원','예비자금 분리','구입자금'],
 'R004':['취득세','중개보수','등기·기타 비용'],
 'R005':['구입자금 2억2천만원','거래비용 1,074만원','집값 6억원'],
 'R006':['6억원 주택','담보평가액 = 매매가','LTV 비율 적용'],
 'R007':['인정소득','연간 상환예산','기존 대출 원리금'],
 'R008':['실제 납부금리','스트레스 가산금리','심사에 쓰는 금리'],
 'R009':['집값 → 담보 한도','소득 → 상환 한도','여러 한도를 비교'],
 'R010':['공제 전 담보 한도','4억2천만원','서울 담보대출 공제'],
 'R011':['6억원 주택','보증 승인으로 공제 보완','매달 갚는 금액'],
 'R029':['보유현금 2억5천만원','인정소득 연1억원','약정금리 4% · 30년'],
 'R030':['매달 예산 300만원','소유비 30만원','남길 저축 100만원'],
 'R031':['매달 예산 300만원','대출 상환액','남길 저축'],
 'R032':['A의 같은 최초 대출원금','약정금리 4% / 6%','각각 360개월'],
 'R033':['현금과 은행 조건','매달의 상환 목표','두 기준의 집값'],
 'R012':['주택가격','6억원 → 9억원','취득세율 구간'],
 'R013':['주택가격','구간별 중개보수','총 거래비용'],
 'R014':['생애최초 주택 구입','취득세 감면 조건','감면 한도 비교'],
 'R015':['A · 생애최초','9억원 주택','필요대출과 은행 한도'],
 'R016':['A · 생애최초','12억원 주택','필요대출과 은행 한도'],
 'R017':['주택가격 구간','총 대출금액 상한','가격별 상한 비교'],
 'R018':['A 가구의 조건','B 가구의 조건','정책대출 검토'],
 'R019':['B · 6억원 주택','디딤돌대출','필요대출과 상품상한'],
 'R020':['B · 6억원 주택','보금자리론 자체 기준','필요대출과 상품상한'],
 'R021':['B의 같은 필요대출','디딤돌 · 보금자리론','신생아 특례'],
 'R022':['대출 실행일','전입 기한','실거주 기간'],
 'R023':['B 출산가구','접수일 기준 출산 시점','소득 · 순자산 조건'],
 'R024':['B · 현재 주택 6억원','신생아 특례 자격','필요한 대출금액'],
 'R025':['B · 신생아 특례','초기 기본금리','처음 5년의 상환'],
 'R026':['B · 초기 기본금리 2.9%','60회 상환','이후 금리와 잔액'],
 'R027':['B · 9억원 주택','신생아 특례','상품 대출상한'],
 'R028':['주택가격 9억원','대출상한 4억원','남은 집값과 비용'],
 'R034':['자기자금','대출 가능 범위','월 상환 목표'],
}


def opening(g,sid,first):
    if first<1.5:return
    d=Drawing();body=''
    for i,label in enumerate(OPENINGS[sid]):
        x=55+i*555
        body+=d.label('opening-node-'+str(i),label,x,150,525,32,'var(--ink)')
        if i<2:body+=d.label('opening-arrow-'+str(i),'→',x+465,260,60,48,'var(--muted)')
    # Neutral input paths, never a finished chart or a conclusion.
    for i in range(3):
        body+=f'<div id="opening-rule-{i}" data-object="shape" style="position:absolute;left:{55+i*555}px;top:330px;width:440px;height:5px;background:#a8b5b6"></div>'
    g['html']='<div id="opening-context" class="opening-context">'+body+'</div>'+g['html']
    g['objects']=d.objects+g['objects']
    g['opening_context']={'id':'opening-context','start_s':0,'end_s':max(0,first-1/30),'basis':'fixed known inputs / spoken topic; separate from writer anchors','labels':OPENINGS[sid]}
    g['source_recipe']['opening_context']=g['opening_context']


def footer(sid):
    if sid in ['R004','R012','R013','R014']:
        return '자료: 서울특별시 · 국가법령정보센터 | 기준 2026.10.26 · 사례 계산'
    if sid in ['R025','R026']:
        return '자료: 주택도시기금 금리표 2026.10.19 | 사례 계산 · 우대금리 0'
    if sid in ['R019','R023','R024','R027','R028']:
        return '자료: 주택도시기금 | 기준 2026.10.26 · 사례 계산'
    if sid=='R020':return '자료: 한국주택금융공사 | 기준 2026.10.26 · 사례 계산'
    if sid in ['R018','R021','R022']:
        return '자료: 주택도시기금 · 한국주택금융공사 | 기준 2026.10.26 · 사례 계산'
    if sid in ['R006','R007','R008','R009','R010','R017']:
        return '자료: 금융위원회 · 한국주택금융공사 | 기준 2026.10.26 · 사례 계산'
    return '자료: 공개 제도 기준 · 사례 계산 | 기준 2026.10.26'


def prepare(run,timing,lock):
    rf=p.owned(p.OUT/run)
    if rf.exists():raise ValueError('Preserve existing run; choose a new run')
    lf=p.source(lock);locked=p.read(lf);sf=p.source(locked['script_path'])
    if locked.get('approved') is not True or locked.get('claude_approved') is not True or p.sha(sf)!=locked['script_sha256']:raise ValueError('Exact approved r2 required')
    tf=p.source(timing);raw=p.read(tf);script=p.read(sf)
    if raw['script_sha256']!=p.sha(sf):raise ValueError('Wrong voice script SHA')
    adapted=normalize_payload(script,raw)
    packet=p.read(p.EP/'research/verified_case_packet.json');nb=p.read(p.EP/'research/newborn_policy_addendum_v2.json')
    override=p.EP/'director/rebuild-v2/visual_overrides.json'
    for voice in adapted['scenes']:
        for pk,sk in [('audio_path','audio_sha256'),('original_audio24_path','original_audio24_sha256')]:
            if p.sha(p.source(voice[pk]))!=voice[sk]:raise ValueError('Audio SHA mismatch '+voice['scene_id'])
        with wave.open(str(p.source(voice['audio_path'])),'rb') as wav:
            if wav.getframerate()!=48000 or abs(wav.getnframes()/48000-voice['duration_s'])>.001:raise ValueError('Actual WAV duration mismatch')
    rows=[]
    for i,(scene,voice) in enumerate(zip(script['scenes'],adapted['scenes'])):
        sid=scene['id'];g=make_scene(scene,packet,nb)
        if sid=='R032':g['source_recipe'].update(visual_override=p.pin(override),override_applied='A from R031; same original principals; 4%/6%, each 360 months; no B balance')
        beats=p.resolve_beats(scene,voice,g,{b['key']:i for i,b in enumerate(g['stages'])})
        opening(g,sid,beats[0]['start_s'])
        folder=rf/'scenes'/sid;duration=p.emit_project(folder,scene,voice,g,beats,footer(sid))
        model=p.read(folder/'scene.json');model.update(opening_context=g.get('opening_context'),source_ids=scene['source_ids'],script_sha256=p.sha(sf),native_timing_sha256=p.sha(tf),actual_cue_timing=True,provisional_design_only=False)
        p.dump(folder/'scene.json',model)
        rows.append({'scene_id':sid,'chapter':scene['chapter'],'order_index':i,'path':str(folder/(sid+'.mp4')),'mp4_path':str(folder/(sid+'.mp4')),'sourceJSON':str(folder/'scene.json'),'source_json_path':str(folder/'scene.json'),'html_path':str(folder/'index.html'),'html_sha256':p.sha(folder/'index.html'),'duration':duration,'duration_s':duration,'video_frames':round(duration*30),'audio':voice['audio_path'],'audio_sha256':voice['audio_sha256'],'original_audio24_path':voice['original_audio24_path'],'original_audio24_sha256':voice['original_audio24_sha256'],'source_audio_duration_s':voice['duration_s'],'last_speech_end_s':voice['last_speech_end_s'],'gap_after_s':voice['gap_after_s'],'tail_added_s':duration-voice['duration_s'],'final_hold_already_in_audio':i==len(script['scenes'])-1,'first_anchor_s':beats[0]['start_s'],'opening_context':g.get('opening_context'),'status':'prepared','kind':g['kind'],'source_ids':scene['source_ids'],'source_recipe':g['source_recipe']})
    pins=[p.pin(p.HERE/n) for n in ['scene_render.py','pipeline.py','frozen_graphics.py','graphics.py','runtime.js','shell.css','voice_adapter.py','verify_templates.cjs']]
    manifest={'status':'actual_34_sources_ready_representatives_pending','script':p.pin(sf),'script_lock':p.pin(lf),'timing':p.pin(tf),'visual_override':p.pin(override),'recovery_provenance':p.pin(tf.parent/'recovery_receipt_verified.json'),'code_inputs':pins,'scene_order':[s['id'] for s in script['scenes']],'scenes':rows,'fps':30,'resolution':[1920,1080],'actual_cue_timing':True,'provisional_design_only':False,'brand_chapter_BGM_included':False,'scene_mp4_contains_narration':True,'gap_in_scene_mp4':False,'final_3s_hold_already_in_last_audio':True,'global_clock_owner':'Lovelace assembly','actual_listening':False,'continuous_playback':False}
    p.dump(rf/'adapted_timing.json',adapted);p.dump(rf/'scene_run_manifest.json',manifest)
    p.dump(rf/'preparation_manifest.json',{'scene_order':manifest['scene_order']})
    return manifest


def execute(argv,cwd,log):
    with Path(log).open('w',encoding='utf8') as f:
        code=subprocess.run(argv,cwd=cwd,env=p.ENV,stdout=f,stderr=subprocess.STDOUT).returncode
    if code:raise ValueError('Command failed: '+str(log))


def render(run,selected):
    rf=p.owned(p.OUT/run);mf=rf/'scene_run_manifest.json';manifest=p.read(mf);cli=p.cli_path()
    for ref in [manifest['script'],manifest['script_lock'],manifest['timing'],*manifest['code_inputs']]:p.checked_ref(ref)
    ids=selected or manifest['scene_order']
    if any(s not in manifest['scene_order'] for s in ids):raise ValueError('Unknown scene')
    # Actual visible glyph geometry includes opening at 0 and before first beat.
    execute(['node',str(p.HERE/'verify_templates.cjs'),str(rf),*ids],p.HERE,rf/('geometry-'+ids[0]+'.log'))
    for row in manifest['scenes']:
        sid=row['scene_id']
        if sid not in ids:continue
        if row['status']=='encoded':
            p.checked_ref(row['encoded']);continue
        folder=Path(row['html_path']).parent;model=p.read(row['source_json_path'])
        if p.sha(folder/'index.html')!=row['html_sha256']:raise ValueError('Source changed')
        row['status']='rendering';p.dump(mf,manifest)
        argv=[cli,'render','.','--quality','looks','--fps','30','--workers','2','--browser-gpu','--output',str(folder/'silent.mp4')]
        print(json.dumps({'phase':'render_start','scene_id':sid,'duration_s':row['duration_s']}),flush=True)
        execute(argv,folder,folder/'render.log')
        mux=[str(p.FFMPEG),'-n','-i',str(folder/'silent.mp4'),'-i',str(p.source(row['audio'])),'-map','0:v:0','-map','1:a:0','-c:v','copy','-af','apad','-t',str(row['duration_s']),'-c:a','aac','-ar','48000','-ac','2',row['mp4_path']]
        execute(mux,folder,folder/'mux.log')
        info=p.probe(Path(row['mp4_path']));v=next(x for x in info['streams'] if x['codec_type']=='video');a=next(x for x in info['streams'] if x['codec_type']=='audio')
        if (v['width'],v['height'],v['r_frame_rate'],a['sample_rate'])!=(1920,1080,'30/1','48000') or abs(float(info['format']['duration'])-row['duration_s'])>.06:raise ValueError('Encoded stream mismatch')
        execute([str(p.FFMPEG),'-v','error','-xerror','-i',row['mp4_path'],'-map','0:v:0','-map','0:a:0','-f','null','-'],folder,folder/'decode.log')
        times={0,row['duration_s']-1/30}
        if model.get('opening_context'):times.add(model['beats'][0]['start_s']/2)
        for b in model['beats']:times.update([max(0,b['start_s']-1/30),min(row['duration_s']-1/30,b['start_s']+.7)])
        evidence=[]
        for i,t in enumerate(sorted(times)):
            target=folder/f'encoded-{i:03}.png'
            execute([str(p.FFMPEG),'-n','-v','error','-ss',str(t),'-i',row['mp4_path'],'-frames:v','1',str(target)],folder,folder/'frame-extract.log')
            evidence.append({'time_s':t,'path':str(target),'sha256':p.sha(target),'manual_viewed':False})
        row.update(status='encoded',encoded=p.pin(row['mp4_path']),probe=info,decode='pass',frames=evidence,commands=[argv,mux])
        manifest['status']='all34_encoded' if all(r['status']=='encoded' for r in manifest['scenes']) else 'partial_encoded_parent_representative_QA_pending'
        p.dump(mf,manifest);p.dump(folder/'render_receipt.json',row)
        print(json.dumps({'phase':'encoded','scene_id':sid,'mp4':row['mp4_path'],'duration_s':row['duration_s'],'decode':'pass'}),flush=True)
    return manifest


def main():
    q=argparse.ArgumentParser();q.add_argument('action',choices=['prepare','render']);q.add_argument('--run',required=True);q.add_argument('--timing',default='narration/rebuild-v2/audio-r2-recovered/final_timing.json');q.add_argument('--script-lock',default='director/rebuild-v2/locked_script_r2.json');q.add_argument('--scene',action='append')
    a=q.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*',a.run):raise ValueError('Unsafe run')
    try:
        m=prepare(a.run,a.timing,a.script_lock) if a.action=='prepare' else render(a.run,a.scene)
        print(json.dumps({'status':m['status'],'scene_count':len(m['scenes'])}),flush=True)
    except Exception as e:
        p.dump(p.OUT/a.run/'current_failure.json',{'status':'failed','action':a.action,'scene_ids':a.scene,'error':str(e),'actual_listening':False});raise


if __name__=='__main__':main()
