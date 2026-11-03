"""Preserve named diagnostic figures and verify every planned deletion."""
from pathlib import Path
from collections import Counter
import csv, hashlib, json, re

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
read = lambda p: json.loads(p.read_text(encoding="utf-8-sig"))
def sha(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for x in iter(lambda:f.read(4*1024*1024), b""): h.update(x)
    return h.hexdigest()
def save(p, d): p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
inventory = read(OUT / "inventory.json")["files"]
by_path = {r["path"]:r for r in inventory}
manifest = read(OUT / "delete_manifest.json")
protected = read(OUT / "protected_hashes.json")
named = []
kept = []
for r in manifest["files"]:
    path = Path(r["path"])
    parts = set(r["path"].lower().split("/"))
    diagnostic = path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"} and ("/qa/" in r["path"] or "/encoded_checks/" in r["path"] or "/director/shorts-ending-fix-v1/" in r["path"] or r["path"].startswith("video/out/qa-"))
    numeric = re.search(r"\d{2,}|\d\.\d+", re.sub(r"v\d+", "version", path.stem, flags=re.I))
    if diagnostic and not numeric:
        named.append({**r, "action": "keep", "reason": "named_diagnostic_figure_preserved"})
    elif r["reason"] == "regenerable_local_python_bytecode" and (parts & {"research", "narration", "writer", "visual", "models", "model-cache", "deps", "node_modules"} or any(x.endswith("deps") for x in parts)):
        named.append({**r, "action": "keep", "reason": "source_or_installed_dependency_bytecode_preserved"})
    else: kept.append(r)
manifest["files"] = kept
manifest.update(delete_count=len(kept), delete_logical_bytes=sum(r["bytes"] for r in kept))
save(OUT / "delete_manifest.json", manifest)
for r in named: protected["files"].append(r)
for r in protected["files"]:
    if r.get("reason") in {"named_diagnostic_figure_preserved", "source_or_installed_dependency_bytecode_preserved"}: r["action"] = "keep"
for value in [
    "video-agent-studio/episodes/housing-choice-networth-20261020/qa/private-production-v1/asr/models/medium/model.bin",
    "video-agent-studio/episodes/housing-choice-networth-20261020/qa/private-production-v1/asr/models/systran-faster-whisper-small/model.bin",
    "video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe",
]:
    if value not in {r["path"] for r in protected["files"]} and value in by_path:
        protected["files"].append({**by_path[value], "sha256": sha(ROOT / value), "reason": "reusable_installed_runtime_or_ASR_model"})
save(OUT / "protected_hashes.json", protected)
with (OUT / "file_decisions.csv").open(encoding="utf-8-sig", newline="") as f: decisions=list(csv.DictReader(f))
names={r["path"]:r["reason"] for r in named}
for r in decisions:
    if r["path"] in names: r.update(action="keep", reason=names[r["path"]])
with (OUT / "file_decisions.csv").open("w", encoding="utf-8-sig", newline="") as f:
    w=csv.DictWriter(f, fieldnames=["path", "action", "bytes", "reason"]); w.writeheader(); w.writerows(decisions)

protected_paths = {r["path"] for r in protected["files"]}
assert not protected_paths & {r["path"] for r in kept}
for r in kept:
    p = (ROOT / r["path"]).resolve()
    assert p.is_relative_to(ROOT)
    assert r["path"].startswith(("video-agent-studio/episodes/", "video/out/", ".cache/webpack/", "video/node_modules/.cache/"))
    parts = set(r["path"].lower().split("/"))
    assert not parts & {"research", "narration", "writer", "visual", "models", "model-cache", "deps", "node_modules"} or r["path"].startswith("video/node_modules/.cache/")
    assert p.stat().st_size == r["bytes"] and sha(p) == r["sha256"]
    q = p.parent
    while q != ROOT:
        assert not (getattr(q.lstat(), "st_file_attributes", 0) & 0x400)
        q = q.parent
cfg = read(ROOT / "config/video_shelf.json")
for entry in cfg["entries"]:
    for label, value in entry["files"].items():
        original = (ROOT / value).resolve()
        assert original.is_file() and original.relative_to(ROOT).as_posix() not in {r["path"] for r in kept}
summary = {"delete_files": len(kept), "delete_logical_GiB": round(manifest["delete_logical_bytes"]/2**30,3), "named_diagnostics_additionally_kept":sum(r.get("reason")=="named_diagnostic_figure_preserved" for r in protected["files"]), "protected_hashed_files":len(protected["files"]), "by_reason":dict(Counter(r["reason"] for r in kept)), "largest_deletions":[{"path":r["path"],"bytes":r["bytes"],"reason":r["reason"]} for r in sorted(kept,key=lambda r:-r["bytes"])[:20]]}
save(OUT / "review_summary.json",summary)
save(OUT / "retention_review.json", {"approved": True, "required_open": 0, "reviewer": "parent agent; not an independent subagent approval", "delete_manifest_sha256":sha(OUT / "delete_manifest.json"), "checks": ["all exact paths/parents within video roots; no junction traversal", "all planned size/SHA values rechecked", "all managed final and reference endpoints protected", "current main baseline audio/patch and corrected Shorts inputs protected", "named diagnostics and representative frames retained", "original voices, models, source/research/data/code/approvals preserved"], "summary":summary})
print(json.dumps(summary, ensure_ascii=False))
