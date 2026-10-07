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
RIDE_KMH = 32.0           # 정차 포함 표정속도
RIDE_DETOUR = 1.3         # 역간 직선 → 선로
WAIT_MIN = 4.0
TRANSFER_MIN = 7.0
WALK_ONLY_KM = 1.5        # 이 안쪽이면 걸어가는 경우와 비교
K_NEAR = 3

COMMUTE_SLACK = 10        # 추정 오차만큼 허용시간에 여유
COMMUTE_FULL = 20         # 이 이하면 통근 점수 만점

# ── 점수 가중치 ───────────────────────────────────────────────────────
W_PRICE, W_COMMUTE, W_PRIORITY = 0.30, 0.25, 0.45
STALE_YEARS = 3
MIN_TRADES = 3            # 그 평형의 누적 거래 — 시세라고 부를 최소 표본
# 세대수가 없어(T6b) 단지 전체 누적 거래로 규모를 가린다. 나홀로 단지가 역 앞이라는
# 이유만으로 1위에 오르는 걸 막는다. 신축은 거래 기간이 짧아 기준을 낮춘다.
MIN_APT_TRADES = 50
MIN_APT_TRADES_NEW = 15
NEW_BUILD_YEARS = 5

# key → (라벨, 컬럼, 클수록 좋은가)
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

PYEONG_CODES = ["10P", "15P", "20P", "25P", "30P", "35P", "40P", "50P", "60P+"]


# ── 답변 ──────────────────────────────────────────────────────────────
@dataclass
class Answers:
    household: str = "couple"
    budget: float | None = None                  # 만원
    pyeongs: list[str] = field(default_factory=list)
    work: tuple[float, float] | None = None      # (lat, lng)
    commute_max: int = 45
    sgg: list[str] = field(default_factory=list)
    priorities: list[str] = field(default_factory=list)

    @classmethod
    def from_payload(cls, p: dict) -> "Answers":
        work = p.get("work")
        if isinstance(work, dict) and work.get("lat") is not None:
            work = (float(work["lat"]), float(work["lng"]))
        elif isinstance(work, (list, tuple)) and len(work) == 2:
            work = (float(work[0]), float(work[1]))
        else:
            work = None
        budget = p.get("budget")
        return cls(
            household=str(p.get("household") or "couple"),
            budget=float(budget) if budget else None,
            pyeongs=[x for x in (p.get("pyeongs") or []) if x in PYEONG_CODES],
            work=work,
            commute_max=int(p.get("commute_max") or 45),
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


def norm_line(line: str) -> str:
    """'9호선(연장)' · '신분당선(연장2)' · '7호선(인천)' 을 본선과 같은 노선으로 본다."""
    return re.sub(r"\(.*?\)", "", str(line)).strip()


def ride_minutes(km, line_a, line_b):
    km = np.asarray(km, dtype=float)
    a = np.vectorize(norm_line)(np.asarray(line_a, dtype=object))
    b = np.vectorize(norm_line)(np.asarray(line_b, dtype=object))
    return WAIT_MIN + km * RIDE_DETOUR / RIDE_KMH * 60 + np.where(a == b, 0.0, TRANSFER_MIN)


class Stations:
    """지하철역 좌표·노선. 통근 추정의 유일한 근거."""

    def __init__(self, df: pd.DataFrame):
        df = df.dropna(subset=["lat", "lng"]).reset_index(drop=True)
        self.df = df
        self.lat = df["lat"].to_numpy(float)
        self.lng = df["lng"].to_numpy(float)
        self.line = df["line"].map(norm_line).to_numpy(object)
        # '남한산성입구(성남법원.검찰청)' → '남한산성입구' (표시용)
        self.name = df["station_name"].map(norm_line).to_numpy(object)

    def nearest(self, lat, lng, k: int = K_NEAR) -> tuple[np.ndarray, np.ndarray]:
        """각 점의 가까운 역 k곳 (인덱스, km). 2만 점 × 800역 정도는 한 번에 된다."""
        lat = np.atleast_1d(np.asarray(lat, dtype=float))
        lng = np.atleast_1d(np.asarray(lng, dtype=float))
        k = min(k, len(self.lat))
        d = haversine_km(lat[:, None], lng[:, None], self.lat[None, :], self.lng[None, :])
        idx = np.argpartition(d, k - 1, axis=1)[:, :k]
        return idx, np.take_along_axis(d, idx, axis=1)

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


def commute_score(minutes, limit: int):
    m = np.asarray(minutes, dtype=float)
    end = limit + COMMUTE_SLACK
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
    if ans.work and "commute_min" in df and "commute" not in skip:
        m &= df["commute_min"] <= ans.commute_max + COMMUTE_SLACK
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


def score(df: pd.DataFrame, ans: Answers) -> pd.DataFrame:
    df = df.copy()
    w = weights(ans)
    if ans.budget:
        use = budget_use_score(df["last_price"] / ans.budget)
    else:
        use = np.full(len(df), 50.0)
    df["s_price"] = 0.5 * use + 0.5 * (100 - df["rel_price_pct"].fillna(50))
    if "commute" in w:
        df["s_commute"] = commute_score(df["commute_min"], ans.commute_max)
    for p in w:
        if p in PRIORITIES:
            _, col, higher = PRIORITIES[p]
            df[f"s_{p}"] = norm_rank(df[col], higher_is_better=higher).to_numpy()
    df["score"] = sum(df[f"s_{k}"] * v for k, v in w.items()).round(1)
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
            area = row.get("area_m2")
            area_s = f"{round(area)}㎡" if pd.notna(area) else "같은 평형"
            return f"같은 구 {area_s} 중 평당가 하위 {max(1, round(pct))}%"
        if ans.budget:
            gap = ans.budget - row["last_price"]
            return "예산과 거의 같은 가격" if gap < 500 else f"예산보다 {fmt_won(gap)} 아래"
        return None
    if key == "commute":
        return f"출근 약 {round(row['commute_min'])}분"
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
             "commute_min", "score"]


