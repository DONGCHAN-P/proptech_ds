from pathlib import Path
import urllib.request,json,re
P=Path(__file__).parent
for name,url in [('wherehome','https://wherehome.lh.or.kr/'),('data15123973','https://www.data.go.kr/data/15123973/openapi.do'),('s5site','https://gycr-s5.co.kr/')]:
 try:
  b=urllib.request.urlopen(url,timeout=25).read();(P/'raw'/f'{name}.html').write_bytes(b)
  print(name,len(b),re.findall(r'<script[^>]+src=[\"\x27]([^\"\x27]+)',b.decode('utf8','ignore'))[-15:])
 except Exception as e:print(name,str(e))
for line in Path('.env').read_text(encoding='utf8').splitlines():
 if '=' in line and any(t in line.split('=')[0].upper() for t in ['VWORLD','GEO','MAP','DATA']): print('ENV_NAME_ONLY',line.split('=')[0])
