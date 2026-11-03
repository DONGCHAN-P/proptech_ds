"""동결 집계표를 편집 계약 JSON으로 변환. stdlib 전용, 원거래/네트워크 접근 없음.

실행: tools/python311/python.exe -X utf8 <이 파일의 경로>
검사: 같은 명령 뒤에 --check (기존 산출물만 검사하며 쓰지 않음)
"""
import argparse
import csv
import hashlib
import json
import math
import platform
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parent
EPISODE = OUT.parent.parent
ROOT = EPISODE.parents[2]
REGIONS = ["서울", "경기", "인천", "부산", "대구", "대전", "세종"]
SCRIPT_SHA = "99b40e8730ee0f8fdf74402cffbe04b5b418540344e6d2a7175e6a01c3054664"
SCENES = [f"S{i:03d}" for i in range(1, 13)]
CHECKS = Counter()


def require(condition, label):
    if not condition:
        raise ValueError(label)
    CHECKS[label.split(":", 1)[0]] += 1


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reject_constant(value):
    raise ValueError(f"JSON 비유한 값: {value}")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"), parse_constant=reject_constant)


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def save(name, value):
    (OUT / name).write_bytes(encoded(value))


def file_record(path):
    return {"path": path.as_posix(), "sha256": sha(path), "bytes": path.stat().st_size}


def close(actual, expected, label):
    if isinstance(expected, bool) or expected is None or isinstance(expected, str):
        require(type(actual) is type(expected) and actual == expected, label)
    else:
        require(type(actual) in (int, float) and math.isfinite(actual)
                and math.isclose(actual, expected, abs_tol=1e-9, rel_tol=1e-12), label)


def quarter_number(quarter):
    return int(quarter[:4]) * 4 + int(quarter[-1]) - 1


def scalar(value, kind):
    if value.strip().lower() in ("", "nan", "null", "none"):
        return None
    if kind == "str":
        return value
    if kind == "bool":
        require(value in ("True", "False", "true", "false"), "CSV타입:boolean")
        return value.lower() == "true"
    number = float(value)
    require(math.isfinite(number), "CSV타입:finite")
    if kind == "int":
        require(number.is_integer(), "CSV타입:integer")
        return int(number)
    return number


def table(spec):
    with (ROOT / spec["path"]).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        require(reader.fieldnames == list(spec["schema"]), "CSV헤더:" + spec["path"])
        rows = []
        for row in reader:
            require(None not in row and None not in row.values(), "CSV열수:" + spec["path"])
            rows.append({key: scalar(row[key], kind) for key, kind in spec["schema"].items()})
    require(len(rows) == spec["rows"], "CSV행수:" + spec["path"])
    return rows


def group(rows):
    require({row["region"] for row in rows} == set(REGIONS), "지역집합:7")
    return {region: [row for row in rows if row["region"] == region] for region in REGIONS}


