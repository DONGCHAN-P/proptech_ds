from pathlib import Path
import urllib.request,urllib.parse,json,sys,hashlib,datetime
E=Path(__file__).resolve().parent;R=E.parents[4];sys.path.insert(0,str(R/'tools/gis_vendor'));from pyproj import Transformer
raw=E/'osm_roads_raw.json';query='[out:json][timeout:30];way[highway~"^(motorway|trunk|primary|secondary|tertiary|residential|unclassified|living_street)$"](37.49,127.17,37.56,127.24);out geom;'
if not raw.exists():
 req=urllib.request.Request('https://overpass-api.de/api/interpreter',data=urllib.parse.urlencode({'data':query}).encode(),headers={'User-Agent':'Realestate-video-source-review/1.0'})
 with urllib.request.urlopen(req,timeout=60) as response:raw.write_bytes(response.read())
data=json.loads(raw.read_text(encoding='utf8'));tr=Transformer.from_crs('EPSG:4326','EPSG:5179',always_xy=True);b=json.loads((E/'source/regional.json').read_text(encoding='utf8'))['meta']['bounds'];rows=[]
for way in data['elements']:
 pts=[]
 for point in way.get('geometry',[]):
  x,y=tr.transform(point['lon'],point['lat']);pts.append([(x-b[0])/(b[2]-b[0])*1000,(b[3]-y)/(b[3]-b[1])*1000])
 if pts:rows.append(dict(id=way['id'],name=way.get('tags',{}).get('name',''),kind=way.get('tags',{}).get('highway',''),d='M'+' L'.join(f'{x:.3f},{y:.3f}' for x,y in pts)))
out=dict(roads=rows,meta=dict(source='OpenStreetMap contributors via Overpass API',license='ODbL',license_url='https://www.openstreetmap.org/copyright',query=query,raw_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),retrieved_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),note='Actual mapped road geometry only; no calculated pedestrian route, crossings or travel time'))
(E/'source/roads.json').write_text(json.dumps(out,ensure_ascii=False),encoding='utf8');print(json.dumps(dict(road_count=len(rows),raw_bytes=raw.stat().st_size)))
