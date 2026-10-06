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


def scope_of(code: str | None) -> str | None:
    """시군구 코드 → 시도. 11 서울 · 28 인천 · 41 경기."""
    return {"11": "서울", "28": "인천", "41": "경기"}.get(str(code or "")[:2])


def svg(highlight: dict[str, str], *, width: int, height: int,
        line: str, fill: str, label_color: str,
        scope: str | None = None) -> str | None:
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
            f'stroke="#FFFFFF" stroke-width="5" paint-order="stroke" '
            f'style="font-family:Pretendard">{nm}</text>')
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
