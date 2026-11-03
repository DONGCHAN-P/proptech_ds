import pathlib,json,math,hashlib
p=pathlib.Path(__file__).parent
d=json.loads(p.joinpath('data.json').read_text(encoding='utf-8'))
raw=json.loads(p.joinpath('raw_osm.json').read_text(encoding='utf-8'))['elements']
edge={}
for e in raw:
 if e['type']=='way' and e.get('tags',{}).get('highway') and 'geometry' in e:
  v=[(round(x['lon'],5),round(x['lat'],5)) for x in e['geometry']]
  for a,b in zip(v,v[1:]): edge.setdefault((a,b),[]).append(e);edge.setdefault((b,a),[]).append(e)
audit={}
for field in ['walkPoints','accessPoints','egressPoints']:
 route=d['commute'][field];ids=set();flag=[]
 for a,b in zip(route,route[1:]):
  found=edge.get((tuple(a),tuple(b)),[])
  if not found:flag.append('unmapped_edge')
  for e in found:
   ids.add(e['id']);t=e.get('tags',{})
   if t.get('highway') in ['motorway','trunk','motorway_link','trunk_link'] or t.get('access') in ['private','no'] or t.get('foot')=='no':flag.append(e['id'])
 audit[field]=dict(osm_way_ids=sorted(ids),prohibited_tags=flag,edge_count=len(route)-1,qualified_reason='일반도로는 보행 허용 태그 미기재가 있어 보도·횡단보도 현장 검증 미완료')
d['commute']['walking_edge_audit']=audit
d['commute']['station']['displayName']='별내역 4번출구 인근'
d['commute']['station']['source']='https://www.openstreetmap.org/node/12121815056'
d['commute']['notes'].append('경로 종점은4번출구 인근 OSM도로점. 출구까지 약41m 접속 보도 미확인; 임의직선으로 연결하지 않음.')
d['commute']['animation_only']=True
d['sources']=[dict(id='NYJ_RAIL',url='https://nyj.go.kr/www/contents.do?key=3108',location='역사 현황 표',checked_on='2026-10-15'),dict(id='NCUC_EIGHT',url='https://www.ncuc.or.kr/jj_line/2340',location='8호선 연장별내선, 경춘선 별내역 환승',checked_on='2026-10-15'),dict(id='NYJ_BUS48',url='https://www.nyj.go.kr/iframe/selectBbsNttView.do?bbsNo=62&key=51&nttNo=483788',location='2024-07-19 신설 알림;현재운영여부는GBIS로확인',checked_on='2026-10-15'),dict(id='GBIS_CURRENT',url='https://www.gbis.go.kr/service/busInfo/townBus.action?centerId=4136000000&cmd=townBus',location='48번현재노선표',checked_on='2026-10-15'),dict(id='GBIS_PATH',url='https://www.gbis.go.kr/gbis2014/schBusAPI.action?cmd=searchMapLineJson&routeId=241347009',location='result.gg.upLine.list 117개중7번~11번정류장구간',checked_on='2026-10-15'),dict(id='GBIS_STOPS',url='https://www.gbis.go.kr/gbis2014/schBusAPI.action?cmd=searchRouteJson&routeId=241347009',location='result.gg.up.list 7~11번정류장',checked_on='2026-10-15'),dict(id='OSM',url='https://www.openstreetmap.org/copyright',location='raw_osm.json 실제geometry;ODbL기여자표기필수',checked_on='2026-10-15')]
facts=[]
for i,(sentence,status,source,loc) in enumerate([
 ('별내역은 경춘선과8호선 환승역이다.','verified','https://www.ncuc.or.kr/jj_line/2340','시설소개'),
 ('별내별가람·오남·진접은 운영중4호선 진접선역이며 진접선은4호선 연장구간이다.','verified','https://nyj.go.kr/www/contents.do?key=3108','역사현황표'),
 ('8호선 운영선은별내역 종착이며별내별가람역까지 운영연장선으로그리지않는다.','verified','https://www.ncuc.or.kr/jj_line/2340','별내선소개'),
 ('48번은공식GBIS현재노선표 및정류장JSON에 존재한다.','verified',d['sources'][3]['url'],'노선표48'),
 ('48번별내역방향탑승정류장은별가람고등학교.대원칸타빌23241,하차는별내역4번출구.이마트49448이다.','verified',d['sources'][5]['url'],'result.gg.up.list indices6..10'),
 ('대원칸타빌대표진입도로점부터역인근까지표시한도보는실제OSM도로망예시다.','qualified','https://www.openstreetmap.org/way/468641433','serviceway619940668;현장정문/보도미확인'),
 ('4번출구좌표는OSMnode12121815056이며경로끝도로점과약41m차이가있다.','qualified','https://www.openstreetmap.org/node/12121815056','OSM ref4출입구;스냅차이'),
 ('걷기·버스애니메이션속도는이동수단시연이며실제소요시간을검증한값이아니다.','qualified','local:data.json','commute.animation_only')],1):
 facts.append(dict(claim_id=f'RAIL-PROOF-{i:03}',sentence=sentence,status=status,source_url=source,evidence_location=loc,as_of='2026-10-15',verified_on='2026-10-15'))
p.joinpath('data.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
p.joinpath('facts.json').write_text(json.dumps(facts,ensure_ascii=False,indent=2),encoding='utf-8')
h=dict(role='video_research',input_revision='video-v3 / script-v2 / audio-v1',outputs=['data.json','facts.json','raw_osm.json','raw_local_osm.json','searchMapLineJson.json','searchRouteJson.json'],affected_scenes=['RAIL-PROOF-01','기존94~174초'],verified=['공식운영역·노선','GBIS48현재노선·정류장방향·실제선형','OSM 실제도로연결과금지태그검사'],unresolved=['현장단지정문 미확인','도보보도·횡단보도현장통행가능성미확인','4번출구까지41m보도접속미확인','실제분·버스대기/신호 미검증'],next_roles=['video_editor','video_qa'],instructions=['본편통합금지:사용자조각시안검토후결정','운영8호선별내역북쪽회차선표시제외','4호선진접선동색연장으로표시','출구끝점임의직선연결금지'],data_sha256=hashlib.sha256(p.joinpath('data.json').read_bytes()).hexdigest())
p.joinpath('handoff.json').write_text(json.dumps(h,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'data_bytes':p.joinpath('data.json').stat().st_size,'audit':{k:v['prohibited_tags'] for k,v in audit.items()}},ensure_ascii=True))
