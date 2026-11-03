"""Verify exact deletion/protection results and write the retained audit report."""
from pathlib import Path
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import csv, hashlib, json, os

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
read = lambda p: json.loads(p.read_text(encoding="utf-8-sig"))
def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for x in iter(lambda:f.read(4*1024*1024), b""): h.update(x)
    return h.hexdigest()
def save(p, d): p.write_text(json.dumps(d, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")

result = read(OUT / "deletion_result.json")
manifest = read(OUT / "delete_manifest.json")
protected = read(OUT / "protected_hashes.json")["files"]
events = [json.loads(line) for line in (OUT / "deletion_events.jsonl").read_text(encoding="utf-8").splitlines()]
assert len(events) == manifest["delete_count"] == result["deleted_files"] + result["failed_or_skipped_files"]
assert sha(OUT / "delete_manifest.json") == result["manifest_sha256"]
deleted = [e for e in events if e["status"] == "deleted"]
still_present = [e["path"] for e in deleted if (ROOT/e["path"]).exists()]
assert not still_present, still_present

def check_protected(r):
    p = ROOT / r["path"]
    if not p.is_file(): return {"path": r["path"], "issue": "missing"}
    if p.stat().st_size != r["bytes"] or sha(p) != r["sha256"]:
        return {"path": r["path"], "issue": "content_changed"}
    return None
with ThreadPoolExecutor(max_workers=4) as pool:
    mismatches = [r for r in pool.map(check_protected, protected) if r]
assert not mismatches, mismatches
with (OUT/"file_decisions.csv").open(encoding="utf-8-sig", newline="") as f: decisions=list(csv.DictReader(f))
missing_kept = [r["path"] for r in decisions if r["action"] == "keep" and not (ROOT/r["path"]).is_file()]
assert not missing_kept, missing_kept

cfg = read(ROOT / "config/video_shelf.json")
aliases = []
digest_cache = {}
for entry in cfg["entries"]:
    for label, source in entry["files"].items():
        original = ROOT / source
        alias = ROOT / cfg["shelf"] / entry["name"] / label
        assert original.is_file() and alias.is_file(), (str(original), str(alias))
        key = str(original.resolve())
        if key not in digest_cache: digest_cache[key] = sha(original)
        assert sha(alias) == digest_cache[key], str(alias)
        aliases.append(str(alias.relative_to(ROOT)))
current = read(ROOT / "config/current_video.json")
assert sha(ROOT/current["video"]) == current["sha256"]
for short in current["shorts"]:
    assert sha(ROOT/short["video"]) == short["sha256"]

groups = defaultdict(lambda:{"deleted":[], "retained":[]})
image_exts = {".png", ".jpg", ".jpeg", ".webp"}
for e in deleted:
    if Path(e["path"]).suffix.lower() in image_exts:
        groups[str(Path(e["path"]).parent)]["deleted"].append(e["path"])
for r in decisions:
    parent = str(Path(r["path"]).parent)
    if parent in groups and r["action"] == "keep" and Path(r["path"]).suffix.lower() in image_exts:
        groups[parent]["retained"].append(r["path"])
save(OUT/"evidence_retention_index.json", dict(groups))
stamp = datetime.now(timezone.utc).isoformat()
verification = {"status":"verified", "verified_at":stamp, "deleted_files":len(deleted), "failed_files":result["failed_or_skipped_files"], "protected_hashes_checked":len(protected), "protected_hash_mismatches":mismatches, "kept_inventory_files_checked":sum(r["action"]=="keep" for r in decisions), "missing_kept_files":missing_kept, "managed_aliases_verified":len(aliases), "current_main_and_two_Shorts_sha_verified":True, "raw_evidence_retention_index":"evidence_retention_index.json", "remote_changes_performed":False, "scope":"Video production intermediates only"}
save(OUT/"post_cleanup_verification.json", verification)

by_ep = defaultdict(list)
for e in deleted:
    parts = Path(e["path"]).parts
    if parts[:2] == ("video-agent-studio", "episodes"):
        by_ep[parts[2]].append(e)
for episode, entries in by_ep.items():
    ep = ROOT / "video-agent-studio/episodes" / episode
    prefix = os.path.relpath(OUT, ep).replace("\\", "/")
    text = "# 2026-10-28 저장공간 후속 정리\n\n"
    text += f"사용자 정리 지시에 따라 이 편의 중간 파일 {len(entries):,}개, 논리 크기 {sum(e['bytes'] for e in entries)/2**30:.3f}GiB를 정리했습니다. 최종 게시본·현재 검토본·원천/재사용 자료·현재 재현 입력·코드·대본·승인/출처/검수 기록과 대표 진단 자료는 보존했습니다.\n\n"
    text += f"- [실제 삭제 경로·해시·결과]({prefix}/deletion_events.jsonl)\n- [남긴 대표 프레임과 정리한 증거 그룹]({prefix}/evidence_retention_index.json)\n- [전체 결과]({prefix}/정리결과.md)\n\n"
    text += "과거 검수 보고서는 당시 관측 기록입니다. 중복 프레임·파생 오디오·폐기된 렌더 일부를 정리했으므로 모든 과거 원시 증거가 현재도 존재하는 것은 아닙니다. 최종 파일·원본 입력·컨택트시트·대표 증거와 삭제 이력을 함께 확인하세요. 이번 파일 정리에서는 YouTube 상태를 변경하지 않았습니다.\n"
    (ep/"STORAGE_RETENTION_20261028.md").write_text(text, encoding="utf-8")

logical = result["deleted_logical_bytes"]/2**30
observed = result["volume_free_delta_bytes"]/2**30
reasons = Counter(e["reason"] for e in deleted)
report = f"""# 영상 작업 파일 정리 결과 — 2026-10-28

중간 파일 **{len(deleted):,}개**를 정리했습니다. 삭제한 논리 크기는 **{logical:.3f}GiB**, 실행 전후 드라이브 여유 공간의 관측 증가는 **{observed:.3f}GiB**입니다. 실패·건너뛰기는 **{result['failed_or_skipped_files']}개**입니다. 여유 공간 변화에는 하드링크와 같은 시간대의 시스템 쓰기가 반영될 수 있어 논리 크기와 구분합니다.

최종 게시 본편·수정 쇼츠, 다른 편의 현재 기준본과 사용자 진입점, 대본·자막·썸네일, 원음·정렬·재사용 자산·지도/논문 원자료·제작 소스·승인/출처/검수/게시 기록을 보존했습니다. 최신 본편이 참조하는 예전 MP4·패치·음성 입력과 설치된 전사 모델도 보존했습니다. 중요한 보존 파일 **{len(protected):,}개**의 SHA를 전후 대조했고, 사용자용 파일 링크 **{len(aliases)}개**의 존재와 내용이 원본과 일치함을 확인했습니다.

주요 정리 대상은 번호가 붙은 중복 검수 프레임, 폐기된 중간 MP4, 전사·디코드·신호 분석 WAV, 이전 쇼츠 합성 오디오, 재생성 가능한 자체 코드의 바이트코드입니다. 이름이 있는 진단 도표와 전후 비교·컨택트시트·그룹별 대표 프레임을 남겼습니다. 파일별 목록과 SHA가 일치한 파일만 PowerShell 기본 파일 명령으로 삭제했으며 재귀 삭제·보안 설정 변경은 하지 않았습니다.

실거래·예측 데이터, 다른 업무 자료, 원본 대화와 자격증명은 정리 범위에서 제외했습니다. YouTube 게시 상태는 변경하지 않았습니다. 보존·삭제 판단은 부모 에이전트가 검토했으며 별도 독립 에이전트 승인으로 표시하지 않았습니다.

- [보존 기준](retention_policy.md)
- [전체 파일별 보존·삭제 목록](file_decisions.csv)
- [삭제 매니페스트](delete_manifest.json)
- [실제 성공·실패 이력](deletion_events.jsonl)
- [삭제 결과와 여유 공간 관측](deletion_result.json)
- [보존 파일·사용자 링크 검증](post_cleanup_verification.json)
- [대표 증거 보존 색인](evidence_retention_index.json)
"""
(OUT/"정리결과.md").write_text(report, encoding="utf-8")
result.update(status="verified_completed", verified_at=stamp, post_verification="post_cleanup_verification.json", report="정리결과.md")
save(OUT/"deletion_result.json", result)
print(json.dumps({"status":"verified_completed", "deleted_files":len(deleted), "logical_GiB":round(logical,3), "observed_free_GiB":round(observed,3), "failed":result["failed_or_skipped_files"], "protected_hashes":len(protected), "managed_links_verified":len(aliases), "report":str((OUT/"정리결과.md").relative_to(ROOT))}, ensure_ascii=False))