def with_commute(df: pd.DataFrame, ans: Answers, stations: Stations | None,
                 home: tuple[np.ndarray, np.ndarray] | None = None) -> pd.DataFrame:
    if not ans.work or stations is None:
        return df
    df = df.copy()
    df["commute_min"] = stations.commute(df["lat"].to_numpy(), df["lng"].to_numpy(),
                                         *ans.work, home=home)
    return df


def count(df: pd.DataFrame, ans: Answers, today: date) -> int:
    return int(df.loc[hard_filter(df, ans, today), "apt_id"].nunique())


def run_match(df: pd.DataFrame, ans: Answers, today: date,
              stations: Stations | None, n: int = 5,
              home: tuple[np.ndarray, np.ndarray] | None = None) -> dict:
    """답변 → Top n. df 는 prepare() 산출물 (commute_min 은 여기서 붙인다)."""
    df = with_commute(df, ans, stations, home)
    if "commute_min" not in df:
        ans = replace(ans, work=None)

    stages: list[tuple[str, Answers]] = [("", ans)]
    if ans.work:
        stages.append(("commute", replace(stages[-1][1], commute_max=ans.commute_max + 15)))
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
              "effective": {"budget": eff.budget, "commute_max": eff.commute_max}}
    if cand.empty:
        result["blocker"] = blocker(df, ans, today)
        return result

    scored = score(cand, eff)
    top = pick_top(scored, n=n)
    w = weights(eff)
    for rank, (_, row) in enumerate(top.iterrows(), 1):
        item = {c: row.get(c) for c in ITEM_COLS if c in row.index}
        item["rank"] = rank
        item["breakdown"] = {k: round(float(row[f"s_{k}"]), 1) for k in w}
        item["reasons"] = reasons(row, eff)
        if ans.work and stations is not None:
            item["commute"] = stations.route(row["lat"], row["lng"], *ans.work)
        result["items"].append(item)

    pts = scored.sort_values("score", ascending=False).drop_duplicates("apt_id").head(300)
    result["points"] = pts[["apt_id", "lat", "lng", "score"]].to_dict(orient="records")
    return result


def blocker(df: pd.DataFrame, ans: Answers, today: date) -> dict:
    """후보가 0곳일 때 어느 조건을 풀면 가장 많이 살아나는지."""
    labels = {"budget": "예산", "pyeong": "평형", "region": "지역", "commute": "통근 시간"}
    best = max(labels, key=lambda k: int(hard_filter(df, ans, today, skip=(k,)).sum()))
    alive = int(df.loc[hard_filter(df, ans, today, skip=(best,)), "apt_id"].nunique())
    return {"key": best, "label": labels[best], "count": alive}
