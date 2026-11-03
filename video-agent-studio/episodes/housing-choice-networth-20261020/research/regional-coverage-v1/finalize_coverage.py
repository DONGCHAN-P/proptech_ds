"""이미 기록한 감사 셀에서 주의사항·인계서 생성 및 교차검증. 원본 재검수 없음."""
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    (HERE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    path = HERE / "coverage.json"
    coverage = json.loads(path.read_text(encoding="utf-8"))
    cells = coverage["cells"]
    sejong = [c for c in cells if c["city"] == "sejong"]
    sejong_periods = []
    for start, end in [("200601", "201112"), ("201201", "201206"), ("201207", "201212"), ("201301", "202609")]:
        rows = [c for c in sejong if start <= c["ym"] <= end]
        sejong_periods.append(dict(start=start, end=end, meta_cells=len(rows),
            positive_cells=sum(c.get("stored_rows", 0) > 0 for c in rows),
            metadata_stored_rows=sum(c.get("stored_rows", 0) for c in rows)))
    coverage["boundary_risks"][0]["observed_finding"] = "27720: 249개 메타 합계 333건, 양수 131개월(최초 200601·최후 202609). 47720: 249개 메타 전부 0건. 과거 코드 귀속·동일 경계·개별 거래 중복은 미확인."
    coverage["boundary_risks"][1]["observed_finding"] = "36110: 249개월 모두 양수(200601~202609). 2012년 이전에도 메타가 있으므로 수집 연월 범위 자체를 세종의 동일 행정경계 과거 시계열로 해석할 수 없음."
    coverage["boundary_risks"][1]["observed_periods"] = sejong_periods
    issue_id = "REGIONAL_COMPARABILITY"
    findings = [dict(
        finding_id="GWANGJU_ALL_ZERO", status="qualified", city="gwangju",
        problem="광주 5코드×249개월의 메타가 모두 0건이다. 파일 수집 검사는 통과했지만 유효 가격 표본은 확인되지 않았다.",
        evidence="coverage.json cities[city=gwangju], cells[city=gwangju]: totalCount=stored_rows=0, complete=true, page1 존재 1,245셀",
        proposal="부모 담당이 원응답·조회조건·코드 매핑을 별도 확인할 때까지 광주의 가격·수익률 지역 비교를 보류한다. 실제 무거래라는 결론은 내리지 않는다.",
        impact="광주 지역 비교에 사용할 비영 표본이 현재 메타에는 없음.",
        affected_claim_ids=[], affected_scene_ids=[])]
    for risk in coverage["boundary_risks"]:
        findings.append(dict(finding_id=risk["issue_id"], status="qualified",
            problem=risk["observed_finding"], evidence="coverage.json boundary_risks 및 연결된 observed_monthly_metadata[].meta_path",
            proposal=risk["note"], impact="장기 지역 비교의 경계·코드 처리 조건 확정 필요.",
            affected_claim_ids=[], affected_scene_ids=[]))
    coverage["interpretation_status"] = "qualified_for_regional_comparisons"
    coverage["interpretation_findings"] = findings
    coverage["methodology"]["finalize_command"] = "tools/python311/python.exe -X utf8 " + (HERE / "finalize_coverage.py").relative_to(ROOT).as_posix()
    coverage["source_list"]["finalizer_script_sha256"] = sha(Path(__file__))
    save("coverage.json", coverage)
    save("issue_REGIONAL_COMPARABILITY.json", dict(issue_id=issue_id, role="research", status="open_for_director_review",
        verified_at=coverage["audit_finished_at"], affected_claim_ids=[], affected_scene_ids=[],
        scene_mapping="지정된 claim/scene ID가 없으며 공통 scenes.json을 읽거나 수정하지 않음.",
        findings=findings, next_owner="director / parent (가격·원응답 검토 담당)", causal_conclusions="없음; 관측된 메타와 파일 존재만 보고"))

    # 출력 JSON에서 독립 산술 재집계 및 예상 코드×연월 집합의 완전 일치 검사.
    loaded = json.loads(path.read_text(encoding="utf-8"))
    expected_months = [f"{y}{m:02}" for y in range(2006, 2027) for m in range(1, 13) if (y, m) <= (2026, 9)]
    expected = {(city["city"], code, ym) for city in loaded["cities"] for code in city["expected_codes"] for ym in expected_months}
    actual = {(c["city"], c["code"], c["ym"]) for c in loaded["cells"]}
    assert expected == actual and len(actual) == len(cells) == 9213
    total = loaded["totals"]
    assert total["metadata_stored_rows"] == sum(c["stored_rows"] for c in loaded["cells"])
    assert total["metadata_declared_totalCount"] == sum(c["totalCount"] for c in loaded["cells"])
    assert total["verified_cells"] == sum(c["verified"] for c in loaded["cells"])
    assert total["present_expected_xml_files"] == sum(p["present"] for c in loaded["cells"] for p in c["xml_files"])
    for city in loaded["cities"]:
        subset = [c for c in loaded["cells"] if c["city"] == city["city"]]
        assert city["metadata_stored_rows"] == sum(c["stored_rows"] for c in subset)
        assert city["expected_cells"] == len(subset)
        assert city["verified_cells"] == sum(c["verified"] for c in subset)
    assert loaded["source_list"]["audit_script_sha256"] == sha(HERE / "audit_coverage.py")
    assert loaded["snapshot"]["stable"]
    issue = json.loads((HERE / "issue_REGIONAL_COMPARABILITY.json").read_text(encoding="utf-8"))
    assert len(issue["findings"]) == 3
    output_names = ["coverage.json", "issue_REGIONAL_COMPARABILITY.json", "audit_coverage.py", "finalize_coverage.py"]
    outputs = [dict(path=(HERE / name).as_posix(), sha256=sha(HERE / name)) for name in output_names]
    handoff = dict(task_id="regional-coverage-20261022", role="research",
        status="coverage_audit_complete_with_interpretation_issues", verified_at=datetime.now(timezone(timedelta(hours=9))).isoformat(),
        summary="200601~202609, 37코드×249개월=9,213셀 검사. complete·수량일치·예상 XML 9,308개 모두 통과, 누락 0. 메타 stored_rows 합계 1,922,287건(중복·해제 미처리). 부산 866,481 / 대구 597,113 / 대전 392,725 / 광주 0 / 세종 65,968. 광주 전 기간 0건과 군위·세종 경계 문제는 후속 확인 필요.",
        input_revisions=dict(basis_date="2026-10-22", fixed_inputs=loaded["source_list"]["fixed_inputs"],
            inventory_sha256=loaded["snapshot"]["initial_inventory_sha256"], metadata_sources="coverage.json cells[].meta_path/meta_sha256", xml_sources="coverage.json cells[].xml_files"),
        outputs=outputs, affected_claim_ids=[], affected_scene_ids=[],
        checks=[dict(check="예상 코드×월 9,213셀과 출력 집합 일치·중복 없음", result="passed", evidence="finalize_coverage.py assertions"),
            dict(check="모든 meta.complete=true, totalCount=stored_rows, 기대 XML 존재·비어 있지 않음", result="passed", evidence="coverage.json totals, missing_or_incomplete_cells, cells"),
            dict(check="도시·전체 합계 출력 JSON 재집계 일치", result="passed", evidence="finalize_coverage.py assertions"),
            dict(check="감사 중 메타/XML 경로·크기·mtime 불변", result="passed", evidence="coverage.json snapshot"),
            dict(check="출력 JSON 재개봉·소스 감사 코드 SHA·출력 SHA 확인", result="passed", evidence="finalize_coverage.py assertions 및 outputs[].sha256")],
        open_issue_ids=[issue_id], unresolved_findings=[f["finding_id"] for f in findings],
        limitations=["XML 내용·거래일·가격·해제거래·중복 여부 미검증", "지역 경계의 역사적 원인·영향은 결론 내리지 않음", "주장·장면 ID 미제공으로 매핑 미수행"],
        next_role="director / parent", next_action="광주 원응답·조회조건, 군위 코드 처리, 세종 2012 경계 확인 후 부모가 가격 정규화·비교 진행. writer에게 조건과 미확인 사항 전달.")
    save("handoff.json", handoff)
    reread = json.loads((HERE / "handoff.json").read_text(encoding="utf-8"))
    assert all(sha(Path(o["path"])) == o["sha256"] for o in reread["outputs"])
    print(json.dumps(dict(verification="passed", expected_cells=len(actual), xml_files=total["present_expected_xml_files"],
        metadata_stored_rows=total["metadata_stored_rows"], sejong_periods=sejong_periods,
        outputs=[o["path"] for o in outputs] + [(HERE / "handoff.json").as_posix()]), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
