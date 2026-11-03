import urllib.request,urllib.parse,pathlib,json
p=pathlib.Path(__file__).resolve().parent
query='''[out:json][timeout:60];(
way[highway~"^(motorway|trunk|primary|secondary)$"](37.54,126.77,37.69,126.98);
way[railway~"^(rail|subway)$"][service!~"yard|siding"](37.54,126.77,37.69,126.98);
way[waterway~"river|stream"](37.54,126.77,37.69,126.98);
way[name~"덕양로|도래울로|권율대로|서오릉로|수색교"](37.54,126.77,37.69,126.98);
nwr[railway=station][name~"원흥|새절|디지털미디어시티|행신|대곡|삼송|지축"](37.54,126.77,37.69,126.98);
nwr[name~"이케아|IKEA|롯데아울렛|삼송2차아이파크|센트럴더포레|창릉호반|원흥역센트럴|지축역센트럴|중흥S|북한산파크뷰"](37.59,126.82,37.69,126.96);
);out center geom;'''
(p/'raw/query.overpass').write_text(query,encoding='utf-8')
req=urllib.request.Request('https://overpass-api.de/api/interpreter',data=urllib.parse.urlencode({'data':query}).encode(),headers={'User-Agent':'RealestateReco-ChangneungReference/1.0 (single-study public vector request)'})
with urllib.request.urlopen(req,timeout=90) as r:
 data=r.read();(p/'raw/osm.json').write_bytes(data)
 print('OSM features:',len(json.loads(data)['elements']),'bytes:',len(data))
