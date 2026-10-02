"""Step 7: 지역별 저평가 단지 Top 5 리스트 생성

지역별 최적 가중치 기준으로 각 시군구 내 저평가 단지 상위 5개를 추출.
산출물: exports/daily/undervalue_top5_YYYYMMDD.parquet + CSV
"""
import sys
sys.path.insert(0, r'c:\projects\realestate_reco')

from common import *
import pandas as pd
import numpy as np
import sqlite3
import json
from datetime import datetime

# DB_PATH 는 common.py 가 결정한다 (legacy/ 이동 대응)
REGION_MAP = {'11': '서울', '28': '인천', '41': '경기'}


def load_data():
    ud = pd.read_parquet(DIRS['master'] / 'unified_apt_pyeong_daily.parquet')
    am = pd.read_parquet(DIRS['master'] / 'apt_id_map.parquet')
    latest = ud['snapshot_date'].max()
    snap = ud[ud['snapshot_date'] == latest].copy()

    con = sqlite3.connect(DB_PATH)
    ext = pd.read_sql("""
        SELECT apt_seq as apt_id,
               nearest_station, walk_min, nearest_line,
               elem_school_cnt_1km, nearest_school_dist,
               redv_nearby, redv_status_best,
               commerce_score, infra_score
        FROM apt_external
    """, con)
    con.close()

    df = snap.merge(ext, on='apt_id', how='left')
    df = df.merge(
        am[['apt_id', 'lat', 'lng', 'sigungu_code']].drop_duplicates('apt_id'),
        on='apt_id', how='left', suffixes=('', '_map')
    )
    if 'sigungu_code_map' in df.columns:
        df['sigungu_code'] = df['sigungu_code'].fillna(df['sigungu_code_map'])
        df.drop(columns=['sigungu_code_map'], inplace=True)
    df['region'] = df['sigungu_code'].str[:2].map(REGION_MAP)
    return df, latest


def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # 단기 모멘텀
    has_30  = df['trade_30d_avg_price'].notna()  & (df['trade_30d_count']  >= 2)
    has_90  = df['trade_90d_avg_price'].notna()  & (df['trade_90d_count']  >= 2)
    has_365 = df['trade_365d_avg_price'].notna() & (df['trade_365d_count'] >= 2)

    df['mom_30_90'] = np.where(
        has_30 & has_90 & (df['trade_90d_avg_price'] > 0),
        (df['trade_30d_avg_price'] - df['trade_90d_avg_price'])
        / df['trade_90d_avg_price'] * 100, 0.0
    ).clip(-20, 20)

    df['mom_90_365'] = np.where(
        has_90 & has_365 & (df['trade_365d_avg_price'] > 0),
        (df['trade_90d_avg_price'] - df['trade_365d_avg_price'])
        / df['trade_365d_avg_price'] * 100, 0.0
    ).clip(-20, 20)

    df['accel'] = df['mom_30_90'] - df['mom_90_365']

    # 시군구 내 비교용 면적 그룹 (1자리 반올림): 84.96·84.97·84.99 → 85.0 으로 묶어 통계적 유의성 확보
    df['area_m2_group'] = df['area_m2_key'].round(1)

    # 지역 내 상대 가치 (시군구+면적그룹 기준)
    df['rel_value_pct'] = df.groupby(['sigungu_code', 'area_m2_group'])[
        'trade_last_price'].rank(pct=True) * 100

    # 시군구 중위가 대비
    sgg_med = df.groupby(['sigungu_code', 'area_m2_group'])['trade_last_price'].transform('median')
    df['price_vs_median'] = np.where(sgg_med > 0, df['trade_last_price'] / sgg_med * 100, 100)

    # 0~100 점수
    df['momentum_score'] = ((df['mom_30_90'] + 20) / 40 * 100).clip(0, 100)
    df['accel_score']    = ((df['accel'].clip(-20, 20) + 20) / 40 * 100).clip(0, 100)
    df['value_score']    = (100 - df['rel_value_pct']).clip(0, 100)
    df['infra']          = df['infra_score'].fillna(0)
    max_vol = df['trade_365d_count'].quantile(0.95) or 1
    df['liquidity']      = (df['trade_365d_count'].fillna(0) / max_vol * 100).clip(0, 100)

    return df


def get_regional_weights() -> dict:
    p = BASE / 'config' / 'regional_weights.json'
    if p.exists():
        return json.loads(p.read_text(encoding='utf-8'))['weights']
    return {}


