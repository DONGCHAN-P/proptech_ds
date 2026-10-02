"""🔍 단지 검색 — 시군구·평형·가격대·인프라 필터 + 카드 + 지도."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
import pydeck as pdk

from _data import load_apt_master, load_unified_latest, attach_master, get_region_options, safe_int
from _ui import inject_css, page_header, COLOR_PRIMARY

st.set_page_config(page_title="단지 검색", page_icon="🔍", layout="wide")
inject_css()
page_header("단지 검색", "시군구·평형·가격대·인프라 점수로 좁혀서 찾기", icon="🔍")

# ── 데이터 ─────────────────────────────────────────────────────
am = load_apt_master()
snap, latest = load_unified_latest()
if snap.empty:
    st.error("master 데이터가 비어있습니다.")
    st.stop()

snap = attach_master(snap, am)

# 같은 단지×평형 중복 제거(최신 1개)
snap = (
    snap.sort_values("snapshot_date")
    .drop_duplicates(subset=["apt_id", "pyeong_bucket"], keep="last")
)

# ── 필터 (사이드바) ────────────────────────────────────────────
region_filter = st.session_state.get("region_filter", ["서울", "경기", "인천"])
opt = get_region_options(snap)
all_sgg: list[str] = []
for r in region_filter:
    all_sgg += opt.get(r, [])

with st.sidebar:
    st.markdown("## 필터")
    sel_sgg = st.multiselect("시군구", options=all_sgg, default=all_sgg[:3] if all_sgg else [])

    pyeong_options = sorted(snap["pyeong_bucket"].dropna().unique())
    sel_pyeong = st.multiselect("평형", options=pyeong_options, default=["20P", "25P", "30P"] if "25P" in pyeong_options else pyeong_options[:3])

    st.markdown("---")
    st.markdown("**가격 (만원, 최근거래)**")
    valid_price = snap["trade_last_price"].dropna()
    if len(valid_price):
        pmin, pmax = int(valid_price.quantile(0.05)), int(valid_price.quantile(0.95))
        price_range = st.slider(" ", min_value=pmin, max_value=pmax, value=(pmin, pmax), step=1000, label_visibility="collapsed")
    else:
        price_range = (0, 10**9)

    st.markdown("**인프라 점수 (0–100)**")
    infra_min = st.slider(" ", 0, 100, 0, label_visibility="collapsed")

    only_subway = st.checkbox("🚇 도보 10분 이내 역세권만", value=False)
    only_redv = st.checkbox("🏗 재개발 인접 단지만", value=False)

    st.markdown("---")
    sort_by = st.selectbox(
        "정렬",
        ["평단가 ↑ (저렴한 순)", "평단가 ↓ (비싼 순)", "최근 거래액 ↓", "30일 거래 많은 순", "인프라 점수 ↓"],
        index=0,
    )

# ── 필터 적용 ──────────────────────────────────────────────────
df = snap.copy()
if sel_sgg:
    df = df[df["sigungu_name"].isin(sel_sgg)]
if sel_pyeong:
    df = df[df["pyeong_bucket"].isin(sel_pyeong)]
df = df[df["trade_last_price"].between(price_range[0], price_range[1]) | df["trade_last_price"].isna()]
df = df[(df["infra_score"].fillna(0) >= infra_min)]
if only_subway:
    df = df[df["walk_min"].fillna(999) <= 10]
if only_redv:
    df = df[df["redv_nearby"].fillna(0) > 0]

# 평단가 컬럼
df = df.copy()
df["price_per_pyeong"] = df["trade_last_per_m2"] * 3.3058

# 정렬
sort_map = {
    "평단가 ↑ (저렴한 순)": ("price_per_pyeong", True),
    "평단가 ↓ (비싼 순)": ("price_per_pyeong", False),
    "최근 거래액 ↓": ("trade_last_price", False),
    "30일 거래 많은 순": ("trade_30d_count", False),
    "인프라 점수 ↓": ("infra_score", False),
}
sort_col, asc = sort_map[sort_by]
df = df.sort_values(sort_col, ascending=asc, na_position="last")

# ── 결과 카운트 ────────────────────────────────────────────────
st.markdown(
    f"<div style='color:#475569;margin-bottom:.5rem'>"
    f"검색 결과 <b style='color:{COLOR_PRIMARY}'>{len(df):,}</b>건"
    f"</div>",
    unsafe_allow_html=True,
)

# ── 지도 ───────────────────────────────────────────────────────
map_df = df.dropna(subset=["lat", "lng"]).head(500).copy()
if not map_df.empty:
    map_df["radius"] = 80
    map_df["price_label"] = map_df["trade_last_price"].apply(
        lambda x: f"{int(x//10000)}억" if pd.notna(x) and x > 10000 else (f"{int(x):,}만" if pd.notna(x) else "—")
    )
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_df,
        get_position=["lng", "lat"],
        get_radius="radius",
        get_fill_color=[30, 64, 175, 180],
        pickable=True,
        radius_min_pixels=4,
        radius_max_pixels=10,
    )
    view = pdk.ViewState(
        latitude=float(map_df["lat"].mean()),
        longitude=float(map_df["lng"].mean()),
        zoom=10,
    )
    st.pydeck_chart(
        pdk.Deck(
            layers=[layer],
            initial_view_state=view,
            tooltip={
                "html": "<b>{apt_name}</b><br/>{sigungu_name} · {pyeong_bucket}<br/>최근거래: {price_label}",
                "style": {"backgroundColor": "white", "color": "#0F172A"},
            },
            map_style=None,
        ),
        height=380,
    )

# ── 카드 그리드 ────────────────────────────────────────────────
st.markdown("### 단지 리스트")
PAGE_SIZE = 30
page = st.session_state.get("search_page", 0)
total_pages = max(1, (len(df) + PAGE_SIZE - 1) // PAGE_SIZE)
page = min(page, total_pages - 1)

start, end = page * PAGE_SIZE, (page + 1) * PAGE_SIZE
sliced = df.iloc[start:end]

cols = st.columns(3, gap="small")
for i, (_, r) in enumerate(sliced.iterrows()):
    col = cols[i % 3]
    with col:
        nm1 = r.get("apt_name")
        nm2 = r.get("apt_name_raw")
        name = nm1 if (pd.notna(nm1) and nm1) else (nm2 if (pd.notna(nm2) and nm2) else "—")
        last_price = r.get("trade_last_price")
        station = r.get("nearest_station") or ""
        walk = r.get("walk_min")
        infra = safe_int(r.get("infra_score"))
        redv = safe_int(r.get("redv_nearby"))
        per_pyeong_val = safe_int(r.get("price_per_pyeong"))

        price_str = "—"
        if pd.notna(last_price):
            eok, rest = int(last_price // 10000), int(last_price % 10000)
            price_str = f"{eok}억 {rest:,}만" if eok else f"{rest:,}만"

        badges = []
        if station and pd.notna(walk) and walk and walk <= 10:
            badges.append(f"<span class='badge badge-green'>🚇 도보{int(walk)}분</span>")
        if redv > 0:
            badges.append("<span class='badge badge-amber'>🏗 재개발인접</span>")
        if infra >= 60:
            badges.append("<span class='badge badge-blue'>인프라★</span>")

        st.markdown(
            f"""
            <div class='apt-card'>
              <div>{''.join(badges)}</div>
              <div class='name'>{name}</div>
              <div class='loc'>{r['sigungu_name']} · {r['pyeong_bucket']}{f" · {station}" if station else ""}</div>
              <div class='price'>{price_str}</div>
              <div class='meta'>평당 {per_pyeong_val:,}만 · 인프라 {infra}점</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("상세 보기", key=f"detail_{r['apt_id']}_{r['pyeong_bucket']}", use_container_width=True):
            st.session_state["selected_apt_id"] = r["apt_id"]
            st.session_state["selected_pyeong"] = r["pyeong_bucket"]
            st.switch_page("pages/2_📊_단지_상세.py")

# ── 페이지 네비게이션 ──────────────────────────────────────────
nav1, nav2, nav3 = st.columns([1, 2, 1])
with nav1:
    if st.button("◀ 이전", disabled=(page == 0), use_container_width=True):
        st.session_state["search_page"] = max(0, page - 1)
        st.rerun()
with nav2:
    st.markdown(
        f"<div style='text-align:center;color:#475569;padding-top:.5rem'>"
        f"{page + 1} / {total_pages} 페이지 · 총 {len(df):,}건</div>",
        unsafe_allow_html=True,
    )
with nav3:
    if st.button("다음 ▶", disabled=(page + 1 >= total_pages), use_container_width=True):
        st.session_state["search_page"] = min(total_pages - 1, page + 1)
        st.rerun()
