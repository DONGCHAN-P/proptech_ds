import sys
import hashlib
sys.path.insert(0, r'c:\projects\realestate_reco')

from common import *
import pandas as pd
import numpy as np
from datetime import datetime

from collector.first_seen import attach_first_seen


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


def attach_identity(df: pd.DataFrame) -> pd.DataFrame:
    """거래 고유 해시키 부착 (T5a).

    apt_id 를 쓰지 않고 원시 필드로만 만든다. apt_id 정의가 바뀌어도
    해시가 살아남아야 first_seen 원장과 발행 원장이 끊기지 않는다.
    """
    df = df.copy()
    area = df['area_m2'].astype(float).map(lambda v: '' if v != v else f'{v:.2f}')
    amt = df['deal_amount'].astype(float).map(lambda v: '' if v != v else f'{v:.0f}')
    flo = df['floor'].map(lambda v: '' if v is None or v != v else str(int(v)))
    raw = (df['legal_dong_code'].fillna('').astype(str)
           + '|' + df['apt_name_norm'].fillna('').astype(str)
           + '|' + pd.to_datetime(df['deal_date']).dt.strftime('%Y-%m-%d')
           + '|' + amt + '|' + area + '|' + flo)
    df['deal_hash'] = raw.map(
        lambda k: hashlib.sha256(k.encode('utf-8')).hexdigest()[:16]
    )
    dup = len(df) - df['deal_hash'].nunique()
    if dup:
        # 1차 dedup(apt_id, 계약일, 면적, 층)이 놓치는 두 유형이 여기서 걸린다.
        #   A) 같은 거래인데 전용면적 표기가 0.001㎡ 다른 경우 (84.9800 vs 84.9810)
        #   B) 같은 단지가 도로명주소 두 개로 등록돼 apt_id 가 갈린 경우
        # 둘 다 같은 날 같은 층 같은 금액이라 동일 신고로 보는 게 맞다.
        # 남길 행은 거래가 많은 쪽 apt_id — 단지의 주 등록으로 모아준다.
        order = df['apt_id'].map(df['apt_id'].value_counts())
        df = (df.assign(_rank=order)
                .sort_values(['deal_hash', '_rank'], ascending=[True, False])
                .drop_duplicates('deal_hash', keep='first')
                .drop(columns='_rank'))
        print(f'deal_hash 중복 제거: {dup:,}건 (면적 정밀도 + 주소 변형)')
    print(f'deal_hash 부착: {df["deal_hash"].nunique():,}개 고유')
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
        'deal_hash', 'first_seen_date', 'first_seen_is_estimate',
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
    df_trade = attach_identity(df_trade)
    df_trade, fs_stats = attach_first_seen(
        df_trade, DIRS['master'], DIRS['raw_trade'])
    print(f"first_seen 원장: {fs_stats['ledger_rows']:,}건 "
          f"(신규 {fs_stats['new_hashes']:,}, "
          f"{'최초 역산' if fs_stats['seeded'] else '증분'})")
    df_events = build_trade_events(df_trade)
    save_trade_events(df_events)
    print('\nStep3 완료')
