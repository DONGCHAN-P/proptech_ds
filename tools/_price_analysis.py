import sys
sys.path.insert(0, r'C:\projects\realestate_reco')
from common import *
import pandas as pd
import numpy as np
from pathlib import Path
import json

# ── 데이터 로드 (2024년 이후 실제 수집 월만) ────────────────
meta_files = list(DIRS['raw_trade'].rglob('*.meta.json'))
real_yms = set(
    json.loads(m.read_text(encoding='utf-8'))['ym']
    for m in meta_files
    if not json.loads(m.read_text(encoding='utf-8')).get('mock', True)
)
real_yms_2024 = {ym for ym in real_yms if ym >= '202401'}

staged_files = []
for p in DIRS['staged_trade'].rglob('*.parquet'):
    parts = p.parts
    yp = next((x for x in parts if x.startswith('year=')), None)
    mp = next((x for x in parts if x.startswith('month=')), None)
    if yp and mp:
        ym = yp.replace('year=', '') + mp.replace('month=', '').zfill(2)
        if ym in real_yms_2024:
            staged_files.append(p)

print(f"로드 파일 수: {len(staged_files):,}개 ({min(real_yms_2024)} ~ {max(real_yms_2024)})")
df = pd.concat([pd.read_parquet(p) for p in staged_files], ignore_index=True)

# 해제 거래 제거, 핵심 컬럼만
df = df[~df['is_canceled']].copy()
df['ym'] = df['deal_date'].dt.to_period('M')
df['sigungu_name'] = df['sigungu_code'].map(SIGUNGU_CODES)
df = df.dropna(subset=['deal_amount', 'area_m2', 'sigungu_name'])

# 평당가(만원/3.3㎡) 기준 분석
df['price_per_pyeong'] = df['deal_amount'] / df['area_m2'] * 3.3058
print(f"분석 대상: {len(df):,}건\n")

# ── 1. 월별 전체 시장 흐름 ────────────────────────────────
monthly = (df.groupby('ym')
             .agg(avg_price=('deal_amount','median'),
                  avg_per_pyeong=('price_per_pyeong','median'),
                  count=('deal_amount','count'))
             .reset_index())
monthly['ym_str'] = monthly['ym'].astype(str)

