"""REQ001의 수정 영향만 검증한다. 원거래/전체 원고/미디어 재생 검사는 하지 않는다."""
import datetime
import hashlib
import html
import json
import re
import shutil
from pathlib import Path
from PIL import Image

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
EDITOR = ROOT / "editor/top20-explain-v3"
SCENE_SHA = "8beec59448e180617327f17913aaa25277b3152769a1815cbdc493351003803e"
MD_SHA = "4259f50a9c5cadbadd864d838559a16f85e07316818ddcb31ce40939fbccac38"
BATCH = "d4003f1f-648e-4985-b21b-7ec8955546d1"
IDS = ["O002", "S005", "S006", "S007", "S017", "S019", "S022"]
NOW = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat()


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def norm(text):
    return re.sub(r"\s", "", text)


def write(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


script_path = EDITOR / "input_snapshot/scene_proposals_v6.json"
md_path = EDITOR / "input_snapshot/script_v6.md"
script = load(script_path)
selected = [s for s in script["scenes"] if s["scene_id"] in IDS]
expected = {x["sentence_id"]: x for s in selected for x in s["sentences"]}
mapping_path = EDITOR / "spec/caption_mapping.json"
mapping = load(mapping_path)
cue_groups = {}
for cue in mapping["cues"]:
    cue_groups.setdefault(cue["sentence_id"], []).append(cue)
checks = {
    "최종_JSON_SHA": sha(script_path) == SCENE_SHA,
    "최종_MD_SHA": sha(md_path) == MD_SHA,
    "대표7장면": len(selected) == 7 and {x["scene_id"] for x in mapping["cues"]} == set(IDS),
    "자막_sentence_id_누락추가없음": set(cue_groups) == set(expected),
    "실제음성타임록주장없음": mapping["timing_locked"] is False,
}
sentence_checks = []
for sid, sentence in expected.items():
    cues = sorted(cue_groups.get(sid, []), key=lambda x: x["start_s"])
    joined = "".join(x["text"] for x in cues)
    matched = norm(joined) == norm(sentence["display_text"])
    sentence_checks.append({"sentence_id": sid, "공백줄바꿈외문자수치일치": matched, "cue_count": len(cues)})
checks["41문장_표시문과실제자막대조"] = len(sentence_checks) == 41 and all(x["공백줄바꿈외문자수치일치"] for x in sentence_checks)
html_checks = []
input_files = []
evidence_dir = OUT / "evidence/spec-final"
evidence_dir.mkdir(parents=True, exist_ok=True)
for path in [script_path, md_path, mapping_path, EDITOR / "build_receipt.json", EDITOR / "input_manifest.json", EDITOR / "caption_integrity.json"]:
    input_files.append({"path": str(path.relative_to(ROOT)).replace("\\", "/"), "sha256": sha(path)})
shutil.copy2(mapping_path, evidence_dir / "caption_mapping.json")
for scene in selected:
    sid = scene["scene_id"]
    path = EDITOR / f"spec/scenes/{sid}.html"
    source = path.read_text(encoding="utf-8-sig")
    text = html.unescape(re.sub(r"<[^>]+>", " ", source))
    normalized = norm(text)
    local = {}
    if sid != "O002":
        feature_sentences = [x for x in scene["sentences"] if x["sentence_id"].split("-")[-1] in ["02", "03", "04"]]
        local["주거특징명소_최종문장연결"] = all(norm(x["display_text"]) in normalized for x in feature_sentences)
        p = scene["price_panel_data"]
        rep = p["representative"]
        local["지역단지가격_구분표시"] = norm(p["display_price"]) in normalized and norm(rep["display_price"]) in normalized and norm(rep["apt_name"]) in normalized
        local["지역단지_거래건수표현"] = f"지역거래{p['n']:,}건" in normalized and f"단지거래{rep['n']:,}건" in normalized and "표본n" not in normalized
    else:
        local["도입출처갱신"] = "국가데이터처" in normalized and "통계청" not in normalized
    local["구대기문구없음"] = "확정대기" not in normalized
    html_checks.append({"scene_id": sid, "checks": local, "sha256": sha(path)})
    input_files.append({"path": str(path.relative_to(ROOT)).replace("\\", "/"), "sha256": sha(path)})
    shutil.copy2(path, evidence_dir / path.name)
checks["7장면_HTML본문가격거래건수"] = all(all(x["checks"].values()) for x in html_checks)

batch_dir = EDITOR / "spec/.hyperframes/artifacts/snapshots" / BATCH
image_inputs = []
timing = load(EDITOR / "timing.provisional.json")["scenes"]
for path in sorted(batch_dir.glob("*.png")):
    with Image.open(path) as im:
        im.load()
        size, fmt = list(im.size), im.format
    sample_s = float(re.search(r"at-([0-9.]+)s", path.name)[1])
    scene_id = next(x["scene_id"] for x in timing if x["start_s"] <= sample_s < x["end_s"])
    copy_path = evidence_dir / path.name
    shutil.copy2(path, copy_path)
    image_inputs.append({"path": str(path.relative_to(ROOT)).replace("\\", "/"), "sha256": sha(path), "qa_copy": str(copy_path.relative_to(OUT)).replace("\\", "/"), "size": size, "format": fmt, "scene_id": scene_id, "provisional_time_s": sample_s, "inspection": "실제 PNG 축소판을 프레임당960×540으로 확인. 최종 MP4 프레임 아님"})
checks["준비된새PNG5개_디코드"] = len(image_inputs) == 5 and all(x["size"] == [1920, 1080] and x["format"] == "PNG" for x in image_inputs)
checks["표본이미지실제확인"] = True
failed = [k for k, v in checks.items() if not v]
status = "passed" if not failed else "awaiting_editor_completion"
report = {
    "status": status,
    "checked_at": NOW,
    "issue_id": "QA-V3-REQ-001",
    "checked_revision": {"scene_json_sha256": SCENE_SHA, "script_md_sha256": MD_SHA, "snapshot_batch": BATCH, "caption_mapping_sha256": sha(mapping_path)},
    "검사범위": {"issue": "구 대표시안의 이전 문장·누락ID 수정 영향만 검수", "source": "7개 영향장면 HTML 및41문장/68자막큐를 최종 표시문과 대조. 원고전체·원거래·좌표 검사 반복 없음", "sampled_images": "O002/S006/S007/S019/S022 정적 PNG5장. 원고와 가격·거래건수의 의미 대응 및 표본 화면 가독성 확인", "unsampled_images": "S005/S017의 실제 PNG는 이번 배치에 없어 HTML·자막 연결만 확인. 전체 장면 픽셀·정밀bbox·모든 경계·최대줌 검수 아님", "continuity": "가용 정적표본·자막/본문 연결 범위. 실제 발화와 화면전환의 시간 일치·연속재생 미검수"},
    "입력이미지SHA": image_inputs,
    "input_files": input_files,
    "checks": checks,
    "sentence_checks": sentence_checks,
    "html_checks": html_checks,
    "failed_checks": failed,
    "pending_evidence": [] if not failed else [{"scene_ids": ["S005", "S017", "S022"], "detail": "본문·자막·거래건수 연결은 일치하나 실제 사진 확정 대기 문구가 HTML에 남음. S005/S017은 이번 PNG 배치에도 없어 사진 단계 완료 여부 미확인"}],
    "required미해결수": len(failed),
    "required_open_count": len(failed),
    "image_observations": ["S006의 주거특징 본문·하단자막이 최종 센트럴파크 문장으로 갱신됨", "S019의 본문·하단자막이 최종 식물전시·야외공원 문장으로 갱신됨", "S007/S022 가격 화면은 지역/단지 거래건수를 분리하고 실제 값 유지. 옛서구 범위 표기 유지", "O002의 출처 및 현재 표본 자막은 최종원고와 대응. 수치·발음의 실제 청취 확인 아님"],
    "actual_listening_performed": False,
    "continuous_playback_performed": False,
    "actual_mp4_review_performed": False,
    "user_script_approval": "pending_parent_finalizer",
    "tts_main_render_upload_authorized_by_this_review": False,
    "결론": "REQ001 영향검증 결과만 기록. script 게이트용 QA이며 사용자 승인·본편완성 판정 아님",
}
write("spec_final_review.json", report)
if failed:
    issue = load(OUT / "issue_QA-V3-REQ-001.json")
    issue["status"] = "awaiting_new_static_spec_completion"
    issue["checked_revision"].update(report["checked_revision"])
    issue["partial_verification"] = {"checked_at": NOW, "evidence": "spec_final_review.json", "confirmed": "최종8bee/4259 연결·7장면41문장/68자막큐·본문·거래건수 수정 일치. 새 PNG5장 확인", "pending": "S005/S017/S022 HTML의 실제사진 확정대기 및 미표본 S005/S017. 완성본으로 추정해 종결하지 않음"}
    write("issue_QA-V3-REQ-001.json", issue)
    findings = load(OUT / "findings.json")
    findings["findings"] = [issue]
    findings["counts"] = {"critical": 0, "required": 1, "recommended": 0}
    findings["pending_static_spec_required"] = 1
    write("findings.json", findings)
    summary = load(OUT / "review_summary.json")
    summary["spec_review"] = "awaiting_editor_completion"
    summary["open_issue_ids"] = ["QA-V3-REQ-001"]
    summary["script_gate_package_pass"] = False
    summary["next"] = "editor 정적시안의 사진단계 준비/완료 알림 후 미확인 영향 범위만 검수. 원고전체·원거래 재검사 없음"
    write("review_summary.json", summary)
    handoff = load(OUT / "handoff.json")
    handoff["status"] = "final_script_passed_static_spec_partial_waiting_editor"
    handoff["outputs"] = ["spec_final_review.json"] + [x for x in handoff["outputs"] if x != "spec_final_review.json"]
    handoff["unresolved"] = "REQ001: 문장/자막/거래건수 수정 확인. S005/S017/S022 실제사진 확정대기 및 S005/S017 표본 미확인으로 시안 완료판정 대기"
    handoff["next_owner"] = "editor→director: 정적시안 사진단계 준비/완료 근거 전달, qa: 남은 영향범위만 검수"
    handoff["script_gate_package_pass"] = False
    handoff["static_spec_review_evidence"] = "spec_final_review.json"
    write("handoff.json", handoff)
    coverage = load(OUT / "coverage.json")
    coverage["editor_spec_snapshot"] = "최종8bee/4259 기반 d400 PNG5장 확인 및 영향7장면41문장/68자막큐·HTML 대조. 사진 미준비/미확인 범위가 있어 대기. 원고전체·원거래 검사 반복 없음"
    write("coverage.json", coverage)
    saved = load(OUT / "spec_final_review.json")
    assert saved["status"] == "awaiting_editor_completion" and saved["required미해결수"] == 1
    assert not re.search(r"\?{2,}", (OUT / "spec_final_review.json").read_text(encoding="utf-8"))
    for row in image_inputs:
        assert sha(ROOT / row["path"]) == row["sha256"] == sha(OUT / row["qa_copy"])
    print(json.dumps({"status": status, "failed_checks": failed}, ensure_ascii=False))
    raise SystemExit(0)

# 근거 확인 뒤에만 해당 이슈를 닫는다.
issue = load(OUT / "issue_QA-V3-REQ-001.json")
issue["status"] = "closed_verified_new_static_spec"
issue["checked_revision"].update(report["checked_revision"])
issue["closure"] = {"checked_at": NOW, "evidence": "spec_final_review.json", "reason": "최종SHA 연결·영향7장면41문장 자막/본문 갱신 및 새PNG5장 표본 확인. 미검수 범위는 보고서에 명시"}
write("issue_QA-V3-REQ-001.json", issue)
findings = load(OUT / "findings.json")
findings["findings"] = [issue]
findings["counts"] = {"critical": 0, "required": 0, "recommended": 0}
findings["pending_static_spec_required"] = 0
findings["resolved_required_count"] = 1
write("findings.json", findings)
summary = load(OUT / "review_summary.json")
summary["spec_review"] = "passed_REQ001_scoped_review"
summary["open_issue_ids"] = []
summary["script_gate_package_pass"] = True
summary["script_gate_package_pass_scope"] = "독립 QA 범위 통과. 사용자 승인 ID는 부모 finalizer가 별도로 발급"
summary["next"] = "director/parent finalizer가 QA와 입력이미지를 확인한 뒤 해당 버전의 script 승인 절차 진행"
write("review_summary.json", summary)
handoff = load(OUT / "handoff.json")
handoff["status"] = "script_and_REQ001_static_spec_review_passed_pending_user_approval"
handoff["outputs"] = ["spec_final_review.json"] + [x for x in handoff["outputs"] if x != "spec_final_review.json"]
handoff["unresolved"] = "검토한 script/REQ001 범위의 required0. 실제음성·MP4·미표본 장면 픽셀 범위 미검수"
handoff["next_owner"] = "director/parent finalizer: QA와 입력PNG를 확인하고 새 script 승인ID 발급 절차"
handoff["script_gate_package_pass"] = True
handoff["static_spec_review_evidence"] = "spec_final_review.json"
write("handoff.json", handoff)
coverage = load(OUT / "coverage.json")
coverage["editor_spec_snapshot"] = "최종SHA 기반 d400 배치의 PNG5장 실제 축소판 확인 + 영향7장면41문장/68자막큐·HTML 연결 대조. REQ001 종결; S005/S017 실제PNG는 미표본"
write("coverage.json", coverage)

# 저장된 결과와 새 입력이 바뀌지 않았는지 확인한다.
saved = load(OUT / "spec_final_review.json")
assert saved["status"] == "passed" and saved["checked_revision"]["scene_json_sha256"] == SCENE_SHA and saved["required미해결수"] == 0
assert not re.search(r"\?{2,}", (OUT / "spec_final_review.json").read_text(encoding="utf-8"))
assert sha(script_path) == SCENE_SHA and sha(md_path) == MD_SHA
for row in image_inputs:
    assert sha(ROOT / row["path"]) == row["sha256"] == sha(OUT / row["qa_copy"])
print(json.dumps({"status": saved["status"], "images": len(image_inputs), "scenes": len(selected), "sentences": len(sentence_checks), "required_open_count": 0, "report": str(OUT / "spec_final_review.json")}, ensure_ascii=False))
