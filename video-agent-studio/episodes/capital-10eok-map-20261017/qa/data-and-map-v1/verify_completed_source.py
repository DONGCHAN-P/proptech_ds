from pathlib import Path
import json,hashlib,xml.etree.ElementTree as ET,collections
import pandas as pd
import numpy as np
Q=Path(__file__).resolve().parent;EP=Q.parents[1];ROOT=EP.parents[2];O=EP/'research/source-completion-v1'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
h=read(O/'handoff.json');files=[{'file':x['path'],'sha256':sha(ROOT/x['path']),'matches':sha(ROOT/x['path'])==x['sha256']} for x in h['outputs']];assert all(x['matches'] for x in files)
rows=pd.read_parquet(O/'episode_84_source_rows.parquet');staged=pd.read_parquet(O/'staged_84_source_rows.parquet');prices=pd.read_parquet(O/'annual_prices_complete.parquet');states=pd.read_parquet(O/'annual_status_complete.parquet');cat=pd.read_parquet(O/'complex_catalog_complete.parquet');summary=pd.read_csv(O/'annual_summary_complete.csv');account=read(O/'row_accounting.json')
recfiles=sorted((O/'raw').rglob('receipt.json'));assert len(recfiles)==266
expected=[];page_count=0;rawcount=0;duplicates=0;page_errors=[];pairs=set()
for rp in recfiles:
 rec=read(rp);pairs.add((str(rec['code']),str(rec['ym'])));payloads=[];n=0
 for page in range(1,rec['pages']+1):
  f=rp.parent/f'page-{page:04d}.xml';root=ET.fromstring(f.read_bytes());items=root.findall('.//item');total=int(root.findtext('.//totalCount'));assert total==rec['totalCount'];n+=len(items);page_count+=1
  for idx,item in enumerate(items):
   d={x.tag:(x.text or '').strip() for x in item};payloads.append(tuple(sorted(d.items())))
   area=float(d.get('excluUseAr') or 'nan')
   if not 83<=area<85:continue
   expected.append({'source_file':str(f.relative_to(ROOT)),'source_filtered_item_index':idx,'amount':float(d['dealAmount'].replace(',','')),'area':area,'seq':d.get('aptSeq','').strip(),'cancel':bool(d.get('cdealType','').strip()) or bool(d.get('cdealDay','').strip()),'date':f"{d['dealYear']}-{int(d['dealMonth']):02d}-{int(d['dealDay']):02d}"})
  for pr in rec['page_receipts']:
   if Path(pr.get('file','')).name==f.name:assert pr['sha256']==sha(f)
 assert n==rec['totalCount']==rec['actual_rows'];rawcount+=n
 extra=n-len(set(payloads));assert extra==rec['identical_payload_extra_occurrences'];duplicates+=extra
 verify=rp.parent/'verify-page-0001.xml'
 assert verify.exists() and verify.read_bytes()==(rp.parent/'page-0001.xml').read_bytes()
print('all raw pages verified',flush=True)
fresh=rows[rows.source_kind.eq('fresh_complete_api')].copy();expected=pd.DataFrame(expected)
key=['source_file','source_filtered_item_index'];assert not fresh.duplicated(key).any();assert not expected.duplicated(key).any()
j=expected.merge(fresh,on=key,how='outer',indicator=True,validate='one_to_one');assert j['_merge'].eq('both').all()
assert (j.amount==j.deal_amount).all() and (j.area==j.area_m2).all() and j.seq.eq(j.apt_seq).all()
assert j.cancel.eq(j.is_canceled.fillna(False)|j.cancel_date.notna()).all();assert pd.to_datetime(j.date).eq(j.deal_date).all()
stagedym=staged.deal_date.dt.strftime('%Y%m');mask=pd.MultiIndex.from_arrays([staged.sigungu_code.astype(str),stagedym]).isin(pairs);kept=rows[rows.source_kind.eq('staged_cached')]
assert len(kept)==(~mask).sum();assert not pd.MultiIndex.from_arrays([kept.sigungu_code.astype(str),kept.deal_date.dt.strftime('%Y%m')]).isin(pairs).any()
old=staged[~mask];cols=['apt_seq','deal_date','deal_amount','area_m2','floor','is_canceled','cancel_date','source_file','source_filtered_item_index']
a=old[cols].sort_values(key).reset_index(drop=True);b=kept[cols].sort_values(key).reset_index(drop=True)
for c in cols:
 if c=='apt_seq':assert a[c].fillna('').astype(str).str.strip().equals(b[c].fillna('').astype(str).str.strip())
 else:assert a[c].equals(b[c]),c
