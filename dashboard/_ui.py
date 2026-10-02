"""대시보드 공통 UI 헬퍼 (KPI 카드, 차트 스타일, 단지 카드)."""
from __future__ import annotations
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# ── 색상 ──────────────────────────────────────────────────────
COLOR_PRIMARY = "#1E40AF"   # deep blue
COLOR_ACCENT = "#16A34A"    # green - 좋은 신호
COLOR_WARNING = "#DC2626"   # red
COLOR_NEUTRAL = "#64748B"   # slate
COLOR_BG_SOFT = "#F1F5F9"

PLOTLY_TEMPLATE = dict(
    layout=dict(
        font=dict(family="Pretendard, -apple-system, system-ui, sans-serif", size=13),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis=dict(showgrid=False, showline=False),
        yaxis=dict(showgrid=True, gridcolor="#E2E8F0", zeroline=False),
        colorway=[COLOR_PRIMARY, COLOR_ACCENT, "#7C3AED", "#F59E0B", "#EC4899"],
    )
)


# ── 페이지 공통 세팅 ──────────────────────────────────────────
def page_header(title: str, subtitle: str = "", icon: str = ""):
    st.markdown(
        f"""
        <div style="margin-bottom:1.2rem">
          <div style="font-size:1.65rem;font-weight:800;color:{COLOR_PRIMARY};letter-spacing:-0.02em">
            {icon} {title}
          </div>
          <div style="color:#64748B;margin-top:0.15rem">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def inject_css():
    """글로벌 미세 조정 CSS."""
    st.markdown(
        """
        <style>
        /* 메인 컨테이너 패딩 — Streamlit 상단 툴바와 겹치지 않도록 충분히 확보 */
        .block-container { padding-top: 3rem; padding-bottom: 2rem; max-width: 1280px; }

        /* 메트릭 라벨 색상 */
        [data-testid="stMetricLabel"] { color: #64748B; font-size: 0.85rem; }
        [data-testid="stMetricValue"] { font-weight: 700; color: #0F172A; }

        /* 사이드바 헤딩 */
        section[data-testid="stSidebar"] h2 { color: #1E40AF; }

        /* 카드 스타일 (단지 카드) */
        .apt-card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 14px 16px;
            margin-bottom: 10px;
            transition: all .15s;
        }
        .apt-card:hover { border-color: #1E40AF; box-shadow: 0 4px 12px rgba(30,64,175,.08); }
        .apt-card .name { font-size: 1.05rem; font-weight: 700; color: #0F172A; }
        .apt-card .loc  { font-size: .85rem; color: #64748B; margin-top: 2px; }
        .apt-card .price { font-size: 1.2rem; font-weight: 800; color: #1E40AF; margin-top: 6px; }
        .apt-card .meta { font-size: .82rem; color: #475569; margin-top: 4px; }
        .apt-card .badge {
            display: inline-block; padding: 2px 8px; border-radius: 999px;
            font-size: .72rem; font-weight: 600; margin-right: 4px;
        }
        .badge-green { background: #DCFCE7; color: #166534; }
        .badge-blue  { background: #DBEAFE; color: #1E40AF; }
        .badge-amber { background: #FEF3C7; color: #92400E; }
        .badge-red   { background: #FEE2E2; color: #991B1B; }

        /* hr 톤 다운 */
        hr { border-color: #E2E8F0 !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ── KPI 카드 ──────────────────────────────────────────────────
def kpi_row(items: list[tuple[str, str, str]]):
    """items: [(label, value, delta_or_caption), ...]."""
    cols = st.columns(len(items))
    for col, (label, value, sub) in zip(cols, items):
        with col:
            st.markdown(
                f"""
                <div style="background:{COLOR_BG_SOFT};border-radius:12px;padding:14px 16px">
                  <div style="font-size:.78rem;color:#64748B;font-weight:600;letter-spacing:.02em">{label}</div>
                  <div style="font-size:1.55rem;font-weight:800;color:#0F172A;margin-top:2px">{value}</div>
                  <div style="font-size:.78rem;color:#475569;margin-top:2px">{sub}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ── 단지 카드 ─────────────────────────────────────────────────
def apt_card(row: dict, key_prefix: str = "card") -> bool:
    """단지 1개 카드 렌더. 클릭(상세 보기) 버튼 누르면 True 반환."""
    name = row.get("apt_name") or row.get("apt_name_raw") or "—"
    sgg = row.get("sigungu_name", "") or ""
    pyeong = row.get("pyeong_bucket", "") or ""
    last_price = row.get("trade_last_price") or row.get("last_price")
    per_pyeong = row.get("price_per_pyeong")
    score = row.get("model_score") or row.get("infra_score")
    station = row.get("nearest_station", "") or ""
    walk = row.get("walk_min")
    redv = row.get("redv_nearby", 0)

    badges = []
    if pd.notna(last_price) and last_price:
        try:
            badges.append(("badge-blue", f"💰 최근거래"))
        except Exception:
            pass
    if station and pd.notna(walk) and walk and walk <= 10:
        badges.append(("badge-green", f"🚇 역세권"))
    if redv and int(redv) > 0:
        badges.append(("badge-amber", "🏗 재개발 인접"))

    badge_html = "".join(
        f'<span class="badge {cls}">{txt}</span>' for cls, txt in badges
    )

    price_text = "—"
    if pd.notna(last_price) and last_price:
        eok = int(last_price // 10000)
        rest = int(last_price % 10000)
        price_text = f"{eok}억 {rest:,}만" if eok else f"{rest:,}만"

    pp_text = ""
    if pd.notna(per_pyeong) and per_pyeong:
        pp_text = f"평당 {int(per_pyeong):,}만"

    score_text = ""
    if pd.notna(score) and score:
        score_text = f" · 점수 {float(score):.0f}"

    walk_text = ""
    if station and pd.notna(walk) and walk:
        walk_text = f" · {station} 도보 {int(walk)}분"

    st.markdown(
        f"""
        <div class="apt-card">
          <div>{badge_html}</div>
          <div class="name">{name}</div>
          <div class="loc">{sgg} · {pyeong}{walk_text}</div>
          <div class="price">{price_text}</div>
          <div class="meta">{pp_text}{score_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    return st.button("상세 보기", key=f"{key_prefix}_{row.get('apt_id','')}_{pyeong}", use_container_width=True)


# ── 공통 차트 ─────────────────────────────────────────────────
def line_price_trend(df: pd.DataFrame, x: str, y: str, title: str = ""):
    fig = px.line(df, x=x, y=y, markers=True, title=title, template="simple_white")
    fig.update_traces(line=dict(color=COLOR_PRIMARY, width=2.5))
    fig.update_layout(**PLOTLY_TEMPLATE["layout"])
    return fig


def bar_compare(df: pd.DataFrame, x: str, y: str, title: str = "", color=None):
    fig = px.bar(df, x=x, y=y, title=title, color=color, template="simple_white")
    fig.update_traces(marker_color=COLOR_PRIMARY) if color is None else None
    fig.update_layout(**PLOTLY_TEMPLATE["layout"])
    return fig
