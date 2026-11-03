"""전 수집 단지의 월별 유효 가격(최근 12개월 실거래 중위값)을 집계한다.

여기서 quote는 관측값 저장 상태다. 매도 호가를 수집한 자료라는 뜻이 아니다.
"""
from pathlib import Path
import collections
import copy
import hashlib
import json
import re
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[4]
OLD=OUT.parent
SOURCE=ROOT/'video-agent-studio/episodes/capital-10eok-map-20261017/research/source-completion-v1'
EXP=ROOT/'analysis/housing_growth_2006/regional_expansion_v1'
REGIONS={'11':'서울','41':'경기','28':'인천','26':'부산','27':'대구','30':'대전','36':'세종'}
DISTRICTS={'11110':'종로구','11170':'용산구','11200':'성동구','11410':'서대문구','11440':'마포구',
    '11470':'양천구','11500':'강서구','11530':'구로구','11560':'영등포구','11590':'동작구',
    '11650':'서초구','11680':'강남구','11710':'송파구','41135':'성남시 분당구','41290':'과천시'}


def save(name,value):
    (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf8')


def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):
            h.update(b)
    return h.hexdigest()


def norm(s):
    return re.sub(r'\s+',' ',str(s or '')).strip()


def mode(s):
    s=s.dropna().map(norm)
    s=s[s.ne('')]
    return '' if s.empty else str(s.value_counts().index[0])


def pool_hash(quotes):
    h=hashlib.sha256()
    for i,v in sorted(quotes.items()):
        h.update(f"{i}\t{v['median_manwon']:.1f}\t{v['n']}\t{v['asof']}\n".encode('utf8'))
    return h.hexdigest()


def age_stats(values):
    return dict(n=len(values),carried=sum(v>0 for v in values),over_12_months=sum(v>12 for v in values),
        over_24_months=sum(v>24 for v in values),over_60_months=sum(v>60 for v in values),
        mean_months=round(float(np.mean(values)),4) if values else 0,
        median_months=float(np.median(values)) if values else 0,max_months=max(values,default=0))


def load_sources():
    prior=json.loads((OLD/'row_accounting.json').read_text(encoding='utf8'))
    inputs=prior['source_inputs'][:2]
    for x in inputs:
        assert sha(ROOT/x['path'])==x['sha256'], '원자료 해시 변경'
    cols=['complex_id','apt_seq','sigungu_code','legal_dong_name','apt_name_raw','build_year',
        'deal_date','deal_amount','area_m2','is_canceled','included_price_analysis',
        'source_file','source_filtered_item_index','source_index_basis']
    m=pd.read_parquet(ROOT/inputs[0]['path'],columns=cols)
    e=pd.read_parquet(ROOT/inputs[1]['path'])
    raw_counts=dict(master=len(m),expansion=len(e))
    assert not set(m.sigungu_code.str[:2])&set(e.sigungu_code.str[:2])
    stages={}
    def filt(g,ok,key,source):
        stages.setdefault(source,{})[key]=int((~ok).sum())
        return g[ok].copy()
    m=filt(m,m.included_price_analysis.fillna(False),'excluded_by_included_price_analysis','master')
    m=filt(m,~m.is_canceled.fillna(False),'canceled','master')
    m=filt(m,m.area_m2.ge(84)&m.area_m2.lt(85),'outside_area','master')
    m=filt(m,m.deal_amount.gt(0)&m.deal_date.notna(),'bad_price_or_date','master')
    m=filt(m,m.deal_date.between(pd.Timestamp('2006-01-01'),pd.Timestamp('2026-07-01'),inclusive='left'),'outside_period','master')
    m=filt(m,m.complex_id.str.fullmatch(r'rtms:\d{5}-\d+').fillna(False)&m.complex_id.eq('rtms:'+m.apt_seq),'uncertain_canonical_identity','master')
    m['id']=m.complex_id
    m['region']=m.sigungu_code.str[:2].map(REGIONS)
    e=filt(e,~e.parse_error.fillna(True),'parse_error','expansion')
    e=filt(e,~e.is_canceled.fillna(False),'canceled','expansion')
    e=filt(e,e.area_m2.ge(84)&e.area_m2.lt(85),'outside_area','expansion')
    e=filt(e,e.deal_amount.gt(0)&e.deal_date.notna(),'bad_price_or_date','expansion')
    e=filt(e,e.deal_date.between(pd.Timestamp('2006-01-01'),pd.Timestamp('2026-07-01'),inclusive='left'),'outside_period','expansion')
    e=filt(e,~e.sigungu_code.isin(['27720','47720']),'gunwi_fixed_boundary','expansion')
    e=filt(e,~e.id_fallback.fillna(True)&e.apt_id.str.fullmatch(r'api:\d{5}-\d+').fillna(False),'fallback_or_uncertain_identity','expansion')
    e['id']=e.apt_id.str.replace('api:','rtms:',regex=False)
    assert e.sigungu_code.str[:2].map(REGIONS).eq(e.region).all()
    assert stages==prior['sequential_exclusions']
    d=pd.concat([m[['id','region','deal_date','deal_amount','area_m2']],e[['id','region','deal_date','deal_amount','area_m2']]],ignore_index=True)
    d['month']=d.deal_date.dt.to_period('M').astype('int64')
    assert len(d)==2153830 and d.id.nunique()==12470
    save('source_accounting.json',dict(source_inputs=inputs,raw_input_rows=raw_counts,
        sequential_exclusions=stages,source_region_overlap=[],all_complexes=12470,valid_transactions=len(d),
        master_included_rows=len(m),expansion_included_rows=len(e),fallback_excluded=0,
        master_item_multiplicity_preserved=True,additional_deduplication_applied=False,
        inherited_expansion_normalization=prior['expansion_upstream_normalization']))
    d.groupby('region').agg(n=('id','size'),complexes=('id','nunique'),first_date=('deal_date','min'),last_date=('deal_date','max')).reset_index().to_csv(OUT/'coverage.csv',index=False,encoding='utf-8-sig')
    return m,e,d,inputs


