import urllib.request,urllib.parse,pathlib
q='''[out:json][timeout:40];(way[landuse](37.616,127.140,37.633,127.160);way[leisure](37.616,127.140,37.633,127.160);way[building](37.616,127.140,37.633,127.160);way[highway](37.616,127.140,37.633,127.160);way[waterway](37.616,127.140,37.633,127.160);nwr[name](37.616,127.140,37.633,127.160););out geom;'''
p=pathlib.Path(__file__).parent/'raw_osm.json'
req=urllib.request.Request('https://overpass.kumi.systems/api/interpreter?'+urllib.parse.urlencode({'data':q}),headers={'User-Agent':'Mozilla/5.0 research map'})
p.write_bytes(urllib.request.urlopen(req,timeout=75).read());print(p.stat().st_size)
