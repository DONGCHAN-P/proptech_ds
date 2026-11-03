"""로컬 실거래 원행으로 분기말 최근 4분기 단지 TOP20을 재현한다."""
from pathlib import Path
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
SOURCE = ROOT / 'video-agent-studio/episodes/capital-10eok-map-20261017/research/source-completion-v1'
EXP = ROOT / 'analysis/housing_growth_2006/regional_expansion_v1'
FIRST, END = pd.Period('2006Q1'), pd.Period('2026Q2')
REGIONS = {'11':'서울','41':'경기','28':'인천','26':'부산','27':'대구','30':'대전','36':'세종'}
TODAY = '2026-10-29'


def save(name, data):
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(4*1024*1024), b''):
            h.update(b)
    return h.hexdigest()


def norm(s):
    return re.sub(r'\s+', ' ', str(s or '')).strip()


def winner(s):
    s = s.dropna().map(norm)
    s = s[s.ne('')]
    return '' if s.empty else str(s.value_counts().index[0])


def sorted_stats(stats, previous, minimum=5):
    s = stats[stats.n >= minimum].copy()
    s['previous_rank'] = s.index.map(previous).fillna(10**9)
    s['id_sort'] = s.index
    return s.sort_values(['median_manwon','previous_rank','id_sort'], ascending=[False,True,True], kind='stable')


