from pathlib import Path
import sys,requests,json,hashlib
P=Path(__file__).parent
sys.path.insert(0,str(Path('video-agent-studio/episodes/namyangju-wangsuk-20261014/research/map-led-v5/_pdfdeps').resolve()))
import pymupdf
u='https://www.hanam.go.kr/DATA/newsletter/3842/20251027103134309_Cygn.pdf'
r=requests.get(u,timeout=30);r.raise_for_status();assert r.content.startswith(b'%PDF');(P/'hanam_rail_official_202510.pdf').write_bytes(r.content)
d=pymupdf.open(stream=r.content,filetype='pdf');pages=[]
for i,pg in enumerate(d):
 if '송파하남선' in pg.get_text():
  pg.get_pixmap(matrix=pymupdf.Matrix(2,2)).save(P/f'rail_official_p{i+1}.png');pages.append(i+1)
(P/'rail_map_manifest.json').write_text(json.dumps({'url':u,'file':'hanam_rail_official_202510.pdf','sha256':hashlib.sha256(r.content).hexdigest(),'pages_with_rail':pages,'date':'2025-10','caution':'철도실시설계상태는2026.9.22답변우선; 지도2025공개자료. 재사용권리별도확인'},ensure_ascii=False,indent=2),encoding='utf-8');print(pages)
