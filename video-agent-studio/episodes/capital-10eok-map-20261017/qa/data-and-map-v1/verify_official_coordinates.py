from pathlib import Path
import json,struct,zipfile,hashlib,re,math
import pandas as pd
Q=Path(__file__).resolve().parent;EP=Q.parents[1];O=EP/'research/coordinate-link-v2';RAW=O/'raw'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=['coordinate_links_reviewed.parquet','coordinates_verified_source_packet.json','capital_official_geometry.parquet','official_attributes.parquet','validation.json','link_quality_validation.json','ES1001AA00101YY2500_zip.zip']
hashes=[{'file':str(O/f),'sha256':sha(O/f)} for f in files]
zpath=O/'ES1001AA00101YY2500_zip.zip';assert sha(zpath)=='44cd4bd9df1c2582d0e022bd5f630df6709b37cd98ae72ff3cc48676e7dbd2e8'
with zipfile.ZipFile(zpath) as z:
 assert z.testzip() is None
 for name in z.namelist():
  if not name.endswith('/'):assert (RAW/name).read_bytes()==z.read(name)
b=(RAW/'APHUS_HSMP_CNTC_INFO.dbf').read_bytes();n,header,width=struct.unpack_from('<IHH',b,4);fields=[];pos=32
while b[pos]!=13:
 f=b[pos:pos+32];fields.append((f[:11].split(b'\0')[0].decode(),f[16]));pos+=32
records=[]
for i in range(n):
 r=b[header+i*width:header+(i+1)*width];d={'record_index':i,'deleted':r[0]==42};at=1
 for key,size in fields:d[key]=r[at:at+size].decode('utf8').strip();at+=size
 records.append(d)
attrs=pd.read_parquet(O/'official_attributes.parquet');original=pd.DataFrame(records)
assert original.equals(attrs)
shp=(RAW/'APHUS_HSMP_CNTC_INFO.shp').read_bytes();assert struct.unpack_from('>i',shp)[0]==9994;assert struct.unpack_from('>i',shp,24)[0]*2==len(shp);assert struct.unpack_from('<i',shp,32)[0]==5
shapes=[];p=100
while p<len(shp):
 recnum,words=struct.unpack_from('>ii',shp,p);body=shp[p+8:p+8+2*words];typ=struct.unpack_from('<i',body)[0];rings=[]
 if typ:
  assert typ==5
  nr,np=struct.unpack_from('<ii',body,36);starts=list(struct.unpack_from('<'+'i'*nr,body,44))+[np];pts=list(struct.iter_unpack('<dd',body[44+4*nr:44+4*nr+16*np]));rings=[pts[starts[j]:starts[j+1]] for j in range(nr)]
 shapes.append(rings);p+=8+2*words
assert len(shapes)==n==45851
geo=pd.read_parquet(O/'capital_official_geometry.parquet');links=pd.read_parquet(O/'coordinate_links_reviewed.parquet');packet=read(O/'coordinates_verified_source_packet.json')
inp=pd.read_parquet(EP/'research/source-completion-v1/coordinate_join_inputs_complete.parquet')
assert len(links)==links.complex_id.nunique()==9172;assert set(links.apt_seq)==set(inp.apt_seq)
assert not geo.HSMP_INNB.duplicated().any();assert geo.SIGNGU_CD.str[:2].isin(['11','28','41']).all()
def inside(x,y,rings):
 parity=False
 for ring in rings:
  for a,bb in zip(ring,ring[1:]):
   if (a[1]>y)!=(bb[1]>y) and x<(bb[0]-a[0])*(y-a[1])/(bb[1]-a[1])+a[0]:parity=not parity
 return parity
for r in geo.itertuples():
 assert not records[r.record_index]['deleted']
 assert records[r.record_index]['HSMP_INNB']==r.HSMP_INNB and records[r.record_index]['PNU']==r.PNU
 assert inside(r.x_5179,r.y_5179,shapes[r.record_index])
 assert all(getattr(r,k)==records[r.record_index][k] for k,_ in fields)
def norm(x):return re.sub('[^가-힣a-z0-9]','',str(x).lower()).replace('아파트','')
def parcel(x):
 m=re.fullmatch(r'(산\s*)?(\d+)(?:-(\d+))?',str(x).strip())
 return (m[2].zfill(4)+(m[3] or '0').zfill(4),'2' if m[1] else None) if m else (None,None)
