"""Prepare native portrait source from frozen, locally excerpted Jun audio. No upload/TTS."""
import hashlib
import html
import json
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
EP = HERE.parents[1]
ROOT = EP.parents[2]
OUT = EP / "outputs/shorts-jun-v1"
read = lambda p: json.loads(p.read_text(encoding="utf-8-sig"))
esc = html.escape
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
prepared = read(EP / "narration/free-tts-v1/prepare-v6/prepared.json")
paras = {p["paragraph_id"]: p for c in prepared["chapters"] for p in c["paragraphs"]}

def dump(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def anchor(timing, clip_num, literal):
    clip = timing["clips"][clip_num - 1]
    p = paras[clip["paragraph_id"]]
    index = p["text"].index(literal, clip["source_start"], clip["source_end"])
    span = next(s for s in p["display_mapping"] if s["source_start"] <= index < s["source_end"])
    spoken = span["spoken_start"] + (index-span["source_start"] if span["kind"] == "literal" else 0)
    align = read(EP / f'narration/jun-production-v1/paragraphs/{clip["paragraph_id"]}/alignment.json')
    time = clip["start_s"] + align["character_start_times_seconds"][spoken] - clip["raw_start_s"]
    assert 0 <= time < timing["duration_s"]
    return {"literal": literal, "clip": clip_num, "paragraph_id": clip["paragraph_id"],
            "source_index": index, "spoken_index": spoken, "time_s": time,
            "basis": "native Jun character alignment mapped to local excerpt PCM"}

def tx(text, x, y, size=52, kind="key_value", color="", weight=700, extra=""):
    style=f"left:{x}px;top:{y}px;font-size:{size}px;font-weight:{weight};"+(f"color:{color};" if color else "")
    return f'<div class="text" data-kind="{kind}" style="{style}" {extra}>{esc(text)}</div>'

def house(x, y, scale=1, color="#286cda"):
    windows="".join(f'<rect x="{xx}" y="{yy}" width="16" height="24" rx="1" fill="#f6f4ef"/>' for yy in [94,134,174,214] for xx in [52,83,114])
    return f'<svg class="house" style="left:{x}px;top:{y}px;width:{240*scale}px;height:{340*scale}px" viewBox="0 0 240 340" aria-hidden="true"><path d="M16 305 173 334 233 302 77 274Z" fill="#173348" opacity=".09"/><path d="M34 68 151 89 151 304 34 282Z" fill="{color}"/><path d="M151 89 208 57 208 271 151 304Z" fill="#173348"/><path d="M34 68 92 36 208 57 151 89Z" fill="#dce5ed"/>{windows}<path d="M82 252 110 257 110 296 82 290Z" fill="#173348"/></svg>'

def row(label, value, y, color="#173348", subtitle=None):
    s=tx(label,160,y,36,"label",color)+tx(value,160,y+48,68,"key_value",color,800)
    if subtitle:s+=tx(subtitle,160,y+132,30,"condition_source")
    return s

def title(lines):
    return '<header class="headline" data-kind="title">'+"<br>".join(esc(t) for t in lines)+"</header>"

def notes(lines):
    return '<footer class="notes" data-kind="condition_source">'+"<br>".join(esc(t) for t in lines)+"</footer>"

def bars(values, emphasis=None):
    # Exact 0 baseline; 10억원 upper reference shared by all scenarios.
    s='<div class="chart-grid">'
    for value in [0,5,10]:
        yy=990-value*40
        s+=f'<div class="gridline" style="top:{yy}px"></div>'+tx(str(value),145,yy-22,28,"condition_source")
    s+='</div>'
    for i,(label,value,col) in enumerate(zip(["매매","전세","월세"],values,["#286cda","#8a6828","#307565"])):
        x=222+i*220;h=value*40
        s+=f'<div class="bar" data-value="{value}" style="left:{x}px;top:{990-h}px;height:{h}px;background:{col};opacity:{1 if emphasis is None or i==emphasis else .48}"></div>'
        s+=tx(f"{value:.1f}억",x-23,990-h-70,54,"key_value",col,800)
        s+=tx(label,x-3,1010,40,"label",col)
    return s

CSS="""
@font-face{font-family:Pretendard;src:url('assets/fonts/Pretendard-Regular.woff2')}@font-face{font-family:Pretendard;src:url('assets/fonts/Pretendard-Bold.woff2');font-weight:700}@font-face{font-family:Pretendard;src:url('assets/fonts/Pretendard-ExtraBold.woff2');font-weight:800}
*{box-sizing:border-box}html,body{margin:0;width:1080px;height:1920px;background:#f6f4ef;color:#173348;font-family:Pretendard,sans-serif;font-variant-numeric:tabular-nums}#root{position:relative;width:1080px;height:1920px;overflow:hidden}.scene{position:absolute;inset:0}.text{position:absolute;white-space:nowrap;line-height:1.2}.headline{position:absolute;left:140px;top:268px;width:700px;margin:0;font-size:64px;line-height:1.16;font-weight:800;letter-spacing:-1px}.notes{position:absolute;left:140px;top:1260px;width:700px;font-size:26px;line-height:33px;color:#485e6e}.house{position:absolute}.bar{position:absolute;width:108px;transform-origin:bottom center;border-radius:8px 8px 0 0}.gridline{position:absolute;left:190px;width:640px;height:2px;background:#d5ddd9}.base-line{position:absolute;left:0;top:1080px;width:1080px;height:3px;background:#d5ddd9}.caption-panel{position:absolute;left:126px;top:1098px;width:728px;height:152px;border-radius:18px;background:#173348}.cue{position:absolute;left:140px;top:1105px;width:700px;height:140px;display:flex;align-items:center;justify-content:center;color:#f6f4ef;font-size:54px;line-height:66px;text-align:center;font-weight:400}.caption-lines{white-space:pre;display:block;max-width:680px}.outline{position:absolute;left:-80px;top:405px;width:1240px;height:640px;border-top:2px solid #d5ddd9;border-bottom:2px solid #d5ddd9}.outline:before,.outline:after{content:'';position:absolute;width:2px;height:100%;background:#d5ddd9;left:80px}.outline:after{left:1160px}.footer-decoration{position:absolute;left:0;right:0;bottom:0;height:450px;background:#e8ede7;clip-path:polygon(0 45%,100% 0,100% 100%,0 100%)}.flow{position:absolute;left:140px;width:680px;height:4px;background:#286cda;transform-origin:left}.pill{position:absolute;left:140px;top:456px;padding:16px 22px;border-radius:12px;background:#173348;color:#f6f4ef;font-size:38px;font-weight:700}.segment{position:absolute;top:720px;height:160px;transform-origin:left}.plus{position:absolute;font-size:62px;font-weight:800}.slab{position:absolute;left:140px;width:690px;height:120px;border-bottom:2px solid #c9d4d7}.cta-rule{position:absolute;left:140px;top:530px;width:700px;height:8px;background:#286cda;transform-origin:left}
"""

def build(ident):
    timing_path=EP/f"narration/shorts-jun-v1/{ident}/timing.json";t=read(timing_path)
    dest=OUT/ident;dest.mkdir(parents=True,exist_ok=True);assets=dest/"assets";assets.mkdir(exist_ok=True)
    source_assets=EP/"outputs/jun-production-v1/ch01/assets"
    for name in ["gsap.min.js", "fonts/Pretendard-Regular.woff2", "fonts/Pretendard-Bold.woff2", "fonts/Pretendard-ExtraBold.woff2"]:
        target=assets/name;target.parent.mkdir(exist_ok=True);shutil.copyfile(source_assets/name,target)
    shutil.copyfile(ROOT/t["audio"],assets/"narration.wav")
    shutil.copyfile(timing_path.parent/"captions.srt",dest/"captions.srt")
    anchors=[]
    def at(clip,literal):
        a=anchor(t,clip,literal);anchors.append(a);return a["time_s"]
    scenes=[]
    def scene(sid,start,end,heading,body,conditions):
        assert end>start
        scenes.append({"id":sid,"start_s":start,"end_s":end,"title":heading,"body":body,"conditions":conditions})
    tail=t["last_speech_end_s"]
    if ident=="funnel":
        cuts={"conditions":8.12,"base":20.12,"change":30.4,"four":at(5,"4%"),"six":at(5,"6%"),"order":40.84}
        base_notes=["집값 연2% · 투자 연6% · 대출 연4%", "월세·보증금 고정 · 남은 돈 전액 투자", "출처: 본편 동일 조건 10년 모형"]
        geo=house(68,605,.95)+house(410,605,.95,"#8a6828")+house(752,605,.95,"#307565")
        intro=tx("매매",155,960,48,"label","#286cda")+tx("전세",465,960,48,"label","#8a6828")+tx("월세",730,960,48,"label","#307565")+geo
        scene("F01",0,cuts["conditions"],["같은 집, 같은 10년","자산은 달라집니다"],intro,["같은 출발 자금 · 세 가지 주거 방식","출처: 본편 동일 조건 10년 모형"])
        body=row("초기 순자산","2억5천만원",470)+row("매달 주거·저축 예산","300만원",666)+row("같은 수준의 집 · 거주 기간","6억원 · 10년",862)
        scene("F02",cuts["conditions"],cuts["base"],["같은 돈으로","시작합니다"],body,["세 가구 모두 같은 투자 규칙","출처: 본편 동일 조건 10년 모형"])
        body=tx("10년 후 순자산 · 약",140,448,36,"label")+bars([6.1,6.6,6.9])
        scene("F03",cuts["base"],cuts["change"],["집값 연2%라면","첫 계산의 결과"],body,base_notes)
        body='<div class="pill" data-kind="label">월세·보증금 그대로</div>'+tx("집값 상승률",140,650,42,"label")+tx("2% → 4% → 6%",140,732,70,"key_value","#286cda",800)+tx("이 조건만 바꿉니다",140,912,40,"label")
        scene("F04",cuts["change"],cuts["four"],["집값 가정을","바꾸면?"],body,["투자 연6% · 대출 연4% 유지","출처: 본편 동일 조건 10년 모형"])
        for sid,start,end,pct,val in [("F05",cuts["four"],cuts["six"],4,7.7),("F06",cuts["six"],cuts["order"],6,9.6)]:
            body=tx("10년 후 순자산 · 약",140,448,36,"label")+bars([val,6.6,6.9],0)
            scene(sid,start,end,[f"집값 연{pct}%라면","매매가 앞서갑니다"],body,[f"집값 연{pct}% · 투자 연6% · 대출 연4%","월세·보증금 고정 · 남은 돈 전액 투자","출처: 본편 동일 조건 10년 모형"])
        body=tx("2%",140,502,56)+tx("4%",380,502,56)+tx("6%",620,502,56)+tx("매매 6.1억",140,608,52,"key_value","#286cda")+tx("7.7억",414,732,68,"key_value","#286cda",800)+tx("9.6억",650,868,68,"key_value","#286cda",800)
        scene("F07",cuts["order"],tail,["집값 상승률에 따라","자산 순위가 바뀝니다"],body,["10년 후 매매 순자산 · 반올림 약값","투자 연6% · 대출 연4% · 월세·보증금 고정","출처: 본편 동일 조건 10년 모형"])
        cta=["어떤 조건에서","내 자산이 더 남을까요?"]
    else:
        cuts={"whole":at(1,"가격이 움직이는"),"up":at(1,"처음 1년"),"five":at(1,"5%"),"costs":at(1,"여기에 이자"),"down":at(1,"가격이 내려갈"),"flows":29.46,"factors":at(2,"어느 쪽"),"choice":43.22}
        base_notes=["같은 6억원 집 · 집 투입 자기자금2.4억원","출처: 본편 매매 가구의 초기 구성"]
        body=tx("집을 살 때 넣은 자기자금",140,476,36,"label")+tx("2억4천만원",140,554,88,"key_value","#286cda",800)+house(610,690,1.1)+tx("대출 3억6천만원",140,898,48,"label")
        scene("A01",0,cuts["whole"],["내 돈과","집값은 크기가 다릅니다"],body,base_notes)
        body=tx("자기자금 2.4억",140,490,54,"key_value","#286cda")+tx("+ 대출 3.6억",140,590,54,"key_value")+'<div class="segment" style="left:140px;width:272px;background:#286cda"></div><div class="segment" style="left:412px;width:408px;background:#173348"></div>'+tx("집 전체 6억원",140,928,76,"key_value","#173348",800)
        scene("A02",cuts["whole"],cuts["up"],["6억원 집 전체에","가격 변화가 적용됩니다"],body,base_notes)
        body=tx("6억원 × 연2%",140,510,60)+tx("+1,200만원",140,650,92,"key_value","#286cda",800)+tx("첫해 집 평가액 증가",140,858,40,"label")
        scene("A03",cuts["up"],cuts["five"],["집값이 연2%","오르는 첫해"],body,["집 평가액 변화 기준","출처: 6억원 × 2% = 1,200만원"])
        body=tx("평가이익 1,200만원",140,508,54)+tx("÷ 자기자금 2.4억원",140,615,54)+tx("= 5%",140,790,120,"key_value","#286cda",800)
        scene("A04",cuts["five"],cuts["costs"],["자기자금과 비교하면","5%에 해당합니다"],body,["첫해 평가이익 / 집 투입 자기자금","이자·보유비용 차감 전","출처: 본편 매매 가구 계산"])
        body=row("매달 투자할 여유에 연결","이자 · 보유비",490)+row("자산에서 차감","남은 대출",750)
        scene("A05",cuts["costs"],cuts["down"],["비용과 남은 대출까지","연결해야 순자산입니다"],body,["순자산 = 집 평가액 + 투자계좌 − 남은 대출","원금 상환은 남은 대출을 줄입니다","출처: 본편 현금흐름 모형"])
        body=tx("집 전체의 가격 변화",140,494,46,"label")+tx("↓",140,598,152,"key_value","#9a4538",800)+tx("대출을 감당하며",140,834,56)+tx("오래 보유할 여력",140,924,56)
        scene("A06",cuts["down"],cuts["flows"],["하락할 때도","집 전체가 움직입니다"],body,["이자 부담 · 보유 기간을 함께 확인","출처: 본편 매매 가구의 위험 설명"])
        body=row("전세","매달 투자금이 큼",486,"#8a6828")+row("월세","초기 투자금이 큼",756,"#307565")
        scene("A07",cuts["flows"],cuts["factors"],["전세와 월세는","투자 시점이 다릅니다"],body,["이 본편의 동일 자금·거주 조건 기준","출처: 본편 세 가구 현금흐름 비교"])
        body=tx("초기 투자금",140,502,66)+tx("+ 월 적립금",140,678,66)+tx("+ 투자수익",140,854,66,"key_value","#286cda",800)
        scene("A08",cuts["factors"],cuts["choice"],["10년 뒤 자산은","세 가지로 결정됩니다"],body,["투자 계좌는 남은 돈을 같은 규칙으로 운용","출처: 본편 현금흐름 모형"])
        body=row("01","보유자금",470)+row("02","월 지출 여력",666)+row("03","거주·보유 기간",862)
        scene("A09",cuts["choice"],tail,["나에게 맞는 선택을","계산하는 기준"],body,["매매 · 전세 · 월세의 현금흐름을 연결","출처: 본편 결론"])
        cta=["우리 집 선택의 계산","채널 본편에서 확인하세요"]
    body='<div class="cta-rule"></div>'+tx("매매 · 전세 · 월세",140,620,62,"key_value","#286cda",800)+tx("같은 돈, 다른 10년",140,758,66)+tx("데이터로보는부동산",140,946,42,"label")
    scene("CTA",tail,t["duration_s"],cta,body,["본편에서 조건별 계산 과정을 확인하세요"])
    source=[];motion=[]
    for scene_row in scenes:
        sid=scene_row["id"];st=scene_row["start_s"];end=scene_row["end_s"]
        source.append(f'<section id="{sid}" class="scene clip" data-start="{st:.9f}" data-duration="{end-st:.9f}" data-track-index="1">'+title(scene_row["title"])+scene_row["body"]+notes(scene_row["conditions"])+"</section>")
        # A short arrival leaves the composition settled for most of the actual sentence.
        motion.append(f'tl.fromTo("#{sid} .headline",{{y:38}},{{y:0,duration:.2,ease:"power4.out"}},{st:.9f});')
        if 'class="bar"' in scene_row["body"]:
            motion.append(f'tl.fromTo("#{sid} .bar",{{scaleY:0}},{{scaleY:1,duration:.55,stagger:.06,ease:"power3.out"}},{st+.1:.9f});')
        if 'class="segment"' in scene_row["body"]:
            motion.append(f'tl.fromTo("#{sid} .segment",{{scaleX:0}},{{scaleX:1,duration:.55,stagger:.08,ease:"power3.out"}},{st+.08:.9f});')
    caption_panel=f'<div class="caption-panel clip" data-start="0" data-duration="{tail:.9f}" data-track-index="2"></div>'
    caption_nodes=[]
    for cue in t["cues"]:
        caption_nodes.append(f'<div id="{cue["id"]}" class="cue clip" data-kind="caption" data-start="{cue["start_s"]:.9f}" data-duration="{cue["end_s"]-cue["start_s"]:.9f}" data-track-index="3"><span class="caption-lines">'+esc("\n".join(cue["display_lines"]))+'</span></div>')
    content=f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=1080,height=1920"><title>{esc(t["title"])}</title><script src="assets/gsap.min.js"></script><style>{CSS}</style></head><body><div id="root" data-composition-id="main" data-width="1080" data-height="1920" data-start="0" data-duration="{t["duration_s"]:.9f}"><div class="outline"></div><div class="footer-decoration"></div>{"".join(source)}{caption_panel}{"".join(caption_nodes)}<audio id="narration" class="clip" src="assets/narration.wav" data-start="0" data-duration="{t["duration_s"]:.9f}" data-track-index="4" data-volume="1"></audio></div><script>window.__timelines=window.__timelines||{{}};const tl=gsap.timeline({{paused:true}});{"".join(motion)}tl.to({{}},{{duration:.001}},{t["duration_s"]-.001:.9f});window.__timelines.main=tl;</script></body></html>'
    (dest/"index.html").write_text(content,encoding="utf8")
    dump(dest/"hyperframes.json",{"authoringSkill":"general-video","paths":{"assets":"assets","blocks":"compositions","components":"compositions/components"}})
    dump(dest/"timing.json",t)
    dump(dest/"anchor_audit.json",{"anchors":anchors,"zero_fallbacks":0})
    dump(dest/"scenes.json",{"audio_revision":"shorts-jun-v1","timing_basis":"measured_Jun_audio_excerpts","scenes":[{k:v for k,v in s.items() if k!="body"} for s in scenes]})
    story=[f'# {t["title"]}',"",'실제 Jun 발화 길이를 기준으로 한 화면 제작 설계입니다. 본편 교체 후 최종 렌더와 검수를 진행합니다.',""]
    for i,s in enumerate(scenes,1):
        story += [f'## Frame {i}', 'status: source_prepared', 'src: index.html',f'time: {s["start_s"]:.3f}–{s["end_s"]:.3f}s',f'scene_id: {s["id"]}','rules: waterfall-entry; stat-bars-and-fills when quantitative bars are present', 'beat: '+" / ".join(s['title']), 'conditions: '+" · ".join(s['conditions']),""]
    (dest/"STORYBOARD.md").write_text("\n".join(story),encoding="utf8")
    shutil.copyfile(HERE/"design.md",dest/"design.md")
    return {"id":ident,"html":str((dest/"index.html").relative_to(ROOT)),"html_sha256":sha(dest/"index.html"),"scenes":len(scenes),"cues":len(t["cues"]),"duration_s":t["duration_s"],"audio_sha256":sha(assets/"narration.wav"),"native_anchors":len(anchors)}

if __name__=="__main__":
    rows=[build(i) for i in ["funnel","analysis"]]
    dump(HERE/"build_receipt.json",{"status":"source_prepared_not_rendered","outputs":rows,"new_TTS_calls":0,"additional_paid_credits":0,"registry":"animated-bar-chart searched; download blocked EACCES; local CSS scaleY implementation","main_upload_not_bypassed":True,"actual_listening":False})
    print(json.dumps(rows,ensure_ascii=False))
