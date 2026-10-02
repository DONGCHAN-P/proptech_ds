"""테스트 데이터 제거 + 재빌드 파이프라인"""
import sys; sys.path.insert(0, r'c:\projects\realestate_reco')
from common import *
import pandas as pd
import numpy as np

TEST_FILTER = lambda df: (
    df['apt_name_raw'].str.contains('테스트', na=False) |
    df['legal_dong_name'].str.contains('테스트', na=False)
)

# ── 1. trade_events 정제 ────────────────────────────────────
print('=== 1. trade_events 정제 ===')
te = pd.read_parquet(DIRS['master'] / 'trade_events.parquet')
mask = TEST_FILTER(te)
print(f'제거 대상: {mask.sum():,}건 / 전체 {len(te):,}건')
te_clean = te[~mask].copy()
tmp = DIRS['master'] / 'trade_events.parquet.tmp'
te_clean.to_parquet(tmp, index=False, compression='zstd')
tmp.replace(DIRS['master'] / 'trade_events.parquet')
print(f'trade_events: {len(te):,} -> {len(te_clean):,}건\n')

# ── 2. apt_id_map 정제 ────────────────────────────────────
print('=== 2. apt_id_map 정제 ===')
am = pd.read_parquet(DIRS['master'] / 'apt_id_map.parquet')
mask_am = (
    am['apt_name_norm'].str.contains('테스트', na=False) |
    am['legal_dong_name'].str.contains('테스트', na=False)
)
print(f'제거 대상: {mask_am.sum()}건 / 전체 {len(am):,}건')
am_clean = am[~mask_am].copy()
tmp = DIRS['master'] / 'apt_id_map.parquet.tmp'
am_clean.to_parquet(tmp, index=False, compression='zstd')
tmp.replace(DIRS['master'] / 'apt_id_map.parquet')
print(f'apt_id_map: {len(am):,} -> {len(am_clean):,}건\n')

# ── 3. apt_master DB 동기화 ────────────────────────────────
print('=== 3. apt_master DB 동기화 ===')
import sqlite3
DB_PATH = BASE / 'realestate.db'
con = sqlite3.connect(DB_PATH)
before = con.execute("SELECT COUNT(*) FROM apt_master").fetchone()[0]
# 테스트 단지 apt_id 목록
test_ids = am[mask_am]['apt_id'].tolist()
if test_ids:
    placeholders = ','.join('?' * len(test_ids))
    con.execute(f"DELETE FROM apt_master WHERE apt_seq IN ({placeholders})", test_ids)
    con.execute(f"DELETE FROM apt_external WHERE apt_seq IN ({placeholders})", test_ids)
    con.commit()
after = con.execute("SELECT COUNT(*) FROM apt_master").fetchone()[0]
print(f'apt_master: {before:,} -> {after:,}건')
con.close()
print()

# ── 4. staged 파일들 정제 (필요시) ────────────────────────
print('=== 4. staged 파일 정제 ===')
staged_files = list(DIRS['staged_trade'].rglob('*.parquet'))
patched = 0
for p in staged_files:
    df = pd.read_parquet(p)
    if 'apt_name_raw' not in df.columns:
        continue
    mask_s = (
        df['apt_name_raw'].str.contains('테스트', na=False) |
        df['legal_dong_name'].str.contains('테스트', na=False)
    )
    if mask_s.any():
        df[~mask_s].to_parquet(p, index=False, compression='zstd')
        patched += 1
print(f'staged 파일 패치: {patched}개\n')

print('정제 완료. unified_daily 재빌드를 실행하세요:')
print('  python run_step4_unified_daily.py')
print('  python run_step7_undervalue.py')
