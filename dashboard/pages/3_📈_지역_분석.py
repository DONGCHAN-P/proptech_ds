"""📈 지역 분석 — 시군구별 평균가/거래량/모멘텀 비교."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from _data import load_unified_full, load_unified_latest, load_apt_master, attach_master
from _ui import inject_css, page_header, COLOR_PRIMARY, COLOR_ACCENT, PLOTLY_TEMPLATE

st.set_page_config(page_title="지역 분석", page_icon="📈", layout="wide")
inject_css()
page_header("지역 분석", "시군구별 평균가·거래량·모멘텀 비교", icon="📈")

# ── 데이터 ────────────────────────────────────────────────────
am = load_apt_master()
snap, latest = load_unified_latest()
full = load_unified_full()

if snap.empty:
    st.error("데이터가 비어있습니다.")
    st.stop()

snap = attach_master(snap, am)
region_filter = st.session_state.get("region_filter", ["서울", "경기", "인천"])
snap = snap[snap["region"].isin(region_filter)]
full = full[full["region"].isin(region_filter)]

# ── 시군구별 핵심 지표 ─────────────────────────────────────────
sgg_summary = (
    snap.dropna(subset=["trade_30d_avg_per_m2"])
    .groupby(["region", "sigungu_name"], as_index=False)
    .agg(
        per_m2=("trade_30d_avg_per_m2", "mean"),
        avg_30d_price=("trade_30d_avg_price", "mean"),
        avg_90d_price=("trade_90d_avg_price", "mean"),
        avg_365d_price=("trade_365d_avg_price", "mean"),
        trades_30d=("trade_30d_count", "sum"),
        trades_90d=("trade_90d_count", "sum"),
        apt_count=("apt_id", "nunique"),
    )
)
sgg_summary = sgg_summary[sgg_summary["trades_30d"] > 0].copy()
sgg_summary["평단가(만원)"] = (sgg_summary["per_m2"] * 3.3058).round(0)
# 모멘텀: 30d / 90d - 1
sgg_summary["모멘텀_30v90"] = (sgg_summary["avg_30d_price"] / sgg_summary["avg_90d_price"] - 1) * 100
sgg_summary["모멘텀_90v365"] = (sgg_summary["avg_90d_price"] / sgg_summary["avg_365d_price"] - 1) * 100

# ── 1) 시군구별 평단가 ────────────────────────────────────────
st.markdown("### 시군구별 평균 평단가 (만원)")
sorted_df = sgg_summary.sort_values("평단가(만원)", ascending=False)
fig1 = px.bar(
    sorted_df,
    x="sigungu_name", y="평단가(만원)",
    color="region",
    color_discrete_map={"서울": COLOR_PRIMARY, "경기": COLOR_ACCENT, "인천": "#7C3AED"},
    text="평단가(만원)",
)
fig1.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
fig1.update_layout(**PLOTLY_TEMPLATE["layout"], xaxis_title=None, yaxis_title="평단가(만원)", height=480, legend_title=None)
fig1.update_xaxes(tickangle=-45)
st.plotly_chart(fig1, use_container_width=True)

st.markdown("<br/>", unsafe_allow_html=True)

# ── 2) 모멘텀 산점도 ──────────────────────────────────────────
left, right = st.columns([1, 1])

with left:
    st.markdown("### 모멘텀 산점도")
    st.caption("X축: 30일 vs 90일 변화율 · Y축: 90일 vs 365일 변화율 (1사분면 = 단·장기 모두 상승)")
    fig2 = px.scatter(
        sgg_summary, x="모멘텀_30v90", y="모멘텀_90v365",
        size="trades_30d", color="region",
        color_discrete_map={"서울": COLOR_PRIMARY, "경기": COLOR_ACCENT, "인천": "#7C3AED"},
        hover_name="sigungu_name",
        size_max=40,
    )
    fig2.add_vline(x=0, line_color="#94A3B8", line_dash="dash")
    fig2.add_hline(y=0, line_color="#94A3B8", line_dash="dash")
    fig2.update_layout(
        **PLOTLY_TEMPLATE["layout"],
        xaxis_title="단기 모멘텀 (%)",
        yaxis_title="중기 모멘텀 (%)",
        height=480, legend_title=None,
    )
    st.plotly_chart(fig2, use_container_width=True)

with right:
    st.markdown("### 30일 거래 빈도 TOP")
    top_trade = sgg_summary.sort_values("trades_30d", ascending=False).head(15)
    fig3 = px.bar(
        top_trade.iloc[::-1],
        x="trades_30d", y="sigungu_name",
        orientation="h", text="trades_30d",
        color="region",
        color_discrete_map={"서울": COLOR_PRIMARY, "경기": COLOR_ACCENT, "인천": "#7C3AED"},
    )
    fig3.update_traces(textposition="outside")
    fig3.update_layout(
        **PLOTLY_TEMPLATE["layout"],
        xaxis_title="30일 거래수", yaxis_title=None, height=480, legend_title=None,
    )
    st.plotly_chart(fig3, use_container_width=True)

st.markdown("<br/>", unsafe_allow_html=True)

# ── 3) 시계열: 시군구별 평균 평단가 추이 (최근 90일) ──────────
st.markdown("### 시군구별 평균 평단가 추이 (최근 90일)")
sgg_select = st.multiselect(
    "비교할 시군구를 선택하세요 (최대 8개 권장)",
    options=sorted(snap["sigungu_name"].dropna().unique()),
    default=sgg_summary.sort_values("평단가(만원)", ascending=False).head(5)["sigungu_name"].tolist(),
)

if sgg_select and not full.empty:
    f = full[full["sigungu_name"].isin(sgg_select)].copy()
    f["per_pyeong"] = f["trade_30d_avg_per_m2"] * 3.3058
    daily = (
        f.dropna(subset=["per_pyeong"])
        .groupby(["snapshot_date", "sigungu_name"], as_index=False)["per_pyeong"]
        .mean()
    )
    fig4 = px.line(daily, x="snapshot_date", y="per_pyeong", color="sigungu_name", markers=False)
    fig4.update_layout(
        **PLOTLY_TEMPLATE["layout"],
        xaxis_title=None, yaxis_title="평단가(만원)",
        height=420, legend_title="시군구",
    )
    st.plotly_chart(fig4, use_container_width=True)
else:
    st.info("시군구를 선택하세요.")

# ── 4) 표 ────────────────────────────────────────────────────
with st.expander("📋 전체 시군구 표로 보기"):
    show = sgg_summary[["region", "sigungu_name", "apt_count", "trades_30d",
                        "평단가(만원)", "모멘텀_30v90", "모멘텀_90v365"]].copy()
    show.columns = ["권역", "시군구", "단지수", "30일 거래", "평단가(만원)", "단기 모멘텀(%)", "중기 모멘텀(%)"]
    show["평단가(만원)"] = show["평단가(만원)"].astype(int)
    show["단기 모멘텀(%)"] = show["단기 모멘텀(%)"].round(2)
    show["중기 모멘텀(%)"] = show["중기 모멘텀(%)"].round(2)
    st.dataframe(show.sort_values("평단가(만원)", ascending=False),
                 use_container_width=True, hide_index=True, height=520)
