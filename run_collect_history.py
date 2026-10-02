"""
최근순 역방향 이력 수집.
- 이미 실제 데이터로 수집된 월은 건너뜀 (meta.json의 mock=False 확인)
- 오늘 남은 호출 수만큼 수집 후 중단
- 내일 다시 실행하면 이어서 진행
"""
import sys
sys.path.insert(0, r'C:\projects\realestate_reco')

from common import *
import time
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from dateutil.relativedelta import relativedelta
import json

SECRETS = load_secrets()
SERVICE_KEY = SECRETS['data_go_kr_service_key']
RTMS_BASE = 'https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev'

DAILY_LIMIT  = 10_000
CALLS_TODAY  = 0     # 오늘 이미 사용한 호출 수
REMAINING    = DAILY_LIMIT - CALLS_TODAY
SLEEP        = 0.35  # 초/호출
N_SIGUNGU    = len(SIGUNGU_CODES)


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


def is_real(meta_path) -> bool:
    """meta.json이 존재하고 mock=False이면 실제 수집된 것으로 간주."""
    if not meta_path.exists():
        return False
    try:
        m = json.loads(meta_path.read_text(encoding='utf-8'))
        return not m.get('mock', True)
    except Exception:
        return False


def generate_months_desc(start_ym: str, end_ym: str) -> list:
    """end_ym부터 start_ym까지 역순 월 목록."""
    s = datetime.strptime(start_ym, '%Y%m')
    e = datetime.strptime(end_ym, '%Y%m')
    months = []
    cur = e
    while cur >= s:
        months.append(cur.strftime('%Y%m'))
        cur -= relativedelta(months=1)
    return months


# ── 수집 대상 계산: 미수집(mock) 구간만 ────────────────────
months_all = generate_months_desc('200601', '201507')  # 2015/07 ~ 2006/01 역순
months_todo = [ym for ym in months_all if not is_real(
    DIRS['raw_trade'] / ym[:4] / ym[4:] / f'{list(SIGUNGU_CODES.keys())[0]}_{ym}.meta.json'
)]

months_per_quota = REMAINING // N_SIGUNGU
today_target = months_todo[:months_per_quota]

total_calls = len(today_target) * N_SIGUNGU
print(f'남은 호출 예상: {REMAINING}회')
print(f'시군구 수: {N_SIGUNGU}')
print(f'수집 대상 월: {len(months_todo)}개월')
print(f'수집 범위: {today_target[0] if today_target else "없음"} ~ {today_target[-1] if today_target else "없음"}')
print(f'예상 소요: {total_calls * SLEEP / 60:.0f}분\n')

# ── 수집 실행 ─────────────────────────────────────────────
done = 0
skipped = 0
errors = []
start_t = time.time()

for ym in today_target:
    year, month = ym[:4], ym[4:]
    out_dir = DIRS['raw_trade'] / year / month
    out_dir.mkdir(parents=True, exist_ok=True)

    for code, name in SIGUNGU_CODES.items():
        xml_path  = out_dir / f'{code}_{ym}.xml'
        meta_path = out_dir / f'{code}_{ym}.meta.json'

        if is_real(meta_path):
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
                last_err = None
                time.sleep(SLEEP)
                break
            except Exception as e:
                last_err = e
                time.sleep(2 ** attempt)

        if last_err:
            errors.append({'ym': ym, 'code': code, 'error': str(last_err)})

        done += 1
        if done % N_SIGUNGU == 0:
            elapsed = time.time() - start_t
            pct = done / total_calls * 100
            remaining_sec = elapsed / max(done, 1) * (total_calls - done)
            print(f'  [{ym}] {pct:.0f}% | 건너뜀: {skipped} | 오류: {len(errors)} | 남은: {remaining_sec/60:.0f}분')

elapsed_total = time.time() - start_t
print(f'\n수집 완료: {done}건 처리 / 건너뜀: {skipped} / 오류: {len(errors)} / 소요: {elapsed_total/60:.1f}분')

if errors:
    print('\n오류 목록:')
    for e in errors[:10]:
        print(f"  {e['ym']} {e['code']}: {e['error']}")

tomorrow_start = months_todo[months_per_quota] if len(months_todo) > months_per_quota else None
if tomorrow_start:
    print(f'\n내일 수집 시작 월: {tomorrow_start}')
    print(f'내일 남은 범위: {tomorrow_start} ~ {months_todo[-1]}')
    print(f'내일 필요 호출: {(len(months_todo) - months_per_quota) * N_SIGUNGU:,}회')
