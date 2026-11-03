"""Source/template preflight only. Never renders video or synthesizes speech."""
import hashlib, html, json, shutil
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

HERE=Path(__file__).resolve().parent
EP=HERE.parent; STUDIO=EP.parents[1]; ROOT=STUDIO.parent
OUT=EP/'outputs/private-production-v1'
BASE=STUDIO/'episodes/housing-choice-networth-20261020'

def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def e(v): return html.escape(str(v),quote=True)
def man(v): return f'{Decimal(str(v))/10000:,.0f}만원'
def eok(v):
    """Display only: round to one manwon, then group large amounts by eok."""
    n=int((Decimal(str(v))/10000).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
    if not n:return '0원'
    whole,rest=divmod(n,10000)
    if not whole:return f'{rest:,}만원'
    if not rest:return f'{whole}억원'
    return f'{whole}억{rest//1000}천만원' if rest%1000==0 else f'{whole}억{rest:,}만원'
def monthly(v): return f'{Decimal(str(v))/10000:,.1f}만원'

def resolve_input(raw):
    raw=Path(raw)
    options=[raw] if raw.is_absolute() else [ROOT/raw,EP/raw]
    found=next((p for p in options if p.is_file()),None)
    if not found:raise ValueError('Required input missing: '+str(raw))
    return found

def load_script_lock(lock_path=None):
    lock_path=Path(lock_path) if lock_path else EP/'director/production-v1/locked_script.json'
    lock=read(lock_path)
    if not all(lock.get(k) is True for k in ['approved','codex_content_pass','claude_content_pass']):raise ValueError('Exact dual-content script lock is required')
    script=resolve_input(lock['script_path'])
    if sha(script)!=lock['script_sha256']:raise ValueError('Canonical script differs from lock')
    for raw,expected in lock['review_receipt_sha256'].items():
        receipt=resolve_input(raw)
        if sha(receipt)!=expected or read(receipt).get('approved') is not True:raise ValueError('Content receipt changed: '+raw)
    for path_key,sha_key in [('source_proposals','source_proposals_sha256'),('facts','facts_sha256')]:
        if sha(resolve_input(lock[path_key]))!=lock[sha_key]:raise ValueError('Locked source input changed: '+path_key)
    return lock,script,lock_path

def bind_approved_scenes(lock,script):
    central=read(EP/'scenes.json');proposal=read(resolve_input(lock['source_proposals']))
    assert central['script_sha256']==lock['script_sha256']
    assert len(central['scenes'])==len(proposal['scenes'])==45
    prepared=EP/'narration/prepare-v2-r2/prepared.json'
    native_plan=read(prepared) if prepared.is_file() else None
    paragraphs=[p for ch in native_plan['chapters'] for p in ch['paragraphs']] if native_plan else []
    if native_plan:assert native_plan['script_sha256']==lock['script_sha256'] and len(paragraphs)==45
    bindings=[]
    for i,(scene,proposed) in enumerate(zip(central['scenes'],proposal['scenes']),1):
        assert scene['scene_id']==proposed['scene_id'] and scene['chapter']==proposed['chapter']
        assert scene['narration_text']==proposed['display_text'] and scene['spoken_text']==proposed['spoken_text']
        if native_plan:
            p=paragraphs[i-1]
            assert p['scene_id']==scene['scene_id'] and p['paragraph']==i and p['chapter']==scene['chapter']
            assert p['text']==scene['narration_text'] and p['spoken_text']==scene['spoken_text']
        bindings.append({'scene_id':scene['scene_id'],'paragraph':i,'chapter':scene['chapter'],'display_text':scene['narration_text'],'spoken_text':scene['spoken_text'],'graphic_id':proposed['graphic_id'],'claim_ids':scene['claim_ids'],'asset_ids':scene['asset_ids'],'start_s':None,'end_s':None,'T_anchors':None,'timing_basis':'pending_actual_native_paragraph_and_cues','estimated_times_used':False})
    dump(OUT/'scene_bindings.json',{'status':'45_approved_text_pairs_bound_actual_timing_pending','script_path':script.relative_to(ROOT).as_posix(),'script_sha256':lock['script_sha256'],'central_scenes_sha256':sha(EP/'scenes.json'),'source_proposals_sha256':sha(resolve_input(lock['source_proposals'])),'prepared_plan_sha256':sha(prepared) if native_plan else None,'prepared_plan_is_measured':False,'bindings':bindings,'body_seconds':None,'film_seconds':None,'global_offsets':None,'full_render_authorized':False})
def text(x,y,s,size=26,fill='var(--ink)',weight=400,anchor='start'):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" text-anchor="{anchor}">{e(s)}</text>'
def rect(x,y,w,h,fill='white',r=12,extra=''):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" {extra}/>'
def svg(body):return '<svg class="graphic" viewBox="0 0 1740 590" xmlns="http://www.w3.org/2000/svg" aria-label="금융 사례 도식">'+body+'</svg>'

def cash(data):
    common=data['packet']['conditions']['common']; c=data['cases']['A_first_P600000000_C0']
    values=[Decimal(common['cash_krw']),Decimal(common['cash_krw'])-Decimal(common['reserve_krw'])]
    values.append(values[-1]-Decimal(c['transaction_costs']['total_krw']))
    body=text(36,42,'6억원 주택 · 예비자금과 거래비용을 먼저 배정',26,weight=600)
    labels=['보유자금','예비자금 배정 후','집값에 넣을 자기자금']; colors=['var(--blue)','var(--gold)','var(--green)']
    for i,(v,label,color) in enumerate(zip(values,labels,colors)):
        x=65+i*535; h=float(v/Decimal(common['cash_krw']))*245
        body+=rect(x,360-h,390,h,color,8)+text(x+195,104,eok(v),40,'var(--gold-ink)' if i==1 else color,700,'middle')+text(x+195,405,label,28,weight=600,anchor='middle')
        if i<2:
            deduction=[common['reserve_krw'],c['transaction_costs']['total_krw']][i]
            body+=text(x+465,235,'−',40,anchor='middle')+text(x+465,277,man(deduction),24,anchor='middle')
    body+=rect(36,452,1668,93)+text(66,489,'잔금 자금 연결',24,weight=600)
    body+=text(66,526,'자기자금 2억926만원 + 필요한 대출 3억9,074만원 = 집값 6억원',34,'var(--blue)',700)
    return svg(body)

def receipts(data,include_loan_comparison=False):
    body=text(36,40,'무주택 한 채 구입 · 전용 84㎡ · 감면 전 · 서울 중개보수 상한·일반과세 가정',25,weight=600)
    for i,price in enumerate([600000000,900000000,1200000000]):
        c=data['cases'][f'A_first_P{price}_C0']; costs=c['transaction_costs']; x=36+i*561
        body+=rect(x,70,546,280)+text(x+28,110,f'{price//100000000}억원 주택',32,'var(--blue)',700)
        lines=[('취득세',costs['acquisition_krw']),('지방교육세',costs['education_krw']),('중개보수·부가세',costs['with_vat_krw']),('기타 계획예산',costs['misc_plan_krw'])]
        for j,(label,value) in enumerate(lines):
            y=153+j*38;body+=text(x+28,y,label,24)+text(x+518,y,man(value),26,weight=600,anchor='end')
        body+=f'<path d="M{x+25} 291 H{x+521}" stroke="var(--line)" fill="none"/>'
        body+=text(x+28,327,'비용 합계',25,weight=600)+text(x+518,327,man(costs['total_krw']),33,'var(--blue)',700,'end')
    # The combined layout is a static stress specimen only; production CH05 uses receipts alone.
    if include_loan_comparison:body+=loan_table(data,394)
    return svg(body)

def loan_table(data,y):
    body=text(36,y,'가구 A · 수도권·규제지역 생애최초 · 인정 연소득 1억원 · 약정 4% / 심사 7% · 30년',24,weight=600)
    headers=[('집값',55),('필요대출',340),('대출상한',745),('추가현금',1160)]
    for label,x in headers:body+=text(x,y+44,label,24,'var(--muted)',600)
    for i,price in enumerate([600000000,900000000,1200000000]):
        c=data['cases'][f'A_first_P{price}_C0'];row_y=y+84+i*39
        body+=text(55,row_y,f'{price//100000000}억원',26,weight=600)
        for x,key in [(340,'required_loan_krw'),(745,'loan_ceiling_krw'),(1160,'cash_shortfall_krw')]:body+=text(x,row_y,eok(c[key]),26,'var(--blue)' if key=='loan_ceiling_krw' else 'var(--ink)',600)
        body+=text(1535,row_y,'담보 한도' if i==0 else 'DSR 한도',24,'var(--green)',600)
    return body

def loan_cases(data):
    """Separate CH06 source template, never mounted during fee narration."""
    return svg(loan_table(data,70))

def reset(data):
    c=data['reset']['case'];common=data['packet']['conditions']['common']
    first=Decimal(c['initial_monthly_krw']); after=Decimal(c['reset_monthly_krw'])
    budget=Decimal(common['housing_savings_budget_monthly_krw']);hold=Decimal(common['ownership_monthly_plan_krw'])
    body=text(36,40,'가구 B · 합산소득 8천만원 · 대출 3억9,074만원 · 30년 원리금균등 · 우대 전',25,weight=600)
    body+=rect(36,69,1668,270)
    body+=text(70,108,'대출접수일 기준 산식 · KB 2026.10.19 공시표 적용',24,'var(--muted)')
    body+='<path d="M90 190 H1630" stroke="var(--line)" stroke-width="7" fill="none"/>'
    initial_width=1540*int(c['initial_months'])/int(c['original_months']);split=90+initial_width
    body+=rect(90,160,initial_width,60,'var(--blue)',6)+rect(split,160,1540-initial_width,60,'var(--gold)',6)
    body+=text(90+initial_width/2,146,'처음 60개월 · 연 2.9%',30,'var(--blue)',700,'middle')
    body+=text((split+1630)/2,146,'남은 300개월 · 연 3.65%',30,'var(--gold-ink)',700,'middle')
    body+=text(90,253,'실행',25)+text(split,253,'60회 상환',25,weight=600,anchor='middle')+text(1630,253,'360회 상환',25,anchor='end')
    body+=text(70,302,f'60회 후 잔액 약 {eok(c["balance_after60_krw"])}  →  접수일 기준 가산 +0.75%p 적용',29,weight=600)
    body+=text(36,384,'월 주거·저축예산 300만원 · 보유비 30만원을 동일하게 배정한 계획 비교',25,weight=600)
    for i,(payment,label) in enumerate([(first,'처음 5년'),(after,'5년 이후')]):
        y=423+i*70;body+=text(36,y+30,label,26,weight=600)
        x=240;width=1420
        for amount,color in [(hold,'var(--muted)'),(payment,'var(--blue)'),(budget-hold-payment,'var(--green)')]:
            w=float(amount/budget)*width;body+=rect(x,y,w,42,color,2);x+=w
        body+=text(240,y+64,'보유비 30만원',22,'var(--muted)')
        body+=text(780,y+64,'월 상환 '+monthly(payment),25,'var(--blue)',600,'middle')
        body+=text(1660,y+64,'남길 저축 '+monthly(budget-hold-payment),25,'var(--green)',600,'end')
    return svg(body)

def caption_markup(cues):
    result=[]
    for i,c in enumerate(cues):
        lines=c['display_lines'];assert 1<=len(lines)<=2
        assert ' '.join(' '.join(lines).split())==' '.join(c['text'].split())
        result.append(f'<p id="cue{i:03d}" class="clip cue" data-start="{c["start_s"]}" data-duration="{c["end_s"]-c["start_s"]}" data-track-index="3"><span class="caption-lines">'+e('\n'.join(lines))+'</span></p>')
    return '\n'.join(result)

def load_measured_inputs(lock_path,timing_path,narration_handoff_path,audio_qa_path):
    """Future integration adapter: fails closed, never estimates or creates T() anchors."""
    files=[Path(p) for p in [lock_path,timing_path,narration_handoff_path,audio_qa_path]]
    if not all(p.is_file() for p in files):raise ValueError('Measured integration requires script lock, timing, narration handoff and audio QA')
    _,timing,handoff,qa=map(read,files)
    lock,script,_=load_script_lock(files[0])
    if qa.get('approved') is not True:raise ValueError('Independent audio QA is not approved')
    expected=lock['script_sha256']
    for record in [timing,handoff]:
        if record.get('script_sha256')!=expected:raise ValueError('Timing/voice script lock mismatch')
    chapters=timing.get('chapters',[])
    if len(chapters)!=10 or sum(len(c.get('paragraphs',[])) for c in chapters)!=45:raise ValueError('Actual 10-chapter / 45-paragraph timing required')
    bindings=read(OUT/'scene_bindings.json')['bindings']
    for chapter in chapters:
        audio=resolve_input(chapter['audio_file'])
        if not audio.resolve().is_relative_to((EP/'narration').resolve()):raise ValueError('Old episode body audio cannot be reused')
        if sha(audio)!=chapter['audio_sha256']:raise ValueError('Actual audio SHA mismatch')
        if not chapter.get('total_seconds',0)>0:raise ValueError('Missing measured chapter duration')
        for paragraph in chapter['paragraphs']:
            binding=next((b for b in bindings if b['paragraph']==paragraph['paragraph']),None)
            if not binding or binding['chapter']!=chapter['chapter']:raise ValueError('Unmapped native paragraph')
            if paragraph.get('offset_s') is None or not paragraph.get('measured_seconds',0)>0:raise ValueError('Unmeasured paragraph, no estimate fallback')
            cues=[c for c in chapter['cues'] if c['paragraph']==paragraph['paragraph']]
            compact=lambda s:''.join(s.split())
            if not cues or compact(''.join(c['text'] for c in cues))!=compact(binding['display_text']):raise ValueError('Native display cue conservation mismatch')
            if compact(''.join(c['spoken_text'] for c in cues))!=compact(binding['spoken_text']):raise ValueError('Native spoken cue conservation mismatch')
            for cue in cues:
                if cue.get('scene_id')!=binding['scene_id']:raise ValueError('Native cue scene mismatch')
                if cue.get('native_start_s') is None or cue.get('native_end_s') is None or not 0<=cue['start_s']<cue['end_s']<=chapter['total_seconds']:raise ValueError('Invalid native cue interval')
                lines=cue.get('display_lines',[])
                if not 1<=len(lines)<=2 or compact(''.join(lines))!=compact(cue['text']):raise ValueError('Native meaning cue display lines required')
    return {'script_sha256':expected,'timing_sha256':sha(files[1]),'narration_receipt_sha256':sha(files[2]),'audio_QA_sha256':sha(files[3]),'timing':timing}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    lock,script,lock_path=load_script_lock()
    rels=['brief.json','state.json','scenes.json','director/production-v1/locked_script.json','outputs/script-final-v2/script_v2.md','research/facts_v2.json','research/verified_case_packet.json','research/newborn_policy_addendum_v2.json','research/sources_current_v2.json','qa/content_v1_review.json','qa/newborn-delta-v2/review.json','writer/script_v2.md','writer/scene_proposals_v2.json','writer/handoff_v2.json','visual/assets.json','director/production-v1/media_assets.json']
    inputs={rel:sha(EP/rel) for rel in rels}
    script_sha='9658fc12dc76f67bb75d00e9c88170b167933ad8482dae1b752e4009d2aaf1a3'
    assert lock['script_sha256']==script_sha==sha(script),'Locked canonical script SHA changed'
    bind_approved_scenes(lock,script)
    packet=read(EP/'research/verified_case_packet.json'); facts=read(EP/'research/facts_v2.json'); reset_data=read(EP/'research/newborn_policy_addendum_v2.json')
    data={'packet':packet,'cases':{c['case_id']:c for c in packet['cases']},'reset':reset_data}
    source_assets=BASE/'outputs/private-production-v3/ch01/assets'
    local=OUT/'assets';(local/'fonts').mkdir(parents=True,exist_ok=True)
    for name in ['gsap.min.js','fonts/Pretendard-Regular.woff2','fonts/Pretendard-SemiBold.woff2','fonts/Pretendard-Bold.woff2','fonts/Pretendard-ExtraBold.woff2']:
        shutil.copy2(source_assets/name,local/name)
        inputs[str((source_assets/name).relative_to(ROOT)).replace('\\','/')]=sha(source_assets/name)
    for name in ['shell.css','runtime.js']:shutil.copy2(HERE/'templates'/name,local/name)
    media=read(EP/'director/production-v1/media_assets.json')
    media_proof=[]
    for asset in media['assets']:
        p=ROOT/asset['path'];assert sha(p)==asset['sha256'];media_proof.append({'asset_id':asset['asset_id'],'path':asset['path'],'sha256':sha(p),'read_only':True})
    visual_proof=[]
    for asset in read(EP/'visual/assets.json')['raster_assets']:
        p=ROOT/asset['path'];assert sha(p)==asset['sha256'];visual_proof.append({'asset_id':asset['asset_id'],'path':asset['path'],'sha256':sha(p),'allowed_chapters':[1] if asset['asset_id']=='HB01' else [8]})
    items=[
      ('cash',6,'6. 가격별 계산',cash(data),'자체 조건부 사례 · 2026.10.26 · 6억·84㎡·예비자금 3천만원·감면 전 비용 1,074만원',[
       ['이제 A가 6억 원 집을 사는 경우입니다.'],['보유자금에서 예비자금과 거래비용을 빼면 집값에 넣을 자기자금은 2억 926만 원,','필요한 대출은 3억 9,074만 원입니다.']]),
      ('fees_cases',5,'5. 거래비용',receipts(data,include_loan_comparison=True),'지방세법·서울시 중개보수 기준 / 검증 사례 2026.10.26 · 기타 150만원은 등기·채권 등 계획예산 · 차감 0은 보증심사 등 충족 가정',[
       ['채권의 즉시매도 부담, 등기수수료, 법무사보수와 인지 등은','계획용 예산 150만 원으로 묶겠습니다.'],['이 예산까지 포함한 총비용은 6억 원에서 1,074만 원,','9억 원에서 3,615만 원, 12억 원에서 4,902만 원입니다.']]),
      ('reset_budget',8,'8. 신생아 특례',reset(data),'주택도시기금·KB 2026.10.19 표 / 2026.10.26 검증 · 추가 출산·금리우대·중도상환 0 · 월 예산은 동일 계획 가정',[
       ['추가 출산·우대·중도상환을 적용하지 않은 기본 사례입니다.'],['60회 상환 뒤 잔액 약 3억 4,676만 원을','남은 300개월 동안 갚으면 월 약 176.4만 원입니다.']])]
    manifest=[];template=(HERE/'templates/scene.html').read_text(encoding='utf8')
    for ident,chapter,title,graphic,source,lines in items:
        directory=OUT/ident;directory.mkdir(exist_ok=True)
        for name in ['gsap.min.js','fonts/Pretendard-Regular.woff2','fonts/Pretendard-SemiBold.woff2','fonts/Pretendard-Bold.woff2','fonts/Pretendard-ExtraBold.woff2']:
            target=directory/'assets'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(local/name,target)
        source_scene={'cash':'S021','fees_cases':'S019','reset_budget':'S034R'}[ident]
        proposal=next(s for s in read(EP/'writer/scene_proposals_v2.json')['scenes'] if s['scene_id']==source_scene)
        cues=[{'id':f'PROVISIONAL_{ident}_{i+1}','source_scene_id':source_scene,'start_s':start,'end_s':end,'display_lines':line,'text':' '.join(line),'timing_basis':'PROVISIONAL_STATIC_TEMPLATE_NOT_NARRATION'} for i,(start,end,line) in enumerate([(0.4,4.4,lines[0]),(5.0,10.9,lines[1])])]
        for cue in cues:assert cue['text'] in proposal['display_text'],'Preview must use a verbatim writer v2 excerpt'
        values={'@@TITLE@@':e(title),'@@ID@@':ident,'@@GRAPHIC@@':graphic,'@@SOURCE@@':e(source),'@@CAPTIONS@@':caption_markup(cues),'@@CSS@@':(HERE/'templates/shell.css').read_text(encoding='utf8').replace('url(fonts/','url(assets/fonts/'),'@@RUNTIME@@':(HERE/'templates/runtime.js').read_text(encoding='utf8')}
        document=template
        for k,v in values.items():document=document.replace(k,v)
        (directory/'index.html').write_text(document,encoding='utf8')
        dump(directory/'timing.json',{'status':'PROVISIONAL','duration_s':12,'not_narration_timing':True,'cues':cues})
        manifest.append({'id':ident,'chapter':chapter,'script_scene_id':source_scene,'file':f'{ident}/index.html','html_sha256':sha(directory/'index.html'),'preview_at_s':6.0,'time_status':'PROVISIONAL','final_timing_assigned':False})
    dump(OUT/'source_preflight.json',{'status':'locked_content_static_templates_actual_audio_pending','preview_revision':'readability-v2','fees_cases_scope':'static worst-case style specimen only; actual CH05 receipts and CH06 loans are separate templates','provisional_script_sha256':script_sha,'provisional_script_content_approved':True,'script_path':script.relative_to(ROOT).as_posix(),'script_lock_sha256':sha(lock_path),'facts_count':len(facts['facts']),'inputs_sha256':inputs,'representatives':manifest,'media_readonly_verified':media_proof,'visual_readonly_verified':visual_proof,'script_lock':lock_path.relative_to(EP).as_posix(),'audio_revision':None,'timing_revision':None,'full_film_render_allowed':False,'new_paid_calls':0})
    dump(OUT/'data_bindings.json',{'status':'provisional_display_data','facts_sha256':sha(EP/'research/facts_v2.json'),'verified_case_packet_sha256':sha(EP/'research/verified_case_packet.json'),'reset_addendum_sha256':sha(EP/'research/newborn_policy_addendum_v2.json'),'preview_case_ids':['A_first_P600000000_C0','A_first_P900000000_C0','A_first_P1200000000_C0'],'B_reset_case':reset_data['case'],'v1_script_approved':False,'source_policy_date':'2026-10-26'})
    links=''.join(f'<li><a href="{i["file"]}">{i["id"]}</a> — PROVISIONAL / 정적 대표시안</li>' for i in manifest)
    (OUT/'index.html').write_text('<!doctype html><html lang="ko"><meta charset="utf-8"><title>매수가격 소스 사전점검</title><body><h1>템플릿·소스 사전점검</h1><p>대본 v2 양측 내용 검수 통과. 정적 시안의 모든 시간은 임시이며 실측 음성·타이밍 연결 대기 중입니다.</p><ul>'+links+'</ul></body></html>',encoding='utf8')
    print(json.dumps({'status':'templates_prepared','static_scenes':len(manifest),'full_render':False,'timing':'PROVISIONAL'}))

if __name__=='__main__':main()
