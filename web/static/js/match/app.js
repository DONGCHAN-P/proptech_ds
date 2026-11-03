/* 맞춤 찾기 진입점 — 질문 → 연출 → 결과 → 리포트를 잇는다 */
(async function () {

  const $ = id => document.getElementById(id);
  let meta = { sigungu: [] };
  let last = null;

  // 테마: 시스템 설정을 따르되, 버튼으로 바꾸면 기억한다
  try {
    const t = localStorage.getItem('match-theme');
    if (t) document.documentElement.dataset.theme = t;
  } catch (e) { /* 저장소가 막혀 있어도 기본 테마로 동작 */ }
  $('themeBtn').addEventListener('click', () => {
    const dark = document.documentElement.dataset.theme
      ? document.documentElement.dataset.theme === 'dark'
      : matchMedia('(prefers-color-scheme: dark)').matches;
    const next = dark ? 'light' : 'dark';
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem('match-theme', next); } catch (e) { /* 무시 */ }
  });

  try { meta = await U.get('/api/meta'); } catch (e) { U.toast('데이터를 불러오지 못했어요. 서버를 확인해 주세요.', 4000); }

  REP.init({ ans: () => WIZ.ans });

  $('shareBtn').addEventListener('click', async () => {
    if(!last) return;
    try { await JIP.save('recommendation', crypto.randomUUID(), {label:'맞춤 추천 · '+last.items.length+'곳', result:last, answers:{...WIZ.payload(true),work:WIZ.ans.work,work2:WIZ.ans.work2}});U.toast('내 저장함에 보관했습니다.'); }
    catch(e){U.toast(e.message,4000);}
  });

  const ctxForSummary = { meta };

  WIZ.init({
    meta,
    async onDone(payload, ans) {
      try {await JIP.ready;await JIP.login();}catch(e){U.toast(e.message);return;}
      document.body.dataset.view = 'searching';
      const count = +($('counterN').textContent.replace(/,/g, '')) || 0;
      $('wizard').hidden = true;
      let data;
      try {
        const req = JIP.api('/api/match', {method:'POST',body:JSON.stringify(payload)});
        [data] = await Promise.all([req, RES.searching(count)]);
        await JIP.refresh();
      } catch (e) {
        $('searching').hidden = true; $('wizard').hidden = false;
        document.body.dataset.view = 'wizard';
        U.toast(e.message || '찾는 중 문제가 생겼어요. 다시 시도해 주세요.', 4000);
        return;
      }
      last = data;
      $('searching').hidden = true;
      document.body.dataset.view = 'result';
      RES.render(data, ans, { tiles: meta.tiles || { url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png', attribution: '&copy; OpenStreetMap', maxZoom: 19 },
        onOpen: it => REP.open(it, last), ctx: ctxForSummary,
        onEdit: i => { REP.close(); RES.hide(); document.body.dataset.view = 'wizard'; WIZ.reopen(i); } });
    },
  });

  // Search draft is tab-local, limited to price only, expires in 30 minutes, consumed once.
  try {const raw=sessionStorage.getItem('jip-search-draft');sessionStorage.removeItem('jip-search-draft');if(raw){const draft=JSON.parse(raw);if(draft.expires>Date.now()&&Number.isFinite(draft.budget))WIZ.ans.budget=draft.budget;}}catch(_){}
  if(location.hash.startsWith('#q=')) history.replaceState(null,'',location.pathname);
  const savedId=new URLSearchParams(location.search).get('saved');
  if(savedId){try{await JIP.ready;await JIP.login();const saved=await JIP.api('/api/saved');const found=saved.items.find(x=>x.id===savedId&&x.kind==='recommendation');if(found){WIZ.restore(found.payload.answers);last=found.payload.result;$('wizard').hidden=true;document.body.dataset.view='result';RES.render(last,WIZ.ans,{tiles:meta.tiles,onOpen:it=>REP.open(it,last),ctx:ctxForSummary,onEdit:i=>{REP.close();RES.hide();document.body.dataset.view='wizard';WIZ.reopen(i);}});}}catch(e){U.toast(e.message);}}

  $('editBtn').addEventListener('click', () => {
    REP.close();
    RES.hide();
    document.body.dataset.view = 'wizard';
    WIZ.reopen();
  });
})();
