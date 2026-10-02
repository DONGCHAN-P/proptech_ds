import sys
sys.path.insert(0, r'C:\projects\realestate_reco')
from common import *
import pandas as pd
import numpy as np
from pathlib import Path
import json

# ── 데이터 로드 ──────────────────────────────────────────
meta_files = list(DIRS['raw_trade'].rglob('*.meta.json'))
real_yms = set(
    json.loads(m.read_text(encoding='utf-8'))['ym']
    for m in meta_files
    if not json.loads(m.read_text(encoding='utf-8')).get('mock', True)
)
real_yms_2024 = {ym for ym in real_yms if ym >= '202401'}

staged_files = [
    p for p in DIRS['staged_trade'].rglob('*.parquet')
    if (lambda parts: (
        (yp := next((x for x in parts if x.startswith('year=')), None)) and
        (mp := next((x for x in parts if x.startswith('month=')), None)) and
        (yp.replace('year=','') + mp.replace('month=','').zfill(2)) in real_yms_2024
    ))(p.parts)
]

df = pd.concat([pd.read_parquet(p) for p in staged_files], ignore_index=True)
df = df[~df['is_canceled']].copy()
df['ym']     = df['deal_date'].dt.to_period('M')
df['year']   = df['deal_date'].dt.year
df['month']  = df['deal_date'].dt.month
df['sigungu_name'] = df['sigungu_code'].map(SIGUNGU_CODES)

def region(code):
    if str(code).startswith('11'): return '서울'
    if str(code).startswith('28'): return '인천'
    if str(code).startswith('41'): return '경기'
    return '기타'
df['region'] = df['sigungu_code'].apply(region)

yms = sorted(df['ym'].unique())
print(f"분석 기간: {yms[0]} ~ {yms[-1]}  |  총 {len(df):,}건\n")

# ── 1. 월별 거래량 + 전월 대비 변화 ──────────────────────
monthly = (df.groupby('ym')
             .agg(count=('deal_amount','count'),
                  median_price=('deal_amount','median'))
             .reset_index())
monthly['mom_chg']  = monthly['count'].pct_change() * 100
monthly['mom_sign'] = monthly['mom_chg'].apply(lambda x: '+' if x >= 0 else '-' if pd.notna(x) else ' ')
monthly['ym_str']   = monthly['ym'].astype(str)

# 같은 달(1~12월) 기준 YoY 비교
monthly['month_num'] = monthly['ym'].apply(lambda p: p.month)
monthly['year_num']  = monthly['ym'].apply(lambda p: p.year)
count_map = dict(zip(zip(monthly['year_num'], monthly['month_num']), monthly['count']))
monthly['yoy_chg'] = monthly.apply(
    lambda r: (r['count'] - count_map.get((r['year_num']-1, r['month_num']), np.nan))
              / count_map.get((r['year_num']-1, r['month_num']), np.nan) * 100
    if count_map.get((r['year_num']-1, r['month_num'])) else np.nan,
    axis=1
)

max_count = monthly['count'].max()

print("=" * 72)
print("[1] 월별 거래량 추이  (전월비 MoM / 전년동월비 YoY)")
print("=" * 72)
print(f"{'월':<9} {'거래량':>7}  {'MoM':>7}  {'YoY':>7}  거래량 바 차트")
print("-" * 72)
for _, r in monthly.iterrows():
    bar_len = int(r['count'] / max_count * 35)
    bar = '#' * bar_len
    mom = f"{r['mom_chg']:>+6.1f}%" if pd.notna(r['mom_chg']) else '      -'
    yoy = f"{r['yoy_chg']:>+6.1f}%" if pd.notna(r['yoy_chg']) else '      -'
    print(f"{r['ym_str']:<9} {r['count']:>7,}건  {mom}  {yoy}  {bar}")

# ── 2. 지역별 월별 거래량 ─────────────────────────────────
print("\n" + "=" * 72)
print("[2] 지역별(서울/경기/인천) 월별 거래량")
print("=" * 72)
reg_vol = (df.groupby(['ym','region'])
             .size()
             .unstack('region')
             .reindex(columns=['서울','경기','인천'])
             .fillna(0)
             .astype(int))
reg_vol['합계'] = reg_vol.sum(axis=1)
reg_vol.index  = reg_vol.index.astype(str)

print(f"{'월':<9} {'서울':>7} {'경기':>8} {'인천':>8} {'합계':>8}  서울비중")
print("-" * 55)
for ym_str, row in reg_vol.iterrows():
    seoul_ratio = row['서울'] / row['합계'] * 100 if row['합계'] > 0 else 0
    print(f"{ym_str:<9} {row['서울']:>7,}  {row['경기']:>7,}  {row['인천']:>7,}  {row['합계']:>7,}  {seoul_ratio:.1f}%")

