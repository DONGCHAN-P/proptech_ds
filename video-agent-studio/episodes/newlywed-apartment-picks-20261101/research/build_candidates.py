"""Build auditable research candidates; outputs are historical transactions, not listings."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def main() -> None:
    connection = duckdb.connect()
    apt = (ROOT / "web/cache/apt_index.parquet").as_posix()
    trades = (ROOT / "web/cache/trades.parquet").as_posix()
    # Current code crosswalk: 2024 Incheon Seo-gu -> the 2026 split areas.
    # Codes are observed in the local serving cache; official name/geometry
    # confirmation remains a separate source check, never inferred from a name.
    selected = connection.execute(f"""
        SELECT a.apt_id, a.apt_name, a.sigungu_code, a.sigungu_name, a.legal_dong_name,
               a.road_address, a.lat, a.lng, a.build_year,
               CASE WHEN t.area_m2 >= 59 AND t.area_m2 < 60 THEN '59'
                    WHEN t.area_m2 >= 84 AND t.area_m2 < 85 THEN '84' END AS area_band,
               count(*) AS n, min(t.deal_date)::DATE AS first_contract,
               max(t.deal_date)::DATE AS last_contract,
               min(t.area_m2) AS area_min_m2, max(t.area_m2) AS area_max_m2,
               median(t.deal_amount) AS median_manwon,
               count(*) FILTER (WHERE t.deal_date >= DATE '2026-07-01') AS q3_n,
               median(t.deal_amount) FILTER (WHERE t.deal_date >= DATE '2026-07-01') AS q3_median_manwon,
               min(t.deal_amount) AS min_manwon, max(t.deal_amount) AS max_manwon,
               min(t.floor) AS floor_min, max(t.floor) AS floor_max
        FROM read_parquet('{trades}') t
        JOIN read_parquet('{apt}') a USING (apt_id)
        WHERE a.sigungu_code IN ('28275','28290')
          AND t.deal_date >= DATE '2026-04-01' AND t.deal_date < DATE '2026-10-01'
          AND t.deal_amount > 0 AND t.floor >= 3
          AND ((t.area_m2 >= 59 AND t.area_m2 < 60) OR (t.area_m2 >= 84 AND t.area_m2 < 85))
        GROUP BY ALL HAVING count(*) >= 5
        ORDER BY area_band, median_manwon, n DESC, a.apt_id
    """).fetchdf()
    rows = json.loads(selected.to_json(orient="records", force_ascii=False, date_format="iso"))
    for row in rows:
        for field in ["first_contract", "last_contract"]:
            row[field] = row[field][:10]
        row["evidence_type"] = "historical_transaction_aggregate"
        row["listing_verification"] = "pending"
    (HERE / "transaction_candidates.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    with (HERE / "transaction_candidates.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    metadata = {
        "contract_window": ["2026-04-01", "2026-09-30"], "area_bands": ["59<=exclusive_m2<60", "84<=exclusive_m2<85"],
        "floor": ">=3", "minimum_n": 5, "statistic": "raw transaction median per apartment and area band",
        "cancellation": "web/build_index.py build_trades selects NOT is_canceled from source master; late cancellations require refresh before publication",
        "transaction_type": "local cache does not expose direct/brokered flag; no brokered-only filter claimed",
        "q3_sensitivity": "2026-07-01~09-30 subset, same area/floor filters; eligibility remains six-month n>=5. Display Q3 median only with its own n, and do not promote a low-n subset to a confirmed price level.",
        "cache_max_contract_date": str(connection.execute(f"SELECT max(deal_date)::DATE FROM read_parquet('{trades}')").fetchone()[0]),
        "candidate_rows": len(rows), "candidate_complexes": len({r["apt_id"] for r in rows}),
        "scope": "Local cache 28275/28290, connected to 2024 Seo-gu as a research grouping; administrative crosswalk to be independently verified.",
        "source_files": [{"path": str(Path(p).relative_to(ROOT)), "sha256": hashlib.sha256(Path(p).read_bytes()).hexdigest()} for p in [apt, trades]],
        "known_gaps": ["매물 호가·판매 상태·동향·수리·입주 가능일", "면적별 주택형/평면·관리비", "현재 역 출입구 기준 도보 경로·운영 상태", "신혼부부의 실제 단지 거주 또는 선택 이유"],
    }
    (HERE / "candidate_method.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    for band in ["59", "84"]:
        values = [r for r in rows if r["area_band"] == band]
        popular = sorted(values, key=lambda r: -r["n"])[:15]
        print(json.dumps({"area_band": band, "eligible_rows": len(values), "most_observed": [
            {k: r[k] for k in ["apt_id", "apt_name", "sigungu_code", "legal_dong_name", "build_year", "median_manwon", "n"]} for r in popular]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
