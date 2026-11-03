"""Cache current primary newborn-loan pages; print only public-source metadata."""
import hashlib
import json
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

OUT=Path(__file__).parent/'evidence/director-newborn-v1'
OUT.mkdir(parents=True,exist_ok=True)
urls={
 'KB':'https://obank.kbstar.com/quics?cc=b032425:b033525&page=C020709&prcode=LN40001049',
 'NHUF':'https://nhuf.molit.go.kr/FP/FP05/FP0503/FP05030801.jsp',
}
def fetch(item):
    name,url=item
    p=OUT/(name+'.html')
    assert not p.exists(),'Preserve cached primary-source evidence.'
    try:
        request=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(request,timeout=20) as response:body=response.read()
        p.write_bytes(body)
        text=body.decode('utf-8',errors='replace')
        return {'source_id':name,'url':url,'file':str(p),'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest(),
                'has_reset_075':bool(re.search(r'0\.75',text)),'retrieved_at_utc':datetime.now(timezone.utc).isoformat()}
    except Exception as exc:
        return {'source_id':name,'url':url,'error_type':type(exc).__name__}
with ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(fetch,urls.items()))
(OUT/'receipt.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(rows,ensure_ascii=False))
