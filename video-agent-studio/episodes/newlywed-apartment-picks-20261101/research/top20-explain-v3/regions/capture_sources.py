import concurrent.futures, hashlib, html, json, pathlib, re, urllib.request
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / 'source_snapshots'
OUT.mkdir(exist_ok=True)
SOURCES = {
 'R03_SAMSONG': 'https://www.goyang.go.kr/dong/dong01/dong01_4/dong01_4_5/dong01_4_5_tab1.jsp',
 'R13_GWONSEON': 'https://ksun.suwon.go.kr/submain_view.asp?MenuID=sub010401',
 'R18_DONGBAEK': 'https://www.giheunggu.go.kr/_lmth/06_dong/dong_090103.asp',
 'R18_MABUK': 'https://www.giheunggu.go.kr/_lmth/06_dong/dong_080103.asp',
 'R16_IH_LIST': 'https://www.ih.co.kr/main/land/landList.do?isComp=y&pgno=2',
 'R16_NAMDONG': 'https://www.namdong.go.kr/dong/sub/present.jsp?dong=nonhyeon2',
 'R08_YEOUIDO': 'https://hangang.seoul.go.kr/www/contents/669.do?mid=431',
 'KAPT_SEOUL': 'https://www.k-apt.go.kr/cmmn/introMmentPop.do?bjdCode=11&searchOccuDate=202609&upYn=Y'
}
class Extract(HTMLParser):
 def __init__(self): super().__init__(); self.skip=0; self.parts=[]
 def handle_starttag(self, tag, attrs):
  if tag in ('script','style'): self.skip+=1
 def handle_endtag(self, tag):
  if tag in ('script','style'): self.skip=max(0,self.skip-1)
 def handle_data(self,data):
  if not self.skip and data.strip(): self.parts.append(data.strip())
def fetch(item):
 key,url=item
 try:
  req=urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0 (compatible; factual-source-check)'})
  with urllib.request.urlopen(req, timeout=22) as resp:
   raw=resp.read(8_000_000); final=resp.url; enc=resp.headers.get_content_charset()
  if not enc:
   m=re.search(br'charset\s*=\s*[\"\']?([a-zA-Z0-9_-]+)',raw[:10000]); enc=m.group(1).decode() if m else 'utf-8'
  body=raw.decode(enc,errors='replace'); parser=Extract();parser.feed(body)
  txt='\n'.join(parser.parts); (OUT/(key+'.txt')).write_text(txt,encoding='utf-8')
  (OUT/(key+'.html')).write_bytes(raw)
  hits=[]
  for word in ['지역특성','구도심','택지','논현 웰카운티','공동주택','잠실엘스','리센츠','잠실5단지','동백2동 소개','금융']:
   pos=txt.find(word)
   if pos>=0: hits.append({'term':word,'text':txt[max(0,pos-120):pos+750]})
  return {'id':key,'url':url,'final_url':final,'checked_date':'2026-11-03','bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'encoding':enc,'text_file':str(OUT/(key+'.txt')),'status':'retrieved','hits':hits}
 except Exception as exc: return {'id':key,'url':url,'status':'failed','error':str(exc)}
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool: results=list(pool.map(fetch,SOURCES.items()))
(OUT/'capture_receipt.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
for row in results: print(json.dumps(row,ensure_ascii=False))
