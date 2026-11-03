"""Prepare capital-area school points and official school-zone polygons."""
from pathlib import Path
import csv,hashlib,io,json,math,sys,zipfile
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'tools/gis_vendor'))
import shapefile
import pyproj
from pyproj import CRS,Transformer

source=json.loads((HERE/'education_sources.json').read_text(encoding='utf8'))
files={f['layer']:f for f in source['files']};target=CRS.from_epsg(5179)
to_native=Transformer.from_crs(4326,target,always_xy=True)
to_wgs=Transformer.from_crs(target,4326,always_xy=True)
# Axis order and projection control point; never infer a CRS from the filename.
x,y=to_native.transform(127.5,38)
assert abs(x-1000000)<0.001 and abs(y-2000000)<0.001

def archive(name):return zipfile.ZipFile(HERE/files[name]['path'])
def csv_rows(name):
    with archive(name) as z:
        n=next(n for n in z.namelist() if n.lower().endswith('.csv'))
        return list(csv.DictReader(io.StringIO(z.read(n).decode('utf-8-sig'))))

schools=[];invalid=[];rows=csv_rows('schools');seen=set();roundtrip=0
for r in rows:
    if r['시도교육청명'] not in {'서울특별시교육청','경기도교육청','인천광역시교육청'}:continue
    try:
        lon,lat=float(r['경도']),float(r['위도'])
        assert math.isfinite(lon) and math.isfinite(lat) and 124<lon<130 and 36<lat<39
        x,y=to_native.transform(lon,lat,errcheck=True);lo,la=to_wgs.transform(x,y,errcheck=True)
        roundtrip=max(roundtrip,abs(lo-lon),abs(la-lat))
    except (ValueError,AssertionError):invalid.append(r['학교ID']);continue
    assert r['학교ID'] not in seen;seen.add(r['학교ID'])
    schools.append({'id':r['학교ID'],'name':r['학교명'],'grade':r['학교급구분'],
                    'address':r['소재지도로명주소'],'office':r['시도교육청명'],
                    'operation':r['운영상태'],'date':r['데이터기준일자'],
                    'xy':[round(x,2),round(y,2)]})
assert roundtrip<1e-8 and schools and not invalid,invalid

zones=[];zone_counts={};crs_checks={}
for kind in ['elementary_zones','middle_zones','high_zones']:
    with archive(kind) as z:
        members={Path(n).suffix.lower():n for n in z.namelist()}
        source_crs=CRS.from_wkt(z.read(members['.prj']).decode('utf8'))
        transformer=Transformer.from_crs(source_crs,target,always_xy=True)
        crs_checks[kind]={'source_epsg':source_crs.to_epsg(),'target_epsg':5179}
        reader=shapefile.Reader(shp=io.BytesIO(z.read(members['.shp'])),
                              dbf=io.BytesIO(z.read(members['.dbf'])),
                              encoding=z.read(members['.cpg']).decode().strip())
        count=0
        for sr in reader.iterShapeRecords():
            r=sr.record.as_dict()
            if r['SD_CD'] not in {'11','28','41'}:continue
            points=sr.shape.points
            xs,ys=transformer.transform([p[0] for p in points],[p[1] for p in points],errcheck=True)
            stops=list(sr.shape.parts)+[len(points)]
            rings=[[[round(xs[i]),round(ys[i])] for i in range(a,b)] for a,b in zip(stops,stops[1:])]
            assert all(math.isfinite(v) for pair in zip(xs,ys) for v in pair)
            zones.append({'id':r['HAKGUDO_ID'],'name':r['HAKGUDO_NM'],'kind':kind,
                          'date':r['BASE_DT'],'area_code':r['SD_CD'],
                          'bbox':[min(xs),min(ys),max(xs),max(ys)],'rings':rings})
            count+=1
        zone_counts[kind]=count

links=[{'zone_id':r['학구ID'],'school_id':r['학교ID'],'date':r['데이터기준일자']}
       for r in csv_rows('school_zone_links') if r['학교ID'] in seen]
# Export school positions as the user's requested SHP, with the same CRS as atlas.
shp_dir=HERE/'processed/schools_5179';shp_dir.mkdir(parents=True,exist_ok=True)
with shapefile.Writer(str(shp_dir/'schools'),shapeType=shapefile.POINT,encoding='utf8') as w:
    for name,size in [('SCHOOL_ID',20),('NAME',160),('GRADE',50),('ADDRESS',254),('BASE_DATE',10)]:w.field(name,'C',size=size)
    for r in schools:w.point(*r['xy']);w.record(r['id'],r['name'],r['grade'],r['address'],r['date'])
(shp_dir/'schools.prj').write_text(target.to_wkt('WKT1_ESRI'),encoding='utf8')
(shp_dir/'schools.cpg').write_text('UTF-8',encoding='ascii')
check=shapefile.Reader(str(shp_dir/'schools'),encoding='utf8')
assert len(check)==len(schools)
assert all(list(s.shape.points[0])==r['xy'] and s.record[0]==r['id'] for s,r in zip(check.iterShapeRecords(),schools))
meta={'source':'한국교육시설안전원 학구도안내서비스',
      'source_url':source['source_url'],'crs':'EPSG:5179',
      'school_dates':sorted({r['date'] for r in schools}),
      'zone_dates':sorted({r['date'] for r in zones}),
      'note':'학교 위치와 배정구역은 별도 자료. 인근 학교/경계 표시가 개별 세대 배정을 확정하지 않음.',
      'source_hashes':{k:v['sha256'] for k,v in files.items()}}
payload={'meta':meta,'schools':schools,'zones':zones,'links':links}
out=HERE/'processed/education.json';out.write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')),encoding='utf8')
validation={'school_count':len(schools),'schools_by_grade':{g:sum(r['grade']==g for r in schools) for g in sorted({r['grade'] for r in schools})},
            'zone_counts':zone_counts,'link_count':len(links),'crs_checks':crs_checks,
            'school_inverse_roundtrip_max_degrees':roundtrip,'invalid_school_coordinates':invalid,
            'school_shp_roundtrip':'pass','pyproj_version':pyproj.__version__,
            'pyshp_version':shapefile.__version__,'payload_sha256':hashlib.sha256(out.read_bytes()).hexdigest()}
(HERE/'education_validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(validation,ensure_ascii=False))
