import json,pathlib,math,html,hashlib
from PIL import Image,ImageDraw,ImageFont
p=pathlib.Path(__file__).resolve().parent;ep=p.parent.parent;out=ep/'outputs/geographic-v1';out.mkdir(parents=True,exist_ok=True)
data=json.loads((p/'raw/osm.json').read_text(encoding='utf-8')); es=data['elements']; byid={e['id']:e for e in es}
FONT='C:/Windows/Fonts/malgun.ttf'; BOLD='C:/Windows/Fonts/malgunbd.ttf'
INK='#173348'; GRAY='#637580'; BLUE='#286cda'; BG='#f6f4ef'
def font(s,b=False):return ImageFont.truetype(BOLD if b else FONT,s)
def coord(e):
 if 'lat' in e:return e['lon'],e['lat']
 if 'center' in e:return e['center']['lon'],e['center']['lat']
 g=e.get('geometry',[])
 return ((min(v['lon'] for v in g)+max(v['lon'] for v in g))/2,(min(v['lat'] for v in g)+max(v['lat'] for v in g))/2)
stations={}
for e in es:
 t=e.get('tags',{})
 if t.get('railway')=='station':stations.setdefault(t['name'],e)
apartments=[e for e in es if e.get('tags',{}).get('residential')=='apartments' and any(s in e['tags'].get('name','') for s in ['삼송2차아이파크','원흥역센트럴','센트럴더포레','지축역센트럴','북한산파크뷰'])]
ikea=byid[470129335];lotte=byid[5314858843]
features=[]
for e in es:
 if e['type']=='way' and e.get('geometry'):
  g={'type':'LineString','coordinates':[[v['lon'],v['lat']] for v in e['geometry']]}
  if e.get('tags',{}).get('residential')=='apartments' or e['id']==ikea['id']:g['type']='Polygon';g['coordinates']=[g['coordinates']]
 elif 'lat'in e:g={'type':'Point','coordinates':[e['lon'],e['lat']]}
 else:continue
 features.append(dict(type='Feature',id=f'{e["type"]}/{e["id"]}',properties=e.get('tags',{}),geometry=g))
(p/'osm_subset.geojson').write_text(json.dumps(dict(type='FeatureCollection',features=features),ensure_ascii=False),encoding='utf-8')
locs=[]
for e in list(stations.values())+apartments+[ikea,lotte]:
 lon,lat=coord(e);locs.append(dict(name=e['tags'].get('name'),osm_type=e['type'],osm_id=e['id'],lon=lon,lat=lat,coordinate_basis='station node' if e in stations.values() else 'OSM point' if e['type']=='node' else 'geometry bounding-box center; not entrance',source_url=f'https://www.openstreetmap.org/{e["type"]}/{e["id"]}',tags=e['tags']))
