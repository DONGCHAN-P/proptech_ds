exec(compile(open(__file__.replace('commute.py','build.py'),encoding='utf-8').read(),'build.py','exec'))
R=6378137
def ll(e):return [float(e['lon'])/R*180/math.pi,(2*math.atan(math.exp(float(e['lat'])/R))-math.pi/2)*180/math.pi]
gbis=json.loads(p.joinpath('searchRouteJson.json').read_text(encoding='utf-8'))['result']['gg']['up']['list']
stops=[dict(id=e['stationId'],name=e['stationNm'],point=ll(e),stationNo=e['stationNo']) for e in gbis]
bl=json.loads(p.joinpath('searchMapLineJson.json').read_text(encoding='utf-8'))['result']['gg']['upLine']['list']
bp=[ll(e) for e in bl]
b0,b1=stops[6],stops[10]
i=min(range(len(bp)),key=lambda i:dist(bp[i],b0['point']));j=min(range(len(bp)),key=lambda j:dist(bp[j],b1['point']))
bus=bp[i:j+1]
local=raw+(json.loads(p.joinpath('raw_local_osm.json').read_text(encoding='utf-8'))['elements'] if p.joinpath('raw_local_osm.json').exists() else [])
roads=[e for e in local if e['type']=='way' and e.get('tags',{}).get('highway') and 'geometry' in e and e['tags'].get('highway') not in ['motorway','motorway_link','trunk','trunk_link'] and e['tags'].get('foot')!='no' and e['tags'].get('access') not in ['no','private']]
apt=next(e for e in raw if e['id']==468641433)
entrances=[e for e in local if e['type']=='node' and e.get('tags',{}).get('entrance') and 37.6607<e['lat']<37.6631 and 127.1231<e['lon']<127.1265]
print('entrances',entrances)
service=[e for e in roads if e.get('tags',{}).get('highway')=='service' and any(37.6608<v['lat']<37.6630 and 127.1233<v['lon']<127.1264 for v in e['geometry'])]
print('service',[(e['id'],e.get('tags'),e['geometry'][0],e['geometry'][-1]) for e in service])
if entrances:origin=[entrances[0]['lon'],entrances[0]['lat']]
else:
 # Actual mapped service-road point at the apartment boundary, not an invented entrance.
 candidates=[(v['lon'],v['lat']) for e in service for v in e['geometry'] if 37.6608<v['lat']<37.6630 and 127.1233<v['lon']<127.1264]
 origin=min(candidates,key=lambda a:dist(a,b0['point']))
target=c(11942201672)
exits=[e for e in local if e['type']=='node' and e.get('tags',{}).get('railway')=='subway_entrance' and 37.640<e['lat']<37.644 and 127.124<e['lon']<127.130]
print('exits',[(e['id'],e.get('tags'),e['lon'],e['lat']) for e in exits])
if exits:
 ex=next(e for e in exits if e.get('tags',{}).get('ref')=='4');target=[ex['lon'],ex['lat']]
walk=route(roads,origin,target)
access=route(roads,origin,b0['point'])
egress=route(roads,b1['point'],target)
data['commute']=dict(apartment=dict(name='남양주별내 대원칸타빌',lon=origin[0],lat=origin[1],source='https://www.openstreetmap.org/way/468641433',origin_basis='OSM 단지 내부 실제 진입도로 점 · 현장 출입구 미확인'),station=dict(name='별내역',lon=target[0],lat=target[1]),walkPoints=walk,busPoints=bus,accessPoints=access,egressPoints=egress,busRoute='48',routeId='241347009',boarding=b0,alighting=b1,stops=stops[6:11],apartmentBoundary=[[v['lon'],v['lat']] for v in apt['geometry']],notes=['애니메이션 속도는 이동수단 구분 시연. 실제 소요시간 비교 아님.','버스 대기·신호·정류장 정차시간 미산정.','도보는 OSM도로망 예시. 현장 보도 및 횡단보도 통행가능성 별도 확인 필요.'],walking_status='qualified',bus_geometry_status='verified_official_GBIS',source='https://www.gbis.go.kr/gbis2014/schBusAPI.action?cmd=searchMapLineJson&routeId=241347009')
data['commute']['endpoint_basis']=dict(target_node_id=ex['id'] if exits else 11942201672,target_name=ex.get('tags') if exits else 'station centroid; no exact entrance confirmed',walk_end_snap_m=dist(walk[-1],target),access_to_boarding_snap_m=dist(access[-1],b0['point']),bus_start_to_boarding_m=dist(bus[0],b0['point']),bus_end_to_alighting_m=dist(bus[-1],b1['point']),egress_start_to_alighting_m=dist(egress[0],b1['point']))
data['localMap']=dict(roads=[dict(id=e['id'],highway=e['tags']['highway'],points=[[v['lon'],v['lat']] for v in e['geometry']]) for e in roads],buildings=[dict(id=e['id'],points=[[v['lon'],v['lat']] for v in e['geometry']]) for e in local if e['type']=='way' and e.get('tags',{}).get('building') and 'geometry' in e],water=[dict(id=e['id'],points=[[v['lon'],v['lat']] for v in e['geometry']]) for e in local if e['type']=='way' and (e.get('tags',{}).get('waterway') or e.get('tags',{}).get('natural')=='water') and 'geometry' in e])
p.joinpath('data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
print('commute',len(walk),len(bus),len(access),len(egress),origin,target)
