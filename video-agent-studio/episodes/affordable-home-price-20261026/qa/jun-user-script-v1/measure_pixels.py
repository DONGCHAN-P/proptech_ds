"""열람한 실제 MP4 프레임의 헤더·금액 막대 픽셀 근거."""
from pathlib import Path
from PIL import Image
import json, hashlib
OWN=Path(__file__).resolve().parent
EP=OWN.parents[1]
ROOT=EP.parents[2]
e=json.loads((OWN/'preview_evidence.json').read_text('utf-8'))
result={'method':'실제 MP4 독립 추출 프레임의 픽셀 측정. 코드 좌표만으로 판정하지 않음.','headers':[],'bars':[]}
def dark_bounds(path,box):
    im=Image.open(path).convert('RGB'); pts=[]
    for y in range(box[1],box[3]):
        for x in range(box[0],box[2]):
            r,g,b=im.getpixel((x,y))
            if max(r,g,b)<180 and max(r,g,b)-min(r,g,b)>8:pts.append((x,y))
    return [min(x for x,y in pts),min(y for x,y in pts),max(x for x,y in pts),max(y for x,y in pts)] if pts else None
def runs_at(path,y,kind):
    im=Image.open(path).convert('RGB'); xs=[]
    for x in range(im.width):
        r,g,b=im.getpixel((x,y))
        ok=(b>120 and b>r*1.4 and b>g*1.1) if kind=='blue' else ((r>130 and r>g*1.05 and g>b*1.25) if kind=='gold' else (g>80 and g>r*1.3 and g>b*.95))
        if ok:xs.append(x)
    groups=[]
    for x in xs:
        if not groups or x>groups[-1][-1]+1:groups.append([x])
        else:groups[-1].append(x)
    return [{'x0':a[0],'x1':a[-1],'width':len(a)} for a in groups if len(a)>=8]
for p in e['previews']:
    f=p['frames'][-1] if p['id']!='S18_S19' else next(f for f in p['frames'] if f['time_s']==10.7)
    path=ROOT/f['path']
    result['headers'].append({'id':p['id'],'mp4_sha256':p['sha256'],'frame':f['path'],'left_brand_dark_bbox':dark_bounds(path,(60,0,850,100)),'right_status_dark_bbox':dark_bounds(path,(1350,0,1870,100))})
    if p['id']=='S13': specs=[(495,'blue'),(495,'gold'),(550,'blue'),(550,'gold')]
    elif p['id']=='S18_S19':specs=[(400,'blue'),(400,'gold'),(550,'blue'),(550,'gold'),(695,'blue'),(695,'gold')]
    else:specs=[(640,'gold'),(640,'green')]
    for y,kind in specs:result['bars'].append({'id':p['id'],'y':y,'color':kind,'runs':runs_at(path,y,kind)})
parent=EP/'director/jun-user-script-v1/preview_checks/S18_S19_10p7.png'
if parent.exists():result['parent_supplied_png']={'path':parent.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(parent.read_bytes()).hexdigest(),'left_brand_dark_bbox':dark_bounds(parent,(60,0,850,100)),'scope':'참고 PNG와 MP4의 실제 상단 상태를 별도로 기록'}
(OWN/'pixel_evidence.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))
