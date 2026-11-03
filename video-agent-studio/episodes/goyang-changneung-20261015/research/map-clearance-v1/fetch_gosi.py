from pathlib import Path
from bs4 import BeautifulSoup
import urllib.request,urllib.parse,json,hashlib,re,io
from PIL import Image
P=Path(__file__).parent;R=P/'raw';s=BeautifulSoup((R/'eum_gosi_2025_813.html').read_bytes(),'html.parser');out=json.loads((P/'download_manifest.json').read_text(encoding='utf-8'))
for a in s.find_all('a'):
 label=a.get_text(' ',strip=True);h=a.get('href','')
 wanted=('가구및획지' in label and '본단지' in label and '총괄도' in label) or label.startswith('국토교통부고시제2025-813호.pdf')
 if not wanted:continue
 m=re.search(r"download\('([^']+)', '([^']+)'\)",h)
 if not m:continue
 n='eum_lots_overall_20251224.jpg' if '가구및획지' in label else 'eum_gosi_2025_813.pdf'
 try:
  u=urllib.parse.urljoin('https://www.eum.go.kr',m[1]);body=urllib.parse.urlencode({'file':m[2],'gosi':'Y','seq':'628391'},encoding='euc-kr').encode('ascii');b=urllib.request.urlopen(urllib.request.Request(u,data=body,headers={'Referer':'https://www.eum.go.kr/web/gs/gv/gvGosiDet.jsp?seq=628391','User-Agent':'Mozilla/5.0'}),timeout=25).read()
  if n.endswith('.jpg'):im=Image.open(io.BytesIO(b));im.verify()
  elif not b.startswith(b'%PDF'):raise ValueError('not PDF')
  (R/n).write_bytes(b);out.append({'file':str(R/n),'url':u,'form_source':'https://www.eum.go.kr/web/gs/gv/gvGosiDet.jsp?seq=628391','attachment_label':label,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'status':'downloaded'})
 except Exception as e:out.append({'file':n,'status':'failed','error':str(e)[:150]})
(P/'download_manifest.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(out[-2:],ensure_ascii=False))
