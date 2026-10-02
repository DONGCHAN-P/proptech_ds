"""Step 4: unified_apt_pyeong_daily.parquet 빌드

각 (apt_id, pyeong_bucket, snapshot_date) 행에 30d/90d/365d 거래 통계를 부착.
"""
import sys
sys.path.insert(0, r'c:\projects\realestate_reco')

from common import *
import pandas as pd
import numpy as np
from datetime import datetime

SNAPSHOT_DAYS = 90  # 최근 90일 스냅샷


def load_events() -> pd.DataFrame:
    p = DIRS['master'] / 'trade_events.parquet'
    df = pd.read_parquet(p)
    df = df[df['is_canceled'] == False].copy()
    df['deal_date'] = pd.to_datetime(df['deal_date'])
    print(f'거래 이벤트: {len(df):,}건 (해제 제외)')
    return df


def build_snapshot_grid(df_events: pd.DataFrame, days: int) -> pd.DataFrame:
    end = df_events['deal_date'].max()
    start = end - pd.Timedelta(days=days - 1)
    dates = pd.date_range(start, end, freq='D')

    keys = (
        df_events[['apt_id', 'area_m2_key', 'pyeong_bucket', 'sigungu_code', 'sigungu_name',
                   'legal_dong_code', 'legal_dong_name', 'apt_name_raw']]
        .drop_duplicates()
    )
    print(f'단지×타입: {len(keys):,} | 날짜: {len(dates)}일 → {len(keys)*len(dates):,}행 예상')

    chunks = []
    for _, kgroup in keys.groupby('sigungu_code'):
        tmp = kgroup.merge(pd.DataFrame({'snapshot_date': dates}), how='cross')
        chunks.append(tmp)
    grid = pd.concat(chunks, ignore_index=True)
    print(f'그리드 생성: {len(grid):,}행')
    return grid


def attach_last_trade(grid: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    last = (
        events.sort_values('deal_date')
        .groupby(['apt_id', 'area_m2_key'])
        .agg(
            trade_last_date=('deal_date', 'last'),
            trade_last_price=('deal_amount', 'last'),
            trade_last_per_m2=('price_per_m2', 'last'),
        )
        .reset_index()
    )
    return grid.merge(last, on=['apt_id', 'area_m2_key'], how='left')


def attach_window_stats(grid: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    """30d/90d/365d 윈도우 통계를 벡터화 방식으로 부착."""
    ev = events[['apt_id', 'area_m2_key', 'deal_date', 'deal_amount', 'price_per_m2']].copy()

    for window in [30, 90, 365]:
        print(f'  window={window}d 계산 중...')

        count_col = f'trade_{window}d_count'
        avg_price_col = f'trade_{window}d_avg_price'
        avg_m2_col = f'trade_{window}d_avg_per_m2'

        result_chunks = []
        for sgg, g in grid.groupby('sigungu_code'):
            apt_ids = g['apt_id'].unique()
            ev_sgg = ev[ev['apt_id'].isin(apt_ids)]
            if len(ev_sgg) == 0:
                g[count_col] = 0
                g[avg_price_col] = np.nan
                g[avg_m2_col] = np.nan
                result_chunks.append(g)
                continue

            merged = g[['apt_id', 'area_m2_key', 'snapshot_date']].merge(
                ev_sgg, on=['apt_id', 'area_m2_key'], how='left'
            )
            lo = merged['snapshot_date'] - pd.Timedelta(days=window)
            in_window = (merged['deal_date'] >= lo) & (merged['deal_date'] <= merged['snapshot_date'])
            merged_w = merged[in_window]

            agg = (
                merged_w.groupby(['apt_id', 'area_m2_key', 'snapshot_date'])
                .agg(
                    **{count_col: ('deal_amount', 'count'),
                       avg_price_col: ('deal_amount', 'mean'),
                       avg_m2_col: ('price_per_m2', 'mean')}
                )
                .reset_index()
            )
            g = g.merge(agg, on=['apt_id', 'area_m2_key', 'snapshot_date'], how='left')
            g[count_col] = g[count_col].fillna(0).astype(int)
            result_chunks.append(g)

        grid = pd.concat(result_chunks, ignore_index=True)

    return grid


def save_unified(df: pd.DataFrame):
    final = DIRS['master'] / 'unified_apt_pyeong_daily.parquet'
    tmp = DIRS['master'] / 'unified_apt_pyeong_daily.parquet.tmp'
    df.to_parquet(tmp, index=False, compression='zstd')
    tmp.replace(final)
    print(f'저장: {final} ({len(df):,}행)')


if __name__ == '__main__':
    print('=== Step 4: unified_apt_pyeong_daily 빌드 ===')
    df_events = load_events()

    print(f'\n그리드 생성 중 (최근 {SNAPSHOT_DAYS}일)...')
    grid = build_snapshot_grid(df_events, SNAPSHOT_DAYS)

    print('\n최근 거래 부착...')
    grid = attach_last_trade(grid, df_events)

    print('\n윈도우 통계 부착...')
    grid = attach_window_stats(grid, df_events)

    save_unified(grid)
    print('\nStep 4 완료')
