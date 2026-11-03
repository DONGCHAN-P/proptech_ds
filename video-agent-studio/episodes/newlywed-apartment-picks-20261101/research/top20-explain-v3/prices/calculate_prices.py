"""20지역 가격 근거를 고정합니다. 외부 호출/DB 변경/공통 파일 변경은 없습니다."""
import csv
import gzip
import json
import math
import os
import re
import struct
import sys
from collections import Counter, defaultdict
from pathlib import Path

import duckdb
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from inspect_freshness import HERE, ROOT, EPISODE, records, sha256, write

OFFICIAL = ROOT / 'video-agent-studio/episodes/capital-10eok-map-20261017/research/coordinate-link-v2'
SNAP = HERE / 'snapshots'
sys.path.insert(0, str(ROOT / 'tools/gis_vendor'))
from pyproj import Transformer, __version__ as proj_version


def export_csv(name, rows):
    pd.DataFrame(rows).to_csv(HERE / name, index=False, encoding='utf-8-sig', lineterminator='\n')


def normalize_name(value):
    return re.sub('[^0-9a-z가-힣]', '', str(value).lower().replace('아파트', ''))


def address_key(code, road):
    m = re.fullmatch(r'(.+?)\s+(\d+)(?:-(\d+))?', str(road).strip())
    return (str(code), m[1].strip(), int(m[2]), int(m[3] or 0)) if m else None


def in_ring(x, y, ring):
    inside = False
    for a, b in zip(ring, ring[1:] + ring[:1]):
        if (a[1] > y) != (b[1] > y) and x < a[0] + (y-a[1])*(b[0]-a[0])/(b[1]-a[1]):
            inside = not inside
    return inside


def in_geojson(x, y, geometry):
    polygons = geometry['coordinates'] if geometry['type'] == 'MultiPolygon' else [geometry['coordinates']]
    return any(in_ring(x,y,p[0]) and not any(in_ring(x,y,hole) for hole in p[1:]) for p in polygons)


def shape_rings(index):
    with (OFFICIAL / 'raw/APHUS_HSMP_CNTC_INFO.shx').open('rb') as f:
        f.seek(100 + index*8)
        offset, words = struct.unpack('>2i', f.read(8))
    with (OFFICIAL / 'raw/APHUS_HSMP_CNTC_INFO.shp').open('rb') as f:
        f.seek(offset*2+8)
        b = f.read(words*2)
    assert struct.unpack_from('<i',b)[0] == 5
    nr, np = struct.unpack_from('<2i',b,36)
    starts = list(struct.unpack_from('<'+'i'*nr,b,44)) + [np]
    pts = list(struct.iter_unpack('<2d',b[44+4*nr:44+4*nr+16*np]))
    return [pts[starts[k]:starts[k+1]] for k in range(nr)]


def scalar_records(df):
    return json.loads(df.to_json(orient='records', date_format='iso', force_ascii=False))