def metadata_for(candidates,m,old):
    result={i:copy.deepcopy(v) for i,v in old['complexes'].items() if i in candidates}
    newids=candidates-set(result)
    for i,g in m[m.id.isin(newids)].groupby('id'):
        years=g.build_year[g.build_year.gt(0)]
        result[i]=dict(name=mode(g.apt_name_raw),display_name=mode(g.apt_name_raw),location='',region=mode(g.region),
            build_year=None if years.empty else int(years.mode().iloc[0]),apt_seq=i[5:],
            sigungu_code=mode(g.sigungu_code),legal_dong_name=mode(g.legal_dong_name),
            original_names=sorted({norm(x) for x in g.apt_name_raw.dropna()}),
            original_sigungu_codes=sorted(g.sigungu_code.unique().tolist()),
            original_legal_dong_names=sorted({norm(x) for x in g.legal_dong_name.dropna()}),
            name_source='source-completion-v1/episode_84_source_rows.parquet',
            name_evidence=[dict(source_file=r.source_file,source_filtered_item_index=int(r.source_filtered_item_index),
                source_index_basis=r.source_index_basis) for r in g.head(1).itertuples()])
    missing=candidates-set(result)
    scans=0
    if missing:
        wanted_prefix={i[5:].split('-')[0] for i in missing}
        manifest=json.loads((EXP/'source_files.json').read_text(encoding='utf8'))
        for rel,_ in sorted(manifest,key=lambda x:x[0],reverse=True):
            path=ROOT/rel
            if path.name[:5] not in wanted_prefix:
                continue
            meta=path.parent/(path.name.split('.page')[0]+'.meta.json')
            if not meta.exists() or not json.loads(meta.read_text(encoding='utf8')).get('complete'):
                continue
            tree=ET.fromstring(path.read_bytes())
            scans+=1
            for item in tree.findall('.//items/item'):
                v={x.tag:(x.text or '').strip() for x in item}
                i='rtms:'+v.get('aptSeq','')
                if i not in missing:
                    continue
                code=v.get('sggCd') or path.name[:5]
                result[i]=dict(name=norm(v.get('aptNm','')),display_name=norm(v.get('aptNm','')),location='',
                    region=REGIONS[code[:2]],build_year=int(v['buildYear']) if v.get('buildYear','').isdigit() else None,
                    apt_seq=v['aptSeq'],sigungu_code=code,legal_dong_name=norm(v.get('umdNm','')),
                    original_names=[v.get('aptNm','')],name_source=rel,name_evidence=[dict(source_file=rel,sha256=sha(path))])
                missing.remove(i)
            if not missing:
                break
    assert not missing, f'명칭 미확인: {missing}'
    catalog=pd.read_parquet(SOURCE/'identity_catalog_complete.parquet')
    issues=[]
    counts=collections.Counter(v['name'] for v in result.values())
    short={'현대14차(203,204,205,206동)':'현대14차','대치우성아파트1동,2동,3동,5동,6동,7동':'대치우성아파트',
        '푸른마을아파트101동~111동':'푸른마을아파트'}
    for i,v in result.items():
        if i in catalog.index:
            z=catalog.loc[i]
            if len(z.sigungu_codes)!=1 or len(z.legal_dong_codes)!=1 or v['name']!=z['name']:
                issues.append(dict(id=i,name=v['name'],sigungu_codes=list(z.sigungu_codes),legal_dong_codes=list(z.legal_dong_codes)))
        if not v['name'] or not v['legal_dong_name']:
            issues.append(dict(id=i,issue='단지명/법정동명 누락'))
        district=DISTRICTS.get(v['sigungu_code'],'시군구코드 '+v['sigungu_code'])
        v['location']=' '.join([v['region'],district,v['legal_dong_name']])
        v['display_name']=short.get(v['name'],v['name'])
        if counts[v['name']]>1:
            v['display_name']+=' · '+v['legal_dong_name']
        v['display_name_status']='proposed_short_label' if v['display_name']!=v['name'] else 'reported_name_whitespace_normalized'
    save('identity_review.json',dict(ever_top20_count=len(result),reused_v1_metadata=len(candidates)-len(newids),
        new_metadata_count=len(newids),expansion_xml_files_read=scans,issues=issues))
    if issues:
        save('issue_identity.json',dict(issue_id='monthly-v2-identity',affected_complexes=issues,
            affected_scene_ids=['monthly_race'],proposal='canonical aptSeq별 위치·명칭의 추가 대조 필요'))
        raise AssertionError(f'후보 식별 문제 {issues}')
    return result


