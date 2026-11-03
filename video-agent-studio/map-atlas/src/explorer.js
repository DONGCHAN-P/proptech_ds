// Public screenshot-inspired exploration, using only our official datasets.
let complexHits=[];
function drawComplexLabels(){
 complexHits=[];if(planView)return;if(!el('complex-labels').checked||view.s<.035)return;
 const occupied=[];ctx.save();ctx.font='bold 12px Malgun Gothic';ctx.textAlign='center';
 for(const i of filtered){const a=items[i],[x,y]=xy(...a.xy);if(x<(W<=850?20:390)||x>W-40||y<45||y>H-100)continue;if(occupied.some(p=>Math.abs(x-p[0])<135&&Math.abs(y-p[1])<55))continue;occupied.push([x,y]);
  let name=a.name.length>12?a.name.slice(0,11)+'…':a.name;const w=Math.max(85,ctx.measureText(name).width+20);ctx.fillStyle=i===selected?'#2848ac':'#6655d9';ctx.fillRect(x-w/2,y-35,w,38);ctx.beginPath();ctx.moveTo(x-5,y+3);ctx.lineTo(x,y+10);ctx.lineTo(x+5,y+3);ctx.fill();ctx.fillStyle='#fff';ctx.fillText(name,x,y-19);ctx.font='11px Malgun Gothic';ctx.fillText(a.homes+'세대',x,y-5);ctx.font='bold 12px Malgun Gothic';complexHits.push({i,x,y,w});
 }ctx.restore();
}
function hitComplexLabel(x,y){const [sx,sy]=xy(x,y),p=complexHits.find(p=>sx>p.x-p.w/2&&sx<p.x+p.w/2&&sy>p.y-35&&sy<p.y+10);if(!p)return false;select(p.i);return true}
function nearbyDetails(a){
 const nearest=(rows)=>rows.map(s=>({...s,d:Math.hypot(s.xy[0]-a.xy[0],s.xy[1]-a.xy[1])})).sort((x,y)=>x.d-y.d);
 const schools=nearest(DATA.education?.schools||[]).slice(0,3),seen=new Set;
 const stations=nearest(DATA.transit?.stations||[]).filter(s=>{if(seen.has(s.name))return false;seen.add(s.name);return true}).slice(0,3);
 const rows=(xs,kind)=>xs.map(s=>`<button class="nearby" data-${kind}="${esc(s.id)}"><b>${esc(s.name)}${kind==='station'&&!s.name.endsWith('역')?'역':''}</b><small>${esc(s.grade||s.line)} · 직선 ${Math.round(s.d).toLocaleString()}m</small></button>`).join('');
 return `<section><h3>주변 학교·교통</h3><p class="muted">단지 대표 좌표 기준 직선거리 · 배정학교 및 도보시간 아님</p>${rows(schools,'school')}${rows(stations,'station')}</section>`;
}
function initExplorer(){
 el('back-to-list').onclick=()=>{document.body.classList.remove('detail-open','show-detail');if(innerWidth<=850)document.body.classList.add('show-search')};
 el('reset').addEventListener('click',()=>document.body.classList.remove('detail-open')); 
 el('complex-labels').onchange=draw;
 el('zoom-in').onclick=()=>{view.s=Math.min(3,view.s*1.6);draw()};el('zoom-out').onclick=()=>{view.s=Math.max(.0007,view.s/1.6);draw()};
 el('details').addEventListener('click',e=>{let b=e.target.closest('[data-school],[data-station]');if(!b)return;if(b.dataset.school)showSchool(b.dataset.school);else showStation(b.dataset.station)});
 el('viewport-list').onclick=()=>{const visible=filtered.filter(i=>{const [x,y]=xy(...items[i].xy);return x>330&&x<W-30&&y>20&&y<H-90});el('found').textContent=`현재 지도 ${visible.length.toLocaleString()}개 · 최대 80개`;el('results').innerHTML=visible.slice(0,80).map(i=>`<div class="result" role="button" tabindex="0" data-i="${i}"><b>${esc(items[i].name)}</b><br><small>${esc(items[i].addr)}</small></div>`).join('')||'<div class="empty">지도를 이동하거나 축소하세요.</div>'};
}
