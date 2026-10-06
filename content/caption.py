"""T16 — 인스타그램 캡션 생성기.

캐러셀 7장과 **같은 소재**로 캡션을 만든다. `carousel.pick()` 을 그대로 쓰는
이유가 그것이다 — 지표 JSON 을 따로 읽으면 캡션이 가리키는 단지와 이미지에
그려진 단지가 어긋날 수 있고, 그 어긋남은 사람 눈에 잘 안 띈다.

스레드와 포맷이 다르다 (`docs/02_CLI_디자인지시사항.md` 8항).

                  스레드                 인스타 캡션
    길이          500자                  2,200자
    면책          1줄 축약 + 프로필      전문 그대로
    해시태그      쓰지 않는다            마지막 블록에 몰아서
    첫 줄         훅 (타임라인에서 접힘) 훅 + "더 보기" 전 2줄이 미리보기

그래서 캡션은 **앞 2줄**에 훅과 넘김 유도를 넣고, 나머지는 더 보기 뒤로
간다는 전제로 쓴다.

실행:
  .venv\Scripts\python.exe -m content.caption
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from content import design as D  # noqa: E402
from content.carousel import pick  # noqa: E402
from content.thread import cta  # noqa: E402
from content.validator import validate  # noqa: E402
from templates.disclaimers import DISCLAIMER_SOCIAL  # noqa: E402

NL = chr(10)

MAX_LEN = 2200      # 인스타 캡션 한도
MAX_TAGS = 30       # 해시태그 한도
PREVIEW_LINES = 2   # "더 보기" 전에 보이는 줄

# 고정 해시태그. 지역·단지 태그는 그날 소재에서 붙인다.
# 금지어가 섞이지 않게 검증기를 똑같이 통과시킨다 (#저평가아파트 같은 게
# 태그로 들어가는 사고를 막는다).
BASE_TAGS = [
    "수도권실거래", "아파트실거래가", "실거래가", "부동산데이터",
    "국토교통부실거래가", "아파트시세", "주간부동산", "데이터로보는부동산",
]


def tags(t: dict) -> str:
    """표지 지역이 맨 앞에 온다.

    태그는 그 게시물이 어디 얘기인지 알리는 자리다. 표지가 마포구인데 태그에
    마포구가 없으면 검색으로 들어올 사람이 못 찾는다.
    """
    c = t["cover"]
    # 덱에 나오는 지역만 태그한다. 표지가 마포구인데 #포천시 가 붙어 있으면
    # 그 태그로 들어온 사람이 "왜 여기 있지"가 된다.
    names = [c.region, c.data.get("legal_dong_name") or ""]
    out, seen = [], set()
    for n in names + BASE_TAGS:
        n = n.replace(" ", "")
        if n and n not in seen:
            seen.add(n)
            out.append("#" + n)
    return " ".join(out[:MAX_TAGS])


def cover_line(c) -> str:
    """캐러셀 표지와 같은 사실을 한 줄로."""
    d = c.data
    if c.angle == "new_high":
        return (f'{c.region} {d["apt_name"]}, 종전 최고가를 '
                f'{d["over_peak_pct"]}% 넘겼어요.')
    if c.angle == "counter":
        return (f'{c.region} {d["apt_name"]} 평단가가 '
                f'{d["change_pct"]}% 올랐어요.')
    return (f'{c.region}, 이번 주 거래가 평소의 '
            f'{D.times(d["week_deals"], d["deals_avg_52w"])}였어요.')


def detail_lines(t: dict) -> list[str]:
    """캡션 본문은 **캐러셀 장 순서를 그대로** 따라간다.

    넘겨 본 사람이 캡션을 읽을 때 순서가 어긋나면 "어느 장 얘기지"가 된다.
    없는 장을 가리키는 건 더 나쁘다 — 전에 "수도권 전체로 보면…" 이라고
    썼는데 그 주 덱에는 온도지도가 없었다.
    """
    c = t["cover"]
    d = c.data
    prof = d.get("profile")
    out: list[str] = []

    if prof:
        # 2장 — 이번 거래
        out.append(f'· 이번 거래 {D.won(d["deal_amount"])} '
                   f'(종전 최고 {D.won(d["prev_peak"])})')
        # 3장 — 주변 단지
        nb = prof.get("neighbors") or []
        if nb:
            hi = max(nb, key=lambda r: r["last_price"])
            name = D.split_name(hi["apt_name"], 10)[0]
            # "9.8억예요" → "9.8억이에요". 억·만 뒤에는 늘 받침이 있다.
            out.append(f'· 같은 동 {D.pyeong(prof["pyeong_bucket"])}에서 가장 비싼 '
                       f'거래는 {name} {D.won(hi["last_price"])}이에요')
        # 4장 — 거래 건수
        pts = prof.get("series") or []
        recent = sum(p["deals"] for p in pts[-12:]) if pts else 0
        prior = sum(p["deals"] for p in pts[-24:-12]) if len(pts) > 12 else 0
        if prior:
            out.append(f'· 이 평형 거래는 직전 1년 {prior}건 → 최근 1년 {recent}건')
    elif c.angle == "counter":
        out.append(f'· 평단가 {D.delta(d["change_pct"], arrow=False)}, '
                   f'거래는 {d["deals_prior"]}건 → {d["deals_recent"]}건')
    else:
        out.append(f'· 이번 주 {d["week_deals"]}건 '
                   f'(평소 {D.num(d["deals_avg_52w"])}건)')

    # 5장 — 그 구는
    r = t.get("cover_region")
    if r and r.get("deals_avg_52w"):
        ratio = r["week_deals"] / r["deals_avg_52w"]
        word = ("붐볐어요" if ratio >= 1.1 else
                "조용했어요" if ratio <= 0.9 else "평소와 비슷했어요")
        out.append(f'· {c.region} 전체는 이번 주 {r["week_deals"]}건 '
                   f'(평소 {D.num(r["deals_avg_52w"])}건) — {word}')
    return out


def hook2(t: dict) -> str:
    """미리보기 둘째 줄. 넘길 이유를 만든다 — 1장과 3장 사이의 긴장."""
    c = t["cover"]
    r = t.get("cover_region")
    if r and r.get("deals_avg_52w"):
        ratio = r["week_deals"] / r["deals_avg_52w"]
        if ratio <= 0.9:
            return f'그런데 {c.region} 전체 거래는 평소보다 조용했어요. →'
        if ratio >= 1.1:
            return f'{c.region} 전체도 평소보다 붐볐고요. →'
    return '같은 주, 동네마다 방향이 달랐어요. →'


def caption(t: dict) -> str:
    # 첫 줄은 **캐러셀 표지와 같은 얘기**여야 한다. 캡션이 다른 지역을
    # 말하면 넘겨 본 사람이 "무슨 소리지"가 된다.
    body = [
        cover_line(t["cover"]),
        hook2(t),
        "",
        *detail_lines(t),
        "",
        f"'평소'는 지난 {t['params']['zscore_hist_weeks']}주 평균이에요. "
        f"지역끼리 비교한 게 아니라 그 지역의 평소와 비교한 값이고요.",
        f"계약하고 {t['params']['report_deadline_days']}일 안에 신고라서 "
        f"최근 주는 집계가 덜 차요. 그래서 "
        f"{t['params']['weekly_lag_days']}일 물린 주를 봐요.",
        "",
        "저장해두고 다음 주 숫자와 비교해보세요.",
        "여러분 동네는 이번 주 어땠나요? 댓글로 알려주세요.",
        "",
        *([cta(), ""] if os.environ.get("NEWSLETTER_URL", "").strip() else []),
        f"매주 이렇게 한 장으로 정리해요. {D.HANDLE} 팔로우하면 "
        f"다음 주에 또 만나요.",
        "",
        DISCLAIMER_SOCIAL,
        "",
        tags(t),
    ]
    return NL.join(body)


def build(data: dict) -> dict | None:
    t = pick(data)
    if t is None:
        return None
    text = caption(t)
    # 캡션이 쓰는 파생값(1년 거래 합)도 발행되는 숫자다. 출처를 대지 않으면
    # 검증기가 막는다 — 막는 게 맞고, 실제로 여기서 한 번 걸렸다.
    prof = (t["cover"].data or {}).get("profile") or {}
    pts = prof.get("series") or []
    facts = {"busiest": t["busiest"], "top": t["top"],
             "cover": t["cover"].data, "cover_region": t.get("cover_region"),
             "deals_recent_1y": sum(p["deals"] for p in pts[-12:]),
             "deals_prior_1y": sum(p["deals"] for p in pts[-24:-12]),
             "drop_pct": round((t["top"]["deals_recent"]
                                / t["top"]["deals_prior"] - 1) * 100, 1),
             "params": t["params"]}
    r = validate(text, facts, kind="social")
    if len(text) > MAX_LEN:
        r.fail(f"캡션 한도 초과 {len(text)}자 (최대 {MAX_LEN})")
    if text.count("#") > MAX_TAGS:
        r.fail(f"해시태그 {text.count('#')}개 (최대 {MAX_TAGS})")
    D.assert_no_jargon(text, "caption")
    return {"text": text, "facts": facts, "ok": r.ok, "reasons": r.reasons,
            "length": len(text), "numbers_checked": r.numbers_checked,
            "preview": "\n".join(text.split("\n")[:PREVIEW_LINES])}


def main() -> int:
    ap = argparse.ArgumentParser(description="T16 인스타 캡션")
    ap.add_argument("--metrics")
    args = ap.parse_args()

    files = sorted((ROOT / "output").glob("metrics_*.json"))
    src = Path(args.metrics) if args.metrics else (files[-1] if files else None)
    if src is None or not src.exists():
        print("지표 JSON 이 없다. 먼저: python -m metrics.build_metrics")
        return 1
    data = json.loads(src.read_text(encoding="utf-8"))
    outdir = ROOT / "output" / data["asof"]
    outdir.mkdir(parents=True, exist_ok=True)

    res = build(data)
    print(f"{'=' * 62}")
    print(f"  인스타 캡션  {data['asof']}")
    print(f"{'=' * 62}")
    if res is None:
        print("  재료 부족 — 이번 주는 만들지 않는다 (폴백)")
        return 0
    if not res["ok"]:
        print(f"  검증 실패 {len(res['reasons'])}건 — 저장하지 않는다")
        for w in res["reasons"]:
            print(f"    ! {w}")
        return 1

    (outdir / "instagram.txt").write_text(res["text"], encoding="utf-8")
    (outdir / "instagram.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  {res['length']}자 / 숫자 {res['numbers_checked']}개 검증")
    print(f"  미리보기(더 보기 전):")
    for ln in res["preview"].split("\n"):
        print(f"    | {ln}")
    print()
    print("\n".join("    " + ln for ln in res["text"].split("\n")))
    print()
    print(f"  저장: {outdir / 'instagram.txt'}")
    print("=" * 62)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
