"""📊 단지 상세 — 시세 추이, 거래 내역, 평형 비교, 주변 인프라."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk

from _data import (
    load_apt_master, load_unified_full, load_trade_events, attach_master, safe_int,
    load_apt_trade_counts, load_trade_counts_by_name,
    find_similar_apts_with_trades, lookup_trades,
)
from _ui import inject_css, page_header, COLOR_PRIMARY, COLOR_ACCENT, COLOR_WARNING, PLOTLY_TEMPLATE

st.set_page_config(page_title="단지 상세", page_icon="📊", layout="wide")
inject_css()

# ── 단지 선택 ──────────────────────────────────────────────────
am = load_apt_master()
events = load_trade_events()
unified = load_unified_full()
trade_counts = load_apt_trade_counts()
trade_counts_by_name = load_trade_counts_by_name()

if am.empty or events.empty:
    st.error("master 데이터가 비어있습니다.")
    st.stop()

# 거래 건수 머지 — 두 방식 모두 시도
am = am.merge(trade_counts, on="apt_id", how="left")
am["sigungu_code"] = am["sigungu_code"].astype(str)
am = am.merge(
    trade_counts_by_name.rename(columns={"apt_name_norm": "apt_name"}),
    on=["sigungu_code", "apt_name"],
    how="left",
)
am["trade_count"] = am["trade_count"].fillna(0).astype(int)
am["trade_count_by_name"] = am["trade_count_by_name"].fillna(0).astype(int)
# 효과적 건수 = 둘 중 큰 값 (fallback 매칭으로 회수될 거래 포함)
am["trade_count_eff"] = am[["trade_count", "trade_count_by_name"]].max(axis=1).astype(int)

# 사이드바: 단지 선택 (검색)
with st.sidebar:
    st.markdown("## 단지 선택")
    region_filter = st.session_state.get("region_filter", ["서울", "경기", "인천"])
    pre_apt = st.session_state.get("selected_apt_id")

    am_f = am[am["region"].isin(region_filter)] if region_filter else am
    name_query = st.text_input("단지명 검색", value="")
    only_with_trades = st.checkbox("📊 거래 이력 있는 단지만", value=True,
                                   help="끄면 거래가 0건인 단지도 검색됨")

    if name_query:
        candidates = am_f[am_f["apt_name"].str.contains(name_query, case=False, na=False)]
    else:
        candidates = am_f

    if only_with_trades:
        candidates = candidates[candidates["trade_count_eff"] > 0]

    # 효과적 거래 건수 많은 순으로 정렬
    candidates = (
        candidates.dropna(subset=["apt_name"])
        .sort_values("trade_count_eff", ascending=False)
        .head(300)
    )
    options = candidates["apt_id"].tolist()

    def _label(apt_id: str) -> str:
        row = candidates[candidates["apt_id"] == apt_id].iloc[0]
        n = int(row["trade_count_eff"])
        sgg = str(row["sigungu_code"])
        suffix = f"거래 {n}" if n > 0 else "거래 없음"
        return f"{row['apt_name']} · {sgg} ({suffix})"

    if not options:
        st.info("검색 결과 없음 — '거래 이력 있는 단지만' 체크 해제하거나 다른 단지명을 시도해 보세요.")
        st.stop()

    default_idx = options.index(pre_apt) if pre_apt in options else 0
    selected_apt = st.selectbox(
        "단지",
        options=options,
        format_func=_label,
        index=default_idx,
    )

# 선택된 단지 정보
apt_row = am[am["apt_id"] == selected_apt].iloc[0]
apt_name = apt_row["apt_name"]
sgg_code = apt_row["sigungu_code"]

# 다단계 거래 매칭: apt_id → (sgg, apt_name_norm) → (sgg, 부분일치)
ev, match_mode = lookup_trades(selected_apt, apt_name, sgg_code, events)
ev = ev.copy()

# unified는 apt_id 기준 (있으면 사용)
uni = unified[unified["apt_id"] == selected_apt].copy() if not unified.empty else pd.DataFrame()

# 거래에서 추출한 sgg 이름이 더 정확하므로 우선
sgg_name = ev["sigungu_name"].iloc[0] if not ev.empty else ""

page_header(apt_name or "—", f"{sgg_name} · 단지 ID {selected_apt[:8]}…", icon="📊")

# 매칭 모드 안내
if match_mode == "norm":
    st.info(
        f"💡 이 단지는 RTMS에서 도로주소가 거래마다 다르게 기록돼 "
        f"여러 apt_id로 분산돼 있었어요. **단지명+시군구로 매칭**해 거래 {len(ev):,}건을 찾았습니다."
    )
elif match_mode == "norm_partial":
    st.warning(
        f"⚠ 정확히 같은 이름의 거래가 없어 **부분일치(같은 시군구)** 로 매칭했습니다. "
        f"{len(ev):,}건이 묶여 있는데, 다른 단지가 섞여 있을 수 있어요. 거래 내역을 확인해 주세요."
    )

# ── KPI ────────────────────────────────────────────────────────
total_trades = len(ev)
recent_30d_trades = len(ev[ev["deal_date"] >= ev["deal_date"].max() - pd.Timedelta(days=30)]) if total_trades else 0
last_price = ev.sort_values("deal_date").iloc[-1]["deal_amount"] if total_trades else 0
last_per_pyeong = (ev.sort_values("deal_date").iloc[-1]["price_per_m2"] * 3.3058) if total_trades else 0
last_date = ev["deal_date"].max() if total_trades else None
infra = safe_int(apt_row.get("infra_score"))
station = apt_row.get("nearest_station") or "—"
if isinstance(station, float) and pd.isna(station):
    station = "—"
walk = apt_row.get("walk_min")

eok = safe_int(last_price // 10000) if pd.notna(last_price) else 0
rest = safe_int(last_price % 10000) if pd.notna(last_price) else 0
price_str = f"{eok}억 {rest:,}만" if eok else (f"{rest:,}만" if rest else "—")

last_per_pyeong_int = safe_int(last_per_pyeong)

c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("최근 거래", price_str, f"{last_date.strftime('%Y.%m.%d')}" if last_date else "—")
with c2: st.metric("최근 평단가", f"{last_per_pyeong_int:,}만" if last_per_pyeong_int else "—", "")
with c3: st.metric("총 거래", f"{total_trades:,}건", f"30일 {recent_30d_trades}건")
with c4: st.metric("인프라 점수", f"{infra} / 100", f"{station} 도보 {int(walk)}분" if pd.notna(walk) else station)

st.markdown("<br/>", unsafe_allow_html=True)

# ── 탭 ────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📈 시세 추이", "📋 거래 내역", "🏠 평형별 시세", "📍 주변 인프라"])

with tab1:
    st.markdown("##### 월별 평균 평단가")
    if ev.empty:
        st.info("거래 데이터가 없습니다.")
    else:
        ev["yearmonth"] = ev["deal_date"].dt.to_period("M").dt.to_timestamp()
        monthly = (
            ev.groupby(["yearmonth", "pyeong_bucket"], as_index=False)
            .agg(avg_per_pyeong=("price_per_pyeong", "mean"),
                 trades=("deal_amount", "count"))
        )
        if monthly.empty:
            st.info("표시할 데이터가 부족합니다.")
        else:
            fig = px.line(
                monthly, x="yearmonth", y="avg_per_pyeong",
                color="pyeong_bucket", markers=True,
            )
            fig.update_layout(
                **PLOTLY_TEMPLATE["layout"],
                xaxis_title=None, yaxis_title="평단가 (만원)",
                legend_title="평형",
                height=440,
            )
            st.plotly_chart(fig, use_container_width=True)

        # 거래 빈도 막대
        st.markdown("##### 월별 거래 건수")
        monthly_count = ev.groupby("yearmonth", as_index=False).agg(cnt=("deal_amount", "count"))
        figc = px.bar(monthly_count, x="yearmonth", y="cnt")
        figc.update_traces(marker_color=COLOR_ACCENT)
        figc.update_layout(**PLOTLY_TEMPLATE["layout"], xaxis_title=None, yaxis_title="건수", height=240)
        st.plotly_chart(figc, use_container_width=True)

with tab2:
    st.markdown("##### 최근 거래 50건")
    if ev.empty:
        st.info(
            "이 단지의 apt_id로 매칭된 RTMS 실거래 데이터가 없습니다.\n\n"
            "K-apt(단지정보)와 RTMS(실거래)는 단지명 정규화 차이로 같은 단지가 "
            "다른 ID로 떨어지는 경우가 있어요. 같은 시군구에서 이름이 비슷한 거래 이력 단지를 찾아봤습니다."
        )

        # ── Fallback: 같은 시군구에서 비슷한 이름의 거래 이력 단지 찾기 ──
        sig_code = apt_row.get("sigungu_code")
        target_name = apt_row.get("apt_name") or ""
        candidates = find_similar_apts_with_trades(target_name, sig_code, events, top=8)

        if candidates.empty:
            st.warning(f"시군구 코드 {sig_code} 내에 이름이 비슷한 거래 이력 단지를 찾지 못했습니다.")
        else:
            st.markdown("##### 🔎 이 단지가 아닐까요?")
            st.caption(f"같은 시군구({sig_code}) RTMS 거래 이력 중 이름이 비슷한 단지 {len(candidates)}개")
            for i, (_, c) in enumerate(candidates.iterrows()):
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(
                        f"<div style='padding:8px 0'>"
                        f"<b>{c['apt_name_raw']}</b> "
                        f"<span style='color:#64748B;font-size:.85rem'>· 거래 {int(c['trade_count'])}건 · 일치도 {c['similarity']*100:.0f}%</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                with col2:
                    st.caption(f"ID {c['apt_id'][:8]}…")
                with col3:
                    if st.button("이 단지로 이동", key=f"sw_{c['apt_id']}", use_container_width=True):
                        st.session_state["selected_apt_id"] = c["apt_id"]
                        st.rerun()
    else:
        show = ev.sort_values("deal_date", ascending=False).head(50)[
            ["deal_date", "pyeong_bucket", "area_m2", "floor", "deal_amount", "price_per_pyeong", "build_year"]
        ].copy()
        show.columns = ["거래일", "평형", "전용면적(㎡)", "층", "거래액(만원)", "평단가(만원)", "준공년"]
        show["거래일"] = show["거래일"].dt.strftime("%Y-%m-%d")
        show["거래액(만원)"] = show["거래액(만원)"].astype(int).map(lambda x: f"{x:,}")
        show["평단가(만원)"] = show["평단가(만원)"].fillna(0).astype(int).map(lambda x: f"{x:,}")
        show["전용면적(㎡)"] = show["전용면적(㎡)"].round(1)
        st.dataframe(show, use_container_width=True, hide_index=True, height=480)

with tab3:
    st.markdown("##### 평형별 거래 분포 (최근 1년)")
    if ev.empty:
        st.info("거래 데이터가 없습니다.")
    else:
        recent = ev[ev["deal_date"] >= ev["deal_date"].max() - pd.Timedelta(days=365)]
        if recent.empty:
            recent = ev
        py = recent.groupby("pyeong_bucket", as_index=False).agg(
            avg_price=("deal_amount", "mean"),
            avg_per_pyeong=("price_per_pyeong", "mean"),
            trades=("deal_amount", "count"),
        ).sort_values("pyeong_bucket")

        l, r = st.columns(2)
        with l:
            fig1 = px.bar(py, x="pyeong_bucket", y="avg_price", text="avg_price")
            fig1.update_traces(marker_color=COLOR_PRIMARY,
                               texttemplate="%{text:,.0f}만")
            fig1.update_layout(**PLOTLY_TEMPLATE["layout"], xaxis_title="평형", yaxis_title="평균 거래액(만)", height=380)
            st.plotly_chart(fig1, use_container_width=True)
        with r:
            fig2 = px.bar(py, x="pyeong_bucket", y="trades", text="trades")
            fig2.update_traces(marker_color=COLOR_ACCENT)
            fig2.update_layout(**PLOTLY_TEMPLATE["layout"], xaxis_title="평형", yaxis_title="거래 건수", height=380)
            st.plotly_chart(fig2, use_container_width=True)

with tab4:
    l, r = st.columns([1, 1])
    with l:
        st.markdown("##### 인프라 정보")
        def _safe_str(v, default="—"):
            if v is None: return default
            if isinstance(v, float) and pd.isna(v): return default
            s = str(v).strip()
            return s if s else default

        nearest_line = _safe_str(apt_row.get("nearest_line"), "")
        walk_min_v = apt_row.get("walk_min")
        gtx_line = _safe_str(apt_row.get("gtx_line"), "—")
        gtx_dist = apt_row.get("gtx_dist")
        elem_cnt = safe_int(apt_row.get("elem_school_cnt_1km"))
        school_dist = apt_row.get("nearest_school_dist")
        park_dist = apt_row.get("park_dist")
        green_score = apt_row.get("green_score") or 0
        if isinstance(green_score, float) and pd.isna(green_score): green_score = 0
        redv_n = safe_int(apt_row.get("redv_nearby"))
        redv_status = _safe_str(apt_row.get("redv_status_best"), "")
        hospital_cnt = safe_int(apt_row.get("hospital_cnt"))
        commerce_score = apt_row.get("commerce_score") or 0
        if isinstance(commerce_score, float) and pd.isna(commerce_score): commerce_score = 0
        infra_score = apt_row.get("infra_score") or 0
        if isinstance(infra_score, float) and pd.isna(infra_score): infra_score = 0

        rows = [
            ("🚇 가장 가까운 역", _safe_str(apt_row.get("nearest_station")),
             f"{nearest_line} · 도보 {int(walk_min_v)}분" if pd.notna(walk_min_v) else ""),
            ("🚄 GTX", gtx_line,
             f"{int(gtx_dist)}m" if pd.notna(gtx_dist) and gtx_dist else ""),
            ("🏫 1km 내 초등학교", f"{elem_cnt}개",
             f"가장 가까운 학교 {int(school_dist)}m" if pd.notna(school_dist) else ""),
            ("🌳 가장 가까운 공원", f"{int(park_dist)}m" if pd.notna(park_dist) else "—",
             f"녹지 점수 {float(green_score):.0f}"),
            ("🏗 재개발 인접", "있음" if redv_n > 0 else "없음", redv_status),
            ("🏥 1km 내 병원", f"{hospital_cnt}개", ""),
            ("🛍 상권 점수", f"{float(commerce_score):.0f} / 100", ""),
            ("⭐ 종합 인프라", f"{float(infra_score):.0f} / 100", ""),
        ]
        for label, val, sub in rows:
            st.markdown(
                f"""
                <div style="border-bottom:1px solid #E2E8F0;padding:10px 0">
                  <div style="display:flex;justify-content:space-between;align-items:baseline">
                    <div style="color:#475569">{label}</div>
                    <div style="font-weight:700">{val}</div>
                  </div>
                  <div style="color:#94A3B8;font-size:.8rem;margin-top:2px">{sub}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with r:
        st.markdown("##### 위치")
        if pd.notna(apt_row.get("lat")) and pd.notna(apt_row.get("lng")):
            point_df = pd.DataFrame([{
                "lat": float(apt_row["lat"]),
                "lng": float(apt_row["lng"]),
                "name": apt_name,
            }])
            layer = pdk.Layer(
                "ScatterplotLayer",
                data=point_df,
                get_position=["lng", "lat"],
                get_radius=80,
                get_fill_color=[220, 38, 38, 220],
                pickable=True,
                radius_min_pixels=8,
            )
            view = pdk.ViewState(
                latitude=float(apt_row["lat"]),
                longitude=float(apt_row["lng"]),
                zoom=14,
            )
            st.pydeck_chart(pdk.Deck(
                layers=[layer], initial_view_state=view,
                tooltip={"text": "{name}"},
                map_style=None,
            ), height=440)
        else:
            st.info("좌표 정보가 없습니다.")

# ── 관심 단지 추가 ─────────────────────────────────────────────
st.markdown("<hr/>", unsafe_allow_html=True)
watchlist = st.session_state.setdefault("watchlist", set())
in_watchlist = selected_apt in watchlist

c1, c2 = st.columns([1, 5])
with c1:
    if in_watchlist:
        if st.button("⭐ 관심 단지에서 빼기", use_container_width=True):
            watchlist.discard(selected_apt)
            st.rerun()
    else:
        if st.button("☆ 관심 단지로 등록", use_container_width=True, type="primary"):
            watchlist.add(selected_apt)
            st.success("관심 단지에 추가됐습니다.")
            st.rerun()
with c2:
    st.caption(f"현재 등록된 관심 단지: {len(watchlist)}개")