def main():
    m,e,d,inputs=load_sources()
    old=json.loads((OLD/'data.json').read_text(encoding='utf8'))
    quotes,previous,ever_top={}, {},set()
    frames,events,leaders,audits,all_ages=[],[],[],[],[]
    for month in pd.period_range('2006-12','2026-06',freq='M'):
        seed=not frames
        window=d[d.month.between(month.ordinal-11,month.ordinal)]
        stats=window.groupby('id').deal_amount.agg(median_manwon='median',n='size')
        new=d[d.month.eq(month.ordinal)].id.value_counts()
        updates=stats[stats.n.ge(5)&(True if seed else stats.index.isin(new.index))]
        newly_qualified=[i for i in updates.index if i not in quotes]
        for i,r in updates.iterrows():
            quotes[i]=dict(median_manwon=float(r.median_manwon),n=int(r.n),asof=month.ordinal)
        ordered=sorted(quotes,key=lambda i:(-quotes[i]['median_manwon'],previous.get(i,float('inf')),i))
        assert len(ordered)>=20
        top=[]
        for rank,i in enumerate(ordered[:20],1):
            quote=quotes[i]
            asof=pd.Period(ordinal=quote['asof'],freq='M')
            top.append(dict(id=i,rank=rank,median_manwon=quote['median_manwon'],n=quote['n'],
                quote_asof_month=str(asof),month_new_n=int(new.get(i,0)),carried=quote['asof']!=month.ordinal,
                stale_age_months=month.ordinal-quote['asof'],current_window_n=int(stats.loc[i,'n']) if i in stats.index else 0,
                quote_window_start=str(asof-11),quote_window_end=str(asof)))
        current={r['id']:r['rank'] for r in top}
        entries=[]
        for r in top:
            if r['id'] not in previous:
                event=dict(period=str(month),event='initial' if seed else ('first_entry' if r['id'] not in ever_top else 'reentry'),**r)
                events.append(event)
                entries.append(event)
        oldleader=frames[-1]['top'][0]['id'] if frames else None
        if oldleader!=top[0]['id']:
            leaders.append(dict(period=str(month),previous_id=oldleader,**top[0]))
        ages=[month.ordinal-v['asof'] for v in quotes.values()]
        topages=[r['stale_age_months'] for r in top]
        all_ages.extend(topages)
        carry_no_new=sum(i not in updates.index and i not in new.index for i in quotes)
        carry_small=sum(i not in updates.index and i in new.index for i in quotes)
        row=dict(period=str(month),window_start=str(month-11),window_end=str(month),top=top,top20=top,
            seed=seed,pool_size=len(quotes),eligible_complexes=len(quotes),
            currently_window_qualified_complexes=int(stats.n.ge(5).sum()),month_transactions=int(new.sum()),
            quote_updates=len(updates),first_qualifications=len(newly_qualified),pool_state_sha256=pool_hash(quotes),
            pool_stale_age=age_stats(ages),top20_stale_age=age_stats(topages),entries=entries,
            exits=[i for i in previous if i not in current],
            rank_changes=[dict(id=i,from_rank=previous[i],to_rank=k,rank_gain=previous[i]-k) for i,k in current.items() if i in previous and previous[i]!=k])
        frames.append(row)
        audits.append(dict(period=str(month),pool_size=len(quotes),window_transactions=len(window),
            month_transactions=int(new.sum()),updated_quotes=len(updates),first_qualifications=len(newly_qualified),
            carried_no_new_trade=carry_no_new,carried_new_trade_but_n_lt5=carry_small,
            seed_qualified_with_no_december_trade=sum(i not in new.index for i in updates.index) if seed else 0,
            top20_carried=sum(r['carried'] for r in top),top20_max_stale_months=max(topages),
            pool_max_stale_months=max(ages)))
        previous=current
        ever_top.update(current)
    assert len(frames)==235
    metadata=metadata_for(ever_top,m,old)
    flat=[]
    for f in frames:
        for r in f['top']:
            r.update({k:metadata[r['id']][k] for k in ('name','display_name','location','region')})
            flat.append(dict(period=f['period'],window_start=f['window_start'],window_end=f['window_end'],**r))
    for items in (events,leaders):
        for r in items:
            r.update({k:metadata[r['id']][k] for k in ('name','display_name','location','region')})
    firstcount=sum(x['event']=='first_entry' for x in events)
    recount=sum(x['event']=='reentry' for x in events)
    summary=dict(frame_count=235,displayed_rows=len(flat),all_collected_complexes=12470,valid_transactions=len(d),
        seed_qualified_complexes=frames[0]['pool_size'],ever_qualified_complexes=len(quotes),
        never_qualified_complexes=12470-len(quotes),ever_top20_complexes=len(ever_top),
        first_entry_events=firstcount,reentry_events=recount,leader_change_count=len(leaders)-1,
        initial_leader=leaders[0],leader_changes=leaders[1:],entry_events=[x for x in events if x['event']!='initial'],
        top20_stale_age_all_frames=age_stats(all_ages),final_top20_stale_age=frames[-1]['top20_stale_age'],
        final_pool_stale_age=frames[-1]['pool_stale_age'],
        total_quote_updates=sum(x['updated_quotes'] for x in audits),
        total_carries_no_new_trade=sum(x['carried_no_new_trade'] for x in audits),
        total_carries_new_trade_but_n_lt5=sum(x['carried_new_trade_but_n_lt5'] for x in audits),
        seed_qualified_with_no_december_trade=audits[0]['seed_qualified_with_no_december_trade'],
        final_top20=frames[-1]['top'])
    limitations=old['meta']['limitations'][:6]+[
        '월별 갱신·이월 버전이다. 과거 12개월의 최신 중위값만 비교하는 분기 v1과 다른 통계이며, 오래된 가격도 사용자 요청에 따라 순위 풀에 계속 남는다.',
        'n은 마지막으로 유효하게 가격을 갱신한 12개월 창의 거래 수다. current_window_n은 현재 프레임의 12개월 거래 수다. 두 값은 이월 시 다를 수 있다.',
        'quote_asof_month는 유효한 통계 산출월이다. 최초 2006-12 시드는 2006년 전체 5건 이상이면 12월 거래 없이도 설정되므로 개별 최종 계약월과 같다는 뜻이 아니다.',
        '신규 거래가 있어도 직전 12개월 표본이 5건 미만이면 이전 통계와 n·기준월을 그대로 유지한다. 미자격 단지는 최초 유효 평가 전 가격을 만들지 않는다.',
        '이월은 가격 추정이나 현재 시장 시세 확인이 아니다. 순위는 현재·과거 서로 다른 기준월의 통계를 함께 비교하므로 기준월/이월 표시를 함께 사용해야 한다.',
        '공식 신고 원명은 보존하고 짧은 표시명은 제안으로 제공한다. 건축물·층·면적 세부 구성 및 거래방식은 별도 통제하지 않는다.']
    data=dict(meta=dict(revision='monthly-v2',measure='last_qualified_trailing_12_month_transaction_median_manwon',
        area_min=84,area_max_exclusive=85,min_n=5,window_months=12,frequency='monthly',
        regions=['서울','경기','인천','부산','대구','대전','세종'],first_period='2006-12',last_period='2026-06',
        transaction_start='2006-01-01',observation_end='2026-06-30',checked_at='2026-10-29',unit='만원/채',
        all_collected_complexes=12470,valid_transactions=len(d),source_inputs=inputs,
        seed_rule='2006-12: 2006년 전체 유효 거래 5건 이상인 모든 단지를 시드로 설정. 12월 신규 거래 조건 없음.',
        update_rule='2007-01 이후: 해당 월 유효 신규 거래 >=1건 AND 해당 월 포함 최근12개월 거래 >=5건이면 원거래 중위값/n/quote_asof_month 갱신.',
        carry_rule='이미 자격을 얻은 단지는 갱신 조건 미충족 시 마지막 유효 median/n/quote_asof_month 유지. 새 거래가 있어도 n<5이면 이월.',
        prequalification_rule='첫 유효 자격 취득 전에는 가격·순위 없음. 0원 생성이나 최초 자격 이전 역방향 채움 없음.',
        n_semantics='마지막 유효 갱신월의 12개월 거래 수; current_window_n은 현재 프레임 창의 거래 수',
        quote_asof_semantics='마지막 유효 통계 갱신월, seed는2006-12',
        carried_semantics='quote_asof_month < period; seed는 모두 false',
        tie_rule='가격 내림차순 → 직전 월 TOP20 순위 오름차순(밖은 동일 무한순위) → canonical ID 사전순',
        ranking_pool='전체12470 수집단지에서 그 월까지 한 번이라도 자격을 얻은 누적 풀. v1의127후보에 제한하지 않음.',
        aggregation='해당12개월 개별 매매 총액 중위값; 짝수이면 가운데 두 원거래 금액의 평균',
        cancellation_policy=old['meta']['cancellation_policy'],identity_policy=old['meta']['identity_policy'],
        limitations=limitations),complexes=metadata,frames=frames,summary=summary)
    save('data.json',data)
    pd.DataFrame(flat).to_csv(OUT/'top20_monthly.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(audits).to_csv(OUT/'monthly_accounting.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(events).to_csv(OUT/'entry_events.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(leaders).to_csv(OUT/'leader_changes.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame([dict(id=i,**{k:v.get(k) for k in ('name','display_name','location','region','build_year','apt_seq')}) for i,v in metadata.items()]).to_csv(OUT/'name_mapping.csv',index=False,encoding='utf-8-sig')
    save('validation.json',dict(status='pending_source_recalculation',data_sha256=sha(OUT/'data.json')))
    print(json.dumps(dict(data_path=str(OUT/'data.json'),frames=235,all_complexes=12470,
        ever_qualified=len(quotes),ever_top20=len(ever_top),leader_changes=len(leaders)-1,
        final_top20_stale_age=summary['final_top20_stale_age'],final_pool_stale_age=summary['final_pool_stale_age']),ensure_ascii=False),flush=True)


if __name__=='__main__':
    main()
