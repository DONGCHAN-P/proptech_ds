/* 공통 헬퍼.
 *
 * 카피 규칙은 content/design.py 와 같다.
 *   · σ·표준편차는 화면에 쓰지 않는다 — "평소의 1.7배"로 번역한다
 *   · 증감은 항상 부호와 방향을 붙인다
 *   · 표본은 숨기지 않는다
 */
const U = (() => {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];

  const esc = s => String(s ?? '').replace(/[&<>"']/g,
    c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  const num = v => v == null ? '–'
    : (Number(v) % 1 ? Number(v).toFixed(1) : Number(v).toFixed(0))
      .replace(/\B(?=(\d{3})+(?!\d))/g, ',');

  /* 평당가는 만원 단위. 1,000만원/평을 넘으면 억으로 읽는 사람이 없어서 그대로 둔다. */
  const ppy = v => v == null ? '–' : num(Math.round(v)) + '만';

  /* "평소의 1.7배" — 표준편차 대신 쓰는 표현 */
  const times = r => r == null ? '–' : r.toFixed(1) + '배';

  /* "+4.2%" / "−3.1%" — 부호를 항상 붙인다 */
  const pct = v => v == null ? '–'
    : (v >= 0 ? '+' : '−') + Math.abs(v).toFixed(1) + '%';

  const arrow = v => v == null ? '' : (v >= 0 ? '▲ ' : '▼ ');

  /* 증감 방향 클래스. 0 근처는 회색으로 둔다 — 0.1% 를 빨갛게 칠하지 않는다. */
  const dirOf = (v, band = 0) =>
    v == null ? 'flat' : (v > band ? 'up' : (v < -band ? 'down' : 'flat'));

  const json = async (url) => {
    const r = await fetch(url);
    if (!r.ok) throw new Error(`${r.status} ${url}`);
    return r.json();
  };

  const debounce = (fn, ms = 220) => {
    let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); };
  };

  /* 거래 건수를 원 반지름으로. 제곱근을 쓰는 이유는 사람이 원을 **넓이**로
     읽기 때문이다. 반지름을 건수에 비례시키면 큰 지역이 실제보다 훨씬 커 보인다. */
  const radius = (n, lo = 5, hi = 22) =>
    Math.max(lo, Math.min(hi, Math.sqrt(Math.max(n, 0)) * 1.8 + 3));

  /* 만원 → 사람이 말하는 단위. 12.8억 / 9,800만 */
  const won = v => {
    if (v == null) return '–';
    const m = Number(v);
    if (Math.abs(m) < 10000) return num(m) + '만';
    const e = m / 10000;
    return (Math.abs(e) >= 100 ? e.toFixed(0) : e.toFixed(1)) + '억';
  };

  /* 아파트 글리프. 이모지를 쓰지 않는 이유는 플랫폼마다 모양이 달라서
     디자인이 기기별로 깨지기 때문이다. */
  const BLDG = `<svg class="bldg" viewBox="0 0 12 14" fill="currentColor"
      aria-hidden="true"><rect x="0.5" y="1.5" width="11" height="12" rx="1.2"/>
      <g fill="#fff"><rect x="2.4" y="3.6" width="2.2" height="2.2" rx=".4"/>
      <rect x="7.4" y="3.6" width="2.2" height="2.2" rx=".4"/>
      <rect x="2.4" y="7.4" width="2.2" height="2.2" rx=".4"/>
      <rect x="7.4" y="7.4" width="2.2" height="2.2" rx=".4"/></g></svg>`;

  /* "2026-09-29" → "26.09.29" */
  const ymd = d => !d ? '–' : String(d).slice(2).replace(/-/g, '.');

  return { $, $$, esc, num, ppy, won, times, pct, arrow, dirOf, json,
           debounce, radius, BLDG, ymd };
})();
