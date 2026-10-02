"""Step 5: 아파트 추천 엔진 (지역별 최적화 모델)

사용법:
  python run_step5_recommend.py --budget 60000 80000 --region 강남구 서초구 --pyeong 25P 30P --top 20
  python run_step5_recommend.py --budget 30000 50000 --region 분당구 --priority school
"""
import sys
sys.path.insert(0, r'c:\projects\realestate_reco')

from common import *
import pandas as pd
import numpy as np
import sqlite3
import json
import argparse
from datetime import datetime

# DB_PATH 는 common.py 가 결정한다 (legacy/ 이동 대응)
REGION_MAP = {'11': '서울', '28': '인천', '41': '경기'}

# ── 지역별 최적 가중치 로드 ────────────────────────────────────
_weights_path = BASE / 'config' / 'regional_weights.json'
if _weights_path.exists():
    _wdata = json.loads(_weights_path.read_text(encoding='utf-8'))
    REGIONAL_WEIGHTS = _wdata['weights']
    print(f'지역별 가중치 로드 ({_wdata["backtest_period"]})')
else:
    REGIONAL_WEIGHTS = {}
    print('⚠ regional_weights.json 없음 → 기본 가중치 사용 (run_step6_model.py 실행 권장)')

DEFAULT_WEIGHTS = {
    'price_fit': 0.20, 'momentum_score': 0.10, 'accel_score': 0.10,
    'value_score': 0.35, 'liquidity': 0.05, 'infra': 0.20,
}


def get_weights(region_code: str) -> dict:
    region = REGION_MAP.get(str(region_code)[:2], '')
    return REGIONAL_WEIGHTS.get(region, DEFAULT_WEIGHTS)


# ── 데이터 로드 ───────────────────────────────────────────────

def load_data():
    ud = pd.read_parquet(DIRS['master'] / 'unified_apt_pyeong_daily.parquet')
    am = pd.read_parquet(DIRS['master'] / 'apt_id_map.parquet')

    latest = ud['snapshot_date'].max()
    snapshot = ud[ud['snapshot_date'] == latest].copy()

    con = sqlite3.connect(DB_PATH)
    ext = pd.read_sql("""
        SELECT apt_seq as apt_id,
               nearest_station, walk_min, nearest_line,
               elem_school_cnt_1km, nearest_school_dist,
               park_dist, redv_nearby, redv_status_best,
               commerce_score, hospital_cnt, infra_score
        FROM apt_external
    """, con)
    con.close()

    df = snapshot.merge(ext, on='apt_id', how='left')
    df = df.merge(
        am[['apt_id', 'lat', 'lng', 'legal_dong_name', 'sigungu_code']]
        .drop_duplicates('apt_id'),
        on='apt_id', how='left',
        suffixes=('', '_map')
    )
    if 'sigungu_code_map' in df.columns:
        df['sigungu_code'] = df['sigungu_code'].fillna(df['sigungu_code_map'])
        df.drop(columns=['sigungu_code_map'], inplace=True)

    df['region'] = df['sigungu_code'].str[:2].map(REGION_MAP)
    return df, latest


# ── 피처 계산 ─────────────────────────────────────────────────

def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # 단기 모멘텀 30d vs 90d
    has_30 = df['trade_30d_avg_price'].notna() & (df['trade_30d_count'] >= 2)
    has_90 = df['trade_90d_avg_price'].notna() & (df['trade_90d_count'] >= 2)
    has_365 = df['trade_365d_avg_price'].notna() & (df['trade_365d_count'] >= 2)

    df['mom_30_90'] = np.where(
        has_30 & has_90 & (df['trade_90d_avg_price'] > 0),
        (df['trade_30d_avg_price'] - df['trade_90d_avg_price'])
        / df['trade_90d_avg_price'] * 100, 0.0
    ).clip(-20, 20)

    # 중기 모멘텀 90d vs 365d
    df['mom_90_365'] = np.where(
        has_90 & has_365 & (df['trade_365d_avg_price'] > 0),
        (df['trade_90d_avg_price'] - df['trade_365d_avg_price'])
        / df['trade_365d_avg_price'] * 100, 0.0
    ).clip(-20, 20)

    # 가속도 (단기가 중기보다 빠를수록 양수)
    df['accel'] = df['mom_30_90'] - df['mom_90_365']

    # 시군구 내 비교용 면적 그룹 (1자리 반올림): step7과 동일 기준
    df['area_m2_group'] = df['area_m2_key'].round(1)

    # 지역내 상대 가치 — 백분위 낮을수록 저평가 → value_score 높게
    df['rel_value_pct'] = df.groupby(['sigungu_code', 'area_m2_group'])[
        'trade_last_price'].rank(pct=True) * 100

    # 0~100 정규화 점수들
    df['momentum_score'] = ((df['mom_30_90'] + 20) / 40 * 100).clip(0, 100)
    df['accel_score']    = ((df['accel'].clip(-20, 20) + 20) / 40 * 100).clip(0, 100)
    # value_score: 저평가(낮은 백분위)를 선호 → 반전
    df['value_score']    = (100 - df['rel_value_pct']).clip(0, 100)
    df['infra']          = df['infra_score'].fillna(0)

    max_vol = df['trade_365d_count'].quantile(0.95) or 1
    df['liquidity']      = (df['trade_365d_count'].fillna(0) / max_vol * 100).clip(0, 100)

    return df


