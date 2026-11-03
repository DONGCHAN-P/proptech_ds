"""Build the 3/5/10-year chart insert from the frozen comparison data."""
from pathlib import Path
import hashlib
import html
import json
import math
import shutil

ROOT = Path(__file__).resolve().parents[2]
DATA = Path(__file__).parent / "comparison.json"
EP = ROOT / "video-agent-studio/episodes/housing-choice-networth-20261020"
OUT = EP / "outputs/returns-motion-v1"
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "compositions").mkdir(exist_ok=True)
(OUT / "assets/fonts").mkdir(parents=True, exist_ok=True)
data = json.loads(DATA.read_text(encoding="utf8"))
shutil.copyfile(DATA, OUT / "data.json")
for weight in ("Regular", "Bold", "ExtraBold"):
    shutil.copyfile(ROOT / f"assets/fonts/Pretendard-{weight}.woff2", OUT / f"assets/fonts/Pretendard-{weight}.woff2")
shutil.copyfile(EP / "outputs/intro-motion-v1/hyperframes.json", OUT / "hyperframes.json")
(OUT / "package.json").write_text(json.dumps({"name": "returns-motion-v1", "private": True, "scripts": {"render": "hyperframes render -o returns_motion_v1.mp4", "check": "hyperframes check"}}, indent=2), encoding="utf8")

COLORS = {"house": "#286cda", "price": "#b35728"}
NAMES = {"house": "수도권 아파트", "price": "S&P500 가격지수"}
X0, X1, Y0, Y1 = 100, 1190, 530, 35
YM = 360
def y(v): return Y0 - v / YM * (Y0 - Y1)
def pct(v): return f"{v:+.2f}%".replace("-", "−")

