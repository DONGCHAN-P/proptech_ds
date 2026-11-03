from pathlib import Path
import pandas as pd,json,hashlib,numpy as np
root=Path('video-agent-studio/episodes/capital-10eok-map-20261017/research/annual-map-v1');root.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
t=pd.read_parquet('master/trade_events.parquet',columns=['apt_id','deal_date','deal_amount','area_m2','is_canceled','build_year','deal_hash']);t=t[(t.area_m2>=83)&(t.area_m2<85)&~t.is_canceled.fillna(False)&t.deal_amount.gt(0)].copy();t['year']=t.deal_date.dt.year
m=pd.read_parquet('master/apt_id_map.parquet'); extra=pd.read_parquet('master/trade_events.parquet',columns=['apt_id','apt_name_raw','apt_name_norm','sigungu_code','legal_dong_code','legal_dong_name','road_address']); extra=extra[extra.apt_id.isin(t.apt_id.unique())&~extra.apt_id.isin(m.apt_id)].drop_duplicates('apt_id'); extra['lat']=np.nan;extra['lng']=np.nan;extra['trade_count']=0;m=pd.concat([m,extra],ignore_index=True);ev=pd.read_parquet('analysis/billion_map_data_audit/staged_identity_evidence.parquet');ev=ev[ev.apt_id.isin(t.apt_id.unique())].copy();ev['apt_seq']=ev.apt_seq.fillna('').str.strip();ev['jibun']=ev.jibun.fillna('').str.strip()
# Conservative: only a unique nonempty official sequence can unify address fragments.
seqs=ev[ev.apt_seq.ne('')].groupby('apt_id').apt_seq.agg(lambda x:sorted(set(x)));mapping={};ambig=[]
for a in t.apt_id.unique():
 s=seqs.get(a,[])
 if len(s)==1:mapping[a]='rtms:'+s[0]
 else:
  sub=ev[ev.apt_id.eq(a)]; parcels=sub.jibun[sub.jibun.ne('')].unique()
  if len(s)==0 and len(parcels)==1 and sub.legal_dong_code.nunique()==1 and sub.apt_name_norm.nunique()==1:
   raw=str(sub.legal_dong_code.iloc[0])+'|'+str(parcels[0])+'|'+str(sub.apt_name_norm.iloc[0]);mapping[a]='parcel:'+hashlib.sha256(raw.encode()).hexdigest()[:20]
  else:mapping[a]='unresolved:'+a;ambig.append(a)
mp=pd.DataFrame([{'apt_id':a,'complex_id':c,'identity_quality':'official_sequence' if c.startswith('rtms:') else ('parcel_name' if c.startswith('parcel:') else 'ambiguous')} for a,c in mapping.items()]);mp.to_parquet(root/'canonical_map.parquet',index=False);mp.to_csv(root/'canonical_map.csv',index=False,encoding='utf-8-sig')
t=t.merge(mp,on='apt_id',validate='many_to_one');m=m.merge(mp,on='apt_id');m['valid_bounds']=m.lat.between(33,39)&m.lng.between(124,132);m['lat5']=m.lat.round(5);m['lng5']=m.lng.round(5)
# Different canonical IDs at same location are suspect; do not jitter them to fake precision.
loc=m[m.valid_bounds].groupby(['lat5','lng5']).complex_id.nunique();shared=set(loc[loc.gt(1)].index)
m['shared_location']=list(zip(m.lat5,m.lng5));m['shared_location']=m.shared_location.isin(shared)
m['sufficient_address']=m.road_address.fillna('').str.strip().str.match(r'^.+\s+\d+(?:-\d+)?$')
cat=[]
trade_groups={k:v for k,v in t.groupby('complex_id')}
for cid,g in m.groupby('complex_id'):
 trade=trade_groups[cid];usable=g[g.valid_bounds&~g.shared_location&g.sufficient_address]
 quality='address_geocode_candidate_unverified';reason=''
 if cid.startswith('unresolved:'):quality='excluded_ambiguous_identity';reason='multiple or missing official sequence/parcel identity'
 elif not g.valid_bounds.any():quality='excluded_missing_coordinate';reason='missing or invalid bounds'
 elif g.shared_location.any():quality='excluded_shared_coordinate';reason='different canonical complexes share rounded5 coordinate'
 elif usable.empty:quality='excluded_ambiguous_address';reason='no full numbered road address'
 elif len(usable)>1:
  spread=max(usable.lat.max()-usable.lat.min(),usable.lng.max()-usable.lng.min())
  if spread>.01:quality='excluded_coordinate_disagreement';reason='same canonical complex coordinates spread > .01 degrees'
 row=(usable if len(usable) else g).sort_values('trade_count',ascending=False).iloc[0]
 by=trade.build_year.dropna().astype(int).unique();cat.append({'complex_id':cid,'name':row.apt_name_raw,'region_code':str(row.sigungu_code)[:2],'lon':float(row.lng) if quality=='address_geocode_candidate_unverified' else None,'lat':float(row.lat) if quality=='address_geocode_candidate_unverified' else None,'first_valid_trade_year':int(trade.year.min()),'build_year':int(by[0]) if len(by)==1 else None,'build_year_conflict':len(by)>1,'coord_quality':quality,'coord_reason':reason,'identity_quality':row.identity_quality,'source_apt_ids':g.apt_id.tolist()})