def compute_score(row, weights: dict) -> float:
    region = REGION_MAP.get(str(row.get('sigungu_code', ''))[:2], '서울')
    w = weights.get(region, {
        'price_fit': 0.20, 'momentum_score': 0.10, 'accel_score': 0.10,
        'value_score': 0.35, 'liquidity': 0.05, 'infra': 0.20,
    })
    return (
        row.get('momentum_score', 50) * w.get('momentum_score', 0.10) +
        row.get('accel_score', 50)    * w.get('accel_score', 0.10) +
        row.get('value_score', 50)    * w.get('value_score', 0.35) +
        row.get('liquidity', 50)      * w.get('liquidity', 0.05) +
        row.get('infra', 50)          * w.get('infra', 0.20)
    )


def build_top5(df: pd.DataFrame, weights: dict) -> pd.DataFrame:
    # apt_id 기준 단일화 (평형별 중 가장 최근 거래 평형 우선)
    df_dedup = (
        df.sort_values('trade_365d_count', ascending=False)
          .drop_duplicates('apt_id')
    )

    df_dedup['model_score'] = df_dedup.apply(
        lambda r: compute_score(r, weights), axis=1
    ).round(2)

    rows = []
    for (region, sgg_code, sgg_name), grp in df_dedup.groupby(
        ['region', 'sigungu_code', 'sigungu_name']
    ):
        # 저평가 기준: value_score 상위, infra 최소 기준 없음
        top5 = (
            grp[grp['trade_last_price'].notna()]
            .sort_values('model_score', ascending=False)
            .head(5)
        )
        for rank, (_, row) in enumerate(top5.iterrows(), 1):
            # 저평가 근거
            reasons = []
            if row['value_score'] >= 70:
                reasons.append(f"지역내 저가{row['rel_value_pct']:.0f}%ile")
            if row['price_vs_median'] <= 85:
                reasons.append(f"중위가比{row['price_vs_median']:.0f}%")
            if row.get('infra', 0) >= 60:
                reasons.append(f"역세권{row.get('walk_min','-'):.0f}분")
            if row.get('elem_school_cnt_1km', 0) >= 2:
                reasons.append(f"학군{int(row['elem_school_cnt_1km'])}개교")
            if row.get('redv_nearby', 0) > 0:
                reasons.append(f"정비구역{int(row['redv_nearby'])}개")
            if row['mom_30_90'] < -3:
                reasons.append(f"단기하락{row['mom_30_90']:+.1f}%→반등기대")

            # 365d 수익률 근거 (있을 때만)
            yoy_str = ''
            if (row.get('trade_365d_avg_price') and row.get('trade_last_price') and
                    row['trade_365d_avg_price'] > 0):
                yoy = (row['trade_last_price'] - row['trade_365d_avg_price']) \
                      / row['trade_365d_avg_price'] * 100
                yoy_str = f"{yoy:+.1f}%"

            rows.append({
                'region':            region,
                'sigungu_code':      sgg_code,
                'sigungu_name':      sgg_name,
                'rank':              rank,
                'apt_id':            row['apt_id'],
                'apt_name':          row['apt_name_raw'],
                'area_m2_key':       row['area_m2_key'],
                'pyeong_bucket':     row['pyeong_bucket'],
                'last_price':        int(row['trade_last_price']) if pd.notna(row['trade_last_price']) else None,
                'price_per_pyeong':  round(row['trade_last_per_m2'] * 3.3058, 0) if pd.notna(row.get('trade_last_per_m2')) else None,
                'rel_value_pct':     round(row['rel_value_pct'], 1),
                'price_vs_median':   round(row['price_vs_median'], 1),
                'mom_30_90':         round(row['mom_30_90'], 2),
                'mom_90_365':        round(row['mom_90_365'], 2),
                'yoy_change':        yoy_str,
                'infra_score':       round(row['infra'], 1),
                'nearest_station':   row.get('nearest_station', ''),
                'walk_min':          row.get('walk_min', None),
                'elem_school_cnt':   int(row['elem_school_cnt_1km']) if pd.notna(row.get('elem_school_cnt_1km')) else 0,
                'redv_nearby':       int(row['redv_nearby']) if pd.notna(row.get('redv_nearby')) else 0,
                'value_score':       round(row['value_score'], 1),
                'model_score':       row['model_score'],
                'reason':            ' | '.join(reasons) if reasons else '종합저평가',
                'snapshot_date':     str(row['snapshot_date'].date()),
            })

    return pd.DataFrame(rows)


# ── 실행 ──────────────────────────────────────────────────────
print('=== Step 7: 지역별 저평가 Top 5 ===\n')

