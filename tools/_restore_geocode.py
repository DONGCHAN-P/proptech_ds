"""SQLite apt_master에서 lat/lng 복원 후 신규 단지만 지오코딩"""
import sys
sys.path.insert(0, r'c:\projects\realestate_reco')
from common import *
import pandas as pd
import sqlite3
import requests
import time

SECRETS = load_secrets()
VWORLD_KEY = SECRETS.get('VWORLD_API_KEY', '')

CITY_PREFIX = {'11': '서울특별시', '28': '인천광역시', '41': '경기도'}


def build_full_address(row) -> str:
    code = str(row['sigungu_code'])
    city = CITY_PREFIX.get(code[:2], '')
    gu = SIGUNGU_CODES.get(code, '')
    road = str(row['road_address'] or '').strip()
    parts = road.rsplit(' ', 1)
    if len(parts) == 2:
        road = parts[0] + ' ' + str(int(parts[1])) if parts[1].isdigit() else road
    return f'{city} {gu} {road}'.strip()


def vworld_geocode(address: str):
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


# ── 1. apt_id_map 로드 ────────────────────────────────────────
am = pd.read_parquet(DIRS['master'] / 'apt_id_map.parquet')
print(f'apt_id_map: {len(am)}개, 컬럼: {list(am.columns)}')

# ── 2. SQLite에서 기존 lat/lng 복원 ──────────────────────────
con = sqlite3.connect(BASE / 'realestate.db')
db = pd.read_sql(
    'SELECT apt_seq as apt_id, lat, lng FROM apt_master WHERE lat IS NOT NULL AND lat != 0',
    con
)
con.close()
print(f'DB 보유 lat/lng: {len(db)}개')

if 'lat' not in am.columns:
    am['lat'] = 0.0
if 'lng' not in am.columns:
    am['lng'] = 0.0

# apt_id 기준으로 lat/lng 채우기
lat_map = db.set_index('apt_id')['lat'].to_dict()
lng_map = db.set_index('apt_id')['lng'].to_dict()
am['lat'] = am['apt_id'].map(lat_map).fillna(0.0)
am['lng'] = am['apt_id'].map(lng_map).fillna(0.0)

restored = (am['lat'] != 0.0).sum()
need_geocode = (am['lat'] == 0.0).sum()
print(f'복원 성공: {restored:,}개 / 신규 지오코딩 필요: {need_geocode:,}개')

# ── 3. 신규 단지만 V-World 지오코딩 ──────────────────────────
todo_idx = am[am['lat'] == 0.0].index
print(f'\n지오코딩 시작: {len(todo_idx):,}건')

ok = 0
fail = 0
for i, idx in enumerate(todo_idx):
    row = am.loc[idx]
    addr = build_full_address(row)
    lat, lng = vworld_geocode(addr)
    if lat != 0.0:
        am.at[idx, 'lat'] = lat
        am.at[idx, 'lng'] = lng
        ok += 1
    else:
        fail += 1
    if (i + 1) % 50 == 0:
        print(f'  {i+1}/{len(todo_idx)} | 성공:{ok} 실패:{fail}')
        # 중간 저장
        tmp = DIRS['master'] / 'apt_id_map.parquet.tmp'
        am.to_parquet(tmp, index=False, compression='zstd')
        tmp.replace(DIRS['master'] / 'apt_id_map.parquet')
    time.sleep(0.05)

print(f'\n지오코딩 완료: 성공 {ok} / 실패 {fail}')

# ── 4. 최종 저장 ─────────────────────────────────────────────
tmp = DIRS['master'] / 'apt_id_map.parquet.tmp'
am.to_parquet(tmp, index=False, compression='zstd')
tmp.replace(DIRS['master'] / 'apt_id_map.parquet')
print(f'apt_id_map 저장 완료: {len(am)}개')
