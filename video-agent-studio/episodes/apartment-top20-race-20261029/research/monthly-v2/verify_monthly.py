"""원 Parquet을 다시 읽어 모든 월의 전체 quote 상태와 TOP20을 별도 검산한다."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[4]
S=ROOT/'video-agent-studio/episodes/capital-10eok-map-20261017/research/source-completion-v1'
E=ROOT/'analysis/housing_growth_2006/regional_expansion_v1'
EXPECTED={
    'video-agent-studio/episodes/capital-10eok-map-20261017/research/source-completion-v1/episode_84_source_rows.parquet':'86b39d1800da16c87039bcaf58e3f0a1a143b2dcafb12eb8a793148b3f1399ab',
    'analysis/housing_growth_2006/regional_expansion_v1/expansion_normalized.parquet':'e12a397460797b19d8ca84898a2934217871b3656fa49d21023c1f218ea80450'}


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):
            h.update(b)
    return h.hexdigest()


def save(name,value):
    (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf8')


def ages_stat(values):
    z=np.asarray(values,dtype=int)
    return dict(n=len(values),carried=int((z>0).sum()),over_12_months=int((z>12).sum()),
        over_24_months=int((z>24).sum()),over_60_months=int((z>60).sum()),
        mean_months=round(float(z.mean()),4),median_months=float(np.median(z)),max_months=int(z.max()))


def main():
    data=json.loads((OUT/'data.json').read_text(encoding='utf8'))
    audit=pd.read_csv(OUT/'monthly_accounting.csv').set_index('period')
    for p,h in EXPECTED.items():
        assert sha(ROOT/p)==h, '입력 소스 변경'
    m=pd.read_parquet(S/'episode_84_source_rows.parquet',columns=['complex_id','apt_seq','sigungu_code','deal_date','deal_amount',
        'area_m2','is_canceled','included_price_analysis','source_file','source_filtered_item_index','source_index_basis'])
    e=pd.read_parquet(E/'expansion_normalized.parquet',columns=['apt_id','sigungu_code','deal_date','deal_amount','area_m2',
        'is_canceled','parse_error','id_fallback'])
    assert not set(m.sigungu_code.str[:2])&set(e.sigungu_code.str[:2])
    m=m[m.included_price_analysis.fillna(False)&~m.is_canceled.fillna(False)&
        m.area_m2.ge(84)&m.area_m2.lt(85)&m.deal_amount.gt(0)&
        (m.deal_date>=pd.Timestamp('2006-01-01'))&(m.deal_date<pd.Timestamp('2026-07-01'))&
        m.complex_id.str.fullmatch(r'rtms:\d{5}-\d+').fillna(False)&m.complex_id.eq('rtms:'+m.apt_seq)].copy()
    e=e[~e.parse_error.fillna(True)&~e.is_canceled.fillna(False)&~e.id_fallback.fillna(True)&
        e.area_m2.ge(84)&e.area_m2.lt(85)&e.deal_amount.gt(0)&
        (e.deal_date>=pd.Timestamp('2006-01-01'))&(e.deal_date<pd.Timestamp('2026-07-01'))&
        ~e.sigungu_code.isin(['27720','47720'])&e.apt_id.str.fullmatch(r'api:\d{5}-\d+').fillna(False)].copy()
    m['id']=m.complex_id
    e['id']=e.apt_id.map(lambda x:'rtms:'+x[4:])
    pieces=[]
    for source,g in [(0,m),(1,e)]:
        x=g[['id','deal_amount','deal_date']].copy()
        x['input_row']=g.index.to_numpy()
        x['source']=source
        pieces.append(x)
    raw=pd.concat(pieces,ignore_index=True)
    assert len(m)==1557479 and len(e)==596351
    assert len(raw)==2153830 and raw.id.nunique()==12470
    ids=raw.id.to_numpy()
    prices=raw.deal_amount.to_numpy()
    months=raw.deal_date.dt.to_period('M').astype('int64').to_numpy()
    origins=raw.input_row.to_numpy()
    sources=raw.source.to_numpy()
    periods=list(map(str,pd.period_range('2006-12','2026-06',freq='M')))
    assert [f['period'] for f in data['frames']]==periods
    quotes,previous,ever_top={}, {},set()
    evidence,events,leaders,alltopages,claims=[],[],[],[],[]
    update_total=carry_total=carry_new_small_total=seed_without_dec=state_checks=0
    lastleader=None
    for step,f in enumerate(data['frames']):
        period=f['period']
        now=pd.Period(period,freq='M')
        assert f['top']==f['top20'] and len(f['top20'])==20
        assert f['window_start']==str(now-11) and f['window_end']==period
        seed=step==0
        ix=np.flatnonzero((months>=now.ordinal-11)&(months<=now.ordinal))
        ordered=ix[np.lexsort((origins[ix],sources[ix],prices[ix],ids[ix]))]
        sortids=ids[ordered]
        starts=np.r_[0,np.flatnonzero(sortids[1:]!=sortids[:-1])+1]
        stops=np.r_[starts[1:],len(ordered)]
        counts=stops-starts
        lo=ordered[starts+(counts-1)//2]
        hi=ordered[starts+counts//2]
        med=(prices[lo].astype(float)+prices[hi].astype(float))/2
        gids=sortids[starts]
        newids,newcounts=np.unique(ids[months==now.ordinal],return_counts=True)
        new=dict(zip(newids,map(int,newcounts)))
        groupindex={i:j for j,i in enumerate(gids)}
        has_new=np.ones(len(gids),dtype=bool) if seed else np.fromiter((i in new for i in gids),dtype=bool,count=len(gids))
        update_idx=np.flatnonzero((counts>=5)&has_new)
        updated={str(gids[j]) for j in update_idx}
        oldids=set(quotes)
        before=quotes.copy()
        for j in update_idx:
            i=str(gids[j])
            quotes[i]=(float(med[j]),int(counts[j]),now.ordinal,int(lo[j]),int(hi[j]))
        newly=updated-oldids
        carried=set(quotes)-updated
        no_new={i for i in carried if i not in new}
        small_new=carried-no_new
        for i in carried:
            assert quotes[i]==before[i],(period,i,'이월 가격/n/기준월 변경')
        for i in small_new:
            assert counts[groupindex[i]]<5
        # 어느 원거래에도 없는 값이나 최초 자격 전의 값은 전체 풀 해시에서 검출된다.
        h=hashlib.sha256()
        for i,v in sorted(quotes.items()):
            h.update(f'{i}\t{v[0]:.1f}\t{v[1]}\t{v[2]}\n'.encode('utf8'))
            assert v[1]>=5 and v[2]<=now.ordinal
        assert h.hexdigest()==f['pool_state_sha256'],(period,'전 단지 누적 상태 불일치')
        state_checks+=len(quotes)
        assert f['pool_size']==len(quotes)==f['eligible_complexes']
        assert f['quote_updates']==len(updated) and f['first_qualifications']==len(newly)
        assert f['month_transactions']==sum(new.values())
        assert f['currently_window_qualified_complexes']==int((counts>=5).sum())
        aa=audit.loc[period]
        assert int(aa.pool_size)==len(quotes) and int(aa.window_transactions)==len(ix)
        assert int(aa.updated_quotes)==len(updated) and int(aa.first_qualifications)==len(newly)
        assert int(aa.carried_no_new_trade)==len(no_new) and int(aa.carried_new_trade_but_n_lt5)==len(small_new)
        if seed:
            seed_without_dec=len(updated-set(new))
            assert int(aa.seed_qualified_with_no_december_trade)==seed_without_dec
            assert len(quotes)==4463
        fullranking=sorted(quotes,key=lambda i:(-quotes[i][0],previous.get(i,float('inf')),i))
        assert [r['id'] for r in f['top20']]==fullranking[:20],(period,'전체 누적 풀 TOP20 불일치')
        if fullranking[0]!=lastleader:
            leaders.append((period,fullranking[0]))
        lastleader=fullranking[0]
        for rank,r in enumerate(f['top20'],1):
            i=r['id']
            p,n,asof,l,u=quotes[i]
            asofmonth=pd.Period(ordinal=asof,freq='M')
            current_n=int(counts[groupindex[i]]) if i in groupindex else 0
            assert r['rank']==rank and r['median_manwon']==p and r['n']==n
            assert r['quote_asof_month']==str(asofmonth) and r['month_new_n']==new.get(i,0)
            assert r['carried']==(i not in updated) and r['stale_age_months']==now.ordinal-asof
            assert r['current_window_n']==current_n
            assert r['quote_window_start']==str(asofmonth-11) and r['quote_window_end']==str(asofmonth)
            assert asofmonth<=now and r['median_manwon']>0
            if not r['carried'] and not seed:
                assert r['month_new_n']>=1 and current_n>=5
            for key in ('name','display_name','location','region'):
                assert r[key]==data['complexes'][i][key] and bool(r[key])
            proof=dict(period=period,id=i,rank=rank,median_manwon=p,n=n,quote_asof_month=str(asofmonth),
                month_new_n=new.get(i,0),carried=r['carried'],current_window_n=current_n)
            for label,index in [('low',l),('high',u)]:
                assert ids[index]==i and asof-11<=months[index]<=asof<=now.ordinal
                src=m if sources[index]==0 else e
                original=src.loc[origins[index]]
                proof[label+'_input_file']=list(EXPECTED)[int(sources[index])]
                proof[label+'_parquet_row_0based']=int(origins[index])
                proof[label+'_price_manwon']=int(prices[index])
                proof[label+'_deal_date']=str(original.deal_date.date())
                if sources[index]==0:
                    proof[label+'_original_source_file']=original.source_file
                    proof[label+'_original_source_item_index']=int(original.source_filtered_item_index)
                    proof[label+'_original_source_index_basis']=original.source_index_basis
            evidence.append(proof)
            claims.append(dict(claim_id='M_'+period.replace('-','_')+'_'+i.replace(':','_').replace('-','_'),
                sentence=f"{period} {r['location']} {r['name']}은 순위 {rank}위, 표시 중위금액 {p:g}만원. 통계 기준월 {asofmonth}, 당시 12개월 표본 {n}건, 현재 월 신규 {new.get(i,0)}건, 이월 {r['carried']}.",
                source_files=list(EXPECTED),evidence_location=f'median_evidence.csv: period={period}, id={i}',
                reference_date=str(asofmonth.end_time.date()),frame_period=period,checked_at='2026-10-29',status='verified'))
            if i not in previous:
                events.append((period,i,'initial' if seed else ('reentry' if i in ever_top else 'first_entry')))
        ages=[now.ordinal-v[2] for v in quotes.values()]
        topages=[r['stale_age_months'] for r in f['top20']]
        alltopages.extend(topages)
        assert f['pool_stale_age']==ages_stat(ages) and f['top20_stale_age']==ages_stat(topages)
        previous={i:k for k,i in enumerate(fullranking[:20],1)}
        ever_top.update(previous)
        update_total+=len(updated)
        carry_total+=len(no_new)
        carry_new_small_total+=len(small_new)
    summary=data['summary']
    assert len(evidence)==4700==summary['displayed_rows']
    assert len(quotes)==summary['ever_qualified_complexes']
    assert 12470-len(quotes)==summary['never_qualified_complexes']
    assert len(ever_top)==summary['ever_top20_complexes']==len(data['complexes'])
    assert sum(x[2]=='first_entry' for x in events)==summary['first_entry_events']
    assert sum(x[2]=='reentry' for x in events)==summary['reentry_events']
    assert leaders==[(x['period'],x['id']) for x in [summary['initial_leader']]+summary['leader_changes']]
    assert len(leaders)-1==summary['leader_change_count']
    assert summary['total_quote_updates']==update_total and summary['total_carries_no_new_trade']==carry_total
    assert summary['total_carries_new_trade_but_n_lt5']==carry_new_small_total
    assert summary['seed_qualified_with_no_december_trade']==seed_without_dec
    assert summary['top20_stale_age_all_frames']==ages_stat(alltopages)
    assert summary['final_top20_stale_age']==data['frames'][-1]['top20_stale_age']
    assert summary['final_pool_stale_age']==data['frames'][-1]['pool_stale_age']
    old=json.loads((OUT.parent/'data.json').read_text(encoding='utf8'))
    for a,b in zip(data['frames'][0]['top20'],old['frames'][0]['top20']):
        assert all(a[k]==b[k] for k in ('id','rank','median_manwon','n'))
    csv=pd.read_csv(OUT/'top20_monthly.csv')
    assert len(csv)==4700
    flat=[dict(period=f['period'],**r) for f in data['frames'] for r in f['top20']]
    for a,b in zip(csv.to_dict('records'),flat):
        assert all(a[k]==b[k] for k in ('period','id','rank','median_manwon','n','quote_asof_month','month_new_n','carried','current_window_n','stale_age_months'))
    pd.DataFrame(evidence).to_csv(OUT/'median_evidence.csv',index=False,encoding='utf-8-sig')
    save('facts.json',dict(revision='monthly-v2',conditions=dict(area='84<=전용면적<85㎡',unit='만원/채',window_months=12,min_n=5,
        statistic='마지막 유효 갱신월의 개별 매매금액 중위값',scope='수집7개지역 누적유효단지풀',
        current_price_caution='이월 포함, 현재월 통계로 간주하지 말 것'),facts=claims))
    receipt=dict(status='passed',data_sha256=sha(OUT/'data.json'),checked_at='2026-10-29',
        algorithm='별도 NumPy 원거래 정렬/중앙값 + 매월 전체 누적 quote 상태 재구성 및 해시 일치',
        frames_checked=235,displayed_rows_checked=4700,all_canonical_complexes=12470,source_valid_rows=2153830,
        cumulative_pool_state_rows_checked=state_checks,ever_qualified=len(quotes),ever_top20=len(ever_top),
        all_source_hashes_match=True,source_region_overlap=False,all_235_pool_hashes_match=True,
        seed_full2006_matches_v1=True,seed_qualified_no_december_trade=seed_without_dec,
        update_rule_checked=True,new_trade_but_sample_lt5_carry_checked=True,
        no_new_trade_carry_checked=True,never_quote_before_first_qualification=True,
        all_quote_samples_at_least5=True,carried_n_and_asof_preserved=True,
        all_source_windows_no_future=True,after2026Q2_excluded=True,top_aliases_equal=True,csv_matches_json=True,
        total_updates_checked=update_total,total_no_new_trade_carries_checked=carry_total,
        total_new_trade_but_sample_lt5_carries_checked=carry_new_small_total,
        final_top20_stale_age=summary['final_top20_stale_age'],final_pool_stale_age=summary['final_pool_stale_age'],
        limitations='로컬 스냅샷 계산 검산. 별도 담당자의 독립 QA·외부 최신시세 확인·영상 재생/청취 아님.',
        independent_agent_qa_performed=False,evidence_file='median_evidence.csv')
    save('validation.json',receipt)
    names=['data.json','top20_monthly.csv','methods.md','validation.json','facts.json','median_evidence.csv',
        'source_accounting.json','coverage.csv','monthly_accounting.csv','identity_review.json',
        'name_mapping.csv','entry_events.csv','leader_changes.csv','build_monthly.py','verify_monthly.py']
    save('handoff.json',dict(task_id='apartment-top20-race-monthly-v2',role='research',status='data_ready',
        input_revisions=EXPECTED,outputs=[dict(path=(OUT/n).relative_to(ROOT).as_posix(),sha256=sha(OUT/n),bytes=(OUT/n).stat().st_size) for n in names],
        schema='frames[].period=YYYY-MM; top과 top20 동일; 행 추가필드 quote_asof_month/month_new_n/carried/stale_age_months/current_window_n',
        affected_scene_ids=['monthly_race_all_235_frames','monthly_entries','monthly_leader_changes','monthly_final_top20'],
        checks=[dict(check='235개 월 전체 후보/갱신/이월/중앙 원행/순위',result='passed',evidence='validation.json; median_evidence.csv')],
        unresolved=['파일별 수집일 혼재·후속 취소 갱신 차이','장기 이월값을 현재 시세로 표현하지 말 것','최종 영상 독립 QA 필요'],
        next_role=['visual','editor','qa'],network_calls=0,paid_calls=0,claude_calls=0,uploads=0,
        summary=f"235개월·전체12470단지 재집계, 누적자격 {len(quotes)}단지·TOP20등장 {len(ever_top)}단지. 신규 {summary['first_entry_events']}회·재진입 {summary['reentry_events']}회·1위 교체 {summary['leader_change_count']}회. 마지막 TOP20 이월 {summary['final_top20_stale_age']['carried']}/20·최대 {summary['final_top20_stale_age']['max_months']}개월, 전체 풀 최대 {summary['final_pool_stale_age']['max_months']}개월. 전 상태 및 4700표시행 검산 통과."))
    print(json.dumps(receipt,ensure_ascii=False),flush=True)


if __name__=='__main__':
    main()