byseq={k:v for k,v in inp.groupby('apt_seq')};eligible=links[links.map_eligible];assert len(eligible)==8288
gdict=geo.set_index('HSMP_INNB');join_errors=[];native=[]
namefields=['POT_HSM_NM','BLD_HSM_NM','ROD_HSM_NM','YRAG1_NM','YRAG2_NM','YRAG3_NM']
for r in eligible.itertuples():
 g=gdict.loc[r.HSMP_INNB];assert int(r.record_index)==int(g.record_index);assert r.PNU==g.PNU
 names={norm(g[k]) for k in namefields if g[k]};parcel_hit=False;same_row_hit=False
 for row in byseq[r.apt_seq].itertuples():
  digits,land=parcel(row.jibun);ph=digits is not None and str(row.legal_dong_code)==g.PNU[:10] and digits==g.PNU[11:] and (land is None or land==g.PNU[10])
  parcel_hit|=ph;same_row_hit|=ph and norm(row.apt_name_raw) in names
 if not same_row_hit:join_errors.append(r.complex_id)
 assert r.lon==g.lon and r.lat==g.lat
 native.append({'complex_id':r.complex_id,'official_id':r.HSMP_INNB,'record_index':int(r.record_index),'x_5179':float(g.x_5179),'y_5179':float(g.y_5179)})
many=set(links[links.status.eq('matched')].HSMP_INNB.value_counts().loc[lambda s:s>1].index)
assert not eligible.HSMP_INNB.isin(many).any();assert not eligible.HSMP_INNB.duplicated().any()
assert len(packet['complexes'])==8288
pk=pd.DataFrame(packet['complexes']).set_index('complex_id');assert set(pk.index)==set(eligible.complex_id)
for r in eligible.itertuples():
 v=pk.loc[r.complex_id];assert v.official_complex_id==r.HSMP_INNB and v.official_pnu==r.PNU and v.source_record_index==r.record_index and v.lon==r.lon and v.lat==r.lat
assert not join_errors
prj=(RAW/'APHUS_HSMP_CNTC_INFO.prj').read_text();assert all(x in prj for x in ['GRS_1980','298.257222101','127.5','0.9996','1000000.0','2000000.0','38.0'])
quality=links.link_quality.value_counts().to_dict();assert len(links)-len(eligible)==884
result={'official_source_link_review_ready':True,'native_5179_point_use_ready':True,'full_map_review_ready':False,'source_zip_sha256':sha(zpath),'file_hashes':hashes,'raw_dbf_records_verified':n,'raw_shp_records_verified':len(shapes),'capital_geometry_records_verified':len(geo),'native_points_inside_original_polygons':len(geo),'input_complexes':len(links),'draw_candidates':len(eligible),'excluded':len(links)-len(eligible),'quality_counts':quality,'shared_official_id_rows_excluded':int(links.HSMP_INNB.isin(many).sum()),'strict_same_input_row_parcel_and_name_errors':join_errors,'packet_source_record_pnu_coordinate_mismatches':0,'independent_proj_available':False,'lonlat_transform_independently_verified':False,'native_direct_alternative':'capital_official_geometry.parquet를 공식ID로 조인해 x_5179/y_5179를 직접 사용. 배경도 실제EPSG5179인 경우 동일축 선형viewport로 표시. 현재JSON은lon/lat만 있으므로 사용계약을명시적으로바꿔야 함.','limitations':['원자료 내부 대표점 검증이며 출입구·해당세대·현장 정확도 검증 아님.','공식 2025판의 시차·행정코드개편·제외884개는 남음. 좌표누락을고가로해석하면안됨.','기존Python환경에pyproj/GDAL·명령행PROJ없음. 새 설치·API호출하지않음.','독립 PROJ 변환을 통과했다고 하지 않음. EPSG5179 직접 사용은 역변환 불확실성을 우회할 수 있으나 실제 renderer 입력·배경CRS·draw/label/safe는 다음 검수.']}
(Q/'official_coordinate_independent_review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
(Q/'native_coordinate_audit.json').write_text(json.dumps({'crs':'EPSG:5179','source_geometry_file':str(O/'capital_official_geometry.parquet'),'source_sha256':sha(O/'capital_official_geometry.parquet'),'points':native},ensure_ascii=False,separators=(',',':')),encoding='utf8')
print(json.dumps({k:v for k,v in result.items() if k not in ['file_hashes','limitations','native_direct_alternative']},ensure_ascii=True),flush=True)
