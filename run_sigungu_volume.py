"""지역구별 거래량 시계열 추출

trade_events.parquet 에서 시군구 × 월 거래량 + 이동평균 + YoY 산출.
산출: exports/daily/sigungu_volume_{YYYYMMDD}.csv + .parquet + .png (matplotlib 있을 때)
"""
import sys
sys.path.insert(0, r'c:\projects\realestate_reco')

from common import *
import pandas as pd
import numpy as np
from datetime import datetime

EVENTS_PATH      = DIRS['master'] / 'trade_events.parquet'
MIN_DEAL_AMOUNT  = 10000
LOOKBACK_MONTHS  = 240
REGION_MAP       = {'11': '서울', '28': '인천', '41': '경기'}


def load_events() -> pd.DataFrame:
    ev = pd.read_parquet(EVENTS_PATH)
    ev = ev[ev['is_canceled'] == False].copy()
    ev = ev[ev['deal_amount'] >= MIN_DEAL_AMOUNT].copy()
    ev['deal_date'] = pd.to_datetime(ev['deal_date'])
    return ev


def aggregate(ev: pd.DataFrame) -> pd.DataFrame:
    ev = ev.copy()
    ev['month'] = ev['deal_date'].dt.to_period('M').dt.to_timestamp()

    end = ev['month'].max()
    start = end - pd.DateOffset(months=LOOKBACK_MONTHS - 1)
    ev = ev[ev['month'] >= start]

    m = (ev.groupby(['sigungu_code', 'sigungu_name', 'month'])
           .agg(trade_count=('deal_amount', 'count'),
                avg_price=('deal_amount', 'mean'),
                median_price=('deal_amount', 'median'))
           .reset_index()
           .sort_values(['sigungu_code', 'month']))

    m['region'] = m['sigungu_code'].astype(str).str[:2].map(REGION_MAP)
    m['ma3']    = m.groupby('sigungu_code')['trade_count'].transform(
                      lambda s: s.rolling(3, min_periods=1).mean()).round(1)
    m['ma12']   = m.groupby('sigungu_code')['trade_count'].transform(
                      lambda s: s.rolling(12, min_periods=3).mean()).round(1)
    m['yoy_pct'] = m.groupby('sigungu_code')['trade_count'].transform(
                       lambda s: (s / s.shift(12) - 1) * 100).round(1)
    m['mom_pct'] = m.groupby('sigungu_code')['trade_count'].transform(
                       lambda s: (s / s.shift(1) - 1) * 100).round(1)
    m['avg_price']    = m['avg_price'].round(0).astype('Int64')
    m['median_price'] = m['median_price'].round(0).astype('Int64')
    m['month'] = m['month'].dt.strftime('%Y-%m')
    return m


def save_outputs(df: pd.DataFrame, ymd: str):
    out_dir = DIRS['exports_daily']
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_p = out_dir / f'sigungu_volume_{ymd}.csv'
    pq_p  = out_dir / f'sigungu_volume_{ymd}.parquet'
    df.to_csv(csv_p, index=False, encoding='utf-8-sig')
    df.to_parquet(pq_p, index=False, compression='zstd')
    print(f'저장:\n  {csv_p}\n  {pq_p}')

    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        try:
            from matplotlib import font_manager
            for f in ['Malgun Gothic', 'AppleGothic', 'NanumGothic']:
                if any(f in fn.name for fn in font_manager.fontManager.ttflist):
                    plt.rcParams['font.family'] = f; break
            plt.rcParams['axes.unicode_minus'] = False
        except Exception:
            pass

        png_p = out_dir / f'sigungu_volume_{ymd}.png'
        fig, axes = plt.subplots(2, 1, figsize=(14, 9))

        # 광역 3개
        reg = df.groupby(['region', 'month'])['trade_count'].sum().reset_index()
        for r in ['서울', '인천', '경기']:
            sub = reg[reg['region'] == r]
            axes[0].plot(sub['month'], sub['trade_count'], label=r, linewidth=2)
        axes[0].set_title('광역별 월 거래량')
        axes[0].set_ylabel('거래건수')
        axes[0].legend(); axes[0].grid(alpha=0.3)
        for label in axes[0].get_xticklabels():
            label.set_rotation(45); label.set_ha('right')

        # 시군구 Top 10
        last_m = df['month'].max()
        top10 = (df[df['month'] == last_m].nlargest(10, 'trade_count')['sigungu_name'].tolist())
        for s in top10:
            sub = df[df['sigungu_name'] == s]
            axes[1].plot(sub['month'], sub['trade_count'], label=s, linewidth=1.5, alpha=0.8)
        axes[1].set_title(f'시군구 Top 10 ({last_m} 기준)')
        axes[1].set_ylabel('거래건수')
        axes[1].legend(loc='upper left', fontsize=8, ncol=2)
        axes[1].grid(alpha=0.3)
        for label in axes[1].get_xticklabels():
            label.set_rotation(45); label.set_ha('right')

        # x축 라벨 간격 조정
        for ax in axes:
            n = len(ax.get_xticklabels())
            step = max(1, n // 12)
            for i, lbl in enumerate(ax.get_xticklabels()):
                lbl.set_visible(i % step == 0)

        plt.tight_layout()
        plt.savefig(png_p, dpi=120, bbox_inches='tight')
        plt.close()
        print(f'  {png_p}')
    except ImportError:
        print('  (matplotlib 미설치 - PNG 생략)')


def print_summary(df: pd.DataFrame):
    last_m = df['month'].max()
    snap = df[df['month'] == last_m]
    print(f'\n=== 최근월 ({last_m}) 거래량 Top 10 ===')
    top = snap.sort_values('trade_count', ascending=False).head(10)
    for _, r in top.iterrows():
        yoy = f"{r['yoy_pct']:+.1f}%" if pd.notna(r['yoy_pct']) else '-'
        mom = f"{r['mom_pct']:+.1f}%" if pd.notna(r['mom_pct']) else '-'
        print(f"  {str(r['sigungu_name']):<12} {r['trade_count']:>5,}건  YoY {yoy:>8}  MoM {mom:>8}")

    print(f'\n=== 광역별 ({last_m}) ===')
    reg = snap.groupby('region')['trade_count'].sum()
    for r, c in reg.items():
        print(f'  {r}: {c:,}건')


def main():
    print('=== 지역구별 거래량 시계열 ===')
    ev = load_events()
    print(f'거래: {len(ev):,}건 (필터 후) | 기간: {ev["deal_date"].min().date()} ~ {ev["deal_date"].max().date()}')

    df = aggregate(ev)
    print(f'집계: 시군구 {df["sigungu_code"].nunique()}개 × 월 {df["month"].nunique()}개 = {len(df):,}행')

    ymd = datetime.now().strftime('%Y%m%d')
    save_outputs(df, ymd)
    print_summary(df)


if __name__ == '__main__':
    main()
