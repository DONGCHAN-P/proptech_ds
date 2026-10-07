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

  // ── 공유 링크: #q=<base64 JSON> ─────────────────────────────────────
  const SHARE_KEYS = ['household', 'budget', 'pyeongs', 'work', 'work2', 'commute_max', 'commute_strict', 'sgg', 'priorities'];
  function encodeState(a) {
    const o = {};
    SHARE_KEYS.forEach(k => { o[k] = a[k]; });
    ['work', 'work2'].forEach(k => { if (o[k]) o[k] = { name: o[k].name, lat: +o[k].lat.toFixed(5), lng: +o[k].lng.toFixed(5) }; });
    return btoa(unescape(encodeURIComponent(JSON.stringify(o)))).replace(/=+$/, '');
  }
  function decodeState(s) {
    try { return JSON.parse(decodeURIComponent(escape(atob(s)))); } catch (e) { return null; }
  }
  $('shareBtn').addEventListener('click', async () => {
    const url = location.origin + location.pathname + '#q=' + encodeState(WIZ.ans);
    history.replaceState(null, '', url);
    try { await navigator.clipboard.writeText(url); U.toast('링크를 복사했어요. 받는 분도 같은 결과를 봅니다.'); }
    catch (e) { U.toast('주소창의 링크를 복사해 보내 주세요.', 3000); }
  });

  const ctxForSummary = { meta };

  WIZ.init({
    meta,
    async onDone(payload, ans) {
      document.body.dataset.view = 'searching';
      const count = +($('counterN').textContent.replace(/,/g, '')) || 0;
      const req = fetch('/api/match', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
      }).then(r => r.json());
      $('wizard').hidden = true;
      let data;
      try {
        [data] = await Promise.all([req, RES.searching(count)]);
      } catch (e) {
        $('searching').hidden = true; $('wizard').hidden = false;
        document.body.dataset.view = 'wizard';
        U.toast('찾는 중 문제가 생겼어요. 다시 시도해 주세요.', 3000);
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

  const shared = location.hash.startsWith('#q=') && decodeState(location.hash.slice(3));
  if (shared) {
    WIZ.restore(shared);
    WIZ.finish();
  }

  $('editBtn').addEventListener('click', () => {
    REP.close();
    RES.hide();
    document.body.dataset.view = 'wizard';
    WIZ.reopen();
  });
})();
