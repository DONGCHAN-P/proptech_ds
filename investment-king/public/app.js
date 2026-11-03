'use strict';
const $=s=>document.querySelector(s);
const fmt=v=>BigInt(v??0).toLocaleString('ko-KR')+'원';
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const statLabels={financial_knowledge:'금융지식',career_skill:'직무능력',execution:'실행력',health:'건강',relationship:'관계',credit:'신용'};
const icons={PART_TIME:'↗',READ_BOOK:'▤',STUDY_CAREER:'✎',EXERCISE:'✳',SOCIALIZE:'☻',APPLY_JOB:'▣'};
let state=null,actions=[],orders=[],tab='life',busy=false,pending=null,reviewedPlan=null,noticeTimer;
function localGet(key,fallback=null){try{return JSON.parse(localStorage.getItem(key))??fallback;}catch{return fallback;}}
function localSet(key,value){try{localStorage.setItem(key,JSON.stringify(value));}catch{notify('브라우저 저장이 제한되어 있습니다. 회차 주소를 별도로 보관해 주세요.',true);}}
function notify(text,error=false){const n=$('#notice');n.textContent=text;n.classList.toggle('error',error);n.hidden=false;clearTimeout(noticeTimer);noticeTimer=setTimeout(()=>n.hidden=true,error?14000:5000);}
async function api(path,body){
  const response=await fetch(path,{method:body===undefined?'GET':'POST',headers:body===undefined?{}:{'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body)});
  const result=await response.json();if(!response.ok){const e=new Error(result.message??result.error);e.code=result.error;e.status=response.status;throw e;}return result;
}
const runPath=()=>`/api/v1/runs/${state.runId}`;
const plan=()=>({turnIndex:state.turnIndex,stateHash:state.stateHash,actions:[...actions],orders:orders.map(o=>({...o}))});
function chart(values,kind='chart'){
  if(values.length<2)return '<div class="chart-empty">분기를 진행하면 나의 기록이 쌓입니다.</div>';
  const numbers=values.map(Number),min=Math.min(...numbers),max=Math.max(...numbers),span=max-min||1;
  const points=numbers.map((v,i)=>`${(i/(numbers.length-1)*580+10).toFixed(1)},${(130-(v-min)/span*110).toFixed(1)}`).join(' ');
  return `<svg class="${kind}" viewBox="0 0 600 145" preserveAspectRatio="none" role="img" aria-label="현재까지의 변화 그래프"><path d="M10 130 H590" fill="none" stroke="#e0e5d5"/><polyline points="${points}" fill="none" stroke="#538166" stroke-width="${kind==='chart'?2.5:4}" vector-effect="non-scaling-stroke"/></svg>`;
}
function render(){
  $('#welcome').hidden=true;$('#game').hidden=false;
  const done=state.status==='COMPLETED',q=state.quarter;
  $('#quarter').textContent=done?'나의 두 번째 20년':`${q.slice(0,4)}년, ${['겨울','봄','여름','가을'][Number(q.at(-1))-1]}`;
  $('#chapter-info').textContent=`${Math.floor(state.ageYears)}세 ${Math.round(state.ageYears%1*12)}개월 · ${state.employed?'회사원':'무직'} · 가족과 동거 · 정보 기준 ${state.asOfDate}`;
  $('#progress-text').textContent=`${state.turnIndex} / 80 분기 ${done?'· ENDING':''}`;$('#progress').value=state.turnIndex;
  const sc=state.scores;
  $('#metrics').innerHTML=[['지금 쓸 수 있는 현금',fmt(state.cashKRW),state.arrearsKRW!=='0'?`미납 ${fmt(state.arrearsKRW)}`:'새로운 선택의 시작'],['나의 순자산',fmt(sc.netWorthKRW),'현금 + 투자 평가액 − 미납'],['삶의 만족도',`${sc.lifeScore.toFixed(1)} <small>/ 100</small>`,'건강 · 관계 · 자율성 · 행복 · 안정'],['균형 점수',`${sc.balanceScore.toFixed(1)} <small>/ 100</small>`,'자산 50% + 삶 50%']].map(([label,value,note])=>`<div class="metric"><div class="metric-label">${label}</div><div class="metric-value">${value}</div><div class="metric-note">${esc(note)}</div></div>`).join('');
  document.querySelectorAll('[data-tab]').forEach(b=>b.classList.toggle('active',b.dataset.tab===tab));
  const panel=$('#panel');
  panel.innerHTML=(done?ending():'')+({life:lifePanel,market:marketPanel,property:propertyPanel,memory:memoryPanel,records:recordsPanel}[tab])();
  renderQueue();
  if(tab==='records'&&done)loadComparison();
}
function lifePanel(){
  const done=state.status==='COMPLETED';
  return `<div class="section-title"><h2>${done?'어떤 삶을 살았나요?':'이번 계절을 어떻게 보낼까요?'}</h2><p>행동당 1 AP</p></div><div class="action-grid">${state.actions.map(a=>`<button class="action-card" data-action="${a.id}" ${done||a.disabled?'disabled':''}><span class="icon" aria-hidden="true">${icons[a.id]}</span><span><strong>${a.label}</strong><small>${a.description}</small></span><span class="plus" aria-hidden="true">+</span></button>`).join('')}</div>
  <section class="card life-state"><div class="section-title"><h2>지금의 나</h2><span class="pill">스트레스 ${Math.round(state.wellbeing.stress)}</span></div><div class="stat-grid">${Object.entries(statLabels).map(([id,label])=>`<div><div class="stat-head"><span>${label}</span><strong>${Math.round(state.stats[id])}</strong></div><progress value="${state.stats[id]}" max="100" aria-label="${label}"></progress></div>`).join('')}</div><p class="fineprint">${state.employed?`월 순급여 ${fmt(state.salaryKRW)} · 급여는 게임용 가상값입니다.`:'직무능력 30부터 취업 지원이 가능합니다. 공부를 먼저 예약한 뒤 지원할 수 있어요.'}</p></section>
  <section class="card chart-card"><div class="section-title"><h2>나의 자산이 걸어온 길</h2><span class="pill">원화 · MOCK</span></div>${chart(['1000000',...state.history.map(h=>h.netWorthKRW)])}<div class="chart-labels"><span>2006 Q4</span><span>${esc(state.quarter)}</span></div></section>${lastResult()}`;
}
function lastResult(){if(!state.lastTurn)return '';const s=state.history.at(-1);return `<section class="card result"><div class="section-title"><h2>지난 계절의 기록</h2><span class="pill">${esc(s.quarter)}</span></div><p>수입 ${fmt(s.incomeKRW)} · 비용 ${fmt(s.expenseKRW)}</p>${state.lastTurn.orders.map(o=>`<div class="event-line">${esc(o.assetId)} ${o.side==='BUY'?'매수':'매도'} ${esc(o.quantity)} · ${o.status==='FILLED'?`체결 / 수수료 ${fmt(o.feeKRW)}`:`거부 (${esc(o.reason)})`}</div>`).join('')}${state.lastTurn.events.map(e=>`<div class="event-line">${esc(e)}</div>`).join('')||'<p class="muted">꾸준한 일상이 쌓인 한 계절이었습니다.</p>'}</section>`;}
function marketPanel(){
  const enabled=state.market.filter(a=>a.status==='AVAILABLE');
  return `<div class="section-title"><h2>기회를 발견하는 곳</h2><span class="pill">역사 시세 미연결</span></div><p class="muted">A·B·금은 모두 인공적으로 만든 테스트 자산입니다. 실제 종목의 가격이나 수익률을 나타내지 않습니다.</p><div class="market-grid">${state.market.map(a=>`<article class="card asset ${a.status!=='AVAILABLE'?'locked':''}"><div><strong>${esc(a.name)}</strong><small>${a.status==='AVAILABLE'?`수수료 ${Number(a.feeBps)/100}% · ${a.class==='STOCK'?'정수 주':'0.01 단위'}`:a.status==='NOT_LISTED'?'당시 미등장 · 거래 잠김':'접근 시점·시세 검증 필요'}</small></div>${a.status==='AVAILABLE'?chart(a.series.map(p=>p.priceKRW),'sparkline'):'<span class="pill">잠김</span>'}<div class="asset-value">${a.priceKRW?fmt(a.priceKRW):'—'}<small>${a.priceDate??'거래 불가'}</small></div></article>`).join('')}</div>
  ${state.status==='COMPLETED'?'':`<section class="card"><h2 class="section-title">투자 주문 예약</h2><form id="order-form" class="order-form"><label>자산<select id="order-asset">${enabled.map(a=>`<option value="${a.id}">${esc(a.name)}</option>`).join('')}</select></label><label>거래 종류<select id="order-side"><option value="BUY">매수</option><option value="SELL">매도</option></select></label><label>수량<input id="order-quantity" type="text" inputmode="decimal" value="1" required maxlength="24"></label><label>매수 최대 지출액 (수수료 포함)<input id="order-budget" type="text" inputmode="numeric" value="100000" maxlength="18" required></label><p id="order-estimate" class="order-estimate">현재 보이는 가격은 과거 참고가입니다. 체결가가 예약액을 넘으면 매수는 거부됩니다.</p><button class="quiet" type="submit">이번 분기에 주문 예약 +</button></form></section>`}
  <section class="card result"><h2 class="section-title">보유 자산</h2>${state.holdings.length?state.holdings.map(h=>`<div class="event-line">${esc(h.assetId)} · ${esc(h.quantity)} 단위 <strong>${fmt(h.valueKRW)}</strong></div>`).join(''):'<p class="muted">아직 보유한 투자 자산이 없습니다.</p>'}</section>${lastResult()}`;
}
function propertyPanel(){return '<div class="section-title"><h2>내 집이라는 선택</h2><span class="pill">다음 개발 단계</span></div><div class="card result"><p>현재 주거: <strong>가족과 동거</strong></p><p class="muted">부동산 6개 지역 시나리오, 전월세 보증금, 주택담보대출과 잔금 심사는 아직 연결되지 않았습니다. 첫 알파에서는 현금·투자·인생 선택의 기본 루프를 검증합니다.</p><p class="fineprint">실거래 자료와 공개 시점·이용 조건을 확인한 후 구현합니다.</p></div>';}
function memoryPanel(){return `<div class="section-title"><h2>희미하지만, 잊히지 않는 것들</h2><span class="pill">${state.memoryFragments.length} / 5</span></div><p class="muted">기억은 정답을 알려주지 않습니다. 무엇을 할지는 지금의 내가 결정합니다.</p>${state.memoryFragments.map((m,i)=>`<article class="memory-card"><p class="eyebrow">FRAGMENT ${String(i+1).padStart(2,'0')}</p><blockquote>“${esc(m)}”</blockquote></article>`).join('')}<p class="fineprint">역사 뉴스 피드는 아직 미연결입니다. 기억만으로 자산 거래가 해금되지는 않습니다.</p>`;}
function recordsPanel(){return `<div class="section-title"><h2>지나온 계절들</h2><span class="pill">${state.history.length}개의 기록</span></div><div class="history-wrap"><table class="history-table"><thead><tr><th>분기</th><th>수입</th><th>비용</th><th>순자산</th><th>삶</th></tr></thead><tbody>${[...state.history].reverse().map(h=>`<tr><td>${esc(h.quarter)}</td><td>${fmt(h.incomeKRW)}</td><td>${fmt(h.expenseKRW)}</td><td>${fmt(h.netWorthKRW)}</td><td>${h.lifeScore.toFixed(1)}</td></tr>`).join('')}</tbody></table></div>${!state.history.length?'<p class="empty-state">첫 번째 선택을 기다리는 빈 페이지입니다.</p>':''}${state.lastTurn?`<section class="card result"><h2 class="section-title">최근 분기의 현금 원장</h2><p class="fineprint">비현금 자산 변화와 미납은 현금 유출과 구분합니다. 전체 원장은 서버 저장 파일에 보존됩니다.</p>${state.lastTurn.ledger.map(e=>{const debit=e.debits.filter(p=>p.account==='CASH').reduce((n,p)=>n+BigInt(p.amountKRW),0n),credit=e.credits.filter(p=>p.account==='CASH').reduce((n,p)=>n+BigInt(p.amountKRW),0n),amount=debit-credit;return `<div class="event-line">${e.month===0?'분기 시작':`${e.month}개월차`} · ${esc(e.reason)} <strong>${amount>0n?'+':''}${fmt(amount)}</strong></div>`;}).join('')}</section>`:''}<div id="comparison" class="result"></div>`;}
function ending(){const s=state.scores;return `<section class="ending"><p class="eyebrow">2026.10.01 · YOUR SECOND LIFE</p><h2>돈 너머에 남은,<br>나만의 스무 해.</h2><div class="score-row"><div><small>자산 점수</small><strong>${s.wealthScore.toFixed(1)}</strong></div><div><small>삶의 점수</small><strong>${s.lifeScore.toFixed(1)}</strong></div><div><small>자유 지수</small><strong>${s.freedomIndex.toFixed(1)}</strong></div></div><p>최종 순자산 ${fmt(s.netWorthKRW)}<br>경제적 성공과 삶의 만족, 두 기록을 함께 남깁니다. MOCK 데이터로 플레이한 결과입니다.</p><button id="share-card" class="primary">나의 인생 카드 저장 ↓</button></section>`;}
async function loadComparison(){const target=$('#comparison');if(!target)return;const ids=localGet('ik-run-ids',[]).filter(id=>id!==state.runId).slice(-5);const results=await Promise.allSettled(ids.map(id=>api(`/api/v1/runs/${id}/ending`)));if(!target.isConnected)return;const runs=results.filter(r=>r.status==='fulfilled').map(r=>r.value);target.innerHTML=`<h2 class="section-title">이전 인생과 비교</h2>${runs.length?runs.map(r=>`<div class="event-line">이전 회차 · 순자산 ${fmt(r.scores.netWorthKRW)} · 삶 ${r.scores.lifeScore.toFixed(1)} · 균형 ${r.scores.balanceScore.toFixed(1)}</div>`).join(''):'<p class="muted">완료한 이전 회차가 없습니다.</p>'}<p class="fineprint">회차마다 시드와 선택이 다를 수 있습니다. 동일 조건의 성과 비교로 해석하지 마세요.</p>`;}
function renderQueue(){
  const done=state.status==='COMPLETED';$('#ap-badge').textContent=`${3-actions.length} / 3 AP`;
  $('#action-queue').innerHTML=Array.from({length:3},(_,i)=>actions[i]?`<li>${esc(state.actions.find(a=>a.id===actions[i]).label)}<button class="remove" data-remove-action="${i}" aria-label="${i+1}번째 행동 취소">×</button></li>`:`<li class="empty">아직 정하지 않은 시간</li>`).join('');
  $('#order-queue').innerHTML=orders.map((o,i)=>`<div class="order-line">${esc(o.assetId)} ${o.side==='BUY'?'매수':'매도'} ${esc(o.quantity)}<button class="remove" data-remove-order="${i}" aria-label="주문 취소">×</button>${o.side==='BUY'?`<br>예약 ${fmt(o.maxSpendKRW)}`:''}</div>`).join('');
  $('#advance').textContent=done?'여든 번의 선택이 끝났습니다':pending?'미확인 정산 다시 확인 →':'다음 3개월 →';$('#advance').disabled=done||busy;
  document.querySelectorAll('[data-action]').forEach(b=>{const id=b.dataset.action;b.disabled=done||busy||!!pending||actions.length>=3||actions.filter(a=>a===id).length>=2||state.actions.find(a=>a.id===id).disabled;});
}
async function refresh(){state=await api(runPath());actions=[];orders=[];render();}
async function advance(){
  if(busy)return;if(pending){await settle();return;}
  busy=true;renderQueue();const snapshot=plan(),id=state.runId;
  try{
    const result=await api(runPath()+'/preview',snapshot);
    if(state.runId!==id||state.stateHash!==snapshot.stateHash)return;
    reviewedPlan=snapshot;
    $('#preview-content').innerHTML=`<div class="preview-row"><span>선택한 행동</span><strong>${snapshot.actions.length} / 3</strong></div><div class="preview-row"><span>행동 비용</span><strong>${fmt(result.actionCostKRW)}</strong></div><div class="preview-row"><span>행동 비용 + 매수 예약</span><strong>${fmt(result.reservedCashKRW)}</strong></div><div class="preview-row"><span>별도 필요한 기본 생활비</span><strong>${fmt(result.livingCostKRW)}</strong></div>${result.warning?`<p class="warning">${esc(result.warning)}</p>`:''}<p class="muted">${snapshot.actions.length?'선택한 순서대로 행동합니다.':'아무 행동 없이도 분기를 진행할 수 있습니다.'}</p>`;
    $('#confirm-dialog').showModal();
  }catch(e){notify(e.message,true);}finally{busy=false;renderQueue();}
}
async function settle(){
  if(busy)return;busy=true;
  if(!pending){if(!reviewedPlan){busy=false;return;}pending={...reviewedPlan,idempotencyKey:crypto.randomUUID()};localSet(`ik-pending-${state.runId}`,pending);reviewedPlan=null;}
  $('#confirm-dialog').close();renderQueue();
  try{await api(runPath()+'/commit',pending);localSet(`ik-pending-${state.runId}`,null);pending=null;await refresh();notify(state.status==='COMPLETED'?'나의 두 번째 20년이 완성되었습니다.':'다음 계절로 왔습니다. 이 PC에 저장했습니다.');}
  catch(e){if(e.status&&e.status<500){localSet(`ik-pending-${state.runId}`,null);pending=null;if(e.status===409){try{await refresh();}catch{}}}notify(e.message+(pending?' 같은 요청으로 다시 확인할 수 있습니다.':''),true);}
  finally{busy=false;renderQueue();}
}
document.addEventListener('click',async e=>{
  const button=e.target.closest('button');if(!button)return;
  if(button.dataset.tab){tab=button.dataset.tab;render();}
  if(button.dataset.action&&!busy&&!pending){actions.push(button.dataset.action);renderQueue();}
  if(button.dataset.removeAction!==undefined&&!busy&&!pending){actions.splice(Number(button.dataset.removeAction),1);renderQueue();}
  if(button.dataset.removeOrder!==undefined&&!busy&&!pending){orders.splice(Number(button.dataset.removeOrder),1);renderQueue();}
  if(button.id==='share-card')downloadCard();
});
$('#start-form').addEventListener('submit',async e=>{e.preventDefault();if(busy)return;busy=true;const button=e.submitter;button.disabled=true;try{state=await api('/api/v1/runs',{seed:$('#seed').value.trim()});localSet('ik-current-run',state.runId);localSet('ik-run-ids',[...new Set([...localGet('ik-run-ids',[]),state.runId])]);history.replaceState(null,'',`/?run=${state.runId}`);pending=null;actions=[];orders=[];tab='life';render();}catch(e){notify(e.message,true);}finally{busy=false;button.disabled=false;if(state)renderQueue();}});
$('#new-run').addEventListener('click',()=>{if(busy)return;$('#game').hidden=true;$('#welcome').hidden=false;$('#seed').focus();});
$('#advance').addEventListener('click',advance);$('#cancel-commit').addEventListener('click',()=>{$('#confirm-dialog').close();reviewedPlan=null;});$('#confirm-commit').addEventListener('click',settle);
document.addEventListener('submit',async e=>{
  if(e.target.id!=='order-form')return;e.preventDefault();if(busy||pending)return;
  const order={assetId:$('#order-asset').value,side:$('#order-side').value,quantity:$('#order-quantity').value.trim()};if(order.side==='BUY')order.maxSpendKRW=$('#order-budget').value.trim();
  const snapshot=plan(),id=state.runId;busy=true;renderQueue();
  try{await api(runPath()+'/preview',{...snapshot,orders:[...snapshot.orders,order]});if(state.runId!==id||state.stateHash!==snapshot.stateHash)return;orders.push(order);notify('주문을 예약했습니다. 다음 3개월 확정 때 체결합니다.');}
  catch(e){notify(e.message,true);}finally{busy=false;renderQueue();}
});
document.addEventListener('change',e=>{if(e.target.id==='order-side'){$('#order-budget').disabled=e.target.value==='SELL';$('#order-budget').required=e.target.value==='BUY';}});
function downloadCard(){const s=state.scores,svg=`<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="620"><rect width="1000" height="620" fill="#183b34"/><text x="65" y="75" fill="#dbeaa5" font-family="sans-serif" font-size="18">나는야 투자왕 · MY SECOND LIFE</text><text x="65" y="170" fill="#fffefa" font-family="sans-serif" font-size="48" font-weight="bold">나의 두 번째 20년</text><text x="65" y="235" fill="#aabfaa" font-family="sans-serif" font-size="22">2006 Q4 — 2026 Q3 · 80번의 선택</text><text x="65" y="335" fill="#fffefa" font-family="sans-serif" font-size="36">${esc(fmt(s.netWorthKRW))}</text><text x="65" y="420" fill="#dbeaa5" font-family="sans-serif" font-size="28">삶 ${s.lifeScore.toFixed(1)}  ·  균형 ${s.balanceScore.toFixed(1)}  ·  자유 ${s.freedomIndex.toFixed(1)}</text><text x="65" y="545" fill="#aabfaa" font-family="sans-serif" font-size="18">MOCK 가상 시세 · 로컬 알파 플레이 기록</text></svg>`;const url=URL.createObjectURL(new Blob([svg],{type:'image/svg+xml;charset=utf-8'})),a=document.createElement('a');a.href=url;a.download='나의_두번째_20년.svg';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
(async()=>{const id=new URLSearchParams(location.search).get('run')??localGet('ik-current-run');if(!id)return;busy=true;try{state=await api(`/api/v1/runs/${encodeURIComponent(id)}`);pending=localGet(`ik-pending-${id}`);render();if(pending)notify('응답을 확인하지 못한 정산이 있습니다. 같은 요청으로 다시 확인해 주세요.',true);}catch(e){notify('이전 회차를 불러오지 못했습니다. 새 인생을 시작하거나 주소를 확인해 주세요.',true);}finally{busy=false;if(state)renderQueue();}})();
