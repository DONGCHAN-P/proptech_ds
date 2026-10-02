"""Step 8: 신규 매매 거래 요약 리포트 생성.

직전 실행 워터마크(logs/trade_watermark_keys.parquet)와 비교해
새로 추가된 거래를 집계하고 3종 파일로 저장:

  exports/daily/new_trades_YYYYMMDD.parquet      신규 거래 전건
  exports/daily/new_trades_sgg_YYYYMMDD.csv      시군구별 집계
  exports/daily/new_trades_notable_YYYYMMDD.csv  직전 90일 평균 대비 +-15% 이상 거래

워터마크는 이 스크립트 실행 완료 시 현재 trade_events 기준으로 갱신됨.
run_daily_update.py에서 호출 시: [0]단계에서 사전 스냅샷을 저장하고 이 스크립트가 후미에 실행됨.
단독 실행 시: 이전 run 이후 추가된 거래를 기준으로 동작함.
"""
import sys
sys.path.insert(0, r'c:\projects\realestate_reco')

from common import *
from metrics.filters import apply_filters
import pandas as pd
import numpy as np
from datetime import datetime
import json

WATERMARK_KEYS = DIRS['logs'] / 'trade_watermark_keys.parquet'
WATERMARK_META = DIRS['logs'] / 'trade_watermark_meta.json'
# 워터마크 키는 deal_hash 하나다 (T5a).
# 예전엔 (apt_id, 계약일, 면적, 층) 조합이었는데, apt_id 정의가 바뀌면
# (2026-05 umd_cd, 2026-10 괄호보존) 전 건이 "신규"로 뒤집힌다. 실제로 T6
# 마이그레이션 직후 신규 거래가 103만 건으로 집계됐다. deal_hash 는 API
# 원본값으로만 만들어 그런 변경에 흔들리지 않는다.
KEY_COLS = ['deal_hash']


def load_new_deals(all_events: pd.DataFrame) -> tuple:
    """워터마크와 비교해 신규 거래 추출.

    Returns: (new_deals_df, prev_meta_dict)
    """
    if not WATERMARK_KEYS.exists():
        print('  워터마크 없음 - 전체 데이터를 신규로 처리')
        return all_events.copy(), {}

    prev_keys = pd.read_parquet(WATERMARK_KEYS)
    prev_meta = json.loads(WATERMARK_META.read_text(encoding='utf-8'))         if WATERMARK_META.exists() else {}

    if 'deal_hash' not in prev_keys.columns:
        print('  워터마크가 구버전(apt_id 기반) - 전체를 신규로 처리하고 갱신')
        return all_events.copy(), prev_meta

    seen = set(prev_keys['deal_hash'])
    is_new = ~all_events['deal_hash'].isin(seen)
    new_deals = all_events[is_new].copy()
    return new_deals, prev_meta


def build_sgg_summary(new_deals: pd.DataFrame) -> pd.DataFrame:
    """시군구별 신규 거래 집계."""
    if len(new_deals) == 0:
        return pd.DataFrame()

    grp = new_deals.groupby(['sigungu_code', 'sigungu_name'])
    s = grp.agg(
        new_count      = ('deal_amount', 'count'),
        avg_price      = ('deal_amount', 'mean'),
        min_price      = ('deal_amount', 'min'),
        max_price      = ('deal_amount', 'max'),
        avg_per_m2     = ('price_per_m2', 'mean'),
        latest_deal    = ('deal_date', 'max'),
        earliest_deal  = ('deal_date', 'min'),
    ).reset_index()
    s['avg_price']  = s['avg_price'].round(0).astype(int)
    s['min_price']  = s['min_price'].astype(int)
    s['max_price']  = s['max_price'].astype(int)
    s['avg_per_m2'] = s['avg_per_m2'].round(1)
    return s.sort_values('new_count', ascending=False).reset_index(drop=True)


def find_notable(new_deals: pd.DataFrame, all_events: pd.DataFrame,
                 threshold_pct: float = 15.0) -> pd.DataFrame:
    """신규 거래 중 직전 90일 평균 대비 threshold_pct% 이상 괴리된 거래."""
    if len(new_deals) == 0:
        return pd.DataFrame()

    # 신규 거래 최소 날짜 기준 90일 이전 데이터로 참조 평균 산출
    cutoff = new_deals['deal_date'].min() - pd.Timedelta(days=90)
    ref = (
        all_events[all_events['deal_date'] < cutoff]
        .groupby(['apt_id', 'area_m2_key'])['deal_amount']
        .agg(ref_count='count', ref_avg='mean')
        .reset_index()
    )
    # 참조 거래가 2건 이상인 경우만 사용 (통계적 유의성)
    ref = ref[ref['ref_count'] >= 2]

    merged = new_deals.merge(ref, on=['apt_id', 'area_m2_key'], how='inner')
    merged['deviation_pct'] = (
        (merged['deal_amount'] - merged['ref_avg']) / merged['ref_avg'] * 100
    ).round(1)

    notable = merged[merged['deviation_pct'].abs() >= threshold_pct].copy()
    notable = notable.sort_values('deviation_pct', ascending=False)

    out_cols = [
        'sigungu_name', 'legal_dong_name', 'apt_name_raw',
        'area_m2', 'floor', 'deal_date', 'deal_amount',
        'ref_avg', 'ref_count', 'deviation_pct',
    ]
    return notable[[c for c in out_cols if c in notable.columns]].head(100)


