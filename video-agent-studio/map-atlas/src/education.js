// Optional official education layers. Coordinates are EPSG:5179 metres.
let eduStats={schools:0,zones:0},eduSelected=null,eduHits=[],eduZonePaths=new Map;
const eduColors={'초등학교':'#9a4dca','중학교':'#188f84','고등학교':'#d17428'};
function educationState(){return {schools:!!el('education-schools')?.checked,zones:!!el('education-zones')?.checked,grade:el('education-grade')?.value||'',zoneKind:el('education-zone-kind')?.value||'elementary_zones'}}
function drawEducation(){
  eduStats={schools:0,zones:0};eduHits=[];
  if(!DATA.education)return;
  const state=educationState(),region=el('region').value;
  const visible=b=>b[2]>=view.x-W/(2*view.s)&&b[0]<=view.x+W/(2*view.s)&&b[3]>=view.y-H/(2*view.s)&&b[1]<=view.y+H/(2*view.s);
  if(state.zones){
    ctx.save();ctx.translate(W/2,H/2);ctx.scale(view.s,view.s);ctx.translate(-view.x,view.y);
    ctx.fillStyle='#9a4dca';ctx.strokeStyle='#7842a0';ctx.lineWidth=1.3/view.s;
    for(const z of DATA.education.zones){
      if(z.kind!==state.zoneKind||(region&&z.area_code!==region)||!visible(z.bbox))continue;
      if(!eduZonePaths.has(z.id))eduZonePaths.set(z.id,geoPath(z.rings));
      const p=eduZonePaths.get(z.id);ctx.globalAlpha=.10;ctx.fill(p,'evenodd');ctx.globalAlpha=.65;ctx.stroke(p);eduStats.zones++;
    }
    ctx.restore();ctx.globalAlpha=1;
  }
  if(state.schools&&view.s>=.012){
    const occupied=[];ctx.font='12px Malgun Gothic';ctx.textAlign='left';
    for(const s of DATA.education.schools){
      if((state.grade&&s.grade!==state.grade)||(region&&!s.office.startsWith({'11':'서울','28':'인천','41':'경기'}[region])))continue;
      const [x,y]=xy(...s.xy);if(x<0||x>W||y<0||y>H)continue;
      ctx.beginPath();ctx.arc(x,y,s.id===eduSelected?7:4,0,Math.PI*2);ctx.fillStyle=eduColors[s.grade]||'#8856a7';ctx.fill();ctx.lineWidth=1;ctx.strokeStyle='#fffefa';ctx.stroke();
      eduHits.push({id:s.id,x,y});eduStats.schools++;
      if((view.s>=.12||s.id===eduSelected)&&!occupied.some(p=>Math.abs(p[0]-x)<100&&Math.abs(p[1]-y)<23)){
        occupied.push([x,y]);ctx.lineWidth=4;ctx.strokeStyle='#fffefa';ctx.strokeText(s.name,x+8,y-7);ctx.fillStyle='#483454';ctx.fillText(s.name,x+8,y-7);
      }
    }
  }
  el('education-status').textContent=`학교 ${DATA.education.schools.length.toLocaleString()}개 · 현재 화면 ${eduStats.schools}개 / 구역 ${eduStats.zones}개${view.s<.012?' · 확대하면 학교 표시':''}`;
}
function showSchool(id){
 document.body.classList.add('detail-open');
  const s=DATA.education?.schools.find(s=>s.id===id);if(!s)return;
  selected=null;eduSelected=id;view.x=s.xy[0];view.y=s.xy[1];view.s=Math.max(view.s,.2);
  el('title').textContent=s.name;
  el('details').innerHTML=`<dl><dt>학교급</dt><dd>${esc(s.grade)}</dd><dt>학교ID</dt><dd>${esc(s.id)}</dd><dt>주소</dt><dd>${esc(s.address)}</dd><dt>운영상태</dt><dd>${esc(s.operation)}</dd><dt>자료 기준일</dt><dd>${esc(s.date)}</dd></dl><p>학교 위치는 한국교육시설안전원 원자료 좌표입니다. 학교 점과 통학구역은 별도 레이어입니다.</p><p class="muted">단지의 배정 학교는 공동통학구역·예외 조건을 포함한 해당 교육청의 안내를 확인해야 합니다.</p>`;
  if(innerWidth<=850){document.body.classList.remove('show-search');document.body.classList.add('show-detail')}
  draw();
}
function hitEducation(x,y){const p=eduHits.find(p=>Math.hypot(xy(x,y)[0]-p.x,xy(x,y)[1]-p.y)<=9);if(!p)return false;showSchool(p.id);return true}
function initEducation(){
  for(const id of ['education-schools','education-zones','education-grade','education-zone-kind'])el(id).addEventListener('change',draw);
  el('reset').addEventListener('click',()=>{eduSelected=null});
}
