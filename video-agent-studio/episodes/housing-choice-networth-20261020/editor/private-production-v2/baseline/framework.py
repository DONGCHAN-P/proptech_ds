"""챕터 모션그래픽 공통 프레임워크.

- script_v1.md 의 해당 장 본문을 의미 단위 자막 큐로 나누고, Jun 실측 속도(교산 v5 SRT 6.19자/초)로
  provisional 시간을 붙인다. 확정 음성이 나오면 timing_override.json 으로 실제 큐 시간을 넣는다.
- 장면 HTML 조각은 chapters.py 가 이 파일의 부품 함수로 만든다.
- 각 장은 독립 HyperFrames 프로젝트(chNN/)로 출력한다.
"""
import json
import re
import shutil
from pathlib import Path

HERE = Path(__file__).parent
EPISODE = HERE.parent.parent
SCRIPT = EPISODE / "outputs/script-review-v1/script_v1.md"
FONTS = Path("C:/projects/realestate_reco/assets/fonts")
CHAPTER_BG = Path("C:/projects/realestate_reco/video-agent-studio/assets/chapter-backgrounds/v1/price.png")

CPS = 6.19
CUE_GAP = 0.25
PARA_GAP = 0.6
CARD_DUR = 3.0       # 교산 v5 챕터 화면 90프레임
LEAD_AFTER_CARD = 0.5
TAIL = 1.2
MAX_LINE = 36
# 휴리스틱이 의미 단위를 끊는 문장에만 쓰는 수동 분할점(이 문구 앞에서 끊는다)
BREAK_BEFORE = ["처음부터 돈이", "계속거주 평가", "수익률 차이와", "실제로 감당할", "소득과 대출", "처음 투자계좌가"]

BUY, JEONSE, WOLSE = "#286cda", "#c29a44", "#3f8f7f"
JEONSE_INK = "#94702a"
HH = [("매매", BUY, BUY), ("전세", JEONSE, JEONSE_INK), ("월세", WOLSE, WOLSE)]


# ---------------------------------------------------------------- 대본·큐
def chapter_paragraphs(num):
    text = SCRIPT.read_text(encoding="utf8")
    parts = re.split(r"^## ", text, flags=re.M)[1:]
    for p in parts:
        head, body = p.split("\n", 1)
        if head.startswith(f"{num}."):
            paras = [x.strip() for x in body.strip().split("\n\n") if x.strip()]
            return head.strip(), paras
    raise KeyError(num)


def _split_long(s):
    """쉼표 기준 → 그래도 길면 가운데 가까운 공백(숫자·'약' 직후 제외)."""
    if len(s) <= MAX_LINE:
        return [s]
    parts = [p for p in re.split(r"(?<=,)\s+", s)]
    out, cur = [], ""
    for p in parts:
        cand = (cur + " " + p).strip()
        if cur and len(cand) > MAX_LINE:
            out.append(cur)
            cur = p
        else:
            cur = cand
    out.append(cur)
    res = []
    for chunk in out:
        if len(chunk) <= MAX_LINE + 6:
            res.append(chunk)
            continue
        forced = next((b for b in BREAK_BEFORE if f" {b}" in chunk), None)
        if forced:
            i = chunk.index(f" {forced}")
            res += [chunk[:i], chunk[i + 1:]]
            continue
        words = chunk.split(" ")
        best = None
        for strict in (True, False):
            best_d = 1e9
            for i in range(1, len(words)):
                left = " ".join(words[:i])
                w, nxt = words[i - 1], words[i]
                if w in ("약", "연", "월", "초기", "같은", "다른", "매달", "새", "그", "이", "두", "세", "더", "따로", "실제로",
                         "추가로", "미리", "하나로", "가장", "매일", "함께", "모두", "다시", "그대로", "먼저", "한"):
                    continue
                if re.fullmatch(r"[\d,.]+", w) or (re.search(r"\d", w) and re.match(r"\d", nxt)):
                    continue
                if re.search(r"(한|할|된|될|인|운|른|던|의|과|와)$", w):
                    continue
                if strict and re.search(r"(는|은)$", w) and not re.search(r"(가구는|조건은|금리는|집값은|투자수익은|결과는|원금은|보증금은|수익률은)$", w):
                    continue
                d = abs(len(left) - len(chunk) / 2)
                if re.search(r"(면|고|서|며|지만|는데|도|므로|때는)$", w):
                    d -= 9
                elif re.search(r"(을|를|에|에서|로|으로|은|는)$", w):
                    d -= 4
                if d < best_d:
                    best, best_d = i, d
            if best:
                break
        res += [" ".join(words[:best]), " ".join(words[best:])] if best else [chunk]
    # 너무 짧은 꼬리는 앞 큐와 합친다(두 줄 허용)
    merged = []
    for c in res:
        if merged and len(c) < 9 and len(merged[-1]) + len(c) < 60:
            merged[-1] = merged[-1] + " " + c
        else:
            merged.append(c)
    return merged


