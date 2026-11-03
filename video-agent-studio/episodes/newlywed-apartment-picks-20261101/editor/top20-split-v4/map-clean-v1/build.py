"""HyperFrames insert reel: a voiced criteria scene and ten photo-to-map transitions."""
from pathlib import Path
import argparse,hashlib,html,json,os,re,shutil
H=Path(__file__).resolve().parent;E=H.parents[2];R=E.parents[2];D=E/'director/top20-split-v4/part1-map-clean-v1'
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
esc=lambda s:html.escape(str(s),quote=True)

CSS='''
@font-face{font-family:Pretendard;src:url('assets/Pretendard-Regular.woff2')}@font-face{font-family:Pretendard;src:url('assets/Pretendard-Bold.woff2');font-weight:700}
*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;background:#f6f4ef;color:#173348;font-family:Pretendard,sans-serif}#root{position:relative;width:100%;height:100%;overflow:hidden}.clip,.source{position:absolute;inset:0;width:100%;height:100%;overflow:hidden}.source{object-fit:fill}.criteria{position:absolute;inset:0;background:#f6f4ef}.brand{position:absolute;left:96px;top:52px;font-size:25px;font-weight:700}.section-label{position:absolute;right:96px;top:52px;font-size:23px;color:#425b6d}.heading{position:absolute;left:96px;top:128px;font-size:68px;line-height:1.2;font-weight:700;letter-spacing:-.035em}.subheading{position:absolute;left:100px;top:226px;font-size:30px;color:#425b6d}.info{position:absolute;top:320px;width:540px;height:340px;padding:32px 36px;border-radius:24px;background:white;border:2px solid #dee5e9}.info .label{font-size:29px;color:#425b6d;margin-top:28px}.info .value{font-size:58px;font-weight:700;line-height:1.2;color:#286cda;margin-top:10px}.info .suffix{font-size:26px;color:#425b6d;margin-top:17px}.info svg{width:64px;height:64px;stroke:#286cda;fill:none;stroke-width:4;stroke-linecap:round;stroke-linejoin:round}.flow{position:absolute;left:100px;top:718px;width:1720px;display:flex;gap:30px;align-items:center}.flow .step{height:104px;width:495px;background:#e7eef7;border-radius:18px;display:flex;align-items:center;justify-content:center;font-size:34px;font-weight:700}.flow .arrow{font-size:44px;color:#286cda}.explain{position:absolute;left:100px;top:850px;font-size:25px;color:#425b6d}.caption-bg{position:absolute;left:96px;top:942px;width:1728px;height:110px;background:white;border-radius:18px}.caption{position:absolute;left:126px;top:945px;width:1668px;height:104px;display:flex;align-items:center;justify-content:center;text-align:center;font-size:39px;line-height:1.3;letter-spacing:-.02em;padding:5px 12px;color:#173348}.hero{position:absolute;left:0;top:0;width:1920px;height:922px;overflow:hidden;background:#142e42}.hero-image{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:center 45%}.shade{position:absolute;inset:0;background:linear-gradient(180deg,rgba(10,27,43,.38) 0%,rgba(10,27,43,.03) 35%,rgba(10,27,43,.68) 61%,rgba(10,27,43,.96) 100%)}.hero-brand{position:absolute;left:96px;top:52px;font-size:25px;font-weight:700;color:#fff}.hero-series{position:absolute;right:96px;top:52px;font-size:25px;color:#fff}.rank{position:absolute;left:96px;top:530px;font-size:128px;font-weight:700;line-height:1.05;color:#e6b868}.region{position:absolute;left:390px;top:548px;font-size:81px;font-weight:700;line-height:1.15;color:#fff;letter-spacing:-.035em;width:1430px}.couples{position:absolute;left:395px;top:661px;font-size:35px;color:#fff}.place{position:absolute;left:100px;top:791px;font-size:24px;color:#fff;width:1700px}.photo-credit{position:absolute;left:100px;top:842px;font-size:20px;line-height:1.3;color:#fff;width:1700px}.accent{position:absolute;left:100px;top:751px;height:4px;width:145px;background:#e6b868}
'''
ICONS=["<rect x='8' y='14' width='48' height='43' rx='5'/><path d='M8 27h48M20 7v14M44 7v14M21 38h8M37 38h7M21 47h8'/>" ,
       "<path d='M9 10h46v46H9zM32 10v46M9 33h46M16 18h8M40 18h8'/><path d='M14 60h36M14 57v6M50 57v6'/>" ,
       "<path d='M9 31L32 11l23 20M16 27v30h32V27M26 57V39h13v18'/><path d='M29 27l5 5 10-10'/>" ]

