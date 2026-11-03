"""가격 재집계 없이 전달 입력과 검수 범위를 기록한다. writer는 준비 알림 후 별도 검수한다."""
import datetime
import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
BASE = "research/top20-explain-v3/prices/final-api-20261103-v2/"
NOW = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat()
INPUTS = {}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path, scope="실제 JSON 내용과 기록 범위 검토"):
    p = ROOT / path
    raw = p.read_bytes()
    INPUTS[path] = {"path": path, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw), "scope": scope}
    return json.loads(raw.decode("utf-8-sig"))


def write(name, data):
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


panel = read("director/top20-explain-v3/price_panel_data.json")
maps = read("visual/top20-explain-v3/maps/map_assets.json")
features = read("research/top20-explain-v3/regions/facts.json")
suggestions = read("research/top20-explain-v3/regions/narration_suggestions.json")
values = read(BASE + "writer_price_values.json")
layers = read(BASE + "map_price_inputs.json")
receipt = read("qa/top20-explain-v3/price_panel_verification.json")
for path in ["state.json", "brief.json", "director/top20-explain-v3/requirements.json", "director/top20-explain-v3/episode_preflight.json", BASE + "methodology.json", BASE + "validation.json", "research/top20-explain-v3/regions/research_records.json", "research/top20-explain-v3/regions/source_registry.json", "research/top20-explain-v3/regions/source_snapshots/capture_receipt.json"]:
    read(path)
panel_sha = INPUTS["director/top20-explain-v3/price_panel_data.json"]["sha256"]
rollup = ROOT / "qa/top20-explain-v3/independent_price_rollup.json"
INPUTS[str(rollup.relative_to(ROOT)).replace("\\", "/")] = {"path": str(rollup), "sha256": sha(rollup), "bytes": rollup.stat().st_size, "scope": "SHA 연결만 확인. 원XML/원거래 재집계·좌표 재계산 없음"}
checks = {
    "latest_panel_sha": panel_sha == "844f0ee211dfc89094b8160558d72e0f8f001e8072d361123447e8c1ebfacdef",
    "panel_source_sha": panel["source_sha256"] == sha(ROOT / panel["source_file"]),
    "receipt_panel_sha": receipt["price_panel_sha256"] == panel_sha,
    "map_panel_sha": maps["source_price_panel_sha256"] == panel_sha,
    "receipt_rollup_sha": receipt["rollup_sha256"] == sha(rollup),
    "receipt_result": receipt["status"] == "passed" and receipt["total_n"] == 14303 and receipt["region_count"] == 20,
    "receipt_20_matches": len(receipt["checks"]) == 20 and all(x["region_n_and_median"] == x["complex_n_name_and_median"] == "exact_match" for x in receipt["checks"]),
}
fi = {x["region_id"]: x for x in features["regions"]}
si = {x["region_id"]: x for x in suggestions["regions"]}
vi = {x["region_id"]: x for x in values["regions"]}
mi = {x["region_id"]: x for x in maps["assets"]}
li = {x["region_id"]: x for x in layers["layers"]}
checks["20_unique_regions"] = set(fi) == set(si) == set(vi) == set(mi) == set(li) == {f"R{i:02}" for i in range(1, 21)}
matrix = []
for x in panel["regions"]:
    rid = x["region_id"]
    a, f, v, m, layer = x["representative"], fi[rid], vi[rid], mi[rid], li[rid]
    va = v["representative"]
    row_checks = {
        "map_panel": x == m["price_panel"],
        "writer_values": (x["median_manwon"], x["n"], a["median_manwon"], a["n"], a["apt_name"], a["api_apt_seq"]) == (v["median_manwon"], v["n"], va["median_manwon"], va["n"], va["name"], va["api_apt_seq"]),
        "map_values": (x["median_manwon"], x["n"], a["median_manwon"], a["n"]) == (layer["regional_fill_value_manwon"], layer["regional_n"], layer["marker"]["median_manwon"], layer["marker"]["n"]),
        "region": x["region"] == f["region"] == v["region"] == layer["region"],
        "scene": x["scene_id"] == f["scene_id"] == v["scene_id"] == layer["scene_id"] == si[rid]["scene_id"],
        "period": x["contract_window"] == {"start": "2026-05-01", "end": "2026-10-31"} and x["as_of_date"] == "2026-11-03",
        "area": x["area_range_m2"] == {"minimum": 83, "maximum": 85, "endpoints_inclusive": True},
        "separate_example": a["label"] == "단지 사례" and va["represents_gu_typical_price"] is False,
        "feature_suggestion": f["narration_suggestion"]["text"] == si[rid]["text"],
        "marker_identity": (a["apt_name"], a["lat"], a["lng"]) == (m["marker"]["apt_name"], m["marker"]["lat"], m["marker"]["lng"]),
        "marker_evidence_status": m["marker_status"] == "verified_coordinate_inside_region",
        "map_file_sha": m["sha256"] == sha(ROOT / m["file"]),
        "boundary_file_sha": m["source_sha256"] == sha(ROOT / m["source"]),
    }
    for path in [m["file"], m["source"]]:
        p = ROOT / path
        INPUTS[path] = {"path": path, "sha256": sha(p), "bytes": p.stat().st_size, "scope": "파일 SHA·manifest 연결; 새 좌표/지도 픽셀 검사 없음"}
    checks[rid] = all(row_checks.values())
    matrix.append({"region_id": rid, "scene_id": x["scene_id"], "region": x["province"] + " " + x["region"], "checks": row_checks, "housing_claims": f["housing_feature_claim_ids"], "landmark_or_named_area_claims": f["landmark_function_claim_ids"], "regional_price": {k: x[k] for k in ["median_manwon", "display_price", "n"]}, "complex_example": {k: a[k] for k in ["apt_name", "api_apt_seq", "median_manwon", "display_price", "n"]}, "photo": {k: f["photo"][k] for k in ["actual_place", "address_or_area", "caption_ko", "photo_capture_date_raw", "ai_generated"]}, "source_evidence_modes": sorted({c["verification_mode"] for c in f["claims"]}), "wording_and_place_guards": f["editorial_cautions"], "final_script": "unchecked_await_parent_ready"})
