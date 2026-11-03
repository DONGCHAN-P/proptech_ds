"""ALL-VALID-TRANSACTIONS-V1: frozen-cache descriptive levels, no matched filter."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager, ticker
import numpy as np
import pandas as pd
import pyarrow
import pyarrow.parquet as pq

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
BASE = ROOT / "analysis/housing_growth_2006/regional_expansion_v1"
ORDER = ["서울", "경기", "인천", "부산", "대구", "대전", "세종"]
QUARTERS = pd.period_range("2006Q1", "2026Q2", freq="Q")
# area_m2_key is recomputed below; no unused master columns are loaded.
COLS = ["apt_id", "deal_date", "sigungu_code", "deal_amount", "area_m2", "is_canceled", "deal_hash"]
PATHS = {
    "master": ROOT / "master/trade_events.parquet",
    "expansion": BASE / "expansion_normalized.parquet",
    "frozen_coverage": BASE / "analysis_coverage.csv",
    "frozen_quarterly_volume": BASE / "quarterly_volume.csv",
    "cleaning_reference": BASE.parent / "regional_expansion_v1.py",
    "cache_normalization_audit": BASE / "normalization.json",
    "analysis_script": Path(__file__).resolve(),
}


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def save_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def main():
    manifest = {}
    for name, path in PATHS.items():
        stat = path.stat()
        manifest[name] = dict(path=path.relative_to(ROOT).as_posix(), sha256=sha256(path),
                              bytes=stat.st_size, mtime_ns=stat.st_mtime_ns)
    master = pq.read_table(PATHS["master"], columns=COLS).to_pandas()
    master["region"] = master.sigungu_code.str[:2].map({"11": "서울", "41": "경기", "28": "인천"})
    assert master.region.notna().all(), "Master scope changed; overlap review required"
    expansion = pq.read_table(PATHS["expansion"], columns=COLS + ["region"]).to_pandas()
    data = pd.concat([master, expansion], ignore_index=True)
    audit = {"master_cache_rows": len(master), "expansion_cache_rows": len(expansion), "combined_cache_rows": len(data)}
    del master, expansion
    # Exact filtering/order from regional_expansion_v1.py:81-94; never import it.
    data["area_m2_key"] = data.area_m2.round(2)
    keep = (~data.is_canceled.fillna(False) & (data.deal_amount > 0)
            & (data.area_m2 > 0) & data.apt_id.notna())
    audit["cached_cancellation_flag_true_rows"] = int(data.is_canceled.fillna(False).sum())
    audit["cached_cancellation_flag_null_rows"] = int(data.is_canceled.isna().sum())
    audit["removed_by_combined_validity_filter"] = int((~keep).sum())
    data = data[keep].copy()
    before = len(data)
    data = data.drop_duplicates("deal_hash").copy()
    audit["duplicate_hashes_removed_after_validity_filter"] = before - len(data)
    data["quarter"] = data.deal_date.dt.to_period("Q")
    before = len(data)
    data = data[data.quarter.between(QUARTERS[0], QUARTERS[-1])].copy()
    audit["outside_quarter_window_removed"] = before - len(data)
    gunwi = data.sigungu_code.isin(["27720", "47720"])
    audit["gunwi_27720_47720_removed"] = int(gunwi.sum())
    data = data[~gunwi].copy()
    data["ppm"] = data.deal_amount / data.area_m2
    assert set(data.region.unique()) == set(ORDER)
    assert data.deal_hash.is_unique and np.isfinite(data.ppm).all()

    coverage = data.groupby("region").agg(transactions=("ppm", "size"), complexes=("apt_id", "nunique"),
                                           first_date=("deal_date", "min"), last_date=("deal_date", "max"))
    frozen = pd.read_csv(PATHS["frozen_coverage"], parse_dates=["first_date", "last_date"]).set_index("region")
    pd.testing.assert_frame_equal(coverage.sort_index(), frozen.sort_index(), check_dtype=False, check_freq=False)
    assert int(coverage.transactions.sum()) == 6_640_041
    group = data.groupby(["region", "quarter"])
    quarterly = group.agg(n=("ppm", "size"), complexes=("apt_id", "nunique"),
                          median_deal_amount_manwon=("deal_amount", "median"), median_area_m2=("area_m2", "median"),
                          median_price_per_m2_manwon=("ppm", "median"))
    quartiles = group.ppm.quantile([0.25, 0.75], interpolation="linear").unstack()
    quarterly["p25_price_per_m2_manwon"] = quartiles[0.25]
    quarterly["p75_price_per_m2_manwon"] = quartiles[0.75]
    # Optional narrow-area illustration: still subject to changing location/age mix.
    area84 = data[(data.area_m2 >= 84) & (data.area_m2 < 85)].groupby(["region", "quarter"]).agg(
        area84_85_n=("ppm", "size"), area84_85_median_deal_amount_manwon=("deal_amount", "median"),
        area84_85_median_price_per_m2_manwon=("ppm", "median"))
    quarterly = quarterly.join(area84)
    quarterly["area84_85_n"] = quarterly.area84_85_n.fillna(0).astype("int64")
    quarterly = quarterly.reset_index()
    quarterly["quarter"] = quarterly.quarter.astype(str)
    old_volume = pd.read_csv(PATHS["frozen_quarterly_volume"])
    actual_volume = quarterly[["region", "quarter", "n", "complexes"]].rename(columns={"n": "transactions"})
    pd.testing.assert_frame_equal(actual_volume.sort_values(["region", "quarter"]).reset_index(drop=True),
                                  old_volume.sort_values(["region", "quarter"]).reset_index(drop=True), check_dtype=False)
    assert quarterly.groupby("region").n.sum().sort_index().equals(coverage.transactions.sort_index())
    assert (quarterly.p25_price_per_m2_manwon <= quarterly.median_price_per_m2_manwon).all()
    assert (quarterly.median_price_per_m2_manwon <= quarterly.p75_price_per_m2_manwon).all()
    quarterly.to_csv(OUT / "quarterly_all_valid_transactions.csv", index=False, encoding="utf-8-sig", float_format="%.12g")
    endpoints = []
    for region in ORDER:
        s = quarterly[quarterly.region == region].sort_values("quarter")
        endpoints.append(dict(region=region, transactions=int(coverage.loc[region, "transactions"]),
                              complexes=int(coverage.loc[region, "complexes"]),
                              first_date=str(coverage.loc[region, "first_date"].date()),
                              last_date=str(coverage.loc[region, "last_date"].date()), quarters=len(s),
                              first=s.iloc[0].drop("region").to_dict(), latest=s.iloc[-1].drop("region").to_dict()))
    sejong_early = data[(data.region == "세종") & (data.quarter <= pd.Period("2014Q4"))]
    early_audit = dict(transactions=len(sejong_early), complexes=int(sejong_early.apt_id.nunique()),
                       sigungu_code_counts={str(k): int(v) for k, v in sejong_early.sigungu_code.value_counts().items()},
                       interpretation="캐시의 36110 재매핑 가능 초기 기록; 과거 세종시 전체의 완전한 지역 포괄을 뜻하지 않음")
    del data

    font = Path(font_manager.findfont("Malgun Gothic", fallback_to_default=False))
    plt.rcParams.update({"font.family": "Malgun Gothic", "axes.unicode_minus": False, "svg.fonttype": "path"})

    def plot(regions, stem, sejong=False):
        fig, axes = plt.subplots(1 if sejong else 3, 1 if sejong else 2,
                                 figsize=(11, 5.3) if sejong else (13, 10.5), sharex=True, sharey=not sejong)
        x = np.arange(len(QUARTERS))
        top = float(quarterly[quarterly.region.isin(regions)].p75_price_per_m2_manwon.max()) * 1.08
        for ax, region in zip(np.atleast_1d(axes).flat, regions):
            s = quarterly[quarterly.region == region].set_index("quarter").reindex(QUARTERS.astype(str))
            ax.fill_between(x, s.p25_price_per_m2_manwon.to_numpy(), s.p75_price_per_m2_manwon.to_numpy(),
                            color="#cbdde8", alpha=0.65)
            ax.plot(x, s.median_price_per_m2_manwon, color="#125278", linewidth=2)
            ax.set_title(region if not sejong else "세종 · 캐시에 수록된 전체 유효 거래", loc="left", fontsize=13, weight="bold")
            ax.set_ylim(0, top)
            ax.set_xlim(0, len(QUARTERS) - 1)
            ax.yaxis.set_major_formatter(ticker.StrMethodFormatter("{x:,.0f}"))
            ticks = [0, 16, 32, 48, 64, 81]
            ax.set_xticks(ticks, ["2006", "2010", "2014", "2018", "2022", "2026Q2"])
            ax.grid(axis="y", color="#dce2e5", linewidth=0.7)
            ax.spines[["top", "right"]].set_visible(False)
            ax.text(0.02, 0.94, f"전체 기간 {int(coverage.loc[region, 'transactions']):,}건", transform=ax.transAxes, va="top", fontsize=10)
            if sejong:
                ax.axvspan(-0.5, 35.5, color="#efc174", alpha=0.22)
                ax.axvline(35.5, color="#b28742", linestyle="--", linewidth=1)
                ax.text(0.02, 0.83, "2006~2014: 36110 재매핑 가능 기록\n과거 도시 전체 포괄이 완전한 이력이 아님", transform=ax.transAxes, va="top", fontsize=10)
        fig.suptitle("분기별 아파트 거래가격 수준 · 전용면적 1㎡당 중위가격", x=0.08, ha="left", fontsize=17, weight="bold")
        fig.supylabel("만원/㎡ · 명목금액", x=0.015, fontsize=11)
        fig.text(0.08, 0.08 if sejong else 0.065,
                 "선: 개별 거래의 ㎡당 가격 중위값   음영: 25~75백분위 범위   |   2006Q1~2026Q2\n"
                 "캐시의 유효 거래 전체 · 분기별 거래 구성 변화 포함 · 동일 품질 가격지수·투자수익률로 해석 불가\n"
                 "출처: 기존 master + regional_expansion_v1 정규화 캐시 · 해제 여부는 캐시 플래그 기준",
                 fontsize=9, va="bottom", linespacing=1.6)
        fig.subplots_adjust(left=0.09, right=0.97, bottom=0.28 if sejong else 0.17, top=0.82 if sejong else 0.91, hspace=0.32)
        for suffix in ("png", "svg"):
            fig.savefig(OUT / f"{stem}.{suffix}", dpi=180, facecolor="white")
        plt.close(fig)

    plot(ORDER[:-1], "quarterly_median_price_per_m2_six_regions_2006")
    plot(["세종"], "quarterly_median_price_per_m2_sejong_cache_history", sejong=True)
    for name, path in PATHS.items():
        stat = path.stat()
        assert (stat.st_size, stat.st_mtime_ns) == (manifest[name]["bytes"], manifest[name]["mtime_ns"]), f"Input changed during run: {name}"
    notes = [
        "전체 유효 거래는 지정된 두 캐시에서 정제 조건을 통과한 거래 전체를 뜻하며, 전국·모든 신고 거래의 완전 수집을 뜻하지 않는다.",
        "지역·분기별 개별 거래에 동일 가중치. ㎡당 가격=거래금액(만원)/전용면적(㎡)을 먼저 계산하고 중위값·25/75백분위를 산출한다. 중위 거래금액/중위 면적의 비율이 아니다.",
        "면적·입지·연식·신축/구축·단지의 거래 비중이 바뀌면 중위가격이 달라진다. 84≤전용면적<85㎡ 보조 통계도 입지·연식 구성을 통제하지 않는다.",
        "명목금액 수준이며 물가 조정을 하지 않았다. 동일 품질 가격지수·주택 보유 수익률·투자수익률로 해석할 수 없다. 기존 매칭 지수에 보완적으로 사용한다.",
        "해제거래 처리는 캐시 is_canceled 플래그(null=False) 감사 범위다. 확장 캐시의 기존 정규화 기록은 동일 hash의 해제 상태를 max로 전파했다고 기록한다. 이번 작업은 원본 XML·최신 신고 정정·해제 누락을 재확인하지 않았다.",
        "기간은 2006Q1~2026Q2(2026-06-30)로 고정했다. 마지막 분기는 Q2이고 2026년 연간치·현재 분기·확정된 영구 최종치가 아니다. 캐시 이후 신고·해제 반영은 검증하지 않았다.",
        "대구는 군위 27720/47720을 제외한 고정 경계다. 세종 초기 기록은 36110 재매핑 가능 기록을 포함하므로 별도 패널에 표시하며 역사적 도시 전체 포괄을 보장하지 않는다.",
    ]
    checks = dict(region_totals_equal_frozen=True, region_complexes_and_dates_equal_frozen=True,
                  quarterly_counts_and_complexes_equal_frozen=True, total_equal_6640041=True,
                  total_valid_transactions=int(coverage.transactions.sum()), quarterly_rows=len(quarterly),
                  unique_region_quarters=not quarterly.duplicated(["region", "quarter"]).any(),
                  quantile_order_valid=True, inputs_stat_unchanged_during_run=True)
    result = dict(task_id="ALL-VALID-TRANSACTIONS-V1", checked_at=datetime.now(timezone.utc).isoformat(),
                  period=dict(first="2006Q1", endpoint="2026Q2", endpoint_date="2026-06-30"),
                  input_manifest=manifest, loaded_columns=dict(master=COLS, expansion=COLS + ["region"]),
                  environment=dict(python=sys.version.split()[0], pandas=pd.__version__, pyarrow=pyarrow.__version__,
                                   numpy=np.__version__, matplotlib=matplotlib.__version__, font_path=str(font), font_sha256=sha256(font)),
                  cleaning_reference="regional_expansion_v1.py:81-99; same order, cached inputs only",
                  cache_filter_audit=audit, normalization_audit=json.loads(PATHS["cache_normalization_audit"].read_text(encoding="utf-8")),
                  validation=checks, region_summary=endpoints, sejong_2006_2014_cache_audit=early_audit,
                  quantile_method="pandas quantile interpolation=linear", notes=notes,
                  verification_scope="자체 검산·산출물 기술 확인. 독립 QA·원 XML 재검증·영상 재생·음성 청취 미실시.")
    # JSON must contain ordinary Python scalars, including validation flags.
    result["validation"]["unique_region_quarters"] = bool(checks["unique_region_quarters"])
    save_json(OUT / "results.json", result)
    lines = ["# 전체 유효 거래의 분기별 가격 수준", "",
             f"고정 캐시 정제 후 **6,640,041건**. 7개 지역별 거래 수·단지 수·최초/최종일과 모든 분기의 거래 수·단지 수가 기존 고정 집계와 일치했다. 분기 관측 {len(quarterly):,}행. 동일 단지·면적의 재거래 매칭 또는 최소 거래 수 필터를 추가하지 않았다.", "",
             "|지역|전체 거래 수|최초 분기|최초 중위가격(만원/㎡)|마지막 분기|마지막 중위가격(만원/㎡)|최초→마지막 중위면적(㎡)|", "|---|---:|---|---:|---|---:|---:|"]
    for item in endpoints:
        first, last = item["first"], item["latest"]
        lines.append(f"|{item['region']}|{item['transactions']:,}|{first['quarter']}|{first['median_price_per_m2_manwon']:,.2f}|{last['quarter']}|{last['median_price_per_m2_manwon']:,.2f}|{first['median_area_m2']:g}→{last['median_area_m2']:g}|")
    lines += ["", "CSV는 지역·분기별 거래 수, 단지 수, 중위 거래금액(만원), 중위 전용면적(㎡), 거래별 ㎡당 가격의 중위값·25/75백분위(만원/㎡), 84≤면적<85㎡ 보조 표본 수·중위금액·중위 ㎡당 가격을 담는다.", ""]
    lines += [f"- {note}" for note in notes]
    lines += ["", f"세종 2006~2014 캐시 표본: {early_audit['transactions']:,}건, {early_audit['complexes']:,}단지, 지역코드별 건수 {early_audit['sigungu_code_counts']}. 초기 관측의 존재와 도시 전체의 과거 포괄성은 구별한다.", "",
              "6개 지역 그래프는 동일한 0 시작 금액 축을 사용한다. 세종은 별도 그래프다. 음영은 거래가격 분포의 25~75백분위로, 신뢰구간이 아니다.", "",
              "[6개 지역 PNG](quarterly_median_price_per_m2_six_regions_2006.png) · [SVG](quarterly_median_price_per_m2_six_regions_2006.svg) · [세종 PNG](quarterly_median_price_per_m2_sejong_cache_history.png) · [세종 SVG](quarterly_median_price_per_m2_sejong_cache_history.svg) · [분기 CSV](quarterly_all_valid_transactions.csv) · [입력 SHA256·검증·끝점 수치](results.json)", "",
              "검증 범위: 직접 실행한 캐시 재집계와 자동 검산. 독립 QA·원 XML 재검증·신규 API 조회는 수행하지 않았다. 대본 v3 연결과 독립 검수는 총괄에게 인계한다."]
    (OUT / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(dict(total=6_640_041, checks=checks, endpoints=[
        dict(region=i["region"], n=i["transactions"], first=i["first"]["median_price_per_m2_manwon"],
             latest=i["latest"]["median_price_per_m2_manwon"]) for i in endpoints]), ensure_ascii=False))


if __name__ == "__main__":
    main()
