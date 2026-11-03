import json,pathlib,urllib.request,urllib.parse
p=pathlib.Path(__file__).resolve().parent
q='''[out:json][timeout:60];(node[railway=station][name~"^(시청|광화문|종로3가|경복궁|여의도|마곡나루|강남|교대|디지털미디어시티|원흥|새절|공덕)$"](37.45,126.78,37.68,127.10);way[waterway=river][name~"한강|창릉천"](37.45,126.78,37.68,127.10););out geom;'''
(p/'raw/query.overpass').write_text(q,encoding='utf-8')
req=urllib.request.Request('https://overpass-api.de/api/interpreter',data=urllib.parse.urlencode({'data':q}).encode(),headers={'User-Agent':'RealestateVideoMap/1.0'})
with urllib.request.urlopen(req,timeout=90) as r: data=r.read()
(p/'raw/osm-wide.json').write_bytes(data)
es=json.loads(data)['elements']
print('elements',len(es))
print([(e['id'],e.get('tags',{}).get('name'),e.get('lon'),e.get('lat')) for e in es if e['type']=='node'])
