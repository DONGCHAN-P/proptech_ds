"""T14 — 주간 롱폼 대본.

구성은 고정이다.

    Hook → 주간 Z-score 지역 → 급등 단지 심층 → 반대 지표 → 정리

**반대 지표 절이 이 템플릿의 핵심이다.** 오른 것만 늘어놓으면 투자 권유처럼
읽힌다. 같은 데이터 안에서 그 이야기를 약화시키는 신호를 찾아 같은 비중으로
싣는다. 보일러플레이트가 아니라 매번 숫자에서 고른다 — 가격 지표는 올랐는데
거래량은 평소보다 적은 지역, 거래가 줄면서 오른 단지 같은 것들.

T12 검증기를 그대로 통과해야 한다. 유튜브 면책은 `kind="youtube"` 로 따로
검사한다 (스레드용과 문구가 다르다).

실행:
  .venv\\Scripts\\python.exe -m content.longform
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from content.validator import validate  # noqa: E402
from templates.disclaimers import (  # noqa: E402
    CTA_NEWSLETTER, CTA_PLACEHOLDER_URL, DISCLAIMER_YOUTUBE, SOURCE_NOTE,
)

THIN_SAMPLE = 20      # 주간 거래가 이보다 적으면 문장에 밝힌다
STRONG_Z = 1.0        # 이 이상이면 "평소와 다르다"고 말할 만하다


def won(man) -> str:
    if man is None:
        return "-"
    man = float(man)
    if abs(man) >= 10000:
        v = man / 10000
        return f"{v:.0f}억" if abs(v) >= 100 else f"{v:.1f}억"
    return f"{man:,.0f}만"


def num(v) -> str:
    """낭독용 숫자. 평단가 3628.0 을 '3,628' 로 읽게 만든다."""
    if v is None:
        return "-"
    f = float(v)
    return f"{f:,.0f}" if f == int(f) else f"{f:,.1f}"


def josa(word: str, pair: str) -> str:
    """받침에 맞는 조사를 붙인다. '황골마을주공1는' 같은 걸 막는다.

    pair 는 '은는' '이가' '을를' '과와' 형태. 끝 글자가 한글이면 종성으로,
    숫자면 그 숫자의 한국어 발음 받침으로 판단한다 (1=일 받침 있음,
    2=이 없음 …). 영문·기호로 끝나면 받침 없음으로 둔다.
    """
    with_, without = pair[0], pair[1:]
    if not word:
        return without
    ch = word.strip()[-1]
    if "가" <= ch <= "힣":
        return with_ if (ord(ch) - 0xAC00) % 28 else without
    if ch.isdigit():
        # 일 삼 육 칠 팔 십 = 받침 있음 / 이 사 오 구 영 = 없음
        return with_ if ch in "1368" or ch == "0" else without
    return without


def J(word: str, pair: str) -> str:
    """단어 + 알맞은 조사."""
    return f"{word}{josa(word, pair)}"


def cta() -> str:
    import os
    url = os.environ.get("NEWSLETTER_URL", "").strip() or CTA_PLACEHOLDER_URL
    return CTA_NEWSLETTER.format(url=url)


# ── 소재 고르기 ──────────────────────────────────────────────────────────
def pick_topics(data: dict) -> dict | None:
    """대본에 쓸 소재를 고른다. 재료가 모자라면 None — 그런 주는 만들지 않는다."""
    z = [r for r in (data.get("weekly", {}).get("sgg_zscore") or [])
         if r.get("deals_z") is not None and r.get("ppy_z") is not None]
    surge = data.get("weekly", {}).get("surge_apt") or []
    if not z or not surge:
        return None

    # 거래량이 평소보다 뚜렷이 많은 지역
    busiest = max(z, key=lambda r: r["deals_z"])
    # 급등 단지 1위
    top = surge[0]

    # 반대 지표 ①: 가격 지표는 위인데 거래량은 아래인 지역.
    # 가격이 올랐다는 신호가 거래로 뒷받침되지 않는 경우다.
    thin_rise = [r for r in z if r["ppy_z"] >= STRONG_Z and r["deals_z"] <= 0]
    thin_rise = max(thin_rise, key=lambda r: r["ppy_z"] - r["deals_z"],
                    default=None)

    # 반대 지표 ②: 거래가 줄면서 오른 단지
    shrinking = [s for s in surge
                 if s.get("deals_prior") and s["deals_recent"] < s["deals_prior"]]
    shrinking = shrinking[0] if shrinking else None

    return {"busiest": busiest, "top": top,
            "thin_rise": thin_rise, "shrinking": shrinking,
            "quiet": min(z, key=lambda r: r["deals_z"])}


# ── 절별 대본 ────────────────────────────────────────────────────────────
def sec_hook(t: dict, p: dict) -> dict:
    b, top = t["busiest"], t["top"]
    narration = (
        f"이번 주 수도권 실거래에서 눈에 띈 건 두 가지입니다. "
        f"{b['sigungu_name']}의 거래량이 평소보다 뚜렷하게 늘었고, "
        f"{top['sigungu_name']} {top['legal_dong_name']}의 {J(top['apt_name'], '은는')} "
        f"최근 {p['surge_window_days']}일 평단가가 그 직전 같은 기간보다 "
        f"{top['change_pct']}% 높게 찍혔습니다. "
        f"다만 두 숫자 모두 그대로 받아들이기 전에 봐야 할 게 있습니다. "
        f"오늘은 그 뒤를 보겠습니다."
    )
    return {"id": "hook", "title": "들어가며",
            "captions": [f"{b['sigungu_name']} 거래량 {b['deals_z']}σ",
                         f"{top['apt_name']} 평단가 {top['change_pct']}%"],
            "narration": narration,
            "facts": {"busiest": b, "top": top}}


def sec_region(t: dict, p: dict) -> dict:
    b, q = t["busiest"], t["quiet"]
    thin = ""
    if b["week_deals"] < THIN_SAMPLE:
        thin = (f" 다만 거래가 {b['week_deals']}건이라 표본이 작습니다. "
                f"이 정도 규모에서는 몇 건 차이로도 수치가 크게 흔들립니다.")
    narration = (
        f"먼저 지역입니다. 저희는 지역끼리 거래량을 비교하지 않습니다. "
        f"강남과 가평은 애초에 규모가 달라서 나란히 놓는 게 의미가 없습니다. "
        f"대신 각 지역의 지난 {p['zscore_hist_weeks']}주 평균과 견줍니다. "
        f"{J(b['sigungu_name'], '은는')} 이번 주 {b['week_deals']}건으로, "
        f"평소 {b['deals_avg_52w']}건보다 많았습니다. "
        f"표준편차 기준으로 {b['deals_z']}입니다.{thin} "
        f"반대로 {J(q['sigungu_name'], '은는')} {q['week_deals']}건으로 "
        f"평소 {q['deals_avg_52w']}건보다 적었습니다. "
        f"한 주 안에서도 지역마다 방향이 갈립니다."
    )
    return {"id": "region", "title": "지역 — 자기 평소와 비교",
            "captions": [f"{b['sigungu_name']} {b['week_deals']}건 (평소 {b['deals_avg_52w']}건)",
                         f"{q['sigungu_name']} {q['week_deals']}건 (평소 {q['deals_avg_52w']}건)"],
            "narration": narration,
            "facts": {"busiest": b, "quiet": q}}


def sec_apt(t: dict, p: dict) -> dict:
    s = t["top"]
    narration = (
        f"다음은 단지입니다. {s['sigungu_name']} {s['legal_dong_name']}의 "
        f"{s['apt_name']} {s['pyeong_bucket']}입니다. "
        f"최근 {p['surge_window_days']}일 평단가가 {num(s['ppy_recent_90d'])}만원, "
        f"그 직전 {p['surge_window_days']}일은 {num(s['ppy_prior_90d'])}만원이었습니다. "
        f"차이가 {s['change_pct']}%입니다. "
        f"표본은 최근 구간 {s['deals_recent']}건, 직전 구간 {s['deals_prior']}건입니다. "
        f"평단가는 거래된 집들의 평균이라, 그 기간에 어떤 평형과 어떤 층이 "
        f"팔렸느냐에 따라 움직입니다. 같은 단지라도 저층과 고층은 가격이 다릅니다."
    )
    return {"id": "apt", "title": "단지 — 무엇이 움직였나",
            "captions": [f"{s['apt_name']} {s['pyeong_bucket']}",
                         f"{num(s['ppy_prior_90d'])}만 → {num(s['ppy_recent_90d'])}만 ({s['change_pct']}%)",
                         f"표본 {s['deals_prior']}건 → {s['deals_recent']}건"],
            "narration": narration,
            "facts": {"top": s}}


def sec_counter(t: dict, p: dict) -> dict:
    """반대 지표. 앞 이야기를 약화시키는 신호를 같은 데이터에서 찾는다."""
    parts = [
        "여기까지만 보면 오른 쪽만 눈에 들어옵니다. "
        "같은 데이터에서 반대로 읽히는 신호도 같이 보겠습니다."
    ]
    facts: dict = {}

    tr = t.get("thin_rise")
    if tr:
        parts.append(
            f"{J(tr['sigungu_name'], '은는')} 평단가 지표가 표준편차 기준 {tr['ppy_z']}로 "
            f"평소보다 높게 나왔습니다. 그런데 같은 주 거래량은 {tr['week_deals']}건, "
            f"평소 {tr['deals_avg_52w']}건보다 적어서 {tr['deals_z']}입니다. "
            f"가격 쪽 숫자는 올라갔는데 거래가 그만큼 따라오지 않은 모양입니다. "
            f"거래가 적을 때는 어떤 집이 팔렸느냐가 평균을 크게 흔듭니다."
        )
        facts["thin_rise"] = tr

    sh = t.get("shrinking")
    if sh:
        parts.append(
            f"{sh['apt_name']}도 비슷합니다. 평단가는 {sh['change_pct']}% 올랐지만 "
            f"거래는 직전 {sh['deals_prior']}건에서 최근 {sh['deals_recent']}건으로 "
            f"줄었습니다. 오른 가격에 실제로 사고판 사람이 더 많아진 건 아닙니다."
        )
        facts["shrinking"] = sh

    parts.append(
        f"하나 더 있습니다. 실거래는 계약 후 {p['report_deadline_days']}일 안에 "
        f"신고합니다. 그래서 최근 주는 집계가 덜 차 있습니다. "
        f"저희가 {p['weekly_lag_days']}일 물린 주를 보는 이유입니다. "
        f"그리고 신고된 뒤에 취소되는 거래도 있습니다. 그런 건은 빼고 계산했습니다."
    )
    return {"id": "counter", "title": "반대로 읽히는 신호",
            "captions": ["가격 지표 ↑ · 거래량 ↓",
                         f"신고 기한 {p['report_deadline_days']}일 · {p['weekly_lag_days']}일 물려 집계"],
            "narration": " ".join(parts), "facts": facts}


def sec_wrap(t: dict, p: dict) -> dict:
    b, s = t["busiest"], t["top"]
    narration = (
        f"정리하겠습니다. 이번 주 {b['sigungu_name']}의 거래량은 평소보다 많았고, "
        f"{s['apt_name']} {s['pyeong_bucket']}의 평단가는 직전 "
        f"{p['surge_window_days']}일 대비 {s['change_pct']}% 높았습니다. "
        f"다만 둘 다 표본이 넉넉한 편은 아니고, 가격이 오른 곳에서 거래가 함께 "
        f"늘지 않은 경우도 있었습니다. "
        f"여기 나온 숫자는 {p['data_start_year']}년부터 쌓은 국토교통부 실거래 "
        f"공개자료를 그대로 집계한 것입니다. 해석은 보시는 분 몫으로 남겨둡니다."
    )
    return {"id": "wrap", "title": "정리",
            "captions": ["표본 크기 확인", "가격과 거래량을 함께 보기"],
            "narration": narration,
            "facts": {"busiest": b, "top": s}}


SECTIONS = [sec_hook, sec_region, sec_apt, sec_counter, sec_wrap]


# ── 조립 ─────────────────────────────────────────────────────────────────
def build(data: dict) -> dict | None:
    t = pick_topics(data)
    if t is None:
        return None
    p = data.get("params") or {}
    secs = [fn(t, p) for fn in SECTIONS]
    body = "\n\n".join(s["narration"] for s in secs)

    # 영상 고정 자막 + 설명란. 둘 다 유튜브 면책을 담는다.
    desc = "\n\n".join([
        f"{data['asof']} 기준 주간 수도권 실거래 지표입니다.",
        SOURCE_NOTE + ".",
        DISCLAIMER_YOUTUBE,
        cta(),
    ])
    return {
        "asof": data["asof"],
        "week_start": t["busiest"].get("week_start"),
        "sections": secs,
        "narration": body,
        "burned_in_caption": DISCLAIMER_YOUTUBE,   # 영상에 고정으로 태운다
        "description": desc,
        "char_count": len(body),
        "est_minutes": round(len(body) / 330, 1),  # 한국어 낭독 약 330자/분
    }


def as_markdown(script: dict) -> str:
    lines = [f"# 주간 롱폼 대본 — {script['asof']}", "",
             f"- 기준 주: {script['week_start']}",
             f"- 분량: {script['char_count']}자 (약 {script['est_minutes']}분)", ""]
    for i, s in enumerate(script["sections"], 1):
        lines += [f"## {i}. {s['title']}", "",
                  "**자막**", ""]
        lines += [f"- {c}" for c in s["captions"]]
        lines += ["", "**내레이션**", "", s["narration"], ""]
    lines += ["---", "", "## 영상 고정 자막", "", script["burned_in_caption"], "",
              "## 설명란", "", script["description"], ""]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="T14 롱폼 대본")
    ap.add_argument("--metrics")
    args = ap.parse_args()

    files = sorted((ROOT / "output").glob("metrics_*.json"))
    src = Path(args.metrics) if args.metrics else (files[-1] if files else None)
    if src is None or not src.exists():
        print("지표 JSON 이 없다. 먼저: python -m metrics.build_metrics")
        return 1
    data = json.loads(src.read_text(encoding="utf-8"))

    script = build(data)
    if script is None:
        print("재료 부족 — 이번 주는 롱폼을 만들지 않는다 (폴백)")
        return 0

    # 검증: 내레이션 전체 + 설명란. 숫자는 각 절의 facts 와 params 로 대조한다.
    facts = {"params": data.get("params"),
             "sections": [s["facts"] for s in script["sections"]]}
    full = script["narration"] + "\n\n" + script["description"]
    r = validate(full, facts, kind="youtube")

    outdir = ROOT / "output" / data["asof"]
    outdir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'=' * 60}\n  주간 롱폼 대본  {data['asof']}\n{'=' * 60}")
    print(f"  기준 주: {script['week_start']}")
    print(f"  분량: {script['char_count']}자 (약 {script['est_minutes']}분)")
    print(f"  검증: {'통과' if r.ok else '차단'} (숫자 {r.numbers_checked}개)")
    for why in r.reasons:
        print(f"    ! {why}")
    for s in script["sections"]:
        print(f"    {s['id']:9s} {len(s['narration']):>4}자  {s['title']}")

    if not r.ok:
        print(f"\n  검증 실패 — 저장하지 않는다\n{'=' * 60}\n")
        return 1

    (outdir / "longform.json").write_text(
        json.dumps(script, ensure_ascii=False, indent=2), encoding="utf-8")
    (outdir / "longform.md").write_text(as_markdown(script), encoding="utf-8")
    print(f"\n  저장: {outdir / 'longform.json'}")
    print(f"        {outdir / 'longform.md'}")
    print(f"{'=' * 60}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
