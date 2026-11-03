"""Current video-only cleanup inventory and dependency-aware plan. No deletion."""
from pathlib import Path
import importlib.util, json, re

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
PREVIOUS = ROOT / "docs/video-maintenance-20261027"

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

OUT.mkdir(exist_ok=True)
inventory = module("video_inventory", PREVIOUS / "inventory_video_storage.py")
inventory.OUT = OUT
inventory.SCOPES = ["video-agent-studio", "video/src", "video/public", "video/out", "video/node_modules/.cache", ".cache/webpack", "assets", "영상"]
inventory.main()
plan = module("video_retention", PREVIOUS / "plan_storage_cleanup.py")
plan.OUT = OUT
plan.ROWS = json.loads((OUT / "inventory.json").read_text(encoding="utf-8"))["files"]
plan.BY_PATH = {r["path"]: r for r in plan.ROWS}
plan.CURRENT_PACKAGES += [
    "video-agent-studio/episodes/affordable-home-price-20261026/outputs/jun-quality-v2",
    "video-agent-studio/episodes/affordable-home-price-20261026/editor/jun-quality-v2/main",
]
plan.ACTIVE_PREFIXES += [
    "video-agent-studio/episodes/affordable-home-price-20261026/editor/jun-quality-v2/main/project/",
]
old_frame_output = plan.frame_output
def frame_output(path):
    if old_frame_output(path): return True
    if "/qa/" in path or path.startswith("video/out/qa-"): return True
    if "/director/shorts-ending-fix-v1/" in path:
        return bool(re.match(r"(?:promo|summary)_(?:v5_\d{2}_\d|\d+\.\d+\.)", Path(path).name))
    return False
plan.frame_output = frame_output

# Protect exact dependencies of the newly published film and corrected Shorts.
# The project still reads older MP4/AAC material; do not infer obsolescence by age.
ep = ROOT / "video-agent-studio/episodes/affordable-home-price-20261026"
for path in [
    ep / "editor/jun-quality-v2/main/patch-S18/final_correction_receipt.json",
    ep / "editor/jun-quality-v2/main/assembly_receipt.json",
    ep / "editor/jun-quality-v2/main/render_receipt.json",
    ep / "director/shorts-ending-fix-v1/promo_render_command.json",
    ep / "director/shorts-ending-fix-v1/summary_render_command.json",
    ep / "director/shorts-ending-fix-v1/edit_plan.json",
    ep / "narration/jun-user-script-v1/scene_alignment.json",
]:
    plan.protect_document_refs(path, "current_published_reproduction_dependency")
for path in [
    ep / "outputs/jun-quality-v2/main/affordable_home_price_jun_quality_v2.mp4",
    ep / "outputs/jun-user-script-v1/full-film-v1/affordable_price_jun_user_script_v2.mp4",
    ep / "editor/jun-quality-v2/main/patch-S18/S18_corrected_v1.mp4",
    ep / "outputs/jun-quality-v2/shorts/01_promo_jun_v4.mp4",
    ep / "outputs/jun-quality-v2/shorts/02_summary_jun_v4.mp4",
    ep / "qa/shorts-ending-fix-v1/promo_before_cta.png",
    ep / "qa/shorts-ending-fix-v1/promo_at_cta.png",
    ep / "qa/shorts-ending-fix-v1/promo_v5_frame_12.png",
    ep / "qa/shorts-ending-fix-v1/summary_v5_frame_12.png",
]:
    plan.protect(path, "current_reproduction_or_representative_failure_evidence")
plan.main()

# Additional bounded derived audio and video/out evidence cases. Keep current
# render inputs and originals; preserve diagnostic contact sheets/first-mid-last.
manifest = json.loads((OUT / "delete_manifest.json").read_text(encoding="utf-8"))
protected = json.loads((OUT / "protected_hashes.json").read_text(encoding="utf-8"))
protected_paths = set(plan.PROTECTED) | {r["path"] for r in protected["files"]}
extra = []
existing_deletes = {r["path"] for r in manifest["files"]}
legacy_groups = {}
for row in plan.ROWS:
    if row["path"].startswith("video/out/qa-") and row["ext"] in {".png", ".jpg", ".jpeg"}:
        legacy_groups.setdefault(str(Path(row["path"]).parent), []).append(row["path"])
for group in legacy_groups.values(): group.sort()
for row in plan.ROWS:
    p, ext = row["path"], row["ext"]
    if p in protected_paths or p in existing_deletes: continue
    reason = None
    parts = set(p.lower().split("/"))
    if p.startswith("video/out/qa-") and ext in {".png", ".jpg", ".jpeg"}:
        siblings = legacy_groups[str(Path(p).parent)]
        representatives = {siblings[0], siblings[len(siblings)//2], siblings[-1]}
        if p not in representatives and not plan.KEEP_IMAGE_NAME.search(Path(p).name):
            reason = "redundant_legacy_video_out_QA_frame"
    if p.startswith("video-agent-studio/episodes/") and ext in {".wav", ".f32", ".pcm"} and not parts & plan.SOURCE_COMPONENTS:
        name = Path(p).name
        if re.search(r"(?:decoded|regression|_asr|_encoded_end|_source_S\d+|analysis_16k|premix|full_mix|mixed_audio)", name, re.I):
            reason = "derived_audio_analysis_or_mix_original_inputs_preserved"
        elif "/editor/jun-quality-v2/shorts/" in p and re.search(r"_v[1-4]_audio\.wav$", name):
            reason = "superseded_shorts_audio_render_original_Jun_inputs_preserved"
    if p.startswith("video-agent-studio/episodes/") and "__pycache__" in parts and not parts & (plan.SOURCE_COMPONENTS | {"deps", "node_modules", "site-packages"}) and not any(x.endswith("deps") for x in parts) and ext == ".pyc":
        reason = "regenerable_local_python_bytecode"
    if not reason: continue
    path = ROOT / p
    assert path.stat().st_size == row["bytes"] and path.stat().st_mtime_ns == row["mtime_ns"]
    extra.append({**row, "action": "delete", "reason": reason, "sha256": plan.sha_file(path)})
manifest["files"].extend(extra)
manifest.update(authorization="2026-10-28 user requested video-work file cleanup; preserve current published originals and sources", delete_count=len(manifest["files"]), delete_logical_bytes=sum(r["bytes"] for r in manifest["files"]))
manifest["files"].sort(key=lambda r:r["path"])
(OUT / "delete_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

import csv
overrides = {r["path"]: r for r in extra}
with (OUT / "file_decisions.csv").open(encoding="utf-8-sig", newline="") as f: decisions = list(csv.DictReader(f))
for row in decisions:
    if row["path"] in overrides:
        row.update(action="delete", reason=overrides[row["path"]]["reason"])
with (OUT / "file_decisions.csv").open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["path", "action", "bytes", "reason"])
    writer.writeheader(); writer.writerows(decisions)
summary = {"delete_count": manifest["delete_count"], "delete_logical_GiB": round(manifest["delete_logical_bytes"]/2**30, 3), "protected_hashed_files": len(protected["files"]), "additional_derived_candidates": len(extra), "largest_delete_candidates": sorted(manifest["files"], key=lambda r:-r["bytes"])[:30]}
(OUT / "current_plan_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({k:v for k,v in summary.items() if k != "largest_delete_candidates"}))
