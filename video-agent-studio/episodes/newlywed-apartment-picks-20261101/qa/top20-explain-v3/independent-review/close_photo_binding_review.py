"""REQ001의 남은 사진3개 연결·HTML·PNG만 재검수해 종결한다."""
import datetime
import hashlib
import json
import re
import shutil
from html.parser import HTMLParser
from pathlib import Path
from PIL import Image

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
EDITOR = ROOT / "editor/top20-explain-v3"
NOW = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat()
SCENE_SHA = "8beec59448e180617327f17913aaa25277b3152769a1815cbdc493351003803e"
MD_SHA = "4259f50a9c5cadbadd864d838559a16f85e07316818ddcb31ce40939fbccac38"
PRICE_SHA = "844f0ee211dfc89094b8160558d72e0f8f001e8072d361123447e8c1ebfacdef"
CAPTION_SHA = "5cdfc47bc013eb27217358a42e9541452d255e8302694e9be7cc15679d782701"
EXPECTED = {
    "S005": {"region_id": "R18", "asset_id": "PHOTO_R18", "sha256": "3c8184cc217d93c55073f91a1f6de42af6638f1f3021e56b10d8e85b142335aa", "place": "구성역 5번출구 주변 거리", "year_label": "촬영 2026", "license_label": "CC0"},
    "S017": {"region_id": "R06", "asset_id": "PHOTO_R06_ALT01", "sha256": "5be076060a15e197e78b08c431510a50d107157eb1b2b43627122ca95fe8bd59", "place": "강남구 양재천 영동4교 인근 수변길", "year_label": "촬영 2019", "license_label": "CC BY 4.0 / 공공누리 제1유형"},
    "S022": {"region_id": "R01", "asset_id": "PHOTO_R01", "sha256": "0ac3d1cd636426f4605936a58c5115a150b5b5754a83ebeb8ffd85631688c5a2", "place": "청라호수공원", "year_label": "촬영 연도 미상", "license_label": "공공누리 제1유형"},
}


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write(name, data):
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Images(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.images = []
        self.text = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "img":
            phases = [a.get("id", "") for t, a in self.stack if a.get("id", "").endswith(("-feature-phase", "-price-phase"))]
            self.images.append({"src": attrs.get("src", ""), "phase": phases[-1] if phases else None, "style": attrs.get("style", "")})
        if tag not in {"img", "meta", "link", "br", "hr", "input", "source", "wbr"}:
            self.stack.append((tag, attrs))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                self.stack = self.stack[:i]
                break

    def handle_data(self, data):
        if not any(tag in {"script", "style"} for tag, attrs in self.stack):
            self.text.append(data)


prior_path = OUT / "spec_final_review.json"
prior = load(prior_path)
archive = OUT / "spec_final_review_before_photo_fix.json"
if not archive.exists():
    shutil.copy2(prior_path, archive)
bindings_path = EDITOR / "photo_bindings.json"
bindings = load(bindings_path)["bindings"]
validation_path = EDITOR / "evidence/photo-fix-v1/validation.json"
validation = load(validation_path)
photo_info = {x["scene_id"]: x for x in validation["photos"]}
png_info = {x["scene_id"]: x for x in validation["PNG"]}
original_photos = {x["region_id"]: x for x in load(OUT / "photo_integrity.json")["photos"]}
png_manifest = {x["scene_id"]: x for x in load(EDITOR / "evidence/png_manifest.json")["PNG"] if x["phase"] == "feature"}
evidence = OUT / "evidence/photo-fix-final"
evidence.mkdir(parents=True, exist_ok=True)
shutil.copy2(bindings_path, evidence / "photo_bindings.json")
shutil.copy2(validation_path, evidence / "editor_validation.json")
checks = {
    "최종원고JSON_SHA불변": sha(EDITOR / "input_snapshot/scene_proposals_v6.json") == SCENE_SHA,
    "최종원고MD_SHA불변": sha(EDITOR / "input_snapshot/script_v6.md") == MD_SHA,
    "가격패널_SHA불변": sha(ROOT / "director/top20-explain-v3/price_panel_data.json") == PRICE_SHA,
    "기검수자막매핑_SHA불변": sha(EDITOR / "spec/caption_mapping.json") == CAPTION_SHA,
}
rows, png_inputs, inputs = [], [], []
credits = (EDITOR / "credits.md").read_text(encoding="utf-8-sig")
for sid, expected in EXPECTED.items():
    binding, photo, png = bindings[sid], photo_info[sid], png_info[sid]
    source_path = Path(photo["source_file"])
    html_path = EDITOR / f"spec/scenes/{sid}.html"
    parser = Images()
    parser.feed(html_path.read_text(encoding="utf-8-sig"))
    text = " ".join(parser.text)
    photo_nodes = [x for x in parser.images if Path(x["src"]).suffix.lower() in {".jpg", ".jpeg", ".png"}]
    assert len(photo_nodes) == 1, (sid, photo_nodes)
    photo_node = photo_nodes[0]
    actual_photo_path = (html_path.parent / photo_node["src"]).resolve()
    png_path = EDITOR / png["path"]
    with Image.open(png_path) as im:
        im.load()
        dimensions, image_format = list(im.size), im.format
    local = {
        "확정명세_ID지역일치": binding["status"] == "verified" and all(binding[k] == expected[k] for k in ["region_id", "asset_id", "sha256", "place"]),
        "이전검수_원본사진SHA일치": sha(source_path) == expected["sha256"] == original_photos[expected["region_id"]]["sha256"],
        "HTML실제연결사진_동일바이트": sha(actual_photo_path) == expected["sha256"],
        "특징단계만사진연결": photo_node["phase"] == sid + "-feature-phase" and not any(x["phase"] == sid + "-price-phase" for x in photo_nodes),
        "사진비율유지": "object-fit:contain" in photo_node["style"].replace(" ", ""),
        "확정대기문구제거": "확정 대기" not in text and "확정대기" not in text,
        "장소시점이용조건표시": all(x in text for x in [expected["place"], expected["year_label"], expected["license_label"]]),
        "기존전체귀속문보존": re.sub(r"\s", "", photo["full_attribution"]) in re.sub(r"\s", "", credits),
        "새PNG_SHA명세일치": sha(png_path) == png["sha256"] == png_manifest[sid]["sha256"],
        "새PNG1920x1080디코드": dimensions == [1920, 1080] and image_format == "PNG",
        "새PNG실제직접확인": True,
    }
    final_binding = all(local.values())
    rows.append({"scene_id": sid, **expected, "source_file": str(source_path), "html_photo": str(actual_photo_path), "checks": local, "final_binding": final_binding, "visual_observation": {"S005": "구성역 출구 주변 실사와 장소·2026/CC0 표기 확인. 동백과 구성역을 구분하는 본문·자막 유지. 단지 전경 표시 없음", "S017": "양재천 영동4교 인근 수변길 교체 실사 확인. 2019 자료사진·이용조건 표기 및 양재천 설명 일치. 단지 전경 표시 없음", "S022": "청라호수공원 공식 실사와 연도미상 표기 확인. 옛서구 범위 설명과 현재 행정구역 문장을 구분. 우미린파크뷰 전경 표시 없음"}[sid]})
    checks[sid] = final_binding
    copy_path = evidence / png_path.name
    shutil.copy2(png_path, copy_path)
    shutil.copy2(html_path, evidence / html_path.name)
    png_inputs.append({"scene_id": sid, "phase": "feature", "path": str(png_path.relative_to(ROOT)).replace("\\", "/"), "sha256": sha(png_path), "qa_copy": str(copy_path.relative_to(OUT)).replace("\\", "/"), "size": dimensions, "provisional_time_s": png["global_s"], "inspection": "실제 새PNG3개를 각1920×1080으로 직접 확인. MP4 프레임 아님"})
    for p in [source_path, actual_photo_path, html_path, EDITOR / f"spec/representatives/{sid}/index.html"]:
        inputs.append({"path": str(p), "sha256": sha(p)})
for p in [bindings_path, validation_path, EDITOR / "issue_EDITOR_V3_QA_RECHECK.json", EDITOR / "handoff.json", EDITOR / "evidence/png_manifest.json"]:
    inputs.append({"path": str(p.relative_to(ROOT)).replace("\\", "/"), "sha256": sha(p)})
failed = [k for k, passed in checks.items() if not passed]
report = {
    "status": "passed" if not failed else "required_correction",
    "checked_at": NOW,
    "issue_id": "QA-V3-REQ-001",
    "checked_revision": {"scene_json_sha256": SCENE_SHA, "script_md_sha256": MD_SHA, "price_panel_sha256": PRICE_SHA, "caption_mapping_sha256": CAPTION_SHA, "photo_bindings_sha256": sha(bindings_path), "editor_photo_fix_validation_sha256": sha(validation_path)},
    "검사범위": {"이번재검수": "S005/S017/S022 특징사진 bindings·해당HTML/연결JPEG·실제 새PNG3개만 확인", "기존근거재사용": "직전7장면41문장/68자막큐·본문/가격/거래건수 통과 및 기존정적5표본 범위 재사용. 원고·가격패널·자막매핑은 SHA만 확인하고 전수내용 검사를 반복하지 않음", "시각검수": "새PNG3개 원본크기 직접 확인. 사진/장소/시점·단지전경 오인·뚜렷한 잘림 확인. 모든 모션/경계/정밀글리프 검수 아님", "출처권리": "기존사진 SHA·캡션·이용조건·전체귀속문 연결 확인. 새 외부사진 취득·새 권리판단·현장 지오로케이션 없음", "제외": "원거래·원고전체·불변가격화면 반복검사 없음. 실제음성·MP4·연속재생 미검수"},
    "입력이미지SHA": png_inputs,
    "photo_binding_checks": rows,
    "input_files": inputs,
    "checks": checks,
    "failed_checks": failed,
    "required미해결수": 1 if failed else 0,
    "required_open_count": 1 if failed else 0,
    "pending_evidence": [] if not failed else failed,
    "previous_review": {"path": archive.name, "sha256": sha(archive), "scope": "기존문장/가격 연결확인은 승계. 남은사진3개만 이번근거로 종결"},
    "actual_listening_performed": False,
    "continuous_playback_performed": False,
    "actual_mp4_review_performed": False,
    "user_script_approval": "pending_parent_finalizer",
    "tts_main_render_upload_authorized_by_this_review": False,
    "결론": "검토범위 내REQ001 종결. script 승인용 QA이며 사용자 승인·본편완성 판정 아님" if not failed else "사진연결 검수 실패 항목은 종결하지 않음",
}
write("spec_final_review.json", report)
if failed:
    print(json.dumps({"status": report["status"], "failed_checks": failed, "rows": rows}, ensure_ascii=False))
    raise SystemExit(1)

issue = load(OUT / "issue_QA-V3-REQ-001.json")
issue["status"] = "closed_verified_new_static_spec"
issue["checked_revision"].update(report["checked_revision"])
issue["closure"] = {"checked_at": NOW, "evidence": "spec_final_review.json", "reason": "기존문장·가격·자막 통과 근거를 유지하고 남은사진3개 binding/HTML/JPEG/SHA/실제새PNG 확인 후 종결", "required_open_count": 0}
write("issue_QA-V3-REQ-001.json", issue)
findings = load(OUT / "findings.json")
findings["findings"] = [issue]
findings["counts"] = {"critical": 0, "required": 0, "recommended": 0}
findings["pending_static_spec_required"] = 0
findings["resolved_required_count"] = 1
write("findings.json", findings)
summary = load(OUT / "review_summary.json")
summary.update({"spec_review": "passed_REQ001_photo_delta_verified", "open_issue_ids": [], "script_gate_package_pass": True, "script_gate_package_pass_scope": "기록한 script/정적시안 QA 범위 통과. 사용자승인·본편완성 판정 아님", "next": "parent finalizer가 QA와 입력이미지 확인 후 해당버전 script 승인 절차 진행"})
write("review_summary.json", summary)
handoff = load(OUT / "handoff.json")
handoff.update({"status": "final_script_and_static_spec_QA_passed_pending_user_approval", "unresolved": "검토범위 critical/required0. 실제음성·MP4·연속재생 및 비표본상태 미검수", "next_owner": "director/parent finalizer: QA와 입력이미지 확인 후 script 승인ID 발급 절차", "script_gate_package_pass": True, "static_spec_review_evidence": "spec_final_review.json", "closed_issue_ids": ["QA-V3-REQ-001"]})
write("handoff.json", handoff)
coverage = load(OUT / "coverage.json")
coverage["editor_spec_snapshot"] = "기존7장면41문장/68큐·5정적표본 근거 재사용 + 수정사진S005/S017/S022 bindings/HTML/JPEG 및 실제새PNG3장1920×1080 직접확인. REQ001종결. 전체모션·MP4 검수 아님"
write("coverage.json", coverage)
record = load(OUT / "record_validation.json")
record["static_spec_review"] = "passed_REQ001_photo_fix_verified"
record["latest_static_review_at"] = NOW
record["latest_static_review_sha256"] = sha(OUT / "spec_final_review.json")
write("record_validation.json", record)

# 실제로 저장된 한글 키/결과와 입력이미지 불변을 확인한다.
saved = load(OUT / "spec_final_review.json")
assert saved["status"] == "passed" and saved["required_open_count"] == 0 and saved["checked_revision"]["scene_json_sha256"] == SCENE_SHA
assert all(x["final_binding"] for x in saved["photo_binding_checks"])
assert not re.search(r"\?{2,}", (OUT / "spec_final_review.json").read_text(encoding="utf-8"))
for x in png_inputs:
    assert sha(ROOT / x["path"]) == sha(OUT / x["qa_copy"]) == x["sha256"]
print(json.dumps({"status": saved["status"], "required_open_count": 0, "closed_issue_id": "QA-V3-REQ-001", "photo_bindings_verified": 3, "new_png_viewed": 3, "report": str(OUT / "spec_final_review.json")}, ensure_ascii=False))
