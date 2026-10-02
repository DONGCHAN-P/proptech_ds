"""apt_id_map.parquet → SQLite apt_master 테이블 동기화"""
import sys
sys.path.insert(0, r'c:\projects\realestate_reco')

from common import *
import pandas as pd
import sqlite3

# DB_PATH 는 common.py 가 결정한다 (legacy/ 이동 대응)
df = pd.read_parquet(DIRS['master'] / 'apt_id_map.parquet')
print(f'apt_id_map 로드: {len(df):,}건 (좌표 보유: {(df["lat"] != 0).sum():,}건)')

con = sqlite3.connect(DB_PATH)

con.execute("""
    CREATE TABLE IF NOT EXISTS apt_master (
        apt_seq   TEXT PRIMARY KEY,
        apt_name  TEXT,
        sigungu_code TEXT,
        lat       REAL,
        lng       REAL
    )
""")

con.execute("DELETE FROM apt_master")

rows = [
    (
        row['apt_id'],
        row['apt_name_norm'],
        row['sigungu_code'],
        float(row['lat']) if row['lat'] and row['lat'] != 0 else None,
        float(row['lng']) if row['lng'] and row['lng'] != 0 else None,
    )
    for _, row in df.iterrows()
]

con.executemany(
    "INSERT OR REPLACE INTO apt_master VALUES (?,?,?,?,?)",
    rows
)
con.commit()

n = con.execute("SELECT COUNT(*) FROM apt_master").fetchone()[0]
n_coord = con.execute("SELECT COUNT(*) FROM apt_master WHERE lat IS NOT NULL").fetchone()[0]
print(f'apt_master 저장: {n:,}건 (좌표 있음: {n_coord:,}건)')
con.close()
