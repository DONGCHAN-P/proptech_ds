"""Narrow public GET-only collection; preserve v1 and cap search batches at six."""
import argparse
from datetime import datetime, timezone
import hashlib,html,json,re,time,urllib.parse,urllib.request
from pathlib import Path
from PIL import Image
ALT=Path(__file__).resolve().parent
EVI=ALT/'evidence';EVI.mkdir(exist_ok=True)
ROOT=ALT.parents[1]
API='https://commons.wikimedia.org/w/api.php'
UA='RealEstateVideoResearch/1.1 (public photo metadata; no upload)'
def plain(s):return html.unescape(re.sub('<[^>]+>',' ',s or '')).strip()
def fetch(url):
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':UA}),timeout=25) as r:return r.read()
def api(params):
 u=API+'?'+urllib.parse.urlencode(dict(params,format='json',formatversion=2));return json.loads(fetch(u)),u
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def summarise(data):
 out=[]
 for p in data.get('query',{}).get('pages',[]):
  ii=p.get('imageinfo',[{}])[0];ex=ii.get('extmetadata',{});v=lambda k:plain(ex.get(k,{}).get('value',''))
  lic=v('LicenseShortName');cats=[x['title'] for x in p.get('categories',[])];text=json.dumps(p,ensure_ascii=False)
  if lic not in ['CC0','CC BY 2.0','CC BY 3.0','CC BY 4.0','KOGL Type 1']:continue
  out.append({'pageid':p['pageid'],'title':p['title'],'size':[ii.get('width'),ii.get('height')],'license':lic,
      'date':v('DateTimeOriginal'),'description':v('ImageDescription')[:650],
      'coords':p.get('coordinates'),'risk_markers':[c for c in cats if any(k in c.lower() for k in ['nofop','minimis','incidental','permission','copyright'])],
      'restrictive_description':any(k in v('ImageDescription').lower() for k in ['may not be manipulated','non-commercial','news organizations','all rights reserved'])})
 return out
def search(batch,queries):
 logp=EVI/'search_batches.json';log=json.loads(logp.read_text(encoding='utf-8')) if logp.exists() else []
 assert len(log)<6,'Six search batches already used'
 entry={'batch':batch,'utc':datetime.now(timezone.utc).isoformat(),'queries':queries};log.append(entry);dump(logp,log)
 for n,(rank,kind,value) in enumerate(queries):
  if n:time.sleep(3)
  params=dict(action='query',prop='imageinfo|coordinates|categories|revisions',cllimit=50,colimit='max',
    rvprop='ids|timestamp|content',rvslots='main',iiprop='url|size|sha1|extmetadata',iiurlwidth=1280,iiextmetadatalanguage='en')
  if kind=='category':params.update(generator='categorymembers',gcmtitle='Category:'+value,gcmnamespace=6,gcmlimit=50)
  else:params.update(generator='search',gsrsearch=value,gsrnamespace=6,gsrlimit=20)
  try:
   data,url=api(params);dst=EVI/f'batch{batch}_R{rank:02d}.json';dump(dst,{'request_url':url,'retrieved_utc':datetime.now(timezone.utc).isoformat(),'response':data})
   print(json.dumps({'rank':rank,'query':value,'candidates':summarise(data),'continue':data.get('continue'),'error':data.get('error')},ensure_ascii=False),flush=True)
  except Exception as e:print(json.dumps({'rank':rank,'error':str(e)},ensure_ascii=False),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--batch',type=int,required=True);p.add_argument('--queries-file',required=True);a=p.parse_args();search(a.batch,json.loads(Path(a.queries_file).read_text(encoding='utf-8')))