def make_cues(paras):
    cues = []
    for pi, para in enumerate(paras):
        sents = re.split(r"(?<=[.?!])\s+", para)
        for si, s in enumerate(sents):
            for ci, c in enumerate(_split_long(s.strip())):
                cues.append({"text": c, "para": pi})
        cues[-1]["para_end"] = True
    return cues


def spoken_len(t):
    return len(re.sub(r"[\s,.·?!]", "", t)) + 2 * t.count("%")


def time_cues(cues, start):
    t = start
    for c in cues:
        c["start"] = round(t, 2)
        c["dur"] = round(spoken_len(c["text"]) / CPS, 2)
        t += c["dur"] + CUE_GAP + (PARA_GAP if c.get("para_end") else 0)
    return round(t - CUE_GAP + TAIL, 2)


# ---------------------------------------------------------------- 부품
def px(v):
    return f"{round(v, 1)}px"


def tx(id, x, y, text, size=24, weight=400, color="var(--ink)", w=None, align="left", extra=""):
    width = f"width:{px(w)};" if w else "white-space:nowrap;"
    return (f'<div id="{id}" class="tx" style="left:{px(x)};top:{px(y)};{width}font-size:{size}px;'
            f'font-weight:{weight};color:{color};text-align:{align};{extra}">{text}</div>')


def panel(id, inner, wide=False, x=80, y=225, w=None, h=540, bg="var(--panel)"):
    w = w or (1740 if wide else 1080)
    return f'<div id="{id}" class="pnl" style="left:{px(x)};top:{px(y)};width:{px(w)};height:{px(h)};background:{bg}">{inner}</div>'


def card(id, top, k, v=None, s=None, color="var(--primary)", left=1250, w=570, vsize=50, h=None):
    hh = f"height:{px(h)};" if h else ""
    body = f'<div class="k">{k}</div>'
    if v:
        body += f'<div class="v" style="font-size:{vsize}px;color:{color}">{v}</div>'
    if s:
        body += f'<div class="s">{s}</div>'
    return f'<div id="{id}" class="card" style="top:{px(top)};left:{px(left)};width:{px(w)};{hh}border-left-color:{color}">{body}</div>'


def box(id, x, y, w, h, inner, border=None, bg="#fff", size=26, weight=700, color="var(--ink)", extra=""):
    b = f"border:2px solid {border};" if border else ""
    return (f'<div id="{id}" class="box" style="left:{px(x)};top:{px(y)};width:{px(w)};height:{px(h)};background:{bg};{b}'
            f'font-size:{size}px;font-weight:{weight};color:{color};{extra}">{inner}</div>')


def sub(t, size=21, color="var(--muted)", weight=400):
    return f'<span class="sub" style="font-size:{size}px;color:{color};font-weight:{weight}">{t}</span>'


def arrow(id, x, y, length, d="r", color="var(--primary)", thick=4):
    if d == "r":
        return f'<div id="{id}" class="arr r" style="left:{px(x)};top:{px(y - thick / 2)};width:{px(length)};height:{thick}px;--c:{color}"></div>'
    return f'<div id="{id}" class="arr d" style="left:{px(x - thick / 2)};top:{px(y)};width:{thick}px;height:{px(length)};--c:{color}"></div>'


def mark(id, x, y, ok=False, text=None):
    sym = "✓" if ok else "✕"
    cls = "ok" if ok else "no"
    lab = f'<span class="ml">{text}</span>' if text else ""
    return f'<div id="{id}" class="mark {cls}" style="left:{px(x)};top:{px(y)}"><b>{sym}</b>{lab}</div>'


