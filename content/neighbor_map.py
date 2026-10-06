"""동네 지도 — 단지 주변을 도식으로.

안내도(게스트하우스 약도) 스타일이다. 지리적으로 정확한 지도가 아니라 **무엇이
어디쯤 있는지**를 한눈에 보여주는 그림이다. 그려 넣는 것은 다섯 가지뿐이다.

    상권      가게가 몰린 자리 (연한 띠)
    지하철역  역 아이콘 + 같은 노선끼리 이은 선
    단지      이 글의 주인공(별)과 주변 단지(점)
    자연      공원·하천 (연녹색 / 연파랑)
    라벨      이름

도로는 그리지 않는다. 좌표 데이터가 없고, 없는 걸 그럴듯하게 그리면 그 순간
지도가 거짓말이 된다. 대신 **지하철 노선**이 뼈대 역할을 한다.

재료는 전부 지표 JSON 의 `profiles[*].around` 에서 온다 — 캐러셀이 DB 를 따로
열지 않는다는 원칙은 지도에도 적용된다.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from content import design as D  # noqa: E402

# 지도에 담을 반경(m). 너무 넓히면 라벨이 겹치고, 좁히면 역이 안 들어온다.
RADIUS_M = 1100
PAD = 56

# 노선 색 — 실제 노선색을 쓰면 서울 사람에게 바로 읽힌다.
LINE_COLORS = {
    "1호선": "#0052A4", "2호선": "#00A84D", "3호선": "#EF7C1C",
    "4호선": "#00A5DE", "5호선": "#996CAC", "6호선": "#CD7C2F",
    "7호선": "#747F00", "8호선": "#E6186C", "9호선": "#BDB092",
    "경의중앙선": "#77C4A3", "분당선": "#FABE00", "신분당선": "#D4003B",
    "경춘선": "#0C8E72", "공항철도": "#0090D2", "우이신설선": "#B0CE18",
    "경강선": "#003DA5", "서해선": "#8FC31F", "김포골드라인": "#A17800",
    "신림선": "#6789CA", "수인선": "#FABE00", "경인선": "#0052A4",
}
LINE_FALLBACK = "#9AA0A6"


def line_color(name: str | None) -> str:
    if not name:
        return LINE_FALLBACK
    for k, v in LINE_COLORS.items():
        if k in name:
            return v
    return LINE_FALLBACK


def _m_per_deg(lat: float) -> tuple[float, float]:
    """위경도 1도가 몇 m 인가. 이 축척에서는 평면 근사로 충분하다."""
    return 111_320.0 * math.cos(math.radians(lat)), 110_540.0


def render(prof: dict, *, width: int, height: int, dark: bool = False,
           neighbors: list[dict] | None = None) -> str | None:
    """단지 주변 도식 지도 SVG."""
    lat0, lng0 = prof.get("lat"), prof.get("lng")
    a = prof.get("around") or {}
    if lat0 is None or lng0 is None:
        return None

    mx, my = _m_per_deg(lat0)

    # 축척은 **실제로 그릴 것들의 범위**에 맞춘다. 반경을 고정해 놓고 정사각
    # 비율로 맞추면, 가로로 긴 캔버스에서 그림이 가운데 40% 에만 몰린다.
    # 주인공을 가운데 두어야 하므로 좌우·상하 대칭으로 잡는다.
    feats = [(f["lat"], f["lng"])
             for key in ("stations", "parks", "commerce", "rivers")
             for f in (a.get(key) or [])]
    feats += [(f["lat"], f["lng"]) for f in (neighbors or [])
              if f.get("lat") is not None]
    def spread(vals: list[float]) -> float:
        """바깥 15% 는 버린다. 멀리 떨어진 상권 격자 하나 때문에 축척이
        내려가면 정작 단지 주변이 작아진다."""
        if not vals:
            return RADIUS_M
        vals = sorted(vals)
        return vals[int(len(vals) * 0.85)] or vals[-1]

    dx = [abs(ln - lng0) * mx for _, ln in feats]
    dy = [abs(la - lat0) * my for la, _ in feats]
    half_x = min(RADIUS_M, max(320.0, spread(dx) * 1.1))
    half_y = min(RADIUS_M, max(320.0, spread(dy) * 1.1))
    # x·y 축척은 같아야 한다 (따로 주면 지도가 찌그러진다). 그래서 남는
    # 여백은 **상자 비율**로 맞춘다 — 동네 데이터는 대체로 정사각이라
    # 가로로 긴 상자를 주면 좌우가 빈다. 카드 쪽에서 상자를 정사각에 가깝게
    # 잡아 둔다.
    scale = min((width - PAD * 2) / (half_x * 2),
                (height - PAD * 2) / (half_y * 2))

    def P(lat: float, lng: float) -> tuple[float, float]:
        return (width / 2 + (lng - lng0) * mx * scale,
                height / 2 - (lat - lat0) * my * scale)

    def inside(lat, lng, slack: float = 1.15) -> bool:
        x, y = P(lat, lng)
        return (-PAD * slack <= x <= width + PAD * slack
                and -PAD * slack <= y <= height + PAD * slack)

    # 지도는 **언제나 밝은 종이** 위에 그린다. 어두운 표지에서도 지도만
    # 밝으면 안내도처럼 읽힌다 — 어둡게 깔면 상권·공원 색이 전부 묻힌다.
    ink, sub, halo, paper = D.INK, D.SUB, "#FFFFFF", "#FFFFFF"
    parts: list[str] = [
        f'<rect width="{width}" height="{height}" rx="28" fill="{paper}"/>']

    # ── 상권: 가게가 몰린 격자를 둥근 띠로 뭉뚱그린다 ──────────────────
    #    격자 하나하나를 네모로 그리면 모자이크가 된다. 겹치는 원을 흐리게
    #    깔아 "이 언저리가 번화하다" 정도만 보이게 한다.
    shop = [c for c in a.get("commerce", [])
            if inside(c["lat"], c["lng"]) and c.get("total_stores", 0) >= 20]
    if shop:
        top = max(c["total_stores"] for c in shop)
        blobs = "".join(
            f'<circle cx="{P(c["lat"], c["lng"])[0]:.0f}" '
            f'cy="{P(c["lat"], c["lng"])[1]:.0f}" '
            f'r="{26 + 30 * (c["total_stores"] / top):.0f}"/>'
            for c in shop)
        parts.append(
            f'<g fill="#C5D6E8" opacity=".85" filter="url(#blur)">{blobs}</g>')

    # ── 자연: 공원 · 하천 ────────────────────────────────────────────
    for pk in a.get("parks", []):
        if not inside(pk["lat"], pk["lng"]):
            continue
        x, y = P(pk["lat"], pk["lng"])
        r = max(16, min(62, math.sqrt(pk.get("area_m2") or 0) * 0.09))
        parts.append(
            f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.0f}" '
            f'fill="#D6E8CC" opacity=".95"/>')
    big_parks = sorted((p for p in a.get("parks", [])
                        if inside(p["lat"], p["lng"])),
                       key=lambda p: p.get("area_m2") or 0, reverse=True)[:2]

    for rv in a.get("rivers", []):
        if not inside(rv["lat"], rv["lng"]):
            continue
        x, y = P(rv["lat"], rv["lng"])
        parts.append(
            f'<circle cx="{x:.0f}" cy="{y:.0f}" r="70" '
            f'fill="#CFE2EF" opacity=".9"/>')

    # ── 지하철: 같은 노선끼리 이어 뼈대를 만든다 ──────────────────────
    #    도로 좌표가 없어서 선을 그릴 수 없다. 노선이 그 자리를 대신한다.
    by_line: dict[str, list[dict]] = {}
    for st in a.get("stations", []):
        if inside(st["lat"], st["lng"]):
            by_line.setdefault(st.get("line") or "", []).append(st)
    for ln, sts in by_line.items():
        if len(sts) < 2:
            continue
        pts = sorted((P(s["lat"], s["lng"]) for s in sts), key=lambda p: p[0])
        d = "M" + "L".join(f"{x:.0f},{y:.0f}" for x, y in pts)
        parts.append(
            f'<path d="{d}" fill="none" stroke="{line_color(ln)}" '
            f'stroke-width="11" stroke-linecap="round" '
            f'stroke-linejoin="round" opacity=".55"/>')

    labels: list[tuple[float, float, str, str, int]] = []
    for st in a.get("stations", []):
        if not inside(st["lat"], st["lng"]):
            continue
        x, y = P(st["lat"], st["lng"])
        parts.append(
            f'<circle cx="{x:.0f}" cy="{y:.0f}" r="17" fill="{paper}" '
            f'stroke="{line_color(st.get("line"))}" stroke-width="6"/>')
        labels.append((x, y + 42, st["name"], ink, 26))

    # ── 단지 ─────────────────────────────────────────────────────────
    for nb in (neighbors or []):
        if nb.get("lat") is None or not inside(nb["lat"], nb["lng"]):
            continue
        x, y = P(nb["lat"], nb["lng"])
        parts.append(
            f'<rect x="{x - 11:.0f}" y="{y - 11:.0f}" width="22" height="22" '
            f'rx="6" fill="{D.NEUTRAL}" stroke="{paper}" stroke-width="3"/>')
        labels.append((x, y - 22, D.split_name(nb["apt_name"], 9)[0], sub, 24))

    # 라벨 충돌 회피 — 겹치면 **지우는 쪽**을 고른다.
    #
    # 겹친 글자는 둘 다 못 읽게 만들고, 지도까지 가린다. 라벨을 밀어내는
    # 방식은 위치가 틀어져서 "저 이름이 저기 있다"가 거짓이 된다. 역 이름을
    # 먼저 두고(뼈대), 자리가 남을 때만 단지 이름을 얹는다.
    taken: list[tuple[float, float, float, float]] = [
        (width / 2 - 150, height / 2 - 60, width / 2 + 150, height / 2 + 10)]

    def text_w(txt: str, size: float) -> float:
        """한글은 거의 1em, 영숫자는 0.55em. 한 계수로 뭉뚱그리면 한글
        라벨이 실제보다 절반쯤 좁게 계산돼 상자 밖으로 넘친다."""
        return sum(size * (1.0 if ord(ch) > 0x2000 else 0.55) for ch in txt)

    def fits(x: float, y: float, w: float, h: float) -> bool:
        box = (x - w / 2, y - h, x + w / 2, y + 4)
        if box[0] < 2 or box[2] > width - 2 or box[1] < 2 or box[3] > height - 2:
            return False
        for t in taken:
            if not (box[2] < t[0] or box[0] > t[2]
                    or box[3] < t[1] or box[1] > t[3]):
                return False
        taken.append(box)
        return True

    # 공원 이름도 같은 검사를 거친다. 따로 그리다가 주인공 별을 덮었다.
    labels += [(P(pk["lat"], pk["lng"])[0], P(pk["lat"], pk["lng"])[1] + 8,
                D.split_name(pk["name"], 8)[0], "#5B7A52", 24)
               for pk in big_parks]

    for x, y, txt, color, size in labels:
        if not fits(x, y, text_w(txt, size), size * 1.1):
            continue
        parts.append(
            f'<text x="{x:.0f}" y="{y:.0f}" text-anchor="middle" '
            f'font-size="{size}" font-weight="600" fill="{color}" '
            f'stroke="{halo}" stroke-width="5" paint-order="stroke" '
            f'style="font-family:Pretendard">{txt}</text>')
    # 주인공은 맨 위에. 별 모양으로 둬서 점들과 섞이지 않게 한다.
    cx, cy = width / 2, height / 2
    parts.append(
        f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="30" fill="{D.UP}" '
        f'opacity=".22"/>'
        f'<path d="{_star(cx, cy, 20, 9)}" fill="{D.UP}" stroke="{paper}" '
        f'stroke-width="3" stroke-linejoin="round"/>'
        f'<text x="{cx:.0f}" y="{cy - 36:.0f}" text-anchor="middle" '
        f'font-size="30" font-weight="800" fill="{D.UP}" stroke="{halo}" '
        f'stroke-width="6" paint-order="stroke" '
        f'style="font-family:Pretendard">'
        f'{D.split_name(prof["apt_name"], 11)[0]}</text>')

    return (f'<svg width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">'
            f'<defs><filter id="blur" x="-30%" y="-30%" width="160%" '
            f'height="160%"><feGaussianBlur stdDeviation="22"/></filter></defs>'
            f'{"".join(parts)}</svg>')


def _star(cx: float, cy: float, r: float, r2: float, n: int = 5) -> str:
    pts = []
    for i in range(n * 2):
        rad = r if i % 2 == 0 else r2
        ang = math.pi / n * i - math.pi / 2
        pts.append(f"{cx + rad * math.cos(ang):.1f},{cy + rad * math.sin(ang):.1f}")
    return "M" + "L".join(pts) + "Z"
