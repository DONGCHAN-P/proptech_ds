"""지오코딩 실패 케이스 재시도 - 도로명 실패 시 법정동+단지명으로 폴백"""
import sys
sys.path.insert(0, r'c:\projects\realestate_reco')

from common import *
import pandas as pd
import requests
import time

SECRETS = load_secrets()
VWORLD_KEY = SECRETS.get('VWORLD_API_KEY', '')

CITY_PREFIX = {'11': '서울특별시', '28': '인천광역시', '41': '경기도'}


def vworld_geocode(address: str) -> tuple[float, float]:
    if not VWORLD_KEY or not address.strip():
        return 0.0, 0.0
    for addr_type in ['ROAD', 'PARCEL']:
        try:
            r = requests.get(
                'https://api.vworld.kr/req/address',
                params={
                    'service': 'address', 'request': 'getcoord',
                    'version': '2.0', 'key': VWORLD_KEY,
                    'address': address, 'type': addr_type,
                    'simple': 'false', 'format': 'json',
                },
                timeout=10
            )
            resp = r.json().get('response', {})
            if resp.get('status') == 'OK':
                pt = resp['result']['point']
                return float(pt['y']), float(pt['x'])
        except Exception:
            pass
    return 0.0, 0.0


def build_road_address(row) -> str:
    code = str(row['sigungu_code'])
    city = CITY_PREFIX.get(code[:2], '')
    gu = SIGUNGU_CODES.get(code, '')
    road = str(row['road_address'] or '').strip()
    parts = road.rsplit(' ', 1)
    if len(parts) == 2 and parts[1].isdigit():
        road = parts[0] + ' ' + str(int(parts[1]))
    return f'{city} {gu} {road}'.strip()


def build_dong_address(row) -> str:
    """법정동 + 단지명으로 주소 구성"""
    code = str(row['sigungu_code'])
    city = CITY_PREFIX.get(code[:2], '')
    gu = SIGUNGU_CODES.get(code, '')
    dong = str(row['legal_dong_name'] or '').strip()
    name = str(row['apt_name_norm'] or '').strip()
    # "서울특별시 강남구 역삼동 래미안"
    return f'{city} {gu} {dong} {name}'.strip()


def build_dong_only(row) -> str:
    """법정동만으로 구성 (단지명 제외)"""
    code = str(row['sigungu_code'])
    city = CITY_PREFIX.get(code[:2], '')
    gu = SIGUNGU_CODES.get(code, '')
    dong = str(row['legal_dong_name'] or '').strip()
    return f'{city} {gu} {dong}'.strip()


df = pd.read_parquet(DIRS['master'] / 'apt_id_map.parquet')
failed = df[(df['lat'] == 0.0) | (df['lat'].isna())].copy()
print(f'재시도 대상: {len(failed)}건')

ok = 0
fail = 0
tried = {}  # idx → 성공한 방법

for i, (idx, row) in enumerate(failed.iterrows()):
    # 시도 순서: 1) 도로명(번지 제외), 2) 법정동+단지명, 3) 법정동만
    candidates = []

    # 도로명에서 번지만 제거한 버전
    code = str(row['sigungu_code'])
    city = CITY_PREFIX.get(code[:2], '')
    gu = SIGUNGU_CODES.get(code, '')
    road = str(row['road_address'] or '').strip()
    road_parts = road.rsplit(' ', 1)
    if len(road_parts) == 2:
        candidates.append((f"{city} {gu} {road_parts[0]}", '도로명(번지제외)'))

    candidates.append((build_dong_address(row), '법정동+단지명'))
    candidates.append((build_dong_only(row), '법정동만'))

    lat, lng, method = 0.0, 0.0, None
    for addr, label in candidates:
        lat, lng = vworld_geocode(addr)
        if lat != 0.0:
            method = label
            break
        time.sleep(0.05)

    if lat != 0.0:
        df.at[idx, 'lat'] = lat
        df.at[idx, 'lng'] = lng
        tried[idx] = method
        ok += 1
    else:
        fail += 1

    if (i + 1) % 50 == 0:
        print(f'  진행: {i+1}/{len(failed)} | 성공: {ok} | 실패: {fail}')

print(f'\n재시도 결과: 성공 {ok} / 실패 {fail}')
if tried:
    from collections import Counter
    print('성공 방법:', dict(Counter(tried.values())))

# 저장
path = DIRS['master'] / 'apt_id_map.parquet'
tmp = DIRS['master'] / 'apt_id_map.parquet.tmp'
df.to_parquet(tmp, index=False, compression='zstd')
tmp.replace(path)

total_ok = (df['lat'] != 0.0).sum()
print(f'\napt_id_map 저장 완료: {total_ok:,}/{len(df):,}건 좌표 보유')
