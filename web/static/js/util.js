/* 공통 유틸 — 금액 포맷, 색상 스케일, fetch 래퍼 */
window.U = (function () {

  /** 만원 단위 금액 → "12억 3,000" 형태 */
  function won(man) {
    if (man == null || isNaN(man)) return '-';
    const v = Math.round(man);
    const eok = Math.floor(v / 10000);
    const rest = v % 10000;
    if (eok === 0) return rest.toLocaleString() + '만';
    if (rest === 0) return eok + '억';
    return eok + '억 ' + rest.toLocaleString();
  }

  /** 지도 말풍선용 짧은 금액 — "12.3억" */
  function wonShort(man) {
    if (man == null || isNaN(man)) return '-';
    if (man >= 10000) {
      const eok = man / 10000;
      return (eok >= 100 ? Math.round(eok) : eok.toFixed(1).replace(/\.0$/, '')) + '억';
    }
    return Math.round(man).toLocaleString() + '만';
  }

  /** 평당가(만원) → "3,240" */
  function ppy(v) {
    return v == null || isNaN(v) ? '-' : Math.round(v).toLocaleString();
  }

  /** 등락률 → {text, cls} */
  function chg(v) {
    if (v == null || isNaN(v)) return { text: '-', cls: 'muted' };
    const s = (v > 0 ? '+' : '') + v.toFixed(1) + '%';
    return { text: s, cls: v > 0 ? 'up' : (v < 0 ? 'down' : 'muted') };
  }

  function chgHtml(v) {
    const c = chg(v);
    return '<span class="' + c.cls + '">' + c.text + '</span>';
  }

  /** 평당가 구간 → p1~p6 색상 클래스. 수도권 실거래 분포 기준 고정 경계. */
  const PPY_BREAKS = [1500, 2500, 3500, 5000, 8000];
  const PPY_LABELS = ['1500↓', '~2500', '~3500', '~5000', '~8000', '8000↑'];

  function ppyClass(v) {
    if (v == null || isNaN(v)) return 'pna';
    for (let i = 0; i < PPY_BREAKS.length; i++) {
      if (v < PPY_BREAKS[i]) return 'p' + (i + 1);
    }
    return 'p6';
  }

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g,
      c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  }

  /** 준공연도 → "23년차" */
  function age(year) {
    if (!year) return '-';
    const a = new Date().getFullYear() - year;
    return a <= 0 ? '신축' : a + '년차';
  }

  function fmtDate(s) {
    return !s ? '-' : String(s).slice(2).replace(/-/g, '.');
  }

  /** 객체 → 쿼리스트링 (빈 값 제거) */
  function qs(obj) {
    const p = new URLSearchParams();
    Object.entries(obj).forEach(([k, v]) => {
      if (v === null || v === undefined || v === '' || v === false) return;
      if (Array.isArray(v)) { if (v.length) p.set(k, v.join(',')); return; }
      p.set(k, v);
    });
    return p.toString();
  }

  const inflight = {};
  /** 같은 키의 이전 요청은 취소한다 (지도 이동 중 연쇄 요청 방지) */
  async function get(url, key) {
    if (key && inflight[key]) inflight[key].abort();
    const ctrl = new AbortController();
    if (key) inflight[key] = ctrl;
    try {
      const r = await fetch(url, { signal: ctrl.signal });
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return await r.json();
    } finally {
      if (key && inflight[key] === ctrl) delete inflight[key];
    }
  }

  function debounce(fn, ms) {
    let t;
    return function (...a) { clearTimeout(t); t = setTimeout(() => fn.apply(this, a), ms); };
  }

  function toast(msg, ms) {
    const el = document.getElementById('toast');
    if (!el) return;
    el.textContent = msg;
    el.hidden = false;
    clearTimeout(el._t);
    el._t = setTimeout(() => { el.hidden = true; }, ms || 2200);
  }

  return { won, wonShort, ppy, chg, chgHtml, ppyClass, PPY_LABELS, esc, age, fmtDate, qs, get, debounce, toast };
})();
