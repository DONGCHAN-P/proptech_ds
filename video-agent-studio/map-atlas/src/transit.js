function stationTitle(name){return name.endsWith('역')?name:name+'역'}
let transitHits=[],transitCount=0;
function drawTransit(){
 transitHits=[];transitCount=0;
 if(!DATA.transit||!el('transit-stations').checked||view.s<.004)return;
 drawRailRoutes();const line=el('transit-line').value,region=el('region').value,occupied=[];
 ctx.save();ctx.font='bold 12px Malgun Gothic';ctx.textAlign='left';
 for(const s of DATA.transit.stations){
  if(line&&s.line!==line)continue;
  if(region&&!s.address.startsWith({'11':'서울특별시','28':'인천광역시','41':'경기도'}[region]))continue;
  const [x,y]=xy(...s.xy);if(x<0||x>W||y<0||y>H)continue;
  ctx.fillStyle='#fffefa';ctx.strokeStyle=railColor(s.line);ctx.lineWidth=2;ctx.beginPath();ctx.arc(x,y,5,0,Math.PI*2);ctx.fill();ctx.stroke();transitHits.push({x,y,s});transitCount++;
  if(view.s>=.025&&!occupied.some(p=>Math.abs(x-p[0])<90&&Math.abs(y-p[1])<22)){occupied.push([x,y]);ctx.lineWidth=4;ctx.strokeStyle='#fffefa';ctx.strokeText(stationTitle(s.name),x+8,y+15);ctx.fillStyle='#173348';ctx.fillText(stationTitle(s.name),x+8,y+15)}
 }
 ctx.restore();
}
function showStation(id){
 document.body.classList.add('detail-open');
 const s=DATA.transit.stations.find(s=>s.id===id);if(!s)return;
 view.x=s.xy[0];view.y=s.xy[1];view.s=Math.max(view.s,.08);selected=null;
 const near=DATA.transit.stations.filter(t=>t.name===s.name&&Math.hypot(t.xy[0]-s.xy[0],t.xy[1]-s.xy[1])<700);
 el('title').textContent=stationTitle(s.name);el('details').innerHTML=`<dl><dt>수록 노선</dt><dd>${esc([...new Set(near.map(t=>t.line))].join(' · '))}</dd><dt>주소</dt><dd>${esc(s.address)}</dd><dt>운영기관</dt><dd>${esc(s.operator)}</dd><dt>행 기준일</dt><dd>${esc(s.date)}</dd></dl><p>공식 역 좌표입니다. 출입구 위치와 다르며, 도보 경로·실제 선로·계획역은 포함하지 않았습니다.</p><p>2026.06.30 묶음 파일이지만 행별 기준일과 수록 범위가 다릅니다. 미수록 역이 있을 수 있습니다.</p>`;
 if(innerWidth<=850){document.body.classList.remove('show-search');document.body.classList.add('show-detail')}draw();
}
function hitTransit(x,y){const [sx,sy]=xy(x,y),p=transitHits.find(p=>Math.hypot(sx-p.x,sy-p.y)<=9);if(!p)return false;showStation(p.s.id);return true}
function initTransit(){if(!DATA.transit)return;for(const line of [...new Set(DATA.transit.stations.map(s=>s.line))].sort()){const o=document.createElement('option');o.value=o.textContent=line;el('transit-line').append(o)}for(const id of ['transit-stations','transit-line'])el(id).addEventListener('change',draw)}
