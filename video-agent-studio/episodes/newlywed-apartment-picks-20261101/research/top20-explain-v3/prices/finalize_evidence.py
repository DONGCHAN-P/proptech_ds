"""가격·지도·대본용 근거를 연결합니다. 담당 폴더 외 쓰기를 하지 않습니다."""
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import duckdb
import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parent))
from inspect_freshness import HERE, ROOT, EPISODE, sha256, write


def amount(value):
    return f'{value:,.1f}'.rstrip('0').rstrip('.')+'만원'


if __name__=='__main__':
    checked=datetime.now(ZoneInfo('Asia/Seoul')).isoformat()
    prices=json.loads((HERE/'regional_prices.json').read_text(encoding='utf-8'))['rows']
    reps=json.loads((HERE/'representatives.json').read_text(encoding='utf-8'))['rows']
    repby={r['region_id']:r for r in reps}
    assets=json.loads((EPISODE/'visual/top20-8min-v2/maps/map_assets.json').read_text(encoding='utf-8'))['assets']
    layers=[]
    for a in assets:
        src=EPISODE/a['geometry_file']
        dest=HERE/'snapshots'/f'boundary_{a["region_id"]}_20241001.geojson.gz'
        if not dest.exists():shutil.copyfile(src,dest)
        assert sha256(src)==sha256(dest)
        p=next(p for p in prices if p['region_id']==a['region_id'])
        r=repby[a['region_id']]
        layers.append({'region_id':a['region_id'],'scene_id':p['scene_id'],'rank':p['rank'],
            'region':p['region'],'province':p['province'],'boundary_file':str(dest.relative_to(HERE)),
            'boundary_sha256':sha256(dest),'boundary_version':'2024-10-01',
            'boundary_source_url':a['source_url'],'boundary_license':a['license'],'boundary_attribution':a['attribution'],
            'statistical_geography':'2024 순위 구역 고정; R01은 현재 서해구+검단구 합산',
            'regional_fill_value_manwon':p['median_manwon'],'regional_n':p['n'],
            'regional_claim_id':'V3_PRICE_'+a['region_id'],'period_start':p['period_start'],'period_end':p['period_end'],
            'price_kind':'historical_observed_sale_median','current_price_verified':False,
            'area_filter':'83<=exclusive_m2<=85','cancel_filter':p['cancel_filter'],
            'marker':{'apt_id':r['apt_id'],'official_id':r['official_id'],'name':r['apt_name_raw'],
                'current_district':r['current_district_name'],'legal_dong_name':r['legal_dong_name'],
                'verified_road_address':r['official_road_address'],'longitude':r['longitude'],'latitude':r['latitude'],
                'coordinate_source':r['coordinate_source'],'coordinate_verified':r['coordinate_verified'],
                'point_in_2024_target_geometry':r['point_in_2024_target_geometry'],
                'point_in_official_polygon':r['point_in_official_polygon'],
                'transform_error_m':r['coordinate_transform_error_m'],
                'point_semantics':r['point_semantics'],'official_name_exact':r['official_name_exact'],
                'official_id_unique':r['official_id_unique_among_observed_apts'],
                'coordinate_basis_year':2025,'median_manwon':r['median_manwon'],'n':r['n'],
                'claim_id':'V3_APT_'+a['region_id'],'small_sample_n_lt10':r['n']<10},
            'display_title':'2026년 4~9월 관측 매매 중위값',
            'display_condition':f'전용 83~85㎡ · {p["n"]:,}건',
            'narration_source_policy':'2024 신혼부부 순위 출처는 도입부에서 설명합니다. 가격의 기간·면적·표본수는 지역 장면에 남깁니다.'})
    write('map_price_inputs.json',{'revision':'top20-explain-v3-prices-local-v1','layers':layers,
        'coordinate_verification_scope':'공식 단지 주소·정규화명·단일 공식ID, 원 SHP 내부점, 독립 PROJ 변환, 2024 구역 내부를 확인했습니다. 현장 출입구·개별 세대 위치를 확인한 것은 아닙니다.'})
    base={'source_url':'https://www.data.go.kr/data/15126468/openapi.do?recommendDataYn=Y',
        'source_file':'snapshots/trade_events_20regions.parquet','reference_date':'2026-09-30','checked_at':checked,
        'status':'qualified','unit':'만원','period':['2026-04-01','2026-09-30'],
        'exclusive_area_m2':{'minimum':83,'maximum':85,'endpoints_inclusive':True},
        'transaction_type':'아파트 매매; 원 로컬 파일은 중개/직거래 필드를 보존하지 않았습니다.',
        'floor_filter':'전체 층','statistic':'보존된 개별 관측 거래 금액 중위값; 월별 중위값 평균이 아닙니다.',
        'aggregation_method':'원금액 정렬의 가운데 값; 짝수는 가운데 두 값의 산술평균; 거래행별 동일 가중치',
        'cancellation_rule':'is_canceled IS FALSE AND cancel_date IS NULL; 현 로컬 스냅샷의 해제 표시는 제외했습니다.',
        'limitations':['현재 호가·판매 가능 상태·2026년10월 전체 자료를 확인하지 못했습니다.',
            '사후 해제와 미신고·지연신고의 최신 반영을 검증하지 못했습니다.',
            '상위 run_step3.py는 apt_id·계약일·전용면적·층 중복을 1행으로 정리한 후 deal_hash 중복을 제거합니다. 동일일·동일층 복수 세대의 별도 계약이 줄어들 수 있어 n은 이 보존 자료의 관측행 수입니다.',
            '연식·층·세부 주택형 구성 차이를 조정하지 않았습니다. 신혼부부 실제 매입가격이나 동일주택 가격지수가 아닙니다.']}
    facts=[]
    for p in prices:
        rid=p['region_id'];r=repby[rid]
        facts.append({**base,'claim_id':'V3_PRICE_'+rid,'affected_scene_ids':[p['scene_id']],
            'sentence':f'{p["province"]} {p["region"]}의 2026년 4~9월 전용 83~85㎡ 관측 매매 {p["n"]:,}건의 중위값은 {amount(p["median_manwon"])}입니다.',
            'scope':{'region_id':rid,'region':p['region'],'province':p['province'],
                     'current_source_codes':next(a['current_cache_codes'] for a in json.loads((EPISODE/'research/top20-8min-v2/price_context.json').read_text(encoding='utf-8'))['geography_crosswalk'] if a['region_id']==rid)},
            'evidence_location':f'regional_prices.csv region_id={rid}; aggregate.sql; 원거래 snapshot에서 scope_codes.csv로 연결합니다.',
            'sample_n':p['n'],'median_manwon':p['median_manwon'],'complex_count':p['complex_count'],
            'first_observed_contract':p['first_contract'],'last_observed_contract':p['last_contract'],
            'canceled_excluded_n':p['canceled_excluded_n'],'current_price_verified':False})
        facts.append({**base,'claim_id':'V3_APT_'+rid,'affected_scene_ids':[p['scene_id']],
            'sentence':f'{r["legal_dong_name"]}의 {r["apt_name_raw"]}는 같은 기간·면적 조건의 관측 거래 {r["n"]}건에서 중위값 {amount(r["median_manwon"])}을 기록한 단지 사례입니다.',
            'scope':{'region_id':rid,'apt_id':r['apt_id'],'official_id':r['official_id'],'verified_road_address':r['official_road_address']},
            'evidence_location':f'representatives.csv region_id={rid}; representative_transaction_evidence.csv apt_id={r["apt_id"]}',
            'sample_n':r['n'],'median_manwon':r['median_manwon'],'first_observed_contract':r['first_contract'],
            'last_observed_contract':r['last_contract'],'selection_reason':r['selection_reason'],
            'housing_stock_reference':{'households_2025_source':r['household_count'],'official_id':r['official_id']},
            'current_price_verified':False,'small_sample_n_lt10':r['n']<10})
        facts.append({'claim_id':'V3_COORD_'+rid,'sentence':f'{r["apt_name_raw"]}의 공식 단지 내부 대표점은 해당 2024년 순위 구역 경계 안에 있습니다.',
            'status':'verified','reference_date':'2025 공간원천; 2024-10-01 구역','checked_at':checked,
            'source_url':'https://www.bigdata-realestate.kr/rebpp/usr/prd/prdInfoDetail.do?req_productId=1',
            'source_file':'snapshots/representative_official_geometry_points.parquet',
            'evidence_location':f'official HSMP_INNB={r["official_id"]}; record_index={r["official_record_index"]}; snapshots/representative_official_polygon_rings.json; {layers[p["rank"]-1]["boundary_file"]}',
            'affected_scene_ids':[p['scene_id']],'longitude':r['longitude'],'latitude':r['latitude'],
            'scope':'단지 도형 내부 대표점입니다. 정문·세대 위치와 현장 확인을 의미하지 않습니다.',
            'source_identity_match':'도로명·본번·부번 단일 일치 + 정규화한 공식 명칭 정확 일치 + 공식ID 단일 일치',
            'independent_transform_engine':'pyproj 3.7.2 / EPSG:5179→EPSG:4326',
            'transform_error_m':r['coordinate_transform_error_m'],'point_in_official_polygon':True,'point_in_2024_target_geometry':True})
    facts.extend([
        {'claim_id':'V3_PRICE_FRESHNESS','sentence':'로컬 원거래의 전체 최신 계약일은 2026년 10월 10일이며 5~10월 전체의 현재 가격을 확정할 수 없습니다.',
         'source_file':'freshness.json','source_url':None,'evidence_location':'files: master/trade_events.parquet coverage; freshness_20regions.csv',
         'reference_date':'2026-10-10','checked_at':checked,'status':'verified','affected_scene_ids':[p['scene_id'] for p in prices]},
        {'claim_id':'V3_ADMIN_R01','sentence':'2024년 인천 서구의 순위 범위는 현재 서해구와 검단구를 합쳐 해석합니다.',
         'source_url':'https://mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=127039',
         'source_file':'raw/rtms_trade_expansion/admin_codes_20261023/jscode20260701.zip',
         'evidence_location':'공식 KIKcd_B.20260701.xlsx 2827500000=서해구, 2829000000=검단구; snapshots/admin_crosswalk.json; 지자체 발표와 출범 보도자료',
         'reference_date':'2026-07-01','checked_at':checked,'status':'verified','affected_scene_ids':['S022'],
         'additional_sources':['https://www.seohae.go.kr/open_content/main/bbs/bbsMsgDetail.do?bcd=report&msg_seq=18773','https://www.geomdan.go.kr/main/bbs/bbsMsgDetail.do?bcd=report&msg_seq=4'],
         'api_request_geography':{'202605_202606':['28260'],'202607_202610':['28275','28290']},
         'local_master_geography':'로컬 master는 과거 계약도 현재 두 코드로 보존합니다. 두 코드를 합산하고 구 코드 28260의 중복 합산은 하지 않았습니다.'},
        {'claim_id':'V3_PRICE_NOT_MARKET_QUOTE','sentence':'실거래 신고금액과 현재 거래 가능한 시세는 다르며 계약일과 신고·공개일 사이에는 시차가 있습니다.',
         'source_url':'https://rt.molit.go.kr/pt/bbs/faqList.do?mobileAt=&qnaProcessSttusCode=1','source_file':None,
         'evidence_location':'FAQ 실거래가와 일반시세 차이; 계약일자·신고일자와 제공시점 항목',
         'reference_date':'2026-11-03 확인','checked_at':checked,'status':'verified','affected_scene_ids':['S001','S002']}
    ])
    write('facts.json',{'revision':'top20-explain-v3-prices-local-v1','checked_at':checked,'claims':facts,
        'current_price_claims_verified':0,'price_claims_qualified':40,'note':'가격 집계의 로컬 재현 검증과 현재가격·전수 거래 원자료 검증을 구분했습니다.'})
    admin_source=ROOT/'raw/rtms_trade_expansion/admin_codes_20261023/district_codes.json'
    code_rows=json.loads(admin_source.read_text(encoding='utf-8'))
    write('snapshots/admin_crosswalk.json',{'effective_date':'2026-07-01','district_codes':[r for r in code_rows if r['code'] in set(pd.read_csv(HERE/'scope_codes.csv',dtype=str).current_code)],
        'R01_2024_code':'28260','R01_current_codes':['28275','28290'],'old2024_scope_preserved':True})
    write('asking_prices.json',{'checked_at':checked,'verified_current_listing_n':0,'rows':[],
        'scope_note':'기존 listing_evidence_v1.json에는 판매 확인 완료 매물이 없습니다. 이번 작업에서 추가 호가 조사·중개사 접촉을 하지 않았습니다.',
        'source_file':'../../listing_evidence_v1.json','transaction_median_combined_with_asking':False})
    sources=[('MLIT','https://www.data.go.kr/data/15126468/openapi.do?recommendDataYn=Y','지역코드와 계약년월로 아파트 매매 신고 상세정보를 조회하는 공식 원천입니다.'),
        ('MLIT_FAQ','https://rt.molit.go.kr/pt/bbs/faqList.do?mobileAt=&qnaProcessSttusCode=1','계약일 기준 자료와 일반시세의 차이 및 신고·공개 시차를 확인했습니다.'),
        ('MOIS','https://mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=127039','2026-07-01 시행 코드 변경 게시물과 이미 보존된 공식 코드 ZIP을 대조했습니다.'),
        ('SEOHAE','https://www.seohae.go.kr/open_content/main/bbs/bbsMsgDetail.do?bcd=report&msg_seq=18773','2026-05-08 게시물 제목에 7월1일 서해구 명칭 시행을 명시합니다.'),
        ('GEOMDAN','https://www.geomdan.go.kr/main/bbs/bbsMsgDetail.do?bcd=report&msg_seq=4','2026-07-02 보도자료 본문은 전날 검단구 실제 출범을 설명합니다.'),
        ('REB','https://www.bigdata-realestate.kr/rebpp/usr/prd/prdInfoDetail.do?req_productId=1','2025판 단지 공간원천의 공식 상품 페이지입니다. 이번 페이지 추출에서 세부 이용조건 본문은 재확인하지 못했으므로 기존 공간원천 인계 기록의 조건을 유지합니다.')]
    write('official_sources.json',{'checked_at':checked,'sources':[{'id':a,'url':b,'finding':c} for a,b,c in sources],
        'new_trade_api_response_received':False,'captured_trade_api_public_responses':0})
    known={'price_period':['2026-04-01','2026-09-30'],'not_current':True,'area':[83,85],
        'cancelled_excluded_n':sum(r['canceled_excluded_n'] for r in prices),'transaction_n':sum(r['n'] for r in prices),
        'direct_brokered_flag':'로컬 master와 서빙 캐시에 필드가 없어 분리할 수 없습니다.',
        'later_cancellation_coverage':'현재 스냅샷 이후 해제 여부를 API 갱신으로 재확인하지 못했습니다.',
        'upstream_dedup':'run_step3.py: apt_id+deal_date+area_m2+floor 중복 정리와 deal_hash 중복 정리',
        'comparison_to_previous_v2':'이전 표는 84<=전용<85㎡·3층 이상입니다. 본 표는 83<=전용<=85㎡·전체 층이며 master 스냅샷도 달라집니다. 두 표의 차이를 가격 상승률로 쓰면 안 됩니다.',
        'missing':['2026-10월 전체','현재 호가·판매 상태','사후 해제 최신 반영','개별 원거래 중개/직거래 유형','상위 중복 정리 전 복수 거래의 복원'],
        'region_coverage_flags':'모든 20지역을 포함했습니다. 위치 미확인 거래는 지역 중위값 계산에서 제외하지 않았습니다. 모든 개별 거래의 위치를 검사한 것은 아닙니다.'}
    write('methodology.json',known)
    header='지역별 가격표와 검증 범위\n\n'
    text=header+'이 자료는 2026년 4월 1일~9월 30일의 관측 실거래 참고자료입니다. 현재 호가나 2026년 5~10월 전체 중위값으로 표시할 수 없습니다. 전용 83~85㎡ 양끝 포함·전체 층·해제 표시 제외 조건으로 20지역 14,182건을 집계했습니다.\n\n'
    text+='지역 순위는 2024년 통계 구역을 유지합니다. R01은 현재 서해구와 검단구를 합산했습니다. 구 중위값은 서로 다른 연식·층·단지의 거래 구성에 영향을 받습니다. 대표단지는 거래가 활발한 법정동의 300세대 이상 단지 중 공식 주소·명칭·좌표가 일치하는 사례이며, 매수 추천이나 최고가 단지 선정이 아닙니다.\n\n'
    text+='|ID|지역|관측 중위값|n|단지 사례|단지 중위값|단지 n|\n|---|---|---:|---:|---|---:|---:|\n'
    for p in prices:
        r=repby[p['region_id']]
        text+=f'|{p["region_id"]}|{p["province"]} {p["region"]}|{amount(p["median_manwon"])}|{p["n"]}|{r["apt_name_raw"]}|{amount(r["median_manwon"])}|{r["n"]}|\n'
    text+='\nAPI 갱신은 승인된 200회 상한 중 1회 시도에서 ConnectionError가 발생해 응답을 받지 못했고, 자동 재시도 없이 중단했습니다. 인증·할당량을 확인하지 못했습니다. 원응답은 0개입니다. 기존 수집기에는 키가 있고 MOCK_MODE는 false이나 키 값은 이 패킷에 포함하지 않았습니다.\n\n'
    text+='상위 master는 동일 단지·계약일·면적·층을 1행으로 정리하므로 별도 세대 거래 일부가 합쳐졌을 가능성이 있습니다. 표본수는 이 보존 자료의 관측행 수이며 전수 신고건수라고 표현하지 않습니다. 최신 사후 해제·지연신고도 미확인입니다.\n\n'
    text+='지도 마커 20개는 공식 주소와 정규화 이름의 정확 일치·공식ID 단일성·원 SHP 내부·독립 pyproj 변환·2024 구 경계 내부 검사를 통과했습니다. 2025 공간원천의 단지 내부 대표점이며 정문 좌표가 아닙니다. 변환 최대 오차는 0.000023m 미만입니다. 실제 현장 방문 확인은 수행하지 않았습니다.\n\n'
    text+='writer 인계: 2024 순위의 한계와 가격 자료의 별도 기간을 도입부에서 설명합니다. 지역 장면에는 기간·면적·n을 남깁니다. 가격을 현재가로 바꾸려면 5~10월 원응답과 사후 해제를 다시 확보해야 합니다.\n\n'
    text+='재현: 프로젝트 루트에서 tools/python311/python.exe -X utf8 <이 폴더>/calculate_prices.py를 실행할 수 있습니다. 현재 결과는 snapshots/와 aggregate.sql로 고정되어 있습니다. aggregate.sql은 이 폴더를 작업 디렉터리로 DuckDB에서 실행합니다. API 스크립트는 장애 후 자동 중단 상태이며 임의 재실행해 갱신했다고 처리하지 않습니다.\n'
    (HERE/'검증범위.txt').write_text(text,encoding='utf-8')
    (HERE/'raw').mkdir(exist_ok=True)
    (HERE/'raw/응답안내.txt').write_text('공식 거래 API 첫 호출이 ConnectionError로 종료되어 보존할 HTTP 원응답이 없습니다. 원응답 수는 0개이며 자동 재시도는 하지 않았습니다.\n',encoding='utf-8')
    inputs=['master/trade_events.parquet','master/apt_id_map.parquet','web/cache/trades.parquet','web/cache/apt_index.parquet',
        'run_step2.py','run_step3.py','web/build_index.py',
        'raw/rtms_trade_expansion/admin_codes_20261023/jscode20260701.zip',
        'raw/rtms_trade_expansion/admin_codes_20261023/district_codes.json',
        str((EPISODE/'research/top20-8min-v2/top20.json').relative_to(ROOT)),
        str((EPISODE/'research/top20-8min-v2/price_context.json').relative_to(ROOT)),
        str((EPISODE/'research/listing_evidence_v1.json').relative_to(ROOT)),
        str((EPISODE/'visual/top20-8min-v2/maps/map_assets.json').relative_to(ROOT))]
    for name in ['capital_official_geometry.parquet','raw/APHUS_HSMP_CNTC_INFO.shp','raw/APHUS_HSMP_CNTC_INFO.shx','raw/APHUS_HSMP_CNTC_INFO.prj']:
        inputs.append(str((ROOT/'video-agent-studio/episodes/capital-10eok-map-20261017/research/coordinate-link-v2'/name).relative_to(ROOT)))
    write('source_manifest.json',{'created_at':checked,'inputs':[{'path':rel.replace('\\','/'),'sha256':sha256(ROOT/rel),'bytes':(ROOT/rel).stat().st_size} for rel in inputs],
        'frozen_snapshots':[{'path':str(p.relative_to(HERE)),'sha256':sha256(p),'bytes':p.stat().st_size} for p in sorted((HERE/'snapshots').iterdir()) if p.is_file()],
        'runtime':{'python':sys.version.split()[0],'duckdb':duckdb.__version__,'pandas':pd.__version__},
        'credential_files_included':False,'global_files_modified':False})
    print(json.dumps({'facts':len(facts),'map_layers':len(layers),'regions':len(prices),'api_attempts':1,'price_status':'qualified_historical_observations'},ensure_ascii=False))
