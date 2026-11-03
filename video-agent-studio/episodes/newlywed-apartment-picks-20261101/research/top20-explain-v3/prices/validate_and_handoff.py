"""고정 스냅샷 재계산·기록 무결성 점검 후 총괄에 인계합니다."""
import csv
import gzip
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
from inspect_freshness import HERE, ROOT, EPISODE, records, sha256, write
from calculate_prices import in_ring, in_geojson


if __name__=='__main__':
    os.chdir(HERE)
    checks=[]
    def check(name,condition,evidence):
        checks.append({'check':name,'result':'passed' if condition else 'failed','evidence':evidence})
        if not condition:raise AssertionError(name)
    source_manifest=json.loads((HERE/'source_manifest.json').read_text(encoding='utf-8'))
    for entry in source_manifest['inputs']:
        check('입력 SHA256: '+entry['path'],sha256(ROOT/entry['path'])==entry['sha256'],entry['sha256'])
    for entry in source_manifest['frozen_snapshots']:
        check('스냅샷 SHA256: '+entry['path'],sha256(HERE/entry['path'])==entry['sha256'],entry['sha256'])
    original=json.loads((HERE/'freshness.json').read_text(encoding='utf-8'))['files']
    originalhash={r['path']:r['sha256'] for r in original}
    check('첫 최신성 조사 후 원천 동일',all(originalhash[r['path']]==r['sha256'] for r in source_manifest['inputs'] if r['path'] in originalhash),'freshness.json ↔ source_manifest.json')
    con=duckdb.connect(':memory:')
    prices=json.loads((HERE/'regional_prices.json').read_text(encoding='utf-8'))['rows']
    reps=json.loads((HERE/'representatives.json').read_text(encoding='utf-8'))['rows']
    source=pd.read_parquet(HERE/'snapshots/trade_events_20regions.parquet')
    scope=pd.read_csv(HERE/'scope_codes.csv',dtype=str)
    source['region_id']=source.sigungu_code.map(dict(zip(scope.current_code,scope.region_id)))
    ok=source[(source.deal_date<'2026-10-01') & source.area_m2.between(83,85) & (source.deal_amount>0) & (source.is_canceled==False) & source.cancel_date.isna()]
    check('고정 20지역·21코드',len(prices)==20 and len(scope)==21 and len(set(scope.region_id))==20,'R01 두 코드, 나머지 각 한 코드')
    check('R01 분할 코드 중복 없음',set(scope[scope.region_id=='R01'].current_code)=={'28275','28290'} and source.deal_hash.duplicated().sum()==0,'구코드 28260 중복 합산 없음; 전체 snapshot deal_hash 고유')
    sql_rows=records(con,(HERE/'aggregate.sql').read_text(encoding='utf-8'))
    for p in prices:
        r=ok[ok.region_id==p['region_id']]
        m=statistics.median(int(v) for v in r.deal_amount)
        sql=next(s for s in sql_rows if s['region_id']==p['region_id'])
        check('독립 중위값·n '+p['region_id'],m==p['median_manwon']==sql['median_manwon'] and len(r)==p['n']==sql['n'],f'statistics.median={m}; n={len(r)}; DuckDB SELECT 일치')
    check('해제 제외와 합계',sum(p['n'] for p in prices)==len(ok)==14182 and sum(p['canceled_excluded_n'] for p in prices)==350,'14,532건 중 해제 표시 350건 제외, 14,182건')
    sql_text=(HERE/'aggregate.sql').read_text(encoding='utf-8')
    check('위치 미확인 거래도 지역 집계에 포함',
          all(name not in sql_text for name in ['apt_id_map','apt_index','latitude','longitude']) and sum(r['n'] for r in sql_rows)==len(ok),
          'SQL은 단지·좌표 테이블 없이 scope 코드만 결합하며 전체 조건부 원거래 행수가 일치합니다.')
    official=pd.read_parquet(HERE/'snapshots/representative_official_geometry_points.parquet')
    rings=json.loads((HERE/'snapshots/representative_official_polygon_rings.json').read_text(encoding='utf-8'))
    layers=json.loads((HERE/'map_price_inputs.json').read_text(encoding='utf-8'))['layers']
    check('대표 사례 20개·최소 5건',len(reps)==20 and min(r['n'] for r in reps)>=5,'모든 지역 한 단지, 모든 표본 n>=5')
    for r in reps:
        rows=ok[ok.apt_id==r['apt_id']]
        check('대표 사례 가격 '+r['region_id'],statistics.median(int(x) for x in rows.deal_amount)==r['median_manwon'] and len(rows)==r['n'],r['apt_id'])
        o=official[official.HSMP_INNB==r['official_id']].iloc[0]
        polygon=rings[str(r['official_record_index'])]
        raw_inside=sum(in_ring(o.x_5179,o.y_5179,ring) for ring in polygon)%2==1
        layer=next(a for a in layers if a['region_id']==r['region_id'])
        geom=json.loads(gzip.decompress((HERE/layer['boundary_file']).read_bytes()))
        target_inside=any(in_geojson(r['longitude'],r['latitude'],f['geometry']) for f in geom['features'])
        check('공식 도형·2024 경계 내부 '+r['region_id'],raw_inside and target_inside and r['official_name_exact'] and r['official_id_unique_among_observed_apts'] and r['coordinate_transform_error_m']<0.1,r['official_id'])
    facts=json.loads((HERE/'facts.json').read_text(encoding='utf-8'))
    price_claims=[r for r in facts['claims'] if 'median_manwon' in r]
    check('가격 주장 현재가 승격 없음',len(price_claims)==40 and all(r['status']=='qualified' and r['current_price_verified']==False for r in price_claims),'가격 주장 40개 qualified, 현재가 검증 0개')
    check('주장 필수 근거 필드',all(all(k in r for k in ['claim_id','sentence','source_url','source_file','evidence_location','reference_date','checked_at','status']) for r in facts['claims']),'63개 주장 전수 확인')
    ledger=json.loads((HERE/'api_request_log.json').read_text(encoding='utf-8'))
    check('API 호출 상한·실패 후 중단',len(ledger['requests'])==1 and ledger['requests'][0]['status']=='network_error' and not list((HERE/'raw').glob('*.xml')),'1회 ConnectionError, HTTP 원응답 0개, 재시도 0회')
    # 값은 출력·기록하지 않고 산출물 내 포함 여부만 확인합니다.
    credentials=json.loads((ROOT/'config/secrets.json').read_text(encoding='utf-8-sig'))
    secrets=[str(v).encode() for k,v in credentials.items() if isinstance(v,str) and len(v)>=16 and any(t in k.lower() for t in ['key','secret','token','password'])]
    for line in (ROOT/'.env').read_text(encoding='utf-8-sig').splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            k,v=line.split('=',1)
            if len(v.strip().strip('"\''))>=16 and any(t in k.lower() for t in ['key','token','secret','password']):secrets.append(v.strip().strip('"\'').encode())
    leakfiles=[]
    for p in HERE.rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts:
            data=p.read_bytes()
            if any(v in data for v in secrets):leakfiles.append(str(p.relative_to(HERE)))
    check('자격증명 값 미포함',not leakfiles,{'matches':len(leakfiles)})
    flat=[]
    for r in facts['claims']:
        flat.append({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in r.items()})
    pd.DataFrame(flat).to_csv(HERE/'facts.csv',index=False,encoding='utf-8-sig',lineterminator='\n')
    table=[]
    for p in prices:
        r=next(r for r in reps if r['region_id']==p['region_id'])
        table.append({**{k:p[k] for k in ['region_id','scene_id','rank','province','region','period_start','period_end','n','complex_count','median_manwon','first_contract','last_contract','canceled_excluded_n']},
            'representative_apt_id':r['apt_id'],'representative_official_id':r['official_id'],
            'representative_name':r['apt_name_raw'],'representative_median_manwon':r['median_manwon'],'representative_n':r['n'],
            'representative_address':r['official_road_address'],'longitude':r['longitude'],'latitude':r['latitude'],
            'coordinates_verified':r['coordinate_verified'],'point_in_2024_target_geometry':r['point_in_2024_target_geometry'],
            'current_price_verified':False,'price_status':'qualified_historical_observations','area_filter':'83<=exclusive_m2<=85','floor_filter':'전체 층','transaction_type':'아파트 매매; 중개/직거래 구분 미확인','cancel_filter':p['cancel_filter'],'unit':'만원'})
    pd.DataFrame(table).to_csv(HERE/'price_table20.csv',index=False,encoding='utf-8-sig',lineterminator='\n')
    stamp=datetime.now(ZoneInfo('Asia/Seoul')).isoformat()
    write('validation.json',{'checked_at':stamp,'status':'passed_with_current_price_gap','checks':checks,
        'continuous_playback_performed':False,'actual_listening_performed':False,'independent_qa_performed':False,
        'scope':'데이터 집계·근거·좌표·파일 무결성 자체 점검입니다. 독립 QA 및 영상 검수가 아닙니다.'})
    outputs=['freshness.json','freshness_20regions.csv','facts.json','facts.csv','price_table20.csv','regional_prices.json','regional_prices.csv',
        'representatives.json','representatives.csv','representative_transaction_evidence.csv','complex_candidates_audit.csv','map_price_inputs.json',
        'methodology.json','asking_prices.json','source_manifest.json','scope_codes.csv','aggregate.sql','extract_snapshot.sql',
        'official_sources.json','api_request_log.json','api_feasibility.json','validation.json','requested_window_incomplete_observations.csv','검증범위.txt',
        'inspect_freshness.py','calculate_prices.py','refresh_official.py','finalize_evidence.py','validate_and_handoff.py','calculation_summary.json',
        'issue_PRICE-FRESHNESS-V3.json','issue_PRICE-API-CONNECTION-V3.json']
    artifact_list=[{'path':name,'sha256':sha256(HERE/name),'bytes':(HERE/name).stat().st_size} for name in outputs]
    write('artifact_manifest.json',{'created_at':stamp,'outputs':artifact_list})
    write('handoff.json',{'task_id':'top20-explain-v3-price-research','role':'research','status':'bounded_research_complete_with_current_price_gap',
        'input_revisions':{'scope':'research/top20-8min-v2/top20.json','scope_sha256':sha256(EPISODE/'research/top20-8min-v2/top20.json'),
            'authorization_event':'output/telegram_conversation/inbox/718066312.json','state_revision_read':'top20-enhance-v2',
            'source_versions':'source_manifest.json','frozen_snapshot_versions':'source_manifest.json frozen_snapshots'},
        'outputs':['price_table20.csv','facts.json','map_price_inputs.json','검증범위.txt','source_manifest.json','artifact_manifest.json','validation.json'],
        'affected_scene_ids':['S%03d'%i for i in range(3,23)],'checks':[
            {'check':'20지역 중위값·표본수·해제 제외','result':'passed','evidence':'validation.json; 14,182건·해제 350건 제외'},
            {'check':'20단지 n>=5·공식ID·주소·좌표·2024 경계','result':'passed','evidence':'representatives.csv; map_price_inputs.json'},
            {'check':'요청한 5~10월 최신 거래 API 확보','result':'failed','evidence':'api_request_log.json; 첫 1회 ConnectionError 후 중단'},
            {'check':'현재 호가·판매 상태','result':'unverified','evidence':'asking_prices.json; 현재 검증 0건'}],
        'open_issue_ids':['PRICE-FRESHNESS-V3','PRICE-API-CONNECTION-V3'],
        'unresolved':['5~10월 최신 원응답','사후 해제 갱신','중개/직거래 필드','현재 호가·판매 상태','상위 master 중복 정리 전 거래 복원'],
        'handoff_note':'4~9월 관측값으로 대체할지 총괄 판단이 필요합니다. 가격은 모두 qualified이며 현재가로 쓰지 않습니다. 지도 마커는 조건을 통과한 단지 내부 대표점입니다.',
        'next_role':['director','writer','visual','qa'],'direct_peer_messages_sent':False,'shared_state_modified':False})
    print(json.dumps({'checks_passed':len(checks),'regions':len(prices),'transaction_n':len(ok),'representatives':len(reps),'minimum_rep_n':min(r['n'] for r in reps),'api_attempts':len(ledger['requests']),'current_price_claims_verified':0,'handoff':'handoff.json'},ensure_ascii=False))
