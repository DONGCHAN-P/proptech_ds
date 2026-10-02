"""⭐ 관심 단지 — 즐겨찾기한 단지의 시세 변동 추적."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
import plotly.express as px

from _data import load_apt_master, load_unified_full, load_trade_events, attach_master, safe_int
from _ui import inject_css, page_header, COLOR_PRIMARY, PLOTLY_TEMPLATE

st.set_page_config(page_title="관심 단지", page_icon="⭐", layout="wide")
inject_css()
page_header("관심 단지", "관심 단지 등록 후 시세 변동을 한 화면에서 추적하세요", icon="⭐")

watchlist: set = st.session_state.setdefault("watchlist", set())

if not watchlist:
    st.info("아직 등록된 관심 단지가 없습니다. **단지 검색** 또는 **단지 상세** 페이지에서 추가해 보세요.")
    st.stop()

am = load_apt_master()
events = load_trade_events()
unified = load_unified_full()

picked_master = am[am["apt_id"].isin(watchlist)].copy()

# ── 카드 그리드 ────────────────────────────────────────────────
st.markdown(f"### 등록 단지 {len(watchlist)}개")
cols = st.columns(3, gap="small")
for i, (_, r) in enumerate(picked_master.iterrows()):
    apt_id = r["apt_id"]
    ev = events[events["apt_id"] == apt_id].sort_values("deal_date")
    last_price = ev.iloc[-1]["deal_amount"] if not ev.empty else None
    last_date = ev.iloc[-1]["deal_date"] if not ev.empty else None

    if not ev.empty and len(ev) >= 2:
        delta_pct = (ev.iloc[-1]["deal_amount"] / ev.iloc[-2]["deal_amount"] - 1) * 100
    else:
        delta_pct = None

    with cols[i % 3]:
        price_str = "—"
        if pd.notna(last_price):
            eok, rest = int(last_price // 10000), int(last_price % 10000)
            price_str = f"{eok}억 {rest:,}만" if eok else f"{rest:,}만"

        delta_html = ""
        if delta_pct is not None:
            color = "#16A34A" if delta_pct >= 0 else "#DC2626"
            arrow = "▲" if delta_pct >= 0 else "▼"
            delta_html = f"<span style='color:{color};font-size:.85rem;font-weight:600'>{arrow} {abs(delta_pct):.1f}% (직전 대비)</span>"

        nm = r.get("apt_name")
        nm = nm if (pd.notna(nm) and nm) else "—"
        sta = r.get("nearest_station") or ""
        if isinstance(sta, float) and pd.isna(sta): sta = ""
        infra_v = safe_int(r.get("infra_score"))

        st.markdown(
            f"""
            <div class='apt-card'>
              <div class='name'>{nm}</div>
              <div class='loc'>{sta} · 인프라 {infra_v}점</div>
              <div class='price'>{price_str}</div>
              <div class='meta'>{(last_date.strftime('%Y-%m-%d') if last_date is not None else '거래없음')} {delta_html}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button("상세", key=f"watch_d_{apt_id}", use_container_width=True):
                st.session_state["selected_apt_id"] = apt_id
                st.switch_page("pages/2_📊_단지_상세.py")
        with c2:
            if st.button("✕ 빼기", key=f"watch_x_{apt_id}", use_container_width=True):
                watchlist.discard(apt_id)
                st.rerun()

st.markdown("<hr/>", unsafe_allow_html=True)

# ── 비교 차트 ──────────────────────────────────────────────────
st.markdown("### 관심 단지 시세 비교 (월별 평균 평단가)")
ev_pick = events[events["apt_id"].isin(watchlist)].copy()
if ev_pick.empty:
    st.info("거래 이력이 없는 단지들입니다.")
else:
    ev_pick = ev_pick.merge(
        am[["apt_id", "apt_name"]].drop_duplicates(),
        on="apt_id", how="left",
    )
    ev_pick["yearmonth"] = ev_pick["deal_date"].dt.to_period("M").dt.to_timestamp()
    monthly = (
        ev_pick.groupby(["yearmonth", "apt_name"], as_index=False)
        .agg(per_pyeong=("price_per_pyeong", "mean"))
    )
    fig = px.line(monthly, x="yearmonth", y="per_pyeong", color="apt_name", markers=True)
    fig.update_layout(
        **PLOTLY_TEMPLATE["layout"],
        xaxis_title=None, yaxis_title="평단가(만원)",
        legend_title="단지",
        height=460,
    )
    st.plotly_chart(fig, use_container_width=True)

# ── 비우기 ─────────────────────────────────────────────────────
if st.button("⚠ 관심 단지 모두 비우기"):
    st.session_state["watchlist"] = set()
    st.rerun()
