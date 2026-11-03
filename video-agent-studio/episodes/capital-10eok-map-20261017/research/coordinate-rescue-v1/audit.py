from pathlib import Path
import json, sqlite3, sys
import pandas as pd
ROOT=Path('C:/projects/realestate_reco')
OUT=Path(__file__).parent
sys.path.insert(0,str(ROOT))
from common import load_secrets
cat=pd.read_parquet(ROOT/'video-agent-studio/episodes/capital-10eok-map-20261017/research/annual-map-v1/complex_catalog.parquet')
mp=pd.read_parquet(ROOT/'video-agent-studio/episodes/capital-10eok-map-20261017/research/annual-map-v1/canonical_map.parquet')
m=pd.read_parquet(ROOT/'master/apt_id_map.parquet').merge(mp,on='apt_id')
old=pd.read_parquet(ROOT/'master/apt_id_map.legacy_20261003_012952.parquet')
k=pd.read_parquet(ROOT/'staged/apt_info_snapshots/kapt_list_20261002.parquet')
shared=cat[cat.coord_quality.eq('excluded_shared_coordinate')]
s=m[m.complex_id.isin(shared.complex_id)].copy()
s['lat5']=s.lat.round(5);s['lng5']=s.lng.round(5)
samples=[]
for loc,g in s.groupby(['lat5','lng5']):
 if g.complex_id.nunique()<2:continue
 samples.append({'location_existing_candidate':list(loc),'complex_count':int(g.complex_id.nunique()),'same_numbered_road_address':g.road_address.nunique()==1,'road_address_count':int(g.road_address.nunique()),'names':g.apt_name_raw.tolist(),'road_addresses':g.road_address.tolist(),'complex_ids':g.complex_id.tolist(),'kapt_codes':g.kapt_code.fillna('').tolist()})
samples.sort(key=lambda x:(x['same_numbered_road_address'],-x['complex_count']))
(OUT/'shared_coordinate_samples.json').write_text(json.dumps(samples[:20],ensure_ascii=False,indent=2),encoding='utf8')
dbinfo={}
db=ROOT/'realestate.db'
if db.exists():
 c=sqlite3.connect('file:'+str(db)+'?mode=ro',uri=True)
 cols=[x[1] for x in c.execute('pragma table_info(apt_master)')]
 dbinfo={'columns':cols}
 if all(x in cols for x in ['apt_seq','lat','lng']):
  d=pd.read_sql_query('select apt_seq,lat,lng from apt_master where lat is not null and lat!=0',c)
  j=m.merge(d,left_on='apt_id',right_on='apt_seq',suffixes=('','_db'))
  dbinfo.update({'coordinate_rows':len(d),'matched_ids':len(j),'coordinates_exactly_same':int(((j.lat-j.lat_db).abs().lt(1e-10)&(j.lng-j.lng_db).abs().lt(1e-10)).sum())})
 c.close()
excluded=m[m.complex_id.isin(cat[~cat.coord_quality.eq('address_geocode_candidate_unverified')].complex_id)]
j=excluded.merge(old[['apt_id','lat','lng']],on='apt_id',suffixes=('','_old'))
report={'checked_on':'2026-10-17','external_address_api_calls':0,'paid_calls':0,'vworld_key_present':bool(load_secrets().get('VWORLD_API_KEY')),'kapt_list_rows':len(k),'kapt_list_columns':k.columns.tolist(),'kapt_precise_coordinates_available':False,'kapt_full_numbered_address_available':False,'shared_coordinate_canonical_count':len(shared),'shared_coordinate_groups':len(samples),'shared_groups_same_numbered_road_address':sum(x['same_numbered_road_address'] for x in samples),'shared_groups_different_numbered_road_addresses':sum(not x['same_numbered_road_address'] for x in samples),'legacy_excluded_id_matches':len(j),'legacy_coord_changed_rows':int(((j.lat-j.lat_old).abs().gt(1e-8)|(j.lng-j.lng_old).abs().gt(1e-8)).sum()),'sqlite':dbinfo,'verified_rescue_count':0,'decision':'Do not call VWorld getCoord for persistent coordinate dataset: official guide explicitly prohibits storage; no bulk authorization implied. Existing candidates remain unverified.'}
(OUT/'audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=False,indent=2))