def link(src,dest):
    dest.parent.mkdir(parents=True,exist_ok=True)
    if not dest.exists():os.link(src,dest)
    assert os.path.samefile(src,dest)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--photos',type=Path,required=True);ap.add_argument('--version',default='project-v1');args=ap.parse_args()
    p=H/args.version;assert not p.exists();p.mkdir();a=p/'assets';a.mkdir()
    t=read(D/'locked_timing.json');plan=t['transition_plan'];rows=read(args.photos);assert len(rows)==10
    clean=read(D/'clean_receipt_v2.json');assert sha(clean['video'])==clean['sha256']
    old=E/'editor/top20-split-v4/intro-rationale-v3/project-v3/assets'
    for f in ['gsap.min.js','Pretendard-Regular.woff2','Pretendard-Bold.woff2']:link(old/f,a/f)
    link(Path(clean['video']),a/'baseline.mp4');link(D/'media/criteria_mixed.wav',a/'criteria.wav')
    units=[];markup=[];js=[];dur=t['insert_duration_s']
    cards=[]
    for i,(label,value,suffix) in enumerate([('계약 기간','2026.05—10','5월부터 10월까지'),('면적 범위','전용 83~85㎡','같은 면적대 아파트'),('조회 기준일','2026.11.03','확인된 계약·취소 반영')]):
        cards.append(f"<div id='info{i}' class='info' style='left:{100+i*572}px'><svg viewBox='0 0 64 68'>{ICONS[i]}</svg><div class='label'>{label}</div><div class='value'>{value}</div><div class='suffix'>{suffix}</div></div>")
        js.append(f"tl.fromTo('#info{i}',{{y:28,opacity:0}},{{y:0,opacity:1,duration:.55,ease:'power3.out'}},{.28+i*.24});")
    markup.append(f"<section class='clip' data-start='0' data-duration='{dur}' data-track-index='1'><div class='criteria'><div class='brand'>데이터로 보는 부동산</div><div class='section-label'>가격 비교 기준</div><div class='heading'>가격은 이렇게 비교했습니다</div><div class='subheading'>국토교통부 아파트 매매 실거래</div>{''.join(cards)}<div class='flow'><div id='step0' class='step'>취소 거래 제외</div><span class='arrow'>→</span><div id='step1' class='step'>단지별로 모으고</div><span class='arrow'>→</span><div id='step2' class='step'>중위가격으로 비교</div></div><div class='explain'>중위가격 = 가격순으로 나열했을 때 가운데 값</div></div></section>")
    for i in range(3):js.append(f"tl.fromTo('#step{i}',{{opacity:.18,y:14}},{{opacity:1,y:0,duration:.45,ease:'power2.out'}},{7.2+i*1.1});")
    for i,c in enumerate(t['criteria_captions_local']):
        markup.append(f"<div class='clip' data-start='{c['start_s']:.9f}' data-duration='{c['end_s']-c['start_s']:.9f}' data-track-index='3'><div class='caption-bg'></div><div class='caption'>{esc(c['text'])}</div></div>")
    markup.append(f"<audio id='criteria-audio' src='assets/criteria.wav' data-start='0' data-duration='{dur}' data-track-index='4'></audio>")
    byrank={int(r['rank']):r for r in rows};names={20:'부천 원미구',19:'서울 중랑구',18:'용인 기흥구',17:'인천 연수구',16:'인천 남동구',15:'서울 구로구',14:'서울 은평구',13:'수원 권선구',12:'수원 영통구',11:'서울 노원구'}
    for u in plan['photos']:
        rank=u['rank'];r=byrank[rank];src=Path(r['file']);assert sha(src)==r['sha256'];shutil.copyfile(src,a/f'R{rank}_hero.jpg')
        start=u['reel_start_s'];length=u['duration_s'];sid=f'hero{rank}';source_t=u['source_start_s'];ss=next(s for s in t['body_scenes']if s['scene_id']==u['scene_id']);count=re.search(r'([\d,]+)쌍',ss['sentences'][0]['text']).group(1)
        years=re.findall(r'(?:19|20)\d{2}',str(r['photo_date']));year=years[0]+'년' if years else '촬영일 원문 참조'
        credit=f"사진: {r['author']} · {r['license_name']} · {year} 촬영"
        markup.append(f"<video id='map{rank}' class='source clip' src='assets/baseline.mp4' data-start='{start:.9f}' data-duration='{length:.9f}' data-media-start='{source_t:.9f}' data-track-index='0' muted playsinline></video>")
        markup.append(f"<section class='clip' data-start='{start:.9f}' data-duration='{length:.9f}' data-track-index='2'><div id='{sid}' class='hero hf-catalog-directional-wipe'><img id='{sid}-image' class='hero-image' src='assets/R{rank}_hero.jpg'/><div class='shade'></div><div class='hero-brand'>데이터로 보는 부동산</div><div class='hero-series'>신혼부부가 사는 곳 · 20위 → 11위</div><div id='{sid}-rank' class='rank'>{rank}위</div><div id='{sid}-region' class='region'>{names[rank]}</div><div class='couples'>신혼부부 {count}쌍</div><div class='accent'></div><div class='place'>{esc(r['actual_place'])}</div><div class='photo-credit'>{esc(credit)}</div></div></section>")
        # Adapt the registry's directional clip reveal; retain the actual source map beneath.
        js.append(f"tl.fromTo('#{sid}',{{clipPath:'inset(0% 100% 0% 0%)',x:60}},{{clipPath:'inset(0% 0% 0% 0%)',x:0,duration:.52,ease:'power3.inOut'}},{start:.9f});")
        js.append(f"tl.fromTo('#{sid}-image',{{scale:1.055}},{{scale:1.005,duration:{length:.9f},ease:'none'}},{start:.9f});")
        js.append(f"tl.fromTo('#{sid}-rank',{{y:26,opacity:0}},{{y:0,opacity:1,duration:.4,ease:'power3.out'}},{start+.20:.9f});")
        js.append(f"tl.fromTo('#{sid}-region',{{x:32,opacity:0}},{{x:0,opacity:1,duration:.44,ease:'power3.out'}},{start+.31:.9f});")
        js.append(f"tl.to('#{sid}',{{opacity:0,x:-28,duration:.55,ease:'power2.inOut'}},{start+length-.55:.9f});")
        units.append(dict(u,photo=r))
    total=plan['reel_total_s']
    index=f"<!doctype html><html lang='ko'><head><meta charset='utf-8'><script src='assets/gsap.min.js'></script><link rel='stylesheet' href='style.css'></head><body><div id='root' data-composition-id='map-clean-reel' data-width='1920' data-height='1080' data-duration='{total:.9f}'>{''.join(markup)}</div><script>const tl=gsap.timeline({{paused:true}});{''.join(js)}window.__timelines['map-clean-reel']=tl;</script></body></html>"
    (p/'index.html').write_text(index,encoding='utf-8');(p/'style.css').write_text(CSS,encoding='utf-8')
    (p/'hyperframes.json').write_text(json.dumps({'name':'part1-map-clean-reel','width':1920,'height':1080,'fps':30},indent=2),encoding='utf-8')
    manifest={'project':str(p),'source_video_sha256':clean['sha256'],'timing_sha256':sha(D/'locked_timing.json'),'photos_manifest':str(args.photos.resolve()),'photos_manifest_sha256':sha(args.photos),'units':units,'duration_s':total,'registry_reference':str(H/'compositions/components/directional-wipe.html'),'new_paid_calls':0}
    (p/'input_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (D/f'build_{args.version}.json').write_text(json.dumps({'project':str(p),'duration_s':total,'photo_transitions':10,'criteria_s':dur,'input_manifest_sha256':sha(p/'input_manifest.json')},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':'reel_source_ready','project':str(p),'duration_s':total,'photo_transitions':10}),flush=True)
if __name__=='__main__':main()