df_raw, snap_date = load_data()
df_feat = compute_features(df_raw)
weights = get_regional_weights()
print(f'기준일: {snap_date.date()} | 후보: {len(df_feat):,}건 | 시군구: {df_feat.sigungu_code.nunique()}개\n')

result = build_top5(df_feat, weights)

# ── 출력 ──────────────────────────────────────────────────────
for region in ['서울', '인천', '경기']:
    r_df = result[result['region'] == region]
    if len(r_df) == 0:
        continue
    print(f'\n{"="*72}')
    print(f'  [{region}] 시군구별 저평가 TOP 5')
    print(f'{"="*72}')
    for sgg, sgg_df in r_df.groupby('sigungu_name', sort=False):
        print(f'\n  ■ {sgg}')
        print(f"  {'순':<3} {'단지명':<18} {'m²':<7} {'최근가(만)':<11} "
              f"{'저평가%ile':<10} {'중위比':<8} {'인프라':<7} {'점수':<6} 근거")
        for _, row in sgg_df.iterrows():
            price_str = f"{row['last_price']:,}" if row['last_price'] else '-'
            print(f"  {row['rank']:<3} {str(row['apt_name']):<18} "
                  f"{row['area_m2_key']:<7} {price_str:<11} "
                  f"{row['rel_value_pct']:<10.1f} {row['price_vs_median']:<8.1f} "
                  f"{row['infra_score']:<7.1f} {row['model_score']:<6.1f} "
                  f"{row['reason']}")

# ── 저장 ──────────────────────────────────────────────────────
out_dir = DIRS['exports_daily']
out_dir.mkdir(parents=True, exist_ok=True)
today = datetime.now().strftime('%Y%m%d')

parquet_path = out_dir / f'undervalue_top5_{today}.parquet'
csv_path     = out_dir / f'undervalue_top5_{today}.csv'

result.to_parquet(parquet_path, index=False, compression='zstd')
result.to_csv(csv_path, index=False, encoding='utf-8-sig')

print(f'\n저장 완료:')
print(f'  {parquet_path}')
print(f'  {csv_path}')
print(f'  총 {len(result):,}건 ({result.sigungu_name.nunique()}개 시군구 × 최대 5개)')

# ── 컬럼 설명 ──────────────────────────────────────────────────
COLUMN_DESC = {
    'region':           '광역 지역 (서울 / 인천 / 경기)',
    'sigungu_code':     '시군구 행정코드 5자리 (RTMS LAWD_CD)',
    'sigungu_name':     '시군구명 (예: 강남구, 화성시 동탄구)',
    'rank':             '시군구 내 저평가 순위 (1=가장 저평가)',
    'apt_id':           '단지 고유 ID (SHA256 해시 16자)',
    'apt_name':         '단지명 (실거래가 원문)',
    'area_m2_key':      '전용면적 타입 키 (소수점 2자리 반올림, 예: 59.93, 74.97)',
    'pyeong_bucket':    '평형 구간 표시용 (10P=10평대, 25P=25평대 등)',
    'last_price':       '최근 실거래가 (만원)',
    'price_per_pyeong': '최근 실거래 평당가 (만원/평)',
    'rel_value_pct':    '시군구+평형 내 가격 백분위 (낮을수록 저평가, 0~100)',
    'price_vs_median':  '시군구+평형 중위가 대비 비율 (100=중위가, 80=중위보다 20% 저렴)',
    'mom_30_90':        '단기 모멘텀: 최근30일 평균가 vs 90일 평균가 변화율(%) ->양수=상승',
    'mom_90_365':       '중기 모멘텀: 최근90일 평균가 vs 365일 평균가 변화율(%) ->양수=상승',
    'yoy_change':       '전년 동기 대비 최근가 변화율 (예: +5.2%)',
    'infra_score':      '인프라 종합점수 0~100 (역세권·학군·공원·병원·상권 가중합산)',
    'nearest_station':  '가장 가까운 지하철역명',
    'walk_min':         '가장 가까운 지하철역까지 도보 분',
    'elem_school_cnt':  '반경 1km 내 초등학교 수',
    'redv_nearby':      '인근 정비구역(재개발·재건축 등) 수',
    'value_score':      '저평가 점수 = 100 - rel_value_pct (높을수록 저평가)',
    'model_score':      '최종 종합점수 (지역별 가중치 적용, 0~100)',
    'reason':           '저평가 선정 근거 요약 문자열',
    'snapshot_date':    '데이터 기준일 (unified_daily 스냅샷 날짜)',
}

print('\n' + '='*72)
print('  [컬럼 설명]')
print('='*72)
for col, desc in COLUMN_DESC.items():
    print(f'  {col:<20} {desc}')
