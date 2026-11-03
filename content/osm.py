"""동네 한 곳을 가까이서 — OpenStreetMap 에서 **경계만** 받아 우리가 그린다.

왜 타일을 안 쓰나
    카카오맵·구글지도는 화면 캡처 재배포를 약관에서 막는다. VWorld 는
    공공데이터라 쓸 수 있지만 **인증키 발급이 전제**다. 키 없이 타일 CDN 을
    직접 때리는 건 약관을 우회하는 것이라 하지 않는다.

    대신 OSM 에서 **좌표**를 받아 우리 색으로 그린다. 시군구 경계를
    통계청 SGIS 에서 받아 그리는 것(`geo.py`)과 같은 방식이다. 지도 그림을
    퍼오는 게 아니라 데이터를 쓰는 것이므로 출처만 적으면 된다.

라이선스
    OpenStreetMap 데이터는 ODbL 1.0. **출처 표기가 의무**다.
    화면과 설명란에 "© OpenStreetMap contributors" 를 넣는다.

실행:
  python -m content.osm --name 광교호수공원 \
      --bbox 37.275,127.050,37.295,127.075
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

CACHE = ROOT / "assets" / "osm"
API = "https://overpass-api.de/api/interpreter"
CREDIT = "© OpenStreetMap contributors (ODbL)"
UA = "proptech-ds/1.0 (real-estate data video; contact via github)"


def fetch(bbox: tuple[float, float, float, float], *,
          name: str, force: bool = False) -> dict:
    """그 네모 안의 물·공원·주요 도로를 받아 둔다. 한 번 받으면 캐시한다.

    Overpass 는 공용 서버다. 같은 걸 매번 다시 묻지 않는 게 예의이고,
    렌더할 때마다 네트워크에 기대면 빌드가 네트워크 사정을 탄다.
    """
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / f"{name}.json"
    if f.exists() and not force:
        return json.loads(f.read_text(encoding="utf-8"))
    s, w, n, e = bbox
    box = f"{s},{w},{n},{e}"
    q = f"""[out:json][timeout:60];
(
  way["natural"="water"]({box});
  way["leisure"="park"]({box});
  way["highway"~"^(motorway|trunk|primary|secondary)$"]({box});
);
out geom;"""
    req = urllib.request.Request(
        API, data=urllib.parse.urlencode({"data": q}).encode(),
        headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=90) as r:
        data = json.loads(r.read())
    out = {"name": name, "bbox": list(bbox),
           "fetched": date.today().isoformat(),
           "source": "OpenStreetMap via Overpass API",
           "license": "ODbL 1.0", "credit": CREDIT,
           "elements": [
               {"kind": ("water" if el.get("tags", {}).get("natural") == "water"
                         else "park" if el.get("tags", {}).get("leisure") == "park"
                         else "road"),
                "name": (el.get("tags", {}).get("name")
                         or el.get("tags", {}).get("name:ko") or ""),
                "pts": [[p["lon"], p["lat"]] for p in el.get("geometry", [])]}
               for el in data.get("elements", []) if el.get("geometry")]}
    f.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    # 사진·음악과 같은 규칙 — 출처 없는 자산은 쓰지 않는다.
    f.with_suffix(".license.json").write_text(json.dumps({
        "source": "OpenStreetMap", "via": "Overpass API",
        "license": "Open Database License (ODbL) 1.0",
        "license_url": "https://opendatacommons.org/licenses/odbl/1-0/",
        "attribution_required": True, "credit": CREDIT,
        "note": ("타일 이미지를 퍼온 게 아니라 좌표만 받아 직접 그렸다. "
                 "그래도 ODbL 은 출처 표기가 의무다."),
        "acquired": date.today().isoformat(),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def load(name: str) -> dict | None:
    f = CACHE / f"{name}.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


def main() -> int:
    ap = argparse.ArgumentParser(description="OSM 경계 받아 두기")
    ap.add_argument("--name", required=True)
    ap.add_argument("--bbox", required=True,
                    help="남,서,북,동 (예: 37.275,127.050,37.295,127.075)")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    bb = tuple(float(x) for x in a.bbox.split(","))
    d = fetch(bb, name=a.name, force=a.force)  # type: ignore[arg-type]
    kinds: dict[str, int] = {}
    for el in d["elements"]:
        kinds[el["kind"]] = kinds.get(el["kind"], 0) + 1
    print(f"  {a.name}: " + " · ".join(f"{k} {v}개" for k, v in kinds.items()))
    print(f"  저장 {CACHE / (a.name + '.json')}")
    print(f"  출처 {CREDIT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
