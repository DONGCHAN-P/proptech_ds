const reportData=JSON.parse(document.getElementById('report-data').textContent);
const chart=document.getElementById('main-chart');
const legend=document.getElementById('region-legend');
const readout=document.getElementById('chart-readout');
const viewState={mode:'start',selected:new Set(['서울','경기','인천']),cursor:0};
const lookups=Object.fromEntries(reportData.regions.map(r=>[r,new Map(reportData.paths[r].map(p=>[p.q,p.v]))]));
const modeLabels={start:'2020년 1분기 이후 가격 경로',peak:'지역별 이전 고점까지의 회복',long:'2006년 이후 장기 가격 경로'};
const basisLabels={start:'2020년 1분기 = 100 · 2026년 2분기까지',peak:'지역별 2020~2022년 최고 분기 = 100 · 2020년 이후 표시',long:'2015년 1분기 = 100 · 세종은 2015년 이전 선을 표시하지 않음'};
const groups={metro:['서울','경기','인천'],other:['부산','대구','대전','세종'],all:reportData.regions};
const bounds={left:58,right:878,top:22,bottom:368};
let currentModel;
const fmt=x=>Number(x).toFixed(2);
const quarterName=q=>`${q.slice(0,4)}년 ${q.slice(-1)}분기`;
function quartersFrom(start){
  const out=[];let year=Number(start.slice(0,4)),q=Number(start.slice(-1));
  while(year<2026||(year===2026&&q<=2)){out.push(`${year}Q${q}`);q++;if(q===5){year++;q=1;}}
  return out;
}
function baseQuarter(region){return viewState.mode==='start'?'2020Q1':viewState.mode==='long'?'2015Q1':reportData.summaries[region].peak_quarter;}
function makeModel(){
  const quarters=quartersFrom(viewState.mode==='long'?'2006Q1':'2020Q1');
  const series=reportData.regions.map(region=>{
    const base=lookups[region].get(baseQuarter(region));
    return {region,values:quarters.map(q=>lookups[region].has(q)?lookups[region].get(q)/base*100:null)};
  });
  const maximum=Math.max(...series.flatMap(s=>s.values.filter(v=>v!==null)));
  const step=viewState.mode==='long'?100:viewState.mode==='peak'?20:50;
  return {quarters,series,max:Math.ceil(maximum/step)*step,step};
}
function coordinates(i,value){
  return [bounds.left+i/(currentModel.quarters.length-1)*(bounds.right-bounds.left),bounds.bottom-value/currentModel.max*(bounds.bottom-bounds.top)];
}
function pathFor(values){
  let fresh=true;const path=[];
  values.forEach((value,i)=>{if(value===null){fresh=true;return;}const [x,y]=coordinates(i,value);path.push(`${fresh?'M':'L'}${x.toFixed(2)},${y.toFixed(2)}`);fresh=false;});
  return path.join(' ');
}
function updateCursor(index,show=true){
  viewState.cursor=Math.max(0,Math.min(currentModel.quarters.length-1,index));
  const i=viewState.cursor,q=currentModel.quarters[i];
  const selected=currentModel.series.filter(s=>viewState.selected.has(s.region));
  if(!selected.length){readout.textContent='지역을 하나 이상 선택해 주세요.';return;}
  readout.innerHTML=`<strong>${quarterName(q)}</strong>`+selected.map(s=>`<span class="readout-value" style="--series:${reportData.colors[s.region]}"><i></i>${s.region} ${s.values[i]===null?'관측 경로 없음':fmt(s.values[i])}</span>`).join('');
  const old=chart.querySelector('#cursor-layer');if(old)old.remove();
  if(!show)return;
  const x=coordinates(i,0)[0];
  const dots=selected.filter(s=>s.values[i]!==null).map(s=>{const [cx,cy]=coordinates(i,s.values[i]);return `<circle cx="${cx}" cy="${cy}" r="4.5" fill="${reportData.colors[s.region]}" stroke="#fffefa" stroke-width="2"/>`;}).join('');
  chart.insertAdjacentHTML('beforeend',`<g id="cursor-layer" pointer-events="none"><line x1="${x}" x2="${x}" y1="${bounds.top}" y2="${bounds.bottom}" stroke="#8496a1" stroke-dasharray="3 4"/>${dots}</g>`);
}
function render(){
  currentModel=makeModel();
  let svg='';
  for(let value=0;value<=currentModel.max;value+=currentModel.step){
    const y=coordinates(0,value)[1];
    svg+=`<line x1="${bounds.left}" x2="${bounds.right}" y1="${y}" y2="${y}" stroke="${value===100?'#8a99a2':'#dce2e2'}" ${value===100?'stroke-dasharray="5 5"':''}/><text x="${bounds.left-12}" y="${y+5}" fill="#536875" font-size="14" text-anchor="end">${value}</text>`;
  }
  if(currentModel.step===100){const y=coordinates(0,100)[1];svg+=`<line x1="${bounds.left}" x2="${bounds.right}" y1="${y}" y2="${y}" stroke="#8a99a2" stroke-dasharray="5 5"/>`;}
  currentModel.quarters.forEach((q,i)=>{
    const last=i===currentModel.quarters.length-1;
    const yearly=q.endsWith('Q1')&&q.slice(0,4)!=='2026';
    const longTick=Number(q.slice(0,4))%4===2;
    if(!last&&(!yearly||(viewState.mode==='long'&&!longTick)))return;
    const x=coordinates(i,0)[0];
    svg+=`<text x="${x}" y="${bounds.bottom+28}" fill="#536875" font-size="14" text-anchor="${last?'end':'middle'}">${last?'2026 Q2':q.slice(0,4)}</text>`;
  });
  const selected=currentModel.series.filter(s=>viewState.selected.has(s.region));
  for(const s of selected){
    const color=reportData.colors[s.region];
    svg+=`<path class="price-line" data-region="${s.region}" d="${pathFor(s.values)}" fill="none" stroke="${color}" stroke-width="3.1" stroke-linejoin="round"/>`;
    const [x,y]=coordinates(s.values.length-1,s.values.at(-1));
    svg+=`<circle cx="${x}" cy="${y}" r="3.8" fill="${color}"/>`;
  }
  if(!selected.length)svg+='<text x="450" y="210" text-anchor="middle" fill="#536875" font-size="20">아래 지역 이름을 눌러 선을 선택하세요</text>';
  chart.innerHTML=svg;
  chart.setAttribute('aria-label',`${modeLabels[viewState.mode]}, ${selected.map(s=>s.region).join('·')||'선택된 지역 없음'}, 기준 지수와 전체 지역 공통 세로축 0~${currentModel.max}`);
  document.getElementById('chart-title').textContent=modeLabels[viewState.mode];
  document.getElementById('chart-basis').textContent=`${basisLabels[viewState.mode]} · 세로축 0~${currentModel.max}`;
  document.getElementById('chart-footnote').textContent=viewState.mode==='peak'?'고점 분기는 지역마다 다릅니다. 지수 100 이상은 해당 표본의 이전 고점 이상이라는 뜻입니다. 지속 회복을 보장하지 않습니다.':'모든 지역을 기준 시점 100으로 환산했습니다. 이 지수는 가격 변화의 경로이며 실제 주택 가격 수준이나 투자수익률이 아닙니다.';
  document.querySelectorAll('[data-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.mode===viewState.mode)));
  document.querySelectorAll('[data-group]').forEach(b=>{const g=groups[b.dataset.group];b.setAttribute('aria-pressed',String(g.length===viewState.selected.size&&g.every(r=>viewState.selected.has(r))));});
  legend.querySelectorAll('[data-region]').forEach(b=>b.setAttribute('aria-pressed',String(viewState.selected.has(b.dataset.region))));
  updateCursor(currentModel.quarters.length-1,false);
}
reportData.regions.forEach(region=>{
  const b=document.createElement('button');b.type='button';b.dataset.region=region;b.style.setProperty('--series',reportData.colors[region]);
  b.setAttribute('aria-pressed',String(viewState.selected.has(region)));b.innerHTML=`<span class="swatch"></span>${region}`;
  b.addEventListener('click',()=>{viewState.selected.has(region)?viewState.selected.delete(region):viewState.selected.add(region);render();});legend.append(b);
});
document.querySelectorAll('[data-mode]').forEach(b=>b.addEventListener('click',()=>{viewState.mode=b.dataset.mode;render();}));
document.querySelectorAll('[data-group]').forEach(b=>b.addEventListener('click',()=>{viewState.selected=new Set(groups[b.dataset.group]);render();}));
chart.addEventListener('pointermove',event=>{
  const box=chart.getBoundingClientRect();const x=(event.clientX-box.left)/box.width*900;
  const y=(event.clientY-box.top)/box.height*430;
  if(y<bounds.top||y>bounds.bottom)return;
  updateCursor(Math.round((x-bounds.left)/(bounds.right-bounds.left)*(currentModel.quarters.length-1)));
});
chart.addEventListener('pointerleave',()=>{const node=chart.querySelector('#cursor-layer');if(node)node.remove();});
chart.setAttribute('tabindex','0');chart.setAttribute('aria-describedby','chart-readout');
chart.addEventListener('keydown',event=>{if(event.key==='ArrowLeft'||event.key==='ArrowRight'){event.preventDefault();updateCursor(viewState.cursor+(event.key==='ArrowLeft'?-1:1));}});
document.getElementById('download-csv').addEventListener('click',()=>{
  const blob=new Blob(['\ufeff'+downloadableCSV],{type:'text/csv;charset=utf-8'}),url=URL.createObjectURL(blob),a=document.createElement('a');
  a.href=url;a.download='지역별_상승률_계산표.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
});
document.getElementById('print-report').addEventListener('click',()=>window.print());
render();
