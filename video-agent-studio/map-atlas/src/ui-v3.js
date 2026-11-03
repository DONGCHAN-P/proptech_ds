function renderComplexDetail(a){
 const schools=(DATA.education?.schools||[]).map(s=>({...s,d:Math.hypot(s.xy[0]-a.xy[0],s.xy[1]-a.xy[1])})).sort((a,b)=>a.d-b.d);
 const station=(DATA.transit?.stations||[]).map(s=>({...s,d:Math.hypot(s.xy[0]-a.xy[0],s.xy[1]-a.xy[1])})).sort((a,b)=>a.d-b.d)[0];
 const approved=a.approved?.replace(/^(\d{4})(\d{2})(\d{2})$/,'$1.$2.$3')||'자료 없음';
 const legacy=el('details').innerHTML;
 el('details').innerHTML=`<p class="detail-address">${esc(a.addr)}</p><div class="summary-grid"><div><small>세대수</small><strong>${esc(a.homes)}<em>세대</em></strong></div><div><small>동수</small><strong>${esc(a.dongs)}<em>개동</em></strong></div><div><small>사용승인</small><strong class="date-value">${esc(approved)}</strong></div></div><nav class="detail-nav"><a href="#overview-section">기본정보</a><a href="#nearby-section">학교·교통</a><a href="#source-section">자료 출처</a></nav><section id="overview-section" class="detail-section"><div class="section-heading"><h3>이 단지 한눈에</h3><span>공식 자료</span></div><div class="insight"><span class="insight-icon">◉</span><div><b>${station?esc(stationTitle(station.name)):'인근 역 자료 없음'}</b><p>${station?'대표 좌표 기준 직선 '+Math.round(station.d).toLocaleString()+'m':'수록된 역 좌표를 기준으로 확인합니다.'}</p></div></div><div class="insight"><span class="insight-icon school">▣</span><div><b>${schools[0]?esc(schools[0].name):'인근 학교 자료 없음'}</b><p>${schools[0]?'직선 '+Math.round(schools[0].d).toLocaleString()+'m · '+esc(schools[0].grade):''}</p></div></div><p class="distance-note">직선거리는 도보거리·시간 및 배정학교를 뜻하지 않습니다.</p></section><section id="nearby-section" class="detail-section">${nearbyDetails(a)}</section><section id="source-section" class="detail-section"><h3>공식 단지·보조 자료</h3><details><summary>주소·단지번호·상권·경사도 상세 보기</summary>${legacy}</details><p class="distance-note">단지 2025 · 학교 2026.10 · 학구도 2026.09 · 역 자료 묶음 2026.06 (행별 시점 다름)</p></section>`;
 el('right').scrollTop=0;
}
function initPolishedUI(){
 for(const b of document.querySelectorAll('[data-layer]')){const input=el(b.dataset.layer);const sync=()=>{b.classList.toggle('active',input.checked);b.setAttribute('aria-pressed',String(input.checked))};b.onclick=()=>{input.click();sync()};input.addEventListener('change',sync);sync()}
 el('advanced-toggle').onclick=()=>{const p=el('advanced-filters');p.hidden=!p.hidden;el('advanced-toggle').setAttribute('aria-expanded',String(!p.hidden))};
 el('clear-search').onclick=()=>{el('search').value='';filter();el('search').focus()};
 const original=select;select=(i,fly=false)=>{original(i,fly);if(i!==null)renderComplexDetail(items[i])};window.ATLAS.select=select;
 el('results').addEventListener('keydown',e=>{if(e.key==='Escape')el('search').focus()});
 el('basemap').addEventListener('change',draw);
 if(location.protocol==='file:'){el('basemap').disabled=true;el('basemap-note').textContent='도로 배경은 웹 주소로 열면 사용할 수 있습니다.'}
}