# ── 3. 계절성 분석 (월별 평균 거래량) ────────────────────
print("\n" + "=" * 72)
print("[3] 계절성 분석  (월별 평균 거래량 / 연도 평균 제거)")
print("=" * 72)
monthly['ym_str2'] = monthly['ym'].astype(str)
seasonal = (monthly.groupby('month_num')
              .agg(avg_count=('count','mean'),
                   std_count=('count','std'),
                   n_years=('count','count'))
              .reset_index())
overall_mean = seasonal['avg_count'].mean()
seasonal['idx'] = seasonal['avg_count'] / overall_mean * 100  # 계절지수

print(f"{'월':>4}  {'평균거래량':>9}  {'계절지수':>8}  상대 바 차트")
print("-" * 55)
for _, r in seasonal.iterrows():
    bar_len = int(r['idx'] / 150 * 30)
    bar = '#' * bar_len
    flag = '<- 성수기' if r['idx'] >= 120 else ('<- 비수기' if r['idx'] <= 80 else '')
    print(f"{int(r['month_num']):>3}월  {r['avg_count']:>9,.0f}건  {r['idx']:>7.1f}   {bar}  {flag}")

# ── 4. 거래량 vs 가격 상관관계 (월별) ────────────────────
print("\n" + "=" * 72)
print("[4] 거래량 vs 가격 상관관계")
print("=" * 72)
corr = monthly[['count','median_price']].corr().iloc[0,1]
print(f"  월별 거래량-중위가 상관계수: r = {corr:.3f}")
if corr > 0.5:
    print("  -> 거래량 증가 시 가격 상승 동행 (양의 상관)")
elif corr < -0.5:
    print("  -> 거래량 증가 시 가격 하락 (음의 상관, 급매 증가 패턴)")
else:
    print("  -> 뚜렷한 선형 관계 없음")

# 거래량 급증 월의 가격 변화 확인
monthly['lead_price_chg'] = monthly['median_price'].pct_change(1).shift(-1) * 100
high_vol = monthly.nlargest(5, 'count')[['ym_str','count','median_price','lead_price_chg']]
print(f"\n  거래량 Top 5개월 → 다음달 가격 변화:")
print(f"  {'월':<9} {'거래량':>7}  {'당월가(만)':>10}  {'다음달가격변화':>13}")
for _, r in high_vol.iterrows():
    nxt = f"{r['lead_price_chg']:>+8.1f}%" if pd.notna(r['lead_price_chg']) else '     N/A'
    print(f"  {r['ym_str']:<9} {r['count']:>7,}건  {r['median_price']/10000:>7.2f}억  {nxt}")

# ── 5. 시군구별 거래량 변화 트렌드 ───────────────────────
print("\n" + "=" * 72)
print("[5] 최근 6개월 거래량 증감 두드러진 시군구")
print("=" * 72)
last6 = yms[-6:]
first3 = last6[:3]
last3  = last6[3:]

sgg_vol = df.groupby(['sigungu_name','ym']).size().unstack('ym').fillna(0)
f3_cols = [ym for ym in first3 if ym in sgg_vol.columns]
l3_cols = [ym for ym in last3  if ym in sgg_vol.columns]

if f3_cols and l3_cols:
    sgg_vol['f3'] = sgg_vol[f3_cols].mean(axis=1)
    sgg_vol['l3'] = sgg_vol[l3_cols].mean(axis=1)
    sgg_vol['trend'] = (sgg_vol['l3'] - sgg_vol['f3']) / sgg_vol['f3'].replace(0, np.nan) * 100
    sgg_vol = sgg_vol.dropna(subset=['trend'])
    sgg_vol['total'] = sgg_vol[f3_cols + l3_cols].sum(axis=1)
    sgg_vol = sgg_vol[sgg_vol['total'] >= 100]  # 소량 제외

    print(f"  비교: {first3[0]}~{first3[-1]} 평균 vs {last3[0]}~{last3[-1]} 평균")
    print(f"\n  증가 Top 10:")
    print(f"  {'시군구':<14} {'전반3개월':>8}  {'후반3개월':>8}  {'변화율':>8}")
    for sgg, row in sgg_vol.nlargest(10,'trend').iterrows():
        print(f"  {sgg:<12} {row['f3']:>7.0f}건  {row['l3']:>7.0f}건  {row['trend']:>+7.1f}%")

    print(f"\n  감소 Top 10:")
    for sgg, row in sgg_vol.nsmallest(10,'trend').iterrows():
        print(f"  {sgg:<12} {row['f3']:>7.0f}건  {row['l3']:>7.0f}건  {row['trend']:>+7.1f}%")

print("\n분석 완료")
