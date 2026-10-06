"""T12 — 스레드(Threads) 본문 생성기.

포맷은 스레드의 읽기 방식에 맞춘다 (`docs/02_CLI_디자인지시사항.md` 8항).

    [1줄 훅] → [근거 3~4줄] → [질문 1줄] → [면책 1줄 + CTA]

지키는 것
  · 첫 줄이 훅이다. 타임라인에서 접히기 전에 보이는 건 거기까지다.
  · 본문은 3~5줄, 구어체("~했어요"). 보고서 문체를 쓰지 않는다.
  · 마지막 본문 줄은 질문형 — 댓글이 붙어야 노출이 는다.
  · σ·표준편차는 쓰지 않는다. "평소의 1.7배"로 번역한다.
  · 면책은 본문 1줄(DISCLAIMER_THREADS)로 줄이고 전문은 프로필 고정 게시물에.

인스타 캡션은 길이도 구조도 달라서 `content/caption.py` 가 따로 만든다.

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
from content.design import pyeong  # noqa: E402
from content.validator import validate  # noqa: E402
from templates.disclaimers import (  # noqa: E402
    ALL_DISCLAIMERS, CTA_NEWSLETTER, CTA_PLACEHOLDER_URL,
    DISCLAIMER_THREADS,
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


def num(v) -> str:
    f = float(v)
    return f"{f:,.0f}" if f == int(f) else f"{f:,.1f}"


def cta() -> str:
    """가입 동선. 링크가 없으면 **자리표시자 대신 팔로우 유도**를 쓴다.

    "(뉴스레터 링크 준비 중)" 을 그대로 올리면 미완성으로 보이고, 그게
    계정 첫인상이 된다. 링크가 생기면 .env 의 NEWSLETTER_URL 만 채우면 된다.
    """
    url = os.environ.get("NEWSLETTER_URL", "").strip()
    if url:
        return CTA_NEWSLETTER.format(url=url)
    from content.design import HANDLE
    return f"매주 이렇게 정리해요. {HANDLE} 팔로우하면 다음 주에 또 만나요."


# ── 포맷 ─────────────────────────────────────────────────────────────────
MAX_LEN = 500        # 스레드 본문 한도. 넘으면 뒤가 잘린다
BODY_LINES = (3, 5)  # 훅 다음 근거 줄 수


def hook_ok(line: str) -> bool:
    """훅은 한 줄로 끝나야 한다. 타임라인에서 접히면 훅이 아니다."""
    return 0 < len(line) <= 60


def assemble(hook: str, body: list[str], question: str) -> str:
    """훅 → 근거 → 질문 → 고정 꼬리(면책 1줄 + CTA).

    고정 꼬리를 여기서만 붙인다. 드래프터마다 따로 붙이면 한 군데서 빠진다.
    """
    body = [b for b in body if b]
    return "\n".join([hook, "", *body, "", question, "",
                         DISCLAIMER_THREADS, "", cta()])


# ── 템플릿 ───────────────────────────────────────────────────────────────
def draft_new_high(f: dict, p: dict) -> str:
    """신고가 경신. '신고가'는 사실 진술이라 금지어가 아니다."""
    body = [
        f"· 이번 거래 {won(f['deal_amount'])} · {f['floor_band']}",
        f"· 종전 최고는 {won(f['prev_peak'])}, {f['over_peak_pct']}% 차이예요",
        f"· {p['data_start_year']}년 이후 같은 단지·같은 평형 기록과 견준 값이에요",
    ]
    if f.get("history_count", 0) < THIN_SAMPLE:
        # 누적 6건짜리 "148% 신고가"를 그냥 쓰면 거짓말이 된다. 표본을 숨기지
        # 않고 근거 줄에 같이 올린다.
        body.append(f"· 다만 이 평형 누적 거래가 {f['history_count']}건뿐이라 "
                    f"들쭉날쭉해요")
    return assemble(
        f"{f['sigungu_name']} {f['apt_name']} {pyeong(f['pyeong_bucket'])}, "
        f"종전 최고가를 넘겼어요.",
        body,
        "이 동네 보고 계신 분 있나요? 체감은 어떠세요?")


def draft_outlier(f: dict, p: dict) -> str:
    """직전 평균 대비 벌어진 거래. 방향을 단정하지 않고 사실만 쓴다."""
    gap = f["deviation_pct"]
    way = "높게" if gap > 0 else "낮게"
    return assemble(
        f"{f['sigungu_name']} {f['legal_dong_name']} {f['apt_name']}, "
        f"평소와 꽤 벌어진 거래가 신고됐어요.",
        [f"· 이번 거래 {won(f['deal_amount'])} · {f['floor_band']} · "
         f"{pyeong(f['pyeong_bucket'])}",
         f"· 직전 {p['outlier_ref_window_days']}일 평균은 "
         f"{won(f['ref_avg'])} (거래 {f['ref_count']}건)",
         f"· {abs(gap)}% {way} 찍힌 셈이에요",
         "· 같은 평형이어도 층·향·수리 상태로 갈려서, 한 건으로 시세를 "
         "말하긴 어려워요"],
        "이런 거래, 동네에서는 어떻게들 보시나요?")


def draft_zscore(f: dict, p: dict) -> str:
    """시군구 거래량이 자기 평소와 얼마나 다른가.

    σ 는 쓰지 않는다. 일반 독자가 해석하지 못하고, 해석하려 들면 틀린다.
    같은 사실을 "평소의 1.7배"로 옮기면 설명이 필요 없다.
    """
    r = f["ratio"]
    body = [
        f"· 이번 주 {f['week_deals']}건, 평소는 {num(f['deals_avg_52w'])}건이에요",
        f"· 지난 {p['zscore_hist_weeks']}주 평균과 견준 값이에요. "
        f"지역끼리 비교한 게 아니고요",
        f"· 계약하고 {p['report_deadline_days']}일 안에 신고라서 최근 주는 "
        f"덜 차요. 그래서 {p['weekly_lag_days']}일 물린 주를 봐요",
    ]
    if f["week_deals"] < THIN_SAMPLE:
        body.append(f"· 주간 거래가 {f['week_deals']}건이라 배수가 크게 "
                    f"흔들릴 수 있어요")
    return assemble(
        f"{f['sigungu_name']}, 이번 주 거래가 평소의 {r}배였어요."
        if r >= 1 else
        f"{f['sigungu_name']}, 이번 주 거래가 평소의 {r}배로 줄었어요.",
        body,
        "여러분 동네는 이번 주 어땠나요?")


# ── 소재 고르기 ──────────────────────────────────────────────────────────
#
# 지표 JSON 은 정렬이 보장되지 않는다. 첫 행을 그냥 쓰면 훅이 "평소의 0.5배"
# 같은 밋밋한 값이 되기도 한다. 종류별로 "글이 될 행"을 앞으로 당긴다.
def prep_zscore(rows: list[dict]) -> list[dict]:
    out = []
    for r in rows:
        base = r.get("deals_avg_52w")
        if not base:
            continue
        # 파생값도 발행되는 숫자다. 행에 남겨야 검증기가 대조할 수 있다.
        r["ratio"] = round(r["week_deals"] / base, 1)
        out.append(r)
    solid = [r for r in out if r["week_deals"] >= THIN_SAMPLE] or out
    return sorted(solid, key=lambda r: abs(r["ratio"] - 1), reverse=True)


def prep_new_high(rows: list[dict]) -> list[dict]:
    """누적 거래가 두터운 단지를 앞으로. 6건짜리 신고가는 글감이 아니다.

    그 주 캐러셀 표지로 고른 단지가 있으면 **그걸 맨 앞에** 둔다. 같은 주에
    인스타는 마포구 얘기를 하는데 스레드는 다른 단지를 말하면, 두 계정이
    따로 노는 것처럼 보인다.
    """
    rows = sorted(rows, key=lambda r: r.get("history_count", 0), reverse=True)
    try:
        from content import cover as CV
        picked = _cover_pick()
        if picked and picked.angle == "new_high":
            name = picked.data.get("apt_name")
            rows.sort(key=lambda r: r.get("apt_name") != name)
    except Exception:
        pass
    return rows


_COVER: object | None = None


def _cover_pick():
    """표지 선정 결과. 같은 지표 JSON 이면 몇 번을 불러도 같은 답이다."""
    global _COVER
    if _COVER is None:
        from content import cover as CV
        src = latest_metrics()
        if not src:
            return None
        _COVER = CV.choose(json.loads(src.read_text(encoding="utf-8")))[0]
    return _COVER


DRAFTERS = {
    "new_high": (draft_new_high, ("daily", "new_high")),
    "outlier": (draft_outlier, ("daily", "outlier")),
    "zscore": (draft_zscore, ("weekly", "sgg_zscore")),
}

PREPS = {"zscore": prep_zscore, "new_high": prep_new_high}


# ── LLM (선택) ───────────────────────────────────────────────────────────
#
# 문장 다듬기용 모델. 실측으로 골랐다 — 숫자 보존·지시 준수·지연을 같은 과제로
# 비교했을 때 mini 급이 가장 안정적이었고, 상위 모델은 3~5배 느린데 결과가 더
# 낫지 않았다. 월 사용량이 입력 90K·출력 42K 토큰 수준이라 비용 차이는 어차피
# 의미가 없다. 바꾸려면 OPENAI_MODEL 환경변수로 덮어쓴다.
LLM_MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.4-mini")
LLM_SYSTEM = """\
너는 부동산 실거래 데이터를 문장으로 옮기는 편집자다.