captions = {
    3: ["출발점을 100으로 맞춰, 최근 3년의 가격 변화를 보겠습니다.", "2022년을 기준으로 잡으면, 두 가격선의 방향이 달라집니다.", "연복리 상승률은 수도권 −2.92%, S&P500 +21.26%입니다.", "이 구간은 2022년의 높은 집값 수준을 출발점으로 삼습니다."],
    5: ["시작을 2020년으로 옮겨, 최근 5년을 비교하겠습니다.", "수도권은 2021~2022년 상승 뒤 하락과 회복을 거칩니다.", "5년 연복리는 수도권 +5.03%, S&P500 +12.75%입니다.", "같은 종료 시점이어도, 출발 시점에 따라 결과가 달라집니다."],
    10: ["이번에는 2015년부터 2025년까지, 최근 10년입니다.", "중간의 상승과 하락을 포함해 전체 경로를 보겠습니다.", "10년 연복리는 수도권 +6.11%, S&P500 +12.85%입니다.", "과거의 가격 변화입니다. 앞으로의 수익률 가정과 구분합니다."],
}
timeline = []
subs = []
summary_checks = []
for order, n in enumerate((3, 5, 10)):
    start, scene = 2025 - n, f"years{n}"
    points = data["paths"][str(start)]
    assert len(points) == n + 1
    end = points[-1]
    cg = {k: ((end[k] / 100) ** (1 / n) - 1) * 100 for k in COLORS}
    for k, label in (("house", "수도권 아파트 가격"), ("price", "S&P500 가격 · USD")):
        reference = next(r["cagr_pct"] for r in data["summary"] if r["start"] == start and r["series"] == label)
        assert abs(cg[k] - reference) < 1e-9
        summary_checks.append({"years": n, "series": k, "cagr": cg[k], "matches_source": True})
    x = lambda year: X0 + (year - start) / n * (X1 - X0)
    grid = []
    for value in range(0, 351, 50):
        dash = 'stroke-dasharray="7 7"' if value == 100 else ''
        grid.append(f'<line x1="{X0}" x2="{X1}" y1="{y(value)}" y2="{y(value)}" stroke="{"#6f7b83" if value == 100 else "#d9dedf"}" stroke-width="{2 if value == 100 else 1}" {dash}/><text x="78" y="{y(value)+8}" text-anchor="end" class="axis">{value}</text>')
    for p in points:
        grid.append(f'<text x="{x(p["year"])}" y="580" text-anchor="middle" class="axis">{p["year"]}</text>')
    lines, anim = [], []
    draw_start, draw_duration = 2.0, 6.7
    for k, color in COLORS.items():
        for j in range(n):
            p0, p1 = points[j], points[j + 1]
            length = math.hypot(x(p1["year"]) - x(p0["year"]), y(p1[k]) - y(p0[k]))
            ident = f"{scene}-{k}-seg{j}"
            lines.append(f'<path id="{ident}" d="M{x(p0["year"]):.4f},{y(p0[k]):.4f} L{x(p1["year"]):.4f},{y(p1[k]):.4f}" fill="none" stroke="{color}" stroke-width="7" stroke-linecap="butt" stroke-dasharray="{length:.6f}" stroke-dashoffset="{length:.6f}"/>')
            anim.append(f'tl.fromTo("#{ident}",{{strokeDashoffset:{length:.6f}}},{{strokeDashoffset:0,duration:{draw_duration/n},ease:"none"}},{draw_start+j*draw_duration/n});')
        for j, p in enumerate(points):
            ident = f"{scene}-{k}-dot{j}"
            lines.append(f'<circle id="{ident}" cx="{x(p["year"])}" cy="{y(p[k])}" r="7" fill="{color}" stroke="#f6f4ef" stroke-width="3" opacity="0"/>')
            anim.append(f'tl.fromTo("#{ident}",{{opacity:0}},{{opacity:1,duration:0.12}},{draw_start+j*draw_duration/n});')
        ident = f"{scene}-{k}-value"
        lines.append(f'<text id="{ident}" x="{X1+18}" y="{y(end[k])+8}" class="endvalue" fill="{color}" opacity="0">{end[k]:.1f}</text>')
        anim.append(f'tl.fromTo("#{ident}",{{opacity:0}},{{opacity:1,duration:0.4}},8.8);')
    cards = []
    for i, k in enumerate(COLORS):
        cards.append(f'<div class="stat stat{i}" id="{scene}-{k}-stat"><div class="stat-label" style="color:{COLORS[k]}">{NAMES[k]}</div><div class="stat-value" style="color:{COLORS[k]}">{pct(cg[k])}</div><div class="stat-detail">{n}년 누적 {pct(end[k]-100)}</div></div>')
        anim.append(f'tl.fromTo("#{scene}-{k}-stat",{{opacity:0}},{{opacity:1,duration:0.5}},{9.4+i*.35});')
    caps = []
    for j, text in enumerate(captions[n]):
        caps.append(f'<div id="{scene}-caption{j}" class="caption clip" data-start="{j*4.5}" data-duration="4.5" data-track-index="9"><span>{html.escape(text)}</span></div>')
        timeline.append({"start": order * 18 + j * 4.5, "end": order * 18 + (j + 1) * 4.5, "text": text})
    body = f'''<div id="root" data-composition-id="{scene}" data-width="1920" data-height="1080" data-duration="18">
      <div class="scene-body" id="{scene}-body">
      <div class="brand">│ 데이터로 보는 부동산</div><div class="chapter-label">가격 변화 비교 · {order+1} / 3</div>
      <h1>최근 {n}년, <span>{start} → 2025</span></h1><div class="subtitle">같은 출발점 100 · 같은 세로축 0~360 · 연간 관측값</div>
      <div class="legend"><span><b style="background:#286cda"></b>수도권 아파트</span><span><b style="background:#b35728"></b>S&P500 가격지수 · USD</span><span class="basis">배당·환율 제외</span></div>
      <div class="chart-panel"><svg viewBox="0 0 1320 610" width="1320" height="610">{''.join(grid)}{''.join(lines)}</svg></div>
      <div class="stats"><div class="stats-header">연평균 상승률</div><div class="stats-sub">연복리 · CAGR</div>{''.join(cards)}<div class="stats-foot">2025년까지의 과거 변화</div></div>
      <div class="condition">집값: 연평균 거래가격　│　S&P500: 연말 가격지수　│　세금·대출·주거편익 제외</div>
      <div class="caption-box"></div>{''.join(caps)}
      <div class="source">출처: 보유 실거래 자료(서울·경기·인천, 동일 단지·면적 매칭) · NYU Damodaran S&P500 연말 지수</div>
      </div></div>'''
    script = f'''<script>{{const tl=gsap.timeline({{paused:true}});{''.join(anim)}
    tl.fromTo("#{scene}-body",{{opacity:0}},{{opacity:1,duration:0.25}},0);
    window.__timelines["{scene}"]=tl;}}</script>'''
    (OUT / f"compositions/{scene}.html").write_text('<!doctype html><html lang="ko"><meta charset="utf-8"><body><template><style>#root{position:absolute;inset:0;overflow:hidden;background:#f6f4ef}</style>'+body+script+'</template></body></html>', encoding="utf8")
    subs.append(f'<div id="mount-{scene}" class="clip" data-composition-id="{scene}" data-composition-src="compositions/{scene}.html" data-start="{order*18}" data-duration="18" data-track-index="{order}" data-width="1920" data-height="1080"></div>')

