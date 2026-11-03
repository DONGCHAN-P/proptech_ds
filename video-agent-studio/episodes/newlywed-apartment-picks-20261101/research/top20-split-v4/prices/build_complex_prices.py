"""Aggregate the frozen API rows and attach only unambiguous official complex points."""
from pathlib import Path
from collections import defaultdict,Counter
import json,gzip,hashlib,math,sys
import pandas as pd
D=Path(__file__).resolve().parent;E=D.parents[2];R=E.parents[2]
sys.path.insert(0,str(D));sys.path.insert(0,str(E/'research/top20-explain-v3/prices'))
from price_domain import price_band,BANDS,select_official
from calculate_prices import normalize_name,address_key,in_geojson,in_ring,shape_rings,OFFICIAL
sys.path.insert(0,str(R/'tools/gis_vendor'))
from pyproj import Transformer
SOURCE=E/'research/top20-explain-v3/prices/final-api-20261103-v2'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def save(name,data):(D/name).write_text(json.dumps(data,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def mode(g,col):
    vals=g[col].dropna().astype(str)
    return vals.mode().iloc[0] if len(vals) else ''

def main():
    trades=pd.read_parquet(SOURCE/'api_rows_valid83_85.parquet')
    assert len(trades)==14303 and trades.api_row_id.nunique()==14303
    assert trades.area_m2.between(83,85).all() and (~trades.canceled).all()
    assert trades.deal_date.between('2026-05-01','2026-10-31').all()
    official=pd.read_parquet(OFFICIAL/'capital_official_geometry.parquet')
    byaddr=defaultdict(list)
    for o in official.to_dict('records'):
        o['names_normalized']={normalize_name(o[k]) for k in ['POT_HSM_NM','BLD_HSM_NM','ROD_HSM_NM'] if o[k]}
        key=(str(o['SIGNGU_CD']),str(o['RN']).strip(),int(o['ROAD_HMNO'] or 0),int(o['ROAD_VCNO'] or 0))
        byaddr[key].append(o)
    ranking=read(E/'research/top20-8min-v2/top20.json')['regions']; rankby={r['region_id']:r for r in ranking}
    bounds={rid:json.loads(gzip.decompress((E/'research/top20-explain-v3/prices/snapshots'/f'boundary_{rid}_20241001.geojson.gz').read_bytes())) for rid in rankby}
    to4326=Transformer.from_crs(5179,4326,always_xy=True)
    rows=[]
    for (rid,aid),g in trades.groupby(['region_id','api_complex_id'],sort=True):
        median=float(g.deal_amount_manwon.median());band=price_band(median)
        row={'region_id':rid,'api_complex_id':aid,'name':mode(g,'aptNm'),'dong':mode(g,'umdNm'),'road_address':mode(g,'road_address'),'query_code':mode(g,'query_code'),
             'n':len(g),'median_manwon':median,'median_eok':median/10000,'band':band,'color':BANDS[band]['color'],
             'contract_first':g.deal_date.min(),'contract_last':g.deal_date.max(),'area_min_m2':float(g.area_m2.min()),'area_max_m2':float(g.area_m2.max()),
             'build_year':mode(g,'buildYear'),'floor_min':float(g.floor_value.min()),'floor_max':float(g.floor_value.max()),'coordinate_verified':False}
        rows.append(row)
        if g.road_address.nunique()!=1:row['coordinate_issue']='multiple_road_addresses';continue
        code='28260' if rid=='R01' else row['query_code']
        candidates=byaddr.get(address_key(code,row['road_address']),[])
        o=select_official(candidates,normalize_name(row['name']))
        if o is None:
            row['coordinate_issue']='ambiguous_official_address' if len(candidates)>1 else ('name_not_exact' if candidates else 'address_not_found')
            continue
        lon,lat=to4326.transform(o['x_5179'],o['y_5179'])
        polygons=shape_rings(int(o['record_index']))
        insideofficial=sum(in_ring(o['x_5179'],o['y_5179'],ring) for ring in polygons)%2==1
        insidegu=any(in_geojson(lon,lat,f['geometry']) for f in bounds[rid]['features'])
        if not insideofficial or not insidegu:row['coordinate_issue']='outside_verified_polygon_or_target_region';continue
        row.update(coordinate_verified=True,coordinate_issue=None,official_id=o['HSMP_INNB'],official_record_index=int(o['record_index']),longitude=lon,latitude=lat,x_5179=float(o['x_5179']),y_5179=float(o['y_5179']),households=int(o['NMHSH'] or 0),official_names=[o[k] for k in ['POT_HSM_NM','BLD_HSM_NM','ROD_HSM_NM'] if o[k]])
    # Multiple transaction identities linked to one official polygon remain in the audit, never two points.
    counts=Counter(r['official_id'] for r in rows if r['coordinate_verified'])
    for row in rows:
        if row['coordinate_verified'] and counts[row['official_id']]>1:
            row.update(coordinate_verified=False,coordinate_issue='multiple_api_ids_for_one_official_complex')
    assert sum(r['n'] for r in rows)==14303 and len(rows)==2304
    regions=[];v3={r['region_id']:r for r in read(SOURCE/'regional_prices.json')['rows']}
    for rank in ranking:
        rid=rank['region_id'];allrows=[r for r in rows if r['region_id']==rid];mapped=[r for r in allrows if r['coordinate_verified']];g=trades[trades.region_id==rid]
        old=v3[rid];assert len(g)==old['n'] and float(g.deal_amount_manwon.median())==old['median_manwon']
        regions.append({**{k:rank[k] for k in ['region_id','rank','province','region','scene_id']},'region_median_manwon':old['median_manwon'],'transaction_n':len(g),'observed_complexes':len(allrows),'mapped_complexes':len(mapped),'mapped_transaction_n':sum(r['n'] for r in mapped),'unmapped_reasons':dict(Counter(r['coordinate_issue'] for r in allrows if not r['coordinate_verified'])),'price_band_counts_all_observed':[sum(r['band']==b for r in allrows) for b in range(6)],'price_band_counts_mapped':[sum(r['band']==b for r in mapped) for b in range(6)],'mapped_min_manwon':min((r['median_manwon'] for r in mapped),default=None),'mapped_max_manwon':max((r['median_manwon'] for r in mapped),default=None)})
    save('legend.json',{'unit':'만원','bands':BANDS,'boundary_rule':'lower_inclusive_upper_exclusive','period':['2026-05-01','2026-10-31'],'retrieved_date':'2026-11-03','area_m2':[83,85],'statistic':'per-api-complex median of recorded uncancelled individual transactions','point':'one location-verified official complex internal point','sample_rule':'n>=1; selected labels show n','school_symbol':'square','station_symbol':'rounded_square','commerce_symbol':'diamond'})
    save('complex_prices.json',{'rows':rows});save('coverage.json',{'regions':regions,'observed_complexes':len(rows),'mapped_complexes':sum(r['coordinate_verified'] for r in rows),'transaction_n':14303,'external_calls':0,'additional_normal_trade_deduplication':False,'source_sha256':{p.name:digest(p) for p in [SOURCE/'api_rows_valid83_85.parquet',SOURCE/'regional_prices.json',OFFICIAL/'capital_official_geometry.parquet']}})
    pd.DataFrame(rows).drop(columns=['official_names'],errors='ignore').to_csv(D/'complex_prices.csv',index=False,encoding='utf-8-sig')
    print(json.dumps({'observed_complexes':len(rows),'mapped_complexes':sum(r['coordinate_verified'] for r in rows),'regions':len(regions),'transaction_n':14303,'map_counts':{r['region_id']:r['mapped_complexes'] for r in regions}},ensure_ascii=False))

if __name__=='__main__':main()
