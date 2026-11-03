from pathlib import Path
import urllib.request,urllib.parse,json,hashlib,re
from bs4 import BeautifulSoup
P=Path(__file__).parent;R=P/'raw';R.mkdir(parents=True,exist_ok=True);records=[]
def save(n,u):
 try:
  b=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=20).read();(R/n).write_bytes(b);records.append({'file':str(R/n),'url':u,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'status':'downloaded'});return b
 except Exception as e:records.append({'file':n,'url':u,'status':'failed','error':str(e)[:100]});return b''
b=save('eum_gosi_2025_813.html','https://www.eum.go.kr/web/gs/gv/gvGosiDet.jsp?seq=628391')
s=BeautifulSoup(b,'html.parser');(R/'eum_gosi_2025_813.txt').write_text(s.get_text('\n',strip=True),encoding='utf-8')
save('eum_copyright.html','https://www.eum.go.kr/web/lc/bi/biCopyRight.jsp')
save('s4_landuse_202607.jpg','https://apply.lh.or.kr/lhapply/lhFile.do?fileid=67715155')
save('eum_kogl_mark.png','https://www.eum.go.kr/web/images/ar/nuri.png')
# Follow only the official attachment link for one overall zoning drawing, retaining original query encoding.
for a in s.find_all('a'):
 h=a.get('href','');label=a.get_text(' ',strip=True)
 if 'DownloadBig' in h and '용도지역' in label and '총괄도' in label:
  h=urllib.parse.urljoin('https://www.eum.go.kr',h);h=urllib.parse.quote(h,safe=':/?=&%;+');save('eum_zoning_overall.jpg',h);break
(P/'download_manifest.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps([{'file':Path(x['file']).name,'status':x['status'],'bytes':x.get('bytes')}for x in records],ensure_ascii=False));print('charset',s.original_encoding);print([(a.get_text(' ',strip=True)[:80],a.get('href','')[:180])for a in s.find_all('a')if 'DownloadBig' in a.get('href','')][:2])