style = '''@font-face{font-family:Pretendard;src:url(assets/fonts/Pretendard-Regular.woff2);font-weight:400}@font-face{font-family:Pretendard;src:url(assets/fonts/Pretendard-Bold.woff2);font-weight:700}@font-face{font-family:Pretendard;src:url(assets/fonts/Pretendard-ExtraBold.woff2);font-weight:800}
*{box-sizing:border-box}html,body{margin:0;width:1920px;height:1080px;overflow:hidden;background:#f6f4ef;color:#173348;font-family:Pretendard,sans-serif}#root{position:relative;width:1920px;height:1080px;overflow:hidden}#root>.clip{position:absolute;inset:0}.scene-body{position:absolute;inset:0;background:#f6f4ef}.brand{position:absolute;left:80px;top:32px;font-size:23px}.chapter-label{position:absolute;right:80px;top:34px;font-size:22px;color:#546973}h1{position:absolute;left:80px;top:91px;margin:0;font-size:48px;font-weight:800}h1 span{margin-left:24px;font-weight:700;color:#546973;font-size:38px}.subtitle{position:absolute;left:80px;top:165px;font-size:23px;color:#546973}.legend{position:absolute;left:110px;top:221px;display:flex;gap:34px;font-size:25px;align-items:center}.legend span{display:flex;align-items:center;gap:12px}.legend b{display:inline-block;width:33px;height:7px;border-radius:5px}.legend .basis{font-size:20px;color:#546973}.chart-panel{position:absolute;left:70px;top:270px;width:1320px;height:610px}.axis{font-size:24px;fill:#546973}.endvalue{font-size:28px;font-weight:800}.stats{position:absolute;left:1440px;top:254px;width:390px;height:560px;border-left:2px solid #d6dad7;padding:20px 0 0 34px}.stats-header{font-size:31px;font-weight:700}.stats-sub{font-size:22px;color:#546973;margin-top:8px}.stat{position:absolute;left:34px;width:350px}.stat0{top:140px}.stat1{top:320px}.stat-label{font-size:28px;font-weight:700}.stat-value{font-size:67px;font-weight:800;letter-spacing:-2px;margin-top:8px;white-space:nowrap}.stat-detail{font-size:23px;color:#546973;margin-top:6px}.stats-foot{position:absolute;left:34px;bottom:5px;font-size:21px;color:#546973}.condition{position:absolute;left:96px;top:884px;font-size:21px;color:#546973}.caption-box{position:absolute;left:96px;top:936px;width:1728px;height:94px;background:#fff;border-radius:13px}.caption{position:absolute;left:120px;top:936px;width:1680px;height:94px;display:flex;align-items:center;justify-content:center;font-size:34px;font-weight:700;line-height:1.3}.source{position:absolute;left:96px;top:1044px;font-size:18px;color:#546973}'''
(OUT / "index.html").write_text('<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=1920,height=1080"><script src="assets/gsap.min.js"></script><style>'+style+'</style></head><body><div id="root" data-composition-id="main" data-width="1920" data-height="1080" data-duration="54" data-fps="30">'+''.join(subs)+'</div><script>const tl=gsap.timeline({paused:true});window.__timelines["main"]=tl;</script></body></html>', encoding="utf8")

def stamp(s):
    ms=round(s*1000)
    return f"{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}"
(OUT / "returns_motion_v1.srt").write_text(''.join(f'{i}\n{stamp(c["start"])} --> {stamp(c["end"])}\n{c["text"]}\n\n' for i,c in enumerate(timeline,1)),encoding="utf8")
(OUT / "BRIEF.md").write_text('---\nworkflow: general-video\nflow: automation\nstoryboard: no\naspect: 1920x1080\nlanguage: ko\nlength: 54s\n---\n\nMP4 insert for the housing-choice episode. Existing cream/Pretendard style. Three 18-second line-chart scenes, 3/5/10-year windows ending 2025. S&P price index USD, no dividend/FX. User requests a video, not a web-page deliverable. No paid narration requested; on-screen explanation, silent.\n',encoding="utf8")
(OUT / "STORYBOARD.md").write_text('---\nmode: autonomous\n---\n'+''.join(f'\n## Frame {i+1}\nstatus: built\nsrc: compositions/years{n}.html\nRules: svg-path-draw, linear per-year reveal, fade stat labels.\nBeat: start=100, trace actual annual path, hold endpoint and CAGR, explain start-date sensitivity.\n' for i,n in enumerate((3,5,10))),encoding="utf8")
(OUT / "data_checks.json").write_text(json.dumps({"source_sha256":hashlib.sha256(DATA.read_bytes()).hexdigest(),"summary_checks":summary_checks,"duration":54,"audio":"none","y_axis":[0,360],"discrete_annual_points":True},ensure_ascii=False,indent=2),encoding="utf8")
print(f"Built {OUT}: 54s, 3 sub-compositions, 12 captions, 6 source checks passed")
