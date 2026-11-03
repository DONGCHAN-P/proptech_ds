from pathlib import Path
import pandas as pd,json,math,hashlib
O=Path(__file__).parent
d=pd.read_parquet(O/'capital_official_geometry.parquet');t=pd.read_parquet(O/'coordinate_links.parquet')
def forward(lon,lat):
 a=6378137.;f=1/298.257222101;e2=f*(2-f);ep2=e2/(1-e2);k=.9996;p=math.radians(lat);p0=math.radians(38);L=math.radians(lon-127.5)
 def mer(p):return a*((1-e2/4-3*e2**2/64-5*e2**3/256)*p-(3*e2/8+3*e2**2/32+45*e2**3/1024)*math.sin(2*p)+(15*e2**2/256+45*e2**3/1024)*math.sin(4*p)-35*e2**3/3072*math.sin(6*p))
 N=a/math.sqrt(1-e2*math.sin(p)**2);T=math.tan(p)**2;C=ep2*math.cos(p)**2;A=math.cos(p)*L
 x=1000000+k*N*(A+(1-T+C)*A**3/6+(5-18*T+T*T+72*C-58*ep2)*A**5/120)
 y=2000000+k*(mer(p)-mer(p0)+N*math.tan(p)*(A*A/2+(5-T+9*C+4*C*C)*A**4/24+(61-58*T+T*T+600*C-330*ep2)*A**6/720))
 return x,y
errors=[]
for v in d.itertuples():
 x,y=forward(v.lon,v.lat);errors.append(math.hypot(x-v.x_5179,y-v.y_5179))
assert max(errors)<.02
many=set(t[t.status.eq('matched')].HSMP_INNB.value_counts().loc[lambda x:x>1].index)
t['link_quality']='unmatched';t.loc[t.status.eq('ambiguous'),'link_quality']='ambiguous_multiple_official_candidates'
t.loc[t.method.eq('exact_parcel_unique_official_complex'),'link_quality']='review_unique_parcel_name_mismatch'
t.loc[t.method.eq('exact_parcel_and_normalized_name'),'link_quality']='exact_parcel_name'
t.loc[t.HSMP_INNB.isin(many),'link_quality']='review_shared_official_complex'
t['map_eligible']=t.link_quality.eq('exact_parcel_name')
t.to_parquet(O/'coordinate_links_reviewed.parquet',index=False);t.to_csv(O/'coordinate_links_reviewed.csv',index=False,encoding='utf-8-sig')
keep=t[t.map_eligible].copy();geo=d.set_index('HSMP_INNB')
packet=[]
for v in keep.itertuples():
 row=geo.loc[v.HSMP_INNB]
 if isinstance(row,pd.DataFrame):raise AssertionError('official identifier duplicated')
 packet.append({'complex_id':v.complex_id,'apt_seq':v.apt_seq,'name':v.name,'lon':v.lon,'lat':v.lat,'official_complex_id':v.HSMP_INNB,'official_pnu':v.PNU,'match_method':v.method,'coordinate_source':'REB apartment complex linkage 2025 SHP','point_role':'polygon interior representative; not entrance or measured household position','source_record_index':v.record_index})
(O/'coordinates_verified_source_packet.json').write_text(json.dumps({'schema':'official_polygon_coordinates_v2','precise_address_matching':True,'coordinate_transform_independently_checked':False,'prototype_until_transform_review':True,'source_zip_sha256':hashlib.sha256((O/'ES1001AA00101YY2500_zip.zip').read_bytes()).hexdigest(),'complexes':packet},ensure_ascii=False,separators=(',',':')),encoding='utf8')
check={'roundtrip_algorithm':'independent forward series against inverse series in link.py; not independent PROJ library','native_crs':'EPSG:5179','test_count':len(d),'max_roundtrip_error_m':max(errors),'origin_test_lon_lat':forward(127.5,38),'quality_counts':t.link_quality.value_counts().to_dict(),'eligible_without_identity_conflicts':int(t.map_eligible.sum()),'shared_official_complex_rows':int(t.HSMP_INNB.isin(many).sum()),'independent_proj_check_pending':True}
(O/'link_quality_validation.json').write_text(json.dumps(check,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(check,ensure_ascii=False,indent=2))
