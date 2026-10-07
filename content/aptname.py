"""단지명을 사람들이 부르는 꼴로 다듬는다.

실거래가 원본의 단지명은 사람이 부르는 이름과 다르다. 가장 흔한 어긋남은
**끝의 '단지'가 통째로 빠지는 것**이다.

    원본        신트리4          목동신시가지12
    사람들      신트리4단지      목동신시가지12단지   (호갱노노·KB 표기)

"신트리4"를 영상에 그대로 띄우면 이름이 잘린 것처럼 읽힌다. 숫자가 몇 동인지
몇 단지인지도 알 수 없다.

여기서 하는 일 셋
  ① 끝이 맨숫자면 '단지'를 붙인다      신트리4   → 신트리4단지
  ② 숫자 묶음 앞을 띄운다              신트리4단지 → 신트리 4단지
  ③ 알려진 합성어 앞머리를 가른다      목동신시가지 → 목동 신시가지

②는 화면에서 읽히라고 하는 것이다. 공공 표기는 붙여 쓰지만 세로 영상에서
한 덩어리로 붙어 있으면 숫자가 묻힌다.

③은 **아는 것만** 가른다. 한국어 합성어를 일반 규칙으로 가르려 들면
"한신트리플"을 "한신 트리플"로 쪼개는 식의 사고가 난다. 확신하는 앞머리만
사전에 둔다.

그래도 안 맞는 이름은 `config/apt_aliases.json` 에 통째로 적는다. 매주 다루는
단지는 몇 곳뿐이라 손으로 적는 편이 규칙을 늘리는 것보다 안전하다.

    {"신트리4": "신트리 4단지"}
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ALIAS_PATH = ROOT / "config" / "apt_aliases.json"

# 아는 합성어 앞머리만, **가를 자리를 적어서** 가른다. 앞 몇 글자가 동네
# 이름이라는 식으로 어림하면 "올림픽선수기자촌"이 "올림 픽선수기자촌"이 된다.
SPLIT = (
    ("목동신시가지", "목동 신시가지"),
    ("올림픽선수기자촌", "올림픽 선수기자촌"),
)

# 끝이 "12단지" "3차" 처럼 숫자+꼬리로 끝나는 꼴
TAIL = re.compile(r"^(?P<head>.*?[^\s\d])\s*(?P<num>\d+)\s*(?P<suf>단지|차)$")
# 끝이 맨숫자인 꼴. 괄호로 끝나면(충무주공(872)) 걸리지 않는다.
BARE = re.compile(r"^(?P<head>.*?[^\s\d])\s*(?P<num>\d+)$")

_alias: dict | None = None


def aliases() -> dict:
    """손으로 적은 대표 명칭. 없거나 깨져 있으면 빈 사전."""
    global _alias
    if _alias is None:
        try:
            _alias = json.loads(ALIAS_PATH.read_text(encoding="utf-8"))
            if not isinstance(_alias, dict):
                _alias = {}
        except Exception:
            _alias = {}
    return _alias


def split_head(name: str) -> str:
    for tight, loose in SPLIT:
        if name.startswith(loose):     # 이미 갈라져 있다
            return name
        if name.startswith(tight):
            return loose + name[len(tight):]
    return name


def tidy(name: str | None) -> str:
    """사람이 부르는 꼴로. 같은 값을 다시 넣어도 그대로다(멱등).

    모르는 이름은 **건드리지 않는다**. 틀리게 고치는 것보다 그대로 두는 쪽이
    낫다 — 원본 이름이면 적어도 검색은 된다.
    """
    if not name:
        return ""
    s = " ".join(str(name).split())
    hit = aliases().get(s)
    if hit:
        return hit

    m = TAIL.match(s)
    if m:
        s = f'{m.group("head")} {m.group("num")}{m.group("suf")}'
    else:
        m = BARE.match(s)
        if m:
            # 맨숫자 꼬리는 거의 단지 번호다. 1~99 만 본다 — "SK뷰101" 같은
            # 세 자리는 동 번호일 수 있어 손대지 않는다.
            if 1 <= int(m.group("num")) <= 99:
                s = f'{m.group("head")} {m.group("num")}단지'
    return split_head(s)


def normalize(data: dict) -> dict:
    """지표 JSON 안의 단지명을 한 번에 다듬는다 (제자리 수정).

    이름이 쓰이는 곳이 표지·이웃·다른 평형·후보 목록·캡션으로 흩어져 있다.
    각자 다듬게 하면 한 곳을 빠뜨리고, 같은 단지가 화면마다 다른 이름으로
    나온다. 들어오는 길목에서 한 번에 바꾼다.
    """
    for grp in ("daily", "weekly"):
        for rows in (data.get(grp) or {}).values():
            if isinstance(rows, list):
                for r in rows:
                    if isinstance(r, dict) and r.get("apt_name"):
                        r["apt_name"] = tidy(r["apt_name"])
    for prof in (data.get("profiles") or {}).values():
        if not isinstance(prof, dict):
            continue
        if prof.get("apt_name"):
            prof["apt_name"] = tidy(prof["apt_name"])
        for nb in prof.get("neighbors") or []:
            if isinstance(nb, dict) and nb.get("apt_name"):
                nb["apt_name"] = tidy(nb["apt_name"])
        for ar in (prof.get("around") or {}).get("apts") or []:
            if isinstance(ar, dict) and ar.get("apt_name"):
                ar["apt_name"] = tidy(ar["apt_name"])
    return data


def main() -> int:
    import sys
    args = sys.argv[1:]
    if not args:
        print("사용: python -m content.aptname 신트리4 목동신시가지12")
        return 1
    for a in args:
        print(f"{a}  ->  {tidy(a)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
