"""QA 기록을 UTF-8 파일에서 직접 저장한다. 다른 담당 파일은 수정하지 않는다."""
import datetime
import hashlib
import json
import re
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
NOW = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat()


def read(name):
    return json.loads((OUT / name).read_text(encoding="utf-8-sig"))


def write(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


script = read("script_review.json")
assert script["status"] == "passed"
script["method"] = "20개 지역의 실제 표시문·읽기문 의미를 검토하고, 읽기문의 한글 금액·거래건수를 독립 파싱해 대조. 원거래 재집계·좌표 재계산 없음"
write("script_review.json", script)
checked = script["checked_revision"]

# 저장 단계에서 소실된 QA 설명·필드만 복구한다. 증거 원파일은 보존한다.
photos = read("photo_integrity.json")
photos["inspection"] = "사진 파일20개 decode·SHA 대조 및 축소 contact sheet 생성. 정확한 장소의 독립 측량·신규 이용허락 심사와 구분"
write("photo_integrity.json", photos)
source = read("source_spotcheck.json")
source["method"] = "지정된 공식 URL 2건의 해당 본문만 독립 재열람. 새 주제 조사 없음"
source["sources"][0]["section"] = "현황·추진경위 L728~744"
source["sources"][0]["result"] = "정비계획 세대수와 준공인가 시점 일치. 현재 실거주 세대수로 확대하지 않음"
kapt = source["sources"][1]
kapt["section"] = "표 머리 L5~6, 대상 행 L60·214·216"
for row, name, address in zip(kapt["observations"], ["개포자이프레지던스", "개포주공6단지", "e편한세상 문래 에듀플라츠"], ["강남구 개포동 189", "강남구 개포동 185", "영등포구 문래동6가 36"]):
    row["name"], row["address_area"] = name, address
kapt["result"] = "지역특징 입력의 수치·사용승인일·주소 일치. 가격 또는 실제 입주율의 근거로 확대하지 않음"
source["coverage_limit"] = "공식 원문 전량을 독립 재열람하지 않음. 나머지는 소스ID·기준일·표현범위 정합성 검토. 로컬 캡처8건 실패를 원문 독립확인으로 간주하지 않음. 기흥구 보완은 부모의 지정 근거 승계이며 새 외부열람 없음"
write("source_spotcheck.json", source)
snapshots = read("spec_snapshot_manifest.json")
for row in snapshots["inputs"]:
    row["viewed"] = "기존 PNG의 축소 contact sheet를 프레임당960×540으로 실제 확인. 정밀 글리프 경계·최대줌·연속재생 아님"
snapshots["older_batch"] = "이전 배치의 placeholder·구기관명은 현재 결함 근거로 승계하지 않음"
snapshots["status"] = "원고 수정 중 만든 구시안. 최종8bee/4259 기반 새 정적 시안 검수 대기"
write("spec_snapshot_manifest.json", snapshots)

issue = {
    "issue_id": "QA-V3-REQ-001",
    "scene_id": ["O002", "S005", "S006", "S007", "S017", "S019", "S022"],
    "timecode": "구 대표시안 임시시간12.0/131.4/165.9/230.1/271.4초. 실제 MP4 시간 아님",
    "severity": "required",
    "문제": "원고 수정 중 만든 구 대표시안의 본문·자막 매핑이 통합v6 이전 문장과 누락ID를 사용했습니다. 부모가 같은 문제를 확인해 최종8bee/4259 기반 재생성을 지시했으며 editor 작업 중입니다. 최종 원고 자체의 결함과 분리합니다.",
    "evidence": [
        {"path": "evidence/spec-v1/caption_mapping.json", "sha256": sha(OUT / "evidence/spec-v1/caption_mapping.json"), "detail": "S005-03 동백호수공원·S005-04 신갈천 연결 문장이 구버전으로 남음. 대표7장면의 가격-20/-21과 주거특징-02 누락을 확인"},
        {"path": "evidence/spec-v1/frame-01-at-131.4s.png", "detail": "S006의 본문·자막은 구 보트하우스 문장. 최종원고는 산책정원·수로 주변 여가시설 설명"},
        {"path": "evidence/spec-v1/frame-03-at-230.1s.png", "detail": "S019의 본문·자막은 구 온실 문장. 최종원고는 식물전시·야외공원의 여가 공간 설명"},
        {"path": "spec_snapshot_manifest.json", "detail": "구 정적PNG5개 SHA·QA 사본. 실제 음성·MP4의 결함으로 판단하지 않음"},
    ],
    "수정안": "editor가 최종 원고SHA를 입력에 고정하고 sentence_id별 표시문·자막 및 주거특징·가격 문장을 다시 연결합니다. 새 정적시안과 caption_mapping의 변경 장면·연결 부분만 QA 재검수합니다. 새로운 기획·자료·문장·TTS·본편렌더를 추가하지 않습니다.",
    "owner": "editor; director가 최종SHA와 재생성 결과 전달",
    "status": "awaiting_new_static_spec_recheck",
    "checked_revision": {**checked, "observed_old_spec_batch": snapshots["batch"]},
    "impact": "script 게이트의 대표시안 패키지. 최종 대본은 별도 독립 검수 통과. 확인되지 않은 새시안을 총괄 의견만으로 통과시키지 않음",
}
write("issue_QA-V3-REQ-001.json", issue)
write("findings.json", {"revision": "final-v6-script-review", "checked_at": NOW, "scope": "최종 원고133문장·20개지역의 가격/조건/특징/읽기문. 구 대표시안 문제와 새 정적시안 재검수 대기 분리", "findings": [issue], "counts": {"critical": 0, "required": 1, "recommended": 0}, "script_only_open_counts": {"critical": 0, "required": 0, "recommended": 0}, "pending_static_spec_required": 1, "checked_revision": checked})

manifest = read("input_manifest.json")
for p, scope in [
    (ROOT / "writer/top20-explain-v3/script_v6.md", "최종133문장 MD와 장면표의 문장 일치 확인"),
    (ROOT / "writer/top20-explain-v3/scene_proposals_v6.json", "최종본문20지역·40가격/40거래건수·읽기문·claim·화면조건 검토"),
    (ROOT / "research/top20-explain-v3/director_supplement.json", "S005-02 지정 보완문구·근거범위만 대조. 새 공식페이지 외부열람 없음"),
    (ROOT / "research/top20-8min-v2/top20.json", "기존 승인 통계20개 행과 원고 수치 연결만 확인. 원통계 새 집계 없음"),
]:
    manifest["inputs"].append({"path": str(p.relative_to(ROOT)).replace("\\", "/"), "sha256": sha(p), "bytes": p.stat().st_size, "scope": scope})
manifest.pop("not_read_pending_ready", None)
manifest["final_checked_revision"] = checked
manifest["script_frozen_copies"] = ["reviewed-inputs/" + checked["script_md_sha256"] + "_script_v6.md", "reviewed-inputs/" + checked["scene_json_sha256"] + "_scene_proposals_v6.json"]
manifest["final_script_check_at"] = script["checked_at"]
write("input_manifest.json", manifest)
coverage = read("coverage.json")
coverage.update({"script_v6": "최종MD4259/JSON8bee 검토완료. 133문장·20지역·40가격·40거래건수·20거주수·4축 의미검토", "scene_proposals_v6": "최종8bee 검토완료. 마지막 O002-02 한 문장만 변경 재확인", "editor_spec_snapshot": "구시안5프레임 축소판 확인. 최종 원고와 구시안의 불일치 기록. 새 정적시안 재검수 대기", "actual_listening_performed": False, "continuous_playback_performed": False})
write("coverage.json", coverage)
previous_summary = read("review_summary.json")
write("input_review_summary.json", previous_summary)
write("review_summary.json", {"revision": "final-v6-independent-script-review", "checked_at": NOW, "script_review": "passed", "checked_revision": checked, "result": "20지역 가격40개·거래건수40개·거주수20개·133문장·표시문/읽기문 및4축 검수 통과. 원거래/좌표 계산은 부모 근거 승계", "source_scope": "기존 가격/사진/특징 입력 검수와 공식2페이지4claim 표본 근거 재사용. S005 보완은 부모의 지정 공식페이지 검증을 승계하고 문구·scope 대조만 수행", "last_delta": "O002-02 혼인신고 후5년 미만 대상 정의 한 문장 복원. 최종 읽기문도 확인", "conditions": "계약5~10월·11월3일조회·전용83~85㎡ 양끝 포함·전체층·중개+직거래·표시해제행제외·n유효기록. 핵심기간/면적/10월신고진행은 낭독, 상세조건은 O002-B2 화면지시로 보존", "spec_review": "awaiting_new_static_spec_recheck", "open_issue_ids": ["QA-V3-REQ-001"], "script_gate_package_pass": False, "user_script_approval": "pending", "actual_listening_performed": False, "continuous_playback_performed": False, "media_completion_judgment": "실제음성/MP4 없음. 본편완성 판정 아님", "next": "새 정적시안 생성 완료 알림·입력SHA 후 영향 장면과 연결 부분 재검수"})
write("handoff.json", {"task_id": "top20-explain-v3-independent-review", "role": "qa", "status": "final_script_passed_waiting_new_static_spec", "checked_revision": checked, "outputs": ["script_review.json", "findings.json", "issue_QA-V3-REQ-001.json", "review_summary.json", "input_manifest.json", "coverage.json", "region_review_matrix.json", "source_spotcheck.json", "photo_integrity.json", "spec_snapshot_manifest.json"], "validation": "최종133문장·20지역·가격40/거래건수40/거주수20 일치. 합니다체·첫출처1회·기준일·조건·4축 검토. 마지막O002-02만 변경 재확인. 원XML·좌표 재계산 없음", "unresolved": "REQ001: 구시안을 최종8bee/4259로 재생성 중. 새 정적시안 영향검증 대기. 원고 필수미해결0", "affected_scene_ids": issue["scene_id"], "next_owner": "editor→director: 새 정적시안·caption_mapping·입력SHA 전달, qa: 영향장면 재검수", "actual_listening_performed": False, "continuous_playback_performed": False, "script_gate_package_pass": False, "user_script_approval": "pending", "tts_main_render_upload_executed": False, "shared_state_modified": False})

# 기록 검증: JSON 구조·필수 한글키·한글 소실 흔적·최종 입력SHA를 실제로 확인한다.
required = {"issue_id", "scene_id", "timecode", "severity", "문제", "evidence", "수정안", "owner", "status", "checked_revision"}
assert required <= read("issue_QA-V3-REQ-001.json").keys()
assert "원고 수정 중" in read("issue_QA-V3-REQ-001.json")["문제"]
bad = []
for path in OUT.glob("*.json"):
    text = path.read_text(encoding="utf-8")
    json.loads(text)
    if re.search(r"\?{2,}", text):
        bad.append(path.name)
assert not bad, bad
assert sha(ROOT / "writer/top20-explain-v3/script_v6.md") == checked["script_md_sha256"]
assert sha(ROOT / "writer/top20-explain-v3/scene_proposals_v6.json") == checked["scene_json_sha256"]
write("record_validation.json", {"checked_at": NOW, "status": "passed", "checks": {"all_root_json_parse": True, "issue_required_korean_keys": True, "issue_korean_text_preserved": True, "question_mark_loss_scan": "0건", "final_script_hashes_match": True}, "repair": "셸 here-string 파이프의 한글 소실을 UTF-8 소스파일에서 직접 작성하는 방식으로 복구. 이슈·사진검수 설명·출처 표본기록·시안manifest의 손상 설명 복구", "script_review": "passed", "static_spec_review": "awaiting_regeneration"})
print(json.dumps({"status": "최종원고 검수 마감·UTF8 기록 복구 확인", "script": "passed", "static_spec": "awaiting_new_static_spec_recheck", "open_issue_ids": [issue["issue_id"]], "encoding_question_mark_loss": bad}, ensure_ascii=False))
