"""최신 가격팩의 재현 SQL·사실 근거·독립 대조·인계 포인터를 고정합니다."""
import json
import os
import statistics
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import duckdb
import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parent))
from inspect_freshness import HERE, ROOT, EPISODE, sha256
from calculate_prices import OFFICIAL, shape_rings

OUT=HERE/'final-api-20261103-v2'


def save(folder,name,data):
    (folder/name).write_text(json.dumps(data,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')


if __name__=='__main__':
    os.chdir(OUT)
    stamp=datetime.now(ZoneInfo('Asia/Seoul')).isoformat()
    prices=json.loads((OUT/'regional_prices.json').read_text(encoding='utf-8'))['rows']
    reps=json.loads((OUT/'representatives.json').read_text(encoding='utf-8'))['rows']
    writer=json.loads((OUT/'writer_price_values.json').read_text(encoding='utf-8'))
    layers=json.loads((OUT/'map_price_inputs.json').read_text(encoding='utf-8'))
    method=json.loads((OUT/'methodology.json').read_text(encoding='utf-8'))
    method.pop('paired_multiple_normal_ambiguity_n',None)
    method['candidate_groups_with_multiple_normal_rows']=0
    method['prior_v1_correction']='v1은 공개 필드가 같은 정상행을 같은 계약으로 추정해 면적 구간 내136행을 추가 삭제했습니다. 고유 계약ID 근거가 없어 이 처리를 철회했습니다. v2는 공식 해제 표시만 제외하고 정상행은 모두 보존합니다. v1 값은 영상에 사용하지 않습니다.'
    save(OUT,'methodology.json',method)
    scope=pd.read_csv(HERE/'scope_codes.csv',dtype=str)
    currentnames=dict(zip(scope.current_code,scope.current_code_name))
    for layer in layers['layers']:
        rep=next(r for r in reps if r['region_id']==layer['region_id'])
        layer['marker']['current_district_name']=currentnames[str(rep['api_query_code'])]
        layer['marker']['query_lawd_cd']=str(rep['api_query_code'])
        if layer['region_id']=='R01':layer['display_region']='서구(2024 범위: 현재 서해구+검단구)'
    save(OUT,'map_price_inputs.json',layers)
    sql="""-- final-api-20261103-v2 폴더를 작업 디렉터리로 사용합니다.
-- 공개 API의 정상 복수 행을 중복 제거하지 않습니다. 고유 계약ID 기반 추가 삭제는 없습니다.
SELECT region_id, count(*) AS n, count(DISTINCT api_complex_id) AS complex_count,
       median(deal_amount_manwon) AS median_manwon,
       min(deal_date) AS first_observed_contract, max(deal_date) AS last_observed_contract
FROM read_parquet('api_rows_all.parquet')
WHERE deal_date >= '2026-05-01' AND deal_date <= '2026-10-31'
  AND area_m2 BETWEEN 83 AND 85 AND deal_amount_manwon > 0
  AND coalesce(cdealType, '') = '' AND coalesce(cdealDay, '') = ''
GROUP BY region_id ORDER BY region_id;
"""
    (OUT/'aggregate.sql').write_text(sql,encoding='utf-8')
    con=duckdb.connect(':memory:')
    calc=con.execute(sql).fetchall()
    independent_path=EPISODE/'qa/top20-explain-v3/independent_price_rollup.json'
    independent=json.loads(independent_path.read_text(encoding='utf-8'))
    byregion={r['region_id']:r for r in independent['regions']}
    byapt={(r['region_id'],r['apt_seq']):r for r in independent['complexes']}
    vf=pd.read_parquet(OUT/'api_rows_valid83_85.parquet')
    comparisons=[]
    for p in prices:
        sqlrow=next(r for r in calc if r[0]==p['region_id'])
        independent_region=byregion[p['region_id']]
        assert sqlrow[1]==p['n']==independent_region['n']
        assert sqlrow[3]==p['median_manwon']==independent_region['median_manwon']
        own=vf[vf.region_id==p['region_id']]
        assert statistics.median(own.deal_amount_manwon)==p['median_manwon']
        rep=next(r for r in reps if r['region_id']==p['region_id'])
        other=byapt[(p['region_id'],rep['api_complex_id'])]
        assert (other['n'],other['median_manwon'])==(rep['n'],rep['median_manwon'])
        assert rep['n']>=5
        comparisons.append({'region_id':p['region_id'],'regional_n_match':True,'regional_median_match':True,'representative_api_apt_seq':rep['api_complex_id'],'representative_n_match':True,'representative_median_match':True})
    assert sum(p['n'] for p in prices)==len(vf)==14303
    assert sum(p['canceled_row_excluded_n'] for p in prices)==550
    assert sum(p['original_cancellation_pair_removed_n'] for p in prices)==0
    assert vf.api_row_id.nunique()==len(vf)
    assert vf.api_complex_id.nunique()==2304
    assert sum(p['brokered_n']+p['direct_n']+p['trade_type_other_or_missing_n'] for p in prices)==14303
    assert all(not p['reporting_complete'] and p['october_reporting_ongoing'] for p in prices)
    official=pd.read_parquet(OFFICIAL/'capital_official_geometry.parquet')
    ids={str(r['official_id']) for r in reps}
    selected=official[official.HSMP_INNB.astype(str).isin(ids)].copy()
    selected.to_parquet(OUT/'representative_official_points.parquet',index=False)
    save(OUT,'representative_official_polygon_rings.json',{str(int(r.record_index)):shape_rings(int(r.record_index)) for r in selected.itertuples()})
    vf[vf.api_complex_id.isin([r['api_complex_id'] for r in reps])].to_csv(OUT/'representative_api_evidence.csv',index=False,encoding='utf-8-sig',lineterminator='\n')
    facts=[];table=[]
    source_url='https://www.data.go.kr/data/15126468/openapi.do?recommendDataYn=Y'
    for p in prices:
        rid=p['region_id'];r=next(r for r in reps if r['region_id']==rid);w=next(w for w in writer['regions'] if w['region_id']==rid)
        common={'source_url':source_url,'source_file':'api_rows_all.parquet','reference_date':'2026-11-03 조회 / 2026-05-01~10-31 계약','checked_at':stamp,
            'status':'verified','verification_scope':'보존된 공식 API 응답의 조회 시점 유효 행 집계입니다. 전수 신고 완결 또는 현재 호가를 확인한 것이 아닙니다.',
            'as_of_date':'2026-11-03','contract_period':['2026-05-01','2026-10-31'],'area_filter':'83<=exclusive_m2<=85; 양끝 포함','floor_filter':'전체 층',
            'transaction_type':'아파트 매매; 중개·직거래 포함; dealingGbn 원필드 보존','unit':'만원','statistic':'원금액의 행별 동일 가중 중위값; 짝수는 가운데 두 값 평균',
            'cancellation_rule':'cdealType/cdealDay에 값이 있는 해제 행 제외; 정상 복수 행 보존; 같은 계약임이 입증되지 않은 추가 감산 없음',
            'reporting_complete':False,'october_reporting_ongoing':True,'asking_prices_included':False,'affected_scene_ids':[p['scene_id']]}
        facts.append({**common,'claim_id':'V3_API_PRICE_'+rid,'sentence':w['regional_sentence'],'region_id':rid,'n':p['n'],'median_manwon':p['median_manwon'],
            'evidence_location':f'api_rows_all.parquet region_id={rid}; aggregate.sql; regional_prices.csv; source_coverage.csv',
            'first_observed_contract':p['first_observed_contract'],'last_observed_contract':p['last_observed_contract'],'canceled_row_excluded_n':p['canceled_row_excluded_n']})
        facts.append({**common,'claim_id':'V3_API_APT_'+rid,'sentence':w['representative_sentence'],'region_id':rid,'api_apt_seq':r['api_complex_id'],'n':r['n'],'median_manwon':r['median_manwon'],
            'evidence_location':f'representative_api_evidence.csv api_complex_id={r["api_complex_id"]}; each row source_response + source_item_index_1based',
            'represents_gu_typical_price':False,'selection_reason':r['selection_reason'],'official_id':str(r['official_id'])})
        facts.append({'claim_id':'V3_API_COORD_'+rid,'sentence':f'{r["api_apt_name"]}의 지도점은 공식 단지 도형과 해당 2024년 구역 경계 안의 대표점입니다.',
            'source_url':'https://www.bigdata-realestate.kr/rebpp/usr/prd/prdInfoDetail.do?req_productId=1','source_file':'representative_official_points.parquet',
            'evidence_location':f'HSMP_INNB={r["official_id"]}; representative_official_polygon_rings.json; ../snapshots/boundary_{rid}_20241001.geojson.gz',
            'reference_date':'2025 단지 공간원천 / 2024-10-01 구역','checked_at':stamp,'status':'verified','affected_scene_ids':[p['scene_id']],
            'longitude':float(r['longitude']),'latitude':float(r['latitude']),'coordinate_source':r['coordinate_source'],'official_name_exact':True,
            'coordinate_transform_error_m':float(r['coordinate_transform_error_m']),'point_in_official_polygon':True,'point_in_2024_target_geometry':True,
            'point_semantics':'단지 내부 대표점입니다. 출입구·세대 위치 또는 실제 현장 방문 확인이 아닙니다.'})
        table.append({**p,'representative_name':r['api_apt_name'],'representative_api_apt_seq':r['api_complex_id'],'representative_n':r['n'],'representative_median_manwon':r['median_manwon'],
            'representative_official_id':str(r['official_id']),'longitude':float(r['longitude']),'latitude':float(r['latitude']),'represents_gu_typical_price':False})
    save(OUT,'facts.json',{'revision':OUT.name,'claims':facts,'as_of_date':'2026-11-03','reporting_complete':False,'contract_period':['2026-05-01','2026-10-31']})
    pd.DataFrame([{k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in r.items()} for r in facts]).to_csv(OUT/'facts.csv',index=False,encoding='utf-8-sig',lineterminator='\n')
    pd.DataFrame(table).to_csv(OUT/'price_table20.csv',index=False,encoding='utf-8-sig',lineterminator='\n')
    # 이전 이슈의 발생 기록은 보존하고 현재 해결 상태를 덧붙입니다.
    for filename in ['issue_PRICE-FRESHNESS-V3.json','issue_PRICE-API-CONNECTION-V3.json']:
        d=json.loads((HERE/filename).read_text(encoding='utf-8'))
        d.update(status='resolved_by_official_api_refresh',resolved_at=stamp,resolution='권한 상승 수동 확인 후 129회 상한 내 시도로 126코드·월 전체 페이지 수신. v2는 해제 표시만 제외한 14,303행입니다.',resolution_artifact='final-api-20261103-v2/writer_price_values.json')
        save(HERE,filename,d)
    save(HERE/'final-api-20261103-v1','VERSION_STATUS.json',{'status':'superseded_do_not_use_for_video','replacement':'../final-api-20261103-v2','reason':'고유 계약ID 없는 공개 필드 매칭으로 정상 136행을 추가 제외한 v1 방식은 철회했습니다. 민감도·경위 기록으로만 보존합니다.'})
    save(HERE,'ACTIVE_PRICE_PACK.json',{'active':'final-api-20261103-v2','contract_period':['2026-05-01','2026-10-31'],'as_of_date':'2026-11-03','reporting_complete':False,'october_reporting_ongoing':True,
        'n':14303,'excluded_canceled_rows':550,'extra_active_rows_removed':0,'prior_local_pack':'상위 폴더의 4~9월 데이터는 예비 보존본입니다. writer와 visual은 active 폴더만 사용합니다.'})
    validation={'status':'passed','checked_at':stamp,'regions_compared':20,'representatives_compared':20,'raw_rows':44984,'valid_n':14303,'excluded_canceled_rows':550,'extra_active_rows_removed':0,
        'unique_api_apt_seq_count':2304,'minimum_rep_n':min(r['n'] for r in reps),'independent_source':str(independent_path.relative_to(ROOT)),
        'independent_source_sha256':sha256(independent_path),'independent_method':'부모가 원 XML 직접 파싱한 결과와 지역·단지 n 및 중위값 40쌍 모두 일치합니다.',
        'comparisons':comparisons,'all_requested_pages_received':True,'reporting_complete':False,'october_reporting_ongoing':True,
        'independent_video_qa':False,'audio_created':False,'render_created':False}
    # 키 값은 출력하지 않고 로컬 산출물에 포함되지 않았는지만 확인합니다.
    credentials=json.loads((ROOT/'config/secrets.json').read_text(encoding='utf-8-sig'))
    needles=[v.encode() for k,v in credentials.items() if isinstance(v,str) and len(v)>=16 and any(w in k.lower() for w in ['key','token','secret'])]
    assert not any(any(v in p.read_bytes() for v in needles) for p in OUT.rglob('*') if p.is_file())
    validation['credential_value_matches']=0
    save(OUT,'validation.json',validation)
    dependencies=[OFFICIAL/'capital_official_geometry.parquet',OFFICIAL/'raw/APHUS_HSMP_CNTC_INFO.shp',OFFICIAL/'raw/APHUS_HSMP_CNTC_INFO.shx',
        HERE/'complex_candidates_audit.csv',HERE/'scope_codes.csv',HERE/'build_final_api_pack.py',HERE/'finish_final_api_pack.py',HERE/'refresh_official.py',
        EPISODE/'research/top20-8min-v2/top20.json',EPISODE/'visual/top20-8min-v2/maps/map_assets.json',independent_path]
    save(OUT,'reproduction_manifest.json',{'version':OUT.name,'dependencies':[{'path':str(p.relative_to(ROOT)),'sha256':sha256(p)} for p in dependencies],
        'artifacts':[{'path':str(p.relative_to(OUT)),'bytes':p.stat().st_size,'sha256':sha256(p)} for p in sorted(OUT.iterdir()) if p.is_file() and p.name not in ['reproduction_manifest.json','handoff.json']],
        'raw_response_manifest':'source_manifest.json','sql':'aggregate.sql','network_calls_for_recalculation':0})
    handoff={'task_id':'top20-explain-v3-prices','role':'research','status':'complete_asof_snapshot_with_reporting_limits','revision':OUT.name,
        'input_revisions':{'ranking':'top20-8min-v2','source_responses':'source_manifest.json','reproduction':'reproduction_manifest.json','independent_qa_price_values':str(independent_path.relative_to(ROOT))},
        'outputs':['writer_price_values.json','map_price_inputs.json','price_table20.csv','facts.json','facts.csv','methodology.json','source_coverage.csv','aggregate.sql','source_manifest.json','reproduction_manifest.json','validation.json'],
        'affected_scene_ids':[p['scene_id'] for p in prices],
        'checks':[{'check':'20지역·20단지 n/중위값 부모 독립 집계 대조','result':'passed','evidence':'validation.json'},
            {'check':'129회 시도·126코드월 전체 페이지·원응답 해시','result':'passed','evidence':'../api_collection_receipt.json; source_manifest.json'},
            {'check':'정상행 보존·해제 표시만 제외','result':'passed','evidence':'유효14,303행, 해제550행, 추가 정상행 삭제0행'},
            {'check':'20지도점 공식 주소/명칭/도형/2024경계','result':'passed','evidence':'map_price_inputs.json; representative_official_points.parquet'}],
        'open_issue_ids':[],'limitations':['11월3일 조회 당시 자료입니다. 10월 신고 진행 중이며 전수 완결이 아닙니다.','조회 이후 해제·정정·지연신고는 미반영입니다.','단지는 별도 사례이며 구 전체의 전형가격이 아닙니다.','호가·매물은 포함하지 않습니다.'],
        'next_role':['writer Pascal','visual','director','qa'],'script_gate_required':True,'tts_or_render_executed':False,'shared_state_modified':False}
    save(OUT,'handoff.json',handoff)
    save(HERE,'handoff.json',{**handoff,'active_pack':'final-api-20261103-v2','outputs':['final-api-20261103-v2/'+p for p in handoff['outputs']],
        'summary':'11월3일 조회 5~10월 계약 실거래 14,303유효행. 지역20/대표20 n·중위값 독립집계 일치. 10월신고 진행을 명시하고 v1과 4~9월 예비본은 영상값에서 제외합니다.'})
    print(json.dumps({'pack':str(OUT),'status':validation['status'],'regions':20,'valid_n':14303,'excluded_canceled_rows':550,'extra_active_rows_removed':0,'representative_n_min':validation['minimum_rep_n'],'independent_region_and_apt_matches':40,'reporting_complete':False},ensure_ascii=False))
