"""FULL-HISTORY-V1: frozen aggregate inputs only; no ingestion or network calls."""
from pathlib import Path
from datetime import datetime
import hashlib
import json
import platform

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
RESEARCH = ROOT / "video-agent-studio/episodes/regional-price-recovery-20261022/research/full-history-v1"
SOURCE = ROOT / "analysis/housing_growth_2006/regional_expansion_v1"
BUILDER = ROOT / "analysis/housing_growth_2006/regional_expansion_v1.py"
END = "2026Q2"
DATA_DATE = "2026-06-30"
CHECK_DATE = "2026-10-23"
ORDER = ["서울", "경기", "인천", "부산", "대구", "대전", "세종"]
MAJOR_PCT = 5.0  # Descriptive display label only: never filters episode detection.
FONT = Path("C:/Windows/Fonts/malgun.ttf")
BG, INK, BLUE, RED, GRAY = "#f6f4ef", "#173348", "#286cda", "#b54c46", "#546973"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path):
    return path.relative_to(ROOT).as_posix()


def save_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def quarter_number(value):
    return pd.Period(value, freq="Q").ordinal


def check_chain(quarters):
    numbers = np.array([quarter_number(q) for q in quarters])
    assert len(numbers) > 1 and np.all(np.diff(numbers) == 1), "분기 중복·역순·누락"


def drawdown_episodes(quarters, values, region):
    """Close at the FIRST return to the prior running high, before later lows exist.

    Equal highs update the peak date to the last touch before a decline. Tied
    troughs use their first occurrence. Strict value comparisons define return;
    only the descriptive 5% label has a numerical rounding tolerance.
    """
    y = [float(v) for v in values]
    assert len(y) == len(quarters) and all(np.isfinite(y)) and min(y) > 0
    peak_i, active, found = 0, None, []
    for i in range(1, len(y)):
        if active is None:
            if y[i] >= y[peak_i]:
                peak_i = i
                continue
            active = {"peak_i": peak_i, "first_decline_i": i, "trough_i": i}
        if y[i] < y[active["trough_i"]]:
            active["trough_i"] = i
        if y[i] >= y[active["peak_i"]]:
            found.append(dict(active, return_i=i))
            active, peak_i = None, i
    if active is not None:
        found.append(dict(active, return_i=None))
    output = []
    for number, item in enumerate(found, 1):
        p, t, r = item["peak_i"], item["trough_i"], item["return_i"]
        end = len(y) - 1 if r is None else r
        duration = quarter_number(quarters[end]) - quarter_number(quarters[p])
        depth = (y[t] / y[p] - 1) * 100
        output.append({
            "episode_id": f"{region}-DD-{number:02d}", "region": region,
            "peak_quarter": quarters[p], "peak_index": y[p],
            "peak_is_observation_start": p == 0,
            "first_decline_quarter": quarters[item["first_decline_i"]],
            "trough_quarter": quarters[t], "trough_index": y[t],
            "max_drawdown_pct": depth,
            "major_ge_5pct": bool(depth <= -MAJOR_PCT + 1e-10),
            "first_return_quarter": None if r is None else quarters[r],
            "first_return_index": None if r is None else y[r],
            "right_censored": r is None, "observed_end_quarter": quarters[end],
            "peak_to_trough_quarters": quarter_number(quarters[t]) - quarter_number(quarters[p]),
            "peak_to_first_return_quarters": None if r is None else duration,
            "trough_to_first_return_quarters": None if r is None else quarter_number(quarters[r]) - quarter_number(quarters[t]),
            "peak_to_observed_end_quarters": duration,
            "peak_to_observed_end_years": duration / 4,
            "underwater_observed_quarters": end - item["first_decline_i"] + (r is None),
            "duration_status": "미회복·관측종료" if r is None else "최초복귀 관측",
        })
    return output


def validate_episodes(quarters, values, episodes):
    """Independent slice checks against the original curve and running maximum."""
    y = np.asarray(values, dtype=float)
    running = np.maximum.accumulate(y)
    dd = (y / running - 1) * 100
    positions = {q: i for i, q in enumerate(quarters)}
    accounted = np.zeros(len(y), dtype=int)
    last_end = -1
    for num, e in enumerate(episodes):
        p, t = positions[e["peak_quarter"]], positions[e["trough_quarter"]]
        r = None if e["first_return_quarter"] is None else positions[e["first_return_quarter"]]
        stop = len(y) if r is None else r
        assert p >= last_end and p < t < stop, "고점/저점 순서 또는 미래 저점 사용"
        assert y[p] == running[p] and y[t] == min(y[p:stop]), "과거 누적 고점/구간 최저 불일치"
        assert t == p + int(np.argmin(y[p:stop])), "동률 저점의 최초 시점 불일치"
        assert np.all(y[p + 1:stop] < y[p]), "최초 복귀 전에 이미 복귀함"
        assert positions[e["first_decline_quarter"]] == p + 1
        if r is None:
            assert num == len(episodes) - 1 and e["right_censored"]
            assert e["observed_end_quarter"] == quarters[-1]
            assert e["peak_to_first_return_quarters"] is None
            assert e["trough_to_first_return_quarters"] is None
            assert not np.any(y[p + 1:] >= y[p]), "미회복 구간에 숨은 복귀 존재"
        else:
            assert not e["right_censored"] and y[r] >= y[p], "첫 교차값이 직전 고점 미달"
            candidates = np.flatnonzero(y[p + 1:] >= y[p])
            assert len(candidates) and r == p + 1 + int(candidates[0])
            assert e["observed_end_quarter"] == quarters[r]
        accounted[p + 1:stop] += 1
        last_end = stop if r is None else r
    assert np.array_equal(accounted, (y < running).astype(int)), "하락 분기 누락·중복"
    episode_min = min([0.0] + [e["max_drawdown_pct"] for e in episodes])
    assert np.isclose(float(dd.min()), episode_min, atol=1e-10)
    return dd


