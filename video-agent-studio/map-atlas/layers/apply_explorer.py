from pathlib import Path
import shutil
H=Path(__file__).resolve().parents[1]
backup=H/'versions/v2-before-explorer'
if not backup.exists():
 backup.mkdir(parents=True);shutil.copytree(H/'src',backup/'src');shutil.copy2(H/'index.html',backup/'index.html')
p=H/'src/app.js';s=p.read_text(encoding='utf8')
s=s.replace('drawEducation();drawTransit();','drawEducation();drawTransit();drawComplexLabels();')
s=s.replace('if(hitTransit(x,y)||','if(hitComplexLabel(x,y)||hitTransit(x,y)||')
s=s.replace('if(fly){view.x=a.xy[0];',"el('details').innerHTML+=nearbyDetails(a);if(fly){view.x=a.xy[0];")
s=s.replace('initEducation();initTransit();','initEducation();initTransit();initExplorer();')
p.write_text(s,encoding='utf8')
p=H/'build.py';s=p.read_text(encoding='utf8').replace("js=(HERE/'src/transit.js')","js=(HERE/'src/explorer.js').read_text(encoding='utf8')+'\\n'+(HERE/'src/transit.js')");p.write_text(s,encoding='utf8')
p=H/'src/index.template.html';s=p.read_text(encoding='utf8')
s=s.replace('<h1>수도권 단지 지도</h1>','<h1>수도권 단지 지도</h1><span class="chip">단지 · 학교 · 교통</span>')
s=s.replace('<p class="muted" id="found">','<label class="toggle"><input type="checkbox" id="complex-labels" checked> 단지 이름·세대수 말풍선</label><button id="viewport-list">현재 지도에서 단지 찾기</button><p class="muted" id="found">')
s=s.replace('<div id="scale">','<div id="zoom-tools"><button id="zoom-in" aria-label="확대">＋</button><button id="zoom-out" aria-label="축소">−</button></div><div id="scale">')
p.write_text(s,encoding='utf8')
p=H/'src/styles.css';s=p.read_text(encoding='utf8')+'''\n/* Explorer: compact left rail, details only after a selection. */
#left{top:12px;left:12px;bottom:70px;border-radius:10px;background:#fffffff5}#right:has(#details>.note),#right:has(#details>p:first-child:not(.muted)){background:#fffffff5}#zoom-tools{position:fixed;right:350px;bottom:110px;display:grid;gap:3px}#zoom-tools button{font-size:24px;width:42px;height:42px;padding:0;box-shadow:0 2px 8px #17334815}.nearby{display:block;text-align:left;width:100%;margin:6px 0;padding:10px}.nearby small{display:block;margin-top:4px}#viewport-list{width:100%;color:#6655d9;border-color:#d7d1fa}.capture #zoom-tools{display:none}@media(max-width:850px){#zoom-tools{right:12px;bottom:135px}}
''';p.write_text(s,encoding='utf8')
