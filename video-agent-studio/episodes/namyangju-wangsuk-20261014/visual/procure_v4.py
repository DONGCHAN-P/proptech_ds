from pathlib import Path
import urllib.request,urllib.parse,json,time,sys
sys.stdout.reconfigure(encoding='utf-8');root=Path(__file__).parent
def get(params):
 url='https://commons.wikimedia.org/w/api.php?'+urllib.parse.urlencode(params)
 req=urllib.request.Request(url,headers={'User-Agent':'NamyangjuEditorialVideo/1.0 (public image licensing research)'})
 return json.loads(urllib.request.urlopen(req,timeout=25).read())
all=[]
for q in ['Byeollae','Dasan Namyangju','Jinjeop','Namyangju station']:
 try:
  d=get({'action':'query','format':'json','generator':'search','gsrsearch':q,'gsrnamespace':6,'gsrlimit':8,'prop':'imageinfo','iiprop':'url|size|extmetadata'})
  pages=list(d.get('query',{}).get('pages',{}).values());all.extend(pages);print(q,len(pages))
 except Exception as e:print(q,type(e).__name__,str(e)[:150])
 time.sleep(1)
(root/'commons_candidates_v4.json').write_text(json.dumps(all,ensure_ascii=False,indent=2),'utf-8')
for p in all:
 i=p.get('imageinfo',[{}])[0];m=i.get('extmetadata',{});print(p['title'],m.get('LicenseShortName',{}).get('value'),i.get('width'),i.get('height'))