def build(lock):
    sources = {name: {**file_record(ROOT / spec["path"]), "relative_path": spec["path"],
                      "prior_evidence": spec["prior_evidence"]}
               for name, spec in lock["inputs"].items()}
    loaded = {name: table(spec) for name, spec in lock["inputs"].items() if "schema" in spec}
    history = read_json(ROOT / lock["inputs"]["history_metadata"]["path"])
    raw = read_json(ROOT / lock["inputs"]["transactions_metadata"]["path"])
    series = {region: [{"quarter": row["quarter"], "index": row["normalized_start_100"],
                        "drawdown": row["running_drawdown_pct"],
                        "matched_complexes": row["matched_complexes"]} for row in rows]
              for region, rows in group(loaded["series"]).items()}
    return {
        "metadata": {
            "endpoint": "2026Q2", "endpoint_date": "2026-06-30", "script_revision": "v3",
            "script_sha256": SCRIPT_SHA, "production_revision": "production-v1-jun",
            "sources": sources,
            "table_schemas": {name: spec["schema"] for name, spec in lock["inputs"].items()
                              if "schema" in spec},
            "cleaning": {
                "reference": raw["cleaning_reference"],
                "rules": ["is_canceled null은 False로 처리한 해제 제외", "deal_amount>0, area_m2>0, apt_id 존재",
                          "유효성 필터 뒤 deal_hash 중복 제거", "2006Q1~2026Q2 한정",
                          "대구 군위 코드 27720/47720 전 기간 제외"],
                "notes": raw["notes"], "performed_in_this_build": False},
            "matching": {"definition": history["price_method_inherited"],
                         "main_min_trades": 2, "min_complexes_per_link": 30,
                         "baseline_matched_complexes": None,
                         "matched_transaction_count": None,
                         "matched_transaction_share_pct": None,
                         "unavailable_reason": history["matched_transaction_count_reason"]},
            "sejong_boundary": {
                "index_start": "2015Q1", "index_quarters": 46, "transaction_start": "2006Q1",
                "transaction_quarters": 82, "early_cache": raw["sejong_2006_2014_cache_audit"],
                "warning": "초기 36110 재매핑 가능 기록은 역사적 세종시 전체의 완전한 지역 포괄을 뜻하지 않음. 2015Q1 이전 가격지수 보간 금지."},
            "coverage_warning": history["volume_scope"],
            "limitations": history["limitations"], "episode_definition": history["method"],
            "series_policy": "원표의 관측 분기와 2건 기준 지수만 유지; 누락 보간·3/5건 시계열 생성 없음",
            "sensitivity": {"reference_peak_window": ["2020Q1", "2022Q4"],
                            "format": "summary_only", "min_trades_present": [2, 3, 5],
                            "coverage": "원표의 13행만 유지; 모든 지역에 3/5건 결과가 있는 것은 아님",
                            "recovery": "최근 주기 고점 대비 관측 저점 이후 최초 교차; 전체 이력 ATH 최초복귀와 구별"},
            "factors_usage": {"scene_ids": ["S011"], "descriptive_only": True,
                              "causal_values": "추가하지 않음; verified_examples 전체 객체를 그대로 복사"},
            "excluded_new_collections": ["광주", "울산", "충북", "충남"],
            "validation_scope": "동결 CSV 직렬화·해시·기존 QA 대조 및 집계표 산술. 원거래 재집계·새 API·영상/음성 검수 없음",
        },
        "regions": REGIONS,
        "series": series,
        "all_transactions": group(loaded["all_transactions"]),
        "summary": {region: rows[0] for region, rows in group(loaded["summary"]).items()},
        "episodes": loaded["episodes"], "annual_volume": loaded["annual_volume"],
        "sensitivity": loaded["sensitivity"], "horizon": loaded["horizon"],
        "factors": read_json(ROOT / lock["inputs"]["factors"]["path"]),
    }


