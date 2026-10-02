"""일단위 파이프라인 갱신 오케스트레이터.

실행:
  python run_daily_update.py               # 최근 2개월 수집 + 전체 갱신
  python run_daily_update.py --months 3    # 최근 3개월 재수집
  python run_daily_update.py --skip-fetch  # API 수집 건너뜀 (이미 수집된 경우)
  python run_daily_update.py --skip-score  # 외부데이터 점수 재산출 건너뜀

파이프라인 순서:
  [0] 사전 스냅샷 저장  (신규 거래 비교 기준)
  [1] RTMS 매매 API 수집  (raw XML)
  [2] XML → staged parquet  (run_step2 --skip-map)
  [3] staged → trade_events  (run_step3)
  [4] unified_apt_pyeong_daily 빌드  (run_step4)
  [5] 외부데이터 점수 재산출  (external_data_collector --score)
  [6] 저평가 Top5 갱신  (run_step7)
  [7] 신규 매매 요약 생성  (run_step8)
"""
import sys
import os
import argparse
import subprocess
import time
import json
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, r'c:\projects\realestate_reco')
from common import BASE, DIRS, SIGUNGU_CODES, load_secrets

RTMS_TRADE_BASE = 'https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev'


def target_months(n: int) -> list:
    """최근 n개월 YYYYMM 리스트 (오름차순)."""
    today = datetime.now()
    seen, result = set(), []
    for i in range(n + 2):
        d = (today.replace(day=1) - timedelta(days=i * 28)).replace(day=1)
        ym = d.strftime('%Y%m')
        if ym not in seen:
            seen.add(ym)
            result.append(ym)
        if len(result) == n:
            break
    return sorted(result)


def fetch_rtms(ym_list: list, service_key: str, sleep: float = 0.35) -> int:
    """RTMS API에서 매매 XML 수집. 오류 건수 반환."""
    total = len(ym_list) * len(SIGUNGU_CODES)
    done = errors = 0
    t0 = time.time()

    for ym in ym_list:
        yr, mo = ym[:4], ym[4:]
        out_dir = DIRS['raw_trade'] / yr / mo
        out_dir.mkdir(parents=True, exist_ok=True)

        for code, name in SIGUNGU_CODES.items():
            xml_path  = out_dir / f'{code}_{ym}.xml'
            meta_path = out_dir / f'{code}_{ym}.meta.json'

            last_err = None
            for attempt in range(1, 4):
                try:
                    url = (
                        f'{RTMS_TRADE_BASE}?serviceKey={service_key}'
                        f'&LAWD_CD={code}&DEAL_YMD={ym}&numOfRows=1000&pageNo=1'
                    )
                    resp = requests.get(url, timeout=30)
                    resp.raise_for_status()
                    xml_text = resp.text

                    root = ET.fromstring(xml_text)
                    tc = root.find('.//totalCount')
                    rows = int(tc.text) if tc is not None and tc.text else 0

                    xml_path.write_text(xml_text, encoding='utf-8')
                    meta_path.write_text(
                        json.dumps({
                            'sigungu_code': code, 'sigungu_name': name,
                            'ym': ym, 'rows': rows,
                            'fetched_at': datetime.now().isoformat(),
                        }, ensure_ascii=False, indent=2),
                        encoding='utf-8'
                    )
                    time.sleep(sleep)
                    last_err = None
                    break
                except Exception as e:
                    last_err = e
                    if attempt < 3:
                        time.sleep(2 ** attempt)

            if last_err:
                errors += 1
                print(f'  오류: {ym} {code} {name} -> {last_err}')

            done += 1
            if done % 100 == 0:
                elapsed = time.time() - t0
                eta = elapsed / done * (total - done)
                print(f'  [{done}/{total}] 오류: {errors} | 남은: {eta:.0f}s')

    print(f'  수집 완료: {done}건 처리, 오류: {errors}건')
    return errors


def run_script(path: str, args: list = None, label: str = '') -> float:
    """Python 스크립트를 서브프로세스로 실행. 실패 시 RuntimeError."""
    cmd = [sys.executable, path] + (args or [])
    env = {**os.environ, 'PYTHONIOENCODING': 'utf-8'}
    t0 = time.time()
    result = subprocess.run(cmd, env=env)
    elapsed = time.time() - t0
    if result.returncode != 0:
        raise RuntimeError(f'{Path(path).name} 실패 (exit={result.returncode})')
    tag = label or Path(path).name
    print(f'  [{tag}] 완료 ({elapsed:.1f}s)')
    return elapsed


