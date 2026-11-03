from pathlib import Path
import subprocess,json,re
H=Path(__file__).resolve().parent
chrome=H.parents[1]/'video/node_modules/.remotion/chrome-headless-shell/win64/chrome-headless-shell-win64/chrome-headless-shell.exe'
js='''<script>let t=setInterval(()=>{if(!window.ATLAS)return;clearInterval(t);let r={};try{let e=document.getElementById('search');e.value='반포자이';e.dispatchEvent(new Event('input'));document.querySelector('[data-i]').click();r.nearby=document.querySelectorAll('.nearby').length===6;r.labels=complexHits.length>0;const before=ATLAS.getView().s;document.getElementById('zoom-in').click();r.zoom=ATLAS.getView().s>before;document.getElementById('viewport-list').click();r.viewport=document.getElementById('found').textContent.includes('현재 지도');document.querySelector('[data-school]').click();r.school_detail=document.getElementById('details').textContent.includes('학교ID');e.value='';e.dispatchEvent(new Event('input'))}catch(e){r.error=e.message}let p=document.createElement('pre');p.id='explorer-test';p.textContent=JSON.stringify(r);document.body.append(p)},100)</script>'''
js=js.replace("r.nearby=document.querySelectorAll('.nearby').length===6;", "r.nearby=document.querySelectorAll('.nearby').length===6;r.detail_panel=getComputedStyle(document.getElementById('right')).display==='block'&&getComputedStyle(document.getElementById('left')).display==='none';document.getElementById('back-to-list').click();r.back=getComputedStyle(document.getElementById('left')).display!=='none';document.querySelector('[data-i]').click();")
p=H/'explorer_runtime.html';p.write_text((H/'index.html').read_text(encoding='utf8').replace('</html>',js+'</html>'),encoding='utf8')
try:
 r=subprocess.run([str(chrome),'--headless','--no-sandbox','--disable-gpu','--dump-dom',f'--screenshot={H/"explorer_preview.png"}','--window-size=1440,1000','--virtual-time-budget=20000',p.as_uri()],capture_output=True,timeout=60)
 m=re.search(r'<pre id="explorer-test">(.*?)</pre>',r.stdout.decode('utf8',errors='replace'),re.S);result=json.loads(m[1]) if m else {'error':'missing result'}
 (H/'explorer_validation.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(result);assert all(result.get(k) for k in ['nearby','labels','zoom','viewport','school_detail','detail_panel','back'])
finally:p.unlink(missing_ok=True)
