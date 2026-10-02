"""T11 — 차트 템플릿.

입력은 `output/metrics_YYYYMMDD.json` 하나뿐이다. 차트가 DB 를 따로 뒤지지
않는 게 중요하다. 발행된 그림의 숫자와 T12 숫자 검증기가 대조하는 값이
같은 파일에서 나와야 어긋나지 않는다.

두 종류를 만든다.
  단지 추이  change-over-time  -> 선 그래프 (단일 계열)
  지역 비교  polarity          -> 발산형 가로 막대 (Z-score, 0 = 자기 평균)

지역 비교를 그냥 크기 막대로 그리지 않은 이유: 강남과 가평은 거래량 규모가
달라 횡단 비교가 무의미하다. Z-score 는 "자기 평소 대비"라 0 이 의미를 갖는
값이고, 그런 값은 발산형으로 그려야 읽힌다.

실행:
  .venv\\Scripts\\python.exe -m content.charts
  .venv\\Scripts\\python.exe -m content.charts --metrics output/metrics_20261001.json
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates               # noqa: E402
import matplotlib.font_manager as fm            # noqa: E402
import matplotlib.pyplot as plt                 # noqa: E402
from matplotlib.ticker import FuncFormatter     # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# ── 팔레트 ───────────────────────────────────────────────────────────────
# dataviz 스킬의 검증된 기본 팔레트에서 가져왔다. 발산 축은 blue <-> red,
# 중립 중앙값은 회색. validate_palette.js 로 통과 확인:
#   CVD ΔE 21.6 (protan) / 정상시야 ΔE 32.3 / 대비 3:1 이상 — 전 항목 PASS
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
INK_MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
SERIES_1 = "#2a78d6"      # 단일 계열 (선 그래프)
# 발산 축의 방향은 한국 관례를 따른다. 상승·증가가 빨강, 하락·감소가 파랑이다
# (미국과 반대). 국내 독자가 보는 콘텐츠라 뒤집으면 바로 오독된다.
DIVERGE_POS = "#e34948"   # 증가
DIVERGE_NEG = "#2a78d6"   # 감소
NEUTRAL = "#f0efec"

# PNG 는 테마 전환이 없다. 스레드·인스타 발행 기준이 밝은 배경이라 light 로
# 고정한다. 다크 변형이 필요해지면 같은 램프에서 다시 뽑아 검증해야 한다.


def setup_font() -> str:
    """한글 폰트. 없으면 글자가 모두 두부(□)로 나온다.

    로드맵은 Pretendard 를 지정했지만 설치돼 있지 않다. 맑은 고딕이 윈도우
    기본으로 깔려 있고 한글 자소를 모두 포함하므로 그걸 쓴다.
    """
    for name in ("Pretendard", "Malgun Gothic", "맑은 고딕",
                 "NanumGothic", "AppleGothic"):
        try:
            path = fm.findfont(fm.FontProperties(family=name), fallback_to_default=False)
        except Exception:
            continue
        if path and Path(path).exists():
            plt.rcParams["font.family"] = name
            plt.rcParams["axes.unicode_minus"] = False   # 마이너스가 깨진다
            return name
    plt.rcParams["axes.unicode_minus"] = False
    return "(기본 폰트 — 한글이 깨질 수 있음)"


def _style(ax) -> None:
    """공통 뼈대. 격자와 축은 뒤로 물리고 데이터를 앞에 둔다."""
    ax.set_facecolor(SURFACE)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(AXIS)
        ax.spines[s].set_linewidth(1)
    ax.tick_params(colors=INK_MUTED, labelsize=9, length=0)
    ax.grid(True, color=GRID, linewidth=1, axis="y", zorder=0)
    ax.set_axisbelow(True)


def won(man: float) -> str:
    """만원 -> '12.3억'."""
    if man is None:
        return "-"
    if abs(man) >= 10000:
        v = man / 10000
        return f"{v:.0f}억" if abs(v) >= 100 else f"{v:.1f}억"
    return f"{man:,.0f}만"


# ── 1. 단지 추이 ─────────────────────────────────────────────────────────
def chart_apt_trend(series: dict, out: Path) -> Path:
    """월별 평균 실거래가 추이. 단일 계열이라 범례를 두지 않는다 — 제목이 이름."""
    pts = series["points"]
    # 거래가 있는 달만 등간격으로 찍으면 시간 축이 왜곡된다. 13개월 공백이
    # 1개월처럼 보여 "쭉 올랐다"는 인상을 준다. 실제 날짜에 배치한다.
    x = [datetime.strptime(p["ym"], "%Y-%m") for p in pts]
    y = [p["avg_price"] for p in pts]

    fig, ax = plt.subplots(figsize=(9, 5), dpi=160, facecolor=SURFACE)
    _style(ax)

    ax.plot(x, y, color=SERIES_1, linewidth=2, zorder=3,
            solid_capstyle="round")
    ax.fill_between(x, y, min(y) * 0.97, color=SERIES_1, alpha=0.08, zorder=2)
    # 거래가 드문드문하다는 사실 자체가 정보다. 점을 모두 찍어 드러낸다.
    ax.scatter(x, y, s=26, color=SERIES_1, zorder=4,
               edgecolors=SURFACE, linewidths=1.5)

    # 라벨은 끝점과 최고점만. 모든 점에 숫자를 붙이면 읽히지 않는다.
    hi = max(range(len(y)), key=lambda i: y[i])
    marks = [len(y) - 1] + ([hi] if hi != len(y) - 1 else [])
    for i in marks:
        ax.scatter([x[i]], [y[i]], s=46, color=SERIES_1, zorder=5,
                   edgecolors=SURFACE, linewidths=2)
        ax.annotate(won(y[i]), (x[i], y[i]), textcoords="offset points",
                    xytext=(0, 11), ha="center", va="bottom",
                    fontsize=10, fontweight="bold", color=INK, zorder=6)

    # AutoDateLocator 는 짧은 구간에서 적정 간격을 못 고르고 경고를 낸다.
    # 기간 길이를 보고 직접 정한다.
    months = (x[-1].year - x[0].year) * 12 + (x[-1].month - x[0].month) + 1
    step = max(1, round(months / 6))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=step))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: won(v)))

    dong = series.get("legal_dong_name") or ""
    fig.suptitle(f"{series['apt_name']} · {series['pyeong_bucket']}",
                 x=0.015, y=0.975, ha="left", fontsize=15,
                 fontweight="bold", color=INK)
    ax.set_title(f"{series['sigungu_name']} {dong} · 월평균 실거래가",
                 loc="left", fontsize=10.5, color=INK_2, pad=14)
    fig.text(0.015, 0.02, "국토교통부 실거래가 공개시스템 · 해제 건 제외",
             fontsize=8, color=INK_MUTED)

    fig.tight_layout(rect=(0, 0.04, 1, 0.94))
    fig.savefig(out, facecolor=SURFACE)
    plt.close(fig)
    return out


# ── 2. 지역 비교 ─────────────────────────────────────────────────────────
def chart_region_zscore(rows: list[dict], out: Path, top: int = 12) -> Path:
    """시군구 거래량 Z-score. 0 이 '자기 평소'라 발산형으로 그린다."""
    rows = [r for r in rows if r.get("deals_z") is not None]
    rows = sorted(rows, key=lambda r: r["deals_z"], reverse=True)
    if len(rows) > top:
        half = top // 2
        rows = rows[:half] + rows[-half:]
    rows = sorted(rows, key=lambda r: r["deals_z"])

    names = [r["sigungu_name"] for r in rows]
    vals = [r["deals_z"] for r in rows]
    y = list(range(len(rows)))

    fig, ax = plt.subplots(figsize=(9, max(4.5, len(rows) * 0.42)),
                           dpi=160, facecolor=SURFACE)
    _style(ax)
    ax.grid(False, axis="y")
    ax.grid(True, color=GRID, linewidth=1, axis="x", zorder=0)

    colors = [DIVERGE_POS if v >= 0 else DIVERGE_NEG for v in vals]
    bars = ax.barh(y, vals, height=0.62, color=colors, zorder=3)
    for b in bars:                       # 막대 끝 둥글리기 대신 표면 링
        b.set_edgecolor(SURFACE)
        b.set_linewidth(2)

    ax.axvline(0, color=AXIS, linewidth=1.2, zorder=4)
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=10, color=INK)

    # 값은 직접 라벨로. 색만으로 +/- 를 읽게 두지 않는다.
    span = max(abs(min(vals)), abs(max(vals))) or 1
    for yi, v, r in zip(y, vals, rows):
        off = 0.06 * span * (1 if v >= 0 else -1)
        ax.annotate(f"{v:+.1f}σ  ({r['week_deals']}건)", (v, yi),
                    textcoords="offset points",
                    xytext=(6 if v >= 0 else -6, 0),
                    ha="left" if v >= 0 else "right", va="center",
                    fontsize=9, color=INK_2, zorder=5)
    ax.set_xlim(-span * 1.45, span * 1.45)

    wk = rows[0].get("week_start", "")
    fig.suptitle("시군구 거래량 — 자기 평소 대비", x=0.015, y=0.975,
                 ha="left", fontsize=15, fontweight="bold", color=INK)
    ax.set_title(f"{wk} 주 · 지난 52주 평균·표준편차 기준 (0 = 평소 수준)",
                 loc="left", fontsize=10.5, color=INK_2, pad=14)
    fig.text(0.015, 0.015,
             "국토교통부 실거래가 공개시스템 · 해제 건 제외 · "
             "신고 지연을 피해 4주 물린 주를 집계",
             fontsize=8, color=INK_MUTED)

    fig.tight_layout(rect=(0, 0.05, 1, 0.94))
    fig.savefig(out, facecolor=SURFACE)
    plt.close(fig)
    return out


# ── 메인 ─────────────────────────────────────────────────────────────────
def latest_metrics() -> Path | None:
    files = sorted((ROOT / "output").glob("metrics_*.json"))
    return files[-1] if files else None


def main() -> int:
    ap = argparse.ArgumentParser(description="T11 차트 생성")
    ap.add_argument("--metrics", help="지표 JSON 경로")
    ap.add_argument("--outdir", help="출력 디렉터리")
    args = ap.parse_args()

    src = Path(args.metrics) if args.metrics else latest_metrics()
    if src is None or not src.exists():
        print("지표 JSON 이 없다. 먼저: python -m metrics.build_metrics")
        return 1
    data = json.loads(src.read_text(encoding="utf-8"))

    font = setup_font()
    outdir = Path(args.outdir) if args.outdir else ROOT / "output" / data["asof"]
    outdir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'=' * 60}\n  차트 생성  기준일 {data['asof']}\n{'=' * 60}")
    print(f"  폰트: {font}")

    made = []
    series = data.get("series") or []
    if series:
        p = chart_apt_trend(series[0], outdir / "chart_apt_trend.png")
        made.append(p)
        print(f"  단지 추이: {series[0]['apt_name']} ({len(series[0]['points'])}개월)")

    z = data.get("weekly", {}).get("sgg_zscore") or []
    if z:
        p = chart_region_zscore(z, outdir / "chart_region_zscore.png")
        made.append(p)
        print(f"  지역 비교: 시군구 {len(z)}개 중 상·하위")

    print(f"\n  저장: {outdir}")
    for p in made:
        print(f"    {p.name}  ({p.stat().st_size / 1024:.0f}KB)")
    print(f"{'=' * 60}\n")
    return 0 if made else 1


if __name__ == "__main__":
    sys.exit(main())
