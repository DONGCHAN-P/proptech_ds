from pathlib import Path
import requests,re
p=Path(__file__).parent
u='https://eum.go.kr/web/gs/gv/gvGosiDet.jsp?seq=642455'
r=requests.get(u,timeout=30);r.raise_for_status();r.encoding='euc-kr';(p/'latest_plan_entry.html').write_text(r.text,encoding='utf-8')
for line in r.text.splitlines():
 if any(k in line for k in ['pdf','FileDown','fileDown','파일','download','다운로드']):print(line.strip()[:1200])
pos=r.text.find('function download');print(r.text[pos:pos+700])
import sys,json,hashlib,urllib.parse
sys.path.insert(0,str(Path('video-agent-studio/episodes/namyangju-wangsuk-20261014/research/map-led-v5/_pdfdeps').resolve()))
import pymupdf
manifest=[]
for i,path in enumerate(re.findall(r"javascript:download\('/web/FileDownload.do', '([^']+)'\)",r.text)):
 payload=urllib.parse.urlencode({'file':path,'gosi':'Y','seq':'642455','mobile_yn':''},encoding='euc-kr')
 b=requests.post('https://eum.go.kr/web/FileDownload.do',data=payload,headers={'Content-Type':'application/x-www-form-urlencoded','Referer':u},timeout=35).content
 name=['latest_plan_20261008.pdf','latest_plan_map_20261008.pdf'][i]
 if not b.startswith(b'%PDF'):raise ValueError('not pdf')
 (p/name).write_bytes(b);d=pymupdf.open(stream=b,filetype='pdf')
 (p/name.replace('.pdf','.txt')).write_text('\n'.join(f'=== PAGE {j+1} ===\n'+pg.get_text() for j,pg in enumerate(d)),encoding='utf-8')
 if i==1:
  for j,pg in enumerate(d):pg.get_pixmap(matrix=pymupdf.Matrix(2,2)).save(p/f'latest_plan_map_p{j+1}.png')
 manifest.append({'file':name,'entry_url':u,'download_endpoint':'https://eum.go.kr/web/FileDownload.do','form_file':path,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'pages':len(d)})
(p/'latest_plan_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');print(manifest)
