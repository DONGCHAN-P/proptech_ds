"""아젠다 공용 뼈대.

단지 소개 말고 **지역·비교 단위** 콘텐츠들이 공유하는 것만 모았다
(예산 지도 · 역세권 · 시간여행). 이들의 공통점은 "모르는 사람에게도 통한다"
는 것이다 — 릴스는 나를 모르는 사람에게 노출되는 매체라, 설명이 필요한
소재는 첫 2초를 못 넘긴다 (실측 평균 시청 2초 / 21초).

여기 둔 것은 **네 번 베껴 쓰게 될 것들**뿐이다. 장면 구성과 문구는 아젠다마다
다르므로 각자 모듈이 갖는다.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from content import design as D  # noqa: E402
from content import reels as R  # noqa: E402


def eok(man: float, digits: int = 1) -> str:
    """만원 → '6억' / '7.5억'. 딱 떨어지면 소수점을 버린다."""
    v = man / 10000
    return f"{v:.0f}억" if abs(v - round(v)) < 0.05 else f"{v:.{digits}f}억"


def man(won_per: float) -> str:
    """평당가처럼 만원 단위가 자연스러운 값."""
    return f"{round(won_per):,}만원"


def rows_html(items: list[tuple[str, str]]) -> str:
    """(왼쪽, 오른쪽) 목록. 막대 없이 이름과 값만.

    어두운 장에서도 읽히는지는 reels.css 가 책임진다 — 거기 색이 빠져
    있어서 검은 글씨가 검은 배경에 그려진 적이 있다.
    """
    cells = "".join(
        f'<div class="rv-bar"><div class="t">'
        f'<span>{a}</span><span>{b}</span></div></div>'
        for a, b in items)
    return f'<div class="rv-bars">{cells}</div>'


def bar_rows(items: list[tuple[str, float, str]], *,
             fmt=None) -> str:
    """(이름, 값, 색) 막대. 가장 큰 값을 가득 채운다."""
    mx = max((v for _, v, _ in items), default=1) or 1
    out = []
    for name, v, color in items:
        txt = fmt(v) if fmt else f"{v:,.0f}"
        out.append(
            f'<div class="rv-bar"><div class="t">'
            f'<span>{name}</span><span>{txt}</span></div>'
            f'<div class="track"><div class="fill" style="width:'
            f'{max(4, v / mx * 100):.1f}%;background:{color}"></div></div>'
            f'</div>')
    return f'<div class="rv-bars">{"".join(out)}</div>'


def follow(facts: dict, *, lead: str, notes: list[str]) -> dict:
    """마지막 장. 팔로우 + 그 아젠다의 주의사항.

    주의사항을 여기 모으는 이유: 앞 장에 끼우면 흐름이 끊기고, 아예 빼면
    "거래가 있었다"가 "지금 그 값에 살 수 있다"로 읽힌다.
    """
    note_html = "<br>".join(f"· {n}" for n in notes)
    return {
        "dark": False, "last": True, "facts": facts,
        "body": lambda p: (
            f'<div class="rv-kick" {R.anim(0, p)}>다음 주에도</div>'
            f'<div class="rv-h1" {R.anim(1, p)}>{lead}</div>'
            f'<div {R.anim(2, p)}><span class="rv-handle">'
            f'{D.HANDLE}</span></div>'
            f'<div class="rv-sub" {R.anim(3, p)}>{note_html}</div>'
            f'<div class="rv-disc" {R.anim(4, p)}>'
            f'{R.DISCLAIMER_SOCIAL}</div>'),
    }


def check(scs: list[dict], tag: str) -> list[str]:
    """발행 문구 검증. 영상에 박히는 글자도 발행물이다.

    화면에 뜬 숫자는 전부 facts 에 근거가 있어야 한다. 반올림한 값도
    발행되는 값이라 따로 대야 한다 — 0.77 만 담고 "77%" 를 쓰면 걸린다.
    """
    fails: list[str] = []
    for i, sc in enumerate(scs, 1):
        text = R.strip_html(sc["body"](1.0))
        D.assert_no_jargon(text, f"{tag}{i}")
        r = R.validate(text, {"card": sc["facts"]}, require_disclaimer=False)
        if not r.ok:
            fails += [f"{i}장: {w}" for w in r.reasons]
    return fails


def publish(scs: list[dict], tag: str, outdir: Path, name: str,
            *, dry: bool = False) -> Path | None:
    """검증 → 렌더. 검증에 걸리면 렌더하지 않는다."""
    fails = check(scs, tag)
    if fails:
        print(f"\n  검증 실패 {len(fails)}건 — 렌더하지 않는다")
        for x in fails:
            print(f"    ! {x}")
        raise RuntimeError("검증 실패: " + " / ".join(fails[:3]))
    print("  검증 통과")
    if dry:
        return None
    outdir.mkdir(parents=True, exist_ok=True)
    out = R.render(scs, outdir, name=name)
    print(f"\n  저장: {out}  ({out.stat().st_size / 1e6:.1f}MB)")
    return out
