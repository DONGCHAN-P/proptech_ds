"""3D 이모지 — 글자 카드를 그림 카드로 바꾸는 재료.

왜 필요한가
    12분짜리에서 글자 카드가 65% 였다. 그중 31% 는 **자막과 같은 말**을
    적고 있었다 — 카드를 먼저 만들고 자막을 나중에 붙여서 생긴 일이다.
    같은 문장이 화면에 두 번 떠 있으면 "글자가 많다"고 느낀다.

    참고한 쇼츠(손손)는 화면에 요소가 하나뿐이다. 큰 3D 이모지 하나 +
    자막 한 줄. 그 자리에 우리는 글자 덩어리를 넣고 있었다.

무엇을 쓰나
    Microsoft Fluent Emoji (MIT). 그 쇼츠가 쓰는 바로 그 3D 이모지다.
    MIT 라 출처만 적으면 상업적 사용도 된다 — 생성 이미지와 달리
    존재하지 않는 건물을 그리지도 않는다.

    받아 둔 파일은 assets/emoji/ 에 남는다. 매번 내려받지 않는다.

실행:
  python -m content.emoji            # 목록에 있는 것 전부 받기
  python -m content.emoji --list     # 어떤 이름이 있나
"""
from __future__ import annotations

import argparse
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / "assets" / "emoji"
BASE = ("https://raw.githubusercontent.com/microsoft/fluentui-emoji/"
        "main/assets")
CREDIT = "이모지: Microsoft Fluent Emoji (MIT)"

# 우리 대본에 쓸 것만. (별칭, Fluent 폴더명, 파일 이름)
# 파일 이름은 폴더명을 소문자·밑줄로 바꾼 꼴이라 대개 자동으로 맞는다.
SET = {
    "도시": "Cityscape",
    "돋보기": "Magnifying glass tilted left",
    "하락": "Chart decreasing",
    "상승": "Chart increasing",
    "자": "Straight ruler",
    "지하철": "Metro",
    "공사": "Building construction",
    "전구": "Light bulb",
    "경고": "Warning",
    "생각": "Thinking face",
    "나침반": "Compass",
    "돈": "Money bag",
    "지도": "World map",
    "모래시계": "Hourglass not done",
    "빌딩": "Office building",
    "물음표": "Red question mark",
    "눈": "Eyes",
    "퍼즐": "Puzzle piece",
    "확성기": "Megaphone",
    "손가락": "Index pointing up",
    "집": "House",
    "열쇠": "Key",
    "달력": "Calendar",
    "불": "Fire",
    "체크": "Check mark button",
    "엑스": "Cross mark",
    "저울": "Balance scale",
    "기차": "Bullet train",
    "공장": "Factory",
    "메모": "Memo",
}


def _slug(name: str) -> str:
    return name.lower().replace(" ", "_").replace("-", "_")


def urls(folder: str) -> list[str]:
    """3D 파일 경로 후보. 피부색이 있는 이모지는 Default 아래에 들어간다."""
    s = _slug(folder)
    q = urllib.parse.quote(folder)
    return [f"{BASE}/{q}/3D/{s}_3d.png",
            f"{BASE}/{q}/Default/3D/{s}_3d_default.png"]


def fetch(alias: str, folder: str, *, force: bool = False) -> Path | None:
    out = DIR / f"{alias}.png"
    if out.exists() and not force:
        return out
    DIR.mkdir(parents=True, exist_ok=True)
    for u in urls(folder):
        try:
            with urllib.request.urlopen(u, timeout=30) as r:
                data = r.read()
            if data[:4] == b"\x89PNG":
                out.write_bytes(data)
                return out
        except Exception:
            continue
    return None


def path(alias: str) -> Path | None:
    p = DIR / f"{alias}.png"
    return p if p.exists() else None


def data_uri(alias: str) -> str:
    """카드에 바로 꽂을 수 있게. 없으면 빈 문자열 — 카드는 글자만 남는다."""
    import base64
    p = path(alias)
    if not p:
        return ""
    return ("data:image/png;base64,"
            + base64.b64encode(p.read_bytes()).decode())


def img(alias: str, size: int = 300) -> str:
    u = data_uri(alias)
    if not u:
        return ""
    return (f'<img src="{u}" width="{size}" height="{size}" '
            f'style="width:{size}px;height:{size}px;display:block" alt="">')


def main() -> int:
    ap = argparse.ArgumentParser(description="3D 이모지 내려받기")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    if a.list:
        for k, v in SET.items():
            mark = "O" if path(k) else "."
            print(f"  {mark} {k:8} {v}")
        return 0

    ok, bad = [], []
    for alias, folder in SET.items():
        p = fetch(alias, folder, force=a.force)
        (ok if p else bad).append(alias)
        print(f"\r  받는 중 {len(ok) + len(bad)}/{len(SET)}", end="",
              flush=True)
    print()
    (DIR / "LICENSE.md").write_text(
        "# 이모지 출처\n\n"
        "Microsoft Fluent Emoji — MIT License\n"
        "https://github.com/microsoft/fluentui-emoji\n\n"
        "3D 버전 PNG 만 내려받아 쓴다. 가공하지 않았다.\n"
        f"화면 표기: {CREDIT}\n", encoding="utf-8")
    print(f"  받음 {len(ok)}개 · 실패 {len(bad)}개"
          + (f" ({', '.join(bad)})" if bad else ""))
    print(f"  저장: {DIR}")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
