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
        onOpen: it => REP.open(it, last) });
    },
  });

  $('editBtn').addEventListener('click', () => {
    REP.close();
    RES.hide();
    document.body.dataset.view = 'wizard';
    WIZ.reopen();
  });
})();
