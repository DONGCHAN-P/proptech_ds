from pathlib import Path
import zipfile,hashlib,json,struct,math,re,shutil
import pandas as pd
ROOT=Path('C:/projects/realestate_reco'); E=ROOT/'video-agent-studio/episodes/capital-10eok-map-20261017'; OUT=Path(__file__).parent
SRC=Path('C:/Users/e2ken/Downloads/ES1001AA00101YY2500_zip.zip'); ZIP=OUT/SRC.name; RAW=OUT/'raw';RAW.mkdir(exist_ok=True)
shutil.copy2(SRC,ZIP)
with zipfile.ZipFile(ZIP) as z:
 assert z.testzip() is None
 for f in z.infolist():
  dest=(RAW/f.filename).resolve();assert dest.is_relative_to(RAW.resolve()) and not Path(f.filename).is_absolute()
 z.extractall(RAW)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
b=(RAW/'APHUS_HSMP_CNTC_INFO.dbf').read_bytes();n,h,r=struct.unpack_from('<IHH',b,4);fields=[];p=32
while b[p]!=13:
 q=b[p:p+32];fields.append({'name':q[:11].split(b'\0')[0].decode(),'type':chr(q[11]),'width':q[16],'decimals':q[17]});p+=32
rows=[]
for i in range(n):
 record=b[h+i*r:h+(i+1)*r];assert len(record)==r
 row={'record_index':i,'deleted':record[0]==42};p=1
 for f in fields:row[f['name']]=record[p:p+f['width']].decode('utf8').strip();p+=f['width']
 rows.append(row)
d=pd.DataFrame(rows);d.to_parquet(OUT/'official_attributes.parquet',index=False)
s=(RAW/'APHUS_HSMP_CNTC_INFO.shp').read_bytes();assert struct.unpack_from('>i',s)[0]==9994;assert struct.unpack_from('<i',s,32)[0]==5
assert struct.unpack_from('>i',s,24)[0]*2==len(s)
shapes=[];p=100
while p<len(s):
 no,words=struct.unpack_from('>2i',s,p);q=s[p+8:p+8+2*words];typ=struct.unpack_from('<i',q)[0]
 if typ==0:shapes.append([])
 else:
  assert typ==5;nr,np=struct.unpack_from('<2i',q,36);starts=list(struct.unpack_from('<'+'i'*nr,q,44))+[np];pts=list(struct.iter_unpack('<2d',q[44+4*nr:44+4*nr+16*np]));shapes.append([pts[starts[j]:starts[j+1]] for j in range(nr)])
 p+=8+2*words
assert len(shapes)==n
# Standard ellipsoidal Transverse Mercator inverse, EPSG:5179 parameters from .prj.
def inverse(x,y):
 a=6378137.;f=1/298.257222101;e2=f*(2-f);ep2=e2/(1-e2);k=.9996;lat0=math.radians(38)
 def mer(phi):return a*((1-e2/4-3*e2**2/64-5*e2**3/256)*phi-(3*e2/8+3*e2**2/32+45*e2**3/1024)*math.sin(2*phi)+(15*e2**2/256+45*e2**3/1024)*math.sin(4*phi)-35*e2**3/3072*math.sin(6*phi))
 M=mer(lat0)+(y-2000000)/k;mu=M/(a*(1-e2/4-3*e2**2/64-5*e2**3/256));e1=(1-math.sqrt(1-e2))/(1+math.sqrt(1-e2))
 ph=mu+(3*e1/2-27*e1**3/32)*math.sin(2*mu)+(21*e1**2/16-55*e1**4/32)*math.sin(4*mu)+151*e1**3/96*math.sin(6*mu)+1097*e1**4/512*math.sin(8*mu)
 N=a/math.sqrt(1-e2*math.sin(ph)**2);R=a*(1-e2)/(1-e2*math.sin(ph)**2)**1.5;T=math.tan(ph)**2;C=ep2*math.cos(ph)**2;D=(x-1000000)/(N*k)
 lat=ph-N*math.tan(ph)/R*(D*D/2-(5+3*T+10*C-4*C*C-9*ep2)*D**4/24+(61+90*T+298*C+45*T*T-252*ep2-3*C*C)*D**6/720)
 lon=math.radians(127.5)+(D-(1+2*T+C)*D**3/6+(5-2*C+28*T-3*C*C+8*ep2+24*T*T)*D**5/120)/math.cos(ph)
 return math.degrees(lon),math.degrees(lat)
def inside(pt,rings):
 x,y=pt;c=False
 for ring in rings:
  for (x1,y1),(x2,y2) in zip(ring,ring[1:]):
   if (y1>y)!=(y2>y) and x<(x2-x1)*(y-y1)/(y2-y1)+x1:c=not c
 return c
def point(rings):
 # Scanline midpoint selected from polygon interior; never bbox centre assumed inside.
 yy=sorted({v[1] for ring in rings for v in ring}); tests=[(yy[0]+yy[-1])/2]+[(a+b)/2 for a,b in zip(yy,yy[1:])]
 best=None
 for y in tests:
  xx=[]
  for ring in rings:
   for (x1,y1),(x2,y2) in zip(ring,ring[1:]):
    if (y1>y)!=(y2>y):xx.append(x1+(y-y1)*(x2-x1)/(y2-y1))
  xx.sort()
  for a,b in zip(xx[::2],xx[1::2]):
   if best is None or b-a>best[0]:best=(b-a,(a+b)/2,y)
 assert best;pt=best[1:];assert inside(pt,rings);return pt