def save_pre_snapshot():
    """갱신 전 거래 키 스냅샷 저장. step8이 신규 거래 비교에 사용."""
    import pandas as pd
    p = DIRS['master'] / 'trade_events.parquet'
    if not p.exists():
        print('  trade_events 없음 - 스냅샷 생략')
        return
    DIRS['logs'].mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(p, columns=['apt_id', 'deal_date', 'area_m2', 'floor'])
    df.to_parquet(DIRS['logs'] / 'trade_watermark_keys.parquet',
                  index=False, compression='zstd')
    meta = {
        'saved_at': datetime.now().isoformat(),
        'count': len(df),
        'max_deal_date': str(df['deal_date'].max().date()) if len(df) > 0 else None,
    }
    (DIRS['logs'] / 'trade_watermark_meta.json').write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8'
    )
    print(f'  사전 스냅샷 저장: {len(df):,}건 (최신 거래일: {meta["max_deal_date"]})')


# ── 메인 ──────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='일단위 파이프라인 갱신')
    parser.add_argument('--months', type=int, default=2,
                        help='재수집 개월 수 (기본: 2 = 이번달+저번달)')
    parser.add_argument('--skip-fetch', action='store_true',
                        help='RTMS API 수집 건너뜀 (이미 수집된 경우)')
    parser.add_argument('--skip-score', action='store_true',
                        help='외부데이터 점수 재산출 건너뜀')
    args = parser.parse_args()

    run_start = time.time()
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'\n{"="*64}')
    print(f'  일단위 파이프라인 갱신  {ts}')
    print(f'{"="*64}')

    secrets = load_secrets()
    base = str(BASE)

    # [0] 사전 스냅샷 (신규 거래 비교 기준)
    print('\n[0] 사전 거래 스냅샷 저장...')
    save_pre_snapshot()

    # [1] RTMS 수집
    if not args.skip_fetch:
        yms = target_months(args.months)
        print(f'\n[1] RTMS 매매 수집 ({", ".join(yms)})...')
        fetch_rtms(yms, secrets['data_go_kr_service_key'])
    else:
        print('\n[1] RTMS 수집 건너뜀 (--skip-fetch)')

    # [2] XML → staged (apt_id_map은 일단위 skip, 주단위로 따로 재빌드)
    print('\n[2] XML -> staged parquet...')
    run_script(f'{base}/run_step2.py', ['--skip-map'], 'step2')

    # [3] staged → trade_events
    print('\n[3] trade_events 빌드...')
    run_script(f'{base}/run_step3.py', label='step3')

    # [4] unified_apt_pyeong_daily
    print('\n[4] unified_apt_pyeong_daily 빌드...')
    run_script(f'{base}/run_step4_unified_daily.py', label='step4')

    # [5] 외부데이터 점수
    if not args.skip_score:
        print('\n[5] 외부데이터 점수 재산출...')
        run_script(f'{base}/legacy/external_data_collector.py', ['--score'], 'score')
    else:
        print('\n[5] 외부데이터 점수 건너뜀 (--skip-score)')

    # [6] 저평가 Top5
    print('\n[6] 저평가 Top5 갱신...')
    run_script(f'{base}/run_step7_undervalue.py', label='step7')

    # [7] 신규 매매 요약
    print('\n[7] 신규 매매 요약 생성...')
    run_script(f'{base}/run_step8_new_trades.py', label='step8')

    # [8] 데이터 품질 검사 + Slack 알림
    print('\n[8] 데이터 품질 8종 검사...')
    try:
        run_script(f'{base}/run_quality_check.py', label='quality_check')
    except RuntimeError as e:
        # quality_check 실패해도 파이프라인은 계속 (--strict 없이 실행)
        print(f'  ⚠️ 품질 검사 이상 감지: {e}')

    # [9] master/ 백업
    print('\n[9] master/ 백업...')
    try:
        run_script(f'{base}/run_backup_master.py', label='backup')
    except RuntimeError as e:
        print(f'  ⚠️ 백업 실패: {e}')

    total_min = (time.time() - run_start) / 60
    print(f'\n{"="*64}')
    print(f'  갱신 완료  {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  '
          f'(총 {total_min:.1f}분)')
    print(f'{"="*64}\n')
