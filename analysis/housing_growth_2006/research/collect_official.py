from pathlib import Path
import requests,re,json,hashlib,time,zipfile,xml.etree.ElementTree as ET
from urllib.parse import urljoin
O=Path(__file__).parent;D=O/'raw';D.mkdir(exist_ok=True);S=requests.Session();S.headers['User-Agent']='Mozilla/5.0'; records=[]
def get(url):
 r=S.get(url,timeout=60);r.raise_for_status();return r

def store(url,name,origin,params=None):
 try:
  r=S.get(url,params=params,timeout=90);r.raise_for_status();b=r.content
  if name.endswith(('.xlsx','.zip')) and not b.startswith(b'PK'):raise ValueError('not_zip_format')
  if name.endswith('.pdf') and not b.startswith(b'%PDF'):raise ValueError('not_pdf')
  (D/name).write_bytes(b);records.append(dict(name=name,source_page=origin,url=r.url,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),status='downloaded'))
  print(name,len(b),flush=True)
 except Exception as e:records.append(dict(name=name,source_page=origin,status='failed',error=type(e).__name__))
 (O/'collection_manifest.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf8')
for rid,cat in [(468,'completions'),(471,'starts'),(31,'permits'),(32,'unsold')]:
 u=f'https://stat.molit.go.kr/portal/cate/statMetaView.do?hRsId={rid}';s=get(u).text;(D/f'metadata_{cat}.html').write_text(s,encoding='utf8')
 links=re.findall(r"downFile\('([^']*)','([^']*)','([^']*)','[^']*'\)",s)
 selected=[]
 for orig,remote,mid in links:
  if (cat!='unsold' and (('25년)' in orig and '지역별' in orig) or ('2025년' in orig and orig.endswith('.zip')))) or (cat=='unsold' and orig.lower().endswith(('.xlsx','.xls','.zip'))):selected.append((orig,remote,mid))
 for i,(orig,remote,mid) in enumerate(selected[:30]):
  name=f'{cat}_{i:02d}'+Path(orig).suffix.lower();store('https://stat.molit.go.kr/portal/common/downLoadFile.do',name,u,dict(oFileName=orig,rFileName=remote,midpath=mid));records[-1]['original_name']=orig
 (O/'collection_manifest.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf8')
for bid,lid,label in [(205,443278,'migration_2025'),(233,438719,'employment_2024')]:
 u=f'https://mods.go.kr/board.es?act=view&bid={bid}&list_no={lid}&mid=a10301020100';s=get(u).text
 for path,title in re.findall(r'<a class="bvf_name" href="([^"]+)">([^<]+)</a>',s):
  if title.endswith(('.xlsx','.pdf')):store(urljoin(u,path),label+Path(title).suffix,u)
u='https://www.bok.or.kr/portal/singl/baseRate/progress.do?dataSeCd=01&menuNo=200643'
s=get(u).text;(D/'bok_base_rate.html').write_text(s,encoding='utf8');records.append(dict(name='bok_base_rate.html',source_page=u,status='downloaded',bytes=len(s.encode())))
(O/'collection_manifest.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf8')
print('done',sum(x['status']=='downloaded' for x in records))
