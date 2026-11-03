from pathlib import Path
import pandas as pd,json,struct,gzip,base64,hashlib,argparse
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent
parser=argparse.ArgumentParser(description='공식 원투영 단지 atlas 정적/오프라인 빌드')
parser.add_argument('--downloads-dir',type=Path,default=Path.home()/'Downloads')
parser.add_argument('--source-dir',type=Path,default=ROOT/'video-agent-studio/episodes/capital-10eok-map-20261017/research/coordinate-link-v2')
parser.add_argument('--output-dir',type=Path,default=HERE)
args=parser.parse_args();OUT=args.output_dir.resolve();OUT.mkdir(parents=True,exist_ok=True);SRC=args.source_dir.resolve();DOWN=args.downloads_dir.resolve()
attrs=pd.read_parquet(SRC/'capital_official_geometry.parquet');indexes={int(v.record_index):v for v in attrs.itertuples()}
extras={};sources=[]
for code in ['AI','AJ','AK','AM']:
 files=list(DOWN.glob('ES1001'+code+'*csv.csv'));assert len(files)==1
 f=files[0];df=pd.read_csv(f,sep='|',dtype=str).fillna('');assert not df.HSMP_INNB.duplicated().any();extras[code]=df.set_index('HSMP_INNB').to_dict('index');sources.append({'file':f.name,'rows':len(df),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
s=(SRC/'raw/APHUS_HSMP_CNTC_INFO.shp').read_bytes();p=100;idx=0;items=[];join={k:0 for k in extras}
while p<len(s):
 _,words=struct.unpack_from('>2i',s,p);q=s[p+8:p+8+words*2];p+=8+words*2
 if idx in indexes:
  v=indexes[idx];assert struct.unpack_from('<i',q)[0]==5;nr,np=struct.unpack_from('<2i',q,36);st=list(struct.unpack_from('<'+'i'*nr,q,44))+[np];pts=list(struct.iter_unpack('<2d',q[44+4*nr:44+4*nr+16*np]));rings=[[[round(x),round(y)] for x,y in pts[st[j]:st[j+1]]] for j in range(nr)]
  ex={}
  for k,lookup in extras.items():
   row=lookup.get(v.HSMP_INNB)
   if row:join[k]+=1;ex[k]=row
  items.append({'id':v.HSMP_INNB,'name':v.POT_HSM_NM or v.BLD_HSM_NM or v.ROD_HSM_NM,'names':[v.POT_HSM_NM,v.BLD_HSM_NM,v.ROD_HSM_NM],'addr':v.LNNO_ADRES,'road':v.RN+' '+v.ROAD_HMNO+('-'+v.ROAD_VCNO if v.ROAD_VCNO and v.ROAD_VCNO!='0' else ''),'code':v.SIGNGU_CD,'pnu':v.PNU,'homes':v.NMHSH,'dongs':v.DONG_CNT,'approved':v.USE_AP_YMD,'xy':[round(v.x_5179),round(v.y_5179)],'bbox':list(struct.unpack_from('<4d',q,4)),'rings':rings,'extra':ex})
 idx+=1
boundary=json.loads((ROOT/'assets/geo/sudogwon_sgg.geojson').read_text(encoding='utf8'))
data={'items':items,'boundary':boundary,'meta':{'schema_version':'1.0.0','dataset_date':'2025','auxiliary_dates':{'AI':'2025','AJ':'2025','AK':'2026Q1','AM':'2026-08'},'id_field':'HSMP_INNB','crs':'EPSG:5179','attribution':'한국부동산원 공동주택 단지 연계정보(2025) · 좌표 가공; 경계: 통계청 SGIS (statgarten/maps, MIT)','source':'한국부동산원 공동주택 단지 연계정보(2025)','source_url':'https://www.bigdata-realestate.kr/rebpp/usr/prd/prdInfoDetail.do?req_productId=1','zip_sha256':'44cd4bd9df1c2582d0e022bd5f630df6709b37cd98ae72ff3cc48676e7dbd2e8','extras':sources,'joins':join}}
education=HERE/'layers/processed/education.json'
if education.exists():
 data['education']=json.loads(education.read_text(encoding='utf8'));data['meta']['education']=data['education']['meta']
transit=HERE/'layers/processed/transit.json'
if transit.exists():
 data['transit']=json.loads(transit.read_text(encoding='utf8'));data['meta']['transit']=data['transit']['meta']
overlays=HERE/'layers/processed/overlays.json'
if overlays.exists():
 data['overlays']=json.loads(overlays.read_text(encoding='utf8'));data['meta']['overlays']=data['overlays']['meta']
raw=json.dumps(data,ensure_ascii=False,separators=(',',':')).encode();compressed=gzip.compress(raw,9,mtime=0);revision=hashlib.sha256(compressed).hexdigest()[:16];payload=base64.b64encode(compressed).decode();template=(HERE/'src/explorer.template.html').read_text(encoding='utf8');js=(HERE/'src/app.js').read_text(encoding='utf8');css=(HERE/'src/explorer-v3.css').read_text(encoding='utf8')
js=(HERE/'src/overlays.js').read_text(encoding='utf8')+'\n'+(HERE/'vendor/proj4.js').read_text(encoding='utf8')+'\n'+(HERE/'src/basemap.js').read_text(encoding='utf8')+'\n'+(HERE/'src/ui-v3.js').read_text(encoding='utf8')+'\n'+(HERE/'src/explorer.js').read_text(encoding='utf8')+'\n'+(HERE/'src/transit.js').read_text(encoding='utf8')+'\n'+(HERE/'src/education.js').read_text(encoding='utf8')+'\n'+js
revision=hashlib.sha256(compressed+js.encode()+css.encode()+template.encode()).hexdigest()[:16]
def render(style,script,config):return template.replace('__STYLE_TAG__',style).replace('__SCRIPT_TAG__',script).replace('__CONFIG_TAG__','<script>window.ATLAS_CONFIG='+json.dumps(config,separators=(',',':'))+';</script>')
html=render('<style>'+css+'</style>','<script>'+js+'</script>',{'schema_version':'1.0.0','revision':revision,'inlineGzip':payload});(OUT/'index.html').write_text(html,encoding='utf8')
web=OUT/'web';(web/'assets/data').mkdir(parents=True,exist_ok=True);(web/'assets/app.js').write_text(js,encoding='utf8');(web/'assets/styles.css').write_text(css,encoding='utf8');(web/'assets/data/atlas.json.gz').write_bytes(compressed)
(web/'index.html').write_text(render(f'<link rel="stylesheet" href="assets/styles.css?v={revision}">',f'<script src="assets/app.js?v={revision}" defer></script>',{'schema_version':'1.0.0','revision':revision,'dataUrl':'assets/data/atlas.json.gz?v='+revision}),encoding='utf8')
manifest={'schema_version':'1.0.0','revision':revision,'payload_sha256':hashlib.sha256(compressed).hexdigest(),'payload':'assets/data/atlas.json.gz','payload_bytes':len(compressed),'item_count':len(items),'meta':data['meta'],'http_contract':{'content_type':'application/gzip','content_encoding':'omit (payload is gzip file; JS decompresses); auto-decoded JSON also accepted via magic bytes','relative_paths':True,'cache_revision_query':revision},'assets':{x:hashlib.sha256((web/x).read_bytes()).hexdigest() for x in ['assets/app.js','assets/styles.css']}}
(OUT/'data').mkdir(exist_ok=True);(OUT/'data/source_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8');(web/'source_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
validation={'count':len(items),'unique_ids':len(set(x['id'] for x in items)),'crs':'EPSG:5179 native xy; no lonlat conversion','coordinate_rounding_m':1,'extra_join_count':join,'input_files':sources,'index_bytes':len(html.encode()),'payload_json_bytes':len(raw),'external_requests_required':0,'network_or_paid_calls':0,'ui_validation':'pending browser QA','index_sha256':hashlib.sha256(html.encode()).hexdigest()};(OUT/'validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(validation,ensure_ascii=False,indent=2))
