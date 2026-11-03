from pathlib import Path
import sys,json,hashlib,shutil,csv,statistics,urllib.request,concurrent.futures
P=Path(__file__).resolve().parent; R=P.parent; E=R.parent
sys.path.insert(0,str(E.parent/'namyangju-wangsuk-20261014/research/map-led-v5/_pdfdeps'))
import pymupdf,duckdb
O=E/'outputs/source-review-v7'; O.mkdir(parents=True,exist_ok=True)
facts=json.loads((R/'price-stage-v3/facts.json').read_text(encoding='utf-8'))['facts']
prices=[f for f in facts if f['claim_id'].endswith('-STAGE')]
manifest=[]
def download(f):
 try:
  b=urllib.request.urlopen(f['source_url'],timeout=15).read()
  if not b.startswith(b'%PDF'): raise ValueError('response is not PDF')
  return b,'downloaded 2026-10-18'
 except Exception as e:return Path(f['local_path']).read_bytes(),'preserved official PDF; online refresh failed: '+type(e).__name__
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool: results=list(pool.map(download,prices))
for f,(b,note) in zip(prices,results):
 block=f['price']['scope'].split()[0]; dest=O/(block+'_official.pdf');dest.write_bytes(b)
 doc=pymupdf.open(dest); pages={'S1':[6,7],'S4':[6,7],'S5':[5,8]}[block]
 imgs=[]
 for num in pages:
  page=doc[num-1]; image=O/f'{block}_p{num}_original.png';page.get_pixmap(matrix=pymupdf.Matrix(2,2)).save(image)
  crop=O/f'{block}_p{num}_table.png';rect=page.rect;rect.y0=rect.height*.08;rect.y1=rect.height*.92;page.get_pixmap(matrix=pymupdf.Matrix(3,3),clip=rect).save(crop)
  (O/f'{block}_p{num}.txt').write_text(page.get_text(),encoding='utf-8');imgs.append(str(crop))
 f.update(checked_on='2026-10-18',source_file=str(dest),status='qualified',qualification=note,visual_evidence=imgs)
 manifest.append({'block':block,'source_url':f['source_url'],'file':str(dest),'sha256':hashlib.sha256(b).hexdigest(),'refresh':note,'pages':pages,'table_images':imgs,'rights':'공고 사실 추출 및 근거 제시용 최소한의 인용 후보. 원문 이미지의 상업 영상 재사용 허락/공공누리 유형은 미확인. 출처·공고일·페이지를 함께 표시하고 사실은 재작성 표로 이용 가능.'})
rows=list(csv.DictReader((R/'prices-v2/verified_rows.csv').open(encoding='utf-8-sig')))
comparisons=json.loads((R/'prices-v2/comparisons.json').read_text(encoding='utf-8'))
cs=comparisons.get('comparisons',comparisons.get('items',[])) if isinstance(comparisons,dict) else comparisons
if not cs:cs=json.loads((R/'prices-v2/facts.json').read_text(encoding='utf-8'))['facts']
con=duckdb.connect(); out=[]
for f in cs:
 if 'apt_id' not in f or 'median_manwon' not in f:continue
 data=[r for r in rows if r['apt_id']==f['apt_id']]; m=statistics.median(int(r['deal_amount']) for r in data)
 assert len(data)==f['n'] and m==f['median_manwon']
 coord=con.execute("SELECT lat,lng,road_address,match_status FROM 'master/apt_id_map.parquet' WHERE apt_id=?",[f['apt_id']]).fetchone()
 out.append({**f,'audit_recomputed':True,'snapshot_reused':'2026-10-16 official XML; no new RTMS request 2026-10-18','latitude':coord[0] if coord else None,'longitude':coord[1] if coord else None,'address':coord[2] if coord else None,'coordinate_match_status':coord[3] if coord else None,'coordinate_source_file':'master/apt_id_map.parquet','coordinate_limits':'기존 마스터 대표점, 출입구/도보경로 아님; 이번 별도 지오코딩 없음'})
out.sort(key=lambda x:x['median_manwon'],reverse=True)
(P/'price_table_descending.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
(P/'resale_map.geojson').write_text(json.dumps({'type':'FeatureCollection','crs_note':'WGS84 EPSG:4326 longitude,latitude','features':[{'type':'Feature','geometry':{'type':'Point','coordinates':[f['longitude'],f['latitude']]},'properties':f} for f in out if f['latitude'] is not None]},ensure_ascii=False,indent=2),encoding='utf-8')
(P/'facts.json').write_text(json.dumps({'revision':'revision-v7','checked_on':'2026-10-18','facts':prices,'resale_audit':out},ensure_ascii=False,indent=2),encoding='utf-8')
(O/'source_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'sources':manifest,'resale':[{k:x[k] for k in ['name','median_manwon','n','latitude','longitude']} for x in out]},ensure_ascii=False))
