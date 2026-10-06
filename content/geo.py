"""`map` 레이아웃 — 수도권 시군구 경계.

`docs/02_CLI_디자인지시사항.md` 5-0항. 경계는 **통계청 SGIS** 를 바탕으로 한
`statgarten/maps` (MIT) 를 쓴다. 지시사항이 직접 이름을 댄 자료이고, 라이선스가
명시돼 있다. 같은 문서가 언급한 다른 경계 파일은 라이선스가 `NOASSERTION` 이라
쓰지 않았다 — "확인하고 쓴다"가 규칙이다.

지도를 표지에 쓰는 이유는 사진의 대안이기 때문이다. 사진은 **오인**을 부른다 —
"마포구 ○○아파트 +53.5%" 옆에 아파트 사진이 있으면 보는 사람은 그게 그 단지라고
믿는다. 지도는 그 위험이 없고, 데이터에서 바로 나오며, 매주 달라진다.

준비 (한 번만):
  .venv\\Scripts\\python.exe -m content.geo --build
"""
from __future__ import annotations

import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEO_DIR = ROOT / "assets" / "geo"
GEO_FILE = GEO_DIR / "sudogwon_sgg.geojson"

BASE = "https://raw.githubusercontent.com/statgarten/maps/main/json/"
SOURCES = {
    "서울": "서울특별시_시군구_경계.json",
    "인천": "인천광역시_시군구_경계.json",
    "경기": "경기도_시군구_경계.json",
}
CREDIT = "경계: 통계청 SGIS (statgarten/maps, MIT)"

# 좌표계는 **경위도가 아니라 UTM-K(EPSG:5179) 투영 미터**다.
# 처음엔 경위도인 줄 알고 cos(위도) 보정을 넣었는데, cos(radians(1951000)) 이
# 엉뚱한 값을 내서 지도가 세로 줄무늬로 깨졌다. 투영 좌표는 이미 평면이라
# 보정이 필요 없다.
#
# 단순화 간격(m). 수도권 폭 약 120km 를 936px 에 그리므로 1px ≈ 130m 다.
# 그보다 촘촘한 점은 그려도 같은 픽셀에 찍힌다.
EPS = 120

# ── 이름 맞추기 ──────────────────────────────────────────────────────────
#
# 경계 파일의 코드는 SGIS 체계라 우리 법정동 시군구 코드와 다르다(강남구가
# 11230 vs 11680). 그래서 **이름**으로 맞춘다.
#
# 행정구역 개편으로 우리 데이터에는 있는데 경계에는 없는 곳이 있다. 그런 곳은
# 상위 시 경계로 대신 칠하고 `approx` 로 표시한다 — 실제보다 넓은 면이 칠해지므로
# 카드에 그 사실을 적는다. 숨기면 "저 동네 전체가 그렇다"로 읽힌다.
REORG = {
    # 부천: 2016 구 폐지 → 2024 재설치. 경계 파일은 부천시 하나뿐
    "부천원미구": "부천시", "부천소사구": "부천시", "부천오정구": "부천시",
    # 화성: 2026 분구
    "화성만세구": "화성시", "화성효행구": "화성시",
    "화성병점구": "화성시", "화성동탄구": "화성시",
    # 인천: 2026 개편 (중구·동구 → 제물포구·영종구 / 서구 → 서구·검단구)
    "제물포구": "중구", "영종구": "중구", "검단구": "서구",
}
EXACT = {"광주시(경기)": "광주시", "중구(인천)": "중구",
         "동구(인천)": "동구", "서구(인천)": "서구"}
# "고양덕양구" → "고양시 덕양구"
_SPLIT = re.compile(r"^(수원|성남|안양|안산|고양|용인|부천|화성)(.+구)$")


def geo_name(name: str) -> tuple[str, bool]:
    """(경계 파일에서 찾을 이름, 근사 여부)."""
    if name in REORG:
        return REORG[name], True
    if name in EXACT:
        return EXACT[name], False
    m = _SPLIT.match(name)
    if m:
        return f"{m.group(1)}시 {m.group(2)}", False
    return name, False


