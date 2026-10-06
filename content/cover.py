"""표지 선정 — `docs/02_CLI_디자인지시사항.md` 5-1항.

**"통계적으로 가장 튄 곳"과 "사람들이 아는 곳"은 다르다.**

지금까지는 평소 대비 배수 1위를 그냥 표지로 썼다. 그러면 매주 표지가 연천군·
가평군처럼 거래가 몇십 건인 외곽으로 간다. 수치는 맞지만 아무도 관심이 없고,
타임라인에서 그냥 넘어간다.

그래서 세 가지를 건다.

  ① 우선 후보  서울 25개 구 · 1기 신도시 · 거래량 상위 단지
                그 밖의 지역은 변화가 **확실히** 클 때만 (배수 1.5배 이상 차이)
  ② 앵글 순위  신고가 → 반전(가격·거래 역방향) → 평소 대비 급증·급감
  ③ 반복 방지  같은 지역이 2주 연속 표지에 오지 않는다

고른 이유는 매주 로그로 남긴다 (`output/cover_log.json`). 성과와 대조해
규칙을 고칠 때 "그때 왜 이걸 골랐지"를 되짚을 수 있어야 한다.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "output" / "cover_log.json"

MIN_SAMPLE = 10          # 표본이 이보다 적으면 표지 금지 (5-1, 6항)

# 단지 소개 캐러셀은 한 단지를 여섯 장에 걸쳐 설명한다. 그러려면 **받쳐줄
# 데이터**가 있어야 한다 — 추이를 그릴 만큼의 월별 기록과, 견줄 이웃 단지.
#
# 실측: 마포구 서강오벨리스크스위트는 신고가 +53.5% 로 1위였지만 창전동
# 같은 평형대에 비교할 단지가 **한 곳뿐**이었다. 그 상태로 "주변과 비교"
# 장을 만들면 막대 두 개짜리 그림이 나온다. 수치가 1위라고 글이 되는 게
# 아니다.
PROFILE_MIN_POINTS = 12      # 월별 기록
PROFILE_MIN_NEIGHBORS = 3    # 견줄 이웃 단지
# 그 단지의 **연간 거래량**. "많은 사람이 아는 곳"의 대리 지표다.
# 상승률로 줄 세우면 아무도 모르는 소형 단지가 1위로 올라온다.
POPULAR_MIN = 20
OUTSIDER_EDGE = 1.5      # 비우선 지역이 표지가 되려면 이만큼 더 커야 한다
RECENT_WEEKS = 1         # 직전 몇 회차까지 같은 지역을 막을 것인가

# 1기 신도시. 행정구역명으로 적는다 — 지표 JSON 이 쓰는 이름과 맞춰야
# 조용히 매칭에 실패하지 않는다.
NEWTOWN_1G = {
    "성남분당구",                      # 분당
    "고양일산동구", "고양일산서구",      # 일산
    "안양동안구",                      # 평촌
    "군포시",                          # 산본
    "부천원미구",                      # 중동
}

# 앵글 우선순위. 숫자가 작을수록 먼저다.
ANGLE_RANK = {"new_high": 0, "counter": 1, "surge": 2}
ANGLE_LABEL = {"new_high": "신고가", "counter": "반전", "surge": "급증·급감"}


# 이름 → 코드 역인덱스. 지표 행에 코드가 빠져 있을 때의 안전망이다.
#
# 이게 없으면 서울 25개 구가 통째로 "기타 지역"으로 떨어져 표지에서 밀린다.
# 실제로 그랬다 — daily.new_high 에 sigungu_code 가 없어서 마포·송파·성북이
# 전부 비우선으로 분류됐다. 지표 쪽도 고쳤지만, 조용히 틀리는 자리라
# 양쪽에 둔다.
def _name_to_code() -> dict[str, str]:
    import sys
    sys.path.insert(0, str(ROOT))
    from common import SIGUNGU_CODES
    out: dict[str, str] = {}
    for code, name in SIGUNGU_CODES.items():
        out.setdefault(name, code)
    return out


NAME_TO_CODE = _name_to_code()


def resolve(name: str, code: str | None) -> str | None:
    return str(code) if code else NAME_TO_CODE.get(name)


def is_seoul(code: str | None) -> bool:
    return bool(code) and str(code).startswith("11")


def is_priority(name: str, code: str | None = None) -> bool:
    """우선 후보인가 — 많은 사람이 이름을 아는 곳인가.

    코드를 못 받았으면 이름으로 되짚는다. 안전망을 호출부가 아니라 **여기**
    두는 이유는, 호출부가 늘 때마다 되짚기를 빠뜨릴 수 있어서다.
    """
    return is_seoul(resolve(name, code)) or name in NEWTOWN_1G


@dataclass
class Candidate:
    angle: str                 # new_high | counter | surge
    region: str                # 표지에 나올 지역명 (중복 방지 키)
    code: str | None
    headline: str              # 왜 이게 글이 되는가 (로그용 한 줄)
    strength: float            # 같은 앵글 안에서의 세기 (배수 등)
    sample: int                # 표본 (n<10 이면 탈락)
    data: dict = field(default_factory=dict)

    @property
    def priority(self) -> bool:
        return is_priority(self.region, self.code)

    def as_log(self) -> dict:
        return {"angle": self.angle, "angle_label": ANGLE_LABEL[self.angle],
                "region": self.region, "priority": self.priority,
                "headline": self.headline,
                "strength": round(self.strength, 2), "sample": self.sample}


# ── 후보 만들기 ──────────────────────────────────────────────────────────
def profile_ok(prof: dict | None) -> bool:
    """단지 소개를 끌고 갈 만한 프로필인가."""
    if not prof:
        return False
    return (len(prof.get("series") or []) >= PROFILE_MIN_POINTS
            and len(prof.get("neighbors") or []) >= PROFILE_MIN_NEIGHBORS
            and prof.get("deals_1y", 0) >= POPULAR_MIN)


def build(data: dict) -> list[Candidate]:
    out: list[Candidate] = []
    weekly = data.get("weekly") or {}
    daily = data.get("daily") or {}
    profs = data.get("profiles") or {}

    # ① 신고가 — 누적 거래가 두터운 평형만. 누적 6건짜리 "148% 경신"은
    #    시세가 아니라 표본이 만든 숫자다.
    for r in daily.get("new_high") or []:
        if r.get("history_count", 0) < MIN_SAMPLE:
            continue
        # 소개할 재료가 없으면 표지로 쓰지 않는다. 수치가 1위여도
        # 여섯 장을 채울 수 없으면 글이 안 된다.
        if not profile_ok(profs.get(r.get("apt_id"))):
            continue
        prof = profs[r["apt_id"]]
        # 세기는 **인기(연간 거래량)**다. 상승률은 헤드라인 숫자로 쓰되
        # 줄 세우는 데는 쓰지 않는다 — 한 단지를 여섯 장에 소개하는 포맷에서
        # 중요한 건 "그 단지를 아는 사람이 얼마나 되는가"다.
        out.append(Candidate(
            "new_high", r["sigungu_name"], r.get("sigungu_code"),
            f'{r["apt_name"]} 종전 최고가 경신 (+{r["over_peak_pct"]}%) · '
            f'1년 거래 {prof["deals_1y"]}건',
            prof["deals_1y"], r["history_count"], dict(r, profile=prof)))

    # ② 반전 — 값은 오르는데 거래는 줄었다. 숫자만 보면 "오르는 동네"로
    #    읽히는 구간이라 설명 가치가 가장 크다.
    for r in weekly.get("surge_apt") or []:
        if r["deals_recent"] >= r["deals_prior"] or r["change_pct"] <= 0:
            continue
        if r["deals_recent"] < MIN_SAMPLE:
            continue
        drop = (1 - r["deals_recent"] / r["deals_prior"]) * 100
        out.append(Candidate(
            "counter", r["sigungu_name"], r.get("sigungu_code"),
            f'{r["apt_name"]} 평단가 +{r["change_pct"]}% 인데 거래는 '
            f'{r["deals_prior"]}건 → {r["deals_recent"]}건',
            r["change_pct"] + drop, r["deals_recent"], r))

    # ③ 평소 대비 급증·급감
    for r in weekly.get("sgg_zscore") or []:
        base = r.get("deals_avg_52w")
        if not base or r["week_deals"] < MIN_SAMPLE:
            continue
        ratio = r["week_deals"] / base
        out.append(Candidate(
            "surge", r["sigungu_name"], r.get("sigungu_code"),
            f'{r["sigungu_name"]} 주간 거래 평소의 {ratio:.1f}배 '
            f'({base:.0f}건 → {r["week_deals"]}건)',
            abs(ratio - 1), r["week_deals"], {**r, "ratio": ratio}))
    return out


# ── 고르기 ───────────────────────────────────────────────────────────────
def recent_regions(asof: str | None = None, n: int = RECENT_WEEKS) -> set[str]:
    """직전 회차들의 표지 지역.

    **이번 회차는 뺀다.** 안 빼면 로그를 쓴 뒤 다시 고를 때 자기 자신이
    걸려서 다른 지역이 나온다 — 캐러셀은 마포구, 캡션은 구로구가 되는
    식으로 같은 발행물 안에서 말이 갈린다. 실제로 그렇게 어긋났다.
    """
    if not LOG.exists():
        return set()
    try:
        rows = json.loads(LOG.read_text(encoding="utf-8"))
    except Exception:
        return set()
    rows = [r for r in rows if r.get("asof") != asof]
    return {r["picked"]["region"] for r in rows[-n:] if r.get("picked")}


def choose(data: dict) -> tuple[Candidate | None, list[Candidate], list[str]]:
    """(고른 것, 후보 3개, 탈락 사유) 를 돌려준다.

    같은 지표 JSON 으로 몇 번을 불러도 같은 답이 나와야 한다 — 캐러셀·캡션·
    스레드가 각자 부르기 때문이다.
    """
    cands = build(data)
    why: list[str] = []
    if not cands:
        return None, [], ["표지로 쓸 만한 후보가 없다 (표본 미달)"]

    blocked = recent_regions(data.get("asof"))
    fresh = [c for c in cands if c.region not in blocked]
    if blocked and len(fresh) < len(cands):
        why.append(f"직전 회차 표지 지역 제외: {', '.join(sorted(blocked))}")
    cands = fresh or cands
    if not fresh:
        why.append("제외하고 나니 후보가 없어 반복 금지를 적용하지 않았다")

    # 비우선 지역은 우선 후보보다 **확실히** 클 때만 남긴다.
    # 같은 앵글 안에서 견준다 — 신고가 +30% 와 거래 1.7배는 비교 단위가 다르다.
    kept: list[Candidate] = []
    for c in cands:
        if c.priority:
            kept.append(c)
            continue
        peer = max((x.strength for x in cands
                    if x.priority and x.angle == c.angle), default=None)
        if peer is None or c.strength >= peer * OUTSIDER_EDGE:
            kept.append(c)
        else:
            why.append(
                f"{c.region}({ANGLE_LABEL[c.angle]}) 제외 — 우선 후보 최고"
                f"({peer:.2f})의 {OUTSIDER_EDGE}배 미만 ({c.strength:.2f})")
    cands = kept or cands

    # 앵글 우선순위 → 같은 앵글 안에서는 세기 순
    cands.sort(key=lambda c: (ANGLE_RANK[c.angle], -c.strength))
    return cands[0], cands[:3], why[:12]


def log(asof: str, picked: Candidate | None, top3: list[Candidate],
        notes: list[str]) -> None:
    """매주 후보 3개와 선정 이유를 남긴다 (5-1항, 10항 성과 측정의 입력)."""
    rows = []
    if LOG.exists():
        try:
            rows = json.loads(LOG.read_text(encoding="utf-8"))
        except Exception:
            rows = []
    rows = [r for r in rows if r.get("asof") != asof]
    rows.append({"asof": asof,
                 "picked": picked.as_log() if picked else None,
                 "candidates": [c.as_log() for c in top3],
                 "notes": notes})
    rows.sort(key=lambda r: r["asof"])
    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.write_text(json.dumps(rows, ensure_ascii=False, indent=2),
                   encoding="utf-8")
