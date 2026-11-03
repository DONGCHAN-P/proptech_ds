from pathlib import Path
import subprocess,json,re
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
chrome=ROOT/'video/node_modules/.remotion/chrome-headless-shell/win64/chrome-headless-shell-win64/chrome-headless-shell.exe'
test='''<script>let timer=setInterval(()=>{if(!window.ATLAS)return;clearInterval(timer);let r={schools_loaded:false,school_markers:false,school_toggle:false,zones:false,school_detail:false};try{r.schools_loaded=ATLAS.data.education.schools.length===4439;document.getElementById('search').value='반포자이';document.getElementById('search').dispatchEvent(new Event('input'));document.querySelector('[data-i]').click();r.school_markers=ATLAS.educationStats().schools>0;document.getElementById('education-schools').click();r.school_toggle=ATLAS.educationStats().schools===0;document.getElementById('education-schools').click();document.getElementById('education-zones').click();r.zones=ATLAS.educationStats().zones>0;ATLAS.showSchool(ATLAS.data.education.schools[0].id);r.school_detail=document.getElementById('details').textContent.includes('학교ID')}catch(e){r.error=e.message}let p=document.createElement('pre');p.id='education-test';p.textContent=JSON.stringify(r);document.body.append(p)},100)</script>'''
temporary=HERE/'education_test_runtime.html'
temporary.write_text((HERE/'index.html').read_text(encoding='utf8').replace('</html>',test+'</html>'),encoding='utf8')
try:
    p=subprocess.run([str(chrome),'--headless','--no-sandbox','--disable-gpu','--dump-dom',f'--screenshot={HERE / "layers/education_preview.png"}','--window-size=1440,1000','--virtual-time-budget=20000',temporary.as_uri()],capture_output=True,timeout=60)
    m=re.search(r'<pre id="education-test">(.*?)</pre>',p.stdout.decode('utf8',errors='replace'),re.S)
    result=json.loads(m[1]) if m else {'error':'No browser result','exit':p.returncode}
    (HERE/'layers/education_ui_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(result,ensure_ascii=False))
    assert all(result.get(k) for k in ['schools_loaded','school_markers','school_toggle','zones','school_detail'])
finally:temporary.unlink(missing_ok=True)
