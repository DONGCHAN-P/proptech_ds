from pathlib import Path
import urllib.request,urllib.parse,json,math,sys
from PIL import Image,ImageDraw,ImageFont
sys.stdout.reconfigure(encoding='utf-8')
root=Path(__file__).parent
q='[out:json][timeout:35];(way[highway~"^(trunk|primary|secondary)$"](37.55,127.03,37.85,127.4);way[waterway=river](37.55,127.03,37.85,127.4);way[railway=rail](37.55,127.03,37.85,127.4);node[place](37.55,127.03,37.85,127.4););out geom;'
url='https://overpass-api.de/api/interpreter?data='+urllib.parse.quote(q)
source=root/'regional_osm_v3.json'
if not source.exists():
    req=urllib.request.Request(url,headers={'User-Agent':'NamyangjuVideoResearch/1.0 (local editorial map; public geographic data)'})
    source.write_bytes(urllib.request.urlopen(req,timeout=50).read())
data=json.loads(source.read_text('utf-8'))
im=Image.new('RGB',(1920,1080),'#F6F4EF');d=ImageDraw.Draw(im)
fontfile='C:/Windows/Fonts/malgun.ttf'
f=ImageFont.truetype(fontfile,26);title=ImageFont.truetype(fontfile,48);small=ImageFont.truetype(fontfile,22)
def p(lon,lat):return (210+(lon-127.03)*math.cos(math.radians(37.7))*740/.30,140+(37.85-lat)*740/.30)
for e in data['elements']:
    if e['type']!='way':continue
    pts=[p(x['lon'],x['lat']) for x in e.get('geometry',[]) if x is not None]
    if len(pts)<2:continue
    tags=e.get('tags',{});color,width=('#9BCFDC',7) if 'waterway' in tags else ('#888888',2) if 'railway' in tags else ('#D2BD92',3)
    d.line(pts,fill=color,width=width)
place=[]
for e in data['elements']:
    if e['type']!='node':continue
    tags=e.get('tags',{});name=tags.get('name:ko',tags.get('name',''))
    if name in ['별내동','별내면','다산동','진접읍','오남읍','호평동','평내동','화도읍','진건읍','퇴계원읍','일패동','이패동']:
        x,y=p(e['lon'],e['lat']);dx,dy={'퇴계원읍':(-90,20),'다산동':(-70,20),'일패동':(12,-40),'이패동':(12,5),'호평동':(10,-40),'평내동':(20,-15),'별내동':(-120,-25),'진건읍':(15,-35)}.get(name,(12,-15));d.ellipse((x-6,y-6,x+6,y+6),fill='#2F6FED');d.text((x+dx,y+dy),name,font=f,fill='#111111',stroke_width=2,stroke_fill='#F6F4EF');place.append({'name':name,'lat':e['lat'],'lon':e['lon'],'osm_type':'node','osm_id':e['id'],'tags':tags})
d.rectangle((0,0,1920,135),fill='#F6F4EF');d.rectangle((0,0,190,1080),fill='#F6F4EF');d.rectangle((960,135,1920,900),fill='#F6F4EF')
d.text((90,50),'남양주의 기존 지역을 먼저 보기',font=title,fill='#111111')
for i,s in enumerate(['실제 OSM 지리 데이터','파란 점: 지역명 위치','생활권·도보권 경계 없음','왕숙1: 진접·진건·퇴계원','왕숙2: 일패·이패동 일대','왕숙 경계: 공식 계획도 참고']):d.text((1120,180+i*55),s,font=small,fill='#111111')
d.rectangle((85,900,1835,998),fill='white')
d.text((110,915),'© OpenStreetMap contributors | ODbL | https://www.openstreetmap.org/copyright',font=small,fill='#555555')
d.text((110,950),'지역명 위치·기존 지형 설명용 / 철도 운영·계획 상태나 신도시 법정 경계의 확정 근거 아님',font=small,fill='#555555')
file=root/'outputs/S002_namyangju_regional_osm_v3.png';im.save(file)
meta={'revision':'visual-v3','actual_file':'visual/outputs/S002_namyangju_regional_osm_v3.png','dimensions':[1920,1080],'source_url':url,'retrieved_at':'2026-10-14','osm_timestamp':data.get('osm3s',{}).get('timestamp_osm_base'),'bounds':[127.03,37.55,127.4,37.85],'place_points':place,'element_count':len(data['elements']),'use':'지역명·도로·하천 설명. 철도 운영상태·왕숙 경계·통근시간 결론 금지.','AI':False,'license':'OSM ODbL, visible attribution plus copyright URL'}
(root/'regional_meta_v3.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps({'saved':str(file),'elements':len(data['elements']),'places':[x['name'] for x in place]},ensure_ascii=False))
