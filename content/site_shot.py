"""평소지도(pulse) 화면을 캡처해 카드·영상에 쓴다.

도식 지도(neighbor_map)는 우리가 직접 그려서 글자가 또렷하지만, **값이
없다**. 평소지도 단지 레이어에는 주변 단지마다 실거래가가 붙어 있어서
"이 단지 10.3억, 옆은 7.7억"이 한 장으로 읽힌다. 비교를 말로 설명하지
않아도 된다.

대신 세 가지를 지켜야 쓸 만해진다.

① **가까이 당긴다.** 서울 전체를 찍으면 마커 220개가 겹쳐 아무것도 안
   읽힌다 (실측). 단지 하나를 가운데 두고 줌 16 정도.
② **2배로 찍고 줄인다.** 848px 슬롯에 1:1 로 찍으면 글자가 뭉갠다.
③ **UI 를 걷어낸다.** 왼쪽 패널·검색창·레이어 버튼은 영상에서 군더더기다.
   지도만 남긴다.

지도 타일은 OpenStreetMap 이다. 출처를 반드시 같이 싣는다 — CREDIT 을
쓰는 쪽에서 꼬리말에 넣는다. (주 1회 몇 장은 OSMF 타일 정책이 막는 대량·
자동 수집이 아니지만, 출처 표기는 면제되지 않는다.)

서버가 안 뜨거나 캡처가 실패하면 **None** 을 돌려준다. 부르는 쪽은 도식
지도로 돌아가면 된다 — 지도 하나 때문에 발행이 멈추면 안 된다.
"""
from __future__ import annotations

import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

HOST, PORT = "127.0.0.1", 8011     # run.bat 의 8001 과 겹치지 않게
ZOOM = 15                          # 주변 단지 10여 곳이 같이 잡히는 줌.
                                   # 16 은 단지 하나만 남아 비교가 사라진다
BOOT_TIMEOUT = 40                  # 서버가 뜨기까지 기다리는 한도 (초)
SCALE = 2                          # 2배로 찍어 줄인다 — 글자가 또렷해진다
SETTLE_MS = 2500                   # 타일·마커가 다 올라올 때까지

CREDIT = "지도 © OpenStreetMap contributors"

# 영상에 필요 없는 UI. 지도만 남긴다.
HIDE = """
  #side, #levelbar, #searchbar, #q, #statebar, #pyeongbar,
  .leaflet-control-zoom, #panel, .leaflet-control-attribution,
  .leaflet-tooltip, .leaflet-popup
    { display: none !important; }
  html, body { background: #EFEDE7 !important; }
  #map { position: fixed !important; inset: 0 !important;
         width: 100vw !important; height: 100vh !important; }
  /* 주인공만 남기고 나머지는 한 톤 죽인다 — 셋 다 빨가면 어느 게
     이 영상의 단지인지 알 수 없다 */
  .apt-dim { opacity: .55 !important; }
  .apt-me { z-index: 9999 !important; transform-origin: 50% 100%; }
  .apt-me > * { box-shadow: 0 0 0 6px rgba(229,72,77,.35) !important; }
"""

# 가운데에 가장 가까운 마커가 이 영상의 단지다. flyTo 가 그 자리를
# 한가운데 놓으므로 좌표를 다시 재지 않아도 된다.
MARK_JS = """() => {
  const els = [...document.querySelectorAll('#map .leaflet-marker-icon')];
  if (!els.length) return 0;
  const cx = innerWidth / 2, cy = innerHeight / 2;
  let best = null, bd = 1e9;
  for (const el of els) {
    const r = el.getBoundingClientRect();
    const d = Math.hypot(r.left + r.width / 2 - cx, r.bottom - cy);
    if (d < bd) { bd = d; best = el; }
  }
  for (const el of els) el.classList.add('apt-dim');
  if (best) { best.classList.remove('apt-dim'); best.classList.add('apt-me'); }
  return els.length;
}"""


def up(host: str = HOST, port: int = PORT) -> bool:
    """이미 떠 있나."""
    with socket.socket() as s:
        s.settimeout(0.4)
        return s.connect_ex((host, port)) == 0


