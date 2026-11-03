from pathlib import Path
import requests,re,json,hashlib
from urllib.parse import urljoin
O=Path(__file__).parent;D=O/'raw';m=json.loads((O/'collection_manifest.json').read_text(encoding='utf8'));s=requests.Session()
u='https://mods.go.kr/board.es?act=view&bid=203&list_no=437767&mid=a10301010000';h=s.get(u,timeout=45);h.raise_for_status()
for p,t in re.findall(r'<a class="bvf_name" href="([^"]+)">([^<]+)</a>',h.text):
 if t.endswith(('.xls','.xlsx')):
  r=s.get(urljoin(u,p),timeout=60);r.raise_for_status();name='census_2024'+Path(t).suffix;(D/name).write_bytes(r.content);m.append(dict(name=name,original_name=t,source_page=u,url=urljoin(u,p),status='downloaded',bytes=len(r.content),sha256=hashlib.sha256(r.content).hexdigest()));print(name,len(r.content))
(O/'collection_manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf8')