assert rows.area_m2.ge(83).all() and rows.area_m2.lt(85).all();assert rows.sigungu_code.astype(str).str[:2].isin(['11','28','41']).all()
cancel=rows.is_canceled.fillna(False)|rows.cancel_date.notna();valid=(~cancel & rows.deal_date.notna() & rows.deal_amount.gt(0) & rows.apt_seq.fillna('').str.strip().ne('') & rows.deal_date.dt.year.between(2006,2026))
assert valid.eq(rows.included_price_analysis).all();v=rows[valid].copy();v['y']=v.deal_date.dt.year;v['cid']='rtms:'+v.apt_seq.str.strip()
agg=v.groupby(['cid','y']).deal_amount.agg(['median','size']).reset_index();cmp=agg.merge(prices,left_on=['cid','y'],right_on=['complex_id','year'],how='outer',indicator=True,validate='one_to_one')
assert cmp['_merge'].eq('both').all() and cmp['median'].eq(cmp.median_manwon).all() and cmp['size'].eq(cmp.n).all()
assert prices.status.eq(np.where(prices.median_manwon.le(100000),'under','over')).all();assert prices.median_krw.eq(prices.median_manwon*10000).all()
assert len(v)==int(prices.n.sum())==int(states.n.sum())==account['valid_84_price_rows'];assert len(rows)==account['total_84_source_rows'];assert int(cancel.sum())==account['cancelled_rows']
first=v.groupby('cid').y.min();assert cat.set_index('complex_id').first_valid_trade_year.sort_index().astype('int64').equals(first.sort_index().rename('first_valid_trade_year').astype('int64'))
assert not states.duplicated(['complex_id','year']).any();assert len(states)==len(cat)*21
missing=states.n.eq(0);assert states.loc[missing,'median_manwon'].isna().all();assert states.loc[missing,'median_krw'].isna().all()
assert states.status.eq(np.where(states.n.gt(0),np.where(states.median_manwon.le(100000),'under','over'),np.where(states.year.lt(states.first_valid_trade_year),'not_yet_observed','no_trade'))).all()
checks=[]
for y,g in states.groupby('year'):
 s=summary[summary.year.eq(y)].iloc[0];actual={'observed_complexes':int(g.n.gt(0).sum()),'under':int(g.status.eq('under').sum()),'over':int(g.status.eq('over').sum()),'n_valid':int(g.n.sum()),'no_trade':int(g.status.eq('no_trade').sum()),'not_yet_observed':int(g.status.eq('not_yet_observed').sum())}
 assert all(actual[k]==int(s[k]) for k in actual);assert actual['observed_complexes']+actual['no_trade']+actual['not_yet_observed']==len(cat);checks.append({'year':int(y),**actual})
reappear=[]
for cid,g in states.sort_values('year').groupby('complex_id'):
 over=None
 for r in g.itertuples():
  if r.status=='over':over=int(r.year)
  elif r.status=='under' and over is not None:reappear.append({'complex_id':cid,'over_year':over,'under_year':int(r.year),'median_manwon':float(r.median_manwon)});over=None
samples=[]
selectors=[prices[prices.median_manwon.eq(100000)],prices[prices.median_manwon.gt(100000)].sort_values('median_manwon'),prices[prices.n.eq(2)],prices[prices.n.mod(2).eq(1)],prices[prices.n.mod(2).eq(0)]]
for sub in selectors:
 r=sub.iloc[0];vals=sorted(v[(v.cid==r.complex_id)&(v.y==r.year)].deal_amount.tolist());samples.append({'complex_id':r.complex_id,'year':int(r.year),'n':len(vals),'raw_amounts_manwon':vals[:30],'amount_list_truncated':len(vals)>30,'recomputed_median':float(pd.Series(vals).median()),'stored_median':float(r.median_manwon),'status':r.status})
report={'price_source_review_ready':True,'full_map_review_ready':False,'file_hashes':files,'raw_complete_pairs':len(recfiles),'raw_pages':page_count,'raw_all_area_rows':rawcount,'raw_identical_payload_extra_occurrences_preserved':duplicates,'fresh_84_source_pointer_value_rows_verified':len(j),'kept_staged_rows_exact_verified':len(kept),'replaced_old_staged_rows':int(mask.sum()),'total_84_rows':len(rows),'valid_rows':len(v),'cancelled_rows':int(cancel.sum()),'catalog_count':len(cat),'annual_price_groups':len(prices),'state_rows':len(states),'exact_10eok_groups':int(prices.median_manwon.eq(100000).sum()),'reappearance_events':len(reappear),'reappearance_samples':reappear[:8],'median_samples':samples,'annual_summary':checks,'build_year_does_not_filter_valid_rows':True,'no_carry_for_missing':True,'limits':['현재 보유 원문 스냅샷과 266개 보완월의 집계 일관성 검증. 모든 과거 정정·신고를 현재일로 전수 재조회한 것은 아님.','canonical aptSeq 집계이며 실제 부동산 단지 경계·좌표 정밀도·재사용 권리 통과가 아님.','기존 6초 시안은 구 packet으로 새 수치와 일치하지 않음. 새 지도·라벨 검수 필요.']}
(Q/'completed_source_independent_review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in report.items() if k not in ['file_hashes','annual_summary','median_samples','reappearance_samples','limits']},ensure_ascii=True),flush=True)
