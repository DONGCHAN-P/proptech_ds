"""Step 6: 가격 피처 확장 + 지역별 모델 최적화 + 백테스트 검증

산출물:
  config/regional_weights.json  — 지역별 최적 가중치
  logs/backtest_YYYYMMDD.json   — 백테스트 검증 리포트

Patch v1.1 (2026-05-03):
  - 미세 누설(forward leak) 제거: past 필터 `<=` → `<`
  - 윈도우 겹침 제거: 분기(QS, ~90일 간격, 16시점) → 반기(2QS=180일, 8시점)로 sparse.
    FUTURE_DAYS=90이라 인접 윈도우 사이에 90일 gap 보장 → 같은 거래 중복 사용 방지.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import *
import pandas as pd
import numpy as np
import sqlite3
import json
from datetime import datetime
from scipy.stats import spearmanr

# DB_PATH 는 common.py 가 결정한다 (legacy/ 이동 대응)
BACKTEST_START = '2022-01-01'   # 백테스트 시작 (데이터 안정성 확보 이후)
BACKTEST_END   = '2025-12-31'
# v1.1: '2QS' = 6개월 시작(1/1, 7/1). FUTURE_DAYS=90과 합치면 윈도우 간 90일 gap.
PRED_FREQ      = '2QS'          # 반기별 예측 시점 (윈도우 비겹침)
FUTURE_DAYS    = 90             # 실제 수익률 측정 기간

REGION_MAP = {'11': '서울', '28': '인천', '41': '경기'}

# ─────────────────────────────────────────────────────────────
# 1. 데이터 로드
# ─────────────────────────────────────────────────────────────

def load_events() -> pd.DataFrame:
    df = pd.read_parquet(DIRS['master'] / 'trade_events.parquet')
    df = df[~df['is_canceled']].copy()
    df['deal_date'] = pd.to_datetime(df['deal_date'])
    df['region'] = df['sigungu_code'].str[:2].map(REGION_MAP)
    print(f'거래 이벤트: {len(df):,}건 ({df.deal_date.min().date()} ~ {df.deal_date.max().date()})')
    return df


def load_infra() -> pd.DataFrame:
    con = sqlite3.connect(DB_PATH)
    ext = pd.read_sql("""
        SELECT apt_seq as apt_id, walk_min, elem_school_cnt_1km,
               redv_nearby, commerce_score, infra_score
        FROM apt_external
    """, con)
    con.close()
    return ext


# ─────────────────────────────────────────────────────────────
# 2. 피처 엔지니어링 (단일 시점)
# ─────────────────────────────────────────────────────────────

def compute_features_at(df_events: pd.DataFrame, pred_date: pd.Timestamp,
                         region_stats: dict) -> pd.DataFrame:
    """pred_date 시점의 (apt_id, area_m2_key) 피처를 계산."""
    cutoff_30  = pred_date - pd.Timedelta(days=30)
    cutoff_90  = pred_date - pd.Timedelta(days=90)
    cutoff_365 = pred_date - pd.Timedelta(days=365)

    # v1.1: forward leak 방지. pred_date 당일 거래는 피처에 포함하지 않음.
    past = df_events[df_events['deal_date'] < pred_date].copy()
    if len(past) == 0:
        return pd.DataFrame()

    key = ['apt_id', 'area_m2_key', 'sigungu_code', 'region']

    def rolling_agg(cutoff, suffix):
        g = (past[past['deal_date'] > cutoff]
             .groupby(['apt_id', 'area_m2_key'])
             .agg(
                 **{f'cnt{suffix}':   ('deal_amount', 'count'),
                    f'avg{suffix}':   ('deal_amount', 'mean'),
                    f'std{suffix}':   ('deal_amount', 'std')}
             ).reset_index())
        return g

    agg30  = rolling_agg(cutoff_30,  '_30')
    agg90  = rolling_agg(cutoff_90,  '_90')
    agg365 = rolling_agg(cutoff_365, '_365')

    # 최근 거래가 (마지막 실거래)
    last = (past.sort_values('deal_date')
                .groupby(['apt_id', 'area_m2_key'])
                .last()[['deal_amount', 'sigungu_code', 'region', 'sigungu_name']]
                .rename(columns={'deal_amount': 'last_price'})
                .reset_index())

    df = (last
          .merge(agg30,  on=['apt_id','area_m2_key'], how='left')
          .merge(agg90,  on=['apt_id','area_m2_key'], how='left')
          .merge(agg365, on=['apt_id','area_m2_key'], how='left'))

    # ── 모멘텀 피처 ──────────────────────────────────────────
    # 단기 모멘텀: 30d vs 90d
    mask_30_90 = df['cnt_30'] >= 2
    df['mom_30_90'] = np.where(
        mask_30_90 & df['avg_90'].notna() & (df['avg_90'] > 0),
        (df['avg_30'] - df['avg_90']) / df['avg_90'] * 100, np.nan
    )

    # 중기 모멘텀: 90d vs 365d
    mask_90_365 = df['cnt_90'] >= 2
    df['mom_90_365'] = np.where(
        mask_90_365 & df['avg_365'].notna() & (df['avg_365'] > 0),
        (df['avg_90'] - df['avg_365']) / df['avg_365'] * 100, np.nan
    )

    # 가속도: 단기가 중기보다 빠르게 상승 중인가
    df['accel'] = df['mom_30_90'].fillna(0) - df['mom_90_365'].fillna(0)

    # 변동성: 최근 90일 CoV (낮을수록 안정)
    df['volatility'] = np.where(
        df['avg_90'] > 0,
        df['std_90'].fillna(0) / df['avg_90'] * 100, 0
    )

    # 거래 활성도 (365d 거래 수)
    df['trade_freq'] = df['cnt_365'].fillna(0)

    # ── 지역 내 상대 가치 ────────────────────────────────────
    # area_m2_group(1자리 반올림)으로 묶어 통계적 유의성 확보 (step7과 동일 기준)
    df['area_m2_group'] = df['area_m2_key'].round(1)
    df['rel_value_pct'] = df.groupby(['sigungu_code', 'area_m2_group'])[
        'last_price'].rank(pct=True) * 100

    # 시군구 중위가 대비 비율 (100 = 중위, 80 = 중위보다 20% 저렴)
    sgg_median = df.groupby(['sigungu_code', 'area_m2_group'])['last_price'].transform('median')
    df['price_vs_median'] = np.where(
        sgg_median > 0, df['last_price'] / sgg_median * 100, 100
    )

    df['pred_date'] = pred_date
    return df


# ─────────────────────────────────────────────────────────────
# 3. 백테스트: 실제 수익률 계산
# ─────────────────────────────────────────────────────────────

def compute_actual_returns(df_events: pd.DataFrame,
                           features: pd.DataFrame) -> pd.DataFrame:
    """각 (apt_id, pyeong, pred_date)에 대해 pred_date → pred_date+90d 실제 수익률."""
    results = []
    events_sorted = df_events.sort_values('deal_date')

    for pred_date, feat_group in features.groupby('pred_date'):
        future_end = pred_date + pd.Timedelta(days=FUTURE_DAYS)
        future = events_sorted[
            (events_sorted['deal_date'] > pred_date) &
            (events_sorted['deal_date'] <= future_end)
        ]
        if len(future) == 0:
            continue

        future_avg = (future.groupby(['apt_id', 'area_m2_key'])['deal_amount']
                      .mean().reset_index().rename(columns={'deal_amount': 'future_price'}))

        merged = feat_group.merge(future_avg, on=['apt_id', 'area_m2_key'], how='inner')
        merged['actual_return'] = (
            (merged['future_price'] - merged['last_price']) / merged['last_price'] * 100
        )
        results.append(merged)

    if not results:
        return pd.DataFrame()
    return pd.concat(results, ignore_index=True)


# ─────────────────────────────────────────────────────────────
# 4. 지역별 피처 중요도 (Spearman 상관)
# ─────────────────────────────────────────────────────────────

FEATURE_COLS = ['mom_30_90', 'mom_90_365', 'accel', 'volatility',
                'trade_freq', 'rel_value_pct', 'price_vs_median']

def compute_regional_importance(bt: pd.DataFrame) -> dict:
    """지역별 피처-실제수익률 Spearman 상관계수 계산."""
    importance = {}
    for region, grp in bt.groupby('region'):
        if len(grp) < 30:
            continue
        grp = grp.dropna(subset=['actual_return'])
        corrs = {}
        for feat in FEATURE_COLS:
            col = grp[feat].fillna(grp[feat].median())
            if col.std() == 0:
                corrs[feat] = 0.0
                continue
            r, p = spearmanr(col, grp['actual_return'])
            corrs[feat] = float(r) if not np.isnan(r) else 0.0
        importance[region] = corrs
    return importance


# ─────────────────────────────────────────────────────────────
# 5. 가중치 최적화 (상관계수 기반)
# ─────────────────────────────────────────────────────────────

def optimize_weights(importance: dict) -> dict:
    """피처 중요도를 추천 모델 가중치로 변환."""
    weights_out = {}
    for region, corrs in importance.items():
        # 양의 상관이 있는 피처만 사용 (음의 상관은 역방향으로)
        mom_signal    = max(0, corrs.get('mom_30_90', 0))
        accel_signal  = max(0, corrs.get('accel', 0))
        medtrend      = max(0, corrs.get('mom_90_365', 0))
        freq_signal   = max(0, corrs.get('trade_freq', 0))
        # rel_value: 저평가(낮은 백분위)가 수익률 높으면 음의 상관 → 반전
        val_corr      = corrs.get('rel_value_pct', 0)
        val_signal    = max(0, -val_corr)  # 음의 상관 = 저평가 선호

        raw = {
            'momentum': mom_signal + accel_signal * 0.5 + medtrend * 0.3,
            'value':    val_signal,
            'liquidity': freq_signal,
        }
        total = sum(raw.values()) or 1.0

        # 모멘텀·가치·유동성 비율 + 인프라는 고정 35%
        infra_w = 0.35
        remain  = 1 - infra_w
        weights_out[region] = {
            'price_fit':      round(0.20, 3),
            'momentum_score': round(remain * raw['momentum'] / total * 0.6, 3),
            'accel_score':    round(remain * raw['momentum'] / total * 0.4, 3),
            'value_score':    round(remain * raw['value']    / total, 3),
            'liquidity':      round(remain * raw['liquidity']/ total, 3),
            'infra':          infra_w,
        }
        # 합산 보정
        s = sum(v for k, v in weights_out[region].items() if k != 'infra')
        for k in ['price_fit', 'momentum_score', 'accel_score', 'value_score', 'liquidity']:
            weights_out[region][k] = round(weights_out[region][k] / s * (1 - infra_w), 3)

    return weights_out


# ─────────────────────────────────────────────────────────────
# 6. 백테스트 검증 지표
# ─────────────────────────────────────────────────────────────

def compute_infra_weights(row, weights: dict) -> float:
    region = str(row.get('region', ''))
    w = weights.get(region, weights.get('서울'))
    score = (
        row.get('price_fit', 50)       * w['price_fit'] +
        row.get('mom_score', 50)       * w['momentum_score'] +
        row.get('accel_score_n', 50)   * w['accel_score'] +
        row.get('val_score', 50)       * w['value_score'] +
        row.get('liq_score', 50)       * w['liquidity'] +
        row.get('infra_score', 50)     * w['infra']
    )
    return score


def validate_model(bt: pd.DataFrame, weights: dict, ext: pd.DataFrame) -> dict:
    """최적화된 가중치로 모델 점수 계산 후 실제 수익률과 비교."""
    bt = bt.merge(ext[['apt_id', 'infra_score']], on='apt_id', how='left')

    # 피처 → 0~100 정규화 점수
    bt['mom_score']     = ((bt['mom_30_90'].fillna(0).clip(-20,20) + 20) / 40 * 100)
    bt['accel_score_n'] = ((bt['accel'].fillna(0).clip(-20,20)    + 20) / 40 * 100)
    bt['val_score']     = (100 - bt['rel_value_pct'].fillna(50))  # 저평가일수록 고점
    bt['liq_score']     = bt.groupby('region')['trade_freq'].transform(
                              lambda x: (x / (x.quantile(0.95) or 1)).clip(0,1) * 100)
    bt['price_fit']     = 50.0  # 백테스트에서 예산 없으므로 중립
    bt['infra_score']   = bt['infra_score'].fillna(50)

    bt['model_score'] = bt.apply(lambda r: compute_infra_weights(r, weights), axis=1)

    report = {}
    for region, grp in bt.groupby('region'):
        if len(grp) < 30:
            continue
        grp = grp.dropna(subset=['actual_return', 'model_score'])
        r, p = spearmanr(grp['model_score'], grp['actual_return'])

        # Top 20% 예측 vs 실제 상위 20% 일치율
        score_q80   = grp['model_score'].quantile(0.80)
        return_q80  = grp['actual_return'].quantile(0.80)
        top_pred    = grp['model_score']   >= score_q80
        top_actual  = grp['actual_return'] >= return_q80
        hit_rate    = (top_pred & top_actual).sum() / top_pred.sum() if top_pred.sum() > 0 else 0

        avg_return_top    = grp.loc[top_pred, 'actual_return'].mean()
        avg_return_bottom = grp.loc[~top_pred, 'actual_return'].mean()

        report[region] = {
            'n_samples':       int(len(grp)),
            'spearman_corr':   round(float(r), 4),
            'p_value':         round(float(p), 4),
            'hit_rate_top20':  round(float(hit_rate), 4),
            'avg_return_top20_pred':    round(float(avg_return_top), 2),
            'avg_return_bottom80_pred': round(float(avg_return_bottom), 2),
            'return_lift':     round(float(avg_return_top - avg_return_bottom), 2),
        }
    return report


# ─────────────────────────────────────────────────────────────
# 7. 실행
# ─────────────────────────────────────────────────────────────

print('=== Step 6: 지역별 모델 최적화 + 백테스트 ===\n')

df_events = load_events()
ext       = load_infra()

# 백테스트 예측 시점 (분기별)
pred_dates = pd.date_range(BACKTEST_START, BACKTEST_END, freq=PRED_FREQ)
print(f'백테스트 예측 시점: {len(pred_dates)}개 분기 ({pred_dates[0].date()} ~ {pred_dates[-1].date()})\n')

print('피처 계산 중...')
feat_chunks = []
for i, pd_ in enumerate(pred_dates):
    print(f'  {pd_.date()} ({i+1}/{len(pred_dates)})', end='\r')
    feat = compute_features_at(df_events, pd_, {})
    if len(feat) > 0:
        feat_chunks.append(feat)
print()

features_all = pd.concat(feat_chunks, ignore_index=True)
print(f'피처 생성 완료: {len(features_all):,}행 ({features_all.apt_id.nunique():,}개 단지)\n')

print('실제 수익률 계산 중...')
backtest = compute_actual_returns(df_events, features_all)
print(f'백테스트 데이터: {len(backtest):,}건\n')

if len(backtest) == 0:
    print('백테스트 데이터 부족. BACKTEST_END를 더 이전으로 조정하세요.')
    sys.exit(1)

print('지역별 피처 중요도 분석...')
importance = compute_regional_importance(backtest)
print()
print('[피처-수익률 Spearman 상관]')
print(f"{'피처':<20}", end='')
for region in importance:
    print(f"  {region:>6}", end='')
print()
for feat in FEATURE_COLS:
    print(f'{feat:<20}', end='')
    for region, corrs in importance.items():
        val = corrs.get(feat, 0)
        mark = '▲' if val > 0.05 else ('▼' if val < -0.05 else ' ')
        print(f"  {val:>+5.3f}{mark}", end='')
    print()

print('\n가중치 최적화 중...')
weights = optimize_weights(importance)

print('\n[지역별 최적 가중치]')
all_regions = list(weights.keys())
header = f"{'항목':<16}" + ''.join(f"  {r:>6}" for r in all_regions)
print(header)
for key in ['price_fit', 'momentum_score', 'accel_score', 'value_score', 'liquidity', 'infra']:
    row_str = f'{key:<16}'
    for region in all_regions:
        row_str += f"  {weights[region].get(key, 0):>6.3f}"
    print(row_str)

print('\n모델 검증 중...')
validation = validate_model(backtest, weights, ext)

print('\n[백테스트 검증 결과]')
print(f"{'지역':<8} {'샘플수':>8} {'Spearman':>10} {'p값':>8} "
      f"{'Hit율(20%)':>12} {'상위평균수익':>12} {'하위평균수익':>12} {'리프트':>8}")
print('-' * 80)
for region, v in validation.items():
    sig = '**' if v['p_value'] < 0.01 else ('*' if v['p_value'] < 0.05 else '')
    print(f"{region:<8} {v['n_samples']:>8,} {v['spearman_corr']:>+10.4f}{sig} "
          f"{v['p_value']:>8.4f} {v['hit_rate_top20']:>12.1%} "
          f"{v['avg_return_top20_pred']:>+12.2f}% "
          f"{v['avg_return_bottom80_pred']:>+12.2f}% "
          f"{v['return_lift']:>+8.2f}%")

# 저장
output = {
    'generated_at': datetime.now().isoformat(),
    'backtest_period': f'{BACKTEST_START} ~ {BACKTEST_END}',
    'future_days': FUTURE_DAYS,
    'weights': weights,
    'importance': {r: {k: round(v, 4) for k,v in c.items()}
                   for r, c in importance.items()},
    'validation': validation,
}

cfg_path = BASE / 'config' / 'regional_weights.json'
cfg_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'\n가중치 저장: {cfg_path}')

log_path = DIRS['logs'] / f"backtest_{datetime.now().strftime('%Y%m%d')}.json"
log_path.parent.mkdir(parents=True, exist_ok=True)
log_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'검증 로그: {log_path}')
print('\nStep 6 완료')
