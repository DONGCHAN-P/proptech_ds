from pathlib import Path
H=Path(__file__).resolve().parents[1]
p=H/'src/overlays.js';s=p.read_text(encoding='utf8')
old="for(const p of r.paths){if(!inView(p.bbox))continue;ctx.lineWidth=6/view.s;ctx.strokeStyle='#ffffffd9';ctx.stroke(p.path);ctx.lineWidth=3.2/view.s;ctx.strokeStyle=r.color;ctx.stroke(p.path);railSegmentCount++}"
new="const visible=r.paths.filter(p=>inView(p.bbox));ctx.lineWidth=6/view.s;ctx.strokeStyle='#ffffffd9';for(const p of visible)ctx.stroke(p.path);ctx.lineWidth=3.2/view.s;ctx.strokeStyle=r.color;for(const p of visible){ctx.stroke(p.path);railSegmentCount++}"
s=s.replace(old,new).replace("function fitPlan(){", "function fitPlan(){el('plan-selection').textContent='지도에서 용지를 클릭하면 이름이 나옵니다.';")
s=s.replace("planView=on;document.body", "planView=on;el('toggle-search').textContent=on?'지구·범례':'검색·필터';document.body")
p.write_text(s,encoding='utf8')
p=H/'src/transit.js';s=p.read_text(encoding='utf8');s="function stationTitle(name){return name.endsWith('역')?name:name+'역'}\n"+s;s=s.replace("s.name+'역'","stationTitle(s.name)");p.write_text(s,encoding='utf8')
p=H/'src/ui-v3.js';s=p.read_text(encoding='utf8').replace("esc(station.name)+'역'","esc(stationTitle(station.name))");p.write_text(s,encoding='utf8')
p=H/'src/explorer.js';s=p.read_text(encoding='utf8').replace("kind==='station'?'역':''","kind==='station'&&!s.name.endsWith('역')?'역':''");p.write_text(s,encoding='utf8')
