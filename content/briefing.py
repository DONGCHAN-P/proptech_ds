"""이번 주 콘텐츠 후보 브리핑.

"뭘 만들지"를 사람이 지표 JSON 을 뒤져 고르면 오래 걸리고, 늘 같은 앵글만
집게 된다. 서로 다른 각도에서 다섯 개를 뽑아 한 번에 보여준다.

앵글 다섯
    신고가    같은 단지·같은 평형에서 종전 최고가를 넘었다
    반전      값은 올랐는데 손바뀜은 줄었다
    회복      전고점 가까이 돌아왔다
    급증·급감  지역 주간 거래가 그 지역의 평소와 다르다
    특이거래   직전 평균과 크게 벌어진 한 건

앵글당 둘까지만, 지역은 겹치지 않게 고른다. 그러지 않으면 한 주 콘텐츠가
전부 "신고가"가 된다.

**바로 만들 수 있는지**도 같이 적는다. 단지 소개 6장은 월별 기록과 견줄
이웃 단지가 있어야 끌고 갈 수 있는데(cover.profile_ok), 프로필은 매번 8개
단지만 만들어진다. 후보가 그 8개 밖이면 build_metrics 를 다시 돌려야 한다.
그걸 모르고 고르면 작업 중간에 막힌다.

실행:
  .venv\\Scripts\\python.exe -m content.briefing
  .venv\\Scripts\\python.exe -m content.briefing --n 8
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from content import aptname as AN  # noqa: E402
from content import cover as CV  # noqa: E402
from content import design as D  # noqa: E402

MIN_SAMPLE = 10            # 표본이 이보다 적으면 후보로 올리지 않는다
MAX_PER_ANGLE = 2          # 같은 앵글이 덱을 다 채우지 않게
RECOVER_NEAR = -5.0        # 전고점 대비 이보다 가까우면 "회복"
RATIO_BAND = (0.75, 1.3)   # 이 안이면 평소와 비슷 — 쓸 거리가 없다
HIST_MIN_WEEKS = 26        # "평소"를 말하려면 반년은 쌓여야 한다
OUTLIER_REF_MIN = 5

ANGLE_ORDER = ["신고가", "반전", "회복", "급증·급감", "특이거래"]

FMT_READY = "릴스 + 캐러셀 6장 (프로필 있음, 바로 제작)"
FMT_REBUILD = "릴스 + 캐러셀 6장 (프로필 재생성 필요)"


@dataclass
class Idea:
    angle: str
    region: str
    subject: str          # 단지명 또는 지역명
    headline: str         # 그대로 쓸 수 있는 한 줄
    why: str              # 왜 글이 되는가
    sample: str           # 표본 — 숫자를 믿어도 되는 근거
    caution: str = ""
    ready: bool = False   # 프로필이 이미 있어 바로 만들 수 있는가
    # 덱으로 못 끌고 가는 소재는 그 이유를 적는다. 빈 문자열이면 덱 가능.
    thread_why: str = ""
    priority: bool = False
    score: float = 0.0
    data: dict = field(default_factory=dict)

    @property
    def apt(self) -> bool:
        return not self.thread_why

    @property
    def fmt(self) -> str:
        if self.thread_why:
            return f"스레드 1편 ({self.thread_why})"
        return FMT_READY if self.ready else FMT_REBUILD


def index(profs: dict) -> dict:
    """프로필을 apt_id 와 (단지명, 시군구) 양쪽으로 찾을 수 있게 색인한다.

    vs_peak·surge_apt 행에는 apt_id 가 없다. 이름으로도 찾지 않으면 프로필이
    있는데도 "재생성 필요"로 잘못 적힌다.
    """
    out: dict = {}
    for k, p in (profs or {}).items():
        out[k] = p
        out[(p.get("apt_name"), p.get("sigungu_name"))] = p
    return out


def lookup(idx: dict, r: dict) -> dict | None:
    """단지+평형이 맞는 프로필. 평형이 어긋나면 덱의 숫자가 어긋난다."""
    hit = CV.find_profile(idx, r)
    if hit:
        return hit
    # 이름으로 찾은 건 평형까지 맞을 때만 받는다
    by_name = idx.get((r.get("apt_name"), r.get("sigungu_name")))
    py = r.get("pyeong_bucket")
    if by_name and (not py or by_name.get("pyeong_bucket") == py):
        return by_name
    return None


def build(data: dict) -> list[Idea]:
    """앵글별 후보를 전부 만든다. 고르는 건 pick() 이 한다."""
    AN.normalize(data)
    daily = data.get("daily") or {}
    weekly = data.get("weekly") or {}
    idx = index(data.get("profiles") or {})
    out: list[Idea] = []

    # (1) 신고가 — 인기 단지일수록 글이 된다
    for r in daily.get("new_high") or []:
        if r.get("history_count", 0) < MIN_SAMPLE:
            continue
        prof = lookup(idx, r)
        pop = (prof or {}).get("deals_1y")
        name = r["apt_name"]
        sample = f'이 평형 누적 {D.num(r["history_count"])}건'
        if pop:
            sample += f' · 단지 1년 {pop}건'
        out.append(Idea(
            "신고가", r["sigungu_name"], name,
            f'{r["sigungu_name"]} {name}, 종전 최고가를 '
            f'{r["over_peak_pct"]}% 넘겼어요',
            f'{D.won(r["prev_peak"])} → {D.won(r["deal_amount"])}. '
            f'신고가는 사실 진술이라 그대로 쓸 수 있다',
            sample,
            caution=("상승폭이 작아 헤드라인이 약하다"
                     if r["over_peak_pct"] < 3 else ""),
            ready=CV.profile_ok(prof),
            score=pop if pop else r["history_count"] / 10, data=r))

    # (2) 반전 — 값은 올랐는데 손바뀜은 줄었다. 설명 가치가 가장 크다
    for r in weekly.get("surge_apt") or []:
        if r["deals_recent"] < MIN_SAMPLE or r["change_pct"] <= 0:
            continue
        if r["deals_recent"] >= r["deals_prior"]:
            continue
        name = r["apt_name"]
        up = D.delta(r["change_pct"], arrow=False)
        out.append(Idea(
            "반전", r["sigungu_name"], name,
            f'{r["sigungu_name"]} {name}, 값은 {up}인데 거래는 줄었어요',
            "숫자만 보면 그냥 오르는 단지로 읽히는 구간이라 "
            "설명을 붙일 자리가 넓다",
            f'최근 90일 {r["deals_recent"]}건 / 직전 {r["deals_prior"]}건',
            ready=CV.profile_ok(lookup(idx, r)),
            score=r["deals_recent"], data=r))

    # (3) 회복 — 전고점 가까이 돌아왔다.
    # near_peak 이 없는 옛 지표 파일이면 vs_peak 으로 떨어진다. 그 목록은
    # 낙폭 큰 쪽으로 정렬돼 있어 조건에 걸리는 행이 거의 없다 — 정상이다.
    for r in daily.get("near_peak") or daily.get("vs_peak") or []:
        v = r.get("vs_peak_pct")
        if r.get("history_count", 0) < MIN_SAMPLE or v is None:
            continue
        if v < RECOVER_NEAR or v >= 0:
            continue
        name = r["apt_name"]
        peak_ym = str(r["peak_date"])[:7]
        out.append(Idea(
            "회복", r["sigungu_name"], name,
            f'{r["sigungu_name"]} {name}, 전고점까지 {abs(v):.1f}% 남았어요',
            "전고점은 사람들이 기준선으로 삼는 숫자라 반응이 온다",
            f'누적 {D.num(r["history_count"])}건 · 전고점 {peak_ym}',
            ready=CV.profile_ok(lookup(idx, r)),
            score=r["history_count"] / 10, data=r))

    # (4) 급증·급감 — 지역 단위. 단지 덱으로는 못 끌고 간다
    for r in weekly.get("sgg_zscore") or []:
        base = r.get("deals_avg_52w")
        if not base or r["week_deals"] < MIN_SAMPLE:
            continue
        if (r.get("hist_weeks") or 0) < HIST_MIN_WEEKS:
            continue
        ratio = r["week_deals"] / base
        if RATIO_BAND[0] <= ratio <= RATIO_BAND[1]:
            continue
        way = "늘었어요" if ratio > 1 else "줄었어요"
        out.append(Idea(
            "급증·급감", r["sigungu_name"], r["sigungu_name"],
            f'{r["sigungu_name"]} 거래가 평소의 {ratio:.1f}배로 {way}',
            "다른 지역과 견준 게 아니라 그 지역의 평소와 견준 값이라 "
            "설명이 짧다",
            f'이번 주 {r["week_deals"]}건 / 평소 {D.num(base)}건 '
            f'({r["hist_weeks"]}주 기준)',
            thread_why="지역 단위라 단지 덱 불가",
            score=r["week_deals"],
            data={**r, "ratio": round(ratio, 2)}))

    # (5) 특이거래 — 한 건이지만 눈에 띈다
    for r in daily.get("outlier") or []:
        if r.get("ref_count", 0) < OUTLIER_REF_MIN:
            continue
        name = r["apt_name"]
        g = abs(r["deviation_pct"])
        out.append(Idea(
            "특이거래", r["sigungu_name"], name,
            f'{r["sigungu_name"]} {name}, 직전 평균과 {g:.1f}% 벌어진 거래',
            "한 건으로 시세를 말할 수 없다는 걸 같이 설명하면 신뢰가 쌓인다",
            f'비교 기준 {r["ref_count"]}건 · {r["floor_band"]} · '
            f'평균 {D.won(r["ref_avg"])}',
            caution="증여성·저층 거래가 섞일 수 있어 단정하지 말 것",
            thread_why="한 건짜리 사건이라 6장을 못 채움",
            score=r["ref_count"], data=r))

    for i in out:
        i.priority = CV.is_priority(i.region, i.data.get("sigungu_code"))
    return out


APT_N = 5
TRADE = ROOT / "master" / "trade_events.parquet"


def deals_1y(apt_ids: list[str], asof: str) -> dict[str, int]:
    """단지별 최근 1년 거래 건수. 인기의 대리 지표다.

    상승률로 줄 세우면 아무도 모르는 소형 단지가 1위가 된다. 한 단지를
    여섯 장에 소개하는 포맷에서는 "그 단지를 아는 사람이 얼마나 되는가"가
    더 중요하다 — cover.py 가 쓰는 기준과 같다.

    DB 를 못 열면 빈 dict. 부르는 쪽은 누적 거래로 줄 세우면 된다.
    """
    if not apt_ids or not TRADE.exists():
        return {}
    try:
        import duckdb
        from metrics.filters import trades_cte
        ids = ",".join(f"'{a}'" for a in set(apt_ids))
        con = duckdb.connect()
        try:
            rows = con.execute(f"""
                {trades_cte(TRADE.as_posix())}
                SELECT apt_id, count(*) FROM trades
                WHERE apt_id IN ({ids})
                  AND deal_date > DATE '{asof}' - INTERVAL 1 YEAR
                  AND deal_date <= DATE '{asof}'
                GROUP BY 1
            """).fetchall()
        finally:
            con.close()
        return {a: n for a, n in rows}
    except Exception as e:
        print(f"  거래량 조회 실패 ({type(e).__name__}) — 누적 거래로 줄 세운다")
        return {}


def apt_candidates(data: dict, n: int = APT_N) -> list[dict]:
    """덱으로 만들 수 있는 **단지** 후보.

    briefing 의 다섯 앵글과 다르다. 저쪽은 "무엇을 쓸까"를 넓게 펴는 쪽이고,
    여기는 "지금 영상 하나를 만든다면 어느 단지인가"만 본다. 그래서 단지가
    특정되는 신고가 행만 쓴다 — 지역 단위(급증·급감)나 한 건짜리(특이거래)는
    여섯 장을 못 채운다.

    같은 시군구는 하나만 올린다. 다섯 개가 전부 화성시면 고를 이유가 없다.
    """
    AN.normalize(data)   # 봇 카드에도 같은 이름이 나가야 한다
    rows = [r for r in (data.get("daily", {}).get("new_high") or [])
            if r.get("history_count", 0) >= MIN_SAMPLE
            and r.get("apt_id") and r.get("pyeong_bucket")]
    if not rows:
        return []
    pop = deals_1y([r["apt_id"] for r in rows], data["asof"])
    idx = index(data.get("profiles") or {})

    seen: set[tuple] = set()
    uniq = []
    for r in rows:
        k = (r["apt_id"], r["pyeong_bucket"])
        if k in seen:
            continue
        seen.add(k)
        uniq.append(r)

    uniq.sort(key=lambda r: (
        not CV.is_priority(r["sigungu_name"], r.get("sigungu_code")),
        -(pop.get(r["apt_id"]) or r["history_count"] / 10)))

    out, regions = [], set()
    for r in uniq:
        if len(out) >= n:
            break
        if r["sigungu_name"] in regions:
            continue
        regions.add(r["sigungu_name"])
        out.append({
            "key": f'{r["apt_id"]}:{r["pyeong_bucket"]}',
            "apt_name": r["apt_name"], "region": r["sigungu_name"],
            "dong": r.get("legal_dong_name", ""),
            "pyeong": D.pyeong(r["pyeong_bucket"]),
            "amount": D.won(r["deal_amount"]),
            "over": r["over_peak_pct"],
            "hist": r["history_count"],
            "deals_1y": pop.get(r["apt_id"]),
            "ready": CV.profile_ok(CV.find_profile(idx, r)),
            "priority": CV.is_priority(r["sigungu_name"],
                                       r.get("sigungu_code")),
            "row": r,
        })
    return out


SEARCH_N = 8


def search_apts(data: dict, term: str, n: int = SEARCH_N) -> list[dict]:
    """이름으로 단지를 찾는다. **오늘 신고가 목록 안에서만** 찾는다.

    덱의 첫 장이 "종전 최고가"라서, 신고가가 아닌 단지로 만들면 그 헤드라인이
    거짓말이 된다. 아무 단지나 찾아 주면 쓸 수 없는 걸 고르게 되므로, 애초에
    만들 수 있는 것만 보여 준다.

    띄어쓰기는 무시한다 — 사람은 "목동신시가지" 로 치고 데이터에는
    "목동 신시가지" 로 들어 있다 (aptname 정규화 뒤).
    """
    AN.normalize(data)
    key = "".join(str(term).split()).lower()
    if not key:
        return []
    rows = [r for r in (data.get("daily", {}).get("new_high") or [])
            if r.get("history_count", 0) >= MIN_SAMPLE
            and r.get("apt_id") and r.get("pyeong_bucket")
            and key in "".join(str(r.get("apt_name", "")).split()).lower()]
    pop = deals_1y([r["apt_id"] for r in rows], data["asof"])
    idx = index(data.get("profiles") or {})
    rows.sort(key=lambda r: -(pop.get(r["apt_id"])
                              or r["history_count"] / 10))
    out = []
    for r in rows[:n]:
        out.append({
            "key": f'{r["apt_id"]}:{r["pyeong_bucket"]}',
            "apt_name": r["apt_name"], "region": r["sigungu_name"],
            "dong": r.get("legal_dong_name", ""),
            "pyeong": D.pyeong(r["pyeong_bucket"]),
            "amount": D.won(r["deal_amount"]),
            "over": r["over_peak_pct"], "hist": r["history_count"],
            "deals_1y": pop.get(r["apt_id"]),
            "ready": CV.profile_ok(CV.find_profile(idx, r)),
            "priority": CV.is_priority(r["sigungu_name"],
                                       r.get("sigungu_code")),
            "row": r,
        })
    return out


def pyeongs_of(data: dict, apt_id: str) -> list[dict]:
    """같은 단지의 다른 평형. 둘이 같은 날 신고가를 치는 일이 있다."""
    AN.normalize(data)
    rows = [r for r in (data.get("daily", {}).get("new_high") or [])
            if r.get("apt_id") == apt_id
            and r.get("history_count", 0) >= MIN_SAMPLE]
    idx = index(data.get("profiles") or {})
    rows.sort(key=lambda r: -r["history_count"])
    return [{
        "key": f'{r["apt_id"]}:{r["pyeong_bucket"]}',
        "apt_name": r["apt_name"], "region": r["sigungu_name"],
        "dong": r.get("legal_dong_name", ""),
        "pyeong": D.pyeong(r["pyeong_bucket"]),
        "amount": D.won(r["deal_amount"]),
        "over": r["over_peak_pct"], "hist": r["history_count"],
        "deals_1y": None,
        "ready": CV.profile_ok(CV.find_profile(idx, r)),
        "priority": CV.is_priority(r["sigungu_name"], r.get("sigungu_code")),
        "row": r,
    } for r in rows]


def pick(ideas: list[Idea], n: int = 5) -> list[Idea]:
    """앵글과 지역이 겹치지 않게 고른다.

    1차로 앵글마다 하나씩 채우고(다양성), 남는 자리를 점수 순으로 채운다.
    우선 지역(서울 25개 구·1기 신도시)을 앞세운다.
    """
    pool = sorted(ideas, key=lambda i: (not i.priority, -i.score))
    chosen: list[Idea] = []
    taken: set[int] = set()
    seen_angle: dict[str, int] = {}
    seen_region: set[str] = set()

    for new_angle_only in (True, False):
        for i in pool:
            if len(chosen) >= n:
                break
            if id(i) in taken:
                continue
            used = seen_angle.get(i.angle, 0)
            if new_angle_only and used:
                continue
            if used >= MAX_PER_ANGLE or i.region in seen_region:
                continue
            chosen.append(i)
            taken.add(id(i))
            seen_angle[i.angle] = used + 1
            seen_region.add(i.region)

    chosen.sort(key=lambda i: (ANGLE_ORDER.index(i.angle)
                               if i.angle in ANGLE_ORDER else 99, -i.score))
    return chosen


def as_dicts(picked: list[Idea]) -> list[dict]:
    return [{"angle": i.angle, "region": i.region, "subject": i.subject,
             "headline": i.headline, "why": i.why, "sample": i.sample,
             "caution": i.caution, "format": i.fmt, "apt": i.apt,
             "ready": i.ready, "priority": i.priority} for i in picked]


def main() -> int:
    ap = argparse.ArgumentParser(description="이번 주 콘텐츠 후보")
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--metrics")
    a = ap.parse_args()

    files = sorted((ROOT / "output").glob("metrics_*.json"))
    src = Path(a.metrics) if a.metrics else (files[-1] if files else None)
    if src is None or not src.exists():
        print("지표 JSON 이 없다. 먼저: python -m metrics.build_metrics")
        return 1
    data = json.loads(src.read_text(encoding="utf-8"))

    ideas = build(data)
    picked = pick(ideas, a.n)
    bar = "=" * 72
    counts: dict[str, int] = {}
    for i in ideas:
        counts[i.angle] = counts.get(i.angle, 0) + 1

    print(f"\n{bar}\n  콘텐츠 후보  기준일 {data['asof']}")
    print("  후보 풀  " + " · ".join(
        f"{k} {counts.get(k, 0)}" for k in ANGLE_ORDER))
    print(bar)
    for k, i in enumerate(picked, 1):
        where = "우선지역" if i.priority else "기타지역"
        print(f"\n{k}. [{i.angle}] {i.subject}  ({i.region} · {where})")
        print(f"   헤드라인  {i.headline}")
        print(f"   왜        {i.why}")
        print(f"   표본      {i.sample}")
        print(f"   포맷      {i.fmt}")
        if i.caution:
            print(f"   주의      {i.caution}")

    out = ROOT / "output" / data["asof"] / "briefing.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(as_dicts(picked), ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"\n  저장: {out}\n{bar}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
