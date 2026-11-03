"""Download public education GIS files through their published download links.
No login, approval submission, API key, or publishing is performed.
"""
from pathlib import Path
import hashlib,json,urllib.request,zipfile,datetime

HERE=Path(__file__).resolve().parent
RAW=HERE/'raw/education-20260920'; RAW.mkdir(parents=True,exist_ok=True)
FILES=[('schools',2967,2997),('elementary_zones',2966,2996),
       ('middle_zones',2965,2995),('high_zones',2964,2994),('school_zone_links',2961,2991)]
results=[]
for name,ntt,fileid in FILES:
    url=f'https://schoolzone.emac.kr/publicData/publicDataFileDownload.do?nttId={ntt}&atchFileId=FILE_00000010000{fileid}&fileSn=0'
    path=RAW/(name+'.zip'); header_filename=None
    if not path.exists():
        req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(req,timeout=45) as response, path.with_suffix('.part').open('wb') as stream:
            header_filename=response.headers.get('Content-Disposition')
            size=0
            while chunk:=response.read(1024*1024):
                size+=len(chunk)
                if size>80*1024*1024:raise RuntimeError('Unexpected file size; stopped at 80 MiB')
                stream.write(chunk)
        path.with_suffix('.part').replace(path)
    with zipfile.ZipFile(path) as archive:
        if archive.testzip():raise RuntimeError('ZIP CRC check failed')
        entries=[{'name':i.filename,'bytes':i.file_size} for i in archive.infolist()]
        projections=[]
        for member in archive.namelist():
            if member.lower().endswith('.prj'):
                projections.append(archive.read(member).decode('utf8',errors='replace')[:1600])
        results.append({'layer':name,'path':str(path.relative_to(HERE)),
                        'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size,
                        'download_url':url,'download_header':header_filename,'entries':entries,
                        'projection_wkt':projections,'zip_crc':'pass'})
manifest={'collected_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'source':'한국교육시설안전원 학구도안내서비스',
          'source_url':'https://schoolzone.emac.kr/publicData/publicDataList.do',
          'listing_reference_date':'2026-09-20',
          'date_note':'목록 기준일과 파일명/행별 기준일은 별도로 확인한다.',
          'status':'downloaded; not yet imported into atlas',
          'files':results,'paid_calls':0,'personal_data_sent':False}
(HERE/'education_sources.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'status':manifest['status'],'files':len(results),'bytes':sum(r['bytes'] for r in results),
                  'manifest':str(HERE/'education_sources.json'),
                  'layers':[{'layer':r['layer'],'entries':len(r['entries']),'has_shp':any(x['name'].lower().endswith('.shp') for x in r['entries'])} for r in results]},ensure_ascii=False))
