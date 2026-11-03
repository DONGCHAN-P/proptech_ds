from pathlib import Path
import json,math,re,hashlib,xml.etree.ElementTree as ET
Q=Path(__file__).resolve().parent;EP=Q.parents[1];R=EP/'research/map-location-v4';O=EP/'outputs/production-v4/plan_geometry'
read=lambda p:json.loads(p.read_text('utf-8-sig'))
lands=read(R/'raw/landfeatures.geojson');boundary=read(R/'raw/boundaryfeatures.geojson');ext=read(R/'block_extents.json');receipt=read(O/'geometry_receipt.json')
def rings(g):return g['coordinates'] if g['type']=='Polygon' else [r for poly in g['coordinates'] for r in poly]
def bounds(features):
 pts=[p for f in features for ring in rings(f['geometry']) for p in ring]
 return [min(p[0] for p in pts),min(p[1] for p in pts),max(p[0] for p in pts),max(p[1] for p in pts)]
def project(p,b,w,h):
 co=math.cos((b[1]+b[3])/2*math.pi/180);scale=min((w-36)/((b[2]-b[0])*co),(h-36)/(b[3]-b[1]));return [w/2+(p[0]-(b[0]+b[2])/2)*co*scale,h/2-(p[1]-(b[1]+b[3])/2)*scale]
def color(n):
 if re.search('공원|녹지',n):return '#cddfc8'
 if '교육' in n:return '#9dccd0'
 if re.search('도로|주차',n):return '#e4e1d9'
 if re.search('하천|수도',n):return '#a7d3e5'
 if re.search('업무|상업',n):return '#d8bed6'
 if '공동주택' in n:return '#eadbb6'
 return '#eee9df'
def paths(root):return list(root.iter('{http://www.w3.org/2000/svg}path'))
def test_shapes(file,features,bbox,w,h,focus=''):
 root=ET.parse(file).getroot();pp=paths(root);bad=[];maxerr=0
 for i,f in enumerate(features):
  nums=list(map(float,re.findall(r'-?\d+(?:\.\d+)?',pp[i].attrib['d'])));expected=[v for ring in rings(f['geometry']) for xy in ring for v in project(xy,bbox,w,h)]
  err=max([abs(a-b) for a,b in zip(nums,expected)] or [0]);maxerr=max(err,maxerr)
  wanted='#eab54d' if f['properties']['bl_type']==f'공동주택 ({focus})' else color(f['properties']['bl_type'])
  if len(nums)!=len(expected) or err>.0051 or pp[i].attrib['fill']!=wanted:bad.append(f['id'])
 return {'file':file.name,'features_checked':len(features),'max_projection_rounding_error_px':maxerr,'bad_feature_ids':bad,'sha256':hashlib.sha256(file.read_bytes()).hexdigest()}
overall=bounds(boundary['features']);results=[test_shapes(O/'overall.svg',lands['features'],overall,1100,650)];locators=[];targets=[]
for block in ['S-1','S-4','S-5']:
 key=f'공동주택 ({block})';e=ext[key];features=read(R/(block+'_context.geojson'))['features'];b=e['detail_extent'];results.append(test_shapes(O/(block+'_detail.svg'),features,b,1100,560,block));results.append(test_shapes(O/(block+'_locator.svg'),lands['features'],overall,320,560))
 target=next(f for f in lands['features'] if f['properties']['bl_type']==key);tb=bounds([target]);targets.append({'block':block,'target_id_matches':target['id']==e['id'],'actual_bbox':tb,'declared_bbox_matches':tb==e['bbox'],'present_in_detail':any(f['id']==target['id'] for f in features)})
 rt=ET.parse(O/(block+'_locator.svg')).getroot();rects=[x for x in rt.iter('{http://www.w3.org/2000/svg}rect') if x.attrib.get('fill')=='none'];a=project([b[0],b[3]],overall,320,560);z=project([b[2],b[1]],overall,320,560);actual=[float(rects[-1].attrib[k]) for k in ['x','y','width','height']];expected=[a[0],a[1],z[0]-a[0],z[1]-a[1]];locators.append({'block':block,'same_extent_as_detail':max(abs(x-y) for x,y in zip(actual,expected))<1e-8,'actual_rect':actual,'detail_extent':b})
report={'revision':'geometry-v4-independent-audit','coordinate_basis':'원천 EPSG4326 경도·위도. 북상향/종횡비 보정 선형 투영 수치 대조. 실제 출력 가독성 검수는 별도.','overall_bbox_matches_boundary':overall==receipt['overall_bbox'],'svg_checks':results,'target_checks':targets,'locator_checks':locators,'limits':['공개 WFS와 SVG 사이 도형·좌표·색분류·현재영역 연결을 검사했다. 733개 도형의 현장/지적 정확성이나 최신 고시 일치를 전수 검증한 것은 아니다.','업무와 상업은 같은 색 계열이므로 직접 라벨이 필요하다. 예정역 권역은 시설 확정 경계나 출입구가 아니다.']}
(Q/'geometry_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8');print(json.dumps(report,ensure_ascii=False,indent=2))