g=[]
for row,rings in zip(rows,shapes):
 if row['deleted'] or not rings:continue
 pt=point(rings);lon,lat=inverse(*pt);assert 124<lon<132 and 33<lat<40
 g.append({'record_index':row['record_index'],'lon':lon,'lat':lat,'x_5179':pt[0],'y_5179':pt[1],'inside_polygon':True})
geo=pd.DataFrame(g);d=d.merge(geo,on='record_index',validate='one_to_one');d['parcel_key']=d.PNU.str[:10]+'|'+d.PNU.str[11:];d['land_flag']=d.PNU.str[10:11]
d=d[d.SIGNGU_CD.str.startswith(('11','28','41'))].copy();d.to_parquet(OUT/'capital_official_geometry.parquet',index=False)
inp=E/'research/source-completion-v1/coordinate_join_inputs_complete.parquet';t=pd.read_parquet(inp)
def parcel(v):
 v=str(v).strip();m=re.fullmatch(r'(산\s*)?(\d+)(?:-(\d+))?',v)
 return (m[2].zfill(4)+(m[3] or '0').zfill(4), '2' if m[1] else None) if m else (None,None)
def norm(v):return re.sub(r'[^가-힣a-z0-9]','',str(v).lower()).replace('아파트','')
results=[];candidates=[];groups={k:v for k,v in d.groupby('parcel_key')}
for seq,grp in t.groupby('apt_seq'):
 matched={};issues=[]
 for _,v in grp.iterrows():
  par,land=parcel(v.jibun)
  if not par:issues.append('unparseable_parcel');continue
  k=str(v.legal_dong_code)+'|'+par;hits=groups.get(k)
  if hits is None:continue
  if land:hits=hits[hits.land_flag.eq(land)]
  for _,u in hits.iterrows():matched[u.HSMP_INNB]=u
 hs=list(matched.values());chosen=None;method='';name_ok=False
 for u in hs:
  for _,v in grp.iterrows():
   names=[norm(u[x]) for x in ['POT_HSM_NM','BLD_HSM_NM','ROD_HSM_NM','YRAG1_NM','YRAG2_NM','YRAG3_NM'] if u[x]]
   if norm(v.apt_name_raw) in names:candidates.append({'apt_seq':seq,'HSMP_INNB':u.HSMP_INNB,'reason':'exact_parcel_and_normalized_name'})
 exact={x['HSMP_INNB'] for x in candidates if x['apt_seq']==seq}
 if len(exact)==1:chosen=matched[next(iter(exact))];method='exact_parcel_and_normalized_name';name_ok=True
 elif len(hs)==1:chosen=hs[0];method='exact_parcel_unique_official_complex'
 status='matched' if chosen is not None else ('ambiguous' if hs else 'unmatched')
 row={'complex_id':'rtms:'+str(seq),'apt_seq':seq,'name':grp.apt_name_raw.iloc[0],'status':status,'method':method,'official_candidate_count':len(hs),'name_exact':name_ok,'HSMP_INNB':chosen.HSMP_INNB if chosen is not None else None,'PNU':chosen.PNU if chosen is not None else None,'lon':chosen.lon if chosen is not None else None,'lat':chosen.lat if chosen is not None else None,'record_index':int(chosen.record_index) if chosen is not None else None,'candidate_ids':[u.HSMP_INNB for u in hs]}
 results.append(row)
res=pd.DataFrame(results);res.to_parquet(OUT/'coordinate_links.parquet',index=False);res.to_csv(OUT/'coordinate_links.csv',index=False,encoding='utf-8-sig')
summary={'source_zip':str(SRC),'workspace_zip_sha256':sha(ZIP),'original_zip_sha256':sha(SRC),'zip_crc_valid':True,'original_preserved':True,'record_count':n,'shape_count':len(shapes),'fields':fields,'crs_identified':'EPSG:5179','crs_basis':'actual .prj parameters','point_method':'longest interior scanline midpoint, validated point-in-polygon in native CRS','coordinate_transform':'standard ellipsoidal inverse Transverse Mercator series; independent PROJ check pending','capital_official_records':len(d),'input_sha256':sha(inp),'input_rows':len(t),'input_apt_seq':int(t.apt_seq.nunique()),'status_counts':res.status.value_counts().to_dict(),'method_counts':res.method.value_counts().to_dict(),'all_coordinates_precise_place_verified':False,'external_api_calls':0,'paid_calls':0,'download_source_url':'https://www.bigdata-realestate.kr/rebpp/usr/prd/prdInfoDetail.do?req_productId=1','source_version':'2025, listed 2026-01-05, user-provided official download','license_basis':'official REBPP PUBLIC and public-work free-use notice; retain attribution; inspect package notes (none beyond SHP components)'}
(OUT/'validation.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in summary.items() if k!='fields'},ensure_ascii=False,indent=2))
