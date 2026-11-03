"""배포 묶음 만들기 — 서버가 실제로 읽는 것만 deploy/build/ 에 모은다.

프로젝트 루트에는 raw/ · master/ · exports/ 같은 수 GB 데이터가 있어서 그대로 빌드
컨텍스트로 쓰면 업로드가 끝나지 않는다. 서버가 읽는 것은 이것뿐이다.

    web/*.py · web/static/      코드
    web/cache/*.parquet         서빙 인덱스 (build_index.py 산출물, 약 75MB)
    legacy/realestate.db        역 · 학교 · 공원 세 테이블만 남긴 사본 (원본 11MB → 수백 KB)
    exports/daily/              랭킹 패널이 읽는 최신 파일 2개 (explore.html 용)

사용:
    .venv\\Scripts\\python.exe deploy\\bundle.py
    cd deploy\\build && fly deploy
"""
from __future__ import annotations

import shutil
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
OUT = HERE / "build"

CACHE_FILES = ["apt_index.parquet", "apt_pyeong.parquet", "trades.parquet",
               "region_index.parquet", "apt_geo.parquet", "complex_facts.parquet"]
DB_TABLES = ["subway_stations", "schools", "parks"]
EXPORT_PATTERNS = ["undervalue_top5_*.parquet", "new_trades_notable_*.csv"]


def copy_code() -> None:
    web = OUT / "web"
    web.mkdir(parents=True)
    for f in (ROOT / "web").glob("*.py"):
        if f.name != "build_index.py":           # 서버에서는 인덱스를 다시 만들지 않는다
            shutil.copy2(f, web / f.name)
    shutil.copy2(ROOT / "web" / "requirements.txt", web / "requirements.txt")
    shutil.copytree(ROOT / "web" / "static", web / "static")


def copy_cache() -> None:
    dst = OUT / "web" / "cache"
    dst.mkdir()
    for name in CACHE_FILES:
        src = ROOT / "web" / "cache" / name
        if not src.exists():
            sys.exit(f"[bundle] {src} 없음 — 먼저 web\\build_index.py 를 돌리세요")
        shutil.copy2(src, dst / name)


def slim_db() -> None:
    """원본 DB 에서 서버가 쓰는 세 테이블만 새 파일로 옮긴다."""
    src = ROOT / "legacy" / "realestate.db"
    dst = OUT / "legacy" / "realestate.db"
    dst.parent.mkdir()
    s = sqlite3.connect(f"file:{src.as_posix()}?mode=ro", uri=True)
    d = sqlite3.connect(dst)
    for t in DB_TABLES:
        ddl = s.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?", [t]).fetchone()[0]
        d.execute(ddl)
        rows = s.execute(f"SELECT * FROM {t}").fetchall()
        if rows:
            d.executemany(f"INSERT INTO {t} VALUES ({','.join('?' * len(rows[0]))})", rows)
    d.commit()
    d.execute("VACUUM")
    d.close()
    s.close()


def copy_exports() -> None:
    dst = OUT / "exports" / "daily"
    dst.mkdir(parents=True)
    for pat in EXPORT_PATTERNS:
        files = sorted((ROOT / "exports" / "daily").glob(pat))
        if files:
            shutil.copy2(files[-1], dst / files[-1].name)


def copy_deploy_files() -> None:
    for name in ["Dockerfile", "fly.toml", ".dockerignore"]:
        shutil.copy2(HERE / name, OUT / name)


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    copy_code()
    copy_cache()
    slim_db()
    copy_exports()
    copy_deploy_files()
    size = sum(f.stat().st_size for f in OUT.rglob("*") if f.is_file())
    print(f"[bundle] {OUT} : {size / 2**20:.1f}MB")


if __name__ == "__main__":
    main()
