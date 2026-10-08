"""맞춤 찾기 — 사용자 조건에 잘 맞는 단지 Top5.

추천이 아니라 **조건 적합도 순위**다. 사용자가 고른 조건(예산·평형·통근·지역·
우선순위)에 얼마나 맞는지만 재고, 오를 것 같은 지표(모멘텀·가속도)는 넣지 않는다.

    하드 필터 → 점수(가격 30 · 통근 25 · 우선순위 45) → 단지당 1행 · 동당 2곳
    → 5곳 미만이면 통근 +15분, 예산 ×1.1 순으로 넓힌다

통근은 키 없이 계산하는 **추정**이다 (역 좌표 + 노선만 있고 노선도는 없다).
    도보(집→역) + 대기 + 역간 직선거리×굴곡 ÷ 표정속도 + 환승 + 도보(역→회사)
집·회사 각각 가까운 역 3곳의 9개 조합 중 최솟값을 쓴다.

순수 함수만 둔다. 파일을 읽는 일은 web/main.py 가 한다.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from datetime import date, timedelta

import numpy as np
import pandas as pd

# ── 통근 추정 상수 ────────────────────────────────────────────────────
WALK_KMH = 4.5
WALK_DETOUR = 1.25        # 직선 → 실제 보행 경로
# 역간 **직선거리** 기준 표정속도. 짧은 구간은 정차가 촘촘해 느리고, 먼 구간은 선로가
# 곧고 급행이 섞여 빠르다. 실측 몇 개로 맞췄다 (직선 km → 실제 탑승 분):
#   잠실→강남 2호선 6km 17분 · 사당→시청 4호선 8km 20분 · 부평→서울역 1호선 24km 40분
RIDE_KMH_BASE = 18.0
RIDE_KMH_PER_KM = 0.9
RIDE_KMH_MAX = 42.0
# 정차가 드문 노선 — 같은 노선으로 끝까지 가면 더 빠르다 (강남→판교 13km 16분)
FAST_LINES = {"신분당선", "공항철도", "GTX-A", "GTX-B", "GTX-C"}
FAST_BONUS = 1.35
WAIT_MIN = 4.0
TRANSFER_MIN = 7.0
WALK_ONLY_KM = 1.5        # 이 안쪽이면 걸어가는 경우와 비교
K_NEAR = 3

COMMUTE_SLACK = 10        # 추정 오차만큼 허용시간에 여유
COMMUTE_FULL = 20         # 이 이하면 통근 점수 만점
COMMUTE_OPEN_END = 150    # "2시간 이상"(제한 없음)일 때 통근 점수가 0 이 되는 지점

# ── 점수 가중치 ───────────────────────────────────────────────────────
W_PRICE, W_COMMUTE, W_PRIORITY = 0.30, 0.25, 0.45
STALE_YEARS = 2           # 이보다 오래된 거래가로는 '지금 이 가격' 이라고 말할 수 없다
# 최근 1년 거래가 얇으면 가격이 지금과 다를 수 있다 — 순위를 조금 내린다
CONFIDENCE = {0: 0.88, 1: 0.95}
MIN_TRADES = 3            # 그 평형의 누적 거래 — 시세라고 부를 최소 표본
# 세대수가 없어(T6b) 단지 전체 누적 거래로 규모를 가린다. 나홀로 단지가 역 앞이라는
# 이유만으로 1위에 오르는 걸 막는다. 신축은 거래 기간이 짧아 기준을 낮춘다.
MIN_APT_TRADES = 50
MIN_APT_TRADES_NEW = 15
NEW_BUILD_YEARS = 5

# key → (라벨, 컬럼, 클수록 좋은가). 점수는 priority_score() 의 절대 기준을 쓴다 —
# 후보 안 상대 순위로 매기면 2005년 준공이 '신축' 1등이 되고 적합도가 부풀려진다.
PRIORITIES: dict[str, tuple[str, str, bool]] = {
    "station": ("역세권", "walk_min", False),
    "school": ("학군", "elem_school_cnt_1km", True),
    "new": ("신축", "build_year", True),
    "green": ("녹지", "green_score", True),
    "active": ("거래 활발", "trade_1y", True),
}

HOUSEHOLD_DEFAULTS = {
    "single": {"pyeongs": ["20P"], "priorities": ["station"]},
    "couple": {"pyeongs": ["25P", "30P"], "priorities": ["station"]},
    "kids": {"pyeongs": ["30P", "35P"], "priorities": ["school"]},
}

# 평형 코드 → 화면에서 부르는 이름. 대형·소형은 코드 여러 개가 한 묶음이라
# "같은 구 대형 중" 이라고 하면 비교 집단을 잘못 말하게 된다 → 비슷한 면적.
AREA_LABEL = {"20P": "59㎡대", "25P": "74㎡대", "30P": "84㎡대"}

PYEONG_CODES = ["10P", "15P", "20P", "25P", "30P", "35P", "40P", "50P", "60P+"]


# ── 답변 ──────────────────────────────────────────────────────────────
@dataclass
class Answers:
    household: str = "couple"
    budget: float | None = None                  # 만원
    pyeongs: list[str] = field(default_factory=list)
    work: tuple[float, float] | None = None      # (lat, lng)
    work2: tuple[float, float] | None = None     # 함께 사는 사람의 근무지 (맞벌이)
    commute_max: int | None = 60                 # None = 2시간 이상 (시간으로 거르지 않음)
    commute_strict: bool = False                 # "30분 미만" — 추정 여유 없이 자른다
    sgg: list[str] = field(default_factory=list)
    priorities: list[str] = field(default_factory=list)

    @classmethod
    def from_payload(cls, p: dict) -> "Answers":
        def point(v):
            if isinstance(v, dict) and v.get("lat") is not None:
                return (float(v["lat"]), float(v["lng"]))
            if isinstance(v, (list, tuple)) and len(v) == 2:
                return (float(v[0]), float(v[1]))
            return None
        work, work2 = point(p.get("work")), point(p.get("work2"))
        if work is None:
            work, work2 = work2, None
        budget = p.get("budget")
        return cls(
            household=str(p.get("household") or "couple"),
            budget=float(budget) if budget else None,
            pyeongs=[x for x in (p.get("pyeongs") or []) if x in PYEONG_CODES],
            work=work,
            work2=work2,
            commute_max=(None if p.get("commute_max") in (None, "", 0) and "commute_max" in p
                         else int(p.get("commute_max") or 60)),
            commute_strict=bool(p.get("commute_strict")),
            sgg=[str(x) for x in (p.get("sgg") or []) if x],
            priorities=[x for x in (p.get("priorities") or []) if x in PRIORITIES][:3],
        )


# ── 거리 · 통근 ───────────────────────────────────────────────────────
def haversine_km(lat1, lng1, lat2, lng2):
    lat1, lng1, lat2, lng2 = (np.radians(np.asarray(x, dtype=float))
                              for x in (lat1, lng1, lat2, lng2))
    a = (np.sin((lat2 - lat1) / 2) ** 2
         + np.cos(lat1) * np.cos(lat2) * np.sin((lng2 - lng1) / 2) ** 2)
    return 6371.0 * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def walk_minutes(km):
    return np.asarray(km, dtype=float) * WALK_DETOUR / WALK_KMH * 60


# 운영상 한 열차로 직결되는 노선들 — 이름이 달라도 갈아타지 않는다.
# 부평(경인선) → 서울역(경부선) 이 환승으로 잡혀 80분이 나오던 문제.
LINE_ALIAS = {
    "경인선": "1호선", "경부선": "1호선", "경원선": "1호선", "장항선": "1호선",
    "중앙선": "경의중앙선", "경의선": "경의중앙선",
    "분당선": "수인분당선", "수인선": "수인분당선",
}


def norm_line(line: str) -> str:
    """'9호선(연장)' · '신분당선(연장2)' · '7호선(인천)' 을 본선과 같은 노선으로 본다."""
    s = re.sub(r"\(.*?\)", "", str(line)).strip()
    return LINE_ALIAS.get(s, s)


def ride_minutes(km, line_a, line_b):
    km = np.asarray(km, dtype=float)
    a = np.vectorize(norm_line)(np.asarray(line_a, dtype=object))
    b = np.vectorize(norm_line)(np.asarray(line_b, dtype=object))
    same = a == b
    kmh = np.clip(RIDE_KMH_BASE + RIDE_KMH_PER_KM * km, RIDE_KMH_BASE, RIDE_KMH_MAX)
    fast = same & np.isin(a, list(FAST_LINES))
    kmh = np.where(fast, kmh * FAST_BONUS, kmh)
    return WAIT_MIN + km / kmh * 60 + np.where(same, 0.0, TRANSFER_MIN)


class Stations:
    """지하철역 좌표·노선. 통근 추정의 유일한 근거."""

    CHUNK = 4000

    def __init__(self, df: pd.DataFrame):
        df = df.dropna(subset=["lat", "lng"]).reset_index(drop=True)
        self.df = df
        self.lat = df["lat"].to_numpy(float)
        self.lng = df["lng"].to_numpy(float)
        self.line = df["line"].map(norm_line).to_numpy(object)
        # '남한산성입구(성남법원.검찰청)' → '남한산성입구' (표시용)
        self.name = df["station_name"].map(lambda x: re.sub(r"\(.*?\)", "", str(x)).strip()).to_numpy(object)

    def nearest(self, lat, lng, k: int = K_NEAR) -> tuple[np.ndarray, np.ndarray]:
        """각 점의 가까운 역 k곳 (인덱스, km).

        4만 점 × 800역을 한 번에 계산하면 거리 행렬만 250MB 다 — 1GB 서버에서 기동 피크가
        된다. CHUNK 행씩 나눠 계산한다.
        """
        lat = np.atleast_1d(np.asarray(lat, dtype=float))
        lng = np.atleast_1d(np.asarray(lng, dtype=float))
        k = min(k, len(self.lat))
        idx = np.empty((len(lat), k), dtype=np.int32)
        dist = np.empty((len(lat), k), dtype=float)
        for a in range(0, len(lat), self.CHUNK):
            b = a + self.CHUNK
            d = haversine_km(lat[a:b, None], lng[a:b, None], self.lat[None, :], self.lng[None, :])
            part = np.argpartition(d, k - 1, axis=1)[:, :k]
            idx[a:b], dist[a:b] = part, np.take_along_axis(d, part, axis=1)
        return idx, dist

    def _combos(self, h_idx, h_d, wlat, wlng):
        w_idx, w_d = self.nearest(wlat, wlng)
        w_idx, w_d = w_idx[0], w_d[0]
        hi, wi = h_idx[:, :, None], w_idx[None, None, :]
        between = haversine_km(self.lat[hi], self.lng[hi], self.lat[wi], self.lng[wi])
        total = (walk_minutes(h_d)[:, :, None] + walk_minutes(w_d)[None, None, :]
                 + ride_minutes(between, self.line[hi], self.line[wi]))
        return total, w_idx

    def commute(self, lat, lng, wlat, wlng, home=None) -> np.ndarray:
        """집 좌표 배열 → 회사까지 추정 분. home=(idx, km) 를 주면 근접역 계산을 건너뛴다."""
        lat = np.atleast_1d(np.asarray(lat, dtype=float))
        lng = np.atleast_1d(np.asarray(lng, dtype=float))
        h_idx, h_d = home if home is not None else self.nearest(lat, lng)
        total, _ = self._combos(h_idx, h_d, wlat, wlng)
        best = total.reshape(len(lat), -1).min(axis=1)
        direct = haversine_km(lat, lng, wlat, wlng)
        walk = walk_minutes(direct)
        return np.where(direct <= WALK_ONLY_KM, np.minimum(best, walk), best)

    def route(self, lat: float, lng: float, wlat: float, wlng: float) -> dict:
        """한 단지의 추정 경로 설명 (리포트용)."""
        h_idx, h_d = self.nearest(lat, lng)
        total, w_idx = self._combos(h_idx, h_d, wlat, wlng)
        flat = int(np.argmin(total[0]))
        i, j = divmod(flat, total.shape[2])
        hs, ws = int(h_idx[0, i]), int(w_idx[j])
        minutes = float(total[0, i, j])
        direct = float(haversine_km(lat, lng, wlat, wlng))
        if direct <= WALK_ONLY_KM and walk_minutes(direct) < minutes:
            return {"minutes": round(float(walk_minutes(direct))), "source": "estimate",
                    "route": "도보"}
        a = f"{self.name[hs]}({self.line[hs]})"
        b = f"{self.name[ws]}({self.line[ws]})"
        return {"minutes": round(minutes), "source": "estimate",
                "route": a if hs == ws else f"{a} → {b}",
                "transfer": bool(self.line[hs] != self.line[ws])}


# ── 점수 곡선 ─────────────────────────────────────────────────────────
def budget_use_score(ratio):
    """예산의 75~100% 를 쓰면 만점, 40% 이하면 0. 너무 작은 집을 위로 올리지 않는다."""
    r = np.asarray(ratio, dtype=float)
    return np.clip((r - 0.40) / (0.75 - 0.40), 0, 1) * 100


def commute_limit(ans: "Answers") -> float | None:
    """하드 필터에 쓰는 실제 상한 (분). None 이면 거르지 않는다."""
    if ans.commute_max is None:
        return None
    return ans.commute_max + (0 if ans.commute_strict else COMMUTE_SLACK)


def commute_score(minutes, limit: float | None):
    """limit 은 commute_limit() 값. 20분 이하 만점, 상한에서 0."""
    m = np.asarray(minutes, dtype=float)
    end = COMMUTE_OPEN_END if limit is None else max(limit, COMMUTE_FULL + 5)
    return np.clip((end - m) / (end - COMMUTE_FULL), 0, 1) * 100


def norm_rank(s: pd.Series, higher_is_better: bool = True) -> pd.Series:
    """0~100 백분위 (꼴찌 0 · 1등 100). 결측은 0, 후보가 하나면 50."""
    r = s.rank(method="average", ascending=higher_is_better, na_option="keep")
    n = s.notna().sum()
    if n <= 1:
        return pd.Series(np.where(s.notna(), 50.0, 0.0), index=s.index)
    return ((r - 1) / (n - 1) * 100).fillna(0.0)


def add_rel_price(df: pd.DataFrame) -> pd.DataFrame:
    """같은 시군구 · 같은 평형에서 1년 평당가 백분위 (0=가장 낮다).

    run_step5 의 rel_value_pct 와 같은 정의다. **필터 전 전체 모집단**에서 잰다 —
    후보 안에서 재면 "같은 구 중 하위 N%" 라고 서술할 수 없다.
    """
    df = df.copy()
    ppy = df["ppy_1y"].fillna(df["last_ppy"]) if "ppy_1y" in df else df["last_ppy"]
    df["_ppy"] = ppy
    df["rel_price_pct"] = (
        df.groupby(["sigungu_code", "pyeong_bucket"])["_ppy"]
        .transform(lambda s: norm_rank(s, higher_is_better=True))
    )
    return df.drop(columns="_ppy")


def prepare(apt: pd.DataFrame, pyeong: pd.DataFrame) -> pd.DataFrame:
    """단지·평형 단위 후보 프레임."""
    keep = ["apt_id", "apt_name", "sigungu_code", "sigungu_name", "legal_dong_name",
            "road_address", "lat", "lng", "region", "build_year", "walk_min",
            "nearest_station", "nearest_line", "elem_school_cnt_1km", "park_dist",
            "green_score", "infra_score"]
    keep = [c for c in keep if c in apt.columns]
    a = apt[keep].assign(apt_trade_total=apt["trade_total"])
    df = pyeong.merge(a, on="apt_id", how="inner")
    return add_rel_price(df)


# ── 필터 · 점수 ───────────────────────────────────────────────────────
def hard_filter(df: pd.DataFrame, ans: Answers, today: date,
                skip: tuple[str, ...] = ()) -> pd.Series:
    m = df["lat"].notna() & df["lng"].notna()
    m &= df["trade_total"].fillna(0) >= MIN_TRADES
    if "apt_trade_total" in df:
        new = df["build_year"].fillna(0) >= today.year - NEW_BUILD_YEARS
        need = np.where(new, MIN_APT_TRADES_NEW, MIN_APT_TRADES)
        m &= df["apt_trade_total"].fillna(0) >= need
    cutoff = pd.Timestamp(today - timedelta(days=365 * STALE_YEARS))
    m &= pd.to_datetime(df["last_date"]) >= cutoff
    if ans.budget and "budget" not in skip:
        m &= df["last_price"] <= ans.budget
    if ans.pyeongs and "pyeong" not in skip:
        m &= df["pyeong_bucket"].isin(ans.pyeongs)
    if ans.sgg and "region" not in skip:
        m &= df["sigungu_code"].astype(str).isin(ans.sgg)
    lim = commute_limit(ans)
    if ans.work and "commute_min" in df and "commute" not in skip and lim is not None:
        m &= df["commute_min"] <= lim
        if ans.work2 and "commute2_min" in df:
            m &= df["commute2_min"] <= lim
    return m


def weights(ans: Answers) -> dict[str, float]:
    prios = ans.priorities or ["station"]
    w = {"price": W_PRICE}
    if ans.work:
        w["commute"] = W_COMMUTE
    for p in prios:
        w[p] = W_PRIORITY / len(prios)
    total = sum(w.values())
    return {k: v / total for k, v in w.items()}


def ramp(x, zero, full):
    """zero 에서 0, full 에서 100 인 선형 (방향은 두 값의 크기로 정해진다)."""
    x = np.asarray(x, dtype=float)
    return np.nan_to_num(np.clip((x - zero) / (full - zero), 0, 1) * 100, nan=0.0)


def priority_score(key: str, df: pd.DataFrame, today: date) -> np.ndarray:
    """고른 우선순위의 0~100 점수 — 절대 기준."""
    if key == "station":                              # 도보 5분 이내 만점, 20분이면 0
        return ramp(df["walk_min"], 20, 5)
    if key == "school":                               # 1km 안 초교 5곳이면 만점 (중앙값 4)
        return ramp(df["elem_school_cnt_1km"], 0, 5)
    if key == "new":                                  # 준공 5년 이내 만점, 25년 넘으면 0
        return ramp(df["build_year"], today.year - 25, today.year - 5)
    if key == "green":                                # 공원 거리와 녹지 점수 반반
        park = ramp(df["park_dist"], 800, 150) if "park_dist" in df else 50.0
        return 0.5 * park + 0.5 * np.nan_to_num(df["green_score"].to_numpy(float), nan=0.0)
    if key == "active":                               # 같은 평형 1년 12건이면 만점
        return ramp(df["trade_1y"], 0, 12)
    raise KeyError(key)


def score(df: pd.DataFrame, ans: Answers, today: date | None = None) -> pd.DataFrame:
    today = today or date.today()
    df = df.copy()
    w = weights(ans)
    if ans.budget:
        use = budget_use_score(df["last_price"] / ans.budget)
    else:
        use = np.full(len(df), 50.0)
    df["s_price"] = 0.5 * use + 0.5 * (100 - df["rel_price_pct"].fillna(50))
    if "commute" in w:
        lim = commute_limit(ans)
        s1 = commute_score(df["commute_min"], lim)
        if ans.work2 and "commute2_min" in df:
            s1 = (s1 + commute_score(df["commute2_min"], lim)) / 2
        df["s_commute"] = s1
    for p in w:
        if p in PRIORITIES:
            df[f"s_{p}"] = priority_score(p, df, today)
    raw = sum(df[f"s_{k}"] * v for k, v in w.items())
    conf = df["trade_1y"].fillna(0).astype(int).map(lambda t: CONFIDENCE.get(t, 1.0))
    df["confidence"] = conf.to_numpy()
    df["score"] = (raw * df["confidence"]).round(1)
    return df


def pick_top(df: pd.DataFrame, n: int = 5, dong_cap: int = 2) -> pd.DataFrame:
    """단지당 최고 평형 1행, 같은 법정동은 dong_cap 곳까지."""
    best = df.sort_values("score", ascending=False).drop_duplicates("apt_id")
    picked, per_dong = [], {}
    for idx, row in best.iterrows():
        key = (row.get("sigungu_code"), row.get("legal_dong_name"))
        if per_dong.get(key, 0) >= dong_cap:
            continue
        per_dong[key] = per_dong.get(key, 0) + 1
        picked.append(idx)
        if len(picked) >= n:
            break
    return best.loc[picked]


# ── 문구 ──────────────────────────────────────────────────────────────
def fmt_won(manwon: float) -> str:
    """만원 → '7억 4,000만' · '6,000만'."""
    v = int(round(float(manwon)))
    eok, man = divmod(abs(v), 10000)
    if eok and man:
        return f"{eok}억 {man:,}만"
    if eok:
        return f"{eok}억"
    return f"{man:,}만"


def reason_text(key: str, row: pd.Series, ans: Answers) -> str | None:
    if key == "price":
        pct = row.get("rel_price_pct")
        if pd.notna(pct) and pct <= 40:
            area_s = AREA_LABEL.get(row.get("pyeong_bucket"), "비슷한 면적")
            return f"같은 구 {area_s} 중 평당가 하위 {max(1, round(pct))}%"
        if ans.budget:
            gap = ans.budget - row["last_price"]
            return "예산과 거의 같은 가격" if gap < 500 else f"예산보다 {fmt_won(gap)} 아래"
        return None
    if key == "commute":
        t = f"출근 약 {round(row['commute_min'])}분"
        c2 = row.get("commute2_min")
        return t + f" · 함께 사는 분 {round(c2)}분" if c2 is not None and pd.notna(c2) else t
    if key == "station":
        wm = row.get("walk_min")
        st = row.get("nearest_station")
        st = norm_line(st) if isinstance(st, str) else st
        if pd.isna(wm):
            return None
        return f"{st}역 도보 {round(wm)}분" if isinstance(st, str) and st else f"역 도보 {round(wm)}분"
    if key == "school":
        c = row.get("elem_school_cnt_1km")
        return f"1km 안 초등학교 {int(c)}곳" if pd.notna(c) else None
    if key == "new":
        y = row.get("build_year")
        return f"{int(y)}년 준공" if pd.notna(y) else None
    if key == "green":
        d = row.get("park_dist")
        if pd.notna(d) and d < 50:
            return "단지 바로 옆 공원"
        if pd.notna(d) and d < 2000:
            return f"공원까지 약 {int(round(d, -1))}m"
        return "녹지 점수 상위권" if row.get("s_green", 0) >= 70 else None
    if key == "active":
        t = row.get("trade_1y")
        return f"최근 1년 거래 {int(t)}건" if pd.notna(t) else None
    return None


def reasons(row: pd.Series, ans: Answers, k: int = 3) -> list[str]:
    w = weights(ans)
    contrib = sorted(w, key=lambda key: row.get(f"s_{key}", 0) * w[key], reverse=True)
    out = []
    for key in contrib:
        t = reason_text(key, row, ans)
        if t:
            out.append(t)
        if len(out) >= k:
            break
    return out


# ── 전체 흐름 ─────────────────────────────────────────────────────────
ITEM_COLS = ["apt_id", "apt_name", "sigungu_name", "legal_dong_name", "road_address",
             "lat", "lng", "build_year", "pyeong_bucket", "area_m2", "last_price",
             "last_date", "last_ppy", "ppy_1y", "chg_1y", "vs_peak", "trade_1y",
             "walk_min", "nearest_station", "elem_school_cnt_1km", "rel_price_pct",
             "commute_min", "commute2_min", "confidence", "score"]


def with_commute(df: pd.DataFrame, ans: Answers, stations: Stations | None,
                 home: tuple[np.ndarray, np.ndarray] | None = None) -> pd.DataFrame:
    if not ans.work or stations is None:
        return df
    df = df.copy()
    lat, lng = df["lat"].to_numpy(), df["lng"].to_numpy()
    df["commute_min"] = stations.commute(lat, lng, *ans.work, home=home)
    if ans.work2:
        df["commute2_min"] = stations.commute(lat, lng, *ans.work2, home=home)
    return df


def count(df: pd.DataFrame, ans: Answers, today: date) -> int:
    return int(df.loc[hard_filter(df, ans, today), "apt_id"].nunique())


def run_match(df: pd.DataFrame, ans: Answers, today: date,
              stations: Stations | None, n: int = 5,
              home: tuple[np.ndarray, np.ndarray] | None = None) -> dict:
    """답변 → Top n. df 는 prepare() 산출물 (commute_min 은 여기서 붙인다)."""
    df = with_commute(df, ans, stations, home)
    if "commute_min" not in df:
        ans = replace(ans, work=None, work2=None)

    stages: list[tuple[str, Answers]] = [("", ans)]
    if ans.work and ans.commute_max is not None:
        stages.append(("commute", replace(stages[-1][1], commute_max=ans.commute_max + 15,
                                          commute_strict=False)))
    if ans.budget:
        stages.append(("budget", replace(stages[-1][1], budget=ans.budget * 1.1)))

    relaxed: list[str] = []
    eff, cand = ans, df.iloc[0:0]
    for name, a in stages:
        if name:
            relaxed.append(name)
        eff = a
        cand = df[hard_filter(df, a, today)]
        if cand["apt_id"].nunique() >= n:
            break

    result = {"count": int(cand["apt_id"].nunique()), "relaxed": relaxed,
              "weights": weights(eff), "items": [], "points": [],
              "effective": {"budget": eff.budget, "commute_max": eff.commute_max,
                            "commute_strict": eff.commute_strict}}
    if cand.empty:
        result["blocker"] = blocker(df, ans, today)
        return result

    scored = score(cand, eff, today)
    top = pick_top(scored, n=n)
    w = weights(eff)
    for rank, (_, row) in enumerate(top.iterrows(), 1):
        item = {c: row.get(c) for c in ITEM_COLS if c in row.index}
        item["rank"] = rank
        item["breakdown"] = {k: round(float(row[f"s_{k}"]), 1) for k in w}
        item["reasons"] = reasons(row, eff)
        if ans.work and stations is not None:
            item["commute"] = stations.route(row["lat"], row["lng"], *ans.work)
        if ans.work2 and stations is not None:
            item["commute2"] = stations.route(row["lat"], row["lng"], *ans.work2)
        result["items"].append(item)

    result["weak"] = weak_point(result["items"], w)

    pts = scored.sort_values("score", ascending=False).drop_duplicates("apt_id").head(300)
    result["points"] = pts[["apt_id", "lat", "lng", "score"]].to_dict(orient="records")
    return result


WEAK_SCORE = 65            # Top5 평균 적합도가 이보다 낮으면 무엇이 아쉬운지 알려 준다
WEAK_ITEM = 50


def weak_point(items: list[dict], w: dict[str, float]) -> dict | None:
    """Top5 가 전반적으로 덜 맞을 때, 평균 점수가 가장 낮은 조건 하나.

    30억 · 강남 · 신축처럼 동시에 만족하는 곳이 거의 없는 조합이면 적합도가 40점대로
    나오는데, 이유를 말하지 않으면 사용자는 순위를 믿지 못한다.
    """
    if not items or np.mean([it["score"] for it in items]) >= WEAK_SCORE:
        return None
    avg = {k: float(np.mean([it["breakdown"][k] for it in items])) for k in w}
    key = min(avg, key=avg.get)
    if avg[key] >= WEAK_ITEM:
        return None
    label = {"price": "가격", "commute": "출근 시간"}.get(key) or PRIORITIES[key][0]
    return {"key": key, "label": label, "avg": round(avg[key])}


def blocker(df: pd.DataFrame, ans: Answers, today: date) -> dict:
    """후보가 0곳일 때 어느 조건을 풀면 가장 많이 살아나는지."""
    labels = {"budget": "예산", "pyeong": "평형", "region": "지역", "commute": "통근 시간"}
    best = max(labels, key=lambda k: int(hard_filter(df, ans, today, skip=(k,)).sum()))
    alive = int(df.loc[hard_filter(df, ans, today, skip=(best,)), "apt_id"].nunique())
    return {"key": best, "label": labels[best], "count": alive}
