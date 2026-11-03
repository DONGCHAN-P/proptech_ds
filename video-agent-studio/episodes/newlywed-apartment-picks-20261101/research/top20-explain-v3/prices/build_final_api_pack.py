"""보존된 공식 API 응답만으로 새 가격팩을 생성합니다. 네트워크 호출은 없습니다."""
import hashlib
import json
import math
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parent))
from inspect_freshness import HERE, ROOT, EPISODE, sha256
from calculate_prices import address_key, normalize_name, shape_rings, in_ring, in_geojson, OFFICIAL
import gzip

OUT=HERE/'final-api-20261103-v2'
OUT.mkdir(exist_ok=True)


def save(name,data):
    (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')


def csvout(name,rows):
    pd.DataFrame(rows).to_csv(OUT/name,index=False,encoding='utf-8-sig',lineterminator='\n')


def numeric(text):
    try:return float(Decimal(str(text).replace(',','').strip()))
    except (ValueError,InvalidOperation):return None


if __name__=='__main__':
    ledger=json.loads((HERE/'api_request_log.json').read_text(encoding='utf-8'))
    receipt=json.loads((HERE/'api_collection_receipt.json').read_text(encoding='utf-8'))
    assert receipt['complete'] and len(ledger['requests'])<=200
    scope=pd.read_csv(HERE/'scope_codes.csv',dtype=str)
    code_region=dict(zip(scope.current_code,scope.region_id))
    rankrows=json.loads((EPISODE/'research/top20-8min-v2/top20.json').read_text(encoding='utf-8'))['regions']
    rankby={r['region_id']:r for r in rankrows}
    successful=[r for r in ledger['requests'] if r['status']=='ok' and r['lawd_cd'] in code_region]
    desired={(code,ym) for code in code_region for ym in ['202605','202606','202607','202608','202609','202610']}
    assert {(r['lawd_cd'],r['contract_month']) for r in successful}==desired
    rawrows=[];coverage=[];response_inputs=[]
    for code,ym in sorted(desired):
        pages=sorted([r for r in successful if r['lawd_cd']==code and r['contract_month']==ym],key=lambda r:r['page'])
        assert len({r['page'] for r in pages})==len(pages)
        expected=pages[0]['total_count']
        assert sum(r['rows'] for r in pages)==expected
        assert [r['page'] for r in pages]==list(range(1,math.ceil(expected/1000)+1))
        coverage.append({'region_id':code_region[code],'query_code':code,'contract_month':ym,'api_total_count':expected,'received_rows':sum(r['rows'] for r in pages),'all_pages_received':True,'as_of_request_start':pages[0]['started_at'],'as_of_request_end':pages[-1]['finished_at'],'reporting_complete':False})
        for response in pages:
            path=HERE/response['response_file'];assert sha256(path)==response['response_sha256']
            response_inputs.append({'file':'../'+response['response_file'],'sha256':response['response_sha256'],'rows':response['rows'],'sequence':response['sequence']})
            root=ET.parse(path).getroot()
            for i,item in enumerate(root.findall('.//item'),1):
                fields={ch.tag:(ch.text or '').strip() for ch in item}
                assert fields.get('sggCd')==code
                date=f'{int(fields["dealYear"]):04d}-{int(fields["dealMonth"]):02d}-{int(fields["dealDay"]):02d}'
                assert date[:7].replace('-','')==ym
                rawrows.append({**fields,'region_id':code_region[code],'query_code':code,'contract_month':ym,'deal_date':date,
                    'deal_amount_manwon':numeric(fields.get('dealAmount','')),'area_m2':numeric(fields.get('excluUseAr','')),
                    'floor_value':numeric(fields.get('floor','')),'canceled':bool(fields.get('cdealType') or fields.get('cdealDay')),
                    'source_response':'../'+response['response_file'],'source_item_index_1based':i,
                    'api_row_id':hashlib.sha256((response['response_sha256']+':'+str(i)).encode()).hexdigest(),
                    'exact_published_item_hash':hashlib.sha256(json.dumps(fields,ensure_ascii=False,sort_keys=True).encode()).hexdigest()})
    # API에 고유 계약ID가 없으므로 같은 날짜·층의 정상 복수 행은 삭제하지 않습니다.
    # 해제 행과 같은 공개 필드를 가진 정상 행은 감사 후보로만 기록합니다.
    # 고유 계약ID가 없어 동일 계약을 확정할 수 없으므로 정상 행을 삭제하지 않습니다.
    immutable=['sggCd','aptSeq','aptNm','umdCd','umdNm','jibun','roadNm','roadNmBonbun','roadNmBubun','dealYear','dealMonth','dealDay','excluUseAr','dealAmount','floor','aptDong','dealingGbn','estateAgentSggNm','buyerGbn','slerGbn','buildYear','landCd','landLeaseholdGbn']
    groups=defaultdict(list)
    for r in rawrows:
        key=tuple(r.get(k,'') for k in immutable)
        r['cancellation_match_key']=hashlib.sha256(json.dumps(key,ensure_ascii=False).encode()).hexdigest()
        groups[key].append(r)
    paired=[]
    for rows in groups.values():
        cancelled=sorted([r for r in rows if r['canceled']],key=lambda r:r['api_row_id'])
        normal=sorted([r for r in rows if not r['canceled']],key=lambda r:r['api_row_id'])
        for a,b in zip(cancelled,normal):
            b['possible_same_contract_as_canceled']=True
            paired.append({'normal_row_id':b['api_row_id'],'canceled_row_id':a['api_row_id'],'match_key':a['cancellation_match_key'],'region_id':b['region_id'],'ambiguous_multiple_normal_rows':len(normal)>1})
    for r in rawrows:
        r.setdefault('paired_original_removed',False)
        r.setdefault('possible_same_contract_as_canceled',False)
        r['exclusion_reason']='canceled' if r['canceled'] else ('original_matched_to_cancellation' if r['paired_original_removed'] else ('missing_or_nonpositive_amount' if r['deal_amount_manwon'] is None or r['deal_amount_manwon']<=0 else ('outside_area_or_missing' if r['area_m2'] is None or not 83<=r['area_m2']<=85 else 'included')))
        main=str(r.get('roadNmBonbun','')).lstrip('0') or '0';sub=str(r.get('roadNmBubun','')).lstrip('0') or '0'
        r['road_address']=r.get('roadNm','')+' '+main+('-'+sub if sub!='0' else '')
        r['api_complex_id']=r.get('aptSeq') or ('fallback:'+hashlib.sha256((r['query_code']+'|'+r.get('aptNm','')+'|'+r['road_address']+'|'+r.get('umdCd','')).encode()).hexdigest()[:16])
    frame=pd.DataFrame(rawrows)
    frame.to_parquet(OUT/'api_rows_all.parquet',index=False)
    valid=[r for r in rawrows if r['exclusion_reason']=='included']
    vf=pd.DataFrame(valid)
    vf.to_parquet(OUT/'api_rows_valid83_85.parquet',index=False)
    save('cancellation_match_candidates.json',{'candidate_match_fields':immutable,'pairs':paired,'automatic_removal_applied':False,'normal_multiple_rows_preserved':True,
        'limitation':'공개 API에는 고유 계약번호가 없어 필드가 같아도 같은 계약인지 재계약·별도 거래인지 확정할 수 없습니다. 해제 표시는 제외하되 정상 행은 보존합니다.'})
    csvout('source_coverage.csv',coverage)
    prices=[]
    for rid,g in vf.groupby('region_id',sort=True):
        rank=rankby[rid]
        rows=[r for r in rawrows if r['region_id']==rid]
        band=[r for r in rows if r['area_m2'] is not None and 83<=r['area_m2']<=85 and r['deal_amount_manwon'] is not None and r['deal_amount_manwon']>0]
        counts=Counter(r['exclusion_reason'] for r in band)
        prices.append({'region_id':rid,'scene_id':rank['scene_id'],'rank':rank['rank'],'province':rank['province'],'region':rank['region'],
            'contract_period_start':'2026-05-01','contract_period_end':'2026-10-31','as_of_date':'2026-11-03',
            'as_of_first_response':min(r['started_at'] for r in successful),'as_of_last_response':max(r['finished_at'] for r in successful),
            'reporting_complete':False,'october_reporting_ongoing':True,'all_requested_pages_received':True,
            'n':len(g),'complex_count':int(g.api_complex_id.nunique()),'median_manwon':float(g.deal_amount_manwon.median()),
            'p25_manwon':float(g.deal_amount_manwon.quantile(.25)),'p75_manwon':float(g.deal_amount_manwon.quantile(.75)),
            'first_observed_contract':min(g.deal_date),'last_observed_contract':max(g.deal_date),
            'brokered_n':int((g.dealingGbn=='중개거래').sum()),'direct_n':int((g.dealingGbn=='직거래').sum()),
            'trade_type_other_or_missing_n':int((~g.dealingGbn.isin(['중개거래','직거래'])).sum()),
            'api_area_rows_before_cancel':len(band),'canceled_row_excluded_n':counts['canceled'],
            'original_cancellation_pair_removed_n':counts['original_matched_to_cancellation'],
            'statistic':'조회 시점 API 유효행 금액 중위값','unit':'만원','area_filter':'83<=exclusive_m2<=85','floor_filter':'전체 층',
            'price_kind':'as_of_observed_sale_median','asking_prices_included':False,'typical_house_price_claim':False})
    csvout('regional_prices.csv',prices);save('regional_prices.json',{'revision':OUT.name,'rows':prices})
    # 검증된 단지 위치 후보를 새 API의 aptSeq·명칭·주소와 직접 연결합니다.
    cached=pd.read_csv(HERE/'complex_candidates_audit.csv',keep_default_na=False).to_dict('records')
    lookup=defaultdict(list)
    for r in cached:
        if r.get('coordinate_verified') not in [True,'True'] or r.get('official_id_unique_among_observed_apts') not in [True,'True']:continue
        if not r.get('household_count') or int(float(r['household_count']))<300:continue
        code=str(r['sigungu_code']);key=address_key(code,r['road_address'])
        for name in set([r['apt_name_raw']]+str(r.get('official_names','')).split(' | ')):
            lookup[(key,normalize_name(name))].append(r)
    candidates=[]
    for (rid,aid),g in vf.groupby(['region_id','api_complex_id'],sort=True):
        first=g.iloc[0];key=(address_key(first.query_code,first.road_address),normalize_name(first.aptNm))
        match={r['apt_id']:r for r in lookup.get(key,[])}
        if len(match)!=1 or g.road_address.nunique()!=1:continue
        c=dict(next(iter(match.values())))
        c.update({'region_id':rid,'api_complex_id':aid,'api_apt_name':first.aptNm,'api_query_code':first.query_code,'api_road_address':first.road_address,'legal_dong_name':first.umdNm,
            'n':len(g),'median_manwon':float(g.deal_amount_manwon.median()),'first_observed_contract':min(g.deal_date),'last_observed_contract':max(g.deal_date)})
        candidates.append(c)
    reps=[]
    for p in prices:
        rid=p['region_id'];dongcounts=vf[vf.region_id==rid].groupby('umdNm').size().to_dict();dongorder=sorted(dongcounts,key=lambda d:(-dongcounts[d],d))
        pool=[r for r in candidates if r['region_id']==rid and r['n']>=5]
        assert pool,'n>=5 representative unavailable '+rid
        r=dict(min(pool,key=lambda r:(dongorder.index(r['legal_dong_name']),abs(r['median_manwon']-p['median_manwon']),-r['n'],r['api_complex_id'])))
        r.update({'scene_id':p['scene_id'],'rank':p['rank'],'region':p['region'],'province':p['province'],'contract_period_start':'2026-05-01','contract_period_end':'2026-10-31','as_of_date':'2026-11-03',
            'reporting_complete':False,'october_reporting_ongoing':True,'unit':'만원','statistic':'API 단지 사례 유효행 금액 중위값','area_filter':'83<=exclusive_m2<=85','floor_filter':'전체 층',
            'selection_reason':'관측 거래가 많은 법정동 순서에서 공식 주소·정규화명·위치 일치와 300세대 이상 조건을 통과한 n>=5 단지 중 구 중위값에 가까운 사례를 선택했습니다.',
            'represents_entire_gu_typical_price':False,'asking_prices_included':False,'living_area_rank_by_observed_n':dongorder.index(r['legal_dong_name'])+1})
        reps.append(r)
    csvout('representatives.csv',reps);save('representatives.json',{'revision':OUT.name,'rows':reps})
    assets=json.loads((EPISODE/'visual/top20-8min-v2/maps/map_assets.json').read_text(encoding='utf-8'))['assets']
    official=pd.read_parquet(OFFICIAL/'capital_official_geometry.parquet')
    layers=[];writer=[]
    for p in prices:
        rid=p['region_id'];r=next(r for r in reps if r['region_id']==rid);a=next(a for a in assets if a['region_id']==rid)
        geom=json.loads(gzip.decompress((EPISODE/a['geometry_file']).read_bytes()))
        o=official[official.HSMP_INNB.astype(str)==str(r['official_id'])].iloc[0]
        rings=shape_rings(int(o.record_index))
        assert sum(in_ring(o.x_5179,o.y_5179,ring) for ring in rings)%2==1
        assert any(in_geojson(float(r['longitude']),float(r['latitude']),f['geometry']) for f in geom['features'])
        layers.append({'region_id':rid,'scene_id':p['scene_id'],'rank':p['rank'],'region':p['region'],'province':p['province'],
            'boundary_file':'../snapshots/boundary_'+rid+'_20241001.geojson.gz','boundary_sha256':sha256(HERE/'snapshots'/('boundary_'+rid+'_20241001.geojson.gz')),
            'boundary_version':'2024-10-01','boundary_attribution':a['attribution'],'boundary_license':a['license'],
            'regional_fill_value_manwon':p['median_manwon'],'regional_n':p['n'],'contract_period_start':'2026-05-01','contract_period_end':'2026-10-31','as_of_date':'2026-11-03',
            'reporting_complete':False,'october_reporting_ongoing':True,'display_title':'11월 3일 조회 · 5~10월 계약 실거래',
            'display_condition':f'전용 83~85㎡ · {p["n"]:,}건 · 10월 신고 진행',
            'marker':{'name':r['api_apt_name'],'api_apt_seq':r['api_complex_id'],'local_apt_id':r['apt_id'],'official_id':str(r['official_id']),
                'longitude':float(r['longitude']),'latitude':float(r['latitude']),'coordinate_verified':True,'point_in_2024_target_geometry':True,'point_in_official_polygon':True,
                'coordinate_source':r['coordinate_source'],'verified_address':r['official_road_address'],'n':r['n'],'median_manwon':r['median_manwon'],
                'label':'단지 사례','represents_gu_typical_price':False,'point_semantics':'단지 내부 대표점; 출입구·세대 위치가 아닙니다.'}})
        writer.append({**p,'regional_claim_id':'V3_API_PRICE_'+rid,'representative':{'claim_id':'V3_API_APT_'+rid,'name':r['api_apt_name'],'api_apt_seq':r['api_complex_id'],'legal_dong_name':r['legal_dong_name'],'n':r['n'],'median_manwon':r['median_manwon'],'label':'별도 단지 사례','represents_gu_typical_price':False},
            'regional_sentence':f'{p["region"]}의 5~10월 계약분 가운데 11월 3일 조회된 전용 83~85㎡ 유효 거래 {p["n"]:,}행의 중위값은 {p["median_manwon"]:,.1f}만원입니다.',
            'representative_sentence':f'{r["legal_dong_name"]}의 {r["api_apt_name"]}는 같은 조건으로 {r["n"]}행, 중위값 {r["median_manwon"]:,.1f}만원인 별도 단지 사례입니다.'})
    save('writer_price_values.json',{'revision':OUT.name,'price_lock':'official_api_asof_2026-11-03','intro_caveat':'가격은 11월 3일 조회한 5~10월 계약 실거래를 비교합니다. 10월 신고는 아직 진행 중입니다.',
        'ranking_basis_caveat':'신혼부부 순위는 2024년 통계 구역과 자료의 한계를 유지합니다. 가격 조사 시점과 순위 기준 시점은 다릅니다.',
        'no_asking_prices':True,'regions':writer})
    save('map_price_inputs.json',{'revision':OUT.name,'as_of_date':'2026-11-03','layers':layers})
    save('methodology.json',{'revision':OUT.name,'as_of_date':'2026-11-03','contract_period':['2026-05-01','2026-10-31'],
        'all_requested_pages_received':True,'reporting_complete':False,'october_reporting_ongoing':True,
        'n_definition':'요청 범위 API 응답 중 면적·금액·해제 필터를 통과한 유효 행 수입니다. 상위 master의 중복 정리 결과를 쓰지 않았습니다.',
        'area_filter':'83<=exclusive_m2<=85; 양끝 포함','floor_filter':'전체 층','unit':'만원','statistic':'원금액 중위값; 짝수 행수는 가운데 두 금액 평균',
        'cancellation_rule':'cdealType 또는 cdealDay 값이 있는 행은 제외합니다. 해제·정상 행의 공개 필드가 같아도 고유 계약ID가 없어 같은 계약으로 확정하지 않습니다. 동일 계약임이 입증되지 않은 정상 행은 삭제하지 않고 대조 후보로 보존합니다.',
        'paired_original_removed_n':0,'possible_cancellation_match_candidates_all_areas':len(paired),'candidate_groups_with_multiple_normal_rows':sum(r['ambiguous_multiple_normal_rows'] for r in paired),
        'identical_normal_rows':'동일 계약일·층·금액의 복수 정상 행도 별도 세대일 수 있어 일괄 중복 제거하지 않습니다. 페이지별 응답은 한 번만 사용했습니다.',
        'late_cancellation_limit':'조회 이후 사후 해제·정정·지연신고는 반영되지 않습니다. 계약월이 끝났다고 전수 신고가 완료된 것은 아닙니다.',
        'direct_brokered':'dealingGbn 원필드를 보존했고 중개·직거래를 함께 집계했습니다. 유형별 n도 제공합니다.',
        'R01':'2024 서구 구역으로 고정합니다. 28260의 5월 응답0과 28275/28290의 과거5월 유효 응답을 비교한 뒤 총괄 지시에 따라 현행 두 코드의 전기간 응답을 합산했습니다. 구코드 응답을 더하지 않았습니다.',
        'representative_selection':'대표단지는 생활권·주택규모·검증 가능성을 고려한 별도 사례입니다. 해당 구 전체의 전형적 주택 가격이나 매수 추천으로 표현하지 않습니다.',
        'asking_prices_included':False,'api_attempts':len(ledger['requests']),'request_limit':200,'raw_response_rows':len(rawrows),'valid_area_rows':len(valid),
        'observed_contract_min':min(vf.deal_date),'observed_contract_max':max(vf.deal_date),
        'prior_pack':'상위 폴더의 regional_prices.csv 등은 4~9월 로컬 예비본입니다. 이 버전과 혼용하지 않습니다.'})
    save('source_manifest.json',{'revision':OUT.name,'responses':response_inputs,'request_ledger':'../api_request_log.json',
        'code_probe_evidence':'../api_geography_feasibility.json','as_of_first_response':min(r['started_at'] for r in successful),'as_of_last_response':max(r['finished_at'] for r in successful),
        'source_url':'https://www.data.go.kr/data/15126468/openapi.do?recommendDataYn=Y','credential_values_exported':False})
    print(json.dumps({'pack':str(OUT),'regions':len(prices),'raw_n':len(rawrows),'valid_n':len(valid),'paired_original_removed_n':0,'possible_match_candidates_all_areas':len(paired),'representatives':len(reps),'rep_n_min':min(r['n'] for r in reps),'writer_values':'writer_price_values.json','map_inputs':'map_price_inputs.json'},ensure_ascii=False))
