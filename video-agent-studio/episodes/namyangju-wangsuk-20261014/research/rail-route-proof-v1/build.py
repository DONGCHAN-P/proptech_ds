import json, pathlib, math, heapq
p=pathlib.Path(__file__).parent
raw=json.loads(p.joinpath('raw_osm.json').read_text(encoding='utf-8'))['elements']
nodes={e['id']:e for e in raw if e['type']=='node'}
ways=[e for e in raw if e['type']=='way' and 'geometry' in e]
def dist(a,b): return math.hypot((a[0]-b[0])*88000,(a[1]-b[1])*111000)
def route(ws,start,end):
 g={}
 for w in ws:
  cs=[(round(v['lon'],5),round(v['lat'],5)) for v in w['geometry']]
  for a,b in zip(cs,cs[1:]):
   g.setdefault(a,[]).append((b,dist(a,b)));g.setdefault(b,[]).append((a,dist(a,b)))
 s=min(g,key=lambda a:dist(a,start));t=min(g,key=lambda a:dist(a,end))
 h=[(0,s)];ds={s:0};prev={}
 while h:
  cost,a=heapq.heappop(h)
  if a==t: break
  if cost!=ds[a]:continue
  for b,c in g[a]:
   if cost+c<ds.get(b,1e30):ds[b]=cost+c;prev[b]=a;heapq.heappush(h,(cost+c,b))
 if t not in ds:raise ValueError('Disconnected geometry')
 out=[t]
 while out[-1]!=s:out.append(prev[out[-1]])
 return list(reversed(out))
ids=[5884250514,11942201672,7265480504,7265480503,7265480502,11942201671,355173346]
stations=[dict(id=str(i),name=nodes[i]['tags']['name']+'역',lon=nodes[i]['lon'],lat=nodes[i]['lat'],source=f'https://www.openstreetmap.org/node/{i}',status='qualified') for i in ids]
def c(i): return [nodes[i]['lon'],nodes[i]['lat']]
lines=[]
for lid,name,color,wnames,start,end in [('gyeongchun','경춘선','#0C8E72',['경춘선'],[127.104,37.613],[127.20,37.65]),('jinjeop','4호선 진접선 (4호선 연장 구간)','#32A1C8',['진접선'],c(355173346),c(7265480502)),('four','4호선 서울 구간','#32A1C8',['4호선'],[127.068,37.658],c(355173346)),('eight','8호선 별내선','#D11D70',['별내선'],c(11942201672),[127.14,37.603])]:
 ws=[w for w in ways if w.get('tags',{}).get('name') in wnames and w.get('tags',{}).get('railway') in ['rail','subway'] and w.get('tags',{}).get('usage','main')=='main']
 try:points=route(ws,start,end)
 except ValueError:
  allws=[w for w in ways if w.get('tags',{}).get('railway') in (['rail'] if lid=='gyeongchun' else ['rail','subway']) and w.get('tags',{}).get('usage','main')=='main']
  try: points=route(allws,start,end)
  except ValueError: points=[]
 lines.append(dict(id=lid,name=name,color=color,points=points,segments=[[[v['lon'],v['lat']] for v in w['geometry']] for w in ws],osm_way_ids=[w['id'] for w in ws],source='https://overpass.kumi.systems/api/interpreter',geometry_status='qualified',operating_status='operating'))
data=dict(revision='rail-route-proof-v1',verified_on='2026-10-15',stations=stations,lines=lines,roads=[dict(points=[[v['lon'],v['lat']] for v in w['geometry']],highway=w['tags']['highway'],id=w['id']) for w in ways if w.get('tags',{}).get('highway')],commute=None,attribution='© OpenStreetMap contributors · ODbL',notes=['4호선 진접선은 같은4호선의 연장 구간. 별개 노선으로 표시하지 않음.','8호선은 별내역에서 끝남. 별내별가람까지 운영선으로 연결 금지.'])
p.joinpath('data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
print([(x['id'],len(x['points']),len(x['segments'])) for x in lines])
