"""Normalize the two bounded research packets and preserve claim provenance."""
import csv
import hashlib
import json
from pathlib import Path

EP=Path(__file__).resolve().parents[2]
OUT=EP/"research/top20-8min-v2"


def main():
    top=json.loads((OUT/"top20.json").read_text(encoding="utf-8"))["regions"]
    packets=[OUT/"ranks01_10_facts.json",OUT/"ranks11_20_facts.json"]
    research={r["region_id"]:r for p in packets for r in json.loads(p.read_text(encoding="utf-8"))["regions"]}
    extra_path=OUT/"supplemental_facts.json"
    if extra_path.exists():
        for extra in json.loads(extra_path.read_text(encoding="utf-8"))["regions"]:
            research[extra["region_id"]]["facts"].extend(extra["facts"])
            research[extra["region_id"]]["sources"].extend(extra["sources"])
    prices=json.loads((OUT/"price_context.json").read_text(encoding="utf-8"))["rows"]
    sources={}
    regions=[]
    for r in top:
        item=research[r["region_id"]]
        count2023=item["count2023"]
        previous=count2023.get("value") if isinstance(count2023,dict) else count2023
        delta=None if previous is None else r["newlywed_couples"]-previous
        rate=None if previous is None else delta/previous*100
        for source in item.get("sources",[]):
            url=source.get("url",source.get("source_url"))
            if url:
                sources[url]=source
        source_packet=packets[0] if r["rank"]<=10 else packets[1]
        regions.append({**r,"count2023":previous,"count2024":r["newlywed_couples"],
          "change_couples":delta,"change_percent":rate,"change_percent_display":None if rate is None else round(rate,1),
          "comparison_available":previous is not None,
          "comparison_note": "2023 원표는 부천시 전체를 공표.2024복원 원미구 동일범위값을 대체하지 않음" if previous is None else "동일 명칭의2023/2024 공표 거주규모 비교; 혼인코호트·이동 등 원인 분해 미실시",
          "feature_facts":[f for f in item.get("facts",[]) if "-F" in f.get("claim_id","")],
          "all_claim_records":item.get("facts",[]),"image_suggestions":item.get("image_suggestions",[]),
          "sources":item.get("sources",[]),"price_context":[p for p in prices if p["region_id"]==r["region_id"]],
          "research_packet":str(source_packet.relative_to(EP)),"research_packet_sha256":hashlib.sha256(source_packet.read_bytes()).hexdigest()})
    assert len(regions)==20 and len({r["region_id"] for r in regions})==20
    comparable=[r for r in regions if r["comparison_available"]]
    rising=[r for r in comparable if r["change_couples"]>0]
    falling=[r for r in comparable if r["change_couples"]<0]
    summary={"regions":20,"comparable_2023_2024":len(comparable),"increasing_count":len(rising),"decreasing_count":len(falling),
      "increasing_regions":[{k:r[k] for k in ["region_id","region","count2023","count2024","change_couples","change_percent_display"]} for r in rising],
      "top20_couples_sum":sum(r["newlywed_couples"] for r in regions),
      "province_district_counts":{p:sum(r["province"]==p for r in regions) for p in ["서울","경기","인천"]},
      "feature_claim_count":sum(len(r["feature_facts"]) for r in regions),
      "verified_feature_claim_count":sum(f.get("status")=="verified" for r in regions for f in r["feature_facts"]),
      "qualified_feature_claim_count":sum(f.get("status")=="qualified" for r in regions for f in r["feature_facts"]),
      "image_place_candidates":sum(len(r["image_suggestions"]) for r in regions),"unique_source_urls":len(sources)}
    assert len(comparable)==19
    payload={"revision":"top20-8min-v2","status":"research_merged_independent_review_pending","summary":summary,"regions":regions,"sources":list(sources.values())}
    (OUT/"combined_facts.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    cols=["rank","province","region","count2023","count2024","change_couples","change_percent_display","comparison_available"]
    with (OUT/"top20_comparison.csv").open("w",encoding="utf-8-sig",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=cols);writer.writeheader();writer.writerows({k:r[k] for k in cols} for r in regions)
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
