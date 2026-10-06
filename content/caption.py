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
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from content import design as D  # noqa: E402
from content.carousel import pick  # noqa: E402
from content.thread import cta  # noqa: E402
from content.validator import validate  # noqa: E402
from templates.disclaimers import DISCLAIMER_SOCIAL  # noqa: E402

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
    b, s = t["busiest"], t["top"]
    names = [b["sigungu_name"], s["sigungu_name"], s["legal_dong_name"]]
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


def caption(t: dict) -> str:
    b, s = t["busiest"], t["top"]
    mult = D.times(b["week_deals"], b["deals_avg_52w"])
    drop = (s["deals_recent"] / s["deals_prior"] - 1) * 100
    # 첫 줄은 **캐러셀 표지와 같은 얘기**여야 한다. 캡션이 다른 지역을
    # 말하면 넘겨 본 사람이 "무슨 소리지"가 된다. 표지는 5-1항 규칙으로
    # 고르므로 거래량 1위와 다를 수 있다.
    hook = cover_line(t["cover"])
    body = [
        # 앞 2줄 = 미리보기. 여기서 넘길지 말지가 결정된다.
        hook,
        "그런데 값이 오른 단지는 오히려 손바뀜이 줄었어요. →",
        "",
        f"· {b['sigungu_name']} 이번 주 {b['week_deals']}건 "
        f"(평소 {D.num(b['deals_avg_52w'])}건)",
        f"· {s['apt_name']} {s['pyeong_bucket']} 평단가 {D.delta(s['change_pct'], arrow=False)}",
        f"· 같은 기간 거래 건수는 {D.delta(drop, arrow=False)}",
        f"· 다만 최근 {s['deals_recent']}건으로 계산한 값이라 흔들릴 수 있어요",
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
        cta(),
        "",
        DISCLAIMER_SOCIAL,
        "",
        tags(t),
    ]
    return "\n".join(body)


def build(data: dict) -> dict | None:
    t = pick(data)
    if t is None:
        return None
    text = caption(t)
    facts = {"busiest": t["busiest"], "top": t["top"],
             "cover": t["cover"].data,
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
