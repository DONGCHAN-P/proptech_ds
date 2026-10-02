"""T12 — 스레드 텍스트 생성기.

포맷은 고정이다.

    [무슨 일] → [데이터] → [조건 설명] → [면책]

LLM 은 **JSON 숫자를 문장으로 옮기는 일만** 한다. 재계산도, 창작도 안 된다.
그래서 기본 경로는 템플릿이고, LLM 은 선택지다. 키가 없어도 돌아가야 한다 —
API 가 막혀서 그날 발행을 못 하는 상황을 만들지 않는다.

LLM 을 쓰든 안 쓰든 결과물은 똑같이 `content.validator.validate()` 를
통과해야 한다. 통과 못 하면 발행하지 않는다.

실행:
  .venv\\Scripts\\python.exe -m content.thread
  .venv\\Scripts\\python.exe -m content.thread --kind outlier
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from content.validator import validate  # noqa: E402
from templates.disclaimers import (  # noqa: E402
    CTA_NEWSLETTER, CTA_PLACEHOLDER_URL, DISCLAIMER_SOCIAL, SOURCE_NOTE,
)

# 표본이 이보다 적으면 문장에 그 사실을 적는다. 연천군 7건으로 "+2.0σ" 를
# 그냥 쓰면 "거래 폭증"으로 읽힌다.
THIN_SAMPLE = 20


def won(man) -> str:
    if man is None:
        return "-"
    man = float(man)
    if abs(man) >= 10000:
        v = man / 10000
        return f"{v:.0f}억" if abs(v) >= 100 else f"{v:.1f}억"
    return f"{man:,.0f}만"


def cta() -> str:
    url = os.environ.get("NEWSLETTER_URL", "").strip() or CTA_PLACEHOLDER_URL
    return CTA_NEWSLETTER.format(url=url)


# ── 템플릿 ───────────────────────────────────────────────────────────────
def draft_new_high(f: dict, p: dict) -> str:
    """신고가 경신. '신고가'는 사실 진술이라 금지어가 아니다."""
    thin = ""
    if f.get("history_count", 0) < THIN_SAMPLE:
        thin = f" 다만 이 평형의 누적 거래는 {f['history_count']}건으로 많지 않습니다."
    return "\n".join([
        f"[{f['sigungu_name']} {f['legal_dong_name']}] "
        f"{f['apt_name']} {f['pyeong_bucket']}가 종전 최고가를 넘겼습니다.",
        "",
        f"· 이번 거래 {won(f['deal_amount'])} ({f['floor_band']}, "
        f"{f['area_m2']}㎡)",
        f"· 종전 최고 {won(f['prev_peak'])}",
        f"· 차이 {f['over_peak_pct']}%",
        "",
        f"{p['data_start_year']}년 이후 같은 단지·같은 평형 기록과 "
        f"비교한 수치입니다.{thin} "
        f"{SOURCE_NOTE}.",
        "",
        DISCLAIMER_SOCIAL,
        "",
        cta(),
    ])


def draft_outlier(f: dict, p: dict) -> str:
    """직전 평균 대비 벌어진 거래. 방향을 단정하지 않고 사실만 쓴다."""
    gap = f["deviation_pct"]
    way = "높게" if gap > 0 else "낮게"
    return "\n".join([
        f"[{f['sigungu_name']} {f['legal_dong_name']}] "
        f"{f['apt_name']} {f['pyeong_bucket']}에서 "
        f"직전 평균과 벌어진 거래가 신고됐습니다.",
        "",
        f"· 이번 거래 {won(f['deal_amount'])} ({f['floor_band']}, "
        f"{f['area_m2']}㎡)",
        f"· 직전 {p['outlier_ref_window_days']}일 평균 {won(f['ref_avg'])} "
        f"(거래 {f['ref_count']}건)",
        f"· 차이 {abs(gap)}% {way}",
        "",
        "층과 향, 수리 상태에 따라 같은 평형도 가격이 갈립니다. "
        f"한 건의 거래로 시세를 판단하기는 어렵습니다. {SOURCE_NOTE}.",
        "",
        DISCLAIMER_SOCIAL,
        "",
        cta(),
    ])


def draft_zscore(f: dict, p: dict) -> str:
    """시군구 거래량이 자기 평소와 얼마나 다른가."""
    z = f["deals_z"]
    way = "많습니다" if z > 0 else "적습니다"
    thin = ""
    if f["week_deals"] < THIN_SAMPLE:
        thin = (f" 다만 주간 거래가 {f['week_deals']}건으로 적어 "
                f"수치가 크게 흔들릴 수 있습니다.")
    return "\n".join([
        f"[{f['sigungu_name']}] {f['week_start']} 주 거래량이 "
        f"평소보다 {way}.",
        "",
        f"· 이번 주 {f['week_deals']}건",
        f"· 지난 {p['zscore_hist_weeks']}주 평균 {f['deals_avg_52w']}건",
        f"· 표준편차 기준 {z}",
        "",
        "다른 지역과 비교한 값이 아니라 그 지역의 평소와 비교한 값입니다. "
        "계약 후 30일 내 신고라 최근 주는 집계가 덜 찹니다. "
        f"그래서 4주 물린 주를 봅니다.{thin} {SOURCE_NOTE}.",
        "",
        DISCLAIMER_SOCIAL,
        "",
        cta(),
    ])


DRAFTERS = {
    "new_high": (draft_new_high, ("daily", "new_high")),
    "outlier": (draft_outlier, ("daily", "outlier")),
    "zscore": (draft_zscore, ("weekly", "sgg_zscore")),
}


# ── LLM (선택) ───────────────────────────────────────────────────────────
LLM_SYSTEM = """\
너는 부동산 실거래 데이터를 문장으로 옮기는 편집자다.

