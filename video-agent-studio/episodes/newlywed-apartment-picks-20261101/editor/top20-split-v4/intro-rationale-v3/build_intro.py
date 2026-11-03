"""Native HyperFrames intro: housing question -> residency data -> ten regions -> map."""
from pathlib import Path
import argparse,csv,hashlib,html,json,os,shutil,sys
H=Path(__file__).resolve().parent;E=H.parents[2];R=E.parents[2];D=E/'director/top20-split-v4/part1-intro-v3'
sys.path.insert(0,str(E/'editor/top20-explain-v3'))
from caption_tools import norm,translated_index
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
esc=lambda x:html.escape(str(x),quote=True)
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(x,encoding='utf-8')
def save(p,x):write(p,json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def at(s,word):
    p=norm(s['text']).find(norm(word))
    if p<0:return s['start_s']
    idx=translated_index(s['text'],s['reading_text'],p)
    return next((w['start_s']for w in s['words']if w['sentence_normalized_char_end']>idx),s['start_s'])

def tower(x,y,w,h,color='#86add6',key=''):
    d=round(w*.28);windows=[]
    for row in range(max(2,round(h/34))):
        for col in range(3):
            wx=x+12+col*(w-20)/3;wy=y-h+16+row*30
            if wy+12<y-12:windows.append(f'<rect x="{wx:.2f}" y="{wy:.2f}" width="10" height="13" rx="2" fill="{("#ffe5a3"if(row+col)%3==0 else"#d8eafb")}"/>')
    return f'<g id="{key}" class="tower"><ellipse cx="{x+w*.65}" cy="{y+14}" rx="{w*.9}" ry="17" fill="#0e2535" opacity=".18"/><polygon points="{x},{y-h} {x+w},{y-h-14} {x+w+d},{y-h-2} {x+d},{y-h+12}" fill="#c9dcf1"/><polygon points="{x+w},{y-h-14} {x+w+d},{y-h-2} {x+w+d},{y-8} {x+w},{y}" fill="#4078b4"/><rect x="{x}" y="{y-h}" width="{w}" height="{h}" rx="3" fill="{color}"/>{"".join(windows)}<rect x="{x+w*.42}" y="{y-25}" width="17" height="25" rx="2" fill="#285c90"/></g>'

def town(prefix='town'):
    towers=''.join(tower(*values,key=f'{prefix}-{i}')for i,values in enumerate([(220,420,93,205),(385,363,81,166),(470,520,116,277),(675,450,91,195),(803,510,110,258)]))
    return f'<svg width="100%" height="100%" viewBox="0 0 1100 680" aria-label="주거 지역을 나타내는 입체 아파트 그래픽"><ellipse cx="570" cy="558" rx="480" ry="100" fill="#286cda" opacity=".12"/><path d="M90 520L500 300L1040 530L590 650Z" fill="#dce9f7" stroke="#6998cb" stroke-width="3"/><path d="M220 510L710 595 M415 375L905 565 M345 610L760 398" fill="none" stroke="#a9c9e9" stroke-width="8"/>{towers}<circle cx="630" cy="490" r="27" fill="#286cda" stroke="#f6f4ef" stroke-width="6"/><path d="M618 491L627 500L644 480" fill="none" stroke="#fff" stroke-width="5"/></svg>'

CSS='''
@font-face{font-family:Pretendard;src:url('assets/Pretendard-Regular.woff2')}@font-face{font-family:Pretendard;src:url('assets/Pretendard-Bold.woff2');font-weight:700}
*{box-sizing:border-box}html,body{width:100%;height:100%;margin:0;background:#f6f4ef;color:#173348;font-family:Pretendard,sans-serif}#intro{position:relative;width:100%;height:100%;overflow:hidden}.frame{position:absolute;inset:0;overflow:hidden}.scene-inner{position:absolute;inset:0;perspective:1400px}.navy{background:#142e42;color:#f6f4ef}.paper{background:#f6f4ef;color:#173348}.eyebrow{position:absolute;left:96px;top:49px;font-size:24px;letter-spacing:.1em;font-weight:700}.section-number{position:absolute;right:98px;top:45px;font-size:24px;color:#6c9ed6}.grid{position:absolute;inset:0;background-image:linear-gradient(#84acd51a 1px,transparent 1px),linear-gradient(90deg,#84acd51a 1px,transparent 1px);background-size:64px 64px;opacity:.65}.glow{position:absolute;left:800px;top:170px;width:950px;height:700px;border-radius:50%;background:radial-gradient(ellipse,#286cda36,transparent 70%)}.hero-copy{position:absolute;left:96px;top:180px;width:940px;z-index:2}.hero-pre{font-size:43px;color:#c1d5ea;margin-bottom:22px}.hero-line{font-size:108px;line-height:1.13;font-weight:700;letter-spacing:-.045em}.hero-line span{display:inline-block}.hero-secondary{font-size:31px;margin-top:30px;color:#c1d5ea}.hero-art{position:absolute;left:800px;top:170px;width:1040px;height:640px;transform-style:preserve-3d}.underword{height:9px;width:540px;background:#e6b868;border-radius:6px;margin-top:26px;transform-origin:0 50%}.tag{position:absolute;padding:14px 24px;border-radius:100px;background:#274b6b;color:#f6f4ef;font-size:25px;font-weight:700;border:2px solid #5786b1}.hud{position:absolute;left:98px;bottom:173px;display:flex;align-items:center;gap:20px;font-size:23px;color:#c1d5ea}.hud i{display:block;width:11px;height:11px;border-radius:50%;background:#e6b868}.big-title{position:absolute;left:96px;top:124px;font-size:78px;font-weight:700;line-height:1.16;letter-spacing:-.035em;width:1740px}.mission-town{position:absolute;left:40px;top:235px;width:850px;height:580px}.pipeline{position:absolute;left:915px;top:330px;width:880px;height:410px}.pipeline-line{position:absolute;left:48px;top:121px;width:750px;height:5px;background:#bed0e5;transform-origin:0 50%}.pipe-node{position:absolute;top:40px;width:240px;height:290px}.pipe-icon{width:146px;height:146px;display:flex;align-items:center;justify-content:center;border:4px solid #286cda;border-radius:50%;background:#e8eff7;font-size:64px;color:#286cda;font-weight:700;margin:0 auto 24px}.pipe-label{font-size:39px;font-weight:700;text-align:center}.pipe-note{font-size:25px;color:#425b6d;text-align:center;margin-top:12px}.datum-title{position:absolute;left:96px;top:126px;font-size:78px;font-weight:700;line-height:1.16;letter-spacing:-.035em}.data-world{position:absolute;left:55px;top:280px;width:1810px;height:545px;perspective:1500px}.data-camera{width:100%;height:100%;transform-style:preserve-3d}.stat-source{position:absolute;left:98px;top:850px;font-size:23px;line-height:1.4;color:#bdd0e4}.selected-count{position:absolute;right:100px;top:125px;text-align:right;font-size:80px;font-weight:700;color:#e6b868}.next-copy{position:absolute;left:96px;top:237px;width:620px;font-size:45px;line-height:1.55;font-weight:700}.next-copy .blue{color:#286cda}.roadmap-art{position:absolute;left:720px;top:258px;width:1110px;height:540px}.road-step{position:absolute;border-radius:17px;background:#e6eef7;border:3px solid #d0dfef;font-size:31px;font-weight:700;padding:22px 28px}.road-step small{display:block;font-size:23px;font-weight:400;color:#425b6d;margin-top:7px}.price-ribbon{position:absolute;left:740px;top:435px;display:grid;grid-template-columns:repeat(3,315px);gap:22px}.price-cell{height:115px;border-radius:15px;background:#fff;padding:25px 18px;display:flex;align-items:center;gap:18px;font-size:34px;font-weight:700;border:2px solid #dde4ea}.price-dot{width:39px;height:39px;border-radius:50%;flex:none}.legend-house{position:absolute;left:55px;top:260px;width:660px;height:530px}.method-note{position:absolute;left:96px;top:850px;font-size:23px;color:#425b6d}.bridge-map{position:absolute;inset:0;width:1920px;height:1080px}.bridge-cover{position:absolute;left:0;top:0;width:1920px;height:922px;background:#142e42}.bridge-rank{position:absolute;left:96px;top:210px;font-size:178px;font-weight:700;color:#e6b868;line-height:1.05}.bridge-title{position:absolute;left:96px;top:435px;font-size:100px;font-weight:700;color:#f6f4ef}.bridge-sub{position:absolute;left:100px;top:585px;font-size:38px;color:#c1d5ea}.caption-box{position:absolute;left:96px;top:942px;width:1728px;height:110px;background:#fff;border-radius:18px;z-index:30}.caption{position:absolute;left:120px;top:946px;width:1680px;height:102px;display:flex;align-items:center;justify-content:center;text-align:center;font-size:39px;line-height:1.25;letter-spacing:-.02em;padding:6px;color:#173348;z-index:31}.progress-line{position:absolute;left:96px;top:890px;width:1728px;height:3px;background:#7894ae44}.progress-fill{height:3px;width:100%;background:#286cda;transform-origin:0 50%}
'''
CSS+='\n.pipeline-line{left:120px;top:111px;width:590px;height:4px}.road-step{width:285px;min-height:126px}\n'
CSS+='\n.section-number{color:#3e6c9c}.legend-point{position:absolute;left:335px;top:500px;width:120px;height:120px;border-radius:50%;border:12px solid #fff;background:#3e82bd;box-shadow:0 0 0 15px #dce7f0}.legend-point-label{position:absolute;left:242px;top:690px;font-size:40px;font-weight:700}\n'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--version',default='project');args=ap.parse_args()
    P=H/args.version;assert not(P/'index.html').exists(),'Use a new source revision for a completed build'
    A=P/'assets';A.mkdir(parents=True,exist_ok=True);T=read(D/'locked_timing.json');ss=T['intro_sentences'];S=[s['start_s']for s in ss];B=T['brand_intro'];end=T['intro_end_s'];duration=T['prefix_end_s'];inputs=[]
    def stage(source,name):
        source=Path(source);dest=A/name
        if dest.exists():assert sha(source)==sha(dest)
        else:os.link(source,dest)
        inputs.append({'source':str(source),'dest':'assets/'+name,'sha256':sha(source)})
    oldassets=E/'editor/top20-split-v4/part1-production-v1/final-v3/assets'
    for name in ['gsap.min.js','Pretendard-Regular.woff2','Pretendard-Bold.woff2']:stage(oldassets/name,name)
    stage(T['original_video'],'original_body.mp4');stage(T['master_audio'],'master_audio.wav');stage(B['source_video'],'brand_intro.mp4')
    # The bridge uses the exact old video's silent pre-region frame, so the handoff keeps the same map geometry.
    bridge=D/'media/bridge_map.png'
    if not bridge.exists():
        import subprocess
        ff=R/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
        subprocess.run([str(ff),'-v','error','-ss',str(T['old_body_cut_s']),'-i',T['original_video'],'-frames:v','1',str(bridge)],check=True)
    stage(bridge,'bridge_map.png')
    rows=list(csv.DictReader((R/'analysis/newlywed_region_2024/capital_gu_ranking.csv').open(encoding='utf-8-sig')));assert len(rows)==53
    expected={r['rank']:r for r in read(E/'research/top20-8min-v2/top20.json')['regions']}
    for r in rows:
        if 11<=int(r['rank'])<=20:assert int(r['newlywed_couples'])==expected[int(r['rank'])]['newlywed_couples']
    write(P/'style.css',CSS)
    parts=[];motion=[];audit=[]
    def slot(key,start,finish,body,theme='paper'):
        parts.append(f'<div class="clip frame {theme}" id="{key}" data-start="{start:.9f}" data-duration="{finish-start:.9f}" data-track-index="1"><div id="{key}-inner" class="scene-inner">{body}</div></div>')
    eyebrow='<div class="eyebrow">데이터로 보는 부동산</div>'
    hook=eyebrow+'<div class="grid" id="hook-grid"></div><div class="glow" id="hook-glow"></div><div class="hero-copy"><div class="hero-pre">우리 예산으로 집을 산다면</div><div class="hero-line"><span id="hook-word1">어느 동네부터</span><div id="hook-word2">찾아볼까요?</div></div><div class="underword" id="hook-underline"></div><div class="hero-secondary" id="hook-support">지역을 고르는 첫 기준, 데이터</div></div><div class="hero-art" id="hook-town">'+town('hook-building')+'</div><div class="tag" id="tag-budget" style="left:1180px;top:240px">내 예산</div><div class="tag" id="tag-life" style="left:1510px;top:660px">우리 생활권</div><div class="hud"><i></i>신혼부부의 집 찾기, 여기서부터</div>'
    slot('hook',0,B['start_s'],hook,'navy')
    motion += ["tl.fromTo('#hook-town',{opacity:0,scale:.74,rotationY:-18,y:70},{opacity:1,scale:1,rotationY:0,y:0,duration:1.05,ease:'power3.out'},.1);",
      "tl.fromTo('#hook-word1',{y:100,opacity:0},{y:0,opacity:1,duration:.55,ease:'power4.out'},.15);",
      "tl.fromTo('#hook-word2',{x:110,opacity:0},{x:0,opacity:1,duration:.6,ease:'expo.out'},.48);",
      "tl.fromTo('#hook-underline',{scaleX:0},{scaleX:1,duration:.65,ease:'power2.inOut'},.65);",
      "tl.fromTo('#hook-support',{y:25,opacity:0},{y:0,opacity:1,duration:.45},1.1);",
      "tl.fromTo('#hook-town .tower',{y:80,opacity:0},{y:0,opacity:1,duration:.55,stagger:.09,ease:'back.out(1.25)'},.2);",
      "tl.fromTo('#tag-budget',{x:60,y:-30,opacity:0},{x:0,y:0,opacity:1,duration:.65,ease:'power3.out'},.8);",
      "tl.fromTo('#tag-life',{x:80,y:20,opacity:0},{x:0,y:0,opacity:1,duration:.65,ease:'power3.out'},1.25);",
      f"tl.to('#hook-town',{{y:-13,duration:1.7,ease:'sine.inOut',yoyo:true,repeat:1}},1.2);tl.to('#hook-town',{{rotationY:7,scale:1.025,duration:1.1,ease:'sine.inOut'}},1.7);tl.to('#hook-glow',{{scale:1.13,duration:2.8,ease:'sine.inOut'}},.2);",
      f"tl.to('#hook-inner',{{opacity:0,duration:.22}},{B['start_s']-.22:.9f});"]
    purpose=eyebrow+'<div class="section-number">01 / 집 찾기의 순서</div><div class="big-title">우리에게 맞는 집을 찾는 과정</div><div class="mission-town" id="mission-town">'+town('mission-building')+'</div><div class="pipeline"><div id="mission-line" class="pipeline-line"></div>'
    for i,(symbol,label,note)in enumerate([('地','지역','어느 동네부터'),('₩','가격대','내 예산에 맞춰'),('집','아파트','비교할 후보')]):
        # Geometric housing/data symbols use text only as labels, never as fabricated floorplans.
        if i==0:symbol='<svg width="78" height="78" viewBox="0 0 100 100"><path d="M50 93C35 70 17 54 17 35A33 33 0 0 1 83 35C83 54 65 70 50 93Z" fill="#286cda"/><circle cx="50" cy="35" r="13" fill="#e8eff7"/></svg>'
        elif i==2:symbol='<svg width="88" height="88" viewBox="0 0 100 100"><path d="M12 88V34L48 18V88M48 88V9L87 26V88Z" fill="#286cda"/><path d="M23 43H34M23 57H34M23 71H34M59 29H72M59 44H72M59 59H72M59 74H72" stroke="#e8eff7" stroke-width="7"/></svg>'
        purpose+=f'<div class="pipe-node" id="purpose-{i}" style="left:{i*295}px"><div class="pipe-icon" style="font-size:{40 if i!=1 else 70}px">{symbol}</div><div class="pipe-label">{label}</div><div class="pipe-note">{note}</div></div>'
    purpose+='</div>'
    slot('purpose',B['start_s']+5,S[2],purpose)
    motion += [f"tl.fromTo('#mission-town',{{opacity:0,rotationY:16,scale:.83,y:40}},{{opacity:1,rotationY:0,scale:1,y:0,duration:.8,ease:'power3.out'}},{S[1]:.9f});",
      f"tl.fromTo('#mission-line',{{scaleX:0}},{{scaleX:1,duration:1.4,ease:'power2.inOut'}},{S[1]+.3:.9f});"]
    for i in range(3):motion.append(f"tl.fromTo('#purpose-{i}',{{opacity:0,y:40,scale:.85}},{{opacity:1,y:0,scale:1,duration:.55,ease:'back.out(1.3)'}},{S[1]+.3+i*.3:.9f});")
    # One persistent data object spans paragraphs 3–5, so 53 rows become the selected ten without a slide reset.
    data=eyebrow+'<div class="grid"></div><div class="glow" id="data-glow"></div>'
    for i,text in [(2,'지역을 고르는 기준은, 데이터'),(3,'신혼부부가 실제로 사는 곳'),(4,'이번에는 20위 → 11위')]:
        data+=f'<div class="datum-title" id="data-title-{i}">{text}</div>'
        motion.append(f"tl.fromTo('#data-title-{i}',{{y:28,opacity:0}},{{y:0,opacity:1,duration:.4,ease:'power3.out'}},{S[i]:.9f});")
        if i<4:motion.append(f"tl.to('#data-title-{i}',{{opacity:0,duration:.2}},{S[i+1]-.2:.9f});")
    data+='<div class="selected-count" id="count-53">53개 구</div><div class="selected-count" id="count-10">10개 지역</div><div class="data-world"><div class="data-camera" id="data-camera"><svg width="1810" height="545" viewBox="0 0 1810 545" style="overflow:visible">'
    for i,r in enumerate(rows):
        x=85+i%9*187;y=28+i//9*82;rank=int(r['rank']);selected=11<=rank<=20
        name=r['region'].replace('부천시 ','').replace('용인시 ','').replace('수원시 ','')
        data+=f'<g transform="translate({x},{y})"><g id="record-{rank}" class="record"><rect width="153" height="68" rx="10" fill="{("#e8f1fc"if selected else"#26465e")}" stroke="{("#709fd1"if selected else"#43617a")}" stroke-width="2"/><text x="14" y="26" fill="{("#173348"if selected else"#d1deec")}" font-size="19" font-weight="700">{esc(name)}</text><text x="14" y="51" fill="{("#286cda"if selected else"#a8bdd2")}" font-size="17">{int(r["newlywed_couples"]):,}쌍</text><text id="rank-label-{rank}" x="0" y="-10" fill="#f6f4ef" font-size="20" font-weight="700">{rank}위</text></g></g>'
        motion.append(f"tl.set('#record-{rank}',{{x:0,y:55,scale:1,opacity:0}},0);tl.to('#record-{rank}',{{opacity:1,y:0,duration:.45,ease:'power3.out'}},{S[2]+.25+i*.012:.9f});")
        if selected:
            j=20-rank;targetx=160+j%5*328;targety=90+j//5*220
            motion.append(f"tl.to('#record-{rank}',{{x:{targetx-x},y:{targety-y},scale:1.65,transformOrigin:'0 0',duration:1.05,ease:'power3.inOut'}},{S[4]+j*.045:.9f});")
            motion.append(f"tl.fromTo('#rank-label-{rank}',{{opacity:0}},{{opacity:1,duration:.35}},{S[4]+.8+j*.045:.9f});")
        else:
            motion.append(f"tl.to('#record-{rank}',{{opacity:0,scale:.7,duration:.6,ease:'power2.in'}},{S[4]:.9f});")
            motion.append(f"tl.set('#rank-label-{rank}',{{opacity:0}},0);")
    data+='</svg></div></div><div class="stat-source">국가데이터처 · 2024.11.01 거주 기준 · 수도권 53개 구<div>신혼부부 거주 수로 지역을 고르고, 실거래가로 예산을 비교합니다.</div></div>'
    slot('data',S[2],S[5],data,'navy')
    motion += [f"tl.fromTo('#data-camera',{{rotationY:-11,scale:.88}},{{rotationY:0,scale:1,duration:1.2,ease:'power3.out'}},{S[2]:.9f});",
      f"tl.fromTo('#count-53',{{opacity:0,y:25}},{{opacity:1,y:0,duration:.5}},{S[3]:.9f});tl.to('#count-53',{{opacity:0,y:-20,duration:.3}},{S[4]:.9f});",
      f"tl.fromTo('#count-10',{{opacity:0,y:30}},{{opacity:1,y:0,duration:.5,ease:'power3.out'}},{S[4]+.4:.9f});tl.to('#data-glow',{{scale:1.14,duration:8,ease:'sine.inOut'}},{S[2]:.9f});"]
    roadmap=eyebrow+'<div class="section-number">02 / 이어지는 지역별 이야기</div><div class="big-title">다음은, 그 지역 안으로</div><div class="next-copy"><div>지역 후보를 고르고</div><div class="blue">생활권을 살펴본 뒤</div><div>예산별 단지를 비교합니다</div></div><div class="roadmap-art" id="roadmap-art">'+town('road-building')
    for i,(label,note)in enumerate([('지역 후보','이번 20~11위 · 다음 10~1위'),('생활권','출근·학교·장보기'),('예산별 아파트','실거래 가격으로 비교')]):
        roadmap+=f'<div id="road-step-{i}" class="road-step" style="left:{i*350}px;top:{355-i*110}px">{label}<small>{note}</small></div>'
    roadmap+='</div>'
    slot('roadmap',S[5],S[6],roadmap)
    motion.append(f"tl.fromTo('#roadmap-art',{{opacity:0,rotationY:-12,scale:.88}},{{opacity:1,rotationY:0,scale:1,duration:.8,ease:'power3.out'}},{S[5]:.9f});")
    for i in range(3):motion.append(f"tl.fromTo('#road-step-{i}',{{opacity:0,x:40,y:40}},{{opacity:1,x:0,y:0,duration:.6,ease:'power3.out'}},{S[5]+.4+i*.5:.9f});")
    colors=['#3E82BD','#299D92','#BEA52D','#E3913D','#D75B58','#954B87'];labels=['5억 미만','5~7억','7~10억','10~15억','15~20억','20억 이상']
    method=eyebrow+'<div class="section-number">03 / 지도를 읽는 방법</div><div class="big-title">집 한 단지 → 지도 점 하나</div><div id="legend-house" class="legend-house">'+town('legend-building')+'</div><div class="price-ribbon">'
    for i,(label,color)in enumerate(zip(labels,colors)):
        method+=f'<div class="price-cell" id="price-band-{i}"><div class="price-dot" style="background:{color}"></div>{label}</div>'
        motion.append(f"tl.fromTo('#price-band-{i}',{{opacity:0,x:-30,scale:.9}},{{opacity:1,x:0,scale:1,duration:.4,ease:'power3.out'}},{S[6]+.5+i*.18:.9f});")
    method+='</div><div class="legend-point" id="legend-single-point"></div><div class="legend-point-label" id="legend-point-label">한 단지 · 한 점</div><div class="method-note">전용83~85㎡ · 2026.05~10 계약 · 2026.11.03 조회 · 10월은 조회일까지 신고분</div>'
    slot('method',S[6],S[7],method)
    motion.append(f"tl.fromTo('#legend-house',{{opacity:0,scale:.8,rotationY:15}},{{opacity:1,scale:1,rotationY:0,duration:.7,ease:'power3.out'}},{S[6]:.9f});")
    motion.append(f"tl.to('#legend-house',{{opacity:0,scale:.35,x:80,duration:.8,ease:'power3.inOut'}},{S[6]+.8:.9f});tl.fromTo('#legend-single-point',{{opacity:0,scale:.2}},{{opacity:1,scale:1,duration:.6,ease:'back.out(1.3)'}},{S[6]+1.05:.9f});tl.fromTo('#legend-point-label',{{opacity:0,y:15}},{{opacity:1,y:0,duration:.4}},{S[6]+1.35:.9f});")
    bridge='<img class="bridge-map" src="assets/bridge_map.png"/><div class="bridge-cover" id="bridge-cover"></div><div id="bridge-copy"><div class="bridge-rank">20위</div><div class="bridge-title">부천 원미구</div><div class="bridge-sub">신혼부부 7,365쌍이 사는 곳</div></div>'
    slot('bridge',S[7],end,bridge)
    motion += [f"tl.fromTo('#bridge-copy',{{opacity:0,x:90}},{{opacity:1,x:0,duration:.55,ease:'power4.out'}},{S[7]:.9f});",
      f"tl.to('#bridge-copy',{{opacity:0,scale:.92,duration:.55,ease:'power2.inOut'}},{end-1:.9f});tl.to('#bridge-cover',{{opacity:0,duration:.65,ease:'power2.inOut'}},{end-.85:.9f});"]
    # Framework-owned media, not native playback; muted pictures because the master already carries brand/voice/music.
    parts.append(f'<video id="brand-intro" class="clip" src="assets/brand_intro.mp4" muted data-start="{B["start_s"]:.9f}" data-duration="5" data-track-index="2" style="position:absolute;inset:0;width:100%;height:100%"></video>')
    parts.append(f'<video id="preserved-body-prefix" class="clip" src="assets/original_body.mp4" muted data-media-start="{T["old_body_cut_s"]:.9f}" data-start="{end:.9f}" data-duration="{duration-end:.9f}" data-track-index="2" style="position:absolute;inset:0;width:100%;height:100%"></video>')
    for i,(a,b)in enumerate([(0,B['start_s']),(B['start_s']+5,end)]):parts.append(f'<div class="clip caption-box" id="caption-box-{i}" data-start="{a:.9f}" data-duration="{b-a:.9f}" data-track-index="3"></div>')
    for i,c in enumerate([c for c in T['captions']if c['sentence_id'].startswith('P01-INTRO-V3')]):parts.append(f'<div class="clip caption" id="caption-{i}" data-start="{c["start_s"]:.9f}" data-duration="{c["end_s"]-c["start_s"]:.9f}" data-track-index="4" data-track-kind="captions">{esc(c["text"])}</div>')
    parts.append(f'<audio class="clip" id="master-audio" src="assets/master_audio.wav" data-start="0" data-duration="{duration:.9f}" data-track-index="5"></audio>')
    src=f'<!doctype html><html lang="ko"><head><meta charset="utf-8"/><link rel="stylesheet" href="style.css"/><script src="assets/gsap.min.js"></script></head><body><div id="intro" data-composition-id="intro" data-width="1920" data-height="1080" data-duration="{duration:.9f}">{"".join(parts)}</div><script>const tl=gsap.timeline({{paused:true}});{"".join(motion)}window.__timelines["intro"]=tl;</script></body></html>'
    src=src.replace('fill="#286cda" font-size="17"','fill="#1f61be" font-size="17"')
    write(P/'index.html',src);save(P/'hyperframes.json',{'name':'part1-intro-rationale-v3','width':1920,'height':1080,'fps':30})
    save(P/'build_receipt.json',{'status':'built_pending_source_check','prefix_end_s':duration,'intro_end_s':end,'native_voice_sentences':8,'timeline_actual':True,'source_registry_primitive':'../compositions/ui-3d-reveal.html','registry_reused_features':'paused timeline, perspective rotationY+scale+y multi-axis entrance; no registry commercial copy/assets shown','new_data_claims':False,'actual_listening':False})
    save(P/'input_manifest.json',{'timing_sha256':sha(D/'locked_timing.json'),'assets':inputs,'registry_sha256':sha(H/'compositions/ui-3d-reveal.html'),'data_csv_sha256':sha(R/'analysis/newlywed_region_2024/capital_gu_ranking.csv')})
    save(P/'motion_plan.json',{'phase_starts':S,'brand':B,'selected_ranks':list(range(20,10,-1)),'selection_count':10,'data_count':53,'rules':['shared object continuity','multi-axis perspective reveal','stagger then readable hold','literal audio word anchored actions'],'motion_seconds_actual':True})
    print(json.dumps({'status':'intro_built','project':str(P),'duration_s':duration,'intro_end_s':end,'selected_regions':10}))
if __name__=='__main__':main()
