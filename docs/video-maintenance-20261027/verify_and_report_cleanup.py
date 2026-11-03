"""Verify actual removal and retained content, then write a human report."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from collections import Counter, defaultdict
from datetime import datetime, timezone
import csv
import hashlib
import json
import os

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
INTENTIONAL_DOCUMENT_EDITS = {
    "video-agent-studio/WORKFLOW.md",
    "video-agent-studio/guides/제작_기본가이드.md",
    "video-agent-studio/guides/자료화면_설계_원칙.md",
    "video-agent-studio/guides/영상제작_마스터가이드.md",
    "video-agent-studio/guides/영상제작_요청추적표.md",
    "video-agent-studio/templates/episode_preflight.json",
    "영상/README.md",
}


def read(name):
    return json.loads((OUT / name).read_text(encoding="utf-8-sig"))


def digest(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for part in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def main():
    result = read("deletion_result.json")
    protected = read("protected_hashes.json")["files"]
    decisions = list(csv.DictReader((OUT / "file_decisions.csv").open(encoding="utf-8-sig", newline="")))
    events = [json.loads(line) for line in (OUT / "deletion_events.jsonl").read_text(encoding="utf-8").splitlines() if line]
    removed = [e for e in events if e["status"] == "deleted"]
    assert len(removed) == result["deleted_files"]
    still_present = [e["path"] for e in removed if (ROOT / e["path"]).exists()]
    kept_missing, kept_size_changed, intentional_document_changes = [], [], []
    for row in decisions:
        if row["action"] != "keep":
            continue
        p = ROOT / row["path"]
        if not p.is_file():
            kept_missing.append(row["path"])
        elif p.stat().st_size != int(row["bytes"]):
            if row["path"] in INTENTIONAL_DOCUMENT_EDITS:
                intentional_document_changes.append({"path": row["path"], "before_bytes": int(row["bytes"]), "after_bytes": p.stat().st_size, "after_sha256": digest(p), "reason": "Authorized master-guide integration; document preserved and intentionally updated."})
            else:
                kept_size_changed.append(row["path"])

    def check(row):
        p = ROOT / row["path"]
        return row["path"], p.is_file() and digest(p) == row["sha256"]
    with ThreadPoolExecutor(max_workers=4) as pool:
        changed = [s for s, ok in pool.map(check, protected) if not ok]
    shelf = json.loads((ROOT / "config/video_shelf.json").read_text(encoding="utf-8"))
    shelf_missing = []
    shelf_mismatch = []
    shelf_files = 0
    for entry in shelf["entries"]:
        for name, source in entry["files"].items():
            original, alias = ROOT / source, ROOT / shelf["shelf"] / entry["name"] / name
            shelf_files += 1
            if not original.is_file() or not alias.is_file():
                shelf_missing.append({"source": source, "alias": str(alias.relative_to(ROOT))})
            elif original.stat().st_size != alias.stat().st_size:
                shelf_mismatch.append({"source": source, "alias": str(alias.relative_to(ROOT))})
        assert (ROOT / shelf["shelf"] / entry["name"] / "작업폴더").exists()
    assert not still_present, still_present
    assert not kept_missing, kept_missing
    assert not kept_size_changed, kept_size_changed
    assert not changed, changed
    assert not shelf_missing and not shelf_mismatch, (shelf_missing, shelf_mismatch)
    removed_by_reason, bytes_by_reason = Counter(), Counter()
    removed_by_episode = defaultdict(list)
    image_groups = defaultdict(list)
    for e in removed:
        removed_by_reason[e["reason"]] += 1
        bytes_by_reason[e["reason"]] += e["bytes"]
        parts = e["path"].split("/")
        if parts[:2] == ["video-agent-studio", "episodes"]:
            removed_by_episode[parts[2]].append(e)
        if Path(e["path"]).suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
            image_groups[str(Path(e["path"]).parent)].append(e)
    kept_images = defaultdict(list)
    for r in decisions:
        if r["action"] == "keep" and Path(r["path"]).suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
            kept_images[str(Path(r["path"]).parent)].append(r["path"])
    index = {"scope": "Historical raw extraction frames selectively removed; original review reports remain historical observations. No claim that deleted raw frames still exist or can be reconstructed from a different revision.", "file_level_deleted_hashes": "delete_manifest.json and deletion_events.jsonl", "groups": [{"directory": name, "deleted_count": len(rows), "retained_images_in_same_directory": kept_images[name]} for name, rows in sorted(image_groups.items())]}
    (OUT / "evidence_retention_index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    for episode, rows in removed_by_episode.items():
        notice = ROOT / "video-agent-studio/episodes" / episode / "STORAGE_RETENTION_20261027.md"
        body = f"""# 2026-10-27 저장공간 정리 기록