규칙:
- 주어진 JSON 의 숫자만 쓴다. 더하거나 빼거나 비율을 다시 계산하지 않는다.
- JSON 에 없는 숫자는 한 개도 쓰지 않는다.
- 매수·매도를 권하지 않는다. 가격이 오를지 내릴지 말하지 않는다.
- "저평가" "유망" "지금이 기회" 같은 가치 판단 표현을 쓰지 않는다.
- 층은 저층/중층/고층 구간으로만 쓴다. 정확한 층수를 쓰지 않는다.
- 문장만 다듬는다. 구조와 순서는 주어진 초안을 따른다.
- 구어체("~했어요", "~예요")를 유지한다. 보고서 문체로 바꾸지 않는다.
- 첫 줄은 훅이다. 한 줄로 두고 길이를 늘리지 않는다.
- 마지막 줄의 질문형을 평서문으로 바꾸지 않는다.
"""


def split_fixed(draft: str) -> tuple[str, str]:
    """다듬을 본문과 그대로 둘 고정 꼬리(면책 + CTA)로 가른다.

    면책은 '변경 금지' 문구인데 통째로 LLM 에 넘기면 재배열한다. 실제로
    후보 모델 셋 다 "매수·매도를 추천하거나" 의 구두점과 줄바꿈을 바꿨다.
    아예 보내지 않으면 건드릴 수가 없다 — 모델을 고르는 것보다 확실하다.
    """
    hits = [i for i in (draft.find(d) for d in ALL_DISCLAIMERS.values())
            if i >= 0]
    if not hits:
        return draft, ""
    i = min(hits)
    return draft[:i].rstrip(), draft[i:]


def polish_with_llm(draft: str, facts: dict) -> str:
    """초안의 **본문만** LLM 으로 다듬는다. 키가 없으면 초안을 그대로 돌려준다.

    면책과 CTA 는 손대지 않고 그대로 다시 붙인다. 다듬은 결과도 호출부에서
    검증하므로, LLM 이 숫자를 건드리면 거기서 걸린다.
    """
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        return draft
    try:
        from openai import OpenAI
    except ImportError:
        return draft

    body, fixed = split_fixed(draft)
    if not body:
        return draft
    try:
        client = OpenAI(api_key=key)
        kw = dict(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": LLM_SYSTEM},
                {"role": "user", "content":
                 f"데이터:\n{json.dumps(facts, ensure_ascii=False)}\n\n"
                 f"초안:\n{body}\n\n문장만 자연스럽게 다듬어 돌려줘."},
            ],
        )
        try:
            r = client.chat.completions.create(**kw, max_completion_tokens=2000)
        except TypeError:
            r = client.chat.completions.create(**kw, max_tokens=2000)
        out = (r.choices[0].message.content or "").strip()
        if not out:
            print("  LLM 이 빈 응답 — 초안 사용")
            return draft
        return f"{out}\n\n{fixed}" if fixed else out
    except Exception as e:
        # 다듬기는 선택 기능이다. 무슨 이유로 실패하든 초안으로 발행을 이어간다 —
        # API 가 막혔다고 그날 발행을 못 하는 상황을 만들지 않는다.
        print(f"  LLM 다듬기 실패 ({type(e).__name__}: {e}) — 초안 사용")
        return draft


# ── 메인 ─────────────────────────────────────────────────────────────────
def latest_metrics() -> Path | None:
    files = sorted((ROOT / "output").glob("metrics_*.json"))
    return files[-1] if files else None


def generate(kind: str, data: dict, n: int = 1, use_llm: bool = False) -> list[dict]:
    drafter, (bucket, key) = DRAFTERS[kind]
    rows = (data.get(bucket) or {}).get(key) or []
    if kind in PREPS:
        rows = PREPS[kind](rows)
    params = data.get("params") or {}
    out = []
    for f in rows[:n]:
        text = drafter(f, params)
        if use_llm:
            text = polish_with_llm(text, f)
        # 방법론 상수(90일 창, 52주 기준 등)도 발행되는 숫자라 출처가 있어야
        # 한다. params 를 함께 넘겨 검증 대상에 포함시킨다.
        # 평형 라벨("25P" → "20평대 후반")은 화면에 **20** 이라는 숫자를
        # 새로 만든다. 원본에 없는 숫자라 검증기가 바로 잡는데, 옳은 동작이다.
        # 라벨도 발행되는 값이므로 facts 에 남겨 출처를 댄다.
        fx = dict(f)
        if f.get("pyeong_bucket"):
            fx["pyeong_label"] = pyeong(f["pyeong_bucket"])
        r = validate(text, {"facts": fx, "params": params}, kind="threads")
        # 길이는 검증기가 아니라 플랫폼이 거는 제약이라 여기서 본다.
        if len(text) > MAX_LEN:
            r.fail(f"스레드 한도 초과 {len(text)}자 (최대 {MAX_LEN})")
        lines = [ln for ln in text.split("\n") if ln.strip()]
        if lines and not hook_ok(lines[0]):
            r.fail(f"훅이 {len(lines[0])}자 — 한 줄(60자)로 줄일 것")
        out.append({"kind": kind, "facts": f, "text": text,
                    "ok": r.ok, "reasons": r.reasons, "length": len(text),
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
    if args.llm and not os.environ.get("OPENAI_API_KEY"):
        print("  (OPENAI_API_KEY 없음 — 템플릿 초안만 생성)")

    results = []
    for k in kinds:
        results += generate(k, data, args.n, args.llm)

    blocked = 0
    for i, r in enumerate(results, 1):
        mark = "통과" if r["ok"] else "차단"
        print(f"\n--- [{mark}] {r['kind']} "
              f"({r['length']}자 / 숫자 {r['numbers_checked']}개 검증)")
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
