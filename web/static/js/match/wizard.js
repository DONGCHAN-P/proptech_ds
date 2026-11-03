/* 질문 마법사 — 진행바 · 카드 전환 · 답변 칩 · 실시간 후보 수 카운터 */
window.WIZ = (function () {

  const steps = STEPS.list;
  const ans = {
    household: null, budget: null, pyeongs: [], work: null, work2: null, commute_max: 60, commute_strict: false,
    sgg: [], priorities: [], _touched: {},
  };
  let cur = 0;          // 현재 단계 인덱스
  let reached = 0;      // 한 번이라도 도달한 가장 뒤 단계
  let ctx = null;       // { meta, onDone }
  let lastCount = null;

  const $ = id => document.getElementById(id);

  function init(opts) {
    ctx = opts;
    $('backBtn').addEventListener('click', back);
    $('nextBtn').addEventListener('click', next);
    document.addEventListener('keydown', e => {
      if ($('wizard').hidden || e.target.tagName === 'INPUT') return;
      if (e.key === 'Enter' || e.key === 'ArrowRight') next();
      if (e.key === 'ArrowLeft') back();
    });
    paintProgress();
    show(0, 0);
    refreshCount();
  }

  /** 지금까지 도달한 단계의 답만 서버로 — 아직 안 본 단계의 기본값이 거르면 안 된다 */
  function payload(full) {
    const upto = full ? steps.length : reached + 1;
    const has = k => steps.findIndex(s => s.key === k) < upto;
    return {
      household: ans.household,
      budget: has('budget') ? ans.budget : null,
      pyeongs: has('pyeongs') ? ans.pyeongs : [],
      work: has('work') && ans.work ? { lat: ans.work.lat, lng: ans.work.lng } : null,
      work2: has('work') && ans.work && ans.work2 ? { lat: ans.work2.lat, lng: ans.work2.lng } : null,
      commute_max: ans.commute_max,
      commute_strict: ans.commute_strict,
      sgg: has('sgg') ? ans.sgg : [],
      priorities: ans.priorities,
    };
  }

  // ── 진행바 ──────────────────────────────────────────────────────────
  function paintProgress() {
    $('progress').innerHTML =
      '<div class="pg-line"><div class="pg-fill" id="pgFill"></div></div>' +
      steps.map((s, i) =>
        '<button type="button" class="pg-dot" data-i="' + i + '" aria-label="' + (i + 1) + '단계 ' + s.label + '">' +
        '<span class="pg-ic">' + s.icon + '</span><span class="pg-l">' + s.label + '</span></button>'
      ).join('');
    $('progress').querySelectorAll('.pg-dot').forEach(d => d.addEventListener('click', () => {
      const i = +d.dataset.i;
      if (i <= reached) go(i);
    }));
  }

  function updateProgress() {
    $('progress').querySelectorAll('.pg-dot').forEach((d, i) => {
      d.classList.toggle('done', i < cur || (i <= reached && i !== cur && steps[i].valid(ans)));
      d.classList.toggle('now', i === cur);
      d.classList.toggle('locked', i > reached);
      d.setAttribute('aria-current', i === cur ? 'step' : 'false');
    });
    $('pgFill').style.width = (cur / (steps.length - 1) * 100) + '%';
    document.body.dataset.step = String(cur + 1);
    document.body.style.setProperty('--hue', steps[cur].hue);
  }

  // ── 카드 ────────────────────────────────────────────────────────────
  function cardHtml(i) {
    const s = steps[i];
    return '<div class="q-head">' +
      '<span class="q-ic">' + s.icon + '</span>' +
      '<span class="q-num">' + String(i + 1).padStart(2, '0') + ' <i>/ ' + String(steps.length).padStart(2, '0') + '</i></span>' +
      '</div>' +
      '<h2 class="q-title">' + s.title + '</h2>' +
      '<p class="q-sub">' + s.sub + '</p>' +
      '<div class="q-body">' + s.render(ans, ctx) + '</div>';
  }

  function stepCtx() {
    return {
      meta: ctx.meta,
      changed: (now) => { paintTrail(); updateNav(); now ? refreshCount() : refreshCountSoon(); },
      next,
      rerender: (keepFocus) => rerender(keepFocus),
    };
  }

  function show(i, dir) {
    const stage = $('stage');
    const old = stage.querySelector('.qcard:not(.leaving)');
    const card = document.createElement('section');
    card.className = 'qcard' + (dir > 0 ? ' from-right' : dir < 0 ? ' from-left' : ' from-below');
    card.innerHTML = cardHtml(i);
    stage.appendChild(card);
    steps[i].bind(card, ans, stepCtx());
    requestAnimationFrame(() => requestAnimationFrame(() => card.classList.remove('from-right', 'from-left', 'from-below')));
    if (old) {
      old.classList.add('leaving', dir >= 0 ? 'to-left' : 'to-right');
      setTimeout(() => old.remove(), 450);
    }
    cur = i;
    reached = Math.max(reached, i);
    updateProgress();
    paintTrail();
    updateNav();
  }

  function rerender() {
    const card = $('stage').querySelector('.qcard:not(.leaving)');
    if (!card) return;
    card.querySelector('.q-body').innerHTML = steps[cur].render(ans, ctx);
    steps[cur].bind(card, ans, stepCtx());
    paintTrail(); updateNav();
  }

  function go(i) {
    if (i === cur || i < 0 || i >= steps.length) return;
    show(i, i > cur ? 1 : -1);
    refreshCount();
  }

  function next() {
    if (!steps[cur].valid(ans)) { nudge(); return; }
    if (cur === steps.length - 1) { ctx.onDone(payload(true), ans); return; }
    go(cur + 1);
  }

  function back() { go(cur - 1); }

  function nudge() {
    const c = $('stage').querySelector('.qcard:not(.leaving)');
    c && (c.classList.add('shake'), setTimeout(() => c.classList.remove('shake'), 420));
  }

  function updateNav() {
    $('backBtn').style.visibility = cur === 0 ? 'hidden' : 'visible';
    const last = cur === steps.length - 1;
    $('nextBtn').textContent = last ? '5곳 찾기 ✦' : '다음 →';
    $('nextBtn').classList.toggle('final', last);
    $('nextBtn').disabled = !steps[cur].valid(ans);
  }

  // ── 답변 칩 ─────────────────────────────────────────────────────────
  function paintTrail() {
    const chips = [];
    for (let i = 0; i <= reached; i++) {
      if (i === cur && !steps[i].valid(ans)) continue;
      const t = steps[i].valid(ans) ? steps[i].summary(ans, ctx) : null;
      if (!t) continue;
      chips.push('<button type="button" class="tchip' + (i === cur ? ' now' : '') + '" data-i="' + i + '">' +
        U.esc(t) + '</button>');
    }
    const el = $('trail');
    const before = el.querySelectorAll('.tchip').length;
    el.innerHTML = chips.join('');
    const all = el.querySelectorAll('.tchip');
    if (all.length > before && all.length) all[all.length - 1].classList.add('pop');
    all.forEach(b => b.addEventListener('click', () => go(+b.dataset.i)));
  }

  // ── 카운터 ──────────────────────────────────────────────────────────
  async function refreshCount() {
    if (!window.JIP?.session) {
      $('counterN').textContent = '로그인 후';
      return;
    }
    try {
      const d = await JIP.api('/api/match/count', {
        method: 'POST',
        body: JSON.stringify(payload(false)),
      });
      roll(d.count);
    } catch (e) { /* 카운터는 보조 정보 — 실패해도 진행은 막지 않는다 */ }
  }
  const refreshCountSoon = U.debounce(refreshCount, 220);

  function roll(to) {
    const el = $('counterN');
    const from = lastCount == null ? to * 1.6 : lastCount;
    lastCount = to;
    const t0 = performance.now(), dur = 650;
    el.parentElement.classList.toggle('low', to < 5);
    el.parentElement.classList.remove('tick'); void el.offsetWidth; el.parentElement.classList.add('tick');
    (function frame(t) {
      const p = Math.min(1, (t - t0) / dur);
      const e = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(from + (to - from) * e).toLocaleString();
      if (p < 1) requestAnimationFrame(frame);
    })(t0);
  }

  /** 공유 링크로 받은 답을 채우고 마지막 단계에 서 있게 한다 */
  function restore(st) {
    Object.assign(ans, st);
    ans._touched = { pyeongs: true, priorities: true };
    reached = steps.length - 1;
    show(steps.length - 1, 0);
    refreshCount();
  }

  function finish() { ctx.onDone(payload(true), ans); }

  function reopen(i) {
    $('wizard').hidden = false;
    go(i == null ? cur : i);
  }

  return { init, ans, payload, reopen, restore, finish };
})();
