import sys
sys.path.insert(0, r'c:\projects\realestate_reco')
from common import *
import pandas as pd

df = pd.read_parquet(DIRS['master'] / 'apt_id_map.parquet')
failed = df[(df['lat'] == 0.0) | (df['lat'].isna())].copy()
print(f'실패 건수: {len(failed)}건')
print()

# road_address 패턴 분석
failed['addr_len'] = failed['road_address'].str.len()
failed['has_number'] = failed['road_address'].str.contains(r'\d', na=False)
failed['road_only'] = ~failed['road_address'].str.contains(r'\d{2,}', na=False)

print('주소 길이 분포:')
print(failed['addr_len'].describe())
print()
print('숫자 없음 (도로명만):', (~failed['has_number']).sum())
print('번지 없음 (2자리 숫자 없음):', failed['road_only'].sum())
print()
print('샘플 실패 주소 (30건):')
for _, row in failed[['sigungu_code','legal_dong_name','road_address']].head(30).iterrows():
    city = {'11':'서울', '28':'인천', '41':'경기'}.get(str(row['sigungu_code'])[:2], '')
    gu = SIGUNGU_CODES.get(str(row['sigungu_code']), '')
    print(f"  [{city} {gu}] '{row['road_address']}'")
