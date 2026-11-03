import urllib.request,urllib.parse,pathlib,json,re,concurrent.futures
p=pathlib.Path(__file__).parent;out=p/'source_assets';out.mkdir(exist_ok=True)
urls={'woori_bank_logo':'https://simg.wooribank.com/img/intro/header/h1_01.png','kakao_chunk':'https://www.kakaocorp.com/page/_nuxt/74f6889.js'}
def fetch(k,u):
 try:
  b=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=35).read();ext='.pdf'if b[:4]==b'%PDF'else'.svg'if u.endswith('.svg')else'.zip'if u.endswith('.zip')else'.jpg'if u.endswith('.jpg')else'.png'if u.endswith('.png')else'.html';(out/(k+ext)).write_bytes(b)
  s=b.decode('utf-8','replace') if ext=='.html'else''
  assets=[]
  for m in re.finditer(r'''(?:src|href)=["']([^"']+)["']|url\(["']?([^\)"']+)''',s):
   a=m.group(1) or m.group(2)
   if any(x in a.lower() for x in ['logo','ci_','_ci','.css']):assets.append(urllib.parse.urljoin(u,a))
  return dict(id=k,url=u,bytes=len(b),file=k+ext,asset_candidates=list(dict.fromkeys(assets)))
 except Exception as e:return dict(id=k,url=u,error=str(e))
with concurrent.futures.ThreadPoolExecutor(max_workers=5)as pool:r=list(pool.map(lambda z:fetch(*z),urls.items()))
(p/'company_downloads.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(r,ensure_ascii=False))
