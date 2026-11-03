"""Static maps from genuine 2024 geometry; plot only verified apartment points.
Input is the director's normalized, audited price_panel_data.json. No network.
"""
from pathlib import Path
import gzip,hashlib,html,json,math
D=Path(__file__).resolve().parent;E=D.parents[1];R=E.parents[2]
O=E/'visual/top20-explain-v3/maps';O.mkdir(parents=True,exist_ok=True)
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def mercator(lon,lat):return 6378137*math.radians(lon),6378137*math.log(math.tan(math.pi/4+math.radians(lat)/2))
def polygons(g):
 if g['type']=='Polygon':return [g['coordinates']]
 if g['type']=='MultiPolygon':return g['coordinates']
 raise ValueError('Expected a real Polygon/MultiPolygon')
def inside_ring(point,ring):
 x,y=point;inside=False
 for a,b in zip(ring,ring[1:]+ring[:1]):
  if(a[1]>y)!=(b[1]>y)and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:inside=not inside
 return inside
def inside_geometry(point,features):
 return any(inside_ring(point,p[0])and not any(inside_ring(point,r)for r in p[1:])for f in features for p in polygons(f['geometry']))

def main():
 data=read(D/'price_panel_data.json');manifest=read(E/'visual/top20-8min-v2/maps/map_assets.json')
 maps={x['region_id']:x for x in manifest['assets']};rows=[]
 assert len(data['regions'])==20
 for price in data['regions']:
  rid=price['region_id'];m=maps[rid];source=E/m['geometry_file'];geo=json.loads(gzip.decompress(source.read_bytes()));features=geo['features']
  points=[mercator(*p[:2])for f in features for polygon in polygons(f['geometry'])for ring in polygon for p in ring]
  x0,y0=min(p[0]for p in points),min(p[1]for p in points);x1,y1=max(p[0]for p in points),max(p[1]for p in points)
  scale=min(740/(x1-x0),540/(y1-y0));ox=(800-(x1-x0)*scale)/2;oy=(600-(y1-y0)*scale)/2
  def project(lon,lat):
   x,y=mercator(lon,lat);return ox+(x-x0)*scale,600-oy-(y-y0)*scale
  shapes=[]
  for feature in features:
   parts=[]
   for polygon in polygons(feature['geometry']):
    for ring in polygon:
     coords=[project(*p[:2])for p in ring]
     parts.append('M'+' L'.join(f'{x:.3f},{y:.3f}'for x,y in coords)+' Z')
   shapes.append('<path d="'+' '.join(parts)+'" fill="#deebfa" fill-rule="evenodd" stroke="#93abc2" stroke-width="1.2" vector-effect="non-scaling-stroke"/>')
  rep=price.get('representative')or{};lat,lng=rep.get('lat'),rep.get('lng');marker=None;reason='coordinate_unverified_or_missing'
  if rep.get('coordinate_status')=='verified'and isinstance(lat,(int,float))and isinstance(lng,(int,float)):
   if inside_geometry((lng,lat),features):
    x,y=project(lng,lat);assert 0<x<800 and 0<y<600
    marker={'x':x,'y':y,'lat':lat,'lng':lng,'apt_id':rep['apt_id'],'apt_name':rep['apt_name'],'point_inside_real_region':True}
    shapes.extend([f'<circle cx="{x:.3f}" cy="{y:.3f}" r="17" fill="#286cda" opacity=".16"/>',f'<circle cx="{x:.3f}" cy="{y:.3f}" r="8" fill="#286cda" stroke="#ffffff" stroke-width="3"/>'])
    reason='verified_coordinate_inside_region'
   else:reason='coordinate_outside_historical_region_not_plotted'
  path=O/f'{rid}_price_map.svg';path.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" viewBox="0 0 800 600">'+''.join(shapes)+'</svg>',encoding='utf-8')
  rows.append({'region_id':rid,'file':str(path.relative_to(E)).replace('\\','/'),'sha256':sha(path),'canvas':[800,600],'projection':'EPSG:3857 equations with aspect-ratio preserved','source':str(source.relative_to(E)).replace('\\','/'),'source_sha256':sha(source),'boundary_version':m['boundary_version'],'feature_count':len(features),'marker':marker,'marker_status':reason,'attribution':m['attribution'],'price_panel':price})
 (O/'map_assets.json').write_text(json.dumps({'revision':'top20-explain-v3','source_price_panel_sha256':sha(D/'price_panel_data.json'),'assets':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'maps':len(rows),'verified_markers':sum(r['marker']is not None for r in rows),'camera_zoom':False,'invented_coordinates':0},ensure_ascii=False))
if __name__=='__main__':main()
