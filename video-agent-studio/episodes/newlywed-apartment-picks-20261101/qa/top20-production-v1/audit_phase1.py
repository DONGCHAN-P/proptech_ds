"""해시 연결·정적 입력 검사. 육안 판정은 실제 열람한 PNG에만 적용한다."""
from pathlib import Path
import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from PIL import Image

OUT = Path(__file__).resolve().parent
EP = OUT.parent.parent
ROOT = EP.parents[2]
NOW = datetime.now(timezone.utc).isoformat()
def read(rel):
    return json.loads((EP / rel).read_text(encoding="utf-8-sig"))
def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name, data):
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
def record(p):
    p = Path(p)
    return {"path": str(p), "sha256": sha(p), "bytes": p.stat().st_size}

OUT.mkdir(parents=True, exist_ok=True)
evidence_dir = OUT / "evidence/phase1"
evidence_dir.mkdir(parents=True, exist_ok=True)
thumb = EP / "outputs/top20-production-v1/thumbnail"
rep = EP / "editor/top20-production-v1/evidence/representative3"
viewed = [
    (thumb / "TH001_신혼부부_수도권TOP20_1280x720.png", "TH001", None, "delivered_thumbnail"),
    (thumb / "TH001_신혼부부_수도권TOP20_mobile_320.png", "TH001", None, "delivered_thumbnail_mobile"),
    (rep / "frame-00-at-133s.png", "I001", 133, "hyperframes_snapshot_provisional"),
    (rep / "frame-01-at-248s.png", "I002", 248, "hyperframes_snapshot_provisional"),
    (rep / "frame-02-at-270s.png", "S013", 270, "hyperframes_snapshot_provisional"),
    (EP / "editor/top20-production-v1/evidence/baseline_current_sheet.jpg", "channel_reference", None, "baseline_contactsheet"),
]
media = []
for p, scene, time, kind in viewed:
    dest = evidence_dir / p.name
    if not dest.exists():
        shutil.copy2(p, dest)
    assert sha(dest) == sha(p), str(p)
    with Image.open(p) as im:
        im.load()
        dims, fmt = list(im.size), im.format
    media.append({**record(p), "scene_id": scene, "timecode_seconds_provisional": time,
                  "kind": kind, "format": fmt, "dimensions": dims,
                  "visually_viewed": True, "qa_evidence_copy": str(dest),
                  "encoded_mp4_frame": False})
assert media[0]["dimensions"] == [1280,720]
assert media[1]["dimensions"] == [320,180]
assert all(m["dimensions"] == [1920,1080] for m in media[2:5])
save("media_facts.json", {"checked_at": NOW, "media": media,
     "mp4_inspected": [], "codec_duration_audio_streams": "unchecked_no_encoded_media_supplied"})

reuse = read("qa/top20-8min-v2/reuse_receipt.json")
followup = read("qa/top20-8min-v2/media_followup.json")
photo_ledger = read("qa/top20-8min-v2/followup_photo_ledger.json")
hash_checks = []
def expected(p, value, scope):
    row = {**record(p), "expected_sha256": value, "matches": sha(p) == value, "scope": scope}
    hash_checks.append(row)
    return row
expected(ROOT / "analysis/newlywed_region_2024/rankings.json", reuse["expected_rankings_sha256"], "기존 통계 QA 불변 입력")
expected(reuse["prior_review_path"], reuse["prior_review_sha256"], "기존 독립 순위 QA 기록")
for row in followup["prior_qa_reuse"]["inputs"]:
    expected(row["path"], row["current_sha256"], "기존 수치·지도 QA 입력")
expected(followup["selected_photo_manifest"], followup["selected_photo_manifest_sha256"], "승인 사진 v2 원장")
for row in photo_ledger["rows"]:
    expected(row["file"], row["sha256"], "사진 픽셀 재검수 없는 SHA 재사용")
    expected(row["source_snapshot"], row["source_snapshot_sha256"], "개별 사진 출처·라이선스 저장 증거")
maps = read("visual/top20-8min-v2/maps/map_assets.json")
for row in maps["assets"]:
    expected(EP / row["actual_file"], row["sha256"], "지도 PNG 기존 검수 재사용")
save("reuse_receipt.json", {"checked_at": NOW, "hash_checks": hash_checks,
     "all_match": all(x["matches"] for x in hash_checks),
     "previous_review": ["qa/ranking_source_review.json", "qa/top20-8min-v2/findings.json", "qa/top20-8min-v2/media_followup.json"],
     "original_86_row_audit_repeated": False, "map_geometry_reaudit": False,
     "photo_metadata_reaudit": False, "source_web_requery": False,
     "inherited_limits": ["기존 원표 텍스트 검수 범위·이미지 미확인 제한 유지", "사진별 장소 확인 정밀도 제한 유지", "최종 구도에서의 제3자 권리 전면 보증으로 확대하지 않음"]})
assert all(x["matches"] for x in hash_checks)

