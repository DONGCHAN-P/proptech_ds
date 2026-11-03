import urllib.request,urllib.parse,pathlib
q='''[out:json][timeout:25];(way[leisure=park](37.637,127.114,37.653,127.133);nwr[shop=supermarket](37.637,127.114,37.653,127.133););out geom;'''
p=pathlib.Path(__file__).parent/'raw_byeollae_south_osm.json'
req=urllib.request.Request('https://overpass.kumi.systems/api/interpreter?'+urllib.parse.urlencode({'data':q}),headers={'User-Agent':'Mozilla/5.0 research map'})
p.write_bytes(urllib.request.urlopen(req,timeout=65).read());print(p.stat().st_size)
