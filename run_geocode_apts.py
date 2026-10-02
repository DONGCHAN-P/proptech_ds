"""apt_id_map에 lat/lng 좌표 추가 - V-World 주소 지오코딩"""
import sys
sys.path.insert(0, r'c:\projects\realestate_reco')

from common import *
import pandas as pd
import requests
import time
from pathlib import Path

SECRETS = load_secrets()
VWORLD_KEY = SECRETS.get('VWORLD_API_KEY', '')

CITY_PREFIX = {
    '11': '서울특별시',
    '28': '인천광역시',
    '41': '경기도',
}


def build_full_address(row) -> str:
    code = str(row['sigungu_code'])
    city = CITY_PREFIX.get(code[:2], '')
    gu = SIGUNGU_CODES.get(code, '')
    road = str(row['road_address'] or '').strip()
    # 번지 앞 0 제거: "00089" → "89"
    parts = road.rsplit(' ', 1)
    if len(parts) == 2:
        road = parts[0] + ' ' + str(int(parts[1])) if parts[1].isdigit() else road
    return f'{city} {gu} {road}'.strip()


def vworld_geocode(address: str) -> tuple[float, float]:
    if not VWORLD_KEY or not address:
        return 0.0, 0.0
    try:
        r = requests.get(
            'https://api.vworld.kr/req/address',
            params={
                'service': 'address', 'request': 'getcoord',
                'version': '2.0', 'key': VWORLD_KEY,
                'address': address, 'type': 'ROAD',
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


def geocode_all(df: pd.DataFrame, batch_size: int = 100) -> pd.DataFrame:
    df = df.copy()

    # 이미 좌표 있으면 건너뜀
    if 'lat' not in df.columns:
        df['lat'] = 0.0
    if 'lng' not in df.columns:
        df['lng'] = 0.0

    todo = df[(df['lat'] == 0.0) | (df['lat'].isna())].index
    total = len(todo)
    print(f'지오코딩 대상: {total:,}건')

    ok = 0
    fail = 0
    for i, idx in enumerate(todo):
        row = df.loc[idx]
        addr = build_full_address(row)
        lat, lng = vworld_geocode(addr)
        if lat != 0.0:
            df.at[idx, 'lat'] = lat
            df.at[idx, 'lng'] = lng
            ok += 1
        else:
            fail += 1

        if (i + 1) % batch_size == 0:
            print(f'  진행: {i+1:,}/{total:,} | 성공: {ok:,} | 실패: {fail:,}')
            # 중간 저장
            _save(df)
            time.sleep(0.05)

    print(f'\n완료: 성공 {ok:,} / 실패 {fail:,} / 전체 {total:,}')
    return df


def _save(df: pd.DataFrame):
    path = DIRS['master'] / 'apt_id_map.parquet'
    tmp = DIRS['master'] / 'apt_id_map.parquet.tmp'
    df.to_parquet(tmp, index=False, compression='zstd')
    tmp.replace(path)


df_map = pd.read_parquet(DIRS['master'] / 'apt_id_map.parquet')
print(f'로드: {len(df_map):,}개 단지')

df_map = geocode_all(df_map)
_save(df_map)

geocoded = (df_map['lat'] != 0.0).sum()
print(f'\napt_id_map 저장 완료: {geocoded:,}/{len(df_map):,}건 좌표 보유')