script_path = EP / "writer/top20-8min-v2/script_v3.md"
script = script_path.read_text(encoding="utf-8-sig")
scenes = read("writer/top20-8min-v2/scene_proposals_v3.json")["scenes"]
top = read("research/top20-8min-v2/top20.json")
by_scene = {x["scene_id"]: x for x in scenes}
def count_number(s):
    m = re.search(r"((?:\d만\s*)?\d[\d,]*)쌍", s)
    value = m.group(1).replace(",", "").replace(" ", "")
    if "만" in value:
        a,b = value.split("만")
        return int(a)*10000+int(b)
    return int(value)
rank_checks = [{"scene_id": r["scene_id"], "region_id": r["region_id"], "rank": r["rank"],
                "approved_count": r["newlywed_couples"],
                "script_count": count_number(by_scene[r["scene_id"]]["narration_text"])} for r in top["regions"]]
assert all(r["approved_count"] == r["script_count"] for r in rank_checks)
narration = script.split("## 낭독",1)[1].split("## 화면 메모",1)[0]
blocks = re.split(r"(?m)^### ", narration)[1:]
def norm(s): return re.sub(r"\s+", " ", s).strip()
text_checks = []
for block in blocks:
    title, text = block.split("\n",1)
    sid = title.split()[0]
    text_checks.append({"scene_id": sid, "script_matches_scene_proposal": norm(text) == norm(by_scene[sid]["narration_text"])})
assert all(r["script_matches_scene_proposal"] for r in text_checks)
authorization = read("director/top20-production-v1/authorization.json")
assert sha(script_path) == authorization["script_sha256"]
save("input_audit.json", {"checked_at": NOW, "script": record(script_path),
     "script_matches_current_authorization_hash": True, "rank_checks": rank_checks,
     "narration_scene_join_checks": text_checks,
     "scope": {"O001": "수도권 53개 구 가운데", "O002": "2024년 11월 1일·거주 신혼부부 전체·쌍", "S003": "2024년 재설치 원미구·2023 비교값 null 유지", "S022": "2024년 당시 옛 서구·현재 서해구+검단구 범위"},
     "viewer_observations": ["거주 규모와 전년 변화·거주 원인을 구분", "사진 지명을 v2 원장과 연결", "신규 대본 작성·변경 요청 없음"],
     "shorts": {"promo": read("editor/top20-production-v1/shorts/promo/clip_contract.json"), "content": read("editor/top20-production-v1/shorts/content/clip_contract.json"), "exact_narration_review": "unchecked_exact_clips_empty"},
     "source_licenses": {"selected_thumbnail_photos": ["PHOTO_R03", "PHOTO_R02_ALT01"], "both": "CC0 1.0", "credits_file": str(next(thumb.glob("*.md"))), "basis": "기존 독립 QA 사진 원장·개별 원문 증거 SHA 일치. 현재 썸네일에서 삼송2021·석촌호수2025 라벨 및 수변 구도 확인."}})

issue = {"issue_id": "QA-T20P-TH-SCOPE-01", "scene_id": ["TH001"], "timecode": None,
    "severity": "required", "문제": "썸네일의 ‘수도권 TOP20’과 ‘2024년 신혼부부 수 기준’에 모집단 53개 구가 빠져 시·군 포함 전체 수도권 순위로 읽힐 수 있음.",
    "evidence": {"media": media[:2], "visible_text": ["수도권 TOP20", "2024년 신혼부부 수 기준"], "approved_scope": top["scope"], "script": "O001 수도권 53개 구 가운데"},
    "수정안": "제목 또는 기준 문구에 ‘수도권 53개 구 중 TOP20’을 긍정형으로 명시. 320px에서도 53개 구가 읽히게 배치한 새 버전 PNG 두 크기를 제출. 기존 제목·사진 디자인 전면 재제작 불필요.",
    "owner": "visual", "status": "open", "checked_revision": {"revision": "top20-production-v1", "png_sha256": [m["sha256"] for m in media[:2]]},
    "impact": "TH001 및 해당 업로드 썸네일만. 통계·사진 원본·본편 대본 변경 없음.",
    "delivery": {"to": "visual", "cc": "director", "direct_peer_message_available": False, "route": "총괄이 이 경로를 담당자에게 전달"}}