# ── 빌드 ─────────────────────────────────────────────────────────────────
def _thin(ring: list) -> list:
    """같은 픽셀에 찍힐 점을 솎아낸다."""
    out = [[round(ring[0][0]), round(ring[0][1])]]
    for x, y in ring[1:]:
        px, py = out[-1]
        if abs(x - px) >= EPS or abs(y - py) >= EPS:
            out.append([round(x), round(y)])
    if out[0] != out[-1]:
        out.append(out[0])
    return out


def _simplify(geom: dict) -> dict:
    polys = (geom["coordinates"] if geom["type"] == "MultiPolygon"
             else [geom["coordinates"]])
    keep = []
    for poly in polys:
        rings = [_thin(r) for r in poly if len(r) >= 4]
        rings = [r for r in rings if len(r) >= 4]
        if rings:
            keep.append(rings)
    return {"type": "MultiPolygon", "coordinates": keep}


def build() -> Path:
    GEO_DIR.mkdir(parents=True, exist_ok=True)
    feats = []
    for region, fname in SOURCES.items():
        url = BASE + urllib.parse.quote(fname)
        print(f"  받는 중 … {fname}")
        with urllib.request.urlopen(url, timeout=120) as r:
            d = json.loads(r.read().decode("utf-8"))
        for f in d["features"]:
            feats.append({
                "type": "Feature",
                "properties": {"name": f["properties"]["title"].strip(),
                               "region": region},
                "geometry": _simplify(f["geometry"]),
            })
    out = {"type": "FeatureCollection", "credit": CREDIT, "features": feats}
    GEO_FILE.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")),
                        encoding="utf-8")
    (GEO_DIR / "LICENSE.md").write_text(
        "# 수도권 시군구 경계\n\n"
        "- 출처: [statgarten/maps](https://github.com/statgarten/maps) "
        "(통계청 SGIS API 기반)\n"
        "- 라이선스: MIT\n"
        f"- 표기 문구: `{CREDIT}`\n"
        "- 받은 날: 2026-10-06\n"
        "- 가공: 서울·인천·경기만 합치고 좌표를 "
        f"{PRECISION}자리로 반올림, {EPS}° 간격으로 점을 솎아냄\n\n"
        "지시사항 5-0항에 따라 이용허락 범위를 확인하고 각주에 출처를 넣는다.\n",
        encoding="utf-8")
    print(f"  저장: {GEO_FILE}  ({GEO_FILE.stat().st_size / 1e6:.2f}MB, "
          f"{len(feats)}개 시군구)")
    return GEO_FILE


# ── 그리기 ───────────────────────────────────────────────────────────────
_cache: dict | None = None


def load() -> dict | None:
    global _cache
    if _cache is None:
        if not GEO_FILE.exists():
            return None
        _cache = json.loads(GEO_FILE.read_text(encoding="utf-8"))
    return _cache


def available() -> bool:
    return GEO_FILE.exists()