def synthetic_checks():
    cases = [
        ("단조상승", [100, 110, 120], []),
        ("복귀후_더낮은미래저점", [100, 80, 105, 90, 70, 100, 110], [(0, 1, 2), (2, 4, 6)]),
        ("고점동률_최초복귀", [100, 90, 100, 95, 105], [(0, 1, 2), (2, 3, 4)]),
        ("고점및저점_동률처리", [100, 100, 90, 90, 100], [(1, 2, 4)]),
        ("미회복_관측종료", [100, 80, 90], [(0, 1, None)]),
        ("정확히5퍼센트", [100, 95, 100], [(0, 1, 2)]),
        ("마지막분기_첫하락", [100, 110, 100], [(1, 2, None)]),
    ]
    passed = []
    for name, values, expected in cases:
        q = [str(x) for x in pd.period_range("2000Q1", periods=len(values), freq="Q")]
        episodes = drawdown_episodes(q, values, "synthetic")
        actual = [(q.index(e["peak_quarter"]), q.index(e["trough_quarter"]),
                   None if e["first_return_quarter"] is None else q.index(e["first_return_quarter"])) for e in episodes]
        assert actual == expected, (name, actual, expected)
        validate_episodes(q, values, episodes)
        if name == "정확히5퍼센트":
            assert episodes[0]["major_ge_5pct"]
        passed.append({"check": name, "status": "pass", "expected_peak_trough_return_positions": expected})
    return passed


def analyze(index, volume, coverage):
    summaries, all_episodes, curves = [], [], []
    assert set(index.region) == set(ORDER) == set(volume.region) == set(coverage.region)
    assert not index.duplicated(["region", "quarter"]).any()
    assert not volume.duplicated(["region", "quarter"]).any() and coverage.region.is_unique
    for region in ORDER:
        s = index[index.region == region].copy()
        v = volume[volume.region == region].copy()
        c = coverage[coverage.region == region].iloc[0]
        quarters = s.quarter.tolist()
        check_chain(quarters)
        check_chain(v.quarter.tolist())
        assert quarters[-1] == END and v.quarter.iloc[-1] == END
        assert quarters[0] == ("2015Q1" if region == "세종" else "2006Q1")
        assert v.quarter.iloc[0] == "2006Q1"
        assert s.matched_complexes.iloc[1:].notna().all() and (s.matched_complexes.iloc[1:] >= 30).all()
        assert pd.isna(s.matched_complexes.iloc[0]), "기준분기는 연결 통계가 없는 기준값"
        assert int(v.transactions.sum()) == int(c.transactions)
        assert (v.transactions > 0).all() and (v.complexes > 0).all()
        assert pd.Period(c.first_date, freq="Q") == pd.Period(v.quarter.iloc[0], freq="Q")
        assert pd.Period(c.last_date, freq="Q") == pd.Period(END, freq="Q")
        y = s["index"].to_numpy(dtype=float)
        assert np.isfinite(y).all() and (y > 0).all()
        episodes = drawdown_episodes(quarters, y, region)
        dd = validate_episodes(quarters, y, episodes)
        all_episodes.extend(episodes)
        top = float(y.max())
        maximum_positions = np.flatnonzero(y == top)
        years = (quarter_number(END) - quarter_number(quarters[0])) / 4
        worst = min(episodes, key=lambda e: e["max_drawdown_pct"]) if episodes else None
        completed = [e for e in episodes if not e["right_censored"]]
        longest = max(completed, key=lambda e: e["peak_to_first_return_quarters"]) if completed else None
        longest_from_trough = max(completed, key=lambda e: e["trough_to_first_return_quarters"]) if completed else None
        active = episodes[-1] if episodes and episodes[-1]["right_censored"] else None
        in_period = v.quarter.map(quarter_number) >= quarter_number(quarters[0])
        row = {
            "region": region, "price_start_quarter": quarters[0], "price_end_quarter": END,
            "price_observed_quarters": len(s), "price_elapsed_years": years,
            "price_calendar_years_touched": len({q[:4] for q in quarters}),
            "baseline_index": float(y[0]), "latest_index": float(y[-1]),
            "full_period_cumulative_change_pct": float((y[-1] / y[0] - 1) * 100),
            "full_period_cagr_pct": float(((y[-1] / y[0]) ** (1 / years) - 1) * 100),
            "all_time_high_index": top, "all_time_high_first_quarter": quarters[int(maximum_positions[0])],
            "all_time_high_last_quarter": quarters[int(maximum_positions[-1])],
            "latest_vs_all_time_high_pct": float((y[-1] / top - 1) * 100),
            "latest_is_all_time_high": bool(y[-1] == top), "had_past_decline": bool(episodes),
            "all_drawdown_episode_count": len(episodes),
            "major_ge_5pct_episode_count": sum(e["major_ge_5pct"] for e in episodes),
            "completed_episode_count": len(completed), "right_censored_episode_count": int(active is not None),
            "max_historical_drawdown_pct": float(dd.min()),
            "max_drawdown_episode_id": None if worst is None else worst["episode_id"],
            "max_drawdown_peak_quarter": None if worst is None else worst["peak_quarter"],
            "max_drawdown_trough_quarter": None if worst is None else worst["trough_quarter"],
            "max_drawdown_first_return_quarter": None if worst is None else worst["first_return_quarter"],
            "max_drawdown_right_censored": None if worst is None else worst["right_censored"],
            "max_drawdown_peak_to_first_return_quarters": None if worst is None else worst["peak_to_first_return_quarters"],
            "max_drawdown_trough_to_first_return_quarters": None if worst is None else worst["trough_to_first_return_quarters"],
            "max_drawdown_peak_to_observed_end_quarters": None if worst is None else worst["peak_to_observed_end_quarters"],
            "longest_completed_recovery_episode_id": None if longest is None else longest["episode_id"],
            "longest_completed_recovery_quarters": None if longest is None else longest["peak_to_first_return_quarters"],
            "longest_completed_recovery_years": None if longest is None else longest["peak_to_first_return_quarters"] / 4,
            "longest_completed_recovery_peak_quarter": None if longest is None else longest["peak_quarter"],
            "longest_completed_recovery_return_quarter": None if longest is None else longest["first_return_quarter"],
            "longest_completed_trough_recovery_episode_id": None if longest_from_trough is None else longest_from_trough["episode_id"],
            "longest_completed_trough_to_first_return_quarters": None if longest_from_trough is None else longest_from_trough["trough_to_first_return_quarters"],
            "active_episode_id": None if active is None else active["episode_id"],
            "active_episode_elapsed_quarters_lower_bound": None if active is None else active["peak_to_observed_end_quarters"],
            "active_episode_trough_quarter_observed_only": None if active is None else active["trough_quarter"],
            "min_link_matched_complexes": int(s.matched_complexes.iloc[1:].min()),
            "latest_link_matched_complexes": int(s.matched_complexes.iloc[-1]),
            "full_volume_start_quarter": v.quarter.iloc[0], "full_volume_end_quarter": END,
            "full_volume_quarters": len(v), "full_volume_calendar_years_touched": len({q[:4] for q in v.quarter}),
            "full_volume_first_date": c.first_date, "full_volume_last_date": c.last_date,
            "full_valid_transaction_total": int(v.transactions.sum()),
            "valid_transactions_within_price_index_dates": int(v.loc[in_period, "transactions"].sum()),
            "valid_transactions_before_price_index_start": int(v.loc[~in_period, "transactions"].sum()),
            "matched_transaction_total": None, "matched_transaction_share_pct": None,
            "matched_trade_count_status": "기존 집계에 매칭 거래건수 없음·산출 불가",
        }
        summaries.append(row)
        for i, q in enumerate(quarters):
            curves.append({"region": region, "quarter": q, "source_index": float(y[i]),
                           "normalized_start_100": float(y[i] / y[0] * 100),
                           "running_high_index": float(np.max(y[:i + 1])),
                           "running_drawdown_pct": float(dd[i]),
                           "matched_complexes": None if i == 0 else int(s.matched_complexes.iloc[i]),
                           "source_row_number_including_header": int(s.index[i]) + 2,
                           "source_file": rel(SOURCE / "quarterly_index.csv")})
    return summaries, all_episodes, pd.DataFrame(curves)


