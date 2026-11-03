import urllib.request,urllib.parse,pathlib
q='''[out:json][timeout:25];(node[entrance](37.660,127.122,37.664,127.128);node[railway=subway_entrance](37.640,127.124,37.644,127.130););out geom;'''
p=pathlib.Path(__file__).parent/'raw_local_osm.json'
req=urllib.request.Request('https://overpass.kumi.systems/api/interpreter?'+urllib.parse.urlencode({'data':q}),headers={'User-Agent':'Mozilla/5.0 research map'})
p.write_bytes(urllib.request.urlopen(req,timeout=100).read());print(p.stat().st_size)
