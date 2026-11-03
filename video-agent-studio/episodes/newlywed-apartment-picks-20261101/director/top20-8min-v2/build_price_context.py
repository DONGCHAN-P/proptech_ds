"""Attach matched-area historical sale context without substituting asking prices."""
import csv
import gzip
import hashlib
import json
from pathlib import Path

import duckdb

EP = Path(__file__).resolve().parents[2]
ROOT = Path(__file__).resolve().parents[5]
OUT = EP / "research/top20-8min-v2"


def main():
    top = json.loads((OUT / "top20.json").read_text(encoding="utf-8"))["regions"]
    geo = json.loads(gzip.decompress((OUT / "source/HangJeongDong_ver20241001.geojson.gz").read_bytes()))
    codes = {}
    for f in geo["features"]:
        p = f["properties"]
        if p["sido"] in {"11","28","41"}:
            province = {"11":"서울","28":"인천","41":"경기"}[p["sido"]]
            codes[(province,p["sggnm"].replace(" ",""))] = p["sgg"]
    bridge = []
    for r in top:
        code = codes[(r["province"],r["region"].replace(" ",""))]
        current = ["28275","28290"] if r["province"] == "인천" and r["region"] == "서구" else [code]
        for c in current:
            bridge.append((r["region_id"],c))
        r["statistical_region_code_2024"] = code
        r["current_cache_codes"] = current
    conn = duckdb.connect()
    conn.execute("CREATE TABLE region_bridge(region_id VARCHAR, sigungu_code VARCHAR)")
    conn.executemany("INSERT INTO region_bridge VALUES (?,?)",bridge)
    apt = (ROOT / "web/cache/apt_index.parquet").as_posix()
    trades = (ROOT / "web/cache/trades.parquet").as_posix()
    rows = conn.execute(f"""
      SELECT b.region_id,
        CASE WHEN t.area_m2>=59 AND t.area_m2<60 THEN '59' ELSE '84' END AS area_band,
        count(*) AS n, count(DISTINCT a.apt_id) AS complex_count,
        median(t.deal_amount) AS median_manwon,
        quantile_cont(t.deal_amount,0.25) AS p25_manwon,
        quantile_cont(t.deal_amount,0.75) AS p75_manwon,
        min(t.deal_date)::DATE AS first_contract, max(t.deal_date)::DATE AS last_contract
      FROM read_parquet('{trades}') t
      JOIN read_parquet('{apt}') a USING(apt_id)
      JOIN region_bridge b USING(sigungu_code)
      WHERE t.deal_date>=DATE '2026-04-01' AND t.deal_date<DATE '2026-10-01'
        AND t.floor>=3 AND t.deal_amount>0
        AND ((t.area_m2>=59 AND t.area_m2<60) OR (t.area_m2>=84 AND t.area_m2<85))
      GROUP BY 1,2 ORDER BY 1,2
    """).fetchdf()
    aggs = json.loads(rows.to_json(orient="records",force_ascii=False,date_format="iso"))
    for row in aggs:
        row["first_contract"] = row["first_contract"][:10]
        row["last_contract"] = row["last_contract"][:10]
        row["publishable_sample_threshold_passed"] = row["n"] >= 20
        row["evidence_type"] = "historical_regional_transaction_distribution"
    assert len(aggs) == 40
    mapping = {r["region_id"]:r for r in top}
    full = [{"rank":mapping[x["region_id"]]["rank"],"province":mapping[x["region_id"]]["province"],
             "region":mapping[x["region_id"]]["region"],**x} for x in aggs]
    payload = {"revision":"top20-8min-v2","contract_window":["2026-04-01","2026-09-30"],
      "cache_max_contract_date":"2026-10-05","area_bands":["59<=exclusive_m2<60","84<=exclusive_m2<85"],
      "floor":">=3","unit":"만원","minimum_display_n":20,
      "meaning":"단지·연식·층 등 구성이 섞인 지역 내 관측 거래 분포. 신혼부부 실제 매입가격·현재 광고호가·동일주택 가격상승률과 별개로 활용.",
      "cancellations":"cache built from master WHERE NOT is_canceled; late cancellations require refresh before final publication",
      "type_filter":"brokered/direct flag not present in cache; no direct-transfer exclusion claimed",
      "source_snapshots":[{"path":str(Path(p).relative_to(ROOT)),"sha256":hashlib.sha256(Path(p).read_bytes()).hexdigest()} for p in [apt,trades]],
      "geography_crosswalk":[{k:r[k] for k in ["region_id","province","region","statistical_region_code_2024","current_cache_codes"]} for r in top],
      "rows":full}
    (OUT / "price_context.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    with (OUT / "price_context.csv").open("w",encoding="utf-8-sig",newline="") as f:
        writer = csv.DictWriter(f,fieldnames=list(full[0]));writer.writeheader();writer.writerows(full)
    summary = {"regions":len(top),"sample_rows":len(full),"all_n_at_least20":all(r["n"]>=20 for r in full),
       "top20_couples_sum":sum(r["newlywed_couples"] for r in top),
       "province_region_counts":{p:sum(r["province"]==p for r in top) for p in ["서울","경기","인천"]},
       "R10_R11_count_difference":top[9]["newlywed_couples"]-top[10]["newlywed_couples"],
       "representative_59":[r for r in full if r["area_band"]=="59" and r["region_id"] in ["R01","R02","R03","R06","R20"]]}
    (OUT / "derived_insights_seed.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__ == "__main__":
    main()
