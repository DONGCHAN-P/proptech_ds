"""이상 거래 단지 탐지

가격/거래량/패턴 3종 이상 신호를 탐지해 anomaly_{YYYYMMDD}.parquet/csv 산출.
"""
import sys
sys.path.insert(0, r'c:\projects\realestate_reco')

from common import *
import pandas as pd
import numpy as np
from datetime import datetime

EVENTS_PATH   = DIRS['master'] / 'trade_events.parquet'
UNIFIED_PATH  = DIRS['master'] / 'unified_apt_pyeong_daily.parquet'
APT_MAP_PATH  = DIRS['master'] / 'apt_id_map.parquet'

PRICE_WINDOW_DAYS       = 90
PRICE_Z_THRESHOLD       = -2.0
PRICE_MIN_SAMPLES       = 3
PRICE_MAD_FLOOR_RATIO   = 0.05
VOLUME_WINDOW_MONTHS    = 12
VOLUME_MULTIPLIER       = 2.0
VOLUME_MIN_CURRENT      = 3
PATTERN_WINDOW_DAYS     = 30
PATTERN_PRICE_DROP_PCT  = -3.0
PATTERN_VOLUME_RISE_PCT = 50.0
PATTERN_MIN_SAMPLES     = 3
MIN_DEAL_AMOUNT         = 10000

OUT_COLS = ['apt_id', 'apt_name', 'sigungu', 'pyeong_bucket',
            'anomaly_type', 'score', '중위값', '거래가', 'snapshot_date']


def load_data():
    events = pd.read_parquet(EVENTS_PATH)
    events = events[events['is_canceled'] == False].copy()
    events = events[events['deal_amount'] >= MIN_DEAL_AMOUNT].copy()
    events['deal_date'] = pd.to_datetime(events['deal_date'])
    apt_map = pd.read_parquet(APT_MAP_PATH)
    return events, apt_map


def detect_price_anomaly(events: pd.DataFrame, snap_date: pd.Timestamp) -> pd.DataFrame:
    start = snap_date - pd.Timedelta(days=PRICE_WINDOW_DAYS)
    win = events[(events['deal_date'] >= start) & (events['deal_date'] <= snap_date)].copy()

    grp = win.groupby(['apt_id', 'pyeong_bucket'])
    stats = grp['deal_amount'].agg(median_price='median', window_count='count').reset_index()
    stats = stats[stats['window_count'] >= PRICE_MIN_SAMPLES]
    if len(stats) == 0:
        return pd.DataFrame()

    mad_src = win.merge(stats[['apt_id', 'pyeong_bucket', 'median_price']],
                        on=['apt_id', 'pyeong_bucket'])
    mad_src['abs_dev'] = (mad_src['deal_amount'] - mad_src['median_price']).abs()
    mad = (mad_src.groupby(['apt_id', 'pyeong_bucket'])['abs_dev']
           .median().reset_index().rename(columns={'abs_dev': 'mad'}))
    stats = stats.merge(mad, on=['apt_id', 'pyeong_bucket'])

    latest = (win.sort_values('deal_date')
              .groupby(['apt_id', 'pyeong_bucket']).tail(1)
              [['apt_id', 'pyeong_bucket', 'deal_amount',
                'sigungu_name', 'apt_name_raw']]
              .rename(columns={'deal_amount': 'last_price'}))

    merged = stats.merge(latest, on=['apt_id', 'pyeong_bucket'])
    merged['mad_eff'] = np.maximum(merged['mad'],
                                   merged['median_price'] * PRICE_MAD_FLOOR_RATIO)
    merged = merged[merged['mad_eff'] > 0].copy()
    if len(merged) == 0:
        return pd.DataFrame()
    merged['score'] = (merged['last_price'] - merged['median_price']) / (1.4826 * merged['mad_eff'])
    result = merged[merged['score'] < PRICE_Z_THRESHOLD].copy()
    result['anomaly_type'] = 'price'
    return result


def detect_volume_anomaly(events: pd.DataFrame, snap_date: pd.Timestamp) -> pd.DataFrame:
    ev = events.copy()
    ev['month'] = ev['deal_date'].dt.to_period('M')
    curr_period = pd.Period(snap_date, freq='M')

    monthly = (ev.groupby(['apt_id', 'month']).size()
               .reset_index(name='count')
               .sort_values(['apt_id', 'month']))
    monthly['ma12'] = (monthly.groupby('apt_id')['count']
                       .transform(lambda s: s.shift(1).rolling(VOLUME_WINDOW_MONTHS,
                                                               min_periods=3).mean()))

    curr = monthly[monthly['month'] == curr_period].copy()
    curr = curr[curr['ma12'].notna()
                & (curr['count'] >= VOLUME_MIN_CURRENT)
                & (curr['count'] > VOLUME_MULTIPLIER * curr['ma12'])]
    if len(curr) == 0:
        return pd.DataFrame()
    curr['score'] = curr['count'] / curr['ma12']

    latest = (events.sort_values('deal_date').groupby('apt_id').tail(1)
              [['apt_id', 'pyeong_bucket', 'deal_amount',
                'sigungu_name', 'apt_name_raw']]
              .rename(columns={'deal_amount': 'last_price'}))

    start = snap_date - pd.Timedelta(days=PRICE_WINDOW_DAYS)
    med = (events[events['deal_date'] >= start]
           .groupby('apt_id')['deal_amount'].median()
           .reset_index().rename(columns={'deal_amount': 'median_price'}))

    result = curr.merge(latest, on='apt_id').merge(med, on='apt_id', how='left')
    result['anomaly_type'] = 'volume'
    return result


