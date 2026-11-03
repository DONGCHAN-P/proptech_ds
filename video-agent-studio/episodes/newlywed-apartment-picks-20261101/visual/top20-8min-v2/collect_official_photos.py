"""Read and preserve official Cheongna park photographs with per-page KOGL type 1 evidence."""
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import sys
import urllib.parse
from PIL import Image
sys.dont_write_bytecode = True
sys.path.insert(0,str(Path(__file__).resolve().parent))
from collect_photos import ROOT, PHOTOS, EVIDENCE, fetch

PAGE='https://www.insiseol.or.kr/park/cheongna/facility/lake.jsp'
class Parser(HTMLParser):
    def __init__(self):super().__init__();self.images=[]
    def handle_starttag(self,tag,attrs):
        if tag=='img': self.images.append(dict(attrs))

if __name__=='__main__':
    data=fetch(PAGE);(EVIDENCE/'R01_official_page.html').write_bytes(data)
    parser=Parser();parser.feed(data.decode('utf-8'))
    selected=[x for x in parser.images if x.get('alt') in ['청라호수공원 사진','청라루와 호수 사진']]
    licenses=[x for x in parser.images if 'kogl_type01' in x.get('src','')]
    if not licenses: raise ValueError('No KOGL type1 mark on original page')
    out={'source_page':PAGE,'retrieved_utc':datetime.now(timezone.utc).isoformat(),
        'author':'인천시설공단 청라공원사업단','photographer':'개별 촬영자 미표시',
        'license':'공공누리 제1유형','license_version':'제1유형(웹페이지 별도 버전 미표시)',
        'license_url':'https://www.kogl.or.kr/info/licenseType1.do',
        'license_mark':licenses,'date_taken':None,'date_note':'원문 촬영일 미표시',
        'place':'청라호수공원, 인천광역시 서해구 크리스탈로 131(2026 현재 표기)', 'files':[]}
    for idx,x in enumerate(selected):
        url=urllib.parse.urljoin(PAGE,x['src']);dst=PHOTOS/f'R01_{"청라호수공원" if idx==0 else "청라루와호수"}.jpg'
        dst.write_bytes(fetch(url))
        with Image.open(dst) as im:im.load();dims=im.size
        r={'title':x['alt'],'url':url,'path':str(dst.relative_to(ROOT)),'width':dims[0],'height':dims[1],
            'sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'bytes':dst.stat().st_size,'decoded':True,
            'original':True,'variant':'official_site_published_file'}
        out['files'].append(r);print(json.dumps(r,ensure_ascii=False))
    (EVIDENCE/'R01_official_metadata.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