print("=" * 65)
print("[1] 전체 수도권 월별 중위 거래가 추이")
print("=" * 65)
print(f"{'월':<8} {'중위가(억)':>10} {'중위평당가(만)':>13} {'거래량':>8}")
print("-" * 45)
for _, r in monthly.iterrows():
    bar = '#' * (int(r['avg_per_pyeong']) // 200)
    print(f"{r['ym_str']:<8} {r['avg_price']/10000:>9.2f}억  {r['avg_per_pyeong']:>9,.0f}만  {r['count']:>7,}건  {bar}")

# ── 2. 시군구별 최신 vs 24년 초 가격 변화율 ────────────────
pivot = (df.groupby(['sigungu_name', 'ym'])['price_per_pyeong']
           .median()
           .unstack('ym'))

# 비교 기준: 2024년 상반기 평균 vs 최근 3개월 평균
yms_sorted = sorted(df['ym'].unique())
base_yms   = [ym for ym in yms_sorted if '2024' in str(ym) and str(ym) <= '202406']
recent_yms = yms_sorted[-3:]

sgg_stats = []
for sgg in pivot.index:
    base_vals   = pivot.loc[sgg, [ym for ym in base_yms if ym in pivot.columns]].dropna()
    recent_vals = pivot.loc[sgg, [ym for ym in recent_yms if ym in pivot.columns]].dropna()
    if len(base_vals) < 2 or len(recent_vals) < 1:
        continue
    base_med   = base_vals.median()
    recent_med = recent_vals.median()
    chg_pct    = (recent_med - base_med) / base_med * 100
    # 거래량
    cnt = df[df['sigungu_name'] == sgg]['deal_amount'].count()
    sgg_stats.append({
        'sigungu':     sgg,
        'base_price':  base_med,
        'recent_price':recent_med,
        'chg_pct':     chg_pct,
        'count':       cnt,
    })

df_sgg = pd.DataFrame(sgg_stats).sort_values('chg_pct', ascending=False)

print("\n" + "=" * 65)
print(f"[2] 시군구별 평당가 변화율  (기준: 24H1 vs 최근 3개월)")
print(f"    비교 기간: {'-'.join(str(x) for x in base_yms[:1]+base_yms[-1:])}  vs  {recent_yms[0]}~{recent_yms[-1]}")
print("=" * 65)
print(f"{'시군구':<14} {'기준평당가':>10} {'최근평당가':>10} {'변화율':>8} {'거래량':>7}")
print("-" * 55)

# 상승 Top 10
print("  --- 상승 Top 10 ---")
for _, r in df_sgg.head(10).iterrows():
    arrow = 'UP' if r['chg_pct'] > 0 else 'DN'
    print(f"  {r['sigungu']:<12} {r['base_price']:>8,.0f}만  {r['recent_price']:>8,.0f}만  {r['chg_pct']:>+6.1f}%  {r['count']:>6,}건")

# 하락 Top 10
print("\n  --- 하락 Top 10 ---")
for _, r in df_sgg.tail(10).sort_values('chg_pct').iterrows():
    print(f"  {r['sigungu']:<12} {r['base_price']:>8,.0f}만  {r['recent_price']:>8,.0f}만  {r['chg_pct']:>+6.1f}%  {r['count']:>6,}건")

# ── 3. 지역군별 (서울/경기/인천) 비교 ────────────────────
print("\n" + "=" * 65)
print("[3] 지역군별 월별 중위 평당가 추이")
print("=" * 65)

seoul_sgg  = {k for k, v in SIGUNGU_CODES.items() if k.startswith('11')}
incheon_sgg= {k for k, v in SIGUNGU_CODES.items() if k.startswith('28')}
gyeonggi_sgg={k for k, v in SIGUNGU_CODES.items() if k.startswith('41')}

def region(code):
    if code in seoul_sgg: return '서울'
    if code in incheon_sgg: return '인천'
    if code in gyeonggi_sgg: return '경기'
    return '기타'

df['region'] = df['sigungu_code'].apply(region)
reg_monthly = (df.groupby(['region', 'ym'])['price_per_pyeong']
                 .median()
                 .unstack('region'))

print(f"\n{'월':<8} {'서울':>10} {'경기':>10} {'인천':>10}  (중위 만원/평)")
print("-" * 45)
for ym in yms_sorted:
    row = reg_monthly.loc[ym] if ym in reg_monthly.index else None
    if row is None:
        continue
    s = f"{row.get('서울', float('nan')):>9,.0f}" if pd.notna(row.get('서울')) else f"{'N/A':>9}"
    g = f"{row.get('경기', float('nan')):>9,.0f}" if pd.notna(row.get('경기')) else f"{'N/A':>9}"
    i = f"{row.get('인천', float('nan')):>9,.0f}" if pd.notna(row.get('인천')) else f"{'N/A':>9}"
    print(f"  {ym}  {s}만  {g}만  {i}만")

# ── 4. 거래량 이상 감지 ───────────────────────────────────
print("\n" + "=" * 65)
print("[4] 거래량 급등/급감 시군구 (전월 대비)")
print("=" * 65)
last2 = yms_sorted[-2:]
if len(last2) == 2:
    vol = (df.groupby(['sigungu_name', 'ym'])
             .size()
             .unstack('ym')
             .fillna(0))
    if last2[0] in vol.columns and last2[1] in vol.columns:
        vol['chg'] = (vol[last2[1]] - vol[last2[0]]) / vol[last2[0]].replace(0, np.nan) * 100
        vol = vol.dropna(subset=['chg'])
        print(f"  비교: {last2[0]} -> {last2[1]}")
        print("  급증 Top 5:")
        for sgg, row in vol.nlargest(5, 'chg').iterrows():
            print(f"    {sgg:<12} {row[last2[0]]:.0f} -> {row[last2[1]]:.0f}건  ({row['chg']:+.1f}%)")
        print("  급감 Top 5:")
        for sgg, row in vol.nsmallest(5, 'chg').iterrows():
            print(f"    {sgg:<12} {row[last2[0]]:.0f} -> {row[last2[1]]:.0f}건  ({row['chg']:+.1f}%)")

print("\n분석 완료")
