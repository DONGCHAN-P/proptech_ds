from pathlib import Path
import subprocess,json,re
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
chrome=ROOT/'video/node_modules/.remotion/chrome-headless-shell/win64/chrome-headless-shell-win64/chrome-headless-shell.exe'
test='''<script>let t=setInterval(()=>{if(!window.ATLAS)return;clearInterval(t);let r={};try{r.loaded=ATLAS.data.transit.stations.length===683;let s=ATLAS.data.transit.stations.find(s=>s.name==='강남');ATLAS.showStation(s.id);r.detail=document.getElementById('title').textContent==='강남역';r.markers=ATLAS.transitStats()>0;document.getElementById('transit-stations').click();r.toggle=ATLAS.transitStats()===0;document.getElementById('transit-stations').click();let l=document.getElementById('transit-line');l.value=s.line;l.dispatchEvent(new Event('change'));r.line_filter=l.value===s.line&&ATLAS.transitStats()>0;r.korean=document.getElementById('transit-stations').parentElement.textContent.includes('철도역')}catch(e){r.error=e.message}let p=document.createElement('pre');p.id='transit-test';p.textContent=JSON.stringify(r);document.body.append(p)},100)</script>'''
p=HERE/'transit_test_runtime.html';p.write_text((HERE/'index.html').read_text(encoding='utf8').replace('</html>',test+'</html>'),encoding='utf8')
try:
 r=subprocess.run([str(chrome),'--headless','--no-sandbox','--disable-gpu','--dump-dom',f'--screenshot={HERE / "layers/transit_preview.png"}','--window-size=1440,1000','--virtual-time-budget=20000',p.as_uri()],capture_output=True,timeout=60)
 m=re.search(r'<pre id="transit-test">(.*?)</pre>',r.stdout.decode('utf8',errors='replace'),re.S)
 result=json.loads(m[1]) if m else {'error':'No browser result'}
 (HERE/'layers/transit_ui_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(result));assert all(result.get(k) for k in ['loaded','detail','markers','toggle','line_filter','korean'])
finally:p.unlink(missing_ok=True)