사용자 명시 요청에 따라 이 편의 확인된 중간 산출물 {len(rows):,}개, 논리 크기 {sum(r['bytes'] for r in rows) / 2**30:.3f}GiB를 정리했습니다. 최종/현재 기준 영상, 원천과 재사용 자산, 현재 재현에 필요한 입력, 승인·출처·검수 기록 및 대표 증거는 보존했습니다.

- [파일별 보존/삭제 목록](../../../docs/video-maintenance-20261027/file_decisions.csv)
- [실제 삭제 경로·해시·성공/실패](../../../docs/video-maintenance-20261027/deletion_events.jsonl)
- [남긴 대표 이미지와 삭제한 원시 증거 그룹](../../../docs/video-maintenance-20261027/evidence_retention_index.json)
- [전체 결과와 보존 검증](../../../docs/video-maintenance-20261027/정리결과.md)

과거 검수 보고서는 당시 관측의 기록입니다. 일부 중복 원시 프레임·중간 MP4·합성 중간 오디오는 현재 보존하지 않습니다. 남은 대표 이미지·컨택트시트·원본 소스·해시와 위 삭제 목록을 함께 참고합니다. 삭제한 과거 폐기본의 모든 프레임을 최신 최종본에서 그대로 재현할 수 있다고 보장하지 않습니다. 원격 유튜브 파일·공개 상태는 이번 정리에서 변경하지 않았습니다.
"""
        notice.write_text(body, encoding="utf-8")
    free_delta = result["volume_free_after_bytes"] - result["volume_free_before_bytes"]
    verification = {"status": "verified", "verified_at_utc": datetime.now(timezone.utc).isoformat(), "deleted_files_absent": len(removed), "retained_file_inventory_presence_and_size": "pass_except_explicit_intentional_document_updates_below", "intentional_document_updates": intentional_document_changes, "protected_SHA256_files_checked": len(protected), "protected_SHA256_changed": changed, "managed_shelf_entries": len(shelf["entries"]), "managed_shelf_files_checked": shelf_files, "managed_shelf_missing": shelf_missing, "managed_shelf_size_mismatch": shelf_mismatch, "failures_or_skips": result["failures"], "logical_deleted_bytes": result["deleted_logical_bytes"], "volume_free_delta_bytes": free_delta, "remote_uploads_changed": False, "raw_collection_data_auth_and_conversations_deleted": False, "new_guides": ["video-agent-studio/guides/영상제작_마스터가이드.md", "video-agent-studio/guides/영상제작_요청추적표.md"]}
    (OUT / "post_cleanup_verification.json").write_text(json.dumps(verification, ensure_ascii=False, indent=2), encoding="utf-8")
    labels = {"regenerable_webpack_build_cache": "재생성 가능한 빌드 캐시", "obsolete_unregistered_video_render_current_and_uploaded_kept": "등록된 최종·현재 기준본을 제외한 중간 MP4", "redundant_encoded_or_render_frame_evidence": "대표 증거를 남긴 중복 점검 프레임", "derived_mix_or_signal_analysis_audio_original_voice_kept": "원본 음성을 남긴 합성·신호 분석 중간 오디오", "superseded_unreferenced_render_cache": "현재 입력에 쓰지 않는 예전 렌더 캐시", "regenerable_legacy_bundle_javascript_source_map": "예전 렌더 번들의 생성 JS source map", "verified_duplicate_legacy_render_bundle_asset": "원천과 동일 SHA를 확인한 예전 번들 중복 자산"}
    lines = ["# 영상 작업 용량 정리 결과 — 2026-10-27", "", f"파일 **{len(removed):,}개**, 논리 크기 **{result['deleted_logical_bytes'] / 2**30:.3f}GiB**를 삭제했습니다. 실행 실패/건너뜀은 **{result['failed_or_skipped_files']}건**입니다.", "", f"드라이브 여유 공간은 실행 전후 관측상 **{free_delta / 2**30:.3f}GiB** 늘었습니다. 하드링크의 파일 크기를 물리 해제량으로 중복 계산하지 않았으며, 드라이브 관측 차이에는 같은 시간의 시스템 쓰기가 포함될 수 있습니다.", "", "| 정리 항목 | 파일 수 | 논리 크기 |", "|---|---:|---:|"]
    for reason, count in removed_by_reason.items():
        lines.append(f"| {labels.get(reason, reason)} | {count:,} | {bytes_by_reason[reason] / 2**30:.3f}GiB |")
    lines += ["", "## 남긴 자료와 확인", "", f"중요 보존 파일 **{len(protected):,}개 SHA-256**이 실행 전과 일치했습니다. 조사 목록의 보존 대상은 모두 남아 있습니다. 공통 가이드·진입 문서의 의도된 업데이트는 별도 기록했고, 나머지 보존 파일의 크기는 유지됐습니다. 사용자 진입점 **{shelf_files}개**의 원본·별칭과 작업폴더 연결을 확인했습니다.", "", "최종 게시본·현재 검토 기준본·자막·썸네일, 원천 실거래/분석/논문/지도/도면, 사용자 DOCX·직접 녹음 가이드, 승인 음성·정렬·전사 모델, 현재 재현 소스·실제 입력, 재사용 이미지·브랜드·음악·폰트, 승인·출처·권리·검수 기록을 보존했습니다. 이름이 cache여도 최신 프로젝트의 실제 입력은 남겼습니다.", "", "일부 과거 원시 점검 프레임과 중간 출력은 정리했습니다. 과거 검수 보고서는 당시 범위의 기록이며 현재 모든 원시 프레임의 존재나 재청취·연속 재생 완료를 의미하지 않습니다. episode별 STORAGE_RETENTION_20261027.md와 아래 증거 인덱스에 연결했습니다.", "", "원격 유튜브 영상·공개 상태, 실거래 수집 원본, 계정·키, 원본 대화와 다른 업무 자료는 삭제하지 않았습니다.", "", "## 새 제작 기준", "", "- [영상 제작 마스터 가이드](../../video-agent-studio/guides/영상제작_마스터가이드.md)", "- [전체 요청 추적표](../../video-agent-studio/guides/영상제작_요청추적표.md)", "", "마스터 가이드를 AGENTS·WORKFLOW·기본가이드·episode preflight에 연결했습니다. 현재 대화45개 묶음과 로컬 기록108개를 공통/편별/대체/보류로 구분했습니다.", "", "## 실제 기록", "", "- [파일별 보존/삭제 결정](file_decisions.csv)", "- [확정 삭제 목록과 해시](delete_manifest.json)", "- [파일별 실제 삭제 이벤트](deletion_events.jsonl)", "- [삭제 결과·실패 목록](deletion_result.json)", "- [보존 파일 실행 후 검증](post_cleanup_verification.json)", "- [남긴 대표 증거 인덱스](evidence_retention_index.json)", "- [삭제 전 독립 보존 검토](retention_review.json)"]
    report = OUT / "정리결과.md"
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    # Keep original-relative Markdown links functional by making short navigation
    # files, rather than hardlinking Markdown into a different relative directory.
    for title, source, target in [("영상 제작 마스터 가이드", ROOT / "video-agent-studio/guides/영상제작_마스터가이드.md", ROOT / "영상/영상제작_마스터가이드.md"), ("영상 제작 요청 추적표", ROOT / "video-agent-studio/guides/영상제작_요청추적표.md", ROOT / "영상/영상제작_요청추적표.md"), ("2026-10-27 영상 작업 용량 정리 결과", report, ROOT / "영상/용량정리_20261027.md")]:
        relative = "../" + source.relative_to(ROOT).as_posix()
        shortcut = f"# {title}\n\n[전체 문서 열기]({relative})\n\n제작 원본과 근거 링크는 위 문서에서 확인합니다.\n"
        if target.exists():
            assert target.read_text(encoding="utf-8") == shortcut, f"Do not overwrite an edited user file: {target}"
        else:
            target.write_text(shortcut, encoding="utf-8")
    print(json.dumps({"status": "verified", "deleted_files": len(removed), "logical_GiB": round(result["deleted_logical_bytes"] / 2**30, 3), "observed_free_delta_GiB": round(free_delta / 2**30, 3), "protected_SHA256_matches": len(protected), "managed_shelf_files": shelf_files, "failures": result["failed_or_skipped_files"], "report": str(report.relative_to(ROOT))}, ensure_ascii=False))


if __name__ == "__main__":
    main()
