"""🏠 홈 — 오늘의 인사이트 (저평가 Top, 거래량 핫 시군구, KPI)."""
from __future__ import annotations
import streamlit as st
import pandas as pd
import plotly.express as px

from _data import (
    load_apt_master, load_unified_latest, load_undervalue_latest,
    load_new_trades_latest, attach_master, fmt_won, safe_int,
)
from _ui import inject_css, page_header, kpi_row, COLOR_PRIMARY, COLOR_ACCENT, PLOTLY_TEMPLATE

st.set_page_config(
    page_title="수도권 아파트 시세 인사이트",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

# ── 사이드바 ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        f"<h2 style='margin-top:0'>🏙️ Insight</h2>"
        f"<div style='color:#64748B;font-size:.85rem;margin-top:-.5rem'>수도권 아파트 시세 대시보드</div><hr/>",
        unsafe_allow_html=True,
    )
    region_filter = st.multiselect(
        "지역",
        options=["서울", "경기", "인천"],
        default=["서울", "경기", "인천"],
    )
    st.caption("지역 필터는 모든 페이지에서 공유됩니다.")
    st.session_state["region_filter"] = region_filter

# ── 데이터 로드 ────────────────────────────────────────────────
am = load_apt_master()
snap, latest = load_unified_latest()
uv, uv_date = load_undervalue_latest()
nt, nt_date = load_new_trades_latest()

if snap.empty:
    st.error("master 데이터가 비어있습니다. step3~4를 먼저 실행해 주세요.")
    st.stop()

snap = attach_master(snap, am)

# 지역 필터 적용
if region_filter:
    snap = snap[snap["region"].isin(region_filter)]
    if not uv.empty:
        uv = uv[uv["region"].isin(region_filter)]
    if not nt.empty and "sigungu_code" in nt.columns:
        nt = nt.assign(region=nt["sigungu_code"].astype(str).str[:2].map({"11": "서울", "28": "인천", "41": "경기"}))
        nt = nt[nt["region"].isin(region_filter)]

# ── 헤더 ───────────────────────────────────────────────────────
page_header(
    "수도권 아파트 시세 인사이트",
    f"기준일: {pd.Timestamp(latest).strftime('%Y년 %m월 %d일')} · 단지 정보 + 실거래 + 인프라 통합",
    icon="🏙️",
)

# ── KPI ────────────────────────────────────────────────────────
apt_count = snap["apt_id"].nunique()
trade_30d = int(snap["trade_30d_count"].fillna(0).sum())
valid_p = snap["trade_30d_avg_per_m2"].dropna()
avg_pyeong_price = float(valid_p.mean() * 3.3058) if len(valid_p) else 0.0
top_undervalue = len(uv) if not uv.empty else 0

kpi_row([
    ("📍 분석 단지", f"{apt_count:,}", "수도권 아파트 단지"),
    ("📊 30일 거래", f"{trade_30d:,}건", f"기준일: {pd.Timestamp(latest).strftime('%m/%d')}"),
    ("💰 평균 평단가", f"{avg_pyeong_price:,.0f}만", "30일 평균 (전체 단지)"),
    ("⭐ 저평가 후보", f"{top_undervalue}개", f"리포트: {uv_date}" if uv_date else "—"),
])

st.markdown("<br/>", unsafe_allow_html=True)

# ── 메인 — 2 컬럼 ──────────────────────────────────────────────
left, right = st.columns([1.4, 1.0], gap="large")

