import sys
sys.path.insert(0, r'C:\projects\realestate_reco')
from common import *
import pandas as pd
import numpy as np
from pathlib import Path
import json

print("=" * 60)
print("데이터 품질 체크")
print("=" * 60)

# ── 1. 수집 커버리지 ────────────────────────────────────────
meta_files = list(DIRS['raw_trade'].rglob('*.meta.json'))
real_meta = [m for m in meta_files
             if not json.loads(m.read_text(encoding='utf-8')).get('mock', True)]

real_yms = sorted(set(
    json.loads(m.read_text(encoding='utf-8'))['ym']
    for m in real_meta
))
print(f"\n[1] 수집 커버리지")
print(f"  실제 수집 파일: {len(real_meta):,}개 / 전체 {len(meta_files):,}개")
if real_yms:
    print(f"  수집 기간: {real_yms[-1]} ~ {real_yms[0]}")
    print(f"  수집 월 수: {len(set(real_yms))}")

total_rows = sum(
    json.loads(m.read_text(encoding='utf-8')).get('rows', 0)
    for m in real_meta
)
print(f"  총 거래 건수 (API totalCount 기준): {total_rows:,}건")

# ── 2. staged 데이터 로드 (실제 수집 월만) ──────────────────
print(f"\n[2] staged parquet 샘플 로드")
real_ym_set = set(real_yms)

staged_files = []
for p in DIRS['staged_trade'].rglob('*.parquet'):
    # 경로에서 year/month 추출
    parts = p.parts
    year_part  = next((x for x in parts if x.startswith('year=')), None)
    month_part = next((x for x in parts if x.startswith('month=')), None)
    if year_part and month_part:
        ym = year_part.replace('year=', '') + month_part.replace('month=', '').zfill(2)
        if ym in real_ym_set:
            staged_files.append(p)

print(f"  실제 staged 파일 수: {len(staged_files):,}개")
if not staged_files:
    print("  staged 파일 없음. step2 먼저 실행 필요.")
    exit()

dfs = [pd.read_parquet(p) for p in staged_files]
df = pd.concat(dfs, ignore_index=True)
print(f"  총 거래 행수: {len(df):,}건")
print(f"  고유 단지 수: {df['apt_id'].nunique():,}개")
print(f"  거래일 범위: {df['deal_date'].min().date()} ~ {df['deal_date'].max().date()}")

# ── 3. 거래가 분포 ─────────────────────────────────────────
print(f"\n[3] 거래가 분포 (만원)")
price_stats = df['deal_amount'].describe(percentiles=[.1, .25, .5, .75, .9])
for k, v in price_stats.items():
    print(f"  {k:8s}: {v:>12,.0f}")

# 이상값 체크
low  = (df['deal_amount'] < 5_000).sum()
high = (df['deal_amount'] > 300_000).sum()
print(f"  5천만원 미만: {low:,}건")
print(f"  30억 초과:    {high:,}건")

# ── 4. 해제 거래 비율 ──────────────────────────────────────
print(f"\n[4] 해제 거래")
cancel_n = df['is_canceled'].sum()
print(f"  해제 건수: {cancel_n:,}건 / {len(df):,}건 ({cancel_n/len(df)*100:.2f}%)")

# ── 5. 시군구별 거래 건수 Top 10 ───────────────────────────
print(f"\n[5] 시군구별 거래 건수 Top 10")
by_sgg = (df.groupby('sigungu_code')
           .size()
           .reset_index(name='count')
           .assign(name=lambda d: d['sigungu_code'].map(SIGUNGU_CODES))
           .sort_values('count', ascending=False)
           .head(10))
for _, r in by_sgg.iterrows():
    print(f"  {r['name']:12s} ({r['sigungu_code']}): {r['count']:,}건")

# ── 6. 평형 분포 ───────────────────────────────────────────
print(f"\n[6] 평형(pyeong_bucket) 분포")
pb = df['pyeong_bucket'].value_counts().sort_index()
for k, v in pb.items():
    bar = '#' * (v * 30 // pb.max())
    print(f"  {k:6s}: {v:>7,}  {bar}")

# ── 7. 연도별 거래 건수 ────────────────────────────────────
print(f"\n[7] 연도별 거래 건수")
by_year = df.groupby(df['deal_date'].dt.year).size()
for yr, cnt in by_year.items():
    bar = '#' * (cnt * 40 // by_year.max())
    print(f"  {yr}: {cnt:>7,}  {bar}")

# ── 8. 단지별 평균 거래가 Top 10 (최근 1년) ───────────────
print(f"\n[8] 단지별 평균 거래가 Top 10 (최근 1년, 비해제)")
cutoff = df['deal_date'].max() - pd.Timedelta(days=365)
df_recent = df[(df['deal_date'] >= cutoff) & (~df['is_canceled'])]
top_apts = (df_recent.groupby(['apt_id', 'apt_name_raw', 'sigungu_code'])
            .agg(avg_price=('deal_amount', 'mean'), count=('deal_amount', 'count'))
            .reset_index()
            .query('count >= 3')
            .assign(sgg=lambda d: d['sigungu_code'].map(SIGUNGU_CODES))
            .sort_values('avg_price', ascending=False)
            .head(10))
for _, r in top_apts.iterrows():
    print(f"  {r['avg_price']:>8,.0f}만원  {r['apt_name_raw'][:15]:15s} ({r['sgg']}, {r['count']}건)")

print("\n" + "=" * 60)
print("체크 완료")
