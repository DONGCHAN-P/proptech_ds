"""로컬 수집 메타데이터·XML 파일 존재 여부 감사. XML 내용/API는 읽지 않는다."""
import ast
import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
EPISODE = HERE.parents[1]
KST = timezone(timedelta(hours=9))
MONTHS = [f"{y}{m:02}" for y in range(2006, 2027) for m in range(1, 13)
          if f"{y}{m:02}" <= "202609"]
SCRIPTS = [ROOT / "collector/collect_three_cities.py",
           ROOT / "collector/collect_gwangju_sejong.py"]
NAMES = dict(busan="부산", daegu="대구", daejeon="대전", gwangju="광주", sejong="세종")


def rel(path):
    return path.relative_to(ROOT).as_posix()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write(name, value):
    (HERE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def extract_codes(path):
    # 수집기를 import/실행하지 않고 CODES 리터럴과 문자열 split만 읽는다.
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "CODES" or
            isinstance(t, ast.Attribute) and t.attr == "CODES" for t in node.targets
        ):
            result = {}
            for key, value in zip(node.value.keys, node.value.values):
                result[ast.literal_eval(key)] = (ast.literal_eval(value.func.value).split()
                    if isinstance(value, ast.Call) and value.func.attr == "split"
                    else ast.literal_eval(value))
            return result
    raise ValueError(f"CODES not found: {path}")


