from pathlib import Path
import urllib.request,json,hashlib
P=Path(__file__).parent
u='https://apply.lh.or.kr/lhapply/lhFile.do?fileid=60486878'
b=urllib.request.urlopen(u,timeout=25).read()
from PIL import Image
import io
im=Image.open(io.BytesIO(b)); im.verify()
p=P/'raw/s5_landuse_20250131.jpg';p.write_bytes(b)
u2='https://www.xn--3-3u6ey6lv7rsa.kr/attach/EDITOR/IMAGE/2025/7/jnHDyQ3Y0wXxfmoFnOoB.jpg'
b2=urllib.request.urlopen(u2,timeout=25).read();im=Image.open(io.BytesIO(b2));im.verify();p2=P/'raw/transport_plan_202507.jpg';p2.write_bytes(b2)
(P/'map_download_manifest.json').write_text(json.dumps([{'file':str(p),'url':u,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'rights':'연구보존만. 상업영상 재가공 이용허락 미확인'},{'file':str(p2),'url':u2,'sha256':hashlib.sha256(b2).hexdigest(),'bytes':len(b2),'rights':'연구보존만. 상업영상 재가공 이용허락 미확인'}],ensure_ascii=False,indent=2),encoding='utf-8')
print('images verified',len(b),len(b2))
