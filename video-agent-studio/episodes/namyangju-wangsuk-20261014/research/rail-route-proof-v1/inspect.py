import json,pathlib,sys,math
sys.stdout.reconfigure(encoding='utf-8');p=pathlib.Path(__file__).parent
d=json.loads(p.joinpath('raw_osm.json').read_text(encoding='utf-8'))['elements']
for e in d:
 if e.get('id')==468641433:print(e)
R=6378137
def ll(x,y):return [float(x)/R*180/math.pi,(2*math.atan(math.exp(float(y)/R))-math.pi/2)*180/math.pi]
st=json.loads(p.joinpath('searchRouteJson.json').read_text(encoding='utf-8'))['result']['gg']['up']['list']
for e in st: print(e['stationNm'],ll(e['lon'],e['lat']))
