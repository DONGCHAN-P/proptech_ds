from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from functools import partial
import subprocess,threading,json,re,html
H=Path(__file__).resolve().parent
chrome=H.parents[1]/'video/node_modules/.remotion/chrome-headless-shell/win64/chrome-headless-shell-win64/chrome-headless-shell.exe'
test='''<script>let timer=setInterval(()=>{if(!window.ATLAS)return;clearInterval(timer);const r={};try{document.getElementById('toggle-search').click();const q=document.getElementById('search');q.value='반포자이';q.dispatchEvent(new Event('input'));document.querySelector('[data-i]').click();r.summary=!!document.querySelector('.summary-grid');r.facilities=document.querySelectorAll('.nearby').length===6;r.detail_visible=getComputedStyle(document.getElementById('right')).display==='block';r.no_horizontal_overflow=document.documentElement.scrollWidth<=innerWidth;r.sections=!!document.querySelector('#nearby-section');r.projection=Math.abs(proj4('EPSG:4326','+proj=tmerc +lat_0=38 +lon_0=127.5 +k=0.9996 +x_0=1000000 +y_0=2000000 +ellps=GRS80 +units=m',[127.5,38])[0]-1000000)<.001;CONFIG.tileUrl='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aWV8AAAAASUVORK5CYII=';document.getElementById('basemap').click();r.tile_geometry=tileCache.size>0&&tileCache.size<=90;document.getElementById('basemap').click();document.getElementById('back-to-list').click();document.querySelector('[data-layer="education-schools"]').click();r.layer_sync=!document.getElementById('education-schools').checked&&!document.querySelector('[data-layer="education-schools"]').classList.contains('active');document.querySelector('[data-layer="education-schools"]').click();document.querySelector('[data-i]').click()}catch(e){r.error=e.message}const p=document.createElement('pre');p.id='qa-v3';p.textContent=JSON.stringify(r);document.body.append(p)},100)</script>'''
p=H/'web/ui_v3_runtime.html';p.write_text((H/'web/index.html').read_text(encoding='utf8').replace('</html>',test+'</html>'),encoding='utf8')
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(H/'web')));threading.Thread(target=server.serve_forever,daemon=True).start()
results={}
try:
 for kind,size in [('desktop','1440,1000'),('mobile','390,844')]:
  proc=subprocess.run([str(chrome),'--headless','--no-sandbox','--disable-gpu','--dump-dom',f'--screenshot={H/ ("ui_v3_"+kind+".png")}',f'--window-size={size}','--virtual-time-budget=15000',f'http://127.0.0.1:{server.server_port}/ui_v3_runtime.html'],capture_output=True,timeout=45)
  m=re.search(r'<pre id="qa-v3">(.*?)</pre>',proc.stdout.decode('utf8',errors='replace'),re.S);r=json.loads(html.unescape(m[1])) if m else {'error':'missing result'};results[kind]=r
 (H/'ui_v3_validation.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(results));assert all(all(r.get(k) for k in ['summary','facilities','detail_visible','no_horizontal_overflow','sections','projection','tile_geometry','layer_sync']) for r in results.values())
finally:server.shutdown();server.server_close();p.unlink(missing_ok=True)