with left:
    st.markdown(f"### 🌟 이번 주 저평가 단지 TOP 10")
    st.caption("지역별 최적 가중치 모델로 산출 · 가격대비 입지·인프라가 좋은 단지 위주")

    if uv.empty:
        st.info("아직 저평가 리포트가 없습니다. `python run_step7_undervalue.py` 실행 후 새로고침.")
    else:
        # rank가 작은 것 중 상위 10개
        top10 = uv.sort_values(["model_score"], ascending=False).head(10).copy()
        for i, (_, r) in enumerate(top10.iterrows(), 1):
            lp = r.get("last_price")
            price_eok = float(lp) if pd.notna(lp) else 0.0
            eok = int(price_eok // 10000); rest = int(price_eok % 10000)
            price_str = f"{eok}억 {rest:,}만" if eok else f"{rest:,}만"
            per_pyeong = safe_int(r.get("price_per_pyeong"))
            station = r.get("nearest_station") or ""
            if isinstance(station, float) and pd.isna(station): station = ""
            walk = r.get("walk_min")
            walk_str = f"· {station} 도보 {int(walk)}분" if station and pd.notna(walk) and walk else ""
            score_v = r.get("model_score")
            score = float(score_v) if pd.notna(score_v) else 0.0
            reason = r.get("reason") or ""
            if isinstance(reason, float) and pd.isna(reason): reason = ""

            st.markdown(
                f"""
                <div style="border:1px solid #E2E8F0;border-radius:10px;padding:12px 14px;margin-bottom:8px;
                            display:flex;align-items:center;gap:14px">
                  <div style="font-size:1.1rem;font-weight:800;color:{COLOR_PRIMARY};
                              min-width:34px;height:34px;background:#DBEAFE;border-radius:8px;
                              display:flex;align-items:center;justify-content:center">{i}</div>
                  <div style="flex:1">
                    <div style="font-weight:700;font-size:1.0rem">{r['apt_name']} <span style="color:#64748B;font-weight:500;font-size:.85rem">· {r['sigungu_name']} · {r['pyeong_bucket']}</span></div>
                    <div style="color:#475569;font-size:.85rem;margin-top:2px">{reason} {walk_str}</div>
                  </div>
                  <div style="text-align:right">
                    <div style="font-weight:800;font-size:1.05rem;color:#0F172A">{price_str}</div>
                    <div style="color:#64748B;font-size:.8rem">평당 {per_pyeong:,}만 · 점수 {score:.0f}</div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

with right:
    st.markdown("### 🔥 거래량 급증 시군구")
    st.caption("최근 갱신분 기준 상위 10")

    if nt.empty:
        st.info("신규 거래 리포트가 없습니다.")
    else:
        nt_top = nt.sort_values("new_count", ascending=False).head(10).copy()
        nt_top = nt_top[["sigungu_name", "new_count", "avg_price"]]
        nt_top.columns = ["시군구", "신규거래", "평균가(만)"]
        nt_top["평균가(만)"] = nt_top["평균가(만)"].astype(int)

        fig = px.bar(
            nt_top.iloc[::-1],
            x="신규거래", y="시군구",
            orientation="h",
            text="신규거래",
        )
        fig.update_traces(marker_color=COLOR_PRIMARY, textposition="outside")
        fig.update_layout(
            **PLOTLY_TEMPLATE["layout"],
            height=420,
            showlegend=False,
            xaxis_title=None, yaxis_title=None,
        )
        st.plotly_chart(fig, use_container_width=True)

st.markdown("<br/>", unsafe_allow_html=True)

# ── 하단 — 시군구별 평균 평단가 ────────────────────────────────
st.markdown("### 📍 시군구별 평균 평단가 분포")
st.caption("30일 평균 거래가 기준")

sgg_summary = (
    snap.dropna(subset=["trade_30d_avg_per_m2"])
    .groupby(["region", "sigungu_name"], as_index=False)
    .agg(per_m2=("trade_30d_avg_per_m2", "mean"),
         trades=("trade_30d_count", "sum"))
)
sgg_summary["평단가(만원)"] = (sgg_summary["per_m2"] * 3.3058).round(0)
sgg_summary = sgg_summary[sgg_summary["trades"] > 0].sort_values("평단가(만원)", ascending=False)

fig2 = px.bar(
    sgg_summary,
    x="sigungu_name", y="평단가(만원)",
    color="region",
    color_discrete_map={"서울": COLOR_PRIMARY, "경기": COLOR_ACCENT, "인천": "#7C3AED"},
)
fig2.update_layout(
    **PLOTLY_TEMPLATE["layout"],
    xaxis_title=None, yaxis_title="평단가(만원)",
    legend_title=None,
    height=420,
)
fig2.update_xaxes(tickangle=-45)
st.plotly_chart(fig2, use_container_width=True)

# ── 푸터 ───────────────────────────────────────────────────────
st.markdown(
    f"""
    <hr style="margin-top:2rem"/>
    <div style="color:#94A3B8;font-size:.8rem;text-align:center">
      데이터 출처: 국토교통부 실거래가 · 공공데이터포털 K-apt · 행정안전부 행정코드 · 시도교육청 학교 위치<br/>
      이 대시보드는 투자 권유가 아니며 정보 제공 목적입니다.
    </div>
    """,
    unsafe_allow_html=True,
)
