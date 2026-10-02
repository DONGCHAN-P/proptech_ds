"""
run_backup_master.py — master/ 자동 일일 백업

산출물: master.backup_{YYYYMMDD_HHMMSS}/
  - unified_apt_pyeong_daily.parquet
  - trade_events.parquet
  - apt_id_map.parquet

보관 정책: 최근 7일치만 유지 (오래된 백업 자동 삭제)

실행:
  python run_backup_master.py
  python run_backup_master.py --keep 14    # 14일치 보관
"""
import sys
import shutil
import json
import re
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import BASE, DIRS

BACKUP_FILES = [
    "unified_apt_pyeong_daily.parquet",
    "trade_events.parquet",
    "apt_id_map.parquet",
]
BACKUP_PATTERN = re.compile(r"^master\.backup_\d{8}_\d{6}$")


def latest_backup_meta() -> dict | None:
    backups = sorted(
        [d for d in BASE.iterdir() if BACKUP_PATTERN.match(d.name)],
        key=lambda d: d.name,
    )
    if not backups:
        return None
    meta_p = backups[-1] / "backup_meta.json"
    if meta_p.exists():
        return json.loads(meta_p.read_text(encoding="utf-8"))
    return {"dir": str(backups[-1])}


def do_backup(keep: int) -> Path:
    ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst      = BASE / f"master.backup_{ts}"
    dst.mkdir()

    copied   = []
    skipped  = []
    total_mb = 0.0

    for fname in BACKUP_FILES:
        src = DIRS["master"] / fname
        if not src.exists():
            skipped.append(fname)
            continue
        shutil.copy2(src, dst / fname)
        mb = src.stat().st_size / 1e6
        total_mb += mb
        copied.append({"file": fname, "mb": round(mb, 2)})
        print(f"  복사: {fname}  ({mb:.1f}MB)")

    if skipped:
        print(f"  스킵 (파일 없음): {skipped}")

    meta = {
        "backup_ts": datetime.now().isoformat(),
        "backup_dir": str(dst),
        "files": copied,
        "skipped": skipped,
        "total_mb": round(total_mb, 2),
    }
    (dst / "backup_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"  총 {total_mb:.1f}MB 백업 완료 → {dst.name}")

    # 오래된 백업 정리
    all_backups = sorted(
        [d for d in BASE.iterdir() if BACKUP_PATTERN.match(d.name)],
        key=lambda d: d.name,
    )
    to_delete = all_backups[:-keep]
    for old in to_delete:
        shutil.rmtree(old)
        print(f"  삭제 (보관기한 초과): {old.name}")

    return dst


def main():
    parser = argparse.ArgumentParser(description="master/ 자동 백업")
    parser.add_argument("--keep", type=int, default=7, help="보관 백업 수 (기본 7)")
    args = parser.parse_args()

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*50}")
    print(f"  master/ 백업  {ts}")
    print(f"{'='*50}\n")

    dst = do_backup(args.keep)

    print(f"\n  백업 디렉토리: {dst}")
    print(f"  보관 정책: 최근 {args.keep}일치")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