def vbars(id, x, base, items, scale, barw=96, gap=40, val_size=21, lab_size=24, lab=True):
    """items: (name, value, color, ink, valtext). base = 기준선 y(프레임 좌표). 아이디 id-b{i}/v{i}/x{i}."""
    h = []
    for i, (name, value, color, ink, vt) in enumerate(items):
        bx = x + i * (barw + gap)
        hpx = value * scale
        h.append(f'<div id="{id}-b{i}" class="bar" style="left:{px(bx)};top:{px(base - hpx)};width:{barw}px;height:{px(hpx)};background:{color}"></div>')
        if vt:
            h.append(f'<div id="{id}-v{i}" class="tx" style="left:{px(bx - 60)};width:{px(barw + 120)};top:{px(base - hpx - val_size - 12)};'
                     f'font-size:{val_size}px;font-weight:700;color:{ink};text-align:center">{vt}</div>')
        if lab:
            h.append(f'<div id="{id}-x{i}" class="tx" style="left:{px(bx - 40)};width:{px(barw + 80)};top:{px(base + 12)};'
                     f'font-size:{lab_size}px;font-weight:700;color:{ink};text-align:center">{name}</div>')
    h.append(f'<div class="tx" style="left:{px(x - 20)};top:{px(base)};width:{px(len(items) * (barw + gap) - gap + 40)};height:2px;background:#9aa4a8"></div>')
    return "\n".join(h)


def hstack(id, x, y, w, h, total, segs, track=True, label_size=22):
    """segs: (value, color, label, label_color). 아이디 id-s{i}."""
    out = []
    if track:
        out.append(f'<div id="{id}-t" class="track" style="left:{px(x)};top:{px(y)};width:{px(w)};height:{px(h)}"></div>')
    cx = x
    for i, (v, color, label, lc) in enumerate(segs):
        sw = w * v / total
        inner = f'<span style="color:{lc}">{label}</span>' if label and sw >= 130 else ""
        out.append(f'<div id="{id}-s{i}" class="seg" style="left:{px(cx)};top:{px(y)};width:{px(sw)};height:{px(h)};background:{color};font-size:{label_size}px">{inner}</div>')
        cx += sw
    return "\n".join(out)


def gridlines(x, w, base, scale, steps, unit="억"):
    out = [f'<div class="gl" style="left:{px(x)};top:{px(base)};width:{px(w)};background:#9aa4a8"></div>']
    for s in steps:
        y = base - s * scale
        out.append(f'<div class="gl" style="left:{px(x)};top:{px(y)};width:{px(w)}"></div>')
        out.append(f'<div class="yl" style="left:{px(x - 64)};top:{px(y - 12)}">{s}{unit}</div>')
    out.append(f'<div class="yl" style="left:{px(x - 64)};top:{px(base - 12)}">0</div>')
    return "\n".join(out)


def eok(v):
    """억 단위 실수 → '약 6억1,400만원' (100만원 반올림)."""
    man = round(v * 1e4 / 100) * 100
    e, r = divmod(int(man), 10000)
    if e and r:
        return f"{e}억{r:,}만원"
    return f"{e}억원" if e else f"{r:,}만원"


# ---------------------------------------------------------------- 페이지
CSS = (HERE / "src/shell.css").read_text(encoding="utf8") if (HERE / "src/shell.css").exists() else ""
HELPERS = (HERE / "src/helpers.js").read_text(encoding="utf8") if (HERE / "src/helpers.js").exists() else ""


