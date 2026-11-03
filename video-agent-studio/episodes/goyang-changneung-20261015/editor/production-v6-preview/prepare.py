from pathlib import Path
import json,re,hashlib,math
E=Path(__file__).resolve().parent; EP=E.parent.parent; R=EP.parents[2]
S=R/'video/src/changneung-v6';O=EP/'outputs/production-v6-preview'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
old=read(R/'video/src/changneung-v5/data.json')
receipts=read(EP/'research/commute-v6/browser_receipts.json')
# Decode the selected Google place's full Plus Code, rather than reuse nearby station pins.
alphabet='23456789CFGHJMPQRVWX'
def decode(code):
 c=code.replace('+','');lat=-90.;lon=-180.;res=20.
 for i in range(0,10,2):
  lat+=alphabet.index(c[i])*res;lon+=alphabet.index(c[i+1])*res
  if i<8:res/=20
 latres=lonres=res
 for x in c[10:]:
  latres/=5;lonres/=4;j=alphabet.index(x);lat+=(j//4)*latres;lon+=(j%4)*lonres
 return [lon+lonres/2,lat+latres/2]
places=[('광화문역','8Q98HX9G+VFF',[1090,390]),('상암 MBC','8Q98HVJR+F86',[700,430]),('여의도역','8Q98GWCF+JPF',[820,650]),('LG사이언스파크','8Q98HR7J+CV6',[440,550]),('강남역','8Q99F2XH+52Q',[1100,760])]
points=[];bb=old['work']['bbox'];w=old['work']['viewport'];scale=old['work']['projection']['scale'];cos=math.cos(old['work']['projection']['mid_lat']*math.pi/180)
def project(p):return [w['x']+w['width']/2+(p[0]-(bb[0]+bb[2])/2)*cos*scale,w['y']+w['height']/2-(p[1]-(bb[1]+bb[3])/2)*scale]
for name,code,label in places:
 assert any(code.replace('+','%252B') in r['accessibility'] for r in receipts),code
 p=decode(code);points.append({'name':name,'plus_code':code,'lonlat':p,'xy':project(p),'label':label,'basis':'selected destination Plus Code in browser_receipts accessibility URL'})
blocks=[{'name':n,'lonlat':[lon,lat],'xy':project([lon,lat])} for n,lat,lon in [('S1',37.629244295,126.847159595),('S4',37.625952195,126.863235045),('S5',37.623044795,126.868664165)]]
data={'destinations':points,'blocks':blocks,'boundary':old['boundary'],'commute':[[66,68,67],[46,62,56],[63,78,72],[72,80,68],[87,94,94]],'prices':old['prices'],'alternatives':old['alternatives']}
(S/'data.json').write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8')
(O/'destination_pin_receipt.json').write_text(json.dumps({'source':'research/commute-v6/browser_receipts.json','source_sha256':hashlib.sha256((EP/'research/commute-v6/browser_receipts.json').read_bytes()).hexdigest(),'points':points,'blocks':blocks,'pin_type':'selected-place representative point; not entrance'},ensure_ascii=False,indent=2),encoding='utf-8')
print('Prepared five exact selected-destination anchors and 15 verified commute values')
