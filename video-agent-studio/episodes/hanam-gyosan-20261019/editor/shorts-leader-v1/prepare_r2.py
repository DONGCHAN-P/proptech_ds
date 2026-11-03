from pathlib import Path
import json
E=Path(__file__).resolve().parent
d=json.loads((E/'data.json').read_text(encoding='utf8'))
for id in ['C2','B2']:
 q=d['details'][id]['block_point'];d['details'][id]['view']=[q[0]-200,q[1]-94,400,400*485/1080]
(E/'data_r2.json').write_text(json.dumps(d,ensure_ascii=False),encoding='utf8')
s=(E/'entry.tsx').read_text(encoding='utf8').replace("'./data.json'","'./data_r2.json'").replace("'.png')} style={{position:'absolute',top:435,width:1080,height:770}}", "(overall?'.png':'-r2.png'))} style={{position:'absolute',top:435,width:1080,height:overall?770:485}}")
s=s.replace('height={770} viewBox={view.join', 'height={overall?770:485} viewBox={view.join').replace('left:620,top:650','left:40,top:660').replace('GyosanLeaderShortV1','GyosanLeaderShortV1R2')
(E/'entry_r2.tsx').write_text(s,encoding='utf8')
m=(E/'measure.cjs').read_text(encoding='utf8').replace("'entry.tsx'","'entry_r2.tsx'").replace("n==='./data.json'","n==='./data_r2.json'").replace("'data.json'","'data_r2.json'").replace("'layout_bounds.json'","'layout_bounds_r2.json'").replace('`layout-${frame}.png`','`layout-r2-${frame}.png`')
(E/'measure_r2.cjs').write_text(m,encoding='utf8')
r=(E/'raster.cjs').read_text(encoding='utf8').replace("require('./data.json')","require('./data_r2.json')").replace("{C2:D.details.C2.view,B2:D.details.B2.view,all:[120,350,550,450],locator:[0,0,1000,1000]}","{C2:D.details.C2.view,B2:D.details.B2.view}").replace('height:770','height:485').replace('height="770"','height="485"').replace("'map-'+id+'.png'","'map-'+id+'-r2.png'")
(E/'raster_r2.cjs').write_text(r,encoding='utf8')
