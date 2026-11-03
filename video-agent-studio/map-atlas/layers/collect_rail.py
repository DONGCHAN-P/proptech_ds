from pathlib import Path
import urllib.request,urllib.parse,json,hashlib
H=Path(__file__).resolve().parent;p=H/'raw/rail_routes_osm.json'
query='''[out:json][timeout:60];(relation["type"="route"]["route"~"^(subway|light_rail)$"](36.85,126.1,38.35,127.9);relation["type"="route"]["route"="train"]["name"~"경춘|경의|수인|분당|경강|서해|공항|신분당|GTX"](36.85,126.1,38.35,127.9););out tags geom;'''
endpoint='https://maps.mail.ru/osm/tools/overpass/api/interpreter'
if not p.exists():
 req=urllib.request.Request(endpoint,data=urllib.parse.urlencode({'data':query}).encode(),headers={'User-Agent':'CapitalApartmentAtlas/1.0 local research','Content-Type':'application/x-www-form-urlencoded'})
 with urllib.request.urlopen(req,timeout=80) as response:raw=response.read(35000000)
 j=json.loads(raw);assert j.get('elements') and not j.get('remark');p.write_bytes(raw)
j=json.loads(p.read_bytes());meta={'endpoint':endpoint,'query':query,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'osm_timestamp':j.get('osm3s',{}).get('timestamp_osm_base'),'relations':len(j['elements']),'license':'ODbL 1.0; © OpenStreetMap contributors'}
(H/'rail_sources.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in meta.items() if k!='query'},ensure_ascii=False))
