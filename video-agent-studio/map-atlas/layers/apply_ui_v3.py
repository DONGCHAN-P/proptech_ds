from pathlib import Path
import shutil
H=Path(__file__).resolve().parents[1];ROOT=H.parents[1]
b=H/'versions/v3-before-rea-ui'
if not b.exists():
 b.mkdir(parents=True);shutil.copytree(H/'src',b/'src');shutil.copy2(H/'index.html',b/'index.html');shutil.copy2(H/'build.py',b/'build.py')
p=H/'src/app.js';s=p.read_text(encoding='utf8')
s=s.replace("ctx.fillRect(0,0,W,H);ctx.save();", "ctx.fillRect(0,0,W,H);const hasBasemap=drawBasemap();ctx.save();")
s=s.replace("ctx.fill(path,'evenodd');ctx.stroke(path)","if(!hasBasemap)ctx.fill(path,'evenodd');ctx.stroke(path)")
s=s.replace("ctx.fillStyle=i===selected?'#ebae43':'#286cda';ctx.globalAlpha=i===selected?.95:.65;", "ctx.fillStyle=i===selected?'#7160df':'#8998b5';ctx.globalAlpha=i===selected?.5:hasBasemap?.12:.24;")
s=s.replace("el('details').innerHTML+=nearbyDetails(a);",'')
s=s.replace('initEducation();initTransit();initExplorer();','initEducation();initTransit();initExplorer();initPolishedUI();')
p.write_text(s,encoding='utf8')
p=H/'build.py';s=p.read_text(encoding='utf8').replace("HERE/'src/index.template.html'","HERE/'src/explorer.template.html'").replace("HERE/'src/styles.css'","HERE/'src/explorer-v3.css'")
needle="js=(HERE/'src/explorer.js')"
s=s.replace(needle,"js=(HERE/'vendor/proj4.js').read_text(encoding='utf8')+'\\n'+(HERE/'src/basemap.js').read_text(encoding='utf8')+'\\n'+(HERE/'src/ui-v3.js').read_text(encoding='utf8')+'\\n'+(HERE/'src/explorer.js')")
p.write_text(s,encoding='utf8')
(H/'vendor').mkdir(exist_ok=True)
shutil.copy2(ROOT/'tools/map-ui/node_modules/proj4/dist/proj4.js',H/'vendor/proj4.js')
shutil.copy2(ROOT/'tools/map-ui/node_modules/proj4/LICENSE.md',H/'vendor/proj4-LICENSE.md')