def inventory(bases):
    found = {}
    for base, codes in bases:
        for city in codes:
            for path in (base / city).rglob("*"):
                if path.is_file() and (path.name.endswith(".meta.json") or path.suffix == ".xml"):
                    stat = path.stat()
                    found[rel(path)] = {"bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns}
    return found


def digest_inventory(value):
    return sha(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def span(values):
    return {"first": min(values), "last": max(values)} if values else None


def summarize(cells):
    existing = [c for c in cells if c["meta_present"]]
    numeric = [c for c in existing if type(c.get("stored_rows")) is int]
    return {
        "expected_cells": len(cells), "present_meta_cells": len(existing),
        "verified_cells": sum(c["verified"] for c in cells),
        "missing_meta_cells": sum(not c["meta_present"] for c in cells),
        "incomplete_or_invalid_present_cells": sum(not c["verified"] for c in existing),
        "meta_complete_true_cells": sum(c.get("complete") is True for c in existing),
        "totalCount_equals_stored_rows_cells": sum(c.get("count_match", False) for c in existing),
        "metadata_stored_rows": sum(c["stored_rows"] for c in numeric),
        "metadata_declared_totalCount": sum(c["totalCount"] for c in existing if type(c.get("totalCount")) is int),
        "zero_stored_rows_cells": sum(c["stored_rows"] == 0 for c in numeric),
        "expected_xml_files_from_meta_pages": sum(c.get("pages", 0) for c in existing if type(c.get("pages")) is int),
        "present_expected_xml_files": sum(p["present"] for c in cells for p in c["xml_files"]),
        "missing_xml_files": sum(not p["present"] for c in cells for p in c["xml_files"]),
        "empty_xml_files": sum(p.get("bytes") == 0 for c in cells for p in c["xml_files"]),
        "observed_meta_request_month_span": span([c["ym"] for c in existing]),
        "positive_stored_rows_request_month_span": span([c["ym"] for c in numeric if c["stored_rows"] > 0]),
        "collected_at_span": span([c["collected_at"] for c in existing if c.get("collected_at")]),
    }


def main():
    started = datetime.now(KST).isoformat()
    bases = [(ROOT / "raw/rtms_trade_expansion" / label, extract_codes(script))
             for label, script in zip(["three_cities", "gwangju_sejong"], SCRIPTS)]
    before = inventory(bases)
    cells = []
    used = set()
    for base, cities in bases:
        for city, codes in cities.items():
            for code in codes:
                for ym in MONTHS:
                    path = base / city / ym / f"{code}.meta.json"
                    key = rel(path)
                    c = dict(dataset=base.name, city=city, code=code, ym=ym, meta_path=key,
                             meta_present=key in before, xml_files=[], issues=[])
                    if not c["meta_present"]:
                        c["issues"].append("missing_meta")
                    else:
                        used.add(key)
                        raw = path.read_bytes()
                        c.update(meta_sha256=sha(raw), meta_stat=before[key])
                        try:
                            meta = json.loads(raw.decode("utf-8-sig"))
                            for field in ["complete", "totalCount", "stored_rows", "pages", "collected_at"]:
                                c[field] = meta.get(field)
                            if any(meta.get(f) != v for f, v in [("city", city), ("code", code), ("ym", ym)]):
                                c["issues"].append("metadata_identity_mismatch")
                            if meta.get("complete") is not True:
                                c["issues"].append("meta_complete_not_true")
                            counts_valid = all(type(meta.get(f)) is int and meta[f] >= 0 for f in ["totalCount", "stored_rows"])
                            c["count_match"] = counts_valid and meta["totalCount"] == meta["stored_rows"]
                            if not c["count_match"]:
                                c["issues"].append("invalid_or_mismatched_row_counts")
                            pages = meta.get("pages")
                            if type(pages) is not int or pages < 1:
                                c["issues"].append("invalid_pages")
                            else:
                                if counts_valid and pages != max(1, math.ceil(meta["totalCount"] / 1000)):
                                    c["issues"].append("page_count_differs_from_collector_1000_rows_rule")
                                for page in range(1, pages + 1):
                                    xml_key = rel(path.parent / f"{code}.page{page}.xml")
                                    p = dict(path=xml_key, present=xml_key in before)
                                    if p["present"]:
                                        used.add(xml_key)
                                        p.update(before[xml_key])
                                        if p["bytes"] == 0:
                                            c["issues"].append("empty_xml_file")
                                    else:
                                        c["issues"].append("missing_xml_file")
                                    c["xml_files"].append(p)
                        except (ValueError, UnicodeError, TypeError) as exc:
                            c["issues"].append("meta_read_error:" + type(exc).__name__)
                    c["verified"] = not c["issues"]
                    cells.append(c)
    after = inventory(bases)
    changes = [p for p in sorted(set(before) | set(after)) if before.get(p) != after.get(p)]
    unexpected = [{"path": p, **before[p]} for p in sorted(set(before) - used)]
    summaries = []
    for base, cities in bases:
        for city, codes in cities.items():
            subset = [c for c in cells if c["city"] == city]
            summaries.append(dict(city=city, name_ko=NAMES[city], dataset=base.name, expected_codes=codes,
                **summarize(subset), by_code=[dict(code=code, **summarize([c for c in subset if c["code"] == code])) for code in codes]))
    boundary = []
    for issue_id, city, codes, note in [
        ("GUNWI_CODE_BOUNDARY", "daegu", ["27720", "47720"],
         "대구 수집기에는 군위 두 코드가 동시에 포함된다. 메타별 원시 합계이며 동일 거래 중복 또는 과거 행정구역 귀속 여부는 XML 미검토로 미확인이다. 동일 경계 시계열로 사용하기 전에 코드 전환·중복 정책이 필요하다."),
        ("SEJONG_2012_BOUNDARY", "sejong", ["36110"],
         "2012년 전후 메타의 양수/0건 분포는 아래 월별 목록과 코드별 범위로 확인한다. 요청 연월은 거래일의 직접 검증이나 당시 동일 행정경계의 증거가 아니다. 2012년 행정경계 연속성 검토 전 장기 지역 비교에 조건을 붙인다.")]:
        subset = [c for c in cells if c["city"] == city and c["code"] in codes]
        boundary.append(dict(issue_id=issue_id, status="qualified", note=note,
            affected_claim_ids=[], affected_scene_ids=[],
            by_code=[dict(code=code, **summarize([c for c in subset if c["code"] == code])) for code in codes],
            observed_monthly_metadata=[{k: c.get(k) for k in ["code", "ym", "totalCount", "stored_rows", "complete", "meta_path"]} for c in subset]))
    context = [ROOT / "video-agent-studio/WORKFLOW.md", EPISODE / "brief.json", EPISODE / "state.json",
               ROOT / "video-agent-studio/agents/video_research.toml", ROOT / "config/video_call_policy.json"]
    sources = [dict(path=rel(p), sha256=sha(p.read_bytes())) for p in SCRIPTS + context]
    coverage = dict(schema_version="regional-coverage-v1", task_id="regional-coverage-20261022",
        project_root=ROOT.as_posix(), episode_root=EPISODE.as_posix(), basis_date="2026-10-22",
        audit_started_at=started, audit_finished_at=datetime.now(KST).isoformat(),
        status="verified_metadata_and_file_presence" if all(c["verified"] for c in cells) and not changes and not unexpected else "qualified",
        scope_note="메타데이터와 XML 파일 존재·크기만 확인. XML 내용 파싱·정규화·가격 집계·거래일 직접 검증·해제거래 처리·중복 제거·외부 검증은 하지 않음. 상태 카운터와 재개 로그는 집계에 사용하지 않음.",
        methodology=dict(expected_month_start="200601", expected_month_end="202609", expected_months_per_code=len(MONTHS),
            month_rule_source="collect_three_cities.py main: range(2026,2005,-1), 월 12..1, ym>202609 제외",
            code_rule="수집기 AST에서 CODES를 추출; collect_gwangju_sejong.py의 worker.CODES 덮어쓰기를 별도 적용",
            count_rule="예상 city/code/ym마다 메타 stored_rows 및 totalCount를 합산. 메타 수치는 XML 실측이 아니며 군위 등 중복 미제거 원시 합계임.",
            xml_rule="메타 pages=N에 대해 code.page1.xml..code.pageN.xml 존재 확인. 0건도 수집기 동작대로 page1 필수. numOfRows=1000과 페이지 수 대조.",
            date_span_rule="ym은 요청 연월; 양수 메타의 최초·최후 연월을 별도 기록. 일 단위 거래일 범위 미확인.",
            replay_command="tools/python311/python.exe -X utf8 " + rel(Path(__file__))),
        totals=summarize(cells), cities=summaries,
        missing_or_incomplete_cells=[{k: c.get(k) for k in ["city", "code", "ym", "meta_path", "issues"]} for c in cells if not c["verified"]],
        issue_counts=dict(Counter(i for c in cells for i in c["issues"])),
        snapshot=dict(stable=not changes, changed_paths=changes, inventory_files=len(before),
            initial_inventory_sha256=digest_inventory(before), final_inventory_sha256=digest_inventory(after),
            digest_rule="SHA256(JSON(sort_keys=True,separators=(',',':'))), relative path -> bytes/mtime_ns; XML 내용 해시 아님"),
        unexpected_data_files=unexpected, boundary_risks=boundary,
        source_list=dict(fixed_inputs=sources, per_cell_sources="cells[].meta_path/meta_sha256/meta_stat 및 cells[].xml_files[].path/bytes/mtime_ns; project_root 기준 경로", audit_script_sha256=sha(Path(__file__).read_bytes())),
        cells=cells)
    write("coverage.json", coverage)
    print(json.dumps({"status": coverage["status"], "totals": coverage["totals"],
        "cities": [{k: s[k] for k in ["city", "expected_cells", "verified_cells", "metadata_stored_rows", "zero_stored_rows_cells", "positive_stored_rows_request_month_span"]} for s in summaries],
        "boundary_codes": [{"issue_id": b["issue_id"], "by_code": b["by_code"]} for b in boundary],
        "snapshot_stable": not changes, "unexpected_files": len(unexpected)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
