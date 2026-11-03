import json,pathlib,math
p=pathlib.Path(__file__).parent;ep=p.parent.parent
raw=json.loads((ep/'research/rail-route-proof-v1/raw_osm.json').read_text(encoding='utf-8'));nodes={e['id']:[e['lon'],e['lat']]for e in raw['elements']if e['type']=='node'}
targets=[('wangsuk',[127.16230,37.65391],'경춘선'),('ilpae',[127.17994,37.61529],'중앙선')]
res=[]
for id,q,name in targets:
 best=None;kx=111320*math.cos(math.radians(q[1]));ky=111320
 for w in raw['elements']:
  if w['type']!='way' or name not in w.get('tags',{}).get('name','') or w.get('tags',{}).get('railway')!='rail':continue
  pts=w.get('geometry') or [{'lon':nodes[n][0],'lat':nodes[n][1]}for n in w.get('nodes',[])if n in nodes]
  for a,b in zip(pts,pts[1:]):
   a=[a['lon'],a['lat']];b=[b['lon'],b['lat']];u=[(b[0]-a[0])*kx,(b[1]-a[1])*ky];v=[(q[0]-a[0])*kx,(q[1]-a[1])*ky];den=u[0]**2+u[1]**2;t=max(0,min(1,sum(x*y for x,y in zip(u,v))/den))if den else 0
   z=[a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])];d=math.hypot((q[0]-z[0])*kx,(q[1]-z[1])*ky)
   if best is None or d<best['distance_m']:best=dict(way_id=w['id'],rail_name=w['tags']['name'],distance_m=d,nearest_existing_track_point=z)
 res.append(dict(station=id,old_approx=q,nearest_track_check=best))
(p/'old_coordinates_audit.json').write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(res,ensure_ascii=False))