규칙:
- 주어진 JSON 의 숫자만 쓴다. 더하거나 빼거나 비율을 다시 계산하지 않는다.
- JSON 에 없는 숫자는 한 개도 쓰지 않는다.
- 매수·매도를 권하지 않는다. 가격이 오를지 내릴지 말하지 않는다.
- "저평가" "유망" "지금이 기회" 같은 가치 판단 표현을 쓰지 않는다.
- 층은 저층/중층/고층 구간으로만 쓴다. 정확한 층수를 쓰지 않는다.
- 문장만 다듬는다. 구조와 순서는 주어진 초안을 따른다.
"""


def polish_with_llm(draft: str, facts: dict) -> str:
    """초안을 LLM 으로 다듬는다. 키가 없으면 초안을 그대로 돌려준다.

    다듬은 결과도 호출부에서 다시 검증한다. LLM 이 숫자를 건드리면 거기서
    걸린다.
    """
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not key:
        return draft
    try:
        import anthropic
    except ImportError:
        return draft
    try:
        client = anthropic.Anthropic(api_key=key)
        msg = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=1200,
            system=LLM_SYSTEM,
            messages=[{"role": "user", "content":
                       f"데이터:\n{json.dumps(facts, ensure_ascii=False)}\n\n"
                       f"초안:\n{draft}\n\n"
                       f"문장만 자연스럽게 다듬어 돌려줘."}],
        )
        return msg.content[0].text.strip()
    except Exception as e:
        print(f"  LLM 다듬기 실패 ({e}) — 초안 사용")
        return draft


# ── 메인 ─────────────────────────────────────────────────────────────────
def latest_metrics() -> Path | None:
    files = sorted((ROOT / "output").glob("metrics_*.json"))
    return files[-1] if files else None


def generate(kind: str, data: dict, n: int = 1, use_llm: bool = False) -> list[dict]:
    drafter, (bucket, key) = DRAFTERS[kind]
    rows = (data.get(bucket) or {}).get(key) or []
    params = data.get("params") or {}
    out = []
    for f in rows[:n]:
        text = drafter(f, params)
        if use_llm:
            text = polish_with_llm(text, f)
        # 방법론 상수(90일 창, 52주 기준 등)도 발행되는 숫자라 출처가 있어야
        # 한다. params 를 함께 넘겨 검증 대상에 포함시킨다.
        r = validate(text, {"facts": f, "params": params})
        out.append({"kind": kind, "facts": f, "text": text,
                    "ok": r.ok, "reasons": r.reasons,
                    "numbers_checked": r.numbers_checked})
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="T12 스레드 초안 생성")
    ap.add_argument("--kind", choices=list(DRAFTERS) + ["all"], default="all")
    ap.add_argument("--n", type=int, default=1, help="종류별 생성 개수")
    ap.add_argument("--llm", action="store_true", help="LLM 으로 문장 다듬기")
    ap.add_argument("--metrics")
    args = ap.parse_args()

    src = Path(args.metrics) if args.metrics else latest_metrics()
    if src is None or not src.exists():
        print("지표 JSON 이 없다. 먼저: python -m metrics.build_metrics")
        return 1
    data = json.loads(src.read_text(encoding="utf-8"))

    kinds = list(DRAFTERS) if args.kind == "all" else [args.kind]
    outdir = ROOT / "output" / data["asof"]
    outdir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'=' * 60}\n  스레드 초안  기준일 {data['asof']}\n{'=' * 60}")
    if args.llm and not os.environ.get("ANTHROPIC_API_KEY"):
        print("  (ANTHROPIC_API_KEY 없음 — 템플릿 초안만 생성)")

    results = []
    for k in kinds:
        results += generate(k, data, args.n, args.llm)

    blocked = 0
    for i, r in enumerate(results, 1):
        mark = "통과" if r["ok"] else "차단"
        print(f"\n--- [{mark}] {r['kind']} (숫자 {r['numbers_checked']}개 검증)")
        if not r["ok"]:
            blocked += 1
            for why in r["reasons"]:
                print(f"    ! {why}")
        print("\n" + "\n".join("    " + ln for ln in r["text"].split("\n")))

    ok_items = [r for r in results if r["ok"]]
    out = outdir / "threads.json"
    out.write_text(json.dumps(ok_items, ensure_ascii=False, indent=2),
                   encoding="utf-8")

    print(f"\n{'=' * 60}")
    print(f"  생성 {len(results)} / 통과 {len(ok_items)} / 차단 {blocked}")
    print(f"  저장: {out}")
    print(f"{'=' * 60}\n")
    return 1 if blocked else 0


if __name__ == "__main__":
    sys.exit(main())
