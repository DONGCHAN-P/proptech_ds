"""Build a silent, provisional HyperFrames map demonstration; never narration or final films."""
from pathlib import Path
import sys,json,shutil,hashlib,argparse,re
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;E=D.parents[1];R=E.parents[2]
V=E/'visual/top20-split-v4';P=E/'editor/top20-split-v4/map-proof-v1'
sys.path.insert(0,str(V));from render_maps import txt,font,S,BG,INK,BLUE
def main():
    global P
    ap=argparse.ArgumentParser();ap.add_argument('--version',default='v2');args=ap.parse_args();assert re.fullmatch(r'v\d+',args.version)
    P=E/'editor/top20-split-v4'/('map-proof-'+args.version)
    assert not (P/'index.html').exists(),'Keep earlier proof project immutable; use another version'
    (P/'assets').mkdir(parents=True,exist_ok=True)
    legend=json.loads((E/'research/top20-split-v4/prices/legend.json').read_text(encoding='utf-8'))
    im=Image.new('RGB',(1920*S,1080*S),BG);d=ImageDraw.Draw(im)
    txt(im,(80,42),'데이터로 보는 부동산 | 신혼부부가 사는 곳',25)
    txt(im,(80,122),'아파트 가격·생활 지도, 이렇게 읽습니다',52,bold=True)
    txt(im,(80,220),'점 하나 = 거래와 위치가 확인된 단지  ·  색 = 전용 83~85㎡의 단지별 중위가격',30)
    for i,b in enumerate(legend['bands']):
        x=80+i*294;d.rounded_rectangle((x*S,318*S,(x+274)*S,545*S),radius=18*S,fill='#FFFFFF')
        d.ellipse(((x+107)*S,350*S,(x+167)*S,410*S),fill=b['color'])
        txt(im,(x+38,446),b['label'],33,bold=True)
    for x,label,icon,color in [(150,'학교','학','#648373'),(740,'지하철·철도역','역','#384C5C'),(1350,'주요 상업시설','상','#9B774F')]:
        if icon=='상':d.polygon([((x+31)*S,650*S),((x+67)*S,686*S),((x+31)*S,722*S),((x-5)*S,686*S)],fill=color)
        else:d.rounded_rectangle((x*S,655*S,(x+62)*S,717*S),radius=8*S,fill=color)
        txt(im,(x+13,665),icon,35,'#FFFFFF',True);txt(im,(x+88,665),label,33,bold=True)
    txt(im,(80,810),'가격: 2026년 5~10월 계약 · 11월 3일 조회  |  신혼부부 순위: 2024년 거주 통계',27)
    txt(im,(80,866),'구 전체 분포를 보고, 선택한 생활권의 역·학교·상업시설을 함께 살펴봅니다.',29,BLUE)
    im.resize((1920,1080),Image.Resampling.LANCZOS).save(P/'assets/legend.png')
    baseline=E/'editor/top20-explain-v3/main/v2-bgm/assets'
    for name in ['gsap.min.js','Pretendard-Regular.woff2','Pretendard-Bold.woff2']:shutil.copy2(baseline/name,P/'assets'/name)
    clips=['<img class="clip plate" data-start="0" data-duration="6" data-track-index="0" src="assets/legend.png">'];motion=[]
    for i,rid in enumerate(['R20','R02','R01']):
        start=6+i*8
        for mode in ['context','prices']:shutil.copy2(V/'maps'/f'{rid}_{mode}.png',P/'assets'/f'{rid}_{mode}.png')
        clips.append(f'<section class="clip" data-start="{start}" data-duration="8" data-track-index="1"><img class="plate" src="assets/{rid}_context.png"><img id="price-{rid}" class="plate prices" src="assets/{rid}_prices.png"></section>')
        motion.append(f'tl.fromTo("#price-{rid}",{{opacity:0}},{{opacity:1,duration:.8,ease:"power2.inOut",immediateRender:false}},{start+2});')
    html='''<!doctype html><html lang="ko"><head><meta charset="UTF-8"><title>가격·생활 지도 모션 시안</title><script src="assets/gsap.min.js"></script><style>
@font-face{font-family:Pretendard;src:url(assets/Pretendard-Regular.woff2)}*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#f6f4ef}#root{position:relative;width:100%;height:100%;overflow:hidden}.clip{position:absolute;inset:0}.plate{position:absolute;inset:0;width:100%;height:100%;object-fit:contain}.prices{opacity:0}.caption{position:absolute;left:96px;top:950px;width:1728px;height:102px;border-radius:12px;background:white;display:flex;align-items:center;justify-content:center;font:32px/1.3 Pretendard;color:#173348;z-index:20}
</style></head><body><div id="root" data-composition-id="map-proof" data-width="1920" data-height="1080" data-start="0" data-duration="30">'''+''.join(clips)+'''
<div class="clip" data-start="0" data-duration="6" data-track-index="10"><div class="caption">같은 가격 범례로 두 편의 모든 지역을 비교합니다.</div></div>
<div class="clip" data-start="6" data-duration="24" data-track-index="10"><div class="caption">구 전체의 가격 분포와 생활권의 역·학교·상업시설을 함께 봅니다.</div></div>
</div><script>const tl=gsap.timeline({paused:true});'''+''.join(motion)+'''window.__timelines["map-proof"]=tl;</script></body></html>'''
    (P/'index.html').write_text(html,encoding='utf-8')
    receipt={'type':'silent_map_motion_proof','provisional_timing':True,'duration_s':30,'final_episode_video':False,'new_voice_generated':False,'cash_spent_krw':0,'source_files':{p.relative_to(P).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in P.rglob('*') if p.is_file()}}
    (D/('map_proof_input_'+args.version+'.json')).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(str(P))
if __name__=='__main__':main()