def detect_pattern_anomaly(events: pd.DataFrame, snap_date: pd.Timestamp) -> pd.DataFrame:
    p1_start = snap_date - pd.Timedelta(days=PATTERN_WINDOW_DAYS)
    p2_start = p1_start - pd.Timedelta(days=PATTERN_WINDOW_DAYS)

    p1 = events[(events['deal_date'] >= p1_start) & (events['deal_date'] <= snap_date)]
    p2 = events[(events['deal_date'] >= p2_start) & (events['deal_date'] < p1_start)]

    s1 = p1.groupby('apt_id').agg(p1_avg=('deal_amount', 'mean'),
                                  p1_cnt=('deal_amount', 'count')).reset_index()
    s2 = p2.groupby('apt_id').agg(p2_avg=('deal_amount', 'mean'),
                                  p2_cnt=('deal_amount', 'count')).reset_index()

    merged = s1.merge(s2, on='apt_id')
    merged = merged[(merged['p2_avg'] > 0)
                    & (merged['p1_cnt'] >= PATTERN_MIN_SAMPLES)
                    & (merged['p2_cnt'] >= PATTERN_MIN_SAMPLES)].copy()
    if len(merged) == 0:
        return pd.DataFrame()
    merged['price_chg_pct']  = (merged['p1_avg'] - merged['p2_avg']) / merged['p2_avg'] * 100
    merged['volume_chg_pct'] = (merged['p1_cnt'] - merged['p2_cnt']) / merged['p2_cnt'] * 100

    flag = merged[(merged['price_chg_pct'] < PATTERN_PRICE_DROP_PCT) &
                  (merged['volume_chg_pct'] > PATTERN_VOLUME_RISE_PCT)].copy()
    if len(flag) == 0:
        return pd.DataFrame()
    flag['score'] = flag['volume_chg_pct'] / 100 - flag['price_chg_pct'] / 100

    latest = (events.sort_values('deal_date').groupby('apt_id').tail(1)
              [['apt_id', 'pyeong_bucket', 'deal_amount',
                'sigungu_name', 'apt_name_raw']]
              .rename(columns={'deal_amount': 'last_price'}))

    med = (events[events['deal_date'] >= p1_start]
           .groupby('apt_id')['deal_amount'].median()
           .reset_index().rename(columns={'deal_amount': 'median_price'}))

    result = flag.merge(latest, on='apt_id').merge(med, on='apt_id', how='left')
    result['anomaly_type'] = 'pattern'
    return result


def normalize(df: pd.DataFrame, snap_date: pd.Timestamp) -> pd.DataFrame:
    if len(df) == 0:
        return pd.DataFrame(columns=OUT_COLS)
    out = pd.DataFrame({
        'apt_id':        df['apt_id'].values,
        'apt_name':      df.get('apt_name_raw', pd.Series([''] * len(df))).values,
        'sigungu':       df.get('sigungu_name', pd.Series([''] * len(df))).values,
        'pyeong_bucket': df.get('pyeong_bucket', pd.Series([''] * len(df))).values,
        'anomaly_type':  df['anomaly_type'].values,
        'score':         df['score'].round(3).values,
        '중위값':         df.get('median_price', pd.Series([np.nan] * len(df))).values,
        '거래가':         df.get('last_price', pd.Series([np.nan] * len(df))).values,
        'snapshot_date': snap_date.date(),
    })
    return out


def main():
    print('=== 이상 거래 단지 탐지 ===')
    events, _ = load_data()
    snap_date = events['deal_date'].max()
    print(f'기준일: {snap_date.date()} | 거래: {len(events):,}건')

    price_df   = detect_price_anomaly(events, snap_date)
    volume_df  = detect_volume_anomaly(events, snap_date)
    pattern_df = detect_pattern_anomaly(events, snap_date)

    result = pd.concat([
        normalize(price_df, snap_date),
        normalize(volume_df, snap_date),
        normalize(pattern_df, snap_date),
    ], ignore_index=True)
    result = result.drop_duplicates(subset=['apt_id', 'pyeong_bucket', 'anomaly_type'])

    DIRS['exports_daily'].mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime('%Y%m%d')
    parquet_path = DIRS['exports_daily'] / f'anomaly_{today}.parquet'
    csv_path     = DIRS['exports_daily'] / f'anomaly_{today}.csv'
    result.to_parquet(parquet_path, index=False, compression='zstd')
    result.to_csv(csv_path, index=False, encoding='utf-8-sig')

    n_p, n_v, n_t = len(price_df), len(volume_df), len(pattern_df)
    print(f'\n탐지 건수: 가격={n_p:,} | 거래량={n_v:,} | 패턴={n_t:,} | 총={len(result):,}')

    if len(result) > 0:
        order = {'price': 0, 'volume': 1, 'pattern': 2}
        rk = result.assign(
            _t=result['anomaly_type'].map(order),
            _s=result['score'].abs(),
        ).sort_values(['_t', '_s'], ascending=[True, False]).head(3)
        print('\nTop 3:')
        for _, r in rk.iterrows():
            print(f"  [{r['anomaly_type']:<7}] {str(r['apt_name'])[:18]:<18} "
                  f"{str(r['sigungu']):<10} {str(r['pyeong_bucket']):<5} "
                  f"score={r['score']:+.2f}")

    print(f'\n저장:')
    print(f'  {parquet_path}')
    print(f'  {csv_path}')


if __name__ == '__main__':
    main()