def serve() -> subprocess.Popen | None:
    """캡처용 서버를 띄운다. 이미 떠 있으면 그대로 쓴다."""
    if up():
        return None
    cmd = [sys.executable, "-m", "uvicorn", "pulse.main:app",
           "--host", HOST, "--port", str(PORT), "--log-level", "warning"]
    p = subprocess.Popen(cmd, cwd=str(ROOT),
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    t0 = time.time()
    while time.time() - t0 < BOOT_TIMEOUT:
        if up():
            return p
        if p.poll() is not None:        # 죽었으면 더 기다릴 이유가 없다
            return None
        time.sleep(0.4)
    p.terminate()
    return None


def capture(lat: float, lng: float, width: int, height: int,
            *, zoom: int = ZOOM, pyeong: str = "") -> bytes | None:
    """단지를 가운데 둔 지도 한 장. 실패하면 None."""
    if lat is None or lng is None:
        return None
    from playwright.sync_api import sync_playwright

    proc = serve()
    try:
        if not up():
            print("  [평소지도] 서버가 뜨지 않았다 — 도식 지도로 간다")
            return None
        # 2배로 찍어 줄이므로 뷰포트도 그만큼
        vw, vh = width, height
        with sync_playwright() as pw:
            br = pw.chromium.launch()
            page = br.new_page(viewport={"width": vw, "height": vh},
                               device_scale_factor=SCALE)
            try:
                page.goto(f"http://{HOST}:{PORT}/", wait_until="load",
                          timeout=30000)
                page.wait_for_function("typeof MapView !== 'undefined'",
                                       timeout=15000)
                # 단지 레이어로 바꾸고 그 자리로 간다
                page.click('button[data-level="apt"]')
                # 평형을 안 고르면 '대표 평형'(거래가 가장 많은 평형)이 뜬다.
                # 영상이 20평대 10.3억을 말하는데 지도에 26평 9.1억이 찍히면
                # 보는 사람은 둘 중 뭐가 맞는지 모른다. 같은 평형으로 맞춘다.
                if pyeong:
                    sel = f'button.chip[data-py="{pyeong}"]'
                    if page.locator(sel).count():
                        page.click(sel)
                        page.wait_for_timeout(600)
                    else:
                        print(f"  [평소지도] {pyeong} 칩이 없다 — 대표 평형으로 간다")
                page.evaluate(
                    "([a,b,z]) => MapView.flyTo(a,b,z)", [lat, lng, zoom])
                page.wait_for_timeout(SETTLE_MS)
                page.add_style_tag(content=HIDE)
                # UI 를 걷어내면 지도 그릇의 크기가 바뀐다. 알려주지 않으면
                # 타일이 예전 크기대로 남아 아래쪽이 비어 버린다.
                page.evaluate("() => dispatchEvent(new Event('resize'))")
                page.wait_for_timeout(1200)
                n = page.evaluate(MARK_JS)
                if not n:
                    print("  [평소지도] 마커가 없다 — 도식 지도로 간다")
                    return None
                page.wait_for_timeout(200)
                return page.screenshot(type="png")
            finally:
                br.close()
    except Exception as e:
        print(f"  [평소지도] 캡처 실패 ({type(e).__name__}) — 도식 지도로 간다")
        return None
    finally:
        if proc is not None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except Exception:
                proc.kill()


def data_uri(png: bytes) -> str:
    import base64
    return "data:image/png;base64," + base64.b64encode(png).decode()


def img_tag(png: bytes, width: int, height: int, radius: int = 20) -> str:
    """카드에 바로 꽂을 <img>. 모서리는 카드 톤에 맞춰 둥글린다."""
    return (f'<img src="{data_uri(png)}" width="{width}" height="{height}" '
            f'style="width:{width}px;height:{height}px;object-fit:cover;'
            f'border-radius:{radius}px;display:block" alt="">')


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="평소지도 캡처 시험")
    ap.add_argument("--lat", type=float, required=True)
    ap.add_argument("--lng", type=float, required=True)
    ap.add_argument("--w", type=int, default=848)
    ap.add_argument("--h", type=int, default=330)
    ap.add_argument("--zoom", type=int, default=ZOOM)
    ap.add_argument("--pyeong", default="")
    ap.add_argument("--out", default="site_shot.png")
    a = ap.parse_args()
    png = capture(a.lat, a.lng, a.w, a.h, zoom=a.zoom,
                  pyeong=a.pyeong)
    if not png:
        return 1
    Path(a.out).write_bytes(png)
    print(f"  저장: {a.out} ({len(png) / 1024:.0f}KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