def print_summary(new_deals: pd.DataFrame, sgg: pd.DataFrame,
                  notable: pd.DataFrame, prev_meta: dict, total: int):
    prev_count   = prev_meta.get('count', 0)
    prev_date    = prev_meta.get('max_deal_date', '-')
    prev_saved   = prev_meta.get('saved_at', '-')[:16]

    print(f'전체 거래: {total:,}건')
    print(f'이전 스냅샷: {prev_count:,}건  (저장: {prev_saved}, 최신 거래일: {prev_date})')
    print(f'신규 거래: {len(new_deals):,}건\n')

    if len(sgg) == 0:
        print('  신규 거래 없음')
        return

    # 시군구별 상위 20
    print(f'{"시군구":<14} {"건수":>5} {"평균가(만)":>10} {"최저가":>8} {"최고가":>8} '
          f'{"평당(만)":>8} {"최신거래일"}')
    print('-' * 72)
    for _, r in sgg.head(20).iterrows():
        print(
            f'{str(r["sigungu_name"]):<14} {r["new_count"]:>5,} '
            f'{r["avg_price"]:>10,} {r["min_price"]:>8,} {r["max_price"]:>8,} '
            f'{r["avg_per_m2"]:>8,.1f} '
            f'{str(r["latest_deal"].date()) if pd.notna(r["latest_deal"]) else "-"}'
        )

    if len(notable) == 0:
        return

    print(f'\n주목 거래 (직전 90일 평균 대비 +-15% 이상, 상위 20건):')
    print(f'{"단지명":<22} {"법정동":<10} {"m2":>6} {"층":>4} '
          f'{"거래일":<12} {"거래가":>9} {"기준가":>9} {"괴리율":>8}')
    print('-' * 86)
    for _, r in notable.head(20).iterrows():
        print(
            f'{str(r["apt_name_raw"]):<22} '
            f'{str(r.get("legal_dong_name", "")):<10} '
            f'{r["area_m2"]:>6.1f} '
            f'{str(int(r["floor"])) if pd.notna(r.get("floor")) else "-":>4} '
            f'{str(r["deal_date"].date()):<12} '
            f'{int(r["deal_amount"]):>9,} '
            f'{int(r["ref_avg"]):>9,} '
            f'{r["deviation_pct"]:>+8.1f}%'
        )


# ── 실행 ──────────────────────────────────────────────────────────────────
print('=== Step 8: 신규 매매 거래 요약 ===\n')

today = datetime.now().strftime('%Y%m%d')
DIRS['logs'].mkdir(parents=True, exist_ok=True)
DIRS['exports_daily'].mkdir(parents=True, exist_ok=True)

# 전체 trade_events 로드
all_events = pd.read_parquet(DIRS['master'] / 'trade_events.parquet')
all_events['deal_date'] = pd.to_datetime(all_events['deal_date'])

# 해제·이상치 공통 필터 (T8). 이게 없던 동안 해제된 거래가 특이거래 Top100 에
# 올라가 있었다 — 발행됐다면 취소된 거래를 "신고가"로 소개할 뻔했다.
_before = len(all_events)
all_events = apply_filters(all_events)
if _before != len(all_events):
    print(f'공통 필터: {_before:,} -> {len(all_events):,}건 '
          f'({_before - len(all_events):,}건 제외 — 해제·가격이상치)')

# 신규 거래 추출
new_deals, prev_meta = load_new_deals(all_events)

# 집계
sgg_summary = build_sgg_summary(new_deals)
notable     = find_notable(new_deals, all_events)

# 출력
print_summary(new_deals, sgg_summary, notable, prev_meta, len(all_events))

# ── 저장 ─────────────────────────────────────────────────────────────────
saved = []

if len(new_deals) > 0:
    p = DIRS['exports_daily'] / f'new_trades_{today}.parquet'
    new_deals.to_parquet(p, index=False, compression='zstd')
    saved.append(str(p))

if len(sgg_summary) > 0:
    p = DIRS['exports_daily'] / f'new_trades_sgg_{today}.csv'
    sgg_summary.to_csv(p, index=False, encoding='utf-8-sig')
    saved.append(str(p))

if len(notable) > 0:
    p = DIRS['exports_daily'] / f'new_trades_notable_{today}.csv'
    notable.to_csv(p, index=False, encoding='utf-8-sig')
    saved.append(str(p))

if saved:
    print(f'\n저장 완료:')
    for s in saved:
        print(f'  {s}')

# ── 워터마크 갱신 ─────────────────────────────────────────────────────────
new_wm = all_events[KEY_COLS].copy()
new_wm.to_parquet(WATERMARK_KEYS, index=False, compression='zstd')
new_meta = {
    'saved_at':      datetime.now().isoformat(),
    'count':         len(all_events),
    'max_deal_date': str(all_events['deal_date'].max().date()),
}
WATERMARK_META.write_text(
    json.dumps(new_meta, ensure_ascii=False, indent=2), encoding='utf-8'
)
print(f'\n워터마크 갱신: {len(all_events):,}건, 최신 거래일: {new_meta["max_deal_date"]}')
