"""Build a file-level, dependency-aware video-only cleanup plan; do not delete."""
from pathlib import Path
from collections import defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor
import csv
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
ROWS = json.loads((OUT / "inventory.json").read_text(encoding="utf-8"))["files"]
BY_PATH = {r["path"]: r for r in ROWS}
PROTECTED = defaultdict(set)
TEXT_EXT = {".json", ".html", ".htm", ".py", ".js", ".ts", ".tsx", ".jsx", ".css", ".md", ".txt", ".srt", ".vtt", ".toml", ".yml", ".yaml", ".csv", ".xml", ".pdf"}
MEDIA_EXT = {".png", ".jpg", ".jpeg", ".webp", ".mp4", ".mov", ".wav", ".mp3", ".m4a", ".aac", ".woff2", ".ttf", ".json", ".html", ".svg"}
PRIVATE_WORDS = re.compile(r"(^|[/_.-])(token|oauth|credentials?|secrets?|cookies?|sessions?|login)([/_.-]|$)", re.I)
SOURCE_COMPONENTS = {"research", "raw", "sources", "source_assets", "source-assets", "source-archive", "source_archive", "source_frames", "source-frames", "real-assets", "audio-source", "assets", "images", "fonts", "models", "model-cache", "narration", "writer", "visual"}
FRAME_COMPONENTS = {"frames", "encoded", "encoded_evidence", "encoded-frames", "actual_frames", "checks", "evidence", "screenshots", "cut_frames", "frame_samples", "states"}
KEEP_IMAGE_NAME = re.compile(r"before|after|contact|sheet|comparison|critical|long.caption|progression|chapter.cards|cut.entries|overview|collage|preview|poster|thumbnail|미리보기|비교", re.I)


def frame_output(path):
    components = path.lower().split("/")[:-1]
    return any(p in FRAME_COMPONENTS or re.search(r"(^|[-_])(frames?|evidence|proofs?)([-_]|$)", p) for p in components)


def legacy_bundle(path):
    return path.startswith("video-agent-studio/episodes/") and any(p == "bundle" or p.endswith("-bundle") for p in path.lower().split("/"))

# These are the retained current/local or published production packages. Entire
# source packages below remain intact; superseded caches are not current inputs.
ACTIVE_PREFIXES = [
    "video-agent-studio/episodes/affordable-home-price-20261026/director/user-recording-v1/",
    "video-agent-studio/episodes/affordable-home-price-20261026/outputs/rebuild-v2/actual-scenes-r2-parent-v3/",
    "video-agent-studio/episodes/affordable-home-price-20261026/director/rebuild-v2/media-input-v1/",
    "video-agent-studio/episodes/housing-choice-networth-20261020/director/launch-and-jun-v1/claude_media_input_v1/",
    "video-agent-studio/episodes/housing-choice-networth-20261020/director/launch-and-jun-v1/shorts_media_input_v2/",
    "video-agent-studio/episodes/regional-price-recovery-20261022/outputs/guide-v3/project/",
]
CURRENT_PACKAGES = [
    "video-agent-studio/episodes/goyang-changneung-20261015/outputs/production-v8-jun",
    "video-agent-studio/episodes/hanam-gyosan-20261019/outputs/production-v5-jun",
    "video-agent-studio/episodes/namyangju-wangsuk-20261014/outputs/readability-cta-v15",
    "video-agent-studio/episodes/housing-choice-networth-20261020/outputs/jun-production-v1",
    "video-agent-studio/episodes/housing-choice-networth-20261020/outputs/shorts-jun-v2",
    "video-agent-studio/episodes/affordable-home-price-20261026/outputs/rebuild-v2/full-film-r2-v1",
    "video-agent-studio/episodes/capital-10eok-map-20261017/outputs/monthly-5eok-permanent-v2",
    "video-agent-studio/episodes/data-insight-20261019/outputs/v2",
    "video-agent-studio/episodes/regional-price-recovery-20261022/outputs/guide-v3",
]


def protect(path, reason):
    try:
        rel = Path(path).resolve().relative_to(ROOT).as_posix()
    except (ValueError, OSError):
        return
    if rel in BY_PATH:
        PROTECTED[rel].add(reason)


def strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for value in obj.values():
            yield from strings(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from strings(value)


def paths_in(value, context):
    """Resolve actual local media/path strings, never shell-evaluate the input."""
    value = value.strip().replace("\\", "/")
    while "//" in value and not value.startswith(("http:", "https:")):
        value = value.replace("//", "/")
    if value.startswith(("http:", "https:", "data:", "app:", "plugin:")) or len(value) > 2000:
        return []
    value = value.split("?", 1)[0]
    if Path(value).suffix.lower() not in MEDIA_EXT | {".srt", ".vtt", ".txt", ".md", ".pdf", ".csv", ".zip"}:
        return []
    candidates = [Path(value)] if re.match(r"^[a-zA-Z]:/", value) else [context.parent / value, ROOT / value.lstrip("/"), ROOT / "video/public" / value.lstrip("/")]
    parts = context.parts
    if "episodes" in parts:
        i = parts.index("episodes")
        if len(parts) > i + 1:
            candidates.append(Path(*parts[:i + 2]) / value)
    result = []
    for q in candidates:
        try:
            r = q.resolve().relative_to(ROOT).as_posix()
            if r in BY_PATH:
                result.append(r)
        except (ValueError, OSError):
            pass
    return list(set(result))


def protect_document_refs(p, reason):
    try:
        text = p.read_text(encoding="utf-8")
        if p.suffix == ".json":
            values = strings(json.loads(text))
        else:
            values = (m.group(1) for m in re.finditer(r'''["']([^"'\n]{1,2000})["']''', text))
        for value in values:
            for rel in paths_in(value, p):
                PROTECTED[rel].add(reason)
    except (OSError, UnicodeError, json.JSONDecodeError):
        pass


def sha_file(p):
    h = hashlib.sha256()
    with p.open("rb") as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    # Every managed alias and its exact original remain valid, including historical
    # reference examples explicitly linked for the user. Never traverse junctions.
    shelf = json.loads((ROOT / "config/video_shelf.json").read_text(encoding="utf-8"))
    for entry in shelf["entries"]:
        for name, target in entry["files"].items():
            protect(ROOT / target, "managed_shelf_source")
            protect(ROOT / shelf["shelf"] / entry["name"] / name, "managed_shelf_alias")
    for p in [ROOT / "config/current_video.json", ROOT / "config/video_style.json"]:
        protect_document_refs(p, "current_config_reference")
    for p in (ROOT / "video-agent-studio/episodes").glob("*/state.json"):
        protect_document_refs(p, "episode_state_reference")
    # Keep every existing actual upload/release artifact, without changing remote
    # publication state. Small approval/receipt files are kept regardless.
    for row in ROWS:
        p = ROOT / row["path"]
        s = row["path"].lower()
        if row["ext"] == ".json" and "node_modules" not in s and not PRIVATE_WORDS.search(s) and row["bytes"] < 3_000_000 and any(w in p.name.lower() for w in ("upload", "release", "publication")):
            protect_document_refs(p, "upload_release_record_reference")
    # Current render project media (not QA frame manifests) can refer to an older
    # cache. Protect that exact input even when its directory is called cache.
    documents = set()
    for prefix in CURRENT_PACKAGES:
        for row in ROWS:
            s = row["path"]
            if not s.startswith(prefix + "/"):
                continue
            name = Path(s).name.lower()
            if row["ext"] == ".json" and any(k in name for k in ("project", "source_manifest", "media_assets", "source_assets", "timeline", "delivery_manifest")) and not any(k in name for k in ("frame_manifest", "evidence_manifest", "layout_guard")):
                documents.add(s)
    for row in ROWS:
        s = row["path"]
        if s.startswith("video/src/") and row["ext"] in {".ts", ".tsx", ".js", ".jsx", ".json"}:
            documents.add(s)
        elif s.startswith("video-agent-studio/") and "/outputs/" in s and row["ext"] == ".html" and not PRIVATE_WORDS.search(s):
            # HTML itself is kept; concrete image/audio inputs must also survive.
            documents.add(s)
    for name in sorted(documents):
        protect_document_refs(ROOT / name, "renderable_source_dependency")
    for row in ROWS:
        s = row["path"]
        if any(s.startswith(prefix) for prefix in ACTIVE_PREFIXES):
            PROTECTED[s].add("current_source_or_review_package")
        if s.startswith("video-agent-studio/") and row["ext"] in {".mp4", ".wav", ".mp3", ".m4a"} and re.search(r"brand|intro_clean|outro_clean|opening_clean|ending_clean|reusable", Path(s).name, re.I):
            PROTECTED[s].add("reusable_brand_asset")
        if s.endswith("/voice_preserved.wav") and "/full-film-r2-v1/" in s:
            PROTECTED[s].add("current_editable_narration_master")

    # Preserve representative diagnostic evidence while pruning redundant raw
    # frame sequences. Contact sheets, critical/before-after views stay intact.
    frame_groups = defaultdict(list)
    for r in ROWS:
        s, ext = r["path"], r["ext"]
        parts = set(s.lower().split("/"))
        if s.startswith("video-agent-studio/episodes/") and ext in {".png", ".jpg", ".jpeg", ".webp"} and frame_output(s) and not parts & SOURCE_COMPONENTS:
            if KEEP_IMAGE_NAME.search(Path(s).name):
                PROTECTED[s].add("diagnostic_or_contact_sheet")
            frame_groups[str(Path(s).parent)].append(s)
    for parent, names in frame_groups.items():
        ordered = sorted(names)
        for i in {0, len(ordered) // 2, len(ordered) - 1}:
            PROTECTED[ordered[i]].add("representative_frame_first_middle_last")

    decisions, deletes = [], []
    for row in ROWS:
        s, ext = row["path"], row["ext"]
        parts = set(s.lower().split("/"))
        reason, action = "unclassified_preserved", "keep"
        is_episode = s.startswith("video-agent-studio/episodes/")
        source = bool(parts & SOURCE_COMPONENTS)
        if s in PROTECTED:
            reason = ";".join(sorted(PROTECTED[s]))
        elif s.startswith("영상/"):
            reason = "user_entrypoint_or_unmanaged_user_file"
        elif PRIVATE_WORDS.search(s) or Path(s).name.startswith(".env"):
            reason = "private_auth_or_account_file_not_in_scope"
        elif s.startswith(("exports/", "output/", "assets/", "video/public/", "video/src/", "tts_benchmark/")):
            reason = "source_research_history_shared_asset_or_other_work"
        elif s.startswith((".cache/webpack/", "video/node_modules/.cache/")):
            action, reason = "delete", "regenerable_webpack_build_cache"
        elif "node_modules" in parts:
            reason = "installed_runtime_dependency"
        elif source:
            reason = "source_research_voice_visual_font_model_or_archive"
        elif ext in TEXT_EXT or ext in {".svg", ".zip", ".gz", ".exe", ".dll", ".bin", ".fst", ".ark"}:
            reason = "code_data_approval_provenance_report_or_dependency"
        elif is_episode and "cache" in parts and ext in {".png", ".jpg", ".jpeg", ".webp", ".mp4", ".wav", ".m4a", ".aac", ".f32", ".pcm", ".raw"}:
            action, reason = "delete", "superseded_unreferenced_render_cache"
        elif is_episode and ext in {".png", ".jpg", ".jpeg", ".webp"} and frame_output(s):
            action, reason = "delete", "redundant_encoded_or_render_frame_evidence"
        elif legacy_bundle(s) and ext == ".map":
            action, reason = "delete", "regenerable_legacy_bundle_javascript_source_map"
        elif is_episode and ext in {".wav", ".m4a", ".f32", ".pcm", ".raw"} and re.search(r"full_mix|premix|voice_preserved_draft|decoded|analysis_16k|mixed_audio", Path(s).name, re.I):
            action, reason = "delete", "derived_mix_or_signal_analysis_audio_original_voice_kept"
        elif is_episode and ext == ".mp4" and ("outputs" in parts or "editor" in parts):
            action, reason = "delete", "obsolete_unregistered_video_render_current_and_uploaded_kept"
        record = {**row, "action": action, "reason": reason}
        decisions.append(record)
        if action == "delete":
            deletes.append(record)
    # Remove redundant copies inside obsolete renderer bundles only after finding
    # an identical stable source outside the bundle. Never deduplicate editable
    # code, current source packages, original voices, or archived source snapshots.
    duplicate_exts = {".png", ".jpg", ".jpeg", ".webp", ".woff2", ".ttf"}
    canonical_by_size = defaultdict(list)
    for row in decisions:
        s = row["path"]
        if row["action"] == "keep" and row["ext"] in duplicate_exts and (s.startswith(("video/public/", "assets/", "video-agent-studio/assets/")) or "/research/" in s or "/visual/" in s) and not legacy_bundle(s):
            canonical_by_size[row["bytes"]].append(s)
    digest_cache = {}
    def cached_sha(rel):
        if rel not in digest_cache:
            digest_cache[rel] = sha_file(ROOT / rel)
        return digest_cache[rel]
    for row in decisions:
        s = row["path"]
        if row["action"] != "keep" or s in PROTECTED or row["ext"] not in duplicate_exts or not legacy_bundle(s):
            continue
        choices = canonical_by_size.get(row["bytes"], [])
        if not choices:
            continue
        value = cached_sha(s)
        for target in choices:
            if cached_sha(target) == value:
                row.update({"action": "delete", "reason": "verified_duplicate_legacy_render_bundle_asset", "retained_duplicate": target, "sha256": value})
                PROTECTED[target].add("retained_identical_asset_for_removed_legacy_bundle_copy")
                deletes.append(row)
                break
    # Bind every delete to its actual content. A later mutation causes a skip.
    previous_hashes = {}
    for previous_name in ("delete_manifest.json", "protected_hashes.json"):
        previous_path = OUT / previous_name
        if previous_path.exists():
            for old in json.loads(previous_path.read_text(encoding="utf-8")).get("files", []):
                previous_hashes[old["path"]] = old
    def add_digest(row):
        p = ROOT / row["path"]
        before = p.stat()
        assert before.st_size == row["bytes"] and before.st_mtime_ns == row["mtime_ns"], row["path"]
        old = previous_hashes.get(row["path"])
        value = old["sha256"] if old and old["bytes"] == row["bytes"] and old["mtime_ns"] == row["mtime_ns"] else sha_file(p)
        after = p.stat()
        assert before.st_size == after.st_size and before.st_mtime_ns == after.st_mtime_ns, row["path"]
        row["sha256"] = value
        return row
    with ThreadPoolExecutor(max_workers=4) as pool:
        deletes = list(pool.map(add_digest, deletes))
    for row in deletes:
        assert not set(row["path"].lower().split("/")) & SOURCE_COMPONENTS or row.get("retained_duplicate")
        assert row["path"] not in PROTECTED
        assert row["path"].startswith(("video-agent-studio/episodes/", ".cache/webpack/", "video/node_modules/.cache/"))
    # Hash the exact protected endpoint files and immutable original voice/model
    # inputs, excluding entire large duplicated source packages from repeat IO.
    core = [r for r in ROWS if r["path"] in PROTECTED and (r["ext"] in {".mp4", ".mp3", ".wav", ".srt", ".md", ".json", ".html"} or "retained_identical_asset_for_removed_legacy_bundle_copy" in PROTECTED[r["path"]]) and not "representative_frame" in ";".join(PROTECTED[r["path"]])]
    with ThreadPoolExecutor(max_workers=4) as pool:
        core_hashes = list(pool.map(add_digest, [dict(r) for r in core]))
    for row in core_hashes:
        row["reason"] = ";".join(sorted(PROTECTED[row["path"]]))
    counts, sizes = Counter(), Counter()
    for row in deletes:
        counts[row["reason"]] += 1
        sizes[row["reason"]] += row["bytes"]
    with (OUT / "file_decisions.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["path", "action", "bytes", "reason"])
        w.writeheader()
        w.writerows({k: r[k] for k in w.fieldnames} for r in decisions)
    manifest = {"root": str(ROOT), "authorization": "2026-10-27 user explicitly requested removal of prior nonreference video work", "scope": "video production intermediate files only; no directory recursion at deletion", "protected_endpoints": len(core_hashes), "delete_count": len(deletes), "delete_logical_bytes": sum(r["bytes"] for r in deletes), "files": deletes}
    (OUT / "delete_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (OUT / "protected_hashes.json").write_text(json.dumps({"files": core_hashes}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    summary = {"delete_count": len(deletes), "delete_logical_GiB": round(manifest["delete_logical_bytes"] / 2**30, 3), "protected_hashes": len(core_hashes), "protected_explicit_paths": len(PROTECTED), "source_reference_documents_scanned": len(documents), "by_reason": {k: {"files": counts[k], "GiB": round(sizes[k] / 2**30, 3)} for k in counts}, "physical_reclaimed_bytes": "not_estimated_from_unavailable_file_ids; measure volume free-space after cleanup", "source_component_exclusion": sorted(SOURCE_COMPONENTS)}
    (OUT / "plan_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
