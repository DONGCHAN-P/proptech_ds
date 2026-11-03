"""Use only the official public download button's documented request, with no email/account."""
from pathlib import Path
import sys,re,json,urllib.parse,urllib.request,hashlib
from PIL import Image
sys.dont_write_bytecode=True
ALT=Path(__file__).resolve().parent;sys.path.insert(0,str(ALT))
from collect_alternates import EVI,ROOT,fetch,dump
for rank in [6,11]:
 s=(EVI/f'R{rank:02d}_SI_candidate.html').read_text(encoding='utf-8')
 nid=re.search(r'id="photo-collection-nid" value="(\d+)"',s).group(1)
 data=urllib.parse.urlencode({'nid':nid,'purpose':'상업적 활용','purpose_detail':''}).encode()
 req=urllib.request.Request('https://data.si.re.kr/photo-n-download',data=data,
   headers={'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8','Referer':f'https://data.si.re.kr/node/{nid}','User-Agent':'RealEstateVideoResearch/1.1'})
 try:
  with urllib.request.urlopen(req,timeout=20) as r:res=json.loads(r.read())
  dump(EVI/f'R{rank:02d}_SI_public_download_response.json',{'request':{'url':req.full_url,'nid':nid,'purpose':'상업적 활용','email_sent':False},'response':res})
  if not res.get('download_url') or res.get('error'):
   print(rank,'NO_PUBLIC_FILE',str(res)[:250]);continue
  url=urllib.parse.urljoin('https://data.si.re.kr',res['download_url'])
  if urllib.parse.urlparse(url).hostname!='data.si.re.kr':raise ValueError('Unexpected download host')
  dst=ALT/f'R{rank:02d}_ALT_{"양재천산책로" if rank==6 else "경춘선숲길"}_서울경관_1600.jpg'
  b=fetch(url);dst.write_bytes(b)
  with Image.open(dst) as im:im.load();dims=im.size
  rec=json.loads((EVI/f'R{rank:02d}_alternate_receipt.json').read_text(encoding='utf-8'))
  rec['public_900px_reference']={k:rec[k] for k in ['actual_file','download_url','sha256','dimensions']}
  rec.update(actual_file=dst.relative_to(ROOT).as_posix(),download_url=url,sha256=hashlib.sha256(b).hexdigest(),bytes=len(b),dimensions=list(dims),stored_dimensions=list(dims),public_download_button_used=True)
  dump(EVI/f'R{rank:02d}_alternate_receipt.json',rec);print(json.dumps({'rank':rank,'file':str(dst),'dimensions':dims,'sha256':rec['sha256']},ensure_ascii=False))
 except Exception as e:print(rank,type(e).__name__,str(e))