def mix(hex_a: str, hex_b: str, t: float) -> str:
    """두 색을 섞는다. 증감 색의 농담을 만들 때 쓴다.

    빨강·파랑 **계열 안에서만** 농도를 바꾼다. 새 색상을 들이면 "빨강=증가,
    파랑=감소"라는 신호가 흐려진다 (지시사항 3항).
    """
    a = [int(hex_a[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(hex_b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(a, b))


def scope_of(code: str | None) -> str | None:
    """시군구 코드 → 시도. 11 서울 · 28 인천 · 41 경기."""
    return {"11": "서울", "28": "인천", "41": "경기"}.get(str(code or "")[:2])


def svg(highlight: dict[str, str], *, width: int, height: int,
        line: str, fill: str, label_color: str,
        label_halo: str = "#FFFFFF",
        scope: str | None = None,
        pins: list[dict] | None = None) -> str | None:
    """수도권 지도 SVG.

    `highlight` 는 {우리 시군구명: 색}. 거기 없는 곳은 전부 중립색이다 —
    지시사항 5-0항의 "대상 지역만 색"이 그 뜻이다. 라벨도 대상에만 단다.
    전부에 이름을 달면 어디를 보라는 건지 사라진다.
    """
    data = load()
    if not data:
        return None
    # 수도권 전체를 그리면 서울 한 구가 점만 해진다. 대상이 속한 시도로
    # 좁히면 "어디인지"가 바로 읽힌다. 경기도는 시·군이 커서 전체로 둬도 된다.
    feats = [f for f in data["features"]
             if scope is None or f["properties"]["region"] == scope]
    if not feats:
        feats = data["features"]
    fill_pin = next(iter(highlight.values()), label_color)
    want = {}
    for name, color in highlight.items():
        g, _ = geo_name(name)
        want[g] = (color, name)

    xs, ys = [], []
    for f in feats:
        for poly in f["geometry"]["coordinates"]:
            for x, y in poly[0]:
                xs.append(x)
                ys.append(y)
    if not xs:
        return None
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    w, h = (x1 - x0) or 1, (y1 - y0) or 1
    scale = min(width / w, height / h) * 0.96
    ox = (width - w * scale) / 2
    oy = (height - h * scale) / 2

    def P(x, y):
        return (ox + (x - x0) * scale,
                oy + (y1 - y) * scale)      # SVG 는 y 가 아래로 증가

    parts, labels = [], []
    for f in feats:
        nm = f["properties"]["name"]
        hit = want.get(nm)
        d = []
        cx = cy = n = 0
        for poly in f["geometry"]["coordinates"]:
            for ring in poly:
                pts = [P(x, y) for x, y in ring]
                d.append("M" + "L".join(f"{a:.1f},{b:.1f}" for a, b in pts) + "Z")
                if hit:
                    for a, b in pts:
                        cx += a
                        cy += b
                        n += 1
        parts.append(f'<path d="{"".join(d)}" fill="{hit[0] if hit else fill}" '
                     f'stroke="#FFFFFF" stroke-width="2" '
                     f'stroke-linejoin="round"/>')
        if hit and n:
            labels.append((cx / n, cy / n, hit[1]))

    for x, y, nm in labels:
        parts.append(
            f'<text x="{x:.0f}" y="{y:.0f}" text-anchor="middle" '
            f'font-size="30" font-weight="700" fill="{label_color}" '
            f'stroke="{label_halo}" stroke-width="5" paint-order="stroke" '
            f'style="font-family:Pretendard">{nm}</text>')
    # 단지 핀. 경계는 투영 미터라 위경도를 같은 좌표계로 옮겨 찍는다.
    for pin in (pins or []):
        if pin.get("lat") is None or pin.get("lng") is None:
            continue
        px, py = P(*to_utmk(pin["lng"], pin["lat"]))
        if pin.get("primary"):
            parts.append(
                f'<circle cx="{px:.1f}" cy="{py:.1f}" r="22" fill="{line}" '
                f'opacity=".35"/>'
                f'<circle cx="{px:.1f}" cy="{py:.1f}" r="11" fill="{fill_pin}" '
                f'stroke="#FFFFFF" stroke-width="4"/>')
        else:
            parts.append(
                f'<circle cx="{px:.1f}" cy="{py:.1f}" r="7" '
                f'fill="{label_color}" opacity=".55" '
                f'stroke="{label_halo}" stroke-width="2"/>')
        if pin.get("label"):
            parts.append(
                f'<text x="{px:.1f}" y="{py - 28:.1f}" text-anchor="middle" '
                f'font-size="30" font-weight="800" fill="{label_color}" '
                f'stroke="{label_halo}" stroke-width="6" paint-order="stroke" '
                f'style="font-family:Pretendard">{pin["label"]}</text>')

    return (f'<svg width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">{"".join(parts)}</svg>')


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="수도권 시군구 경계 준비")
    ap.add_argument("--build", action="store_true")
    a = ap.parse_args()
    if a.build:
        build()
        return 0
    print("경계 파일 있음" if available() else "없음 — --build 로 받으세요")
    return 0


if __name__ == "__main__":
    sys.exit(main())


# ── 온도지도 ─────────────────────────────────────────────────────────────
# 범위 계산에서 빼는 지역. 백령도·연평도가 서쪽으로 100km 넘게 떨어져 있어
# 그대로 두면 bbox 가 두 배로 늘고 수도권 본토가 화면 오른쪽 절반에만 그려진다.
# **그리기는 그대로** 하고 범위 계산에서만 뺀다 — 뷰박스 밖으로 나가면
# 자연히 잘린다. 아파트 실거래가 거의 없는 곳이라 색도 비어 있다.
BBOX_SKIP = {"옹진군"}


def _bbox(feats: list[dict]) -> tuple[float, float, float, float]:
    xs, ys = [], []
    for f in feats:
        if f["properties"]["name"] in BBOX_SKIP:
            continue
        for poly in f["geometry"]["coordinates"]:
            for x, y in poly[0]:
                xs.append(x)
                ys.append(y)
    if not xs:
        xs, ys = [0, 1], [0, 1]
    return min(xs), max(xs), min(ys), max(ys)


def heat(values: dict[str, float], *, width: int, height: int,
         bg: str, up: str, down: str, dim: str,
         labels: dict[str, str] | None = None) -> str | None:
    """수도권 전체를 평소 대비 배수로 칠한다.

    `map_cover` 가 대상 하나만 칠하는 것과 다르다. 여기서는 **어디가 뜨겁고
    어디가 식었는지**를 한 장에 보여주는 게 목적이라, 전부 칠해야 그림이 된다.

    농도는 5단계로 끊는다. 연속 그라데이션으로 칠하면 예쁘지만 "이 색이 몇
    배인지"를 읽을 수 없다. 끊어 두면 범례와 1:1로 대응한다.

    `values` 에 없는 지역은 `dim` (표본 부족·판단 보류)으로 둔다. 회색으로
    칠하지 않고 비워 두면 "데이터가 없다"가 "변화가 없다"로 읽힌다.
    """
    data = load()
    if not data:
        return None
    x0, x1, y0, y1 = _bbox(data["features"])
    w, h = (x1 - x0) or 1, (y1 - y0) or 1
    scale = min(width / w, height / h) * 0.98
    ox, oy = (width - w * scale) / 2, (height - h * scale) / 2

    # 우리 이름 → 경계 이름. 개편으로 여러 구가 한 면을 가리키면 가장 센 쪽을 쓴다.
    byname: dict[str, float] = {}
    for name, v in values.items():
        g, _ = geo_name(name)
        if g not in byname or abs(v - 1) > abs(byname[g] - 1):
            byname[g] = v

    parts = []
    for f in data["features"]:
        nm = f["properties"]["name"]
        v = byname.get(nm)
        parts.append(
            f'<path d="{_path(f, ox, oy, y1, x0, scale)}" '
            f'fill="{bin_color(v, bg, up, down, dim)}" '
            f'stroke="#FFFFFF" stroke-width="1.6" stroke-linejoin="round"/>')
    for nm, txt in (labels or {}).items():
        g, _ = geo_name(nm)
        f = next((x for x in data["features"]
                  if x["properties"]["name"] == g), None)
        if not f:
            continue
        cx, cy, n = 0.0, 0.0, 0
        for poly in f["geometry"]["coordinates"]:
            for x, y in poly[0]:
                cx += ox + (x - x0) * scale
                cy += oy + (y1 - y) * scale
                n += 1
        if n:
            parts.append(
                f'<text x="{cx / n:.0f}" y="{cy / n:.0f}" text-anchor="middle" '
                f'font-size="28" font-weight="800" fill="#111111" '
                f'stroke="#FFFFFF" stroke-width="6" paint-order="stroke" '
                f'style="font-family:Pretendard">{txt}</text>')
    return (f'<svg width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">{"".join(parts)}</svg>')


# 평소 대비 배수 구간. 범례와 1:1 로 대응한다.
BINS = [(0.75, "down", 1.0), (0.9, "down", 0.45),
        (1.1, None, 0.0), (1.3, "up", 0.45), (9e9, "up", 1.0)]
BIN_LABELS = ["0.8배 이하", "0.9배", "평소", "1.2배", "1.3배 이상"]


def bin_color(v: float | None, bg: str, up: str, down: str, dim: str) -> str:
    if v is None:
        return dim
    for edge, side, t in BINS:
        if v < edge:
            if side is None:
                return mix(bg, "#000000", 0.07)
            return mix(bg, up if side == "up" else down, t)
    return dim


def legend_colors(bg: str, up: str, down: str) -> list[tuple[str, str]]:
    out = []
    for (edge, side, t), lab in zip(BINS, BIN_LABELS):
        c = (mix(bg, "#000000", 0.07) if side is None
             else mix(bg, up if side == "up" else down, t))
        out.append((c, lab))
    return out


def _path(f: dict, ox: float, oy: float, y1: float, x0: float,
          scale: float) -> str:
    d = []
    for poly in f["geometry"]["coordinates"]:
        for ring in poly:
            pts = [(ox + (x - x0) * scale, oy + (y1 - y) * scale)
                   for x, y in ring]
            d.append("M" + "L".join(f"{a:.1f},{b:.1f}" for a, b in pts) + "Z")
    return "".join(d)


# ── 좌표 변환 (WGS84 → EPSG:5179) ────────────────────────────────────────
#
# 경계는 UTM-K(Korea 2000 Unified, EPSG:5179) 투영 미터인데 단지 좌표는
# 위경도다. 지도에 단지 핀을 찍으려면 같은 좌표계로 옮겨야 한다.
#
# pyproj 를 쓰지 않는다 — 의존성 하나를 더 들이는 대신, 파라미터가 공개된
# 표준 횡축 메르카토르 식을 그대로 옮긴다. 아래 상수가 EPSG:5179 정의다.
# (`tests/test_cover.py` 가 시군구 경계 중심과 대조해 오차를 확인한다.)
import math  # noqa: E402

_A = 6378137.0                 # GRS80 장반경
_F = 1 / 298.257222101         # GRS80 편평률
_K0, _LAT0, _LON0 = 0.9996, 38.0, 127.5
_X0, _Y0 = 1_000_000.0, 2_000_000.0


def to_utmk(lng: float, lat: float) -> tuple[float, float]:
    """위경도 → EPSG:5179 (m). 표준 TM 전개식."""
    e2 = _F * (2 - _F)
    ep2 = e2 / (1 - e2)
    p, l = math.radians(lat), math.radians(lng)
    p0, l0 = math.radians(_LAT0), math.radians(_LON0)

    def M(phi: float) -> float:
        return _A * (
            (1 - e2 / 4 - 3 * e2**2 / 64 - 5 * e2**3 / 256) * phi
            - (3 * e2 / 8 + 3 * e2**2 / 32 + 45 * e2**3 / 1024) * math.sin(2 * phi)
            + (15 * e2**2 / 256 + 45 * e2**3 / 1024) * math.sin(4 * phi)
            - (35 * e2**3 / 3072) * math.sin(6 * phi))

    N = _A / math.sqrt(1 - e2 * math.sin(p) ** 2)
    T = math.tan(p) ** 2
    C = ep2 * math.cos(p) ** 2
    A = (l - l0) * math.cos(p)
    x = _X0 + _K0 * N * (
        A + (1 - T + C) * A**3 / 6
        + (5 - 18 * T + T**2 + 72 * C - 58 * ep2) * A**5 / 120)
    y = _Y0 + _K0 * (
        M(p) - M(p0) + N * math.tan(p) * (
            A**2 / 2 + (5 - T + 9 * C + 4 * C**2) * A**4 / 24
            + (61 - 58 * T + T**2 + 600 * C - 330 * ep2) * A**6 / 720))
    return x, y
