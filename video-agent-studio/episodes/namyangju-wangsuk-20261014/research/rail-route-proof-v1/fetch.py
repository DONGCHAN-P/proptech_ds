import urllib.request, urllib.parse, pathlib
q='''[out:json][timeout:90];(nwr[railway](37.60,127.065,37.74,127.22);relation[route=bus][ref=48](37.64,127.10,37.70,127.14);way[highway](37.64,127.10,37.67,127.14);nwr[name~"별내|미라벨|아이파크"](37.64,127.10,37.67,127.14););out geom;'''
p=pathlib.Path(__file__).parent/'raw_osm.json'
req=urllib.request.Request('https://overpass.kumi.systems/api/interpreter?'+urllib.parse.urlencode({'data':q}),headers={'User-Agent':'Mozilla/5.0 research map'})
p.write_bytes(urllib.request.urlopen(req,timeout=120).read())
print(p.stat().st_size)
