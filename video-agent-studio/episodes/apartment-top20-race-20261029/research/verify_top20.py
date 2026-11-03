"""별도 NumPy 정렬/중앙값 알고리즘으로 79개 시점 전체 풀과 원행을 검산한다.

제작 담당과 다른 사람의 독립 QA를 수행했다는 의미는 아니다.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
S=ROOT/'video-agent-studio/episodes/capital-10eok-map-20261017/research/source-completion-v1'
E=ROOT/'analysis/housing_growth_2006/regional_expansion_v1'


def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):
            h.update(b)
    return h.hexdigest()


def save(name,v):
    (OUT/name).write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf8')


def main():
    data=json.loads((OUT/'data.json').read_text(encoding='utf8'))
    account=json.loads((OUT/'row_accounting.json').read_text(encoding='utf8'))
    for x in account['source_inputs']:
        assert digest(ROOT/x['path'])==x['sha256'], '입력 해시 변경'
    m=pd.read_parquet(S/'episode_84_source_rows.parquet',columns=['complex_id','apt_seq','sigungu_code',
        'area_m2','deal_date','deal_amount','is_canceled','included_price_analysis',
        'source_file','source_filtered_item_index','source_index_basis'])
    e=pd.read_parquet(E/'expansion_normalized.parquet',columns=['apt_id','sigungu_code','area_m2','deal_date','deal_amount',
        'is_canceled','parse_error','id_fallback'])
    # 집계 스크립트를 import/호출하지 않고 독립적으로 유효 조건을 적용한다.
    m=m[m.included_price_analysis.eq(True)&m.is_canceled.eq(False)&
        (m.area_m2>=84)&(m.area_m2<85)&(m.deal_amount>0)&
        (m.deal_date>=pd.Timestamp('2006-01-01'))&(m.deal_date<pd.Timestamp('2026-07-01'))&
        m.complex_id.str.fullmatch(r'rtms:\d{5}-\d+').fillna(False)&m.complex_id.eq('rtms:'+m.apt_seq)].copy()
    e=e[e.is_canceled.eq(False)&e.parse_error.eq(False)&e.id_fallback.eq(False)&
        (e.area_m2>=84)&(e.area_m2<85)&(e.deal_amount>0)&
        (e.deal_date>=pd.Timestamp('2006-01-01'))&(e.deal_date<pd.Timestamp('2026-07-01'))&
        ~e.sigungu_code.isin(['27720','47720'])&e.apt_id.str.fullmatch(r'api:\d{5}-\d+').fillna(False)].copy()
    assert len(m)==account['master_included_rows'] and len(e)==account['expansion_included_rows']
    m['id']=m.complex_id
    e['id']=e.apt_id.map(lambda s:'rtms:'+s[4:])
    assert not set(m.sigungu_code.str[:2])&set(e.sigungu_code.str[:2])
    chunks=[]
    for source,g in [(0,m),(1,e)]:
        x=g[['id','deal_amount','deal_date']].copy()
        x['input_row']=g.index.to_numpy()
        x['source']=source
        chunks.append(x)
    rows=pd.concat(chunks,ignore_index=True)
    ids=rows.id.to_numpy()
    price=rows.deal_amount.to_numpy()
    quarters=rows.deal_date.dt.to_period('Q').astype('int64').to_numpy()
    inputrow=rows.input_row.to_numpy()
    source=rows.source.to_numpy()
    assert len(rows)==2153830==data['meta']['actual_included_transactions']
    assert rows.id.nunique()==12470==data['meta']['actual_collected_complexes']
    expected_periods=list(map(str,pd.period_range('2006Q4','2026Q2',freq='Q')))
    assert [f['period'] for f in data['frames']]==expected_periods
    previous,ever,events,leader_changes={},set(),[],[]
    median_evidence=[]
    eligible_summary=[]
    tie_groups=0
    last_leader=None
    for frame in data['frames']:
        q=pd.Period(frame['period'])
        assert frame['window_start']==str(q-3) and frame['window_end']==str(q)
        assert frame['top20']==frame['top'] and len(frame['top20'])==20
        ix=np.flatnonzero((quarters>=q.ordinal-3)&(quarters<=q.ordinal))
        order=np.lexsort((inputrow[ix],source[ix],price[ix],ids[ix]))
        si=ix[order]
        sorted_ids=ids[si]
        starts=np.r_[0,np.flatnonzero(sorted_ids[1:]!=sorted_ids[:-1])+1]
        ends=np.r_[starts[1:],len(si)]
        n=ends-starts
        lower=starts+(n-1)//2
        upper=starts+n//2
        med=(price[si[lower]].astype(float)+price[si[upper]].astype(float))/2
        groupids=sorted_ids[starts]
        keep=np.flatnonzero(n>=5)
        fullorder=sorted(keep,key=lambda j:(-med[j],previous.get(groupids[j],float('inf')),groupids[j]))
        expected=[str(groupids[j]) for j in fullorder[:20]]
        actual=[r['id'] for r in frame['top20']]
        assert actual==expected, (frame['period'],'全体候補TOP20相違')
        assert len(fullorder)==frame['eligible_complexes']
        assert len(ix)==frame['window_transactions']
        assert set(actual)<=set(data['complexes'])
        eligible_summary.append(dict(period=frame['period'],eligible=len(fullorder)))
        tie_groups+=sum(med[fullorder[j]]==med[fullorder[j-1]] for j in range(1,20))
        if actual[0]!=last_leader:
            leader_changes.append((frame['period'],actual[0]))
        last_leader=actual[0]
        for rank,(entry,j) in enumerate(zip(frame['top20'],fullorder[:20]),1):
            assert entry['median_manwon']==float(med[j]) and entry['n']==int(n[j]) and entry['rank']==rank
            meta=data['complexes'][entry['id']]
            assert all(entry[k]==meta[k] for k in ['name','display_name','location','region'])
            evidence=dict(period=frame['period'],id=entry['id'],claim_id=entry['claim_id'],rank=rank,n=int(n[j]),
                median_manwon=float(med[j]),window_start=str(q-3),window_end=str(q))
            for label,index in [('low',si[lower[j]]),('high',si[upper[j]])]:
                src=m if source[index]==0 else e
                original=src.loc[inputrow[index]]
                evidence[label+'_input_file']=(S/'episode_84_source_rows.parquet' if source[index]==0 else E/'expansion_normalized.parquet').relative_to(ROOT).as_posix()
                evidence[label+'_parquet_row_0based']=int(inputrow[index])
                evidence[label+'_price_manwon']=int(price[index])
                evidence[label+'_deal_date']=str(original.deal_date.date())
                if source[index]==0:
                    evidence[label+'_original_source_file']=original.source_file
                    evidence[label+'_original_source_item_index']=int(original.source_filtered_item_index)
                    evidence[label+'_original_source_index_basis']=original.source_index_basis
            median_evidence.append(evidence)
            if entry['id'] not in previous:
                events.append((frame['period'],entry['id'],'initial' if not ever else ('reentry' if entry['id'] in ever else 'first_entry')))
        previous={i:k for k,i in enumerate(actual,1)}
        ever.update(actual)
    s=data['summary']
    assert len(ever)==s['ever_top20_complexes']==127
    assert len(leader_changes)-1==s['leader_change_count']==13
    assert sum(t=='first_entry' for _,_,t in events)==s['first_entry_events']==107
    assert sum(t=='reentry' for _,_,t in events)==s['reentry_events']==197
    assert leader_changes==[(x['period'],x['id']) for x in [s['initial_leader']]+s['leader_changes']]
    identity=pd.read_parquet(S/'identity_catalog_complete.parquet')
    identity_checks=[]
    for i,v in data['complexes'].items():
        if i in identity.index:
            z=identity.loc[i]
            assert i=='rtms:'+v['apt_seq']
            assert v['name']==z['name'],(i,'단지명 불일치')
            assert v['sigungu_code'] in z.sigungu_codes
            assert len(z.sigungu_codes)==1 and len(z.legal_dong_codes)==1,(i,'후보 단지 식별 분기 필요')
            identity_checks.append(i)
    assert len(identity_checks)==127
    pd.DataFrame(median_evidence).to_csv(OUT/'median_evidence.csv',index=False,encoding='utf-8-sig')
    receipt=dict(status='passed',checked_at='2026-10-29',algorithm='NumPy lexsort 원거래 정렬 후 양쪽 중앙값; 전 단지 최소건수/순위 재선정',
        frames_checked=79,price_n_rank_claims_checked=1580,all_pool_rows_checked=len(rows),all_pool_complexes_checked=12470,
        top20_alias_matches=True,source_hashes_unchanged=True,future_transactions_excluded=True,
        no_zero_fill=True,no_forward_fill=True,canonical_identity_catalog_matches=len(identity_checks),
        top20_equal_price_adjacent_pairs=int(tie_groups),
        independent_agent_qa_performed=False,independent_agent_qa_note='별도 계산 알고리즘 검산만 수행. 담당자 독립 QA는 후속 단계.',
        evidence='median_evidence.csv',data_sha256=digest(OUT/'data.json'))
    save('validation.json',receipt)
    facts=json.loads((OUT/'facts.json').read_text(encoding='utf8'))
    for fact in facts['facts']:
        if fact['claim_id'].startswith('P_'):
            fact['status']='verified'
            fact['verification_note']='로컬 입력 스냅샷 기준: 전 풀 순위 및 원거래 중앙값·표본 수를 별도 NumPy 계산으로 일치 확인. 현재 외부 시세 확인을 뜻하지 않음.'
    save('facts.json',facts)
    outputs=['data.json','top20_quarterly.csv','facts.json','name_mapping.csv','entry_events.csv','leader_changes.csv',
        'sensitivity.json','coverage.csv','period_accounting.csv','row_accounting.json','identity_review.json','median_evidence.csv',
        'validation.json','writer_handoff.json','research_preflight.json','build_top20.py','package_top20.py','verify_top20.py']
    revision={x['path']:x['sha256'] for x in account['source_inputs']}
    for p in [OUT.parent/'brief.json',OUT.parent/'state.json']:
        revision[p.relative_to(ROOT).as_posix()]=digest(p)
    handoff=dict(task_id='apartment-top20-race-20261029-research-v1',role='research',status='data_ready',
        input_revisions=revision,outputs=[dict(path=(OUT/n).relative_to(ROOT).as_posix(),sha256=digest(OUT/n),bytes=(OUT/n).stat().st_size) for n in outputs],
        data_contract='frames[].top20 와 frames[].top 은 동일한 20개 배열. 금액=만원/채, n=해당 4분기 유효거래 수.',
        affected_scene_ids=['全레이스79분기','최종TOP20','신규진입','1위교체'],
        checks=[dict(check='79개 분기·1580개 가격/표본수/순위 및 전체 풀 TOP20',result='passed',evidence='validation.json'),
            dict(check='127개 등장 단지 canonical aptSeq·명칭·법정동 코드 단일성',result='passed',evidence='identity_review.json; validation.json'),
            dict(check='원자료 해시·취소/면적/기간·지역 중복·중앙 원행 증거',result='passed',evidence='row_accounting.json; median_evidence.csv'),
            dict(check='제작물 실제 프레임·연속 재생·청취',result='not_performed_research_only',evidence=None),
            dict(check='담당자 독립 QA',result='pending_next_role',evidence=None)],
        open_issue_ids=[],unresolved=['원자료 파일별 수집시각·후속 취소 갱신 차이','확장 자료의 기존 중복제거 한계','미수집 지역 전체순위','외부 단지대장 현재명칭 대조'],
        next_role=['writer','visual','qa'],network_calls=0,paid_calls=0,claude_calls=0,uploads=0,
        summary=f'7개 수집 지역 12,470단지·2,153,830건. 2006Q4~2026Q2 79개 분기 TOP20 재선정. 총 127단지, 신규 진입 107·재진입 197·1위 교체 13회. 2026-10-10까지 포함된 선행 소스도 2026-06-30 계약 종료로 제한. 0원/전방 채움 없음. 1,580개 중위값·표본 수·순위 검산 통과. 원명과 표시명 매핑, 원거래 중앙행 증거 동봉.')
    save('handoff.json',handoff)
    print(json.dumps(receipt,ensure_ascii=False))


if __name__=='__main__':
    main()
