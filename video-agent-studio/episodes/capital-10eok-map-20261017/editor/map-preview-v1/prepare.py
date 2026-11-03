from pathlib import Path
import json,hashlib
import sys,types,subprocess
# Existing Node's built-in Brotli decoder; no package installation.
def brotli_decode(buf):
 return subprocess.run(['node','-e',"const z=require('zlib'),a=[];process.stdin.on('data',b=>a.push(b));process.stdin.on('end',()=>process.stdout.write(z.brotliDecompressSync(Buffer.concat(a))));"],input=buf,capture_output=True,check=True).stdout
sys.modules['brotli']=types.SimpleNamespace(decompress=brotli_decode)
from fontTools.ttLib import TTFont
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from geometry import forward,inside
P=Path(__file__).resolve().parent;E=P.parent.parent;R=E.parents[2];V=E/'visual/map-preview-v1';V.mkdir(exist_ok=True,parents=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for weight in ['Regular','Bold']:
 src=R/f'video/public/changneung-v3/Pretendard-{weight}.woff2';dst=V/f'Pretendard-{weight}.ttf'
 if not dst.exists():
  f=TTFont(src);f.flavor=None;f.save(dst)
boundary=R/'assets/geo/sudogwon_sgg.geojson';d=json.loads(boundary.read_text(encoding='utf-8'));anchor=[127.0275574,37.4979497];p=forward(*anchor);matches=[f['properties']['name'] for f in d['features'] if f['properties']['region']=='서울' and inside(p,f['geometry'])];passed=bool(matches);assert passed,'강남역-서울 경계 정합 실패'
report={'boundary_sha256':sha(boundary),'boundary_features':len(d['features']),'inferred_crs':'EPSG:5179','local_file_crs_metadata_present':False,'crs_inference_scope':'SGIS 출처+공식SGIS 좌표계 설명+강남역 앵커 서울면내 검사. 파일별 CRS 인증이나 정밀도 검증 아님.','anchor':{'name':'강남역','lonlat':anchor,'projected_xy':p,'inside_seoul':passed,'matched_districts':matches,'source':'기존 검증 OSM node5927529147'},'sources':['assets/geo/LICENSE.md','https://github.com/statgarten/maps','https://sgis.mods.go.kr/view/pss/dataProvdIntrcn','https://sgis.kostat.go.kr/developer/upload/doc/DataAPI-definition.pdf'],'metadata_issue':'LICENSE의 °솎아냄 표기와 실제 투영 좌표 단위가 모순. 원본은 보존.','font_conversion':'기존 Pretendard WOFF2를 설치 없이 TTF로 변환, 새 의존성 없음'}
(V/'geometry_preflight.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report['anchor'],ensure_ascii=False))