# ── 추천 점수 계산 ────────────────────────────────────────────

def score_recommendations(df: pd.DataFrame, budget_lo: float, budget_hi: float,
                           regions: list, pyeongs: list, priority: str) -> pd.DataFrame:
    result = df.copy()

    if regions:
        mask = result['sigungu_name'].apply(lambda x: any(r in str(x) for r in regions))
        result = result[mask]

    if pyeongs:
        result = result[result['pyeong_bucket'].isin(pyeongs)]

    if budget_lo > 0:
        result = result[
            result['trade_last_price'].between(budget_lo * 0.8, budget_hi * 1.2)
        ]

    if len(result) == 0:
        return result

    # 가격 적합도
    budget_mid = (budget_lo + budget_hi) / 2 if budget_lo > 0 else 0
    if budget_mid > 0:
        result['price_fit'] = (
            100 - ((result['trade_last_price'] - budget_mid).abs() / budget_mid * 100)
        ).clip(0, 100)
    else:
        result['price_fit'] = 50.0

    # priority 오버라이드 가중치
    priority_override = {
        'school': {'infra': 0.55, 'value_score': 0.20, 'price_fit': 0.15,
                   'momentum_score': 0.05, 'accel_score': 0.03, 'liquidity': 0.02},
        'price':  {'price_fit': 0.45, 'value_score': 0.25, 'momentum_score': 0.10,
                   'accel_score': 0.05, 'liquidity': 0.10, 'infra': 0.05},
        'trend':  {'momentum_score': 0.30, 'accel_score': 0.20, 'infra': 0.25,
                   'price_fit': 0.15, 'value_score': 0.05, 'liquidity': 0.05},
        'infra':  {'infra': 0.60, 'value_score': 0.15, 'price_fit': 0.15,
                   'momentum_score': 0.05, 'accel_score': 0.03, 'liquidity': 0.02},
    }

    def row_score(row):
        w = (priority_override[priority] if priority in priority_override
             else get_weights(row.get('sigungu_code', '')))
        return (
            row.get('price_fit', 50)       * w.get('price_fit', 0.20) +
            row.get('momentum_score', 50)  * w.get('momentum_score', 0.10) +
            row.get('accel_score', 50)     * w.get('accel_score', 0.10) +
            row.get('value_score', 50)     * w.get('value_score', 0.15) +
            row.get('liquidity', 50)       * w.get('liquidity', 0.05) +
            row.get('infra', 50)           * w.get('infra', 0.40)
        )

    result['total_score'] = result.apply(row_score, axis=1).round(1)
    return result.sort_values('total_score', ascending=False)


# ── 출력 ──────────────────────────────────────────────────────