def style_axis(ax):
    ax.set_facecolor(BG)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(length=0, labelcolor=GRAY, labelsize=11, pad=6)
    ax.grid(axis="y", color="#d9dedf", linewidth=.8)


def plot_charts(curves, summaries, episodes):
    font_manager.fontManager.addfont(str(FONT))
    plt.rcParams.update({"font.family": "Malgun Gothic", "axes.unicode_minus": False,
                         "font.size": 13, "svg.fonttype": "path"})
    lookup = {r["region"]: r for r in summaries}
    assets = []

    def save(fig, name):
        for ext in ("png", "svg"):
            path = OUT / f"{name}.{ext}"
            fig.savefig(path, dpi=150, facecolor=BG)
            assets.append(path)
        plt.close(fig)

    fig, axes = plt.subplots(3, 2, figsize=(16, 13), facecolor=BG)
    fig.subplots_adjust(left=.075, right=.95, top=.845, bottom=.145, hspace=.65, wspace=.23)
    fig.text(.075, .962, "2006년부터 이어 본 지역별 가격 경로", fontsize=26, weight="bold", color=INK)
    fig.text(.075, .922, "6개 지역 · 2006Q1 = 100 · 동일 세로축 · 자료 종료 2026Q2 (2026-06-30)", color=GRAY)
    ymax = np.ceil(curves[curves.region != "세종"].normalized_start_100.max() / 100) * 100
    for ax, region in zip(axes.flat, ORDER[:-1]):
        c = curves[curves.region == region]
        r = lookup[region]
        x = np.arange(len(c))
        style_axis(ax)
        ax.axhline(100, color=GRAY, linewidth=1, linestyle=(0, (4, 4)))
        ax.plot(x, c.normalized_start_100, color=BLUE, linewidth=2.7)
        ax.scatter([x[-1]], [c.normalized_start_100.iloc[-1]], color=BLUE, s=25)
        ax.set_xlim(0, len(c) - 1)
        ax.set_ylim(0, ymax)
        ax.set_yticks(np.arange(0, ymax + 1, 100))
        ticks = [i for i, q in enumerate(c.quarter) if q.endswith("Q1") and int(q[:4]) % 4 == 2 and i < len(c) - 8]
        ax.set_xticks(ticks + [len(c) - 1], [c.quarter.iloc[i][:4] for i in ticks] + ["2026Q2"])
        ax.set_title(region + (" (군위 제외)" if region == "대구" else ""), loc="left", color=INK, weight="bold", fontsize=19, pad=39)
        ax.text(0, 1.075, f"누적 {r['full_period_cumulative_change_pct']:+.1f}%  |  연환산 {r['full_period_cagr_pct']:.2f}%", transform=ax.transAxes, color=BLUE, fontsize=12)
        ax.text(.98, .94, f"전체 최고 대비 {r['latest_vs_all_time_high_pct']:.1f}%", transform=ax.transAxes, ha="right", va="top", color=INK, fontsize=11)
    footnotes(fig, .075, .091)
    save(fig, "full_history_six_regions_2006")

    fig, ax = plt.subplots(figsize=(13, 7.5), facecolor=BG)
    fig.subplots_adjust(left=.085, right=.95, top=.77, bottom=.25)
    c, r = curves[curves.region == "세종"], lookup["세종"]
    fig.text(.085, .94, "세종은 2015년부터 별도로 봅니다", fontsize=25, weight="bold", color=INK)
    fig.text(.085, .883, "지원되는 연속 가격지수: 2015Q1~2026Q2 · 2015Q1 = 100", color=GRAY)
    fig.text(.085, .833, f"누적 {r['full_period_cumulative_change_pct']:+.1f}% · 연환산 {r['full_period_cagr_pct']:.2f}% · 전체 최고 대비 {r['latest_vs_all_time_high_pct']:.1f}%", color=BLUE)
    style_axis(ax)
    ax.plot(np.arange(len(c)), c.normalized_start_100, color=BLUE, linewidth=3)
    ax.axhline(100, color=GRAY, linewidth=1, linestyle=(0, (4, 4)))
    peak = c.source_index.idxmax()
    peak_pos = c.index.get_loc(peak)
    ax.scatter([peak_pos, len(c) - 1], [c.loc[peak, "normalized_start_100"], c.normalized_start_100.iloc[-1]], color=BLUE)
    ax.annotate(f"전체 최고 {r['all_time_high_first_quarter']}", (peak_pos, c.loc[peak, "normalized_start_100"]), xytext=(0, 15), textcoords="offset points", ha="center", fontsize=12, color=INK)
    ticks = [i for i, q in enumerate(c.quarter) if q.endswith("Q1") and int(q[:4]) % 2 == 1]
    ax.set_xticks(ticks + [len(c) - 1], [c.quarter.iloc[i][:4] for i in ticks] + [END])
    ax.set_ylim(0, 260)
    ax.set_xlim(0, len(c) - 1)
    fig.text(.085, .172, "2006~2014년 가격선은 만들지 않았습니다. 2006년 이후 거래량 자료와 가격지수의 지원 기간은 다릅니다.", fontsize=11, color=GRAY)
    footnotes(fig, .085, .12)
    save(fig, "full_history_sejong_2015")

    fig, axes = plt.subplots(4, 2, figsize=(16, 15), facecolor=BG)
    fig.subplots_adjust(left=.075, right=.95, top=.86, bottom=.12, hspace=.64, wspace=.23)
    fig.text(.075, .955, "그때까지의 최고값에서 얼마나 내려왔나", fontsize=25, weight="bold", color=INK)
    fig.text(.075, .92, "누적 고점 대비 낙폭 (%) · 가격지수의 전체 가용 이력 · 자료 종료 2026Q2", color=GRAY)
    floor = min(-5, np.floor(curves.running_drawdown_pct.min() / 5) * 5)
    for ax, region in zip(axes.flat, ORDER):
        c, r = curves[curves.region == region], lookup[region]
        style_axis(ax)
        x, y = np.arange(len(c)), c.running_drawdown_pct.to_numpy()
        ax.fill_between(x, y, 0, color=RED, alpha=.16)
        ax.plot(x, y, color=RED, linewidth=2.3)
        ax.axhline(0, color=GRAY, linewidth=.8)
        ax.axhline(-5, color=GRAY, linestyle=(0, (4, 4)), linewidth=.8)
        ax.set_ylim(floor, 1.8)
        ax.set_xlim(0, len(c) - 1)
        ax.set_yticks(np.arange(floor, 1, 5))
        ticks = sorted({0} | {i for i, q in enumerate(c.quarter) if q.endswith("Q1") and int(q[:4]) % 5 == 0 and i < len(c) - 8})
        ax.set_xticks(ticks + [len(c) - 1], [c.quarter.iloc[i][:4] for i in ticks] + [END])
        ax.set_title(region + (" · 2015Q1부터" if region == "세종" else " · 2006Q1부터"), loc="left", color=INK, weight="bold", fontsize=16, pad=29)
        ax.text(0, 1.055, f"최대 낙폭 {r['max_historical_drawdown_pct']:.1f}%  |  현재 {r['latest_vs_all_time_high_pct']:.1f}%", transform=ax.transAxes, fontsize=11, color=RED)
    axes.flat[-1].axis("off")
    axes.flat[-1].text(0, .95, "해석할 때 지킬 조건", color=INK, fontsize=17, weight="bold", va="top")
    axes.flat[-1].text(0, .70, "0% = 그 분기까지의 최고값\n최신 0%여도 과거 하락은 존재할 수 있음\n-5% 점선은 설명용 기준이며 모든 하락구간을 집계\n미회복 기간의 최종 저점·최종 회복일은 알 수 없음", color=GRAY, fontsize=12, linespacing=1.8, va="top")
    footnotes(fig, .075, .071)
    save(fig, "running_peak_drawdown_full_history")
    return assets


