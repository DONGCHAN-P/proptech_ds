"""
Colab 업로드용 통합 parquet 생성.
- trade_events + apt_id_map join -> 분석에 필요한 모든 컬럼 포함
- 용량 최적화: 불필요 컬럼 제거, zstd 압축
"""
import sys, io
sys.path.insert(0, r'C:\projects\realestate_reco')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from common import *
import pandas as pd
from pathlib import Path

print("통합 파일 생성 중...")

# ── 0. 실제 수집된 월 목록 로드 ──────────────────────────
import json
meta_files = list(DIRS['raw_trade'].rglob('*.meta.json'))
real_yms = {
    json.loads(m.read_text(encoding='utf-8'))['ym']
    for m in meta_files
    if not json.loads(m.read_text(encoding='utf-8')).get('mock', True)
}
print(f"실제 수집 월: {len(real_yms)}개  ({min(real_yms)} ~ {max(real_yms)})")

# ── 1. trade_events 로드 (실제 수집 월만) ───────────────
df_raw = pd.read_parquet(DIRS['master'] / 'trade_events.parquet')
df_raw['deal_ym_key'] = df_raw['deal_date'].dt.strftime('%Y%m')
df = df_raw[df_raw['deal_ym_key'].isin(real_yms)].drop(columns='deal_ym_key')
print(f"trade_events: {len(df):,}건, {df.apt_id.nunique():,}개 단지")

# ── 2. apt_id_map join (단지 메타) ────────────────────────
apt = pd.read_parquet(DIRS['master'] / 'apt_id_map.parquet')
apt_meta = apt[['apt_id', 'kapt_code', 'match_status']].drop_duplicates('apt_id')
df = df.merge(apt_meta, on='apt_id', how='left')

# ── 3. 파생 컬럼 추가 ─────────────────────────────────────
df['deal_year']  = df['deal_date'].dt.year
df['deal_month'] = df['deal_date'].dt.month
df['deal_ym']    = df['deal_date'].dt.to_period('M').astype(str)

# 지역 구분
def region(code):
    c = str(code)
    if c.startswith('11'): return '서울'
    if c.startswith('28'): return '인천'
    if c.startswith('41'): return '경기'
    return '기타'
df['region'] = df['sigungu_code'].apply(region)

# ── 4. 타입 최적화 ────────────────────────────────────────
df['deal_amount']      = df['deal_amount'].astype('float32')
df['area_m2']          = df['area_m2'].astype('float32')
df['price_per_m2']     = df['price_per_m2'].astype('float32')
df['price_per_pyeong'] = df['price_per_pyeong'].astype('float32')

# ── 5. 저장 ───────────────────────────────────────────────
out_path = BASE / 'exports' / 'realestate_metro_2006_2026.parquet'
out_path.parent.mkdir(parents=True, exist_ok=True)
df.to_parquet(out_path, index=False, compression='zstd')

size_mb = out_path.stat().st_size / 1024 / 1024
print(f"\n저장 완료: {out_path}")
print(f"행수:   {len(df):,}건")
print(f"컬럼:   {len(df.columns)}개")
print(f"용량:   {size_mb:.1f} MB")

# ── 6. 컬럼 목록 출력 ────────────────────────────────────
print(f"\n컬럼 목록:")
for col in df.columns:
    print(f"  {col:<25} {str(df[col].dtype):<12} "
          f"null: {df[col].isna().sum():,}건")

# ── 7. 연도별 행수 요약 ───────────────────────────────────
print(f"\n연도별 거래 건수:")
for yr, cnt in df.groupby('deal_year').size().items():
    print(f"  {yr}: {cnt:>8,}건")
