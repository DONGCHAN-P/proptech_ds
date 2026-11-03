"""Rank official 2024 newlywed stock counts without parent/child double counting."""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
SOURCE_URL = "https://mods.go.kr/boardDownload.es?bid=11815&list_no=442387&seq=3"


def rank(rows: list[dict]) -> list[dict]:
    ordered = sorted(rows, key=lambda r: (-r["newlywed_couples"], r["province"], r["region"]))
    previous = None
    result = []
    current_rank = 0
    for i, row in enumerate(ordered, 1):
        if row["newlywed_couples"] != previous:
            current_rank = i
        previous = row["newlywed_couples"]
        result.append({"rank": current_rank, **row})
    return result


def table(rows: list[dict]) -> str:
    return "\n".join([
        "| 순위 | 지역 | 신혼부부 수(쌍) | 초혼(쌍) |",
        "|---:|---|---:|---:|",
        *[f'| {r["rank"]} | {r["province"]} {r["region"]} | {r["newlywed_couples"]:,} | {r["first_marriage_couples"]:,} |' for r in rows],
    ])


def main() -> None:
    with (BASE / "source/capital_rows.tsv").open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    numeric = ["newlywed_couples", "first_marriage_couples", "remarried_couples", "pdf_page"]
    for row in rows:
        for key in numeric:
            row[key] = int(row[key])
        row["reference_date"] = "2024-11-01"
        row["source_url"] = SOURCE_URL + f'#page={row["pdf_page"]}'
    assert len(rows) == 86
    assert len({(r["province"], r["region"]) for r in rows}) == 86
    gu = [r for r in rows if r["region"].endswith("구")]
    municipalities = [r for r in rows if r["province"] != "경기" or " " not in r["region"]]
    parent_names = {r["region"].split()[0] for r in rows if " " in r["region"]}
    leaf = [r for r in rows if r["region"] not in parent_names]
    assert len(gu) == 53
    assert len(municipalities) == 66
    assert len(leaf) == 79

    official_totals = {"서울": 166163, "인천": 61064, "경기": 288801}
    reconciliation = []
    for province, official in official_totals.items():
        for label, values in [("municipalities", municipalities), ("leaf", leaf)]:
            total = sum(r["newlywed_couples"] for r in values if r["province"] == province)
            delta = total - official
            # Each rounded detail cell and the rounded province total can differ
            # by at most 0.5 couple from its unrounded weight-based value.
            region_count = sum(r["province"] == province for r in values)
            rounding_bound = (region_count + 1) / 2
            assert abs(delta) <= rounding_bound, (province, label, delta, rounding_bound)
            reconciliation.append({"province": province, "scope": label, "sum": total,
                                   "official_province_total": official, "rounding_difference": delta,
                                   "rounding_bound": rounding_bound})
    views = {
        "capital_gu_ranking": rank(gu),
        "capital_municipality_ranking": rank(municipalities),
        "capital_leaf_ranking": rank(leaf),
    }
    for name, values in views.items():
        with (BASE / f"{name}.csv").open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(values[0]))
            writer.writeheader()
            writer.writerows(values)
    manifest = {
        "reference_date": "2024-11-01", "publication_date": "2025-12-12",
        "retrieved_date": "2026-11-01", "source_url": SOURCE_URL,
        "pdf_sha256": hashlib.sha256((BASE / "source/newlyweds_2024.pdf").read_bytes()).hexdigest(),
        "table": "6. 시군구별 신혼부부 수", "printed_pages": [25, 26], "pdf_pages": [32, 33],
        "transcription": "Manual numeric transcription from official PDF table and its web-extracted text; cross-check against province totals and independent review required.",
        "definition": "2024-11-01 기준 혼인신고 후 5년 미경과, 혼인관계 유지, 부부 중 1명 이상 국내 거주. 전체는 초혼·재혼·혼인종류 미상 포함.",
        "weighting": "부부의 거처가 다르면 각 시군구에 0.5 가중치. 공표 수치는 반올림되어 합계 차이 가능.",
        "boundaries": "2024 통계표 행정구역. 이후 분구·개편은 이 순위에 소급 적용하지 않음.",
        "ranking_metric": "전체 신혼부부 수 내림차순, 동률 공동순위(competition ranking). 초혼은 별도 열.",
        "scope_counts": {name: len(values) for name, values in views.items()},
        "city_with_gu": sorted(parent_names), "reconciliation": reconciliation,
        "interpretation": "구가 있는 도시의 전체 합계와 하위 구를 같은 순위에 중복 포함하지 않음. 신혼부부 거주 규모로 활용하며 선호도·순유입·투자수익은 별도 검증.",
        "built_at": datetime.now().astimezone().isoformat(),
    }
    packet = {"metadata": manifest, **views}
    (BASE / "rankings.json").write_text(json.dumps(packet, ensure_ascii=False, indent=2), encoding="utf-8")
    (BASE / "validation.json").write_text(json.dumps({"row_counts_passed": True, "unique_keys_passed": True,
       "descending_order_passed": all(all(a["newlywed_couples"] >= b["newlywed_couples"] for a,b in zip(v, v[1:])) for v in views.values()),
       "reconciliation": reconciliation, "independent_source_review": "pending"}, ensure_ascii=False, indent=2), encoding="utf-8")
    sections = [
        "# 수도권 신혼부부 지역별 순위\n",
        "기준일: **2024년 11월 1일** · 자료 발표: 2025년 12월 12일 · 기록: 2026년 11월 1일\n",
        "혼인신고 후 5년이 지나지 않은 신혼부부를 거주지 기준으로 집계한 수치다. 단위는 쌍이며 전체에는 초혼·재혼·혼인종류 미상이 포함된다.\n",
        "부부의 거처가 다르면 각 시군구에 0.5 가중치를 적용한다. 공표값은 반올림되어 세부 지역 합계와 시도 공표 합계가 다를 수 있다.\n",
        f"출처: [국가데이터처 「2024년 신혼부부통계」, 통계표 25~26쪽]({SOURCE_URL}#page=32). 원본 PDF와 행 단위 전사 자료는 `source/`에 보존했다.\n",
        "## 1. 2024 통계구역 기준 수도권 53개 구 거주 규모 순위\n",
        "서울 25개 구, 인천 8개 구, 경기 20개 일반구를 비교한다. 화성·평택·남양주 등 시·군은 다음 표에 별도로 기록했다.\n",
        table(views["capital_gu_ranking"]),
        "\n## 2. 2024 통계구역 기준 수도권 66개 시·군·자치구 거주 규모 순위\n",
        "서울 25개 자치구, 인천 8개 자치구·2개 군, 경기 31개 시·군을 비교한다. 경기의 일반구는 상위 시로 합쳐진 공식 합계를 사용한다.\n",
        table(views["capital_municipality_ranking"]),
        "\n## 3. 2024 통계구역 기준 수도권 세부 지역 79곳 거주 규모 순위\n",
        "구가 있는 경기도 7개 도시는 하위 구로 나누고 시 전체 행은 제외했다. 지역 크기는 서로 다르므로 전체 규모·집중도·이동 흐름을 각각 검토한다.\n",
        table(views["capital_leaf_ranking"]),
        "\n## 영상에서 적용할 비교 기준\n",
        "- 이번 순위는 2024년 거주 규모다. 신혼부부 비중과 이동은 대응하는 가구·이동 통계를 더해 분석한다.\n- 새 아파트 공급, 전체 가구 수와 지역 면적 차이를 함께 살펴 추천 지역의 범위를 좁힌다.\n- 인천 행정구역 등 이후 개편이 있으면 2024년 통계 구역과 현재 단지 구역을 교차표로 연결한다.\n- 매물은 촬영·제작 시점의 가격·확인일·면적·동/층·중복 제거·판매 상태를 별도 확인한다. 실거래가는 계약일·표본·취소 반영 시점을 함께 기록한다.\n- 최초 순위는 전체 신혼부부 수를 사용한다. 초혼 중심 분석은 분리된 지표로 계산한다.\n",
    ]
    (BASE / "수도권_신혼부부_순위.md").write_text("\n".join(sections), encoding="utf-8")
    print(json.dumps({"scope_counts": manifest["scope_counts"], "gu_top10": views["capital_gu_ranking"][:10],
                      "municipality_top5": views["capital_municipality_ranking"][:5], "reconciliation": reconciliation}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