def footnotes(fig, x, y):
    for i, text in enumerate([
        "출처: regional_expansion_v1의 동결 CSV · 보유 유효거래 기반 자체 매칭지수 · 공식 지수/투자수익률 아님",
        "동일 단지·전용면적(0.01㎡ 반올림)의 ㎡당 분기 중위값 연결 · 양 분기 각각 2건 이상 · 연결당 30개 단지 이상",
        "분기별 매칭 표본 변화, 동·층·수리 상태 미조정 · 대구 군위 제외 · 자료 종료 2026-06-30 / 계산 확인 2026-10-23",
    ]):
        fig.text(x, y - i * .021, text, fontsize=9.3, color=GRAY)


def write_report(summaries, episodes, total):
    by_region = {r["region"]: r for r in summaries}
    lines = [
        "# 전체 가용 이력 분석 FULL-HISTORY-V1", "",
        f"자료 종료: **2026Q2 (2026-06-30)**. 계산 확인일: **{CHECK_DATE}**. 입력은 `../regional_expansion_v1/`의 동결 집계 네 개다. 원자료 수집·재정규화·외부 조회는 실행하지 않았다.", "",
        "## 먼저 읽을 결과", "",
        "6개 지역(서울·경기·인천·부산·대구·대전)은 2006Q1~2026Q2의 82개 분기, 20.25년을 연결했다. 세종은 2015Q1~2026Q2의 46개 분기, 11.25년만 지원된다. 세종의 2006년 가격지수를 만들지 않았으며, 누적 변화율과 CAGR의 비교 기간도 다르다.", "",
        "|지역|가격지수 기간|전체 누적 변화|전체 CAGR|전체 최고 분기|최신/전체 최고|역사적 최대 낙폭|",
        "|---|---|---:|---:|---|---:|---:|",
    ]
    for r in summaries:
        lines.append(f"|{r['region']}|{r['price_start_quarter']}~{END}|{r['full_period_cumulative_change_pct']:+.2f}%|{r['full_period_cagr_pct']:.2f}%|{r['all_time_high_first_quarter']}|{r['latest_vs_all_time_high_pct']:.2f}%|{r['max_historical_drawdown_pct']:.2f}%|")
    lines += ["", "CAGR = `(마지막 지수 / 첫 지수)^(1 / ((마지막 분기-첫 분기)/4)) - 1`. 82개 관측값의 시간 간격은 81분기다. 연도별 관측값 개수를 보유 기간으로 쓰지 않았다. 물가·배당·임대료·세금·금융비용을 반영하지 않은 명목 가격지수 변화다.", "",
              "## 과거 하락과 회복을 모두 세기", "",
              "회복은 특정 시기를 골라 정한 고점이나 전체 이력을 본 뒤의 미래 저점에 의존하지 않는다. 매 분기까지의 누적 고점에서 한 번이라도 내려가면 구간을 시작하고, **그 고점 이상으로 처음 돌아온 분기**에 즉시 닫는다. 이후 더 낮은 저점이 나와도 이미 끝난 구간에 붙이지 않는다. 고점 동률은 하락 직전의 마지막 접점, 저점 동률은 해당 구간의 첫 최저점을 쓴다. 관측 첫 분기 이전의 고점·하락은 알 수 없다.", "",
              "`episodes.csv`에는 크기와 무관하게 모든 하락구간을 저장했다. 최대 낙폭이 5% 이상인 `major_ge_5pct`는 발표 때 가독성을 위한 설명용 표식이며, 하락 검출·전체 최고·최대 낙폭·최장 회복 계산의 필터가 아니다.", "",
              "|지역|모든 하락구간 / 5% 이상|역사적 최대낙폭 고점→저점|그 구간 최초복귀|최장 관측 완료 회복(고점→복귀)|현재 미회복 경과 하한|",
              "|---|---:|---|---|---|---|"]
    for r in summaries:
        longest = "완료 사례 없음" if r["longest_completed_recovery_quarters"] is None else f"{r['longest_completed_recovery_quarters']}분기 ({r['longest_completed_recovery_years']:.2f}년), {r['longest_completed_recovery_peak_quarter']}→{r['longest_completed_recovery_return_quarter']}"
        active = "없음" if r["active_episode_elapsed_quarters_lower_bound"] is None else f"{r['active_episode_elapsed_quarters_lower_bound']}분기 경과·회복기간 미정"
        lines.append(f"|{r['region']}|{r['all_drawdown_episode_count']} / {r['major_ge_5pct_episode_count']}|{r['max_drawdown_peak_quarter']}→{r['max_drawdown_trough_quarter']}|{r['max_drawdown_first_return_quarter'] or '2026Q2까지 미회복'}|{longest}|{active}|")
    lines += ["", "완료 회복기간은 고점→최초복귀의 **분기 간격**이며, 저점→복귀 기간과 그 최장 완료 사례도 별도 열로 제공한다. 최장 기간의 동률은 먼저 관측된 구간을 대표로 쓰며 모든 동률 사례는 episodes.csv에 남는다. 관측 첫 분기가 고점인 구간은 `peak_is_observation_start=true`로 표시하며, 그 이전 고점을 안다는 뜻이 아니다. 미회복 구간에는 복귀일·완료 회복기간을 빈 값으로 남기고 `right_censored=true`로 표시한다. 미회복 경과기간은 이미 관측된 하한일 뿐 최종 소요기간이 아니다. 해당 저점도 2026Q2까지 관측된 최저일 뿐 미래까지 확정된 바닥이 아니다. 최초복귀는 지속적 안착·추세 확정을 뜻하지 않는다.", "",
              "## 거래량 전체와 매칭 가격 표본의 범위", "",
              f"보유 자료에서 필터를 통과한 유효거래는 합계 **{total:,}건**이다. 이는 보유·수집 범위의 유효거래 전체이고, 전국 전체 거래나 전수 가격 매칭을 뜻하지 않는다. 각 지역의 거래량 분기는 모두 2006Q1~2026Q2(82개)이며 달력연도 21개에 걸친다. 2006~2025년은 20개 연도, 2026년은 상반기만 포함한다. 연도별 건수는 `annual_valid_volume.csv`에서 확인할 수 있다.", "",
              "|지역|거래량 최초~최종 계약일|전체 유효거래|가격지수 지원기간 안의 유효거래|지원 이전 유효거래|연결 단지 최소 / 최신|",
              "|---|---|---:|---:|---:|---:|"]
    for r in summaries:
        lines.append(f"|{r['region']}|{r['full_volume_first_date']}~{r['full_volume_last_date']}|{r['full_valid_transaction_total']:,}|{r['valid_transactions_within_price_index_dates']:,}|{r['valid_transactions_before_price_index_start']:,}|{r['min_link_matched_complexes']} / {r['latest_link_matched_complexes']}|")
    lines += ["", "가격지수 지원기간 안의 유효거래 건수도 **실제로 매칭된 거래건수가 아니다**. 기존 CSV에는 매칭 단지 수만 있고 매칭 거래건수·비율은 없다. 이를 분기 거래량이나 단지 수로 역산하지 않았으며, 해당 값은 `null`로 남겼다. 분기별 매칭 단지 수의 합도 고유 단지 수나 고유 거래건수가 아니다.", "",
              "## 산식과 입력의 한계", "",
              "가격은 단순 최고 거래가격·전체 평균가격이 아니다. 동일 단지와 전용면적(0.01㎡ 반올림) 그룹의 분기별 ㎡당 중위가격을 계산하고, 양 분기 각각 2건 이상인 그룹끼리 비교한다. 면적별 로그 변화율을 단지 안에서 평균한 후 지역 안의 단지를 동일 가중해 분기 연결한다. 한 연결에 단지 30개 이상인, 2026Q2에 끝나는 연속 구간만 사용한 기존 지수다. 84㎡ 등 고정 면적에 한정하지 않는다. 신규 단지와 거래 표본의 변화, 동·층·수리 상태 등은 완전히 통제하지 못한다.", "",
              "기존 빌더에 기록된 유효거래 정의는 취소 표시 거래 제외, 양수 거래금액·면적, 단지 식별자 존재, 거래 해시 중복 제거, 2006Q1~2026Q2 계약이다. 신규 정규화는 같은 거래키에서 취소 표시가 한 번이라도 있으면 취소로 처리한다. 실제 원본 취소·신고변동을 이번 작업에서 재확인한 것은 아니다. 대구는 군위 거래를 전 기간 제외한 경계다. 세종은 36110 코드로 확보된 이력이며 2006년 당시 행정구역 전체를 재구성한 것이 아니다.", "",
              "광주는 기존 입력에 유효거래·지원 가격지수가 없어 이번 분석에서 제외했다. 다른 수집 작업의 진행 상태를 이 분석의 확보 사실로 확대하지 않는다. 광주나 새 지역이 추가되면 입력 버전과 SHA가 다른 분석으로 다시 계산해야 한다. 지역별 원자료 수집 시점도 달라 신고·취소 수정 상태가 서로 다를 수 있다. 2026Q3 및 그 이후는 이번 분석에 포함하지 않았다.", "",
              "## v3 대본에 전달할 구체적인 해석", ""]
    seoul = by_region["서울"]
    lines += [
        f"- ‘서울의 최신값은 이 자체 지수의 전체 최고라 현재 낙폭은 0%입니다. 그렇다고 과거 하락이 없었던 것은 아닙니다. 전체 이력에서는 최대 {abs(seoul['max_historical_drawdown_pct']):.1f}% 하락이 관측됐습니다.’처럼 현재 위치와 과거 위험을 함께 말한다.",
        "- 2006년 출발선을 보여주는 6개 지역 화면과 2015년 출발선의 세종 화면을 분리한다. 세종의 짧은 관측기간에서 구한 CAGR을 같은 20년 수익률 순위로 제시하지 않는다.",
        "- `episodes.csv`의 장기 하락·완료 회복 사례를 함께 사용하면 2020년 이후의 한 주기만으로 지역을 규정하는 오류를 줄일 수 있다. 아래 설명용 주요 하락 목록에서 고점·저점·최초복귀를 그대로 인용할 수 있다.",
        "- ‘이 지역은 앞으로도 회복한다’, ‘고점까지 몇 년 남았다’, ‘공급·금리·일자리 때문에 이렇게 됐다’는 결론은 이 계산으로 입증되지 않는다. 이번 결과는 보유 표본 안에서 관측된 경로와 소요기간이다.",
        "- 거래량 합계는 가격지수를 만든 실제 매칭건수로 읽지 않는다. 수치는 보유 유효거래 전체와 매칭 표본의 지원 조건을 나누어 소개한다.", "",
        "### 설명용 주요 하락구간(최대낙폭 5% 이상)", "",
        "|지역|고점|관측 저점|최대 낙폭|최초복귀|고점→복귀 / 미회복 경과|", "|---|---|---|---:|---|---|",
    ]
    for e in episodes:
        if e["major_ge_5pct"]:
            length = f"{e['peak_to_observed_end_quarters']}분기 경과·관측종료" if e["right_censored"] else f"{e['peak_to_first_return_quarters']}분기"
            lines.append(f"|{e['region']}|{e['peak_quarter']}|{e['trough_quarter']}|{e['max_drawdown_pct']:.2f}%|{e['first_return_quarter'] or '미회복'}|{length}|")
    lines += ["", "## 재현과 검증", "",
              "실행: `tools/python311/python.exe -X utf8 analysis/housing_growth_2006/full_history_v1/analyze_full_history.py`.", "",
              "입력·기존 빌더·글꼴 SHA256은 `input_manifest.json`, 환경 버전과 산식은 `results.json`, 실제 곡선 값과 원본 행 위치는 `chart_source.csv`, 알고리즘 합성 사례와 실자료 구조 검사는 `validation.json`에 기록했다. 이미지의 데이터 근거는 모두 동결 CSV이며 AI 이미지는 사용하지 않았다.", "",
              "합성 검사는 단조 상승, 첫 회복 후 더 낮은 미래 저점, 고점 동률로 복귀, 고점/저점의 동률 처리, 미회복, 정확히 5% 하락, 마지막 분기 첫 하락을 포함한다. 실자료 검사는 분기 연속성·순서·중복, 기준분기와 연결 단지 수, 거래량/커버리지 합계, 첫 고점 교차, 저점의 구간 내 존재, 미회복 구간의 검열, 모든 하락 분기의 누락·중복을 확인한다.", "",
              "계산 내부 검증과 PNG 표본 검토는 별도 기록한다. 독립 QA와 공식 가격지수 대조·원자료 재검증은 총괄의 다음 단계이며 이 문서는 이를 완료했다고 주장하지 않는다."]
    (OUT / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    RESEARCH.mkdir(parents=True, exist_ok=True)
    files = [SOURCE / x for x in ("quarterly_index.csv", "quarterly_volume.csv", "analysis_coverage.csv", "results.json")]
    files += [BUILDER, FONT, Path(__file__).resolve()]
    manifest = [{"path": str(p) if p == FONT else rel(p), "sha256": sha(p), "bytes": p.stat().st_size,
                 "role": "font" if p == FONT else "source_script" if p == Path(__file__).resolve() else "definition_only_not_executed" if p == BUILDER else "frozen_aggregate_input"} for p in files]
    old = json.loads((SOURCE / "results.json").read_text(encoding="utf-8-sig"))
    assert old["endpoint"] == END and old["included_regions"] == ORDER
    synthetic = synthetic_checks()
    index = pd.read_csv(SOURCE / "quarterly_index.csv")
    volume = pd.read_csv(SOURCE / "quarterly_volume.csv")
    coverage = pd.read_csv(SOURCE / "analysis_coverage.csv")
    summaries, episodes, curves = analyze(index, volume, coverage)
    volume["year"] = volume.quarter.str[:4].astype(int)
    annual = volume.groupby(["region", "year"], sort=False).agg(valid_transactions=("transactions", "sum"), observed_quarters=("quarter", "size")).reset_index()
    annual["period_note"] = np.where(annual.year == 2026, "2026Q1~Q2·상반기", "Q1~Q4")
    assert (annual.observed_quarters == np.where(annual.year == 2026, 2, 4)).all()
    for name, frame in [("summary.csv", pd.DataFrame(summaries)), ("episodes.csv", pd.DataFrame(episodes)),
                        ("chart_source.csv", curves), ("annual_valid_volume.csv", annual)]:
        frame.to_csv(OUT / name, index=False, encoding="utf-8-sig")
    assets = plot_charts(curves, summaries, episodes)
    total = sum(r["full_valid_transaction_total"] for r in summaries)
    write_report(summaries, episodes, total)
    validation = {
        "status": "pass", "verified_at": CHECK_DATE, "synthetic_checks": synthetic,
        "checks": {"monotone_consecutive_quarter_chain": "pass", "no_future_trough": "pass",
                   "first_cross_ge_prior_high": "pass", "episode_censoring": "pass",
                   "all_underwater_quarters_accounted_once": "pass", "max_drawdown_matches_running_curve": "pass",
                   "quarterly_volume_equals_coverage": "pass", "matched_complex_link_support_ge30": "pass"},
        "input_rows": {"quarterly_index": len(index), "quarterly_volume": len(volume), "analysis_coverage": len(coverage)},
        "real_episode_count": len(episodes), "major_episode_count": sum(e["major_ge_5pct"] for e in episodes),
        "original_aggregate_inputs_and_builder_unchanged": all(sha(p) == m["sha256"] for p, m in zip(files, manifest)),
        "external_calls": 0, "raw_ingestion_runs": 0,
        "visual_review": "pending; actual PNG inspection recorded separately", "independent_qa": "not_performed_by_this_worker",
    }
    assert validation["original_aggregate_inputs_and_builder_unchanged"]
    save_json(OUT / "input_manifest.json", manifest)
    save_json(OUT / "validation.json", validation)
    result = {
        "analysis_id": "FULL-HISTORY-V1", "data_endpoint": END, "data_end_date": DATA_DATE,
        "verification_date": CHECK_DATE, "generated_at": datetime.now().astimezone().isoformat(),
        "input_revision": "regional_expansion_v1 frozen aggregates", "input_manifest": rel(OUT / "input_manifest.json"),
        "source_script": rel(Path(__file__).resolve()), "source_script_sha256": sha(Path(__file__).resolve()),
        "runtime": {"python": platform.python_version(), "pandas": pd.__version__, "numpy": np.__version__, "matplotlib": matplotlib.__version__},
        "regions": ORDER, "unavailable_regions_in_frozen_input": old["unavailable_regions"],
        "summaries": summaries, "episodes": episodes, "full_valid_transaction_total": total,
        "volume_scope": "보유·수집 범위 내 유효거래 전체; 전국 전수 또는 전 거래 가격 매칭을 의미하지 않음",
        "price_method_inherited": old["method"],
        "method": {"history": "각 지역의 전체 지원 연속 이력; 임의의 2020년 고점 창 없음", "all_time_high": "max of every supported quarter; first and last ties recorded",
                   "running_drawdown_pct": "100 * (index / cumulative_max(index) - 1)",
                   "episode": "last running-high touch before a decline through first subsequent value >= that high",
                   "trough": "first minimum strictly before first return, or through endpoint if right censored",
                   "duration": "quarter interval, not count of inclusive quarter observations; years=quarters/4",
                   "cagr": "100*((last/first)**(4/(last_quarter_ordinal-first_quarter_ordinal))-1)",
                   "major_threshold_pct": MAJOR_PCT, "major_threshold_use": "descriptive presentation label only; every episode retained",
                   "recovery_numeric_comparison": "strict >= prior high; no tolerance except 5pct display label",
                   "baseline_note": "first quarter is a reference value; matched_complexes is blank there"},
        "matched_transaction_count": None, "matched_transaction_count_reason": "Existing aggregates contain matched complexes, not matched transaction counts; raw data deliberately not read.",
        "limitations": ["공식 가격지수·투자수익률 아님", "가격 매칭표본은 유효거래 전체의 일부이며 매칭 거래건수·비율 산출 불가",
                        "세종은 2015Q1부터 가격지수 지원; 2006년부터의 거래량을 가격선으로 보간하지 않음",
                        "미회복 구간의 저점은 관측 종료일까지의 최저; 최종 회복일·기간·미래 경로 알 수 없음",
                        "관측 최초 분기 이전 고점·하락은 미관측", "분기별 표본 변화 및 동·층·수리 상태 미통제",
                        "지역별 원자료 수집 시점과 취소 수정 상태가 다를 수 있음", "대구 군위 전 기간 제외, 세종 36110 코드 범위",
                        "광주 미확보는 동결 입력의 상태이며 다른 담당 수집 결과를 반영하지 않음",
                        "기존 결과의 2020~2022년 기준 고점·저점·회복일은 사용하지 않음", "이번 분석만으로 공급·금리·일자리의 인과효과나 향후 회복기간을 판단할 수 없음"],
        "validation": rel(OUT / "validation.json"), "charts": [rel(p) for p in assets],
        "chart_data": rel(OUT / "chart_source.csv"), "annual_volume": rel(OUT / "annual_valid_volume.csv"),
    }
    save_json(OUT / "results.json", result)
    write_handoff(result, manifest)
    print(json.dumps({"status": "pass", "output": rel(OUT), "research": rel(RESEARCH), "episodes": len(episodes),
                      "major_episodes": validation["major_episode_count"], "valid_transactions": total,
                      "summary": [{k: r[k] for k in ("region", "full_period_cumulative_change_pct", "full_period_cagr_pct", "max_historical_drawdown_pct", "latest_vs_all_time_high_pct", "longest_completed_recovery_quarters")} for r in summaries]}, ensure_ascii=False, indent=2))


def write_handoff(result, manifest):
    facts = []
    for r in result["summaries"]:
        facts.append({
            "claim_id": f"FH-V1-{ORDER.index(r['region']) + 1:02d}",
            "sentence": f"{r['region']}의 {r['price_start_quarter']}~{END} 자체 가격지수 누적 변화는 {r['full_period_cumulative_change_pct']:+.2f}%, 연환산 {r['full_period_cagr_pct']:.2f}%, 전체 최고 대비 최신값은 {r['latest_vs_all_time_high_pct']:.2f}%, 역사적 최대 낙폭은 {r['max_historical_drawdown_pct']:.2f}%다. 관측이 완료된 최장 고점→최초복귀는 {r['longest_completed_recovery_peak_quarter']}→{r['longest_completed_recovery_return_quarter']}의 {r['longest_completed_recovery_quarters']}분기다.",
            "original_source_file": rel(SOURCE / "quarterly_index.csv"), "original_source_url": None,
            "evidence_location": f"region={r['region']}, quarter={r['price_start_quarter']}..{END}; summary.csv region={r['region']}; episodes.csv 해당 지역",
            "data_as_of": DATA_DATE, "verified_at": CHECK_DATE, "status": "qualified",
            "verification_scope": "동결 집계에서 산술·구간 탐지 검증; 원자료·공식 지수 대조는 이번 범위 밖",
            "price_statistic": "단지·면적별 ㎡당 분기 중위가격의 로그변화율을 단지 내 평균 후 단지 동일 가중으로 연결",
            "region_scope": r["region"] + ("·군위 제외" if r["region"] == "대구" else "·36110 코드" if r["region"] == "세종" else ""),
            "exclusive_area_m2": "고정면적 아님; 동일 전용면적 0.01㎡ 반올림 매칭",
            "trade_period": f"{r['price_start_quarter']}~{END}", "trade_type": "아파트 매매·기존 RTMS 파생 집계",
            "unit": "지수 포인트·%·분기", "sample": {"valid_trades_in_index_period_not_matched_count": r["valid_transactions_within_price_index_dates"],
                                                        "min_matched_complexes_per_link": r["min_link_matched_complexes"], "latest_matched_complexes": r["latest_link_matched_complexes"], "matched_trade_count": None},
            "cancellation_treatment": "기존 빌더의 취소 표시 제외·해시 중복 제거; 신규 정규화는 동일 키 취소 우선. 이번에 원본 재검증하지 않음",
            "comparison_conditions": "6개 지역은 20.25년, 세종은 11.25년. 공식 지수·투자수익률 아님. 매칭 거래 수는 기존 입력으로 미확인.",
        })
    facts.append({"claim_id": "FH-V1-VOLUME", "sentence": f"보유 자료의 2006Q1~2026Q2 7개 지역 유효거래 합계는 {result['full_valid_transaction_total']:,}건이나, 가격지수에 모든 거래가 매칭됐다는 뜻은 아니다.",
                  "original_source_file": [rel(SOURCE / "quarterly_volume.csv"), rel(SOURCE / "analysis_coverage.csv")],
                  "evidence_location": "전체 지역 transactions 합계 및 analysis_coverage와 동일성 검사", "data_as_of": DATA_DATE,
                  "verified_at": CHECK_DATE, "status": "qualified", "unit": "건", "matched_trade_count": None})
    save_json(RESEARCH / "facts.json", {"analysis_id": "FULL-HISTORY-V1", "claims": facts})
    save_json(RESEARCH / "issue_FH-V1-SCRIPT-SCOPE.json", {
        "issue_id": "FH-V1-SCRIPT-SCOPE", "scene_ids": [], "scene_id_status": "v3 공통 장면표 미배정; 총괄 매핑 필요",
        "affected_claim_ids": [f["claim_id"] for f in facts], "affected_scene_ids": [],
        "problem": "v3는 2020년 이후 한 주기에서 전체 가용 이력으로 범위를 확대해야 함. 최신 고점 대비 0%를 과거 하락 부재로 읽으면 오류.",
        "evidence": [rel(OUT / "summary.csv"), rel(OUT / "episodes.csv"), rel(OUT / "report.md")],
        "proposal": "6개 지역 2006Q1~, 세종 2015Q1~를 분리하고 전체 누적·최대낙폭·모든 과거 회복구간을 설명. 거래량 전체와 가격 매칭 표본을 분리.",
        "impact": "v3 장기 가격·회복 설명 및 그래프. v1/v2 원본과 공통 상태를 수정하지 않음. 인과·향후 회복 예측 근거로 확대 금지.",
        "to": ["director", "writer", "visual", "qa"], "status": "proposed_for_parent_integration",
    })
    (RESEARCH / "writer_notes.md").write_text(
        "# v3 전달 사항\n\n기준일은 2026Q2입니다. 전체 결과와 인용 가능한 주요 하락구간은 "
        f"`{rel(OUT / 'report.md')}`에 있습니다.\n\n"
        "6개 지역은 2006Q1부터, 세종은 2015Q1부터만 가격지수가 지원됩니다. 최신 고점 거리 0%와 과거 하락 부재를 구별하세요. "
        "미회복은 관측 종료이지 미래 회복기간의 추정이 아닙니다. 거래량 전체를 실제 가격 매칭 건수로 말하지 마세요. "
        "공급·일자리·금리의 인과효과나 향후 경로는 이 분석으로 검증되지 않았습니다.\n\n"
        "곡선 값은 chart_source.csv의 source_file·source_row_number_including_header로 원본과 연결됩니다. "
        "광주 등 새 수집 결과는 총괄이 별도 버전으로 반영해야 합니다. 독립 QA와 공식 지수 대조는 미완료입니다.\n", encoding="utf-8")
    save_json(RESEARCH / "handoff.json", {
        "task_id": "FULL-HISTORY-V1", "role": "research", "status": "computed_internal_checks_pass_independent_qa_pending",
        "input_revisions": {"revision": "regional_expansion_v1 frozen", "manifest": rel(OUT / "input_manifest.json")},
        "output_directory": rel(OUT), "chart_paths": result["charts"],
        "outputs": [rel(OUT / p) for p in ("analyze_full_history.py", "summary.csv", "episodes.csv", "results.json", "report.md", "chart_source.csv", "validation.json")] + [rel(RESEARCH / "facts.json")],
        "affected_scene_ids": [], "scene_mapping": "v3 미배정·총괄 확인", "checks": [{"check": "7개 합성사례·실자료 구조/회복 검사", "result": "pass", "evidence": rel(OUT / "validation.json")}],
        "open_issue_ids": ["FH-V1-SCRIPT-SCOPE"], "next_role": ["director", "writer", "visual", "independent_qa"],
        "unresolved": ["매칭 거래건수 미제공", "공식 지수 대조·독립 QA 미완료", "추가 지역 수집은 총괄 소관"],
        "summary": "2006Q1부터 6개 지역, 세종 2015Q1부터 전체 이력 분석. 특정 고점 창 없이 모든 하락/최초복귀 산출. 미회복 기간 검열 표시. 외부 호출·원자료 수집·공통 상태/대본 편집 없음.",
    })


if __name__ == "__main__":
    main()
