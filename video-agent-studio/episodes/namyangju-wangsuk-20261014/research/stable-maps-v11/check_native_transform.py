import pathlib,sys,json,collections,math
p=pathlib.Path(__file__).parent;src=p.parent/'map-led-v5';sys.path.insert(0,str(src/'_pdfdeps'));import fitz
def entries(name,bounds):
 d=fitz.open(src/name);out=collections.defaultdict(list)
 for z in d[4].get_drawings():
  r=z['rect'];w,h=r.width,r.height
  if not z['fill']or w<3 or h<3 or not(bounds[0]<r.x0<r.x1<bounds[2] and bounds[1]<r.y0<r.y1<bounds[3]):continue
  items=z['items']
  if len(items)<4 or len(items)>30:continue
  sig=[]
  for item in items:
   sig.append(item[0])
   for a in item[1:]:
    if hasattr(a,'x')and hasattr(a,'y'):sig.extend([round((a.x-r.x0)/w,3),round((a.y-r.y0)/h,3)])
    elif hasattr(a,'x0'):sig.extend([round((a.x0-r.x0)/w,3),round((a.y0-r.y0)/h,3),round((a.x1-r.x0)/w,3),round((a.y1-r.y0)/h,3)])
  key=str([tuple(round(c,2)for c in z['fill']),sig]);out[key].append([r.x0+w/2,r.y0+h/2,w,h])
 return out
a=entries('w1_a1_pamphlet.pdf',[790,119,1145,829]);b=entries('w1_b17_pamphlet.pdf',[900,164,1237,830]);pairs=[]
for k,v in a.items():
 if len(v)==1 and len(b.get(k,[]))==1:
  x,y=v[0],b[k][0]
  if .90<y[2]/x[2]<.98 and .90<y[3]/x[3]<.98:pairs.append([x[:2],y[:2]])
def fit(axis):
 xs=[z[0][axis]for z in pairs];ys=[z[1][axis]for z in pairs];mx=sum(xs)/len(xs);my=sum(ys)/len(ys);s=sum((x-mx)*(y-my)for x,y in zip(xs,ys))/sum((x-mx)**2 for x in xs);return s,my-s*mx
sx,tx=fit(0);sy,ty=fit(1)
res=[math.hypot(y[0]-(sx*x[0]+tx),y[1]-(sy*x[1]+ty))for x,y in pairs]
source_station=[1044.5,635];a1=[(source_station[0]-tx)/sx,(source_station[1]-ty)/sy];native=[(a1[0]-830)*1654/330,(a1[1]-500)*1504/300]
out=dict(matching_unique_factual_vector_paths=len(pairs),pairs=pairs,transform_a1_to_b17={'sx':sx,'tx':tx,'sy':sy,'ty':ty},residual_rms_pdf_pt=math.sqrt(sum(r*r for r in res)/len(res)),residual_max_pdf_pt=max(res),b17_station_symbol_pdf=source_station,a1_equivalent_station_pdf=a1,south_board_station_pixel=native,old_south_anchor=[620,595],method='same-published-landuse geometry paths matched across two official PDFs; geometric layout transform only, not WGS84 georegistration',limitations='manual station circle center estimate approx1 PDFpt; published plan symbol not surveyed station exit')
(p/'native_transform_check.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in out.items()if k!='pairs'}))
