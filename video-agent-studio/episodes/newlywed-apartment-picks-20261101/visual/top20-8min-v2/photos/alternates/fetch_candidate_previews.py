import sys,json,hashlib,time
from pathlib import Path
from PIL import Image
sys.dont_write_bytecode=True
ALT=Path(__file__).resolve().parent;sys.path.insert(0,str(ALT))
from collect_alternates import fetch,dump,ROOT
CHOICES=[(2,163360944),(2,163360945),(6,44957993),(6,44957994)]
for n,(rank,pageid) in enumerate(CHOICES):
 if n:time.sleep(2)
 d=json.loads((ALT/f'evidence/batch1_R{rank:02d}.json').read_text(encoding='utf-8'))
 p=next(p for p in d['response']['query']['pages'] if p['pageid']==pageid);ii=p['imageinfo'][0]
 dst=ALT/f'candidate_R{rank:02d}_{pageid}_1280.jpg'
 try:
  dst.write_bytes(fetch(ii['thumburl']))
  with Image.open(dst) as im:im.load();dims=im.size
  dump(ALT/f'evidence/candidate_{pageid}.json',{'page':p,'file':str(dst.relative_to(ROOT)),'download_url':ii['thumburl'],'sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'dimensions':dims})
  print(json.dumps({'rank':rank,'title':p['title'],'file':str(dst),'dimensions':dims},ensure_ascii=False),flush=True)
 except Exception as e:print(pageid,str(e),flush=True)
