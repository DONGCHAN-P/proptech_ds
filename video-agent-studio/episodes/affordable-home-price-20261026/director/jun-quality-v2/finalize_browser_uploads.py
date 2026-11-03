"""Record the three uploads verified through the visible YouTube Studio UI."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json

EP = Path(__file__).resolve().parents[2]
ROOT = EP.parents[2]
DIR = Path(__file__).parent
REL = EP / "outputs/jun-quality-v2/release"
BATCH = REL / "private-upload-20261028"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


expected_ids = {
    "main": "0495J7FMmCk",
    "promo": "PwqvBlxAoII",
    "summary": "Y9lZk9PmNUA",
}
stamp = datetime.now(timezone.utc).isoformat()
records = []
for name, video_id in expected_ids.items():
    folder = BATCH / name
    job = read(folder / "upload_job.json")
    receipt = read(folder / "upload_receipt.json")
    assert receipt["video_id"] == video_id
    assert receipt["sha256"] == job["sha256"] == sha(ROOT / job["video"])
    assert receipt["job_sha256"] == sha(folder / "upload_job.json")
    assert job["channel_id"] == "UCr_mTC0x_Uobv6MrIsOkrXw"
    assert job["privacy"] == "private"
    assert job["subtitles_sha256"] == sha(ROOT / job["subtitles"])
    evidence = {
        "method": "Chrome extension / visible YouTube Studio UI",
        "channel_id": job["channel_id"],
        "channel_name_observed": "데이터로보는부동산",
        "title": job["title"],
        "privacy": "private",
        "privacy_evidence": "Exact-title content row and video details show 비공개",
        "processing": "HD complete",
        "processing_evidence": "Video details show 표준 화질 완료 and 고화질 완료",
        "copyright_check": "No issues found",
        "copyright_evidence": "Upload wizard: 저작권 검사 완료 발견된 문제 없음",
        "caption": "Korean SRT uploaded and saved",
        "caption_evidence": "Imported time-coded text, 완료 saved, 한국어 source and 자막 수정 visible on language page",
        "caption_player_serving_tested": False,
        "synthetic_media_disclosed": True,
        "made_for_kids": False,
        "notify_subscribers": False,
        "verified_at": stamp,
    }
    if name == "main":
        thumb = EP / "outputs/jun-quality-v2/thumbnail/thumbnail.png"
        assert sha(thumb) == "063662bc485f991db84d15924ade7b1f37646919174f68a52904a1a4125a7a1f"
        evidence.update(thumbnail_uploaded=True, thumbnail_evidence="업로드된 썸네일 and visible wooden-house artwork with 내 돈으로 얼마짜리 집?")
    receipt.update(
        phase="private_uploaded_verified",
        private_verified=True,
        processing_verified=True,
        caption_uploaded=True,
        caption_saved_verified=True,
        caption_language_verified="ko",
        caption_player_serving_verified=False,
        browser_verification=evidence,
        verified_at=stamp,
    )
    if name == "main":
        receipt["thumbnail_uploaded"] = True
    save(folder / "upload_receipt.json", receipt)
    records.append({
        "id": name, "video_id": video_id, "url": receipt["url"],
        "sha256": receipt["sha256"], "title": job["title"],
        "privacy": "private", "processing": "HD complete",
        "caption": "Korean SRT saved", "verification_method": evidence["method"],
    })

assert len({item["video_id"] for item in records}) == 3
report = {
    "status": "private_uploaded_verified", "updated_at": stamp,
    "items": records, "uploads_performed": 3,
    "public_release": False, "existing_videos_deleted": False,
    "claude_final_review_pass": False,
    "actual_listening": False, "continuous_playback": False,
    "additional_paid_generation_calls": 0, "additional_cash_krw": 0,
    "source_authorization": "director/jun-quality-v2/current_upload_authorization.json",
    "verification_method": "Visible YouTube Studio UI; no API success claimed",
    "shorts_related_video": "Pending public or unlisted main video; private visibility preserved",
}
save(BATCH / "completion.json", report)

status = "# 비공개 업로드 완료\n\n" + "\n".join(
    "- " + item["title"] + " — " + item["url"] for item in records
) + "\n\n2026년 10월 28일, 로그인된 데이터로보는부동산 채널의 YouTube Studio에서 세 편의 비공개 상태와 고화질 처리 완료를 확인했습니다. 본편 썸네일을 적용하고 세 편의 한국어 SRT를 저장했습니다. 업로드 단계의 저작권 검사에서 발견된 문제는 없습니다.\n\n검수 범위: 실제 업로드 화면·콘텐츠 목록·동영상 세부정보·언어 페이지 확인. 플레이어의 선택 자막 제공, 연속 재생, 실제 청취는 이번 업로드 확인에 포함하지 않았습니다. Claude 최종 검수는 미확인으로 유지하며, 최신 사용자의 직접 업로드 지시에 따라 진행했습니다.\n\n쇼츠의 관련 동영상 연결은 본편 공개 범위 변경 후 설정할 수 있습니다. 현재 세 편 모두 비공개입니다. 기존 비공개 영상은 보존했습니다. API 인증 오류는 해결되었다고 기록하지 않으며 이번 업로드는 Chrome 웹에서 진행했습니다.\n"
(REL / "upload_status.md").write_text(status, encoding="utf-8")

manifest = read(REL / "upload_manifest.json")
manifest.update(status=report["status"], uploads_performed=3, uploaded_items=records, updated_at=stamp, verification_method=report["verification_method"])
save(REL / "upload_manifest.json", manifest)
external = read(DIR / "external_status.json")
external["youtube"].update(
    browser_fallback="completed_visible_UI_verified", uploads_performed=3,
    new_video_ids=[item["video_id"] for item in records], verified_items=records,
    verified_at=stamp, upload_blocked=False,
    current_direct_user_authorization=report["source_authorization"],
    next_step="사용자가 요청하면 공개 범위와 쇼츠 관련 동영상 연결 결정",
)
save(DIR / "external_status.json", external)

state = read(EP / "state.json")
state.update(stage=report["status"], new_upload_performed=True,
             private_upload_url=records[0]["url"], private_uploads=records,
             private_upload_authorized=True, public_release_authorized=False,
             updated_at=stamp)
state["blocked_tasks"] = [{"task": "Claude final review", "reason": "Final review remains unconfirmed; latest direct user instruction authorized these private uploads"}]
state["active_work"].update(stage=report["status"], new_upload_performed=True,
                            private_upload_url=records[0]["url"], private_uploads=records)
save(EP / "state.json", state)
local_report = EP / "outputs/jun-quality-v2/main/completion.json"
local = read(local_report)
local.update(status=report["status"], new_upload_performed=True, private_uploads=records, upload_verified_at=stamp)
save(local_report, local)

review_path = EP / "outputs/jun-quality-v2/main/검토안내.md"
review = review_path.read_text(encoding="utf-8")
marker = "\n\n## 2026-10-28 비공개 업로드 확인"
if marker in review:
    review = review.split(marker)[0]
review_path.write_text(review + marker + "\n\n" + status.split("\n\n", 1)[1], encoding="utf-8")

shelf_path = ROOT / "config/video_shelf.json"
shelf = read(shelf_path)
entry = next(item for item in shelf["entries"] if item["workspace"].endswith("affordable-home-price-20261026"))
entry.update(status="Jun 화면 개선 본편·쇼츠 2편 비공개 업로드 / 고화질 처리·한국어 자막·본편 썸네일 확인 / Claude 최종 검수 미확인",
             youtube_url=records[0]["url"], youtube_visibility="private",
             shorts_youtube_urls=[item["url"] for item in records[1:]])
save(shelf_path, shelf)
print(json.dumps(report, ensure_ascii=False))