def validate(data, lock):
    inputs = lock["inputs"]
    qa = read_json(ROOT / inputs["independent_qa"]["path"])
    prior = read_json(ROOT / inputs["prior_recheck"]["path"])
    final = read_json(ROOT / inputs["final_recheck"]["path"])
    require(qa["status"] == "pass" and not qa["failures"], "기존QA:independent_pass")
    require(not prior["checks"]["failures"] and final["required_count"] == 0, "기존QA:final_required_zero")
    require(final["checked_revision"]["script_sha256"] == SCRIPT_SHA, "승인:v3")
    require(final["checked_revision"]["prior_recheck_sha256"] == inputs["prior_recheck"]["sha256"], "기존QA:recheck_link")
    require(prior["reuse"]["sha256"] == inputs["independent_qa"]["sha256"], "기존QA:independent_link")
    require(data["regions"] == REGIONS, "계약:지역순서")
    require(sum(map(len, data["series"].values())) == qa["coverage"]["index_rows"] == 538, "행수:538")
    require(sum(map(len, data["all_transactions"].values())) == qa["coverage"]["volume_rows"] == 574, "행수:574")
    require(len(data["episodes"]) == qa["coverage"]["episodes"] == 33, "행수:33")
    require(len(data["annual_volume"]) == 147 and len(data["sensitivity"]) == 13
            and len(data["horizon"]) == 7 and len(data["summary"]) == 7, "행수:기타표")
    qa_summary = {row["region"]: row for row in qa["recomputed_summaries"]}
    qa_episodes = {row["episode_id"]: row for row in qa["recomputed_episodes"]}
    region_receipts = {}
    for region in REGIONS:
        series, raw, summary = data["series"][region], data["all_transactions"][region], data["summary"][region]
        # 독립 QA는 정확한 거래일 두 필드를 검증하지 않았다. CSV 값은 보존한다.
        require(set(summary) - set(qa_summary[region]) == {"full_volume_first_date", "full_volume_last_date"}
                and not set(qa_summary[region]) - set(summary), "요약QA검증범위:" + region)
        for key, expected in qa_summary[region].items():
            close(summary[key], expected, f"독립QA요약:{region}.{key}")
        expected_start = "2015Q1" if region == "세종" else "2006Q1"
        require(series[0]["quarter"] == expected_start and series[-1]["quarter"] == "2026Q2", "지수끝점:" + region)
        require(len(series) == (46 if region == "세종" else 82), "지역지수행수:" + region)
        require(len(raw) == 82 and raw[0]["quarter"] == "2006Q1" and raw[-1]["quarter"] == "2026Q2", "지역거래행수끝점:" + region)
        for rows in (series, raw):
            quarters = [quarter_number(row["quarter"]) for row in rows]
            require(len(set(quarters)) == len(quarters) and all(b-a == 1 for a,b in zip(quarters, quarters[1:])), "관측키:" + region)
        close(series[0]["index"], summary["baseline_index"], "지수기준:" + region)
        close(series[-1]["index"], summary["latest_index"], "지수끝값QA:" + region)
        close(series[-1]["drawdown"], summary["latest_vs_all_time_high_pct"], "하락끝값QA:" + region)
        cagr = 100 * ((series[-1]["index"] / series[0]["index"]) ** (4 / (quarter_number("2026Q2") - quarter_number(expected_start))) - 1)
        close(cagr, qa_summary[region]["full_period_cagr_pct"], "전체기간CAGR_QA:" + region)
        total = sum(row["n"] for row in raw)
        require(total == prior["all_valid_transactions"]["region_totals"][region] == summary["full_valid_transaction_total"], "지역거래수QA:" + region)
        require(series[0]["matched_complexes"] is None, "기준분기null:" + region)
        require(all(type(row["matched_complexes"]) is int and row["matched_complexes"] >= 30 for row in series[1:]), "매칭수타입:" + region)
        region_receipts[region] = {"index_rows": len(series), "transaction_rows": len(raw), "valid_transactions": total,
                                   "start": expected_start, "endpoint": series[-1]["quarter"],
                                   "latest_index": series[-1]["index"], "full_period_cagr_pct": cagr}
    require(sum(x["valid_transactions"] for x in region_receipts.values()) == qa["full_valid_transaction_total"] == 6640041, "전체거래수QA:6640041")
    require(len({row["episode_id"] for row in data["episodes"]}) == 33, "구간키:33")
    for row in data["episodes"]:
        expected = qa_episodes[row["episode_id"]]
        require(set(row) == set(expected), "구간전체열:" + row["episode_id"])
        for key, value in expected.items():
            close(row[key], value, "독립QA구간:" + row["episode_id"] + "." + key)
        if row["right_censored"]:
            require(all(row[key] is None for key in ("first_return_quarter", "first_return_index", "peak_to_first_return_quarters", "trough_to_first_return_quarters")), "미회복null:" + row["episode_id"])
    require(sum(row["right_censored"] for row in data["episodes"]) == qa["coverage"]["censored_episodes"] == 6, "미회복수:6")
    for row in data["horizon"]:
        series = data["series"][row["region"]]
        values = {quarter_number(x["quarter"]): x["index"] for x in series}
        end = quarter_number("2026Q2")
        for years in (3, 5, 10):
            cagr = 100 * ((values[end] / values[end-years*4]) ** (1/years) - 1)
            close(row[f"cagr_{years}y_pct"], cagr, "기간별CAGR:" + row["region"] + str(years))
            if row["region"] == "세종":
                close(cagr, prior["sejong_horizon_cagr_pct"][str(years)], "세종기간별CAGR_QA:" + str(years))
    for row in data["annual_volume"]:
        raw = data["all_transactions"][row["region"]]
        same_year = [x for x in raw if int(x["quarter"][:4]) == row["year"]]
        require(row["valid_transactions"] == sum(x["n"] for x in same_year)
                and row["observed_quarters"] == len(same_year), "연간일치:" + row["region"] + str(row["year"]))
    require(data["factors"] == read_json(ROOT / inputs["factors"]["path"]), "factors:완전일치")
    require(all(x["causal_relationship"] == "not_established" for x in data["factors"]["examples"]), "factors:기술사례한정")
    return region_receipts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    lock_path = OUT / "frozen_inputs.json"
    lock = read_json(lock_path)
    for name, spec in lock["inputs"].items():
        path = ROOT / spec["path"]
        require(sha(path) == spec["sha256"] and path.stat().st_size == spec["bytes"], "입력SHA:" + name)
    require(lock["inputs"]["approved_script"]["sha256"] == SCRIPT_SHA, "승인SHA:고정")
    expected = build(lock)
    data = read_json(OUT / "chart_data.json") if args.check else json.loads(encoded(expected), parse_constant=reject_constant)
    require(data == expected, "직렬화:全セル완전일치")
    regions = validate(data, lock)
    if args.check:
        receipt = read_json(OUT / "validation_receipt.json")
        require(receipt["status"] == "pass", "저장검증:pass")
        for record in receipt["outputs"]:
            path = Path(record["path"])
            require(sha(path) == record["sha256"] and path.stat().st_size == record["bytes"], "저장SHA:" + path.name)
        handoff = read_json(OUT / "handoff.json")
        require(handoff["validation_receipt"]["sha256"] == sha(OUT / "validation_receipt.json"), "핸드오프SHA:receipt")
        print(json.dumps({"status": "pass", "mode": "check", "checks": sum(CHECKS.values()), "regions": 7, "raw_quarters": 574, "index_rows": 538, "episodes": 33}, ensure_ascii=False))
        return
    save("chart_data.json", data)
    require(read_json(OUT / "chart_data.json") == expected, "저장재읽기:일치")
    sources = list(data["metadata"]["sources"].values())
    assets = {
        "task_id": "RPR-PROD1-DATA", "script_revision": "v3", "script_sha256": SCRIPT_SHA,
        "production_brief": {"canvas": {"width": 1920, "height": 1080, "fps": 30},
                             "scope": "편집 소비자용 데이터 준비", "composition_color_text_margin": "이번 작업의 신규 시각 지시 없음; 그래픽 제작하지 않음"},
        "assets": [{"asset_id": "RPR_PROD1_CHART_DATA", "scene_ids": SCENES, "type": "chart_data",
                    "source_or_prompt": sources, "dimensions": None,
                    "actual_file": (OUT / "chart_data.json").as_posix(),
                    "actual_place": "editor/production-v1 및 outputs/production-v1-jun/project의 데이터 입력",
                    "AI 표기": "비해당: 기존 수치의 결정적 형식 변환; 생성 이미지 없음", "ai_generated": False,
                    "사용조건": "동결 v3 범위와 출처·한계를 함께 유지. 인과효과·공식 지수·투자수익률로 확대 금지.",
                    "검수 상태": "직렬화·타입·해시·기존 독립 QA 수치 대조 통과; 최종 화면 검수 별도",
                    "sha256": sha(OUT / "chart_data.json"), "upscaled": False}],
        "source_ledger": sources,
    }
    save("assets.json", assets)
    receipt = {"task_id": "RPR-PROD1-DATA", "status": "pass", "python": platform.python_version(),
               "script_sha256": SCRIPT_SHA, "input_lock": file_record(lock_path),
               "inputs": data["metadata"]["sources"], "check_counts": dict(CHECKS),
               "total_checks": sum(CHECKS.values()), "region_controls": regions,
               "totals": {"regions": 7, "raw_quarters": 574, "index_rows": 538, "episodes": 33,
                          "censored_episodes": 6, "valid_transactions": 6640041},
               "prior_qa": {"independent_checks_reused": 7130, "v3_checks_reused": 1468,
                            "raw_price_independent_samples_reused": 3,
                            "scope": "원가격 574분기 전량 독립 검산으로 확대하지 않음"},
               "outputs": [file_record(OUT / name) for name in ("chart_data.json", "assets.json", "build_chart_data.py", "frozen_inputs.json")],
               "raw_ingestion_runs": 0, "new_api_calls": 0, "external_model_calls": 0,
               "paid_actions": 0, "new_graphics": 0, "new_videos": 0,
               "independent_qa_of_this_conversion": "미실시; 기존 독립 수치 QA 재사용과 제작자 변환 검사를 구별",
               "limitations": ["원거래·원 XML 재집계/재취득 없음", "새 수집 지역 제외", "영상 연속재생·음성청취 대상 없음",
                               "full_volume_first_date/last_date는 동결 CSV 그대로 보존. 기존 독립 QA는 분기 내 위치만 검사했으며 정확한 거래일 독립 검산은 미실시"],
               "inherited_open_issue_ids": ["FHQA-R01"],
               "inherited_issue_impact": "기존 제작자 검수 메타데이터의 인코딩 권고; 수치 영향 없음. 보정본은 별도 outputs/script-review-v3 기록이며 원본/공통 상태는 수정하지 않음"}
    save("validation_receipt.json", receipt)
    save("handoff.json", {
        "task_id": "RPR-PROD1-DATA", "role": "visual", "status": "ready_for_editor",
        "input_revisions": {"script_revision": "v3", "script_sha256": SCRIPT_SHA,
                            "frozen_revision": ["full_history_v1", "full_transactions_v1", "regional_expansion_v1"],
                            "lock": file_record(lock_path)},
        "outputs": [file_record(OUT / name) for name in ("chart_data.json", "assets.json", "build_chart_data.py", "frozen_inputs.json", "validation_receipt.json")],
        "affected_scene_ids": SCENES,
        "checks": [{"check": "UTF-8·원 헤더/타입·null·NaN 금지·전체 셀 일치·SHA", "result": "pass"},
                   {"check": "7지역/574분기/538지수행/33구간·CAGR·끝값의 기존 QA 대조", "result": "pass"}],
        "validation_receipt": file_record(OUT / "validation_receipt.json"),
        "open_issue_ids": [], "inherited_open_issue_ids": ["FHQA-R01"],
        "unresolved": ["최종 그래픽/영상/음성 검수는 후속 단계", "실측 timing lock은 총괄/음성 담당 소관"],
        "next_role": ["editor", "director"],
        "consumer_directories": [(EPISODE / "editor/production-v1").as_posix(), (EPISODE / "outputs/production-v1-jun/project").as_posix()],
        "reproduce_argv": [(ROOT / "tools/python311/python.exe").as_posix(), "-X", "utf8", (OUT / "build_chart_data.py").as_posix()],
        "check_argv": [(ROOT / "tools/python311/python.exe").as_posix(), "-X", "utf8", (OUT / "build_chart_data.py").as_posix(), "--check"],
        "summary": "동결 CSV 계약 변환 완료. 7지역 574분기/538지수행/33구간, CAGR·끝값을 기존 QA와 대조. factors 전체 객체 동일. 세종 초기 포괄 한계·민감도 고점 정의 유지. 신규 수집·원거래 재집계·외부 호출·유료 생성 없음."
    })
    print(json.dumps({"status": "pass", "output": (OUT / "chart_data.json").as_posix(), "sha256": sha(OUT / "chart_data.json"), "checks": sum(CHECKS.values())}, ensure_ascii=False))


if __name__ == "__main__":
    main()
