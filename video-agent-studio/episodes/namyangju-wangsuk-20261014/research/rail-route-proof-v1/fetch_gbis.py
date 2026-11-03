import urllib.request,pathlib
p=pathlib.Path(__file__).parent
u='https://www.gbis.go.kr/service/busInfo/townBus.action?centerId=4136000000&cmd=townBus'
p.joinpath('gbis.html').write_bytes(urllib.request.urlopen(u,timeout=40).read())
p.joinpath('gbis_js.js').write_bytes(urllib.request.urlopen('https://www.gbis.go.kr/gbis2014/js/businfo/mtrbsRoute.js',timeout=40).read())
p.joinpath('gbis_route.html').write_bytes(urllib.request.urlopen('https://www.gbis.go.kr/gbis2014/schBus.action?cmd=mainSearchText&gubun=busInfo&searchText=48&routeId=241347009',timeout=40).read())
p.joinpath('gbis_search.js').write_bytes(urllib.request.urlopen('https://www.gbis.go.kr/gbis2014/js/map/searchRoute.js?ver=1.60',timeout=40).read())
p.joinpath('gbis_total.js').write_bytes(urllib.request.urlopen('https://www.gbis.go.kr/gbis2014/js/map/searchTotal_2025.js?ver=1.17',timeout=40).read())
for cmd in ['searchMapLineJson','searchRouteJson']:
 p.joinpath(cmd+'.json').write_bytes(urllib.request.urlopen('https://www.gbis.go.kr/gbis2014/schBusAPI.action?cmd='+cmd+'&routeId=241347009',timeout=40).read())