if __name__ == '__main__':
    SNAP.mkdir(exist_ok=True)
    os.chdir(HERE)
    con = duckdb.connect(':memory:')
    ranking = json.loads((EPISODE / 'research/top20-8min-v2/top20.json').read_text(encoding='utf-8'))['regions']
    crosswalk = json.loads((EPISODE / 'research/top20-8min-v2/price_context.json').read_text(encoding='utf-8'))['geography_crosswalk']
    codes = {x['region_id']: x['current_cache_codes'] for x in crosswalk}
    official_codes = json.loads((ROOT / 'raw/rtms_trade_expansion/admin_codes_20261023/district_codes.json').read_text(encoding='utf-8'))
    official_names = {r['code']:r['fields'][2] for r in official_codes}
    scope = [{**{k:r[k] for k in ['region_id','scene_id','rank','province','region']},
              'current_code':code, 'current_code_name':official_names[code]} for r in ranking for code in codes[r['region_id']]]
    export_csv('scope_codes.csv', scope)
    scope_frame = pd.DataFrame(scope)
    code_to_region = {r['current_code']:r['region_id'] for r in scope}
    extraction = "SELECT * FROM read_parquet(?) WHERE sigungu_code IN (SELECT current_code FROM read_csv('scope_codes.csv',all_varchar=true)) AND deal_date>=DATE '2026-04-01' AND deal_date<DATE '2026-11-01' ORDER BY sigungu_code,deal_date,apt_id,deal_hash"
    (HERE / 'extract_snapshot.sql').write_text(extraction.replace('?',"'"+(ROOT/'master/trade_events.parquet').as_posix()+"'")+';\n',encoding='utf-8')
    trades = con.execute(extraction,[str(ROOT/'master/trade_events.parquet')]).fetchdf()
    trades.to_parquet(SNAP/'trade_events_20regions.parquet',index=False)
    aptids = set(trades.apt_id)
    maps = pd.read_parquet(ROOT/'master/apt_id_map.parquet')
    maps = maps[maps.apt_id.isin(aptids)].copy()
    maps.to_parquet(SNAP/'apt_id_map_20regions.parquet',index=False)
    trades['region_id'] = trades.sigungu_code.map(code_to_region)
    window = trades[trades.deal_date < '2026-10-01'].copy()
    ok = window[(window.is_canceled == False) & window.cancel_date.isna() & (window.deal_amount > 0) & window.area_m2.between(83,85)].copy()
    regional = records(con, (HERE/'aggregate.sql').read_text(encoding='utf-8'))
    for r in regional:
        subset = ok[ok.region_id == r['region_id']]
        source = window[window.region_id == r['region_id']]
        area = source[source.area_m2.between(83,85) & (source.deal_amount > 0)]
        r.update({'period_start':'2026-04-01','period_end':'2026-09-30','area_filter':'83<=exclusive_m2<=85',
            'floor_filter':'전체 층; 층 제한 없음','cancel_filter':'is_canceled IS FALSE AND cancel_date IS NULL',
            'transaction_type':'아파트 매매; 중개/직거래 구분 불가','statistic':'개별 보존 원거래 금액 중위값',
            'unit':'만원','current_price_verified':False,'price_status':'qualified_historical_observations',
            'period_total_source_rows':len(source),'area_rows_before_cancel':len(area),
            'canceled_excluded_n':int(((area.is_canceled != False)|area.cancel_date.notna()).sum()),
            'missing_area_rows_all_sizes':int(source.area_m2.isna().sum()),
            'missing_floor_rows_included':int(subset.floor.isna().sum()),
            'missing_apt_identity_rows_included':int((~subset.apt_id.isin(aptids & set(maps.apt_id))).sum()),
            'actual_floor_min':int(subset.floor.min()),'actual_floor_max':int(subset.floor.max()),
            'latest_any_size_source_contract':str(trades[trades.region_id==r['region_id']].deal_date.max().date()),
            'median_eok':r['median_manwon']/10000})
        for k in ['first_contract','last_contract']:r[k]=str(r[k])
    write('regional_prices.json',{'rows':regional})
    export_csv('regional_prices.csv', regional)
    partial = trades[(trades.deal_date>='2026-05-01') & (trades.is_canceled==False) & trades.cancel_date.isna() & (trades.deal_amount>0) & trades.area_m2.between(83,85)]
    incomplete = scalar_records(partial.groupby('region_id').agg(n=('deal_amount','size'),median_manwon=('deal_amount','median'),first_contract=('deal_date','min'),last_contract=('deal_date','max')).reset_index())
    for r in incomplete:r.update({'requested_start':'2026-05-01','requested_end':'2026-10-31','coverage_status':'incomplete_current_price_label_prohibited','gap':'10월 전체 미수집; 지역별 마지막 관측 계약일 이후 미확인'})
    export_csv('requested_window_incomplete_observations.csv', incomplete)
    # 지역 집계에는 주소·좌표 결합을 쓰지 않아 위치 미확인 거래도 포함합니다.
    complexes = []
    for (rid, aid), g in ok.groupby(['region_id','apt_id'],sort=True):
        r = {'region_id':rid,'apt_id':aid,'n':len(g),'median_manwon':float(g.deal_amount.median()),
             'first_contract':str(g.deal_date.min().date()),'last_contract':str(g.deal_date.max().date()),
             'actual_area_min_m2':float(g.area_m2.min()),'actual_area_max_m2':float(g.area_m2.max()),
             'floor_min':int(g.floor.min()),'floor_max':int(g.floor.max()),
             'build_year':int(g.build_year.mode().iloc[0]) if not g.build_year.dropna().empty else None}
        for field in ['apt_name_raw','sigungu_code','legal_dong_code','legal_dong_name','road_address']:
            r[field]=str(g[field].mode().iloc[0]) if not g[field].dropna().empty else ''
        r['road_address_variants']=int(g.road_address.nunique())
        complexes.append(r)
    official = pd.read_parquet(OFFICIAL/'capital_official_geometry.parquet')
    address_groups = defaultdict(list)
    for row in scalar_records(official):
        address_groups[(row['SIGNGU_CD'],str(row['RN']).strip(),int(row['ROAD_HMNO'] or 0),int(row['ROAD_VCNO'] or 0))].append(row)
    assets = json.loads((EPISODE/'visual/top20-8min-v2/maps/map_assets.json').read_text(encoding='utf-8'))['assets']
    geometries = {r['region_id']:json.loads(gzip.decompress((EPISODE/r['geometry_file']).read_bytes())) for r in assets}
    transformer = Transformer.from_crs(5179,4326,always_xy=True)
    reverse = Transformer.from_crs(4326,5179,always_xy=True)
    for r in complexes:
        keycode = '28260' if r['region_id']=='R01' else r['sigungu_code']
        matches = address_groups.get(address_key(keycode,r['road_address']),[])
        r['official_address_match_count']=len(matches)
        r['official_name_exact']=False
        r['coordinate_verified']=False
        if len(matches)!=1:continue
        o=matches[0]
        names=[o[k] for k in ['POT_HSM_NM','BLD_HSM_NM','ROD_HSM_NM']]
        exact=normalize_name(r['apt_name_raw']) in {normalize_name(n) for n in names if n}
        r.update({'official_id':o['HSMP_INNB'],'official_record_index':int(o['record_index']),
                  'official_names':' | '.join(n for n in names if n),'official_name_exact':exact,
                  'official_pnu':o['PNU'],'household_count':int(o['NMHSH'] or 0),
                  'official_old_sigungu_code':o['SIGNGU_CD'],
                  'official_road_address':str(o['RN']).strip()+' '+str(int(o['ROAD_HMNO'] or 0)) + ('-'+str(int(o['ROAD_VCNO'])) if int(o['ROAD_VCNO'] or 0) else '')})
        if not exact:continue
        lon,lat=transformer.transform(o['x_5179'],o['y_5179'])
        xx,yy=reverse.transform(o['lon'],o['lat'])
        error=math.hypot(xx-o['x_5179'],yy-o['y_5179'])
        rings=shape_rings(int(o['record_index']))
        official_inside=sum(in_ring(o['x_5179'],o['y_5179'],ring) for ring in rings)%2==1
        boundary_inside=any(in_geojson(lon,lat,f['geometry']) for f in geometries[r['region_id']]['features'])
        r.update({'longitude':lon,'latitude':lat,'coordinate_transform_error_m':error,
                  'point_in_official_polygon':official_inside,'point_in_2024_target_geometry':boundary_inside,
                  'coordinate_verified':bool(official_inside and boundary_inside and error<0.1),
                  'coordinate_source':'한국부동산원 공동주택 단지 연계정보(2025) 공식 폴리곤 내부점; pyproj 독립 재변환',
                  'point_semantics':'단지 내부 대표점; 정문·세대 위치 아님'})
    matched_counts=Counter(r.get('official_id') for r in complexes if r.get('official_name_exact'))
    for r in complexes:
        r['official_id_unique_among_observed_apts'] = bool(r.get('official_id') and matched_counts[r['official_id']]==1)
        r['eligible_representative'] = bool(r['n']>=3 and r.get('household_count',0)>=300 and r.get('coordinate_verified') and r['official_id_unique_among_observed_apts'] and r['road_address_variants']==1)
    export_csv('complex_candidates_audit.csv',complexes)
    reps=[]
    for regional_row in regional:
        rid=regional_row['region_id']
        dong_counts=ok[ok.region_id==rid].groupby('legal_dong_name').size().to_dict()
        dong_order=sorted(dong_counts,key=lambda x:(-dong_counts[x],x))
        candidates=[r for r in complexes if r['region_id']==rid and r['eligible_representative']]
        preferred=[r for r in candidates if r['n']>=5]
        candidates=preferred or candidates
        if not candidates:continue
        r=dict(min(candidates,key=lambda a:(dong_order.index(a['legal_dong_name']),abs(a['median_manwon']-regional_row['median_manwon']),-a['n'],a['apt_id'])))
        r.update({'scene_id':regional_row['scene_id'],'rank':regional_row['rank'],'province':regional_row['province'],
                  'region':regional_row['region'],'current_district_name':official_names[r['sigungu_code']],
                  'period_start':'2026-04-01','period_end':'2026-09-30','unit':'만원','statistic':'단지 내 83~85㎡ 관측 매매 중위값',
                  'area_filter':'83<=exclusive_m2<=85','floor_filter':'전체 층','canceled_excluded':True,
                  'living_area_observation_n':int(dong_counts[r['legal_dong_name']]),
                  'living_area_rank_by_observed_83_85_n':dong_order.index(r['legal_dong_name'])+1,
                  'selection_reason':'동일 면적 관측 거래가 많은 법정동 순서에서, 공식 단일 주소·명칭·ID·좌표 검사를 통과한 300세대 이상 단지 중 지역 관측 중위값에 가장 가까운 사례를 선택했습니다. n>=5를 우선했습니다.',
                  'not_a_purchase_recommendation':True,'current_price_verified':False})
        reps.append(r)
    write('representatives.json',{'rows':reps,'missing_region_ids':[r['region_id'] for r in ranking if r['region_id'] not in {a['region_id'] for a in reps}]})
    export_csv('representatives.csv',reps)
    wanted={r['official_record_index'] for r in reps}
    official[official.record_index.isin(wanted)].to_parquet(SNAP/'representative_official_geometry_points.parquet',index=False)
    write('snapshots/representative_official_polygon_rings.json',{str(i):shape_rings(i) for i in wanted})
    keep_ids={r['apt_id'] for r in reps}
    export_csv('representative_transaction_evidence.csv',scalar_records(ok[ok.apt_id.isin(keep_ids)].sort_values(['region_id','apt_id','deal_date','deal_hash'])))
    write('calculation_summary.json',{'regions':len(regional),'included_n':len(ok),'representatives':len(reps),
        'representative_n_min':min([r['n'] for r in reps],default=0),
        'raw_snapshot_rows':len(trades),'source_deal_hash_duplicates':int(trades.deal_hash.duplicated().sum()),
        'observed_apt_ids':len(complexes),'eligible_representative_count':sum(r['eligible_representative'] for r in complexes),
        'coordinate_engine':'pyproj '+proj_version,'external_api_calls':0,'database_mutation':False})
    print(json.dumps({'regions':len(regional),'included_n':len(ok),'representatives':len(reps),'missing_reps':[r['region_id'] for r in ranking if r['region_id'] not in {a['region_id'] for a in reps}]},ensure_ascii=False))
