from pathlib import Path
import datetime, json, urllib.request, urllib.parse

root = Path(__file__).resolve().parent
query = '''[out:json][timeout:90];(
way[waterway=river](37.46,126.78,37.77,127.25);
way[highway~"^(motorway|trunk)$"](37.46,126.78,37.77,127.25);
);out geom;'''
url = 'https://overpass-api.de/api/interpreter'
request = urllib.request.Request(url, data=urllib.parse.urlencode({'data':query}).encode(),
                                 headers={'User-Agent':'Realestate map research/1.0'})
with urllib.request.urlopen(request, timeout=120) as response:
    raw = response.read()
(root/'osm_raw.json').write_bytes(raw)
data = json.loads(raw)
paths = []
for way in data.get('elements', []):
    points = [[p['lon'],p['lat']] for p in way.get('geometry', [])]
    if len(points)<2:
        continue
    tags = way.get('tags', {})
    paths.append({'osm_way_id':way['id'], 'kind':'water' if tags.get('waterway') else 'road',
                  'name':tags.get('name',''), 'points':points})
assert len(paths)>100 and any(p['kind']=='water' for p in paths)
result = {'bounds':[126.78,37.46,127.25,37.77], 'paths':paths,
          'source':url, 'query':query,
          'retrieved_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'attribution':'© OpenStreetMap contributors', 'license':'ODbL 1.0',
          'scope':'Actual major road and river centerline context; not complete street, cadastral, or commute map'}
(root/'geometry.json').write_text(json.dumps(result, ensure_ascii=False), encoding='utf-8')
print(json.dumps({'paths':len(paths), 'water_paths':sum(p['kind']=='water' for p in paths),
                  'raw_bytes':len(raw), 'geometry_bytes':(root/'geometry.json').stat().st_size}))