def format_output(df: pd.DataFrame, top_n: int, snapshot_date):
    top = df.drop_duplicates('apt_id').head(top_n)

    print(f"\n{'='*78}")
    print(f"  추천 결과 (기준일: {snapshot_date.date()}, 상위 {len(top)}건)")
    print(f"{'='*78}")
    print(f"{'순':<3} {'단지명':<18} {'지역':<10} {'형':<5} {'최근가(만)':<11} "
          f"{'인프라':<7} {'저평가':<7} {'총점':<6} {'이유'}")
    print('-' * 78)

    for rank, (_, row) in enumerate(top.iterrows(), 1):
        reasons = []
        if row.get('infra_score', 0) >= 70:
            reasons.append(f"역세권{row.get('walk_min','-'):.0f}분")
        if row.get('elem_school_cnt_1km', 0) >= 3:
            reasons.append(f"학군{int(row['elem_school_cnt_1km'])}개교")
        if row.get('mom_30_90', 0) > 3:
            reasons.append(f"단기↑{row['mom_30_90']:+.1f}%")
        elif row.get('mom_30_90', 0) < -3:
            reasons.append(f"단기↓{row['mom_30_90']:+.1f}%")
        if row.get('value_score', 0) >= 75:
            reasons.append('저평가')
        if row.get('redv_nearby', 0) > 0:
            reasons.append(f"정비{int(row['redv_nearby'])}개")
        if not reasons:
            reasons.append('균형')

        price_str = f"{int(row['trade_last_price']):,}" if pd.notna(row.get('trade_last_price')) else '-'
        print(f"{rank:<3} {str(row['apt_name_raw']):<18} "
              f"{str(row['sigungu_name']):<10} {row['pyeong_bucket']:<5} "
              f"{price_str:<11} {row.get('infra_score',0):<7.1f} "
              f"{row.get('value_score',0):<7.1f} {row['total_score']:<6.1f} "
              f"{', '.join(reasons)}")

    print(f"{'='*78}")

    # 지역별 요약
    summary = (
        df.drop_duplicates('apt_id')
        .groupby(['region', 'sigungu_name'])
        .agg(단지수=('apt_id','count'),
             평균점수=('total_score','mean'),
             중위가격=('trade_last_price','median'),
             평균저평가=('value_score','mean'))
        .sort_values('평균점수', ascending=False)
        .head(10)
    )
    print('\n[지역별 요약]')
    print(summary.round(1).to_string())

    # 인사이트 출력
    print('\n[모델 인사이트]')
    if REGIONAL_WEIGHTS:
        for region, w in REGIONAL_WEIGHTS.items():
            print(f"  {region}: 저평가 {w['value_score']:.0%} | "
                  f"인프라 {w['infra']:.0%} | "
                  f"모멘텀 {w['momentum_score']+w['accel_score']:.0%} | "
                  f"유동성 {w['liquidity']:.0%}")
    print()
    return top


def save_results(df: pd.DataFrame, regions, priority):
    out_dir = DIRS['exports_daily']
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    region_str = '_'.join(regions) if regions else 'all'
    fname = f"recommend_{region_str}_{priority}_{ts}.parquet"
    df.to_parquet(out_dir / fname, index=False, compression='zstd')
    print(f'결과 저장: {out_dir / fname}')


# ── 실행 ──────────────────────────────────────────────────────
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='아파트 추천 엔진 (지역별 최적화)')
    parser.add_argument('--budget', type=float, nargs=2, default=[0, 999999],
                        metavar=('MIN', 'MAX'), help='예산 범위 만원 (예: 60000 80000)')
    parser.add_argument('--region', nargs='+', default=[],
                        help='지역 필터 (예: 강남구 서초구 분당구)')
    parser.add_argument('--pyeong', nargs='+', default=[],
                        help='평형 필터 (예: 25P 30P)')
    parser.add_argument('--priority', default='balanced',
                        choices=['balanced', 'school', 'price', 'infra', 'trend'],
                        help='우선순위 (기본: balanced=지역최적화)')
    parser.add_argument('--top', type=int, default=20, help='상위 N건')
    args = parser.parse_args()

    print('\n데이터 로드 중...')
    df_raw, snap_date = load_data()
    df_feat = compute_features(df_raw)
    print(f'전체 후보: {len(df_feat):,}건 (단지×평형 조합)')

    result = score_recommendations(
        df_feat,
        budget_lo=args.budget[0], budget_hi=args.budget[1],
        regions=args.region, pyeongs=args.pyeong,
        priority=args.priority
    )

    if len(result) == 0:
        print('조건에 맞는 단지가 없습니다. 필터를 완화해보세요.')
    else:
        print(f'필터 후 후보: {len(result):,}건')
        top = format_output(result, args.top, snap_date)
        save_results(top, args.region, args.priority)
