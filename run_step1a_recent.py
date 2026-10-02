"""최근 3개월 실제 API 수집 (검증용). skip_existing=False로 mock 파일 덮어씀."""
import sys
sys.path.insert(0, r'C:\projects\realestate_reco')

from common import *
import time
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import json
import pandas as pd

SECRETS = load_secrets()
SERVICE_KEY = SECRETS['data_go_kr_service_key']
MOCK_MODE = SECRETS.get('MOCK_MODE', False)
print(f'MOCK_MODE = {MOCK_MODE}')
print(f'시군구 수 = {len(SIGUNGU_CODES)}')

RTMS_TRADE_BASE = 'https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev'


def fetch_rtms_trade(sigungu_code: str, ym: str, timeout: int = 30) -> str:
    # 인코딩 키를 URL에 직접 삽입해 이중 인코딩 방지
    url = (
        f'{RTMS_TRADE_BASE}?serviceKey={SERVICE_KEY}'
        f'&LAWD_CD={sigungu_code}&DEAL_YMD={ym}&numOfRows=1000&pageNo=1'
    )
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def parse_row_count(xml_text: str) -> int:
    try:
        root = ET.fromstring(xml_text)
        tc = root.find('.//totalCount')
        return int(tc.text) if tc is not None and tc.text else 0
    except Exception:
        return -1


def collect_months(ym_list: list, sleep_per_call: float = 0.35, retries: int = 3):
    total = len(ym_list) * len(SIGUNGU_CODES)
    done = 0
    errors = []
    start = time.time()

    for ym in ym_list:
        year, month = ym[:4], ym[4:]
        out_dir = DIRS['raw_trade'] / year / month
        out_dir.mkdir(parents=True, exist_ok=True)

        for code, name in SIGUNGU_CODES.items():
            xml_path  = out_dir / f'{code}_{ym}.xml'
            meta_path = out_dir / f'{code}_{ym}.meta.json'

            last_err = None
            for attempt in range(1, retries + 1):
                try:
                    xml_text = fetch_rtms_trade(code, ym)
                    rows = parse_row_count(xml_text)
                    xml_path.write_text(xml_text, encoding='utf-8')
                    meta_path.write_text(
                        json.dumps({
                            'sigungu_code': code, 'sigungu_name': name,
                            'ym': ym, 'rows': rows,
                            'fetched_at': datetime.now().isoformat(),
                            'mock': False,
                        }, ensure_ascii=False, indent=2),
                        encoding='utf-8'
                    )
                    last_err = None
                    time.sleep(sleep_per_call)
                    break
                except Exception as e:
                    last_err = e
                    time.sleep(2 ** attempt)

            if last_err:
                errors.append({'ym': ym, 'code': code, 'name': name, 'error': str(last_err)})

            done += 1
            if done % 66 == 0:
                elapsed = time.time() - start
                remaining = elapsed / done * (total - done)
                print(f'  [{done}/{total}] {ym} 완료 | 오류: {len(errors)} | 남은: {remaining:.0f}초')

    print(f'\n수집 완료: {done}건 처리, 오류 {len(errors)}건')
    if errors:
        for e in errors:
            print(f"  오류: {e['ym']} {e['code']} {e['name']} -> {e['error']}")
    return errors


# 최근 3개월 수집
target_yms = ['202602', '202603', '202604']
print(f'\n수집 대상: {target_yms}')
print(f'총 {len(target_yms) * len(SIGUNGU_CODES)}회 API 호출 예정')
print(f'예상 소요: 약 {len(target_yms) * len(SIGUNGU_CODES) * 0.35:.0f}초\n')

errors = collect_months(target_yms)

# 수집 결과 샘플 확인
print('\n=== 수집 결과 샘플 (강남구 2026/04) ===')
sample = DIRS['raw_trade'] / '2026' / '04' / '11680_202604.xml'
if sample.exists():
    root = __import__('xml.etree.ElementTree', fromlist=['ElementTree']).parse(str(sample)).getroot()
    items = root.findall('.//item')
    tc = root.find('.//totalCount')
    print(f'totalCount: {tc.text if tc is not None else "N/A"}')
    print(f'item 수: {len(items)}')
    if items:
        for c in items[0]:
            print(f'  {c.tag}: {c.text}')
