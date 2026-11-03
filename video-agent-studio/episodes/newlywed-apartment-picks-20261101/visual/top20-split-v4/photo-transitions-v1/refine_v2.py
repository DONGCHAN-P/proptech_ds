"""Two-asset revision only; v1 assets and photo bytes remain unchanged."""
import concurrent.futures
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
from collect import ROOT, OLD, api, fetch, plain
from PIL import Image,ImageOps,ImageDraw,ImageFont

E=ROOT/'evidence_v2';E.mkdir(exist_ok=True)

def search(item):
    tag,q=item
    d,u=api(dict(action='query',generator='search',gsrsearch=q,gsrnamespace=6,gsrlimit=12,
                prop='imageinfo|coordinates',iiprop='url|size|extmetadata|sha1',iiurlwidth=1920,colimit='max'))
    (E/f'search_{tag}.json').write_text(json.dumps({'url':u,'query':q,'response':d},ensure_ascii=False,indent=2),'utf-8')
    out=[]
    for p in sorted(d.get('query',{}).get('pages',[]),key=lambda p:p.get('index',99)):
        i=p.get('imageinfo',[{}])[0];e=i.get('extmetadata',{});v=lambda k:plain(e.get(k,{}).get('value'))
        out.append({'id':p['pageid'],'title':p['title'],'size':[i.get('width'),i.get('height')],
                    'license':v('LicenseShortName'),'date':v('DateTimeOriginal'),'description':v('ImageDescription')[:240]})
    return {'tag':tag,'candidates':out}

def previews(jungnang=False):
    titles=(['File:ROK National Route 47 Yongmasanro Neungsan Tway Intersection(Sinnae IC Dir).jpg',
             'File:Costco Sangbong branch Seoul Korea 20181122 161832.jpg'] if jungnang else
            ['File:Tongil-ro at Gupabal Station.jpg','File:Eunpyeong New Town Lotte Castle.jpeg',
             'File:ROK National Route 6 Manguro Mangu Crossroad(Westward Dir) 1.jpg'])
    pages={}
    for f in E.glob('search_*.json'):
        for p in json.loads(f.read_text('utf-8'))['response'].get('query',{}).get('pages',[]):pages[p['title']]=p
    sheet=Image.new('RGB',(960,310*len(titles)),'#162330');draw=ImageDraw.Draw(sheet)
    for n,t in enumerate(titles):
        p=pages[t];i=p['imageinfo'][0];dest=E/f'preview_{p["pageid"]}.jpg';dest.write_bytes(fetch(i['thumburl']))
        with Image.open(dest) as im:im=ImageOps.fit(ImageOps.exif_transpose(im).convert('RGB'),(960,270));sheet.paste(im,(0,n*310+40))
        draw.text((10,n*310+10),t,fill='white')
    sheet.save(E/('candidates19.jpg' if jungnang else 'candidates.jpg'))

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='previews':
        previews();sys.exit()
    if len(sys.argv)>1 and sys.argv[1]=='previews19':
        previews(True);sys.exit()
    qs=[('R19e','intitle:"Sangbong" -sign -train -platform'),
        ('R19f','intitle:"Sinnae" -station -train -sign')]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for r in pool.map(search,qs):print(json.dumps(r,ensure_ascii=False),flush=True)
