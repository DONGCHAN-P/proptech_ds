"""누락 시군구 재수집 스크립트

대상:
  - 부천시 원미구(41192), 소사구(41194), 오정구(41196): 기존 41190 코드로 0건 수집됨 → 새 코드로 전체 재수집
  - 화성시(41590): 전체 기간 재시도 (API 임시 오류 가능성)

실행:
  python run_recollect_missing.py
  python run_recollect_missing.py --skip-hwaseong  # 화성시 제외
"""
import sys
sys.path.insert(0, r'c:\projects\realestate_reco')

from common import *
import time
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from dateutil.relativedelta import relativedelta
import json
import argparse

SECRETS = load_secrets()
SERVICE_KEY = SECRETS['data_go_kr_service_key']
RTMS_BASE = 'https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev'
SLEEP = 0.35

# 재수집 대상
TARGET_CODES = {
    '41192': '부천시 원미구',
    '41194': '부천시 소사구',
    '41196': '부천시 오정구',
    '41591': '화성시 만세구',
    '41593': '화성시 효행구',
    '41595': '화성시 병점구',
    '41597': '화성시 동탄구',
}

START_YM = '200601'
END_YM   = '202604'


def fetch(sigungu_code: str, ym: str, timeout: int = 30) -> str:
    url = (f'{RTMS_BASE}?serviceKey={SERVICE_KEY}'
           f'&LAWD_CD={sigungu_code}&DEAL_YMD={ym}&numOfRows=1000&pageNo=1')
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def parse_count(xml_text: str) -> int:
    try:
        root = ET.fromstring(xml_text)
        tc = root.find('.//totalCount')
        return int(tc.text) if tc is not None and tc.text else 0
    except Exception:
        return -1


def generate_months(start_ym: str, end_ym: str) -> list:
    s = datetime.strptime(start_ym, '%Y%m')
    e = datetime.strptime(end_ym, '%Y%m')
    months = []
    cur = s
    while cur <= e:
        months.append(cur.strftime('%Y%m'))
        cur += relativedelta(months=1)
    return months


def already_collected(meta_path) -> bool:
    if not meta_path.exists():
        return False
    try:
        m = json.loads(meta_path.read_text(encoding='utf-8'))
        return not m.get('mock', True) and m.get('rows', 0) > 0
    except Exception:
        return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--skip-hwaseong', action='store_true', help='화성시(41590) 제외')
    parser.add_argument('--force', action='store_true', help='이미 수집된 것도 재수집')
    args = parser.parse_args()

    codes = dict(TARGET_CODES)
    if args.skip_hwaseong:
        codes.pop('41590', None)
        print('화성시 제외 모드')

    months = generate_months(START_YM, END_YM)
    print(f'수집 대상: {list(codes.values())}')
    print(f'기간: {START_YM} ~ {END_YM} ({len(months)}개월)')

    total_plan = len(codes) * len(months)
    print(f'최대 API 호출: {total_plan:,}회 (이미 수집된 건 제외)\n')

    done = 0
    skipped = 0
    errors = []
    nonzero = 0
    start_t = time.time()

    for code, name in codes.items():
        print(f'\n=== {name}({code}) 수집 시작 ===')
        code_nonzero = 0

        for ym in months:
            year, month = ym[:4], ym[4:]
            out_dir = DIRS['raw_trade'] / year / month
            out_dir.mkdir(parents=True, exist_ok=True)

            xml_path  = out_dir / f'{code}_{ym}.xml'
            meta_path = out_dir / f'{code}_{ym}.meta.json'

            if not args.force and already_collected(meta_path):
                skipped += 1
                done += 1
                continue

            last_err = None
            for attempt in range(1, 4):
                try:
                    xml_text = fetch(code, ym)
                    rows = parse_count(xml_text)
                    xml_path.write_text(xml_text, encoding='utf-8')
                    meta_path.write_text(json.dumps({
                        'sigungu_code': code, 'sigungu_name': name,
                        'ym': ym, 'rows': rows,
                        'fetched_at': datetime.now().isoformat(),
                        'mock': False,
                    }, ensure_ascii=False, indent=2), encoding='utf-8')
                    if rows > 0:
                        code_nonzero += 1
                        nonzero += 1
                    last_err = None
                    time.sleep(SLEEP)
                    break
                except Exception as e:
                    last_err = e
                    time.sleep(2 ** attempt)

            if last_err:
                errors.append({'ym': ym, 'code': code, 'error': str(last_err)})

            done += 1

        elapsed = time.time() - start_t
        print(f'  {name}: {code_nonzero}/{len(months)}개월 데이터 확인 | 소요: {elapsed/60:.1f}분')

    elapsed_total = time.time() - start_t
    print(f'\n=== 완료 ===')
    print(f'처리: {done}건 | 건너뜀: {skipped} | 오류: {len(errors)} | 데이터 있음: {nonzero}개월')
    print(f'소요: {elapsed_total/60:.1f}분')

    if errors:
        print(f'\n오류 {len(errors)}건:')
        for e in errors[:10]:
            print(f"  {e['ym']} {e['code']}: {e['error']}")

    print('\n다음 단계:')
    print('  python run_step2_stage.py   # staged parquet 재생성')
    print('  python run_step3.py          # trade_events 재빌드')
    print('  python run_step4_unified_daily.py')
    print('  python run_step7_undervalue.py')
