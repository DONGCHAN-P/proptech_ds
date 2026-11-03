import sys,json,hashlib,re,urllib.parse,time
from datetime import datetime,timezone
from pathlib import Path
from PIL import Image,ImageOps
sys.dont_write_bytecode=True
ALT=Path(__file__).resolve().parent;sys.path.insert(0,str(ALT))
from collect_alternates import api,fetch,dump,plain,ROOT,EVI
def record(rank,dst,url,meta):
 b=fetch(url);dst.write_bytes(b)
 with Image.open(dst) as im:
  im.load();raw=im.size;display=ImageOps.exif_transpose(im);dims=display.size
  exif={str(k):str(v) for k,v in im.getexif().items() if k in [270,271,272,274,305,306,315,33432,36867,40091,40092,40093,40094,40095]}
 rec={'rank':rank,'actual_file':dst.relative_to(ROOT).as_posix(),'download_url':url,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),
     'dimensions':list(dims),'stored_dimensions':list(raw),'decoded':True,'source':meta,'exif':exif,'retrieved_utc':datetime.now(timezone.utc).isoformat()}
 dump(EVI/f'R{rank:02d}_alternate_receipt.json',rec);print(json.dumps({'rank':rank,'file':str(dst),'dimensions':dims,'exif':exif},ensure_ascii=False))

if __name__=='__main__':
 # Single title request returns complete category list; the broad candidate response had category continuation.
 data,u=api(dict(action='query',titles='File:20250409 석촌호수공원 2.jpg',prop='imageinfo|categories|revisions|coordinates',
    cllimit='max',colimit='max',rvprop='ids|timestamp|content',rvslots='main',iiprop='url|size|sha1|extmetadata',iiurlwidth=3840,iiextmetadatalanguage='en'))
 dump(EVI/'R02_final_commons.json',{'request_url':u,'response':data})
 p=data['query']['pages'][0];ii=p['imageinfo'][0]
 # Standard CDN avoids the previously observed original-server rate limit.
 record(2,ALT/'R02_ALT_석촌호수_수변_CC0.jpg',ii['thumburl'],{'provider':'Wikimedia Commons','page':p,'metadata_file':str((EVI/'R02_final_commons.json').relative_to(ROOT))})
 for rank,code,page in [(6,'06A05509Bb60000','https://data.si.re.kr/photo/06a05509bb60000'),(11,'06I00312Ac30000','https://data.si.re.kr/node/58286')]:
  time.sleep(2)
  url=f'https://data.si.re.kr/sites/default/files/photos6/{code}.jpg'
  meta={'provider':'서울특별시·서울연구원 서울연구데이터서비스','code':code,'file_page':page,
      'metadata_file':str((EVI/f'R{rank:02d}_SI_candidate.html').relative_to(ROOT)),
      'copyright_policy':'https://data.si.re.kr/node/65064#photo-rights',
      'license_links':['https://www.kogl.or.kr/info/licenseType1.do','https://creativecommons.org/licenses/by/4.0/deed.ko']}
  record(rank,ALT/f'R{rank:02d}_ALT_{"양재천산책로" if rank==6 else "경춘선숲길"}_서울경관.jpg',url,meta)
 policy=fetch('https://data.si.re.kr/node/65064');(EVI/'SI_photo_rights_policy.html').write_bytes(policy)
