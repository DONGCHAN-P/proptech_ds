from pathlib import Path
import urllib.request,urllib.parse,json,re,hashlib,sys,concurrent.futures
from bs4 import BeautifulSoup
P=Path(__file__).parent; R=P/'raw';R.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(P.parents[2]/'namyangju-wangsuk-20261014/research/map-led-v5/_pdfdeps'))
import pymupdf
base='https://apply.lh.or.kr/lhapply/apply/wt/wrtanc/selectWrtancInfo.do?aisTpCd=05&ccrCnntSysDsCd=02&mi=1027&uppAisTpCd=05&panId='
tasks={'s5_corrected.html':base+'0000060807','s4_original.html':base+'0000061121','s1_notice.pdf':'https://gc.lynn.co.kr/fileview/1661/'+urllib.parse.quote('260430 고양 창릉 우미린_모집공고.pdf'),'gys_latest.html':'https://m.gys.or.kr/page/city/develop/changlng.php','jobs_lh.html':'https://www.lh.or.kr/gallery.es?act=view&b_list=8&bid=0003&keyField=&list_no=11516&mid=a10502000000&nPage=1&orderby=&vlist_no_npage=0'}
records=[]
def get(n,u):
 try:
  b=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=25).read();(R/n).write_bytes(b)
  if n.endswith('.pdf'):
   d=pymupdf.open(stream=b,filetype='pdf');(R/(n[:-4]+'.txt')).write_text('\n'.join('=== PAGE '+str(i+1)+' ===\n'+p.get_text()for i,p in enumerate(d)),encoding='utf-8')
  elif n.endswith('.html'):(R/(n[:-5]+'.txt')).write_text(BeautifulSoup(b,'html.parser').get_text('\n',strip=True),encoding='utf-8')
  x={'file':str(R/n),'url':u,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'status':'downloaded','checked_on':'2026-10-16'};records.append(x);return b.decode('utf-8',errors='replace')if n.endswith('.html')else ''
 except Exception as e:records.append({'file':n,'url':u,'status':'failed','error':str(e)[:140]});return ''
with concurrent.futures.ThreadPoolExecutor(max_workers=4)as ex: rs=list(ex.map(lambda z:(z[0],get(*z)),tasks.items()))
for n,s in rs:
 if n.startswith(('s5_','s4_')):
  for fid,label in re.findall(r"fileDownLoad\('([0-9]+)'\);\">([^<]+\.pdf)</a>",s):
   if '공고' in label and '팸플릿' not in label:get(n[:-5]+'.pdf','https://apply.lh.or.kr/lhapply/lhFile.do?fileid='+fid);break
  pan=re.search(r"var currPanId = '([0-9]+)'",s)
  if pan and pan.group(1)not in ('0000060807','0000061121'):
   cor=get(n.split('_')[0]+'_latest.html',base+pan.group(1))
   for fid,label in re.findall(r"fileDownLoad\('([0-9]+)'\);\">([^<]+\.pdf)</a>",cor):
    if '공고' in label and '팸플릿' not in label:get(n.split('_')[0]+'_latest.pdf','https://apply.lh.or.kr/lhapply/lhFile.do?fileid='+fid);break
(P/'download_manifest.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps([{'file':Path(x['file']).name,'status':x['status'],'bytes':x.get('bytes')}for x in records],ensure_ascii=False))
