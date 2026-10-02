"""T12 — 발행 전 검증기 (3중 안전장치).

발행 경로는 **반드시** 여기를 통과한다. 우회 경로를 만들지 않는다.

  ① 면책 문구가 붙어 있는가
  ② 금지 표현이 섞이지 않았는가   — 투자 권유로 읽히면 안 된다
  ③ 글의 모든 숫자가 원본에 있는가 — LLM 이 숫자를 지어내면 즉시 차단

③ 이 가장 중요하다. LLM 에게는 JSON 숫자를 문장으로 옮기는 일만 맡기고,
재계산이나 창작은 시키지 않는다. 그 약속이 지켜졌는지 기계가 확인한다.
사람이 눈으로 보는 것으로는 못 막는다.

쓰는 법:

    from content.validator import validate
    r = validate(text, facts)
    if not r.ok:
        raise RuntimeError(r.reasons)
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from templates.disclaimers import ALL_DISCLAIMERS

# ── ② 금지 표현 ──────────────────────────────────────────────────────────
#
# 각 패턴은 띄어쓰기를 무시하도록 정규화된 문자열에 대해 돌린다("매수 추천"도
# 걸린다). 내부 지표명으로 쓰는 "저평가"는 발행 문구에서 금지다 —
# run_step7_undervalue.py 의 산출물명이 그거라 혼동하기 쉽다.
BANNED = [
    (r"매수추천|매도추천|매수를추천|매도를추천", "매수·매도 추천"),
    (r"저평가|고평가", "가치 판단 단정 (내부 지표명이지 발행 표현이 아니다)"),
    (r"무조건오를|무조건오른|반드시오를|확실히오를", "가격 상승 단정"),
    (r"떡상|떡락|존버|불장", "투자 속어"),
    (r"강추|적극추천|추천합니다|추천드립니다|추천종목", "추천 프레이밍"),
    (r"바닥확인|바닥을확인|상투|꼭지", "시점 단정"),
    (r"지금사야|지금이기회|지금진입|막차", "매수 시점 권유"),
    (r"사지마세요|팔아야|손절하세요|익절하세요", "매도 권유"),
    (r"오를것|오를겁니다|오를예정|상승할것|하락할것|떨어질것", "가격 예측"),
    (r"수익률보장|원금보장|보장합니다", "수익 보장"),
    (r"유망|알짜|숨은보석|흙속의진주", "가치 단정 수식"),
]

# ── ③ 숫자 검증 ──────────────────────────────────────────────────────────
#
# 글에서 뽑아낸 숫자가 전부 facts 에서 유래해야 한다. 해시태그·연월·단위처럼
# 숫자가 아닌 맥락은 먼저 지운다.
_NUM = re.compile(r"[-+]?\d[\d,]*(?:\.\d+)?")

# 검증에서 빼는 토큰 — 글 구조에서 나오는 숫자지 데이터가 아니다
_STRIP = [
    re.compile(r"#\S+"),                       # 해시태그
    re.compile(r"https?://\S+"),               # URL
    re.compile(r"\d{4}-\d{2}-\d{2}"),          # 날짜 (별도 검증)
    re.compile(r"\d{4}년\s*\d{1,2}월(\s*\d{1,2}일)?"),
]


@dataclass
class Result:
    ok: bool = True
    reasons: list[str] = field(default_factory=list)
    numbers_checked: int = 0

    def fail(self, why: str) -> None:
        self.ok = False
        self.reasons.append(why)


def _squash(s: str) -> str:
    """공백·구두점을 지우고 NFKC 정규화. '매 수 추천' 같은 우회를 막는다."""
    s = unicodedata.normalize("NFKC", s)
    return re.sub(r"[\s​·,./\-_*~`'\"()\[\]]", "", s)


def check_banned(text: str) -> list[str]:
    """금지 표현 검사.

    면책 문구는 검사에서 뺀다. "매수·매도를 추천하거나 ... 보장하지 않으며"
    처럼 부정문 안에 금지어가 들어 있어서, 그대로 돌리면 승인된 고정 문구가
    자기 자신에게 걸린다. 면책의 존재 여부는 check_disclaimer 가 따로 본다.
    """
    squashed = _squash(text)
    for fixed in ALL_DISCLAIMERS.values():
        squashed = squashed.replace(_squash(fixed), "")
    hits = []
    for pat, label in BANNED:
        m = re.search(pat, squashed)
        if m:
            hits.append(f"금지 표현 '{m.group(0)}' ({label})")
    return hits


def _variants(v) -> set[str]:
    """하나의 값이 글에 나타날 수 있는 모든 표기."""
    out: set[str] = set()
    if v is None:
        return out
    if isinstance(v, bool):
        return out
    if isinstance(v, str):
        for m in _NUM.finditer(v):
            out |= _variants_num(_to_num(m.group(0)))
        return out
    if isinstance(v, (int, float)):
        return _variants_num(float(v))
    return out


def _to_num(s: str) -> float:
    return float(s.replace(",", "").replace("+", ""))


def _variants_num(n: float) -> set[str]:
    """숫자 하나의 표기 변형. 반올림·단위 변환까지 포함한다."""
    out: set[str] = set()

    def add(x: float) -> None:
        out.add(f"{x:.4f}".rstrip("0").rstrip("."))

    add(n)
    add(abs(n))
    add(round(n))
    add(round(abs(n)))
    for d in (1, 2):
        add(round(n, d))
        add(round(abs(n), d))
    # 만원 -> 억 (10.3억, 11억)
    if abs(n) >= 1000:
        for d in (0, 1, 2):
            add(round(n / 10000, d))
            add(round(abs(n) / 10000, d))
    # 비율은 소수/퍼센트 양쪽
    if abs(n) <= 1:
        add(round(n * 100, 1))
        add(round(abs(n) * 100, 1))
    return out


def allowed_numbers(facts) -> set[str]:
    """facts 안의 모든 값에서 허용 숫자 집합을 만든다."""
    out: set[str] = set()
    stack = [facts]
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            stack.extend(cur.values())
        elif isinstance(cur, (list, tuple)):
            stack.extend(cur)
        else:
            out |= _variants(cur)
    return out


def check_numbers(text: str, facts) -> tuple[list[str], int]:
    body = text
    for pat in _STRIP:
        body = pat.sub(" ", body)
    allow = allowed_numbers(facts)

    bad, checked = [], 0
    for m in _NUM.finditer(body):
        raw = m.group(0)
        try:
            n = _to_num(raw)
        except ValueError:
            continue
        checked += 1
        if _variants_num(n) & allow:
            continue
        # 글 구조에서 나오는 작은 정수(순번 등)는 눈감아 준다
        if n == int(n) and 0 <= n <= 10:
            continue
        ctx = body[max(0, m.start() - 18):m.end() + 18].strip().replace("\n", " ")
        bad.append(f"출처 없는 숫자 '{raw}' … {ctx}")
    return bad, checked


def check_disclaimer(text: str, kind: str = "social") -> list[str]:
    want = ALL_DISCLAIMERS.get(kind)
    if want is None:
        return [f"알 수 없는 면책 종류 '{kind}'"]
    if _squash(want) not in _squash(text):
        return [f"면책 문구 누락 ({kind})"]
    return []


def check_floor_exposure(text: str) -> list[str]:
    """정확한 층수 노출 차단.

    동·호수를 안 써도 '15층'이면 특정 세대가 좁혀진다. 지표는 저/중/고
    구간만 내보내므로(T9), 글에 층수가 있으면 LLM 이 지어낸 것이다.
    """
    m = re.search(r"\d+\s*층", text)
    return [f"정확한 층수 노출 '{m.group(0)}' — 저/중/고 구간만 쓴다"] if m else []


def validate(text: str, facts, *, kind: str = "social",
             require_disclaimer: bool = True) -> Result:
    r = Result()
    if require_disclaimer:
        for why in check_disclaimer(text, kind):
            r.fail(why)
    for why in check_banned(text):
        r.fail(why)
    for why in check_floor_exposure(text):
        r.fail(why)
    bad, checked = check_numbers(text, facts)
    r.numbers_checked = checked
    for why in bad:
        r.fail(why)
    return r