(p/'locations.json').write_text(json.dumps(locs,ensure_ascii=False,indent=2),encoding='utf-8')
pages=[]
def make(name,title,bbox,local=False):
 W,H=1920,1080;im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im);svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080"><rect width="1920" height="1080" fill="{BG}"/>']
 def txt(t,x,y,s=27,c=INK,b=False):
  if x>=1390:
   while d.textlength(t,font=font(s,b))>430 and s>19:s-=1
  d.text((x,y),t,font=font(s,b),fill=c);svg.append(f'<text x="{x}" y="{y+s}" font-family="Malgun Gothic" font-size="{s}" font-weight="{700 if b else 400}" fill="{c}">{html.escape(t)}</text>')
 txt('데이터로 보는 부동산 / 고양 창릉 · 실제 지리 지도',80,35,24,GRAY)
 txt(title,80,85,46,INK,True)
 txt('OSM 실제 지리 벡터 / 북쪽 위 / 확인 대상만 표시 · 출입구·보행경로·계획역 정밀점 없음',80,154,25,GRAY)
 left,top,mw,mh=80,220,1260,640
 lon0,lat0,lon1,lat1=bbox;cos=math.cos(math.radians((lat0+lat1)/2));scale=min(mw/((lon1-lon0)*cos),mh/(lat1-lat0));ww=(lon1-lon0)*cos*scale;hh=(lat1-lat0)*scale;ox=(mw-ww)/2;oy=(mh-hh)/2
 def xy(lon,lat):return ox+(lon-lon0)*cos*scale,oy+(lat1-lat)*scale
 layer=Image.new('RGB',(mw,mh),'#edf0e8');ld=ImageDraw.Draw(layer)
 paths=[]
 def path(points,c,w):
  ld.line(points,fill=c,width=w,joint='curve');pts=' '.join(f'{left+x:.2f},{top+y:.2f}' for x,y in points);paths.append(f'<polyline points="{pts}" fill="none" stroke="{c}" stroke-width="{w}"/>')
 railcolors={'3호선':'#df7e24','서울 지하철 3호선':'#df7e24','일산선':'#df7e24','6호선':'#b68a35','경의본선':'#278d85','경의선':'#278d85','용산선':'#278d85','인천국제공항선':'#4999c5','서해선':'#89a834','수도권광역급행철도에이선':'#8e649a'}
 for e in es:
  g=e.get('geometry');t=e.get('tags',{})
  if not g:continue
  pts=[xy(v['lon'],v['lat']) for v in g]
  if not any(-100<x<mw+100 and -100<y<mh+100 for x,y in pts):continue
  if 'waterway'in t:path(pts,'#badbe6',6)
  elif 'highway'in t:
   n=t.get('name','');primary=t['highway'] in ['motorway','trunk','primary'];c='#c5bdab' if primary else '#d2cdc1';w=5 if primary else 3
   if n in ['덕양로','도래울로','권율대로','서오릉로']:c='#aa9a7b';w=6
   path(pts,c,w)
 for e in es:
  t=e.get('tags',{});g=e.get('geometry')
  if not g or t.get('railway') not in ['rail','subway'] or t.get('service') in ['yard','siding']:continue
  pts=[xy(v['lon'],v['lat']) for v in g]
  if any(-100<x<mw+100 and -100<y<mh+100 for x,y in pts):path(pts,railcolors.get(t.get('name',''),'#9ca8ae'),3)
 # Polygons are OSM geographic features, independent of official planning images.
 for e in apartments+[ikea]:
  g=e['geometry'];pts=[xy(v['lon'],v['lat']) for v in g]
  if any(0<x<mw and 0<y<mh for x,y in pts):
   col='#d2e4f3' if e!=ikea else '#ffe0a2';ld.polygon(pts,fill=col,outline=BLUE if e!=ikea else '#b37f27',width=3)
   paths.append(f'<polygon points="'+ ' '.join(f'{left+x:.2f},{top+y:.2f}' for x,y in pts)+f'" fill="{col}" stroke="{BLUE if e!=ikea else "#b37f27"}" stroke-width="3"/>')
 im.paste(layer,(left,top));d=ImageDraw.Draw(im)
 svg+=['<defs><clipPath id="map"><rect x="80" y="220" width="1260" height="640"/></clipPath></defs><g clip-path="url(#map)">']+paths+['</g>']
 def marker(e,label,dx=12,dy=-28,col=BLUE,num=None):
  lon,lat=coord(e);xx,yy=xy(lon,lat);x=left+xx;y=top+yy
  if not (left<x<left+mw and top<y<top+mh):return
  d.ellipse((x-8,y-8,x+8,y+8),fill='white',outline=col,width=4);svg.append(f'<circle cx="{x}" cy="{y}" r="8" fill="white" stroke="{col}" stroke-width="4"/>')
  label=(str(num)+' ' if num else '')+label;f=font(25,True);box=d.textbbox((x+dx,y+dy),label,font=f);d.rectangle((box[0]-4,box[1]-3,box[2]+4,box[3]+4),fill='white');txt(label,x+dx,y+dy,25,col,True)
 if not local:
  offsets={'대곡':(15,-35),'행신':(15,5),'원흥':(-92,-40),'삼송':(15,-40),'지축':(15,5),'새절':(15,-35),'디지털미디어시티':(15,5)}
  for n,e in stations.items():marker(e,'DMC역' if n=='디지털미디어시티' else n+'역',*offsets.get(n,(10,-30)))
  marker(ikea,'이케아·롯데아울렛 고양',-80,20,'#986a17')
 else:
  marker(stations['원흥'],'원흥역',10,-40)
  marker(stations['삼송'],'삼송역',10,-36)
  marker(ikea,'이케아·롯데아울렛',-80,25,'#986a17')
  for i,e in enumerate(apartments,1):
   n=e['tags']['name'];short='삼송2차아이파크' if '삼송2차' in n else '원흥역센트럴' if '원흥역' in n else '도래울센트럴더포레' if '더포레' in n else '지축센트럴' if '지축역센트럴' in n else '지축중흥'
   marker(e,short,-205 if '지축' in n else 10,32 if '지축역센트럴' in n else 8 if '원흥역' in n else -30,num=i)
 # Road labels at longest returned segment; same coordinate system as line.
 for n in ['덕양로','도래울로','권율대로','서오릉로']:
  ways=[e for e in es if e.get('tags',{}).get('name')==n and e.get('geometry')]
  if not ways:continue
  w=max(ways,key=lambda e:len(e['geometry']));g=w['geometry'];v=g[len(g)//2];xx,yy=xy(v['lon'],v['lat']);x=left+xx;y=top+yy
  if left+10<x<left+mw-150 and top+10<y<top+mh-35:txt(n,x,y,22,'#7e7059',True)
 txt('N ↑',1265,230,25,GRAY,True)
 # 1km geographic scale at central latitude.
 px=scale/111.32;d.line((115,815,115+px,815),fill=INK,width=5);txt('1 km',115,777,21,GRAY)
 svg.append(f'<line x1="115" y1="815" x2="{115+px}" y2="815" stroke="{INK}" stroke-width="5"/>')
 txt('이 지도에서 읽을 것',1390,235,29,INK,True)
 if not local:
  rows=[('주황','3호선·일산선','#df7e24'),('청록','경의선·용산선','#278d85'),('하늘','공항철도','#4999c5'),('황토','6호선','#b68a35'),('연두','서해선','#89a834'),('보라','GTX-A 기존 선형','#8e649a')]
  for i,(_,t,c) in enumerate(rows):txt('━ '+t,1390,300+i*57,25,c,True)
  txt('선형: OSM 이름 태그 기준',1390,675,23,GRAY);txt('거점: 연구 확인 운영역',1390,716,23,GRAY)
  txt('미래 창릉역 핀 없음',1390,770,26,'#986a17',True)
 else:
  txt('실제 시설 건물·단지 범위',1390,305,25,BLUE,True)
  txt('파랑: OSM 아파트 용지',1390,365,23,GRAY)
  txt('노랑: 이케아 건물',1390,405,23,GRAY)
  txt('롯데아울렛은 같은 건물',1390,450,25,'#986a17',True)
  txt('권율대로 420 · 공식 확인',1390,490,23,GRAY)
  txt('도형은 OSM 기여 자료',1390,570,24,GRAY)
  txt('공식 사업경계·출입구 아님',1390,610,23,GRAY)
  txt('보행시간·횡단 경로',1390,700,23,GRAY)
  txt('검증 전이므로 미표시',1390,735,23,GRAY)
  txt('생활권 비교용 지리판',1390,775,26,BLUE,True)
 txt('© OpenStreetMap contributors · ODbL · https://www.openstreetmap.org/copyright',80,875,22,GRAY)
 d.rectangle((96,922,1824,1052),fill='white');txt('기존 역과 생활시설의 실제 위치입니다. 단지에서의 접근 시간은 별도로 확인해야 합니다.',125,957,30)
 txt('2026.10.16 공개 OSM 자료 / 유료 지도·AI 이미지 사용 없음',80,1055,17,GRAY)
 # Caption rectangle in SVG precedes caption text only in export: add separate original map SVG without overlays for edit.
 svg.append('</svg>');(p/(name+'.svg')).write_text('\n'.join(svg),encoding='utf-8');im.save(out/(name+'.png'))
 pages.append(dict(name=name,bbox=bbox,dimensions=[1920,1080],map_rect=[80,220,1260,640],projection='local equirectangular with cosine correction at bounding-box mid-latitude; north up',no_future_station_pin=True))
make('GEO01_commute','기존 운영역의 위치부터 봅니다',(126.79,37.57,126.95,37.663))
make('GEO02_life','원흥·도래울의 실제 도로와 생활시설',(126.842,37.620,126.926,37.657),True)
(p/'map_specs.json').write_text(json.dumps(pages,ensure_ascii=False,indent=2),encoding='utf-8')
print('Saved map PNG/SVG 2 each. stations',len(stations),'apartment polygons',len(apartments))
