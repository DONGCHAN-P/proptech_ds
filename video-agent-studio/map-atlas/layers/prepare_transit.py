"""Official KRIC station workbook -> capital-area station points, never inferred tracks."""
from pathlib import Path
import sys,json,zipfile,xml.etree.ElementTree as E,hashlib,datetime
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[2]/'tools/gis_vendor'))
import pyproj,shapefile
p=HERE/'raw/stations_20260630.xlsx'
ns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
with zipfile.ZipFile(p) as z:
    strings=[''.join(si.itertext()) for si in E.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si',ns)]
    rows=[]
    for row in E.fromstring(z.read('xl/worksheets/sheet1.xml')).findall('.//m:row',ns):
        values={}
        for c in row:
            col=''.join(ch for ch in c.get('r') if ch.isalpha())
            v=c.findtext('m:v','',ns)
            values[col]=strings[int(v)] if c.get('t')=='s' else v
        rows.append(values)
headers=rows[0]
tr=pyproj.Transformer.from_crs(4326,5179,always_xy=True)
stations=[];invalid=[]
for i,row in enumerate(rows[1:],2):
    r={label:row.get(col,'') for col,label in headers.items()}
    addr=r['역사도로명주소'].strip()
    if not addr.startswith(('서울특별시','경기도','인천광역시')):continue
    try:
        lon,lat=float(r['역경도']),float(r['역위도'])
        assert 124<lon<130 and 36<lat<39
        x,y=tr.transform(lon,lat,errcheck=True)
    except (ValueError,AssertionError):invalid.append(i);continue
    date=r['데이터기준일자']
    if date.replace('.','',1).isdigit():date=(datetime.datetime(1899,12,30)+datetime.timedelta(days=float(date))).date().isoformat()
    if not date or date.startswith('1900'):date='기준일 미기재'
    stations.append({'id':f"{r['노선번호']}:{r['역번호']}:{i}",'name':r['역사명'],'line':r['노선명'],'line_id':r['노선번호'],'address':addr,'operator':r['운영기관명'],'date':date,'xy':[round(x,2),round(y,2)]})
assert stations and not invalid
out=HERE/'processed/stations_5179';out.mkdir(parents=True,exist_ok=True)
with shapefile.Writer(str(out/'stations'),shapeType=shapefile.POINT,encoding='utf8') as w:
    for key,size in [('ID',80),('NAME',150),('LINE',180),('ADDRESS',254),('BASE_DATE',30)]:w.field(key,'C',size=size)
    for s in stations:w.point(*s['xy']);w.record(s['id'],s['name'],s['line'],s['address'],s['date'])
(out/'stations.prj').write_text(pyproj.CRS(5179).to_wkt('WKT1_ESRI'),encoding='utf8')
(out/'stations.cpg').write_text('UTF-8',encoding='ascii')
check=shapefile.Reader(str(out/'stations'),encoding='utf8')
assert len(check)==len(stations)
assert all(list(a.shape.points[0])==b['xy'] for a,b in zip(check.iterShapeRecords(),stations))
meta={'source':'철도산업정보센터 · 전체 도시철도역사정보 20260630','source_url':'https://data.kric.go.kr/rips/M_01_01/detail.do?id=32','download_url':'https://data.kric.go.kr/rips/dataset/download.file?type=filedata&id=32&operation=1','source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'crs':'EPSG:5179','note':'원자료 주소가 서울·경기·인천인 역별 노선 레코드. 환승역은 노선별 중복. 역 중심 좌표이며 출입구 좌표 아님. 실제 선로·계획역 자료 미포함.','dates':sorted({s['date'] for s in stations})}
(HERE/'processed/transit.json').write_text(json.dumps({'meta':meta,'stations':stations},ensure_ascii=False,separators=(',',':')),encoding='utf8')
result={'station_line_records':len(stations),'lines':sorted({s['line'] for s in stations}),'dates':meta['dates'],'invalid':invalid,'shp_roundtrip':'pass','meta':meta}
(HERE/'transit_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(result,ensure_ascii=False))