save("issue_QA-T20P-TH-SCOPE-01.json", issue)
representatives = {"task_id": "top20-production-independent-qa-v1", "checked_at": NOW,
    "verdict": "pass_for_three_provisional_snapshots_only", "required_changes": [], "critical_open": 0, "required_open": 0,
    "scenes": [
      {"scene_id": "I001", "media": media[2], "observed": "7,797→기흥7,686(-111)·연수7,875(+78) 수치·방향 일치. 7,600–7,900 확대축 명시. 서로 맞는 두 지역 사진. 자막 박스 안에 해당 표본 글자가 들어옴."},
      {"scene_id": "I002", "media": media[3], "observed": "전체8,388·8,329 차이59, 초혼7,634·6,746 차이888, 재혼733·1,563 차이830 일치. 독립 막대 길이가 동일0–8,000축에 비례. 누적합으로 전체를 만들지 않음."},
      {"scene_id": "S013", "media": media[4], "observed": "미추홀8,483·노원보다10쌍·+420·5.2% 일치. 문학경기장 외관/촬영2024 라벨과 실제 사진 비율 유지. 지도·출처·큰 수치·흰 자막 박스가 보임."}],
    "style_comparison": {"baseline": media[5], "palette": "크림 바탕·네이비 글자·파랑/황토 강조", "type": "굵은 제목·브랜드 행·일반 본문이 최신 기준과 같은 계열", "captions": "하단 고정 흰 박스·짙은 글자. 확인한 3표본 잘림 없음", "limit": "서체 파일/코드 검사만으로 픽셀 가독성을 대체하지 않음. 썸네일은 별도 승인 네이비 디자인."},
    "not_verified": ["실제 MP4 인코딩 결과", "모든 장면·전환 경계·최대 줌", "최악 길이 자막", "세로 앱 UI", "실제 음성 동기", "연속 재생", "실제 청취"],
    "notification": {"to": "editor/Ampere", "cc": "director", "direct_message_available": False, "message": "대표3종 직접 확인: 현 표본 필수 수정0. 전체 재작업 요청 없음. 이 결과는 HF 잠정 시안 한정. 실제 타이밍·MP4 후 영향 장면/경계 검수 필요."}}
save("representative_review.json", representatives)
coverage = {"phase": "thumbnail_inputs_representative3", "thumbnail_pngs_actually_viewed": 2,
    "hyperframes_snapshot_files_actually_viewed": 3, "baseline_contactsheet_files_viewed": 1,
    "sampled_encoded_mp4_frames_viewed": 0, "all_scenes_and_cuts": "unchecked",
    "maximum_zoom_frames": "unchecked", "vertical_app_ui": "unchecked", "continuous_playback": "unchecked",
    "actual_listening": "unchecked", "audio_stream_inspection": "unchecked", "audio_timing": "pending_narration_agent",
    "full_video_decode": "unchecked", "final_delivery_zip": "unchecked_not_supplied"}
save("coverage.json", coverage)
save("findings.json", {"task_id": "top20-production-independent-qa-v1", "revision": "top20-production-v1-phase1",
    "checked_at": NOW, "status": "partial_waiting_actual_timing_and_encoded_media", "critical_open": 0,
    "required_open": 1, "recommended_open": 0, "findings": [issue], "coverage": coverage,
    "final_approval": False, "per_media_hash_facts": "media_facts.json"})
handoff = {"task_id": "top20-production-independent-qa-v1", "role": "qa", "status": "phase1_complete_waiting_actual_media",
    "input_revisions": {"script_v3_sha256": sha(script_path), "photo_manifest_v2_sha256": followup["selected_photo_manifest_sha256"], "timing": "provisional_not_audio_aligned", "top20_sha256": sha(EP / "research/top20-8min-v2/top20.json")},
    "outputs": ["findings.json", "representative_review.json", "input_audit.json", "media_facts.json", "reuse_receipt.json", "coverage.json", "issue_QA-T20P-TH-SCOPE-01.json"],
    "affected_scene_ids": ["TH001", "I001", "I002", "S013"],
    "checks": [{"check": "실제 썸네일1280/320", "result": "required_scope_correction", "evidence": "media_facts.json"}, {"check": "대표3종 HF스냅샷", "result": "pass_with_pending_media_limits", "evidence": "representative_review.json"}, {"check": "대본·입력·불변검수 재사용", "result": "pass_scoped", "evidence": "input_audit.json;reuse_receipt.json"}, {"check": "MP4·실제청취·연속재생", "result": "unchecked", "evidence": None}],
    "critical_open": 0, "required_open": 1, "open_issue_ids": [issue["issue_id"]], "final_approval": False,
    "next_role": "director→visual(TH001 범위 표기), editor/Ampere(대표3종 결과 수신·실제MP4 전달)",
    "next_inputs": ["수정 썸네일1280/320의 새 해시", "실제 음성 타이밍·SRT", "본편+쇼츠2 실제 MP4·씬/컷 시간표·출처·인코딩 receipt", "전 장면 대표/전 컷 경계/최대줌/최악 자막/세로 앱 UI 증거"],
    "communications": "직접 peer 메시지 도구 없음. issue/representative_review 경로로 총괄·담당에게 전달. 외부 Claude 검수·Max/Opus 검수 수행 안 함."}
assert len(json.dumps(handoff,ensure_ascii=False)) <= 1600
save("handoff.json", handoff)
print(json.dumps({"phase1": "written", "critical_open": 0, "required_open": 1, "hash_checks": len(hash_checks), "all_hashes_match": True, "viewed": 6, "encoded_mp4_frames": 0, "handoff": str(OUT / "handoff.json")}, ensure_ascii=False))