def build_chapter(num, scenes, tag="주거 방식 비교"):
    """scenes: list of dict(id,title,at(None=첫 장면),src,html,js)."""
    head, paras = chapter_paragraphs(num)
    cues = make_cues(paras)
    override = HERE / f"ch{num:02d}_timing_override.json"
    first = CARD_DUR + LEAD_AFTER_CARD
    total = time_cues(cues, first)
    if override.exists():
        ov = json.loads(override.read_text(encoding="utf8"))
        for c, o in zip(cues, ov["cues"]):
            c["start"], c["dur"] = o["start"], o["dur"]
        total = ov["total"]

    def cue_of(sub):
        for c in cues:
            if sub in c["text"]:
                return c
        raise KeyError(f"ch{num} anchor not found: {sub}")

    starts = []
    for i, s in enumerate(scenes):
        starts.append(CARD_DUR if i == 0 else round(cue_of(s["at"])["start"] - 0.3, 2))
    spans = [(st, round((starts[i + 1] if i + 1 < len(starts) else total) - st, 2)) for i, st in enumerate(starts)]

    body = []
    body.append(f'<section id="card" class="clip" data-start="0" data-duration="{CARD_DUR}" data-track-index="1">'
                f'<div class="wrap" id="card-w"><img class="cardbg" src="assets/chapter_bg.png" alt=""/><div class="cardgrad"></div>'
                f'<div id="card-t" class="cardtitle">{head}</div><div class="cardnote">AI 개념 이미지 · 실제 단지가 아닙니다</div></div></section>')
    rest = round(total - CARD_DUR, 2)
    body.append(f'<div id="brand" class="clip" data-start="{CARD_DUR}" data-duration="{rest}" data-track-index="0"><i>|</i><span>데이터로 보는 부동산</span></div>')
    body.append(f'<div id="tag" class="clip" data-start="{CARD_DUR}" data-duration="{rest}" data-track-index="0">{tag}</div>')
    for s, (st, du) in zip(scenes, spans):
        body.append(f'<h2 id="title-{s["id"]}" class="clip title" data-start="{st}" data-duration="{du}" data-track-index="2">{s["title"]}</h2>')
    for s, (st, du) in zip(scenes, spans):
        body.append(f'<section id="{s["id"]}" class="scene clip" data-start="{st}" data-duration="{du}" data-track-index="3"><div class="wrap" id="{s["id"]}-w">\n{s["html"]}\n</div></section>')
    body.append(f'<div id="capbox" class="clip" data-start="{CARD_DUR}" data-duration="{rest}" data-track-index="7"></div>')
    for s, (st, du) in zip(scenes, spans):
        body.append(f'<p id="src-{s["id"]}" class="clip source" data-start="{st}" data-duration="{du}" data-track-index="8">{s["src"]}</p>')
    for i, c in enumerate(cues):
        body.append(f'<p id="cue{i + 1:03d}" class="clip cue" data-start="{c["start"]}" data-duration="{c["dur"] + CUE_GAP:.2f}" data-track-index="9">{c["text"]}</p>')

    # 장면마다 블록 스코프: 장면 사이 const 이름 충돌 방지
    js_scenes = "\n".join("// " + s["id"] + " " + s["title"] + "\n{\n" + s["js"] + "\n}" for s in scenes)
    html = f"""<!doctype html>
<html lang="ko">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <title>{head}</title>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
{(HERE / "src/shell.css").read_text(encoding="utf8")}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{total}" data-width="1920" data-height="1080">
{chr(10).join(body)}
    </div>
    <script>
      const CUES = {json.dumps([[c["start"], c["text"]] for c in cues], ensure_ascii=False)};
      const SPANS = {json.dumps({s["id"]: sp for s, sp in zip(scenes, spans)})};
      const CARD = {CARD_DUR};
{(HERE / "src/helpers.js").read_text(encoding="utf8")}
{js_scenes}
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""
    out = HERE / f"ch{num:02d}"
    (out / "assets/fonts").mkdir(parents=True, exist_ok=True)
    for f in FONTS.glob("Pretendard-*.woff2"):
        if f.stem.split("-")[1] in ("Regular", "SemiBold", "Bold", "ExtraBold"):
            shutil.copy2(f, out / "assets/fonts" / f.name)
    shutil.copy2(CHAPTER_BG, out / "assets/chapter_bg.png")
    for extra in scenes_assets(scenes):
        shutil.copy2(extra, out / "assets" / Path(extra).name)
    (out / "index.html").write_text(html, encoding="utf8")
    (out / "hyperframes.json").write_text(json.dumps({
        "$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
        "registry": "https://raw.githubusercontent.com/heygen-com/hyperframes/main/registry",
        "paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"},
        "media": {"autoProxy": True}, "authoringSkill": "general-video"}, indent=2), encoding="utf8")
    (out / "meta.json").write_text(json.dumps({"id": f"housing-ch{num:02d}", "name": f"housing-ch{num:02d}"}, indent=2), encoding="utf8")
    (out / "package.json").write_text(json.dumps({"name": f"housing-ch{num:02d}", "private": True, "type": "module", "scripts": {
        "check": "npx --yes hyperframes@0.8.181 check", "render": "npx --yes hyperframes@0.8.181 render"}}, indent=2), encoding="utf8")
    (out / "timing_provisional.json").write_text(json.dumps({
        "basis": f"chapter card {CARD_DUR}s + Jun {CPS} chars/s estimate (gyosan v5 SRT); override with real voice alignment",
        "chapter": head, "total_seconds": total,
        "scenes": [{"id": s["id"], "title": s["title"], "start": sp[0], "dur": sp[1]} for s, sp in zip(scenes, spans)],
        "cues": cues}, ensure_ascii=False, indent=2), encoding="utf8")
    return head, total, len(cues), spans


def scenes_assets(scenes):
    out = []
    for s in scenes:
        out += s.get("assets", [])
    return out