def main():
    mpath, epath = SOURCE/'episode_84_source_rows.parquet', EXP/'expansion_normalized.parquet'
    m = pd.read_parquet(mpath, columns=['complex_id','apt_seq','sigungu_code','legal_dong_name','legal_dong_code',
        'apt_name_raw','jibun','build_year','deal_date','deal_amount','area_m2','is_canceled',
        'included_price_analysis','source_file','source_filtered_item_index','source_index_basis','source_kind'])
    e = pd.read_parquet(epath)
    accounting = {'master_input_rows':len(m),'expansion_input_rows':len(e),
        'master_region_counts':m.sigungu_code.str[:2].value_counts().to_dict(),
        'expansion_region_counts':e.region.value_counts().to_dict(),
        'additional_deduplication_applied':False,
        'master_item_multiplicity_preserved':True,
        'expansion_upstream_normalization':json.loads((EXP/'normalization.json').read_text(encoding='utf8'))}
    mprefix, eprefix = set(m.sigungu_code.str[:2]), set(e.sigungu_code.str[:2])
    assert not mprefix.intersection(eprefix), '자료 간 지역 중복: 병합 중단'
    accounting['source_region_overlap'] = []
    stages = {}
    def filt(df, condition, name, source):
        stages.setdefault(source, {})[name] = int((~condition).sum())
        return df[condition].copy()
    m = filt(m, m.included_price_analysis.fillna(False), 'excluded_by_included_price_analysis', 'master')
    m = filt(m, ~m.is_canceled.fillna(False), 'canceled', 'master')
    m = filt(m, m.area_m2.ge(84) & m.area_m2.lt(85), 'outside_area', 'master')
    m = filt(m, m.deal_amount.gt(0) & m.deal_date.notna(), 'bad_price_or_date', 'master')
    m = filt(m, m.deal_date.between(FIRST.start_time, END.end_time), 'outside_period', 'master')
    ok = m.complex_id.str.fullmatch(r'rtms:\d{5}-\d+').fillna(False) & m.complex_id.eq('rtms:'+m.apt_seq)
    m = filt(m, ok, 'uncertain_canonical_identity', 'master')
    m['id'] = m.complex_id
    m['region'] = m.sigungu_code.str[:2].map(REGIONS)
    assert m.region.notna().all()
    e = filt(e, ~e.parse_error.fillna(True), 'parse_error', 'expansion')
    e = filt(e, ~e.is_canceled.fillna(False), 'canceled', 'expansion')
    e = filt(e, e.area_m2.ge(84) & e.area_m2.lt(85), 'outside_area', 'expansion')
    e = filt(e, e.deal_amount.gt(0) & e.deal_date.notna(), 'bad_price_or_date', 'expansion')
    e = filt(e, e.deal_date.between(FIRST.start_time, END.end_time), 'outside_period', 'expansion')
    e = filt(e, ~e.sigungu_code.isin(['27720','47720']), 'gunwi_fixed_boundary', 'expansion')
    accounting['expansion_fallback_rows_within_target_before_exclusion'] = int(e.id_fallback.fillna(True).sum())
    ok = ~e.id_fallback.fillna(True) & e.apt_id.str.fullmatch(r'api:\d{5}-\d+').fillna(False)
    e = filt(e, ok, 'fallback_or_uncertain_identity', 'expansion')
    e['id'] = e.apt_id.str.replace('api:', 'rtms:', regex=False)
    assert e.sigungu_code.str[:2].map(REGIONS).eq(e.region).all()
    accounting['sequential_exclusions'] = stages
    for key, df in [('master',m),('expansion',e)]:
        accounting[key+'_included_rows'] = len(df)
        accounting[key+'_included_complexes'] = int(df.id.nunique())
    cols = ['id','region','deal_date','deal_amount','area_m2']
    d = pd.concat([m[cols],e[cols]], ignore_index=True)
    d['q'] = d.deal_date.dt.to_period('Q').astype('int64')
    accounting['included_rows'] = len(d)
    accounting['included_complexes'] = int(d.id.nunique())
    coverage = d.groupby('region').agg(n=('id','size'),complexes=('id','nunique'),first_date=('deal_date','min'),last_date=('deal_date','max')).reset_index()
    coverage.to_csv(OUT/'coverage.csv',index=False,encoding='utf-8-sig')
    previous, seen, frames, events, leaders, checks, sensitivity = {}, set(), [], [], [], [], []
    for q in pd.period_range('2006Q4', END, freq='Q'):
        window = d[d.q.between(q.ordinal-3, q.ordinal)]
        stats = window.groupby('id').deal_amount.agg(median_manwon='median',n='size')
        ordered = sorted_stats(stats, previous)
        assert len(ordered)>=20, f'{q}: TOP20 부족'
        top = [{'id':i,'median_manwon':float(r.median_manwon),'n':int(r.n),'rank':k}
            for k,(i,r) in enumerate(ordered.head(20).iterrows(),1)]
        current = {r['id']:r['rank'] for r in top}
        entries = []
        for r in top:
            if r['id'] not in previous:
                ev = dict(period=str(q),id=r['id'],rank=r['rank'],median_manwon=r['median_manwon'],n=r['n'],
                          event='initial' if not frames else ('first_entry' if r['id'] not in seen else 'reentry'))
                entries.append(ev)
                events.append(ev)
        old_leader = frames[-1]['top'][0]['id'] if frames else None
        if old_leader != top[0]['id']:
            leaders.append(dict(period=str(q),previous_id=old_leader,**top[0]))
        movers = []
        if frames:
            for r in top:
                if r['id'] in previous and r['rank'] != previous[r['id']]:
                    movers.append(dict(id=r['id'],from_rank=previous[r['id']],to_rank=r['rank'],
                                       rank_gain=previous[r['id']]-r['rank']))
        frames.append(dict(period=str(q),window_start=str(q-3),window_end=str(q),top=top,
            eligible_complexes=len(ordered),window_transactions=len(window),entries=entries,
            exits=[i for i in previous if i not in current],rank_changes=movers))
        checks.append(dict(period=str(q),window_start=str(q-3),window_end=str(q),
            window_transactions=len(window),observed_complexes=len(stats),eligible_complexes=len(ordered),
            cutoff_median_manwon=top[-1]['median_manwon'],rank21_median_manwon=None if len(ordered)<21 else float(ordered.iloc[20].median_manwon),
            source_regions=','.join(sorted(window.region.unique()))))
        if q==END or old_leader!=top[0]['id']:
            for minimum in (3,5,10):
                ss=sorted_stats(stats,previous,minimum).head(20)
                sensitivity.append(dict(period=str(q),min_n=minimum,
                    tie_basis='본편 직전 분기 TOP20 순위, 그다음 canonical ID',
                    top=[dict(id=i,rank=k,median_manwon=float(r.median_manwon),n=int(r.n)) for k,(i,r) in enumerate(ss.iterrows(),1)],
                    overlap_with_main=len(set(ss.index).intersection(current))))
        previous=current
        seen.update(current)
    pd.DataFrame(checks).to_csv(OUT/'period_accounting.csv',index=False,encoding='utf-8-sig')
    ids = {r['id'] for f in frames for r in f['top']}
    # 명칭과 위치는 실제 등장 후보만 해석한다. 전체 거래 재취득/전수 XML 파싱 없음.
    metadata, identity_issues = {}, []
    for i,g in m[m.id.isin(ids)].groupby('id',sort=True):
        name=winner(g.apt_name_raw)
        dong=winner(g.legal_dong_name)
        codes=sorted(g.sigungu_code.dropna().unique().tolist())
        dongs=sorted({norm(x) for x in g.legal_dong_name.dropna() if norm(x)})
        names=sorted({norm(x) for x in g.apt_name_raw.dropna() if norm(x)})
        seq=i.removeprefix('rtms:')
        years=sorted(int(x) for x in g.build_year.dropna().unique() if x>0)
        metadata[i]=dict(name=name,display_name=name,location='',region=winner(g.region),
            build_year=int(g.build_year[g.build_year.gt(0)].mode().iloc[0]) if years else None,
            apt_seq=seq,sigungu_code=winner(g.sigungu_code),legal_dong_name=dong,
            original_names=names,original_sigungu_codes=codes,original_legal_dong_names=dongs,
            build_year_variants=years,name_source='source-completion-v1/episode_84_source_rows.parquet',
            name_evidence=[dict(source_file=str(r.source_file),source_filtered_item_index=int(r.source_filtered_item_index),
                                source_index_basis=str(r.source_index_basis),source_kind=str(r.source_kind)) for r in g.head(1).itertuples()])
        if not name or not dong or len(codes)>1 or len(dongs)>1:
            identity_issues.append(dict(id=i,name=name,names=names,sigungu_codes=codes,dong_names=dongs,
                missing_name=not bool(name),missing_dong=not bool(dong),canonical_apt_seq=seq))
    missing=ids-set(metadata)
    mapping_scan={'needed_ids':sorted(missing),'xml_files_read':0,'completed_meta_checked':True,'resolved_ids':[]}
    if missing:
        manifest=json.loads((EXP/'source_files.json').read_text(encoding='utf8'))
        prefixes={i.removeprefix('rtms:').split('-')[0] for i in missing}
        # 새 파일부터 필요한 시군구만. 필요한 aptSeq를 찾으면 중단한다.
        for rel,_ in sorted(manifest,key=lambda x:x[0],reverse=True):
            if Path(rel).name[:5] not in prefixes:
                continue
            path=ROOT/rel
            metapath=path.parent/(path.name.split('.page')[0]+'.meta.json')
            if not metapath.exists() or not json.loads(metapath.read_text(encoding='utf8')).get('complete'):
                continue
            tree=ET.fromstring(path.read_bytes())
            mapping_scan['xml_files_read']+=1
            for item in tree.findall('.//items/item'):
                v={x.tag:(x.text or '').strip() for x in item}
                i='rtms:'+v.get('aptSeq','')
                if i not in missing:
                    continue
                code=v.get('sggCd') or path.name[:5]
                name=norm(v.get('aptNm',''))
                metadata[i]=dict(name=name,display_name=name,location='',region=REGIONS[code[:2]],
                    build_year=int(v['buildYear']) if v.get('buildYear','').isdigit() else None,
                    apt_seq=v['aptSeq'],sigungu_code=code,legal_dong_name=norm(v.get('umdNm','')),
                    original_names=[v.get('aptNm','')],original_sigungu_codes=[code],
                    original_legal_dong_names=[v.get('umdNm','')],name_source=rel,
                    name_evidence=[dict(source_file=rel,apt_seq=v['aptSeq'],source_sha256=sha(path))])
                mapping_scan['resolved_ids'].append(i)
                missing.remove(i)
            if not missing:
                break
    assert not missing, f'후보 명칭 미확인 {missing}'
    save('identity_review.json',dict(candidate_count=len(ids),candidates_requiring_review=identity_issues,
         expansion_name_mapping=mapping_scan,canonical_rule='api:aptSeq → rtms:aptSeq, fallback 제외; canonical ID 간 명칭만으로 병합하지 않음'))
    save('calculation.json',dict(frames=frames,complexes=metadata,entry_events=events,leader_changes=leaders,sensitivity=sensitivity))
    accounting['source_inputs']=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in (mpath,epath,EXP/'source_files.json',SOURCE/'identity_catalog_complete.parquet')]
    save('row_accounting.json',accounting)
    print(json.dumps(dict(frames=len(frames),candidates=len(ids),included_rows=len(d),regions=coverage.to_dict('records'),
        identity_issues=identity_issues,leader_changes=leaders,final_top20=frames[-1]['top']),ensure_ascii=False,default=str),flush=True)


if __name__=='__main__':
    main()
