import sys
sys.path.insert(0, r'c:\projects\realestate_reco')

from common import *
import pandas as pd
import numpy as np
from datetime import datetime


def load_all_staged_trade() -> pd.DataFrame:
    files = list(DIRS['staged_trade'].rglob('*.parquet'))
    if not files:
        raise FileNotFoundError('staged 거래 파일 없음')
    dfs = [pd.read_parquet(p) for p in files]
    df = pd.concat(dfs, ignore_index=True)
    print(f'로드: {len(files):,}개 파일, {len(df):,}건 거래')
    return df


def dedup_trades(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    is_test = (
        df['apt_name_raw'].str.contains('테스트', na=False) |
        df['legal_dong_name'].str.contains('테스트', na=False)
    )
    df = df[~is_test]
    removed_test = before - len(df)
    if removed_test:
        print(f'테스트 데이터 제거: {removed_test:,}건')

    df = df.sort_values(['apt_id', 'deal_date', 'area_m2', 'floor', 'deal_amount'])
    df = df.drop_duplicates(
        subset=['apt_id', 'deal_date', 'area_m2', 'floor'],
        keep='last'
    )
    print(f'dedup: {before - removed_test:,} -> {len(df):,} ({before - removed_test - len(df):,}건 중복 제거)')
    return df


def build_trade_events(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['sigungu_name'] = df['sigungu_code'].map(SIGUNGU_CODES)
    df['price_per_m2'] = df['deal_amount'] / df['area_m2']
    df['price_per_pyeong'] = df['price_per_m2'] * 3.3058
    df['age_at_deal'] = df['deal_date'].dt.year - df['build_year']
    cols = [
        'apt_id', 'area_m2_key', 'pyeong_bucket', 'deal_date',
        'sigungu_code', 'sigungu_name', 'legal_dong_code', 'legal_dong_name',
        'apt_name_raw', 'apt_name_norm',
        'deal_amount', 'area_m2', 'floor', 'build_year', 'age_at_deal',
        'price_per_m2', 'price_per_pyeong',
        'is_canceled', 'cancel_date',
        'road_address',
    ]
    df = df[[c for c in cols if c in df.columns]]
    print(f'trade_events: {len(df):,}건')
    return df


def save_trade_events(df: pd.DataFrame):
    final_path = DIRS['master'] / 'trade_events.parquet'
    tmp_path = DIRS['master'] / 'trade_events.parquet.tmp'
    DIRS['master'].mkdir(parents=True, exist_ok=True)
    df.to_parquet(tmp_path, index=False, compression='zstd')
    tmp_path.replace(final_path)
    print(f'저장: {final_path}')


if __name__ == '__main__':
    df_trade = load_all_staged_trade()
    df_trade = dedup_trades(df_trade)
    df_events = build_trade_events(df_trade)
    save_trade_events(df_events)
    print('\nStep3 완료')
