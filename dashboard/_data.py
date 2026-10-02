"""대시보드 데이터 로더 (캐싱 적용).

상위 프로젝트 루트의 master/, realestate.db, exports/ 를 읽어와
페이지별로 가공된 DataFrame을 반환한다.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
import streamlit as st

# ── 경로 ──────────────────────────────────────────────────────
BASE = Path(__file__).resolve().parent.parent  # C:\projects\realestate_reco
MASTER = BASE / "master"
DB_PATH = BASE / "realestate.db"
EXPORTS_DAILY = BASE / "exports" / "daily"

REGION_MAP = {"11": "서울", "28": "인천", "41": "경기"}

CACHE_TTL = 60 * 30  # 30분


# ── 기본 로더 ─────────────────────────────────────────────────
@st.cache_data(ttl=CACHE_TTL, show_spinner="단지 정보 로딩...")
def load_apt_master() -> pd.DataFrame:
    """apt_master + apt_external 조인 (sqlite)."""
    if not DB_PATH.exists():
        return pd.DataFrame()
    con = sqlite3.connect(DB_PATH)
    df = pd.read_sql(
        """
        SELECT m.apt_seq AS apt_id,
               m.apt_name,
               m.sigungu_code,
               m.lat, m.lng,
               e.nearest_station, e.walk_min, e.nearest_line, e.line_grade,
               e.elem_school_cnt_1km, e.nearest_school_dist,
               e.park_dist, e.river_dist, e.green_score,
               e.redv_nearby, e.redv_status_best,
               e.gtx_dist, e.gtx_line,
               e.commerce_score, e.hospital_cnt, e.infra_score
        FROM apt_master m
        LEFT JOIN apt_external e ON e.apt_seq = m.apt_seq
        """,
        con,
    )
    con.close()
    df["region"] = df["sigungu_code"].astype(str).str[:2].map(REGION_MAP)
    return df


@st.cache_data(ttl=CACHE_TTL, show_spinner="시세 스냅샷 로딩...")
def load_unified_latest() -> tuple[pd.DataFrame, pd.Timestamp]:
    """unified_apt_pyeong_daily 의 최신 스냅샷 1일치만."""
    p = MASTER / "unified_apt_pyeong_daily.parquet"
    if not p.exists():
        return pd.DataFrame(), pd.NaT
    df = pd.read_parquet(p)
    df["snapshot_date"] = pd.to_datetime(df["snapshot_date"])
    latest = df["snapshot_date"].max()
    snap = df[df["snapshot_date"] == latest].copy()
    snap["region"] = snap["sigungu_code"].astype(str).str[:2].map(REGION_MAP)
    return snap, latest


@st.cache_data(ttl=CACHE_TTL, show_spinner="시세 시계열 로딩...")
def load_unified_full() -> pd.DataFrame:
    """unified 전체 90일치 (차트용). 큰 파일이라 column 선택."""
    p = MASTER / "unified_apt_pyeong_daily.parquet"
    if not p.exists():
        return pd.DataFrame()
    cols = [
        "apt_id", "pyeong_bucket", "snapshot_date",
        "sigungu_code", "sigungu_name", "apt_name_raw",
        "trade_30d_count", "trade_30d_avg_price", "trade_30d_avg_per_m2",
        "trade_90d_count", "trade_90d_avg_price", "trade_90d_avg_per_m2",
        "trade_365d_count", "trade_365d_avg_price", "trade_365d_avg_per_m2",
        "trade_last_date", "trade_last_price", "trade_last_per_m2",
    ]
    df = pd.read_parquet(p, columns=cols)
    df["snapshot_date"] = pd.to_datetime(df["snapshot_date"])
    df["region"] = df["sigungu_code"].astype(str).str[:2].map(REGION_MAP)
    return df


@st.cache_data(ttl=CACHE_TTL, show_spinner="거래 이벤트 로딩...")
def load_trade_events() -> pd.DataFrame:
    p = MASTER / "trade_events.parquet"
    if not p.exists():
        return pd.DataFrame()
    df = pd.read_parquet(p)
    df["deal_date"] = pd.to_datetime(df["deal_date"])
    if "is_canceled" in df.columns:
        df = df[df["is_canceled"] == False].copy()
    df["region"] = df["sigungu_code"].astype(str).str[:2].map(REGION_MAP)
    return df


@st.cache_data(ttl=CACHE_TTL, show_spinner="추천 결과 로딩...")
def load_undervalue_latest() -> tuple[pd.DataFrame, str]:
    """가장 최근 undervalue_top5_*.csv 1건."""
    files = sorted(EXPORTS_DAILY.glob("undervalue_top5_*.csv"))
    if not files:
        return pd.DataFrame(), ""
    f = files[-1]
    df = pd.read_csv(f, encoding="utf-8-sig")
    return df, f.stem.replace("undervalue_top5_", "")


@st.cache_data(ttl=CACHE_TTL, show_spinner="신규 거래 로딩...")
def load_new_trades_latest() -> tuple[pd.DataFrame, str]:
    files = sorted(EXPORTS_DAILY.glob("new_trades_sgg_*.csv"))
    if not files:
        return pd.DataFrame(), ""
    f = files[-1]
    df = pd.read_csv(f, encoding="utf-8-sig")
    return df, f.stem.replace("new_trades_sgg_", "")


# ── 가공 헬퍼 ─────────────────────────────────────────────────
def attach_master(df: pd.DataFrame, am: pd.DataFrame) -> pd.DataFrame:
    """unified snapshot 에 apt_master(좌표/인프라) 붙이기."""
    if df.empty or am.empty:
        return df
    return df.merge(
        am[[
            "apt_id", "apt_name", "lat", "lng",
            "nearest_station", "walk_min", "nearest_line",
            "elem_school_cnt_1km", "redv_nearby", "redv_status_best",
            "commerce_score", "infra_score",
        ]],
        on="apt_id",
        how="left",
        suffixes=("", "_m"),
    )


def get_region_options(df: pd.DataFrame) -> dict:
    """시군구 옵션 dict {region: [sigungu_name, ...]}."""
    out: dict[str, list[str]] = {}
    if df.empty:
        return out
    for region in ["서울", "경기", "인천"]:
        sgg = sorted(df.loc[df["region"] == region, "sigungu_name"].dropna().unique())
        if sgg:
            out[region] = sgg
    return out


def kpi_summary(snap: pd.DataFrame) -> dict:
    """홈 KPI 카드용 요약."""
    if snap.empty:
        return dict(apt_count=0, trade_30d=0, avg_per_pyeong=0, latest="—")
    apt_count = snap["apt_id"].nunique()
    trade_30d = int(snap["trade_30d_count"].fillna(0).sum())
    valid_p = snap["trade_30d_avg_per_m2"].dropna()
    avg_per_pyeong = float(valid_p.mean() * 3.3058) if len(valid_p) else 0.0
    return dict(
        apt_count=apt_count,
        trade_30d=trade_30d,
        avg_per_pyeong=avg_per_pyeong,
    )


def lookup_trades(
    apt_id: str,
    apt_name_norm: str | None,
    sigungu_code: str | None,
    events: pd.DataFrame,
) -> tuple[pd.DataFrame, str]:
    """단지의 거래 이벤트를 다단계로 조회.

    1) apt_id 직접 매칭
    2) 실패 시 (sigungu_code, apt_name_norm) 매칭 — road_address 차이로
       apt_id 가 갈라진 경우를 회수
    3) 실패 시 (sigungu_code, apt_name_norm 부분일치) 매칭 — 정규화 차이까지 회수

    Returns: (matched_df, match_mode)  match_mode in {"id", "norm", "norm_partial", "none"}
    """
    if events.empty:
        return events, "none"

    direct = events[events["apt_id"] == apt_id]
    if not direct.empty:
        return direct, "id"

    if not apt_name_norm or not sigungu_code:
        return direct, "none"

    sgg = str(sigungu_code)
    same_sgg = events[events["sigungu_code"].astype(str) == sgg]
    if same_sgg.empty:
        return same_sgg, "none"

    # 정확한 정규화명 매칭
    if "apt_name_norm" in same_sgg.columns:
        exact = same_sgg[same_sgg["apt_name_norm"] == apt_name_norm]
        if not exact.empty:
            return exact, "norm"

    # 부분 일치 (3자 이상 공통 substring)
    target = "".join(str(apt_name_norm).split()).lower()
    if len(target) < 3:
        return pd.DataFrame(), "none"

    def _hit(raw):
        if not isinstance(raw, str):
            return False
        s = "".join(raw.split()).lower()
        return target in s or s in target

    name_col = "apt_name_norm" if "apt_name_norm" in same_sgg.columns else "apt_name_raw"
    partial = same_sgg[same_sgg[name_col].map(_hit)]
    if not partial.empty:
        return partial, "norm_partial"

    return pd.DataFrame(), "none"


@st.cache_data(ttl=CACHE_TTL, show_spinner="거래 건수 집계...")
def load_apt_trade_counts() -> pd.DataFrame:
    """단지별 trade_events 건수 (dropdown 정렬·표시용).
    apt_id 직접 + (sigungu_code, apt_name_norm) 두 방식 모두 집계.
    """
    p = MASTER / "trade_events.parquet"
    if not p.exists():
        return pd.DataFrame(columns=["apt_id", "trade_count"])
    cols = ["apt_id", "sigungu_code", "apt_name_norm", "is_canceled"]
    df = pd.read_parquet(p, columns=cols)
    if "is_canceled" in df.columns:
        df = df[df["is_canceled"] == False]
    by_id = df.groupby("apt_id").size().reset_index(name="trade_count")
    return by_id


@st.cache_data(ttl=CACHE_TTL, show_spinner="거래 건수 집계...")
def load_trade_counts_by_name() -> pd.DataFrame:
    """(sigungu_code, apt_name_norm) 별 거래 건수.
    sqlite apt_master ↔ trade_events 사이의 apt_id 갈라짐 보정용.
    """
    p = MASTER / "trade_events.parquet"
    if not p.exists():
        return pd.DataFrame(columns=["sigungu_code", "apt_name_norm", "trade_count_by_name"])
    df = pd.read_parquet(p, columns=["sigungu_code", "apt_name_norm", "is_canceled"])
    if "is_canceled" in df.columns:
        df = df[df["is_canceled"] == False]
    df["sigungu_code"] = df["sigungu_code"].astype(str)
    return (
        df.groupby(["sigungu_code", "apt_name_norm"])
        .size()
        .reset_index(name="trade_count_by_name")
    )


def find_similar_apts_with_trades(
    target_name: str,
    sigungu_code: str,
    events: pd.DataFrame,
    top: int = 8,
) -> pd.DataFrame:
    """직접 apt_id 매칭이 실패했을 때, 같은 시군구의 trade_events에서
    이름이 일부라도 겹치는 단지를 점수순으로 찾아 반환.
    columns: apt_id, apt_name_raw, trade_count, similarity
    """
    if not target_name or events.empty:
        return pd.DataFrame()
    sgg = str(sigungu_code) if sigungu_code is not None else ""
    if not sgg:
        return pd.DataFrame()

    norm_target = "".join(str(target_name).split()).lower()
    if not norm_target:
        return pd.DataFrame()

    same = events[events["sigungu_code"].astype(str) == sgg].copy()
    if same.empty:
        return pd.DataFrame()

    # apt 별 대표 raw 이름 + 거래수
    grp = (
        same.groupby("apt_id")
        .agg(apt_name_raw=("apt_name_raw", "first"),
             trade_count=("apt_name_raw", "size"))
        .reset_index()
    )

    def _sim(raw: str) -> float:
        if not isinstance(raw, str):
            return 0.0
        a = "".join(raw.split()).lower()
        if not a:
            return 0.0
        # 가장 긴 공통 substring 길이 비율 — 부분 일치에 강함
        best = 0
        # short scan: 3+자 윈도우
        for L in range(min(len(a), len(norm_target)), 2, -1):
            for i in range(len(norm_target) - L + 1):
                if norm_target[i:i + L] in a:
                    best = L
                    break
            if best:
                break
        return best / max(len(norm_target), 1)

    grp["similarity"] = grp["apt_name_raw"].map(_sim)
    grp = grp[grp["similarity"] > 0.4].sort_values(
        ["similarity", "trade_count"], ascending=[False, False]
    ).head(top)
    return grp.reset_index(drop=True)


def safe_int(v, default: int = 0) -> int:
    """NaN / None / 빈 문자열을 기본값으로 처리하면서 int 변환."""
    try:
        if v is None:
            return default
        if isinstance(v, float) and pd.isna(v):
            return default
        if isinstance(v, str) and not v.strip():
            return default
        return int(v)
    except (TypeError, ValueError):
        return default


def fmt_won(amount_eok: float) -> str:
    """만원 단위 → '12억 3,400만' 포맷."""
    if pd.isna(amount_eok) or amount_eok == 0:
        return "—"
    eok = int(amount_eok // 10000)
    rest = int(amount_eok % 10000)
    if eok > 0 and rest > 0:
        return f"{eok}억 {rest:,}만"
    if eok > 0:
        return f"{eok}억"
    return f"{rest:,}만"