write("input_manifest.json", {"checked_at": NOW, "inputs": list(INPUTS.values()), "photo_hashes": "photo_integrity.json", "not_read_pending_ready": ["writer/top20-explain-v3/script_v6.md", "writer/top20-explain-v3/scene_proposals_v6.json"]})
write("region_review_matrix.json", {"checked_at": NOW, "checks": checks, "regions": matrix})
failed = [k for k, ok in checks.items() if not ok]
if failed:
    raise RuntimeError("검수 연결 실패: " + ", ".join(failed))
coverage = {"raw_xml_reaggregation": "부모의 현재SHA receipt 연결; 재집계 미실행", "region_complex_values": "20/20 final v2→패널→지도 입력의 중위값·n·단지명 대조", "geographic_projection_and_point_in_polygon": "부모 근거 재사용. 좌표 재계산 미실행", "photo_decode_sha": "20/20 일치", "photo_contact_sheet": "20/20 축소판 실제 확인. 정밀 지오로케이션/새 권리심사와 구분", "feature_photo_text": "20/20 자료 범위·설명·주의문 읽음", "official_primary_source_spotcheck": "공식 2페이지·4claim; source_spotcheck.json", "script_v6": "unchecked; 최종준비 알림 전 읽지 않음", "scene_proposals_v6": "unchecked; 최종준비 알림 전 읽지 않음", "editor_spec_snapshot": "unchecked; 이번 입력 검수에 미포함", "actual_encoded_mp4_frames": "unchecked; 현재 버전 MP4 없음", "tts_measured_timing": "unchecked; 현재 버전 음성 없음", "actual_listening_performed": False, "continuous_playback_performed": False, "codec_duration_zip": "script 게이트에서 해당 없음"}
write("coverage.json", coverage)
write("findings.json", {"revision": "top20-explain-v3-input-review-1", "checked_at": NOW, "scope": "입력 자료 검수. 최종원고/미디어 검수 미포함", "issue_schema": ["issue_id", "scene_id", "timecode", "severity", "문제", "evidence", "수정안", "owner", "status", "checked_revision"], "severity_allowed": ["critical", "required", "recommended"], "findings": [], "counts": {"critical": 0, "required": 0, "recommended": 0}, "conclusion": "검토한 입력 범위에서 확정 결함 없음. 대본/본편 통과 판정 아님"})
write("review_summary.json", {"revision": "top20-explain-v3-input-review-1", "checked_at": NOW, "status": "input_review_complete_final_script_pending", "price_panel_sha256": panel_sha, "price_scope": {"retrieval_date": "2026-11-03", "contract_window": ["2026-05-01", "2026-10-31"], "exclusive_area_m2": [83, 85], "area_inclusive": True, "floors": "전체 층", "cancellation_exclusion": "공식 해제표시만 제외; 정상행 추정삭제0", "transaction_types": "중개·직거래 함께", "valid_rows": 14303, "reporting_complete": False, "october_reporting_ongoing": True, "asking_prices": False}, "confirmed": ["부모 원XML 독립 재집계 receipt와 최신 패널SHA 연결. 원거래/좌표 재계산 미실행", "구·단지 중위값/n/단지명 20지역 연결; 20SVG·경계 기록SHA 일치", "사진20개 decode/SHA·축소판 확인; 정확한 촬영시점·권리·장소는 기존 메타데이터의 범위 유지", "주거특징·랜드마크/명명된 생활권·구가격·단지사례 입력 연결20행. 최종원고의 설명충분성은 대기"], "integration_guards": [{"scene_id": "S022", "guard": "2024 인천서구=현재 서해구+검단구 범위 유지. 청라호수공원 사진과 검단 단지사례는 별개 장소"}, {"scene_id": ["S017", "S015", "S014", "S010", "S008", "S004"], "guard": "다른 동·시설의 사진/주거/단지사례를 같은 현장처럼 연결하지 않음. 판교제2·3은 수정구. 2015신내역 사진과 현재환승 사실 시점분리"}, {"scene_id": ["S005", "S009", "S003"], "guard": "기흥 주거특징은 단지상가 존재의 단일사례라 비교설명 약할 수 있음. 은평뉴타운·중동신도시를 대표생활권으로 사용할 때 명칭·기능 연결. 확보근거 우선, 조사확대 없음"}], "pending_script_acceptance": ["지역/단지별 정확한 가격/n/단지명, 구별20·장면 대응", "합니다/입니다체, 문장별 수치·단위·조건, 불필요 회피/부정 반복", "첫출처 국가데이터처1회, 2024-11-01 거주통계 한계, 2026-11-03조회·5~10월계약·전용83~85㎡·전체층·중개직거래·해제표시제외·10월신고진행", "주거특징+랜드마크/명명된 생활권+지역가격+단지사례 네축의 실제원고 검수", "대표시안 준비 후 snapshot 검수 가능. 실제음성/MP4/연속재생 검수와 구분"], "coverage_file": "coverage.json", "script_gate_pass": False, "authorization": "새 대본승인 전 TTS·본편렌더·업로드 금지. 유료·외부Claude전송 금지"})
write("handoff.json", {"task_id": "top20-explain-v3-independent-review", "role": "qa", "status": "inputs_reviewed_waiting_parent_final_writer_ready", "revision": "top20-explain-v3-input-review-1", "outputs": ["findings.json", "review_summary.json", "region_review_matrix.json", "input_manifest.json", "coverage.json", "source_spotcheck.json", "photo_integrity.json", "photo_contact_sheet.jpg"], "input_version": {"price_pack": "final-api-20261103-v2", "price_panel_sha256": panel_sha, "regional_features": features["revision"], "input_manifest": "input_manifest.json"}, "validation": "부모 receipt 해시연결·구/단지수치와n20지역 대조·사진SHA/decode/축소판20장·공식2페이지4claim 표본. 확정이슈0. 원XML/좌표 재계산 없음", "unresolved": ["최종 writer 준비 알림 전 script_v6/scene_proposals_v6 미검수", "실제음성·MP4·연속재생·청취 미검수"], "affected_scene_ids": [x["scene_id"] for x in panel["regions"]], "next_owner": "director: writer최종준비 알림+고정 원고/장면표SHA 전달 → qa: 실제 문장·수치·4축 검수", "peer_message_tool": "unavailable; 총괄이 handoff와 이후 issue_<ID>.json 전달", "shared_state_modified": False, "script_gate_pass": False, "tts_render_upload_executed": False})
print(json.dumps({"status": "input_review_recorded", "regions": len(matrix), "failed_checks": failed, "outputs": sorted(p.name for p in OUT.iterdir() if p.is_file())}, ensure_ascii=False))
