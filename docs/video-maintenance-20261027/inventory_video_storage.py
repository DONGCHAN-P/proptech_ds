"""Read-only inventory: never follow directory junctions or remove any file."""
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone
import json
import os
import shutil
import stat

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SCOPES = ["video-agent-studio", "video", "output", "exports", "tts_benchmark", ".remotion", ".cache", "영상", "assets"]
REPARSE = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


def main():
    files, skipped, errors = [], [], []
    for scope in SCOPES:
        start = ROOT / scope
        if not start.exists():
            continue
        pending = [start]
        while pending:
            directory = pending.pop()
            try:
                with os.scandir(directory) as entries:
                    for entry in entries:
                        p = Path(entry.path)
                        relative = p.relative_to(ROOT).as_posix()
                        try:
                            s = entry.stat(follow_symlinks=False)
                            if getattr(s, "st_file_attributes", 0) & REPARSE or entry.is_symlink():
                                skipped.append(relative)
                            elif entry.is_dir(follow_symlinks=False):
                                # Dependencies are inventoried but never deleted by name alone.
                                pending.append(p)
                            elif entry.is_file(follow_symlinks=False):
                                files.append({"path": relative, "bytes": s.st_size, "mtime_ns": s.st_mtime_ns, "dev": s.st_dev, "ino": s.st_ino, "nlink": s.st_nlink, "ext": p.suffix.lower()})
                        except OSError as ex:
                            errors.append({"path": relative, "error": type(ex).__name__})
            except OSError as ex:
                errors.append({"path": directory.relative_to(ROOT).as_posix(), "error": type(ex).__name__})
    files.sort(key=lambda r: r["path"])
    totals = defaultdict(lambda: {"bytes": 0, "files": 0})
    for r in files:
        parts = r["path"].split("/")
        if parts[:2] == ["video-agent-studio", "episodes"] and len(parts) > 2:
            key = "/".join(parts[:3])
        elif parts[0] == "video" and len(parts) > 1:
            key = "/".join(parts[:2])
        else:
            key = parts[0]
        totals[key]["bytes"] += r["bytes"]
        totals[key]["files"] += 1
    groups = defaultdict(list)
    for row in files:
        groups[(row["dev"], row["ino"])].append(row)
    ids_available = all(r["ino"] and r["nlink"] for r in files)
    summary = {"generated_at_utc": datetime.now(timezone.utc).isoformat(), "scope": SCOPES, "files": len(files), "logical_bytes": sum(r["bytes"] for r in files), "unique_file_bytes": sum(v[0]["bytes"] for v in groups.values()) if ids_available else None, "file_identity_metadata_available": ids_available, "volume_free_before_bytes": shutil.disk_usage(ROOT).free, "skipped_reparse_points": skipped, "errors": errors, "by_area": dict(sorted(totals.items(), key=lambda x: -x[1]["bytes"])), "largest_files": sorted(files, key=lambda r: -r["bytes"])[:100]}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "inventory.json").write_text(json.dumps({"root": str(ROOT), "files": files}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (OUT / "inventory_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"files": len(files), "logical_GiB": round(summary["logical_bytes"] / 2**30, 2), "unique_GiB": round(summary["unique_file_bytes"] / 2**30, 2) if ids_available else None, "free_GiB": round(summary["volume_free_before_bytes"] / 2**30, 2), "areas": [{"path": k, "GiB": round(v["bytes"] / 2**30, 2), "files": v["files"]} for k, v in list(summary["by_area"].items())[:24]], "reparse_skipped": len(skipped), "errors": len(errors)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
