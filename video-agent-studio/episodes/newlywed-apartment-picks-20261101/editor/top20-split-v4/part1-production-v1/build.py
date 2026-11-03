"""Part1: frozen maps, licensed photos, spoken-price comparisons and native-word cues."""
from pathlib import Path
import argparse,hashlib,html,json,math,shutil,sys
H=Path(__file__).resolve().parent;E=H.parents[2];R=E.parents[2]
D=E/'director/top20-split-v4/part1-production-v1'
sys.path.insert(0,str(E/'editor/top20-explain-v3'))
from caption_tools import translated_index,norm
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
esc=lambda s:html.escape(str(s),quote=True)
def write(p,s):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf-8')
def save(p,x):write(p,json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def money(v):
    a,b=divmod(round(v),10000)
    return (f'{a}억'+(f'{b:,}만원'if b else'원'))if a else f'{b:,}만원'
def anchor(s,text):
    pos=norm(s['text']).find(norm(text))
    if pos<0:return s['start_s']
    i=translated_index(s['text'],s['reading_text'],pos)
    return next((w['start_s']for w in s['words']if w['sentence_normalized_char_end']>i),s['start_s'])

CSS='''
@font-face{font-family:Pretendard;src:url('assets/Pretendard-Regular.woff2')}@font-face{font-family:Pretendard;src:url('assets/Pretendard-Bold.woff2');font-weight:700}
*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;background:#f6f4ef;color:#173348;font-family:Pretendard,sans-serif}#main{position:relative;width:100%;height:100%;overflow:hidden}.scene{position:absolute;inset:0;width:100%;height:100%;overflow:hidden;background:#f6f4ef}.plate{position:absolute;inset:0;width:100%;height:100%}.mast{position:absolute;left:0;top:0;width:1920px;height:148px;background:#f6f4ef}.brand{position:absolute;left:60px;top:28px;font-size:23px}.title{position:absolute;left:60px;top:79px;font-size:47px;font-weight:700;line-height:1.15;width:970px}.count{position:absolute;right:62px;top:81px;font-size:33px;font-weight:700;color:#286cda}.tag{position:absolute;right:62px;top:30px;font-size:22px;color:#425b6d}.bottom-cover{position:absolute;left:0;top:922px;width:1920px;height:158px;background:#f6f4ef}.caption-bg{position:absolute;left:96px;top:942px;width:1728px;height:110px;background:white;border-radius:18px}.caption{position:absolute;left:126px;top:945px;width:1668px;height:104px;display:flex;align-items:center;justify-content:center;text-align:center;font-size:39px;line-height:1.3;letter-spacing:-.02em;padding:5px 12px;color:#173348}.panel{position:absolute;left:760px;top:205px;width:1100px;height:625px;border-radius:16px;overflow:hidden;background:white}.photo-panel{background:#183447;display:flex;align-items:center;justify-content:center}.photo-panel img{width:100%;height:100%;object-fit:contain}.photo-credit{position:absolute;left:18px;right:18px;bottom:14px;padding:11px 16px;font-size:20px;line-height:1.35;color:white;background:#173348eF;border-radius:8px}.price-panel{padding:36px 40px}.small{font-size:23px;line-height:1.35;color:#425b6d}.pane-title{font-size:35px;font-weight:700;margin:0 0 18px}.price-row{position:relative;margin-top:28px;padding:12px 0 20px;height:178px}.price-name{font-size:29px;font-weight:700;width:510px}.price-value{position:absolute;right:0;top:4px;font-size:48px;font-weight:700;color:#286cda}.price-n{font-size:23px;color:#425b6d;margin-top:10px}.bar-base{height:22px;width:100%;background:#e7edf0;border-radius:11px;margin-top:18px;overflow:hidden}.bar-fill{height:22px;border-radius:11px;width:calc(var(--pct)*var(--hf-grow,1));background:#286cda}.chart-foot{position:absolute;bottom:30px;left:40px;font-size:23px;color:#425b6d}.ring{position:absolute;width:46px;height:46px;border:4px solid #286cda;border-radius:50%;background:transparent;box-shadow:0 0 0 5px #ffffffbb;pointer-events:none}.focus-note{position:absolute;left:770px;top:154px;width:1080px;height:40px;font-size:26px;font-weight:700;background:#f6f4ef;line-height:1.35}.rank-strip{position:absolute;left:60px;top:123px;height:6px;width:1800px;background:#dae3e9}.rank-strip span{display:block;height:6px;background:#286cda}.full-card{position:absolute;left:60px;top:148px;width:1800px;height:760px}.intro-title{font-size:76px;line-height:1.25;font-weight:700;letter-spacing:-.04em}.intro-sub{font-size:32px;line-height:1.5;color:#425b6d}.mosaic{display:flex;gap:18px;position:absolute;left:0;right:0;top:330px;height:388px}.mosaic img{width:calc((100% - 36px)/3);height:388px;object-fit:cover;border-radius:16px}.scope-num{font-size:150px;font-weight:700;line-height:1.1;color:#286cda}.legend-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:24px;margin-top:32px}.legend-item{height:162px;background:white;border-radius:18px;padding:29px 30px;display:flex;align-items:center;gap:23px;font-size:33px;font-weight:700;border:3px solid #e0e6e8}.legend-dot{width:52px;height:52px;border-radius:50%;flex:none}.symbol-row{display:flex;gap:70px;margin-top:30px;font-size:29px;align-items:center}.symbol{display:inline-flex;width:42px;height:42px;align-items:center;justify-content:center;color:white;font-size:24px;margin-right:12px;border-radius:6px}.next-row{display:flex;gap:24px;margin-top:40px}.next-item{width:calc((100% - 48px)/3);height:280px;border-radius:24px;background:white;padding:32px;font-size:31px;line-height:1.45}.next-number{font-size:52px;font-weight:700;color:#286cda}.mini-chart{display:flex;height:106px;gap:16px;margin-top:20px;align-items:flex-end}.mini-chart span{width:90px;border-radius:8px 8px 0 0;background:#c7d9ef}.cta{display:flex;gap:28px;margin-top:60px}.cta span{padding:24px 50px;border-radius:18px;background:#286cda;color:white;font-size:42px;font-weight:700}.intro-credit{position:absolute;left:18px;bottom:10px;font-size:16px;background:#173348eF;color:white;padding:7px 10px;max-width:550px}
'''
CSS += '\n.rank-strip{top:140px}.focus-note{left:760px;top:150px;width:1100px;height:45px}\n'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--timing',type=Path,default=D/'locked_timing.json');ap.add_argument('--version',default='final-v1');ap.add_argument('--resume-incomplete',action='store_true');a=ap.parse_args()
    P=H/a.version
    assert not P.exists()or(a.resume_incomplete and not(P/'index.html').exists()and not(P/'build_receipt.json').exists()),'Preserve complete version; choose a new name'
    T=read(a.timing);assert T['timing_locked'] and T['part']==1
    script=read(D/'approved_part1_scene_proposals.json');assert sha(D/'approved_part1_scene_proposals.json')==T['source_scene_json_sha256']
    A=P/'assets';A.mkdir(parents=True,exist_ok=a.resume_incomplete);inputs=[]
    def stage(p,name):
        p=Path(p);dest=A/name
        if dest.exists():assert sha(p)==sha(dest),'Changed frozen asset'
        else:shutil.copy2(p,dest)
        assert sha(p)==sha(dest)
        inputs.append({'source':str(p),'dest':'assets/'+name,'sha256':sha(p)})
        return 'assets/'+name
    base=E/'editor/top20-explain-v3/main/v2-bgm/assets'
    for name in ['gsap.min.js','Pretendard-Regular.woff2','Pretendard-Bold.woff2']:stage(base/name,name)
    stage(R/T['audio_path'],'narration.wav')
    for b in T['brand_inserts']:stage(b['source_file'],'brand_'+b['kind']+'.mp4')
    photo={x['region_id']:x for x in read(E/'visual/top20-8min-v2/photo_assets_v2.json')['assets']}
    maps=read(E/'visual/top20-split-v4/map_assets.json')['assets']
    meta={(x['region_id'],x['mode']):x for x in maps};ss={s['scene_id']:s for s in script['scenes']}
    for i in range(11,21):
        rid=f'R{i:02d}'
        for mode in ['context','prices']:stage(E/Path(meta[rid,mode]['file']),rid+'_'+mode+'.png')
        assert sha(Path(photo[rid]['absolute_file']))==photo[rid]['sha256']
        stage(photo[rid]['absolute_file'],rid+'_photo'+Path(photo[rid]['absolute_file']).suffix.lower())
    # Reuse the installed registry component's paused-timeline growth model, styled for two real comparisons.
    component=R/'video-agent-studio/episodes/search-to-choice-shorts-20261029/editor/project/compositions/components/animated-bar-chart.html'
    write(P/'references/animated-bar-chart.html',component.read_text(encoding='utf-8'));inputs.append({'source':str(component),'sha256':sha(component),'use':'--hf-grow deterministic bar model; adapted to actual two-group data'})
    write(P/'style.css',CSS)
    hosts=[];story=[];anchors=[];photoaudit=[];priceaudit=[]
    def mast(title,tag='',count=''):
        return f'<div class="mast"><div class="brand">데이터로 보는 부동산 | 신혼부부가 사는 곳</div><div class="title">{esc(title)}</div><div class="tag">{esc(tag)}</div><div class="count">{esc(count)}</div></div>'
    def price_pane(scene,ts):
        sentence=next(v for v in scene['sentences']if v['map_phase']=='price_selected')
        vals=[]
        for f in sentence['source_fields']:
            if not f['path'].endswith('region_insights.json'):continue
            data=read(R/f['path'])
            for key in f['field'].strip('/').split('/'):data=data[int(key)]if isinstance(data,list)else data[key]
            if isinstance(data,dict):vals.append(data)
        assert len(vals)==2
        pid=scene['scene_id']+'-price';bs=[];an=[]
        distribution='median_manwon'not in vals[0]
        heading='단지별 가격대 분포'if distribution else('준공 시기별 거래 중위값'if 'build_cohorts'in sentence['source_fields'][0]['field']else'동별 거래 중위값')
        maximum=max(x.get('median_manwon',x.get('complex_n'))for x in vals)
        for j,v in enumerate(vals):
            label=v.get('dong',v.get('label','')).replace('2000년 이전 준공','2000년까지 준공')
            value=(str(v['complex_n'])+'단지')if distribution else money(v['median_manwon'])
            n=(f"지도 연결 {v['denominator']}단지 기준")if distribution else f"거래 {v['transaction_n']:,}건 · {v['complex_n']}단지"
            pct=100*v.get('median_manwon',v.get('complex_n'))/maximum
            color=v.get('color')
            if color is None:
                palette=['#3E82BD','#299D92','#BEA52D','#E3913D','#D75B58','#954B87']
                color=palette[sum(v['median_manwon']>=edge for edge in [50000,70000,100000,150000,200000])]
            rowid=pid+f'-row{j}'
            bs.append(f'<div class="price-row" id="{rowid}"><div class="price-name">{esc(label)}</div><div class="price-value" id="{rowid}-value">{esc(value)}</div><div class="price-n">{esc(n)}</div><div class="bar-base"><div class="bar-fill" id="{rowid}-bar" style="--pct:{pct:.7f}%;background:{color}"></div></div></div>')
            literal=(str(v['complex_n'])+'곳')if distribution else value
            at=anchor(ts,literal)-scene['_start']
            an.append(f"tl.fromTo('#{rowid}-value',{{opacity:0,y:12}},{{opacity:1,y:0,duration:.4}}, {at:.6f});tl.fromTo('#{rowid}-bar',{{'--hf-grow':0}},{{'--hf-grow':1,duration:.9,ease:'power2.out'}},{at:.6f});")
            anchors.append({'scene_id':scene['scene_id'],'kind':'price_value','text':literal,'global_s':at+scene['_start']})
        priceaudit.append({'scene_id':scene['scene_id'],'sentence_id':sentence['sentence_id'],'groups':vals,'distribution':distribution,'source_fields':[f for f in sentence['source_fields']if f['path'].endswith('region_insights.json')]})
        foot='전용 83~85㎡ · 2026.05~10 계약 · 11.03 조회'
        return f'<div id="{pid}" class="panel price-panel hf-catalog-animated-bar-chart"><div class="pane-title">{heading}</div><div class="small">같은 구 안에서 달라지는 예산 조건</div>{"".join(bs)}<div class="chart-foot">{foot}</div></div>',''.join(an)
    for s in T['scenes']:
        sid=s['scene_id'];st=s['start_s'];dur=s['duration_s'];original=ss[sid];body='';anim='';beats=[]
        if s.get('region_id'):
            rid=s['region_id'];reg=dict(original,_start=st);count=original['sentences'][0]['text'].split(',')[-1].strip().replace('입니다.','')
            count=next((m.group(0)for m in __import__('re').finditer(r'[\d,]+쌍',original['sentences'][0]['text'])),'')
            body=f'<img class="plate" src="../assets/{rid}_context.png"/><img class="plate" id="{sid}-points" src="../assets/{rid}_prices.png"/>'+mast(original['title'],'2024.11.01 신혼부부 거주 수',count)
            body+=f'<div class="rank-strip"><span style="width:{(21-s["rank"])/10*100:.0f}%"></span></div>'
            anim+=f"tl.fromTo('#{sid}-points',{{opacity:0}},{{opacity:1,duration:.7}},.25);"
            focused=next((v for v in s['sentences']if v['map_phase']=='focused_context'),None)
            photo_s=next(v for v in s['sentences']if v['map_phase']=='landmark_photo');photo_end=next((v['start_s']for v in s['sentences']if v['start_s']>photo_s['start_s']),photo_s['end_s']+.2)
            p=photo[rid];credit=f"사진: {p['source_or_prompt']['author']} · {p['license']['name']} · {p.get('photo_capture_year')or'자료사진'}"
            file=rid+'_photo'+Path(p['absolute_file']).suffix.lower();photoid=sid+'-photo'
            body+=f'<div id="{photoid}" class="panel photo-panel"><img src="../assets/{file}"/><div class="photo-credit">{esc(p["actual_place"])} · {esc(credit)}</div></div>'
            anim+=f"tl.fromTo('#{photoid}',{{opacity:0}},{{opacity:1,duration:.5}},{photo_s['start_s']-st:.6f});tl.to('#{photoid}',{{opacity:0,duration:.45}},{photo_end-st-.05:.6f});"
            photoaudit.append({'scene_id':sid,'region_id':rid,'actual_place':p['actual_place'],'source_sha256':p['sha256'],'start_s':photo_s['start_s'],'end_s':photo_end,'treatment':'object-fit:contain, unchanged color, letterbox','credit':credit})
            price_s=next(v for v in s['sentences']if v['map_phase']=='price_selected');price_end=next((v['start_s']for v in s['sentences']if v['start_s']>price_s['end_s'] and v['map_phase']=='focused_context'),s['end_s'])
            pane,growth=price_pane(reg,price_s);body+=pane
            anim+=f"tl.fromTo('#{sid}-price',{{opacity:0}},{{opacity:1,duration:.45}},{price_s['start_s']-st:.6f});"+growth
            if price_end<s['end_s']-.1:anim+=f"tl.to('#{sid}-price',{{opacity:0,duration:.4}},{price_end-st:.6f});"
            context=read(E/f'visual/top20-split-v4/atlas-context/{rid}_context.json')
            done=set()
            for v in s['sentences']:
                if v['map_phase']not in ['focused_context','focused_feature']:continue
                for f in context['schools']+context['stations']:
                    name=f['name'];literal=name+('역'if f in context['stations']else'')
                    match=__import__('re').search(r'(?<![가-힣A-Za-z0-9])'+__import__('re').escape(literal),v['text'])
                    if not match or (v['sentence_id'],name)in done:continue
                    done.add((v['sentence_id'],name));x,y=f['xy'];which='detail';bb=meta[rid,'prices']['detail_bounds_5179'];w,h,ox=1100,625,760
                    if not(bb[0]<=x<=bb[2]and bb[1]<=y<=bb[3]):which='overview';bb=meta[rid,'prices']['overview_bounds_5179'];w,h,ox=640,625,60
                    scale=min((w-24)/(bb[2]-bb[0]),(h-24)/(bb[3]-bb[1]));px=ox+(x-(bb[0]+bb[2])/2)*scale+w/2;py=205+((bb[1]+bb[3])/2-y)*scale+h/2
                    if not(ox+10<px<ox+w-10 and 215<py<820):continue
                    key=f'{sid}-ring{len(anchors)}';at=anchor(v,name);end=min(v['end_s'],at+5)
                    body+=f'<div id="{key}" class="ring" style="left:{px-23:.3f}px;top:{py-23:.3f}px"></div>'
                    anim+=f"tl.fromTo('#{key}',{{opacity:0,scale:1.7}},{{opacity:1,scale:1,duration:.45}},{at-st:.6f});tl.to('#{key}',{{opacity:0,duration:.35}},{end-st:.6f});"
                    anchors.append({'scene_id':sid,'kind':'facility','text':name,'global_s':at,'panel':which,'pixel_xy':[px,py],'source_xy':f['xy']})
            for v in s['sentences']:
                phase=v['map_phase'];label={'full_district':'구 전체 · 생활권 상세','focused_feature':'주거권과 주요 생활 거점','landmark_photo':p['actual_place'],'price_selected':'가격 차이를 읽는 비교','decision_context':'두 사람의 생활 조건과 연결','focused_context':'학교·역·단지의 실제 위치'}[phase]
                fid=v['sentence_id']+'-note';body+=f'<div id="{fid}" class="focus-note">{esc(label)}</div>'
                anim+=f"tl.fromTo('#{fid}',{{opacity:0}},{{opacity:1,duration:.2}},{v['start_s']-st:.6f});tl.to('#{fid}',{{opacity:0,duration:.12}},{v['end_s']-st+.05:.6f});"
                beats.append({'sentence_id':v['sentence_id'],'phase':phase,'start_s':v['start_s'],'end_s':v['end_s']})
        else:
            body=mast('신혼부부가 사는 곳 · 1편','수도권 20위 → 11위')
            for j,v in enumerate(s['sentences']):
                fid=v['sentence_id']+'-card';inner='';caption=''
                if s['scene_kind']=='intro' and j==0:
                    inner='<div class="intro-title">같은 예산,<div>어느 생활권까지?</div></div><div class="intro-sub" style="margin-top:18px">신혼부부 거주 순위 × 아파트 가격 × 생활권</div><div class="mosaic">'
                    for rid in ['R20','R17','R12']:
                        p=photo[rid];file=rid+'_photo'+Path(p['absolute_file']).suffix.lower()
                        inner+=f'<div style="position:relative;flex:1;overflow:hidden;border-radius:16px"><img style="width:100%;object-fit:contain;background:#183447" src="../assets/{file}"/><div class="intro-credit">{esc(p["actual_place"])} · {esc(p["source_or_prompt"]["author"])} · {esc(p["license"]["name"])}</div></div>'
                    inner+='</div>'
                elif s['scene_kind']=='intro' and j==1:
                    inner='<div class="intro-title">신혼부부가 많이 사는 구</div><div class="scope-num" style="margin-top:42px">20위 → 11위</div><div class="intro-sub" style="margin-top:42px">국가데이터처 2024년 신혼부부통계<div>수도권 53개 구 · 2024년 11월 1일 거주 기준</div></div>'
                elif s['scene_kind']=='intro' and j==2:
                    inner='<div class="intro-title" style="font-size:60px">점 하나 = 아파트 한 단지의 중위가격</div><div class="legend-grid">'
                    labels=['5억 미만','5~7억','7~10억','10~15억','15~20억','20억 이상'];colors=['#3E82BD','#299D92','#BEA52D','#E3913D','#D75B58','#954B87']
                    for k,(label,color)in enumerate(zip(labels,colors)):
                        inner+=f'<div id="legend-{k}" class="legend-item"><span class="legend-dot" style="background:{color}"></span>{label}</div>'
                        at=anchor(v,label)-st;anim+=f"tl.fromTo('#legend-{k}',{{opacity:.65}},{{opacity:1,duration:.35}},{at:.6f});"
                    inner+='</div><div class="symbol-row"><span><b class="symbol" style="background:#658773">학</b>학교</span><span><b class="symbol" style="background:#344e5e">역</b>지하철역</span><span><b style="color:#9b744b;font-size:43px;margin-right:12px">◆</b>상업시설</span></div>'
                elif s['scene_kind']=='intro':
                    inner='<img src="../assets/R20_prices.png" style="position:absolute;left:-60px;top:-148px;width:1920px;height:1080px"/><div style="position:absolute;left:-60px;top:-148px;width:1920px;height:148px;background:#f6f4ef;padding:70px 60px 0;font-size:45px;font-weight:700">구 전체 분포와 생활권 상세를 함께 읽습니다</div>'
                elif j==0:
                    inner='<div class="intro-title" style="font-size:61px">가격과 생활권을 함께 비교하세요</div><div class="next-row"><div class="next-item"><div class="next-number">예산</div>같은 구 안의<div>가격 차이</div><div class="mini-chart"><span style="height:46px"></span><span style="height:87px;background:#286cda"></span></div></div><div class="next-item"><div class="next-number">출근</div>두 사람의<div>실제 목적지</div></div><div class="next-item"><div class="next-number">일상</div>학교·장보기<div>주변 동선</div></div></div>'
                elif j==1:
                    inner='<div class="intro-sub">다음 편</div><div class="scope-num" style="margin-top:32px">10위 → 1위</div><div class="intro-title" style="font-size:54px;margin-top:42px">미추홀구부터 2024년 당시 인천 서구까지</div><div class="intro-sub" style="margin-top:28px">같은 가격 범례로 상위 10곳을 이어서 비교합니다.</div>'
                else:
                    inner='<div class="intro-title" style="font-size:70px">다음 생활권도 함께 비교하세요</div><div class="intro-sub" style="margin-top:34px">데이터로 보는 부동산</div><div class="cta"><span>구독</span><span style="background:#299D92">좋아요</span></div>'
                body+=f'<div id="{fid}" class="full-card">{inner}</div>'
                begin=0 if j==0 else v['start_s']-st;end=s['sentences'][j+1]['start_s']-st if j+1<len(s['sentences'])else dur
                anim+=(f"tl.set('#{fid}',{{opacity:1}},0);"if j==0 else f"tl.fromTo('#{fid}',{{opacity:0}},{{opacity:1,duration:.35}},{begin:.6f});")
                if end<dur-.01:anim+=f"tl.to('#{fid}',{{opacity:0,duration:.2}},{end-.01:.6f});"
                beats.append({'sentence_id':v['sentence_id'],'phase':v['map_phase'],'start_s':v['start_s'],'end_s':v['end_s']})
        body+='<div class="bottom-cover"></div>'
        if s['scene_kind']=='intro':
            body=body.replace('<div class="mast">',f'<div id="{sid}-mast" class="mast">',1)
            at=s['sentences'][3]['start_s']-st
            anim+=f"tl.set('#{sid}-mast',{{opacity:0}},{at:.6f});"
            b=T['brand_inserts'][0]
            anim+=f"tl.set('#{sid}-content',{{opacity:0}},{b['start_s']-st:.6f});tl.set('#{sid}-content',{{opacity:1}},{b['start_s']+b['duration_s']-st:.6f});"
        sub=f'<template><div id="{sid}" class="scene" data-composition-id="{sid}" data-width="1920" data-height="1080" data-duration="{dur:.9f}"><div id="{sid}-content" style="position:absolute;inset:0">{body}</div></div><script>(()=>{{const tl=gsap.timeline({{paused:true}});{anim}window.__timelines["{sid}"]=tl;}})();</script></template>'
        write(P/f'scenes/{sid}.html',sub)
        hosts.append(f'<div id="{sid}" class="clip" data-composition-id="{sid}" data-composition-src="scenes/{sid}.html" data-start="{st:.9f}" data-duration="{dur:.9f}" data-track-index="1"></div>')
        story.append({'scene_id':sid,'start_s':st,'end_s':s['end_s'],'beats':beats})
    # Stable caption box during narration only. No baked placeholder and no captions over brand.
    for i,(start,end)in enumerate([(0,T['brand_inserts'][0]['start_s']),(T['brand_inserts'][0]['start_s']+5,T['last_spoken_end_s'])]):
        hosts.append(f'<div id="caption-bg-{i}" class="clip caption-bg" data-start="{start:.9f}" data-duration="{end-start:.9f}" data-track-index="3"></div>')
    for i,c in enumerate(T['captions']):hosts.append(f'<div id="cue-{i}" class="clip caption" data-start="{c["start_s"]:.9f}" data-duration="{c["end_s"]-c["start_s"]:.9f}" data-track-index="4" data-track-kind="captions">{esc(c["text"])}</div>')
    for b in T['brand_inserts']:hosts.append(f'<video id="brand-{b["kind"]}" class="clip" src="assets/brand_{b["kind"]}.mp4" muted data-start="{b["start_s"]:.9f}" data-duration="{b["duration_s"]:.9f}" data-track-index="5" style="position:absolute;inset:0;width:100%;height:100%;z-index:20"></video>')
    hosts.append(f'<audio id="main-narration" class="clip" src="assets/narration.wav" data-start="0" data-duration="{T["total_s"]:.9f}" data-track-index="6"></audio>')
    fit="document.fonts.ready.then(()=>{for(const el of document.querySelectorAll('.caption')){let n=39;while((el.scrollHeight>el.clientHeight||el.scrollWidth>el.clientWidth)&&n>32){el.style.fontSize=(--n)+'px'}}});"
    root=f'<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8"/><link rel="stylesheet" href="style.css"/><script src="assets/gsap.min.js"></script></head><body><div id="main" data-composition-id="main" data-width="1920" data-height="1080" data-duration="{T["total_s"]:.9f}">{"".join(hosts)}</div><script>window.__timelines["main"]=gsap.timeline({{paused:true}});{fit}</script></body></html>'
    write(P/'index.html',root)
    save(P/'hyperframes.json',{'name':'newlywed-top20-part1','width':1920,'height':1080,'fps':30})
    save(P/'storyboard.json',story);save(P/'anchor_audit.json',anchors);save(P/'photo_audit.json',photoaudit);save(P/'price_audit.json',priceaudit)
    save(P/'input_manifest.json',{'timing_sha256':sha(a.timing),'script_sha256':T['source_scene_json_sha256'],'assets':inputs,'new_paid_calls':0,'cash_cost_krw':0})
    save(P/'build_receipt.json',{'status':'built_actual_timing_pending_check','version':a.version,'project':str(P),'scene_count':12,'sentence_count':85,'captions':len(T['captions']),'duration_s':T['total_s'],'timing_locked':True,'photo_count':len(photoaudit),'price_comparisons':len(priceaudit),'brand_video_muted':True,'actual_listening':False})
    save(H/'ownership_transfer.json',{'from':'stopped_editor_worker','to':'director_local','reason':'no files produced at checkpoint; parent resumes concrete builder','owned_folder':str(H)})
    print(json.dumps({'project':str(P),'scene_count':12,'captions':len(T['captions']),'duration_s':T['total_s'],'photos':len(photoaudit),'comparisons':len(priceaudit)},ensure_ascii=False))
if __name__=='__main__':main()
