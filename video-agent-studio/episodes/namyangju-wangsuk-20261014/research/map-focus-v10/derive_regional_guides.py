import pathlib,json,math
p=pathlib.Path(__file__).parent;ep=p.parent.parent
raw=json.loads((ep/'research/rail-route-proof-v1/raw_osm.json').read_text(encoding='utf-8'))
geo={}
for e in raw['elements']:
 if e.get('type')=='node' and e.get('tags',{}).get('railway')=='station' and e['tags'].get('name')in['퇴계원','사릉','금곡','도농','양정']:geo[e['tags']['name']]=[e['lon'],e['lat']]
geo.update({'별내':[127.1278172,37.6420348],'다산':[127.1497626,37.6243286]})
def solve(A,b):
 a=[r[:]+[v]for r,v in zip(A,b)]
 for i in range(3):
  k=max(range(i,3),key=lambda k:abs(a[k][i]));a[i],a[k]=a[k],a[i];s=a[i][i];a[i]=[v/s for v in a[i]]
  for j in range(3):
   if j!=i:
    s=a[j][i];a[j]=[v-s*w for v,w in zip(a[j],a[i])]
 return [r[3]for r in a]
def fit(points):
 X=[[x,y,1]for _,[x,y]in points];M=[[sum(r[i]*r[j]for r in X)for j in range(3)]for i in range(3)]
 return [solve(M,[sum(r[i]*geo[name][axis]for r,(name,_)in zip(X,points))for i in range(3)])for axis in range(2)]
def ev(coef,xy):return [sum(c*v for c,v in zip(a,[*xy,1]))for a in coef]
def dist(a,b):return math.hypot((a[0]-b[0])*111320*math.cos(math.radians(a[1])),(a[1]-b[1])*111320)
sets=[dict(id='w1_regional',image='regional_rail_reference.png',source='w1_a1_pamphlet.pdf',page=4,clip=[910,550,1180,755],scale=4,points=[('별내',[84,301]),('퇴계원',[237,233]),('사릉',[509,194]),('금곡',[791,355]),('다산',[300,488]),('도농',[389,664]),('양정',[679,719])],target=[390,168],station_id='wangsuk_planned'),dict(id='w2_regional',image='w2_regional_rail_reference.png',source='w2_a3_pamphlet.pdf',page=4,clip=[920,410,1240,655],scale=4,points=[('별내',[39,229]),('퇴계원',[238,135]),('사릉',[597,86]),('금곡',[967,295]),('다산',[322,471]),('도농',[439,701]),('양정',[819,775])],target=[654,609],station_id='ilpae_planned')]
results=[]
for d in sets:
 coef=fit(d['points']);res=[dict(name=n,pixel=xy,lonlat=geo[n],residual_m=round(dist(ev(coef,xy),geo[n]),1))for n,xy in d['points']]
 cv=[]
 for n,xy in d['points']:cv.append(dist(ev(fit([(nn,xx)for nn,xx in d['points']if nn!=n]),xy),geo[n]))
 pred=ev(coef,d['target']);results.append(dict(**d,lonlat=[round(v,5)for v in pred],coefficients=coef,controlpoints=res,residual_rms_m=round(math.sqrt(sum(r['residual_m']**2 for r in res)/len(res)),1),leave_one_out_max_error_m=round(max(cv),1),position_status='approximate_reading_of_official_regional_schematic_not_published_station_GPS',recommended_uncertainty_radius_m=max(500,round(max(cv)/100)*100),source_terms='public official location diagram; direct original raster is reference only; newly drawn geographic guide pin is an approximation',prohibited='Do not label surveyed/exact entrance coordinates; no station access route or distance inference.'))
(p/'regional_registration_evidence.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
a=json.loads((p/'anchors.json').read_text(encoding='utf-8'))
for s in a['stations']:
 r=next(r for r in results if r['station_id']==s['id']);s.update(lonlat=r['lonlat'],gis_label=s['label']+' · 위치 개략',gis_position_status=r['position_status'],gis_uncertainty_radius_m=r['recommended_uncertainty_radius_m'],gis_evidence='research/map-focus-v10/regional_registration_evidence.json',gis_method='Official LH regional diagram planned station symbol fit against seven existing station locations from stored OSM. Broad guidance only, no legal/geodetic registration.',gis_required_note='계획역 위치 개략 · 공개 교통도 기준 추정 안내 · 출입구 아님')
a['revision']='map-focus-v10-with-qualified-regional-guides';a['limitations'][0]='Station WGS84s are independently estimated regional schematic guides with 500m+ uncertainty, NOT official exact coordinates.'
(p/'anchors.json').write_text(json.dumps(a,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps([{k:v for k,v in r.items()if k in ['station_id','lonlat','residual_rms_m','leave_one_out_max_error_m','recommended_uncertainty_radius_m']}for r in results]))