catalog=pd.DataFrame(cat);catalog.to_parquet(root/'complex_catalog.parquet',index=False)
(root/'complex_catalog.json').write_text(json.dumps(cat,ensure_ascii=False,allow_nan=False),encoding='utf8')
a=t.groupby(['complex_id','year']).deal_amount.agg(median_manwon='median',n='size').reset_index();a['median_krw']=a.median_manwon*10000
frames=[];summ=[]
for year in range(2006,2027):
 y=catalog[['complex_id','first_valid_trade_year','build_year','coord_quality']].merge(a[a.year.eq(year)],on='complex_id',how='left');y['year']=year;y['n']=y.n.fillna(0).astype(int);y['status']=np.where(y.n.gt(0),np.where(y.median_manwon.le(100000),'under','over'),np.where(y.first_valid_trade_year.gt(year),'not_yet_observed','no_trade'));y['map_eligible']=y.coord_quality.eq('address_geocode_candidate_unverified');frames.extend(y[['complex_id','year','status','median_manwon','median_krw','n','map_eligible']].where(pd.notna(y),None).to_dict('records'));s={'year':year,'period':'YTD_through_2026-10-10' if year==2026 else 'calendar_year','observed_complexes':int(y.n.gt(0).sum()),'under':int(y.status.eq('under').sum()),'over':int(y.status.eq('over').sum()),'no_trade':int(y.status.eq('no_trade').sum()),'not_yet_observed':int(y.status.eq('not_yet_observed').sum()),'n_valid':int(y.n.sum()),'single_trade_complexes':int(y.n.eq(1).sum()),'map_observed':int((y.n.gt(0)&y.map_eligible).sum()),'map_under':int((y.status.eq('under')&y.map_eligible).sum()),'map_over':int((y.status.eq('over')&y.map_eligible).sum())};summ.append(s)
# Replace NaN explicitly for JSON interoperability.
for f in frames:
 for k in ['median_manwon','median_krw']:
  if pd.isna(f[k]):f[k]=None
(root/'annual_status.json').write_text(json.dumps(frames,ensure_ascii=False,allow_nan=False,separators=(',',':')),encoding='utf8');pd.DataFrame(summ).to_csv(root/'annual_summary.csv',index=False,encoding='utf-8-sig');(root/'annual_summary.json').write_text(json.dumps(summ,ensure_ascii=False,indent=2),encoding='utf8')
excluded=catalog[~catalog.coord_quality.eq('address_geocode_candidate_unverified')];excluded.to_csv(root/'excluded_complexes.csv',index=False,encoding='utf-8-sig');print('catalog',len(catalog),'quality',catalog.coord_quality.value_counts().to_dict(),'mapping',mp.identity_quality.value_counts().to_dict(),'input eligible',len(t),'output n',sum(s['n_valid'] for s in summ)); print(summ[0]);print(summ[-2]);print(summ[-1])
prov={'checked_on':'2026-10-17','source':'master/trade_events.parquet','source_sha256':sha('master/trade_events.parquet'),'coordinate_source_sha256':sha('master/apt_id_map.parquet'),'eligible_transactions':len(t),'legacy_apt_ids':t.apt_id.nunique(),'canonical_complexes':len(catalog),'quality_counts':catalog.coord_quality.value_counts().to_dict(),'identity_counts':mp.identity_quality.value_counts().to_dict(),'period':['2006-01-01','2026-10-10'],'all_prices_manwon':True,'threshold_manwon':100000,'strict_over':True,'area_gte':83,'area_lt':85,'canceled_excluded':True,'floor_filter':None,'no_trade_carry_forward':False,'reappearance':True,'coordinates_verified':False,'external_calls':0,'paid_calls':0};(root/'provenance.json').write_text(json.dumps(prov,ensure_ascii=False,indent=2),encoding='utf8')

