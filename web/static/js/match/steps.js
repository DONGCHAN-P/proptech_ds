/* 질문 6단계 정의 — 각 단계는 그리기(render) · 이벤트 연결(bind) · 요약(summary)을 갖는다.
 * 상태는 wizard.js 의 ans 객체 하나다. 단계는 ans 를 직접 고치고 ctx.changed() 를 부른다. */
window.STEPS = (function () {

  const PYEONG_GROUPS = [
    { key: 'small', codes: ['10P', '15P'], t: '소형', d: '전용 ~49㎡ · 원룸·투룸', ic: '🛋️' },
    { key: '59', codes: ['20P'], t: '59㎡대', d: '24평형 · 방 3개 소형', ic: '🏠' },
    { key: '74', codes: ['25P'], t: '74㎡대', d: '29평형 · 방 3개', ic: '🏡' },
    { key: '84', codes: ['30P'], t: '84㎡대', d: '34평형 · 국민평형', ic: '🏘️' },
    { key: 'large', codes: ['35P', '40P', '50P', '60P+'], t: '대형', d: '100㎡ 이상 · 40평형~', ic: '🏰' },
  ];

  const HOUSEHOLDS = [
    { key: 'single', t: '혼자 살아요', d: '1인 가구', ic: '🧑', pyeong: ['20P'], prio: ['station'] },
    { key: 'couple', t: '둘이 살아요', d: '신혼 · 2인 가구', ic: '💑', pyeong: ['25P', '30P'], prio: ['station'] },
    { key: 'kids', t: '아이가 있어요', d: '자녀가 있는 가구', ic: '👨‍👩‍👧', pyeong: ['30P', '35P'], prio: ['school', 'station'] },
  ];

  const PRIORITIES = [
    { key: 'station', t: '역세권', d: '지하철역까지 걷는 시간', ic: '🚇' },
    { key: 'school', t: '학군', d: '1km 안 초등학교 수', ic: '🎒' },
    { key: 'new', t: '신축', d: '준공 연도가 최근일수록', ic: '✨' },
    { key: 'green', t: '녹지', d: '공원 · 숲 · 하천 가까이', ic: '🌳' },
    { key: 'active', t: '거래 활발', d: '최근 1년 실거래가 많은 곳', ic: '🔁' },
  ];

  const BUDGET_CHIPS = [30000, 50000, 70000, 90000, 120000, 150000, 200000];
  const COMMUTES = [30, 45, 60];
  const REGIONS = ['서울', '경기', '인천'];

  const esc = s => U.esc(s);
  const opt = (sel, o, multi) =>
    '<button type="button" class="opt' + (sel ? ' on' : '') + '" data-k="' + esc(o.key) + '"' +
    ' role="' + (multi ? 'checkbox' : 'radio') + '" aria-checked="' + !!sel + '">' +
    '<span class="opt-ic">' + o.ic + '</span>' +
    '<span class="opt-t">' + esc(o.t) + '</span>' +
    '<span class="opt-d">' + esc(o.d) + '</span>' +
    (multi ? '<span class="opt-check" aria-hidden="true">✓</span>' : '') +
    '</button>';

  function bigWon(man) {
    if (!man) return '<b>—</b>';
    const eok = man / 10000;
    if (eok >= 1) {
      const t = (Math.round(eok * 10) / 10).toString();
      return '<b>' + t + '</b><small>억</small>';
    }
    return '<b>' + Math.round(man).toLocaleString() + '</b><small>만</small>';
  }

  const list = [
    // 1 ─ 누가
    {
      key: 'household', icon: '👋', hue: 258, label: '가구',
      title: '누가 살 집인가요?',
      sub: '고르시면 평형과 중요한 것을 알맞게 미리 골라 둘게요.',
      render: a => '<div class="opts opts-3">' +
        HOUSEHOLDS.map(o => opt(a.household === o.key, o)).join('') + '</div>',
      bind(el, a, ctx) {
        el.querySelectorAll('.opt').forEach(b => b.addEventListener('click', () => {
          const h = HOUSEHOLDS.find(x => x.key === b.dataset.k);
          a.household = h.key;
          if (!a._touched.pyeongs) a.pyeongs = h.pyeong.slice();
          if (!a._touched.priorities) a.priorities = h.prio.slice();
          ctx.changed(true);
          setTimeout(ctx.next, 260);
        }));
      },
      valid: a => !!a.household,
      summary: a => { const h = HOUSEHOLDS.find(x => x.key === a.household); return h && h.ic + ' ' + h.t; },
    },

    // 2 ─ 예산
    {
      key: 'budget', icon: '💰', hue: 200, label: '예산',
      title: '매매가는 얼마까지 생각하세요?',
      sub: '최근 실거래가가 이 금액 이하인 집만 봅니다.',
      render: a => '<div class="budget">' +
        '<div class="budget-big" id="budgetBig">' + bigWon(a.budget) + '<span class="budget-tail">이하</span></div>' +
        '<input class="range" id="budgetRange" type="range" min="10000" max="300000" step="1000" value="' +
        (a.budget || 70000) + '" aria-label="예산" />' +
        '<div class="range-scale"><span>1억</span><span>10억</span><span>20억</span><span>30억</span></div>' +
        '<div class="chips">' + BUDGET_CHIPS.map(v =>
          '<button type="button" class="chip' + (a.budget === v ? ' on' : '') + '" data-v="' + v + '">' +
          U.won(v) + '</button>').join('') + '</div></div>',
      bind(el, a, ctx) {
        const r = el.querySelector('#budgetRange');
        const big = el.querySelector('#budgetBig');
        const paint = () => {
          big.innerHTML = bigWon(a.budget) + '<span class="budget-tail">이하</span>';
          const pct = (r.value - r.min) / (r.max - r.min) * 100;
          r.style.setProperty('--fill', pct + '%');
          el.querySelectorAll('.chip').forEach(c => c.classList.toggle('on', +c.dataset.v === a.budget));
        };
        if (!a.budget) a.budget = +r.value;
        paint(); ctx.changed();
        r.addEventListener('input', () => { a.budget = +r.value; paint(); ctx.changed(); });
        el.querySelectorAll('.chip').forEach(c => c.addEventListener('click', () => {
          a.budget = +c.dataset.v; r.value = a.budget; paint(); ctx.changed(true);
        }));
      },
      valid: a => a.budget > 0,
      summary: a => '💰 ' + U.won(a.budget) + ' 이하',
    },

    // 3 ─ 평형
    {
      key: 'pyeongs', icon: '📐', hue: 168, label: '평형',
      title: '어느 정도 크기를 찾으세요?',
      sub: '여러 개 고를 수 있어요.',
      render: a => '<div class="opts opts-5">' + PYEONG_GROUPS.map(g =>
        opt(g.codes.some(c => a.pyeongs.includes(c)), g, true)).join('') + '</div>',
      bind(el, a, ctx) {
        el.querySelectorAll('.opt').forEach(b => b.addEventListener('click', () => {
          const g = PYEONG_GROUPS.find(x => x.key === b.dataset.k);
          const on = g.codes.some(c => a.pyeongs.includes(c));
          a.pyeongs = on ? a.pyeongs.filter(c => !g.codes.includes(c))
                         : a.pyeongs.concat(g.codes);
          a._touched.pyeongs = true;
          b.classList.toggle('on', !on);
          b.setAttribute('aria-checked', String(!on));
          ctx.changed(true);
        }));
      },
      valid: a => a.pyeongs.length > 0,
      summary: a => '📐 ' + PYEONG_GROUPS.filter(g => g.codes.some(c => a.pyeongs.includes(c)))
        .map(g => g.t).join('·'),
    },

    // 4 ─ 근무지
    {
      key: 'work', icon: '🏢', hue: 32, label: '출근',
      title: '출근은 어디로 하세요?',
      sub: '회사 근처 지하철역을 검색하세요. 출근하지 않으면 건너뛰어도 돼요.',
      render: a => '<div class="work">' +
        '<div class="search-box"><span class="search-ic">🔍</span>' +
        '<input id="stInput" type="text" autocomplete="off" placeholder="예: 강남, 판교, 여의도" value="' +
        esc(a.work ? a.work.name : '') + '" aria-label="회사 근처 역" />' +
        '<div class="st-results" id="stResults" hidden></div></div>' +
        '<div class="work-picked" id="workPicked">' + (a.work
          ? '<span class="pin">📍</span><b>' + esc(a.work.name) + '역</b> 근처로 출근' +
            '<button type="button" class="link" id="workClear">지우기</button>' : '') + '</div>' +
        '<div class="sub-q">출근에 얼마나 쓸 수 있나요? <small>(편도)</small></div>' +
        '<div class="seg" role="radiogroup">' + COMMUTES.map(m =>
          '<button type="button" class="seg-b' + (a.commute_max === m ? ' on' : '') + '" data-m="' + m + '">' +
          m + '분</button>').join('') + '</div>' +
        '<button type="button" class="link skip" id="workSkip">출근하지 않아요 · 건너뛰기</button></div>',
      bind(el, a, ctx) {
        const inp = el.querySelector('#stInput');
        const box = el.querySelector('#stResults');
        const search = U.debounce(async () => {
          const q = inp.value.trim();
          if (!q) { box.hidden = true; return; }
          const d = await U.get('/api/stations?q=' + encodeURIComponent(q), 'st');
          box.innerHTML = d.items.length ? d.items.map((s, i) =>
            '<button type="button" class="st" data-i="' + i + '"><b>' + esc(s.name) + '</b>' +
            '<span>' + s.lines.map(esc).join(' · ') + '</span></button>').join('')
            : '<div class="st-empty">역을 찾지 못했어요</div>';
          box.hidden = false;
          box.querySelectorAll('.st').forEach(b => b.addEventListener('click', () => {
            const s = d.items[+b.dataset.i];
            a.work = { name: s.name, lat: s.lat, lng: s.lng, lines: s.lines };
            ctx.changed(true); ctx.rerender();
          }));
        }, 160);
        inp.addEventListener('input', search);
        if (!a.work) setTimeout(() => inp.focus(), 380);
        const clr = el.querySelector('#workClear');
        clr && clr.addEventListener('click', () => { a.work = null; ctx.changed(true); ctx.rerender(); });
        el.querySelectorAll('.seg-b').forEach(b => b.addEventListener('click', () => {
          a.commute_max = +b.dataset.m;
          el.querySelectorAll('.seg-b').forEach(x => x.classList.toggle('on', x === b));
          ctx.changed(true);
        }));
        el.querySelector('#workSkip').addEventListener('click', () => {
          a.work = null; ctx.changed(true); ctx.next();
        });
      },
      valid: () => true,
      summary: a => a.work ? '🏢 ' + a.work.name + ' ' + a.commute_max + '분 안' : '🏢 출근 무관',
    },

    // 5 ─ 지역
    {
      key: 'sgg', icon: '🗺️', hue: 330, label: '지역',
      title: '살고 싶은 지역이 있나요?',
      sub: '여러 곳을 고를 수 있어요. 고르지 않으면 수도권 전체에서 찾습니다.',
      render(a, ctx) {
        const tab = a._regionTab || '서울';
        const sgg = (ctx.meta.sigungu || []).filter(s => s.region === tab);
        return '<div class="region">' +
          '<button type="button" class="anywhere' + (a.sgg.length ? '' : ' on') + '" id="anywhere">' +
          '🌏 상관없어요' + (a.work ? ' <small>(출근 시간으로 거릅니다)</small>' : '') + '</button>' +
          '<div class="tabs" role="tablist">' + REGIONS.map(r => {
            const n = (ctx.meta.sigungu || []).filter(s => s.region === r && a.sgg.includes(s.code)).length;
            return '<button type="button" role="tab" class="tab' + (r === tab ? ' on' : '') + '" data-r="' + r + '">' +
              r + (n ? ' <i>' + n + '</i>' : '') + '</button>';
          }).join('') + '</div>' +
          '<div class="chips chips-grid">' + sgg.map(s =>
            '<button type="button" class="chip' + (a.sgg.includes(s.code) ? ' on' : '') + '" data-c="' + esc(s.code) + '">' +
            esc(s.name.replace(/^(서울|인천)\s*/, '')) + '</button>').join('') + '</div></div>';
      },
      bind(el, a, ctx) {
        el.querySelector('#anywhere').addEventListener('click', () => { a.sgg = []; ctx.changed(true); ctx.rerender(); });
        el.querySelectorAll('.tab').forEach(t => t.addEventListener('click', () => {
          a._regionTab = t.dataset.r; ctx.rerender(true);
        }));
        el.querySelectorAll('.chip').forEach(c => c.addEventListener('click', () => {
          const code = c.dataset.c;
          a.sgg = a.sgg.includes(code) ? a.sgg.filter(x => x !== code) : a.sgg.concat(code);
          c.classList.toggle('on');
          el.querySelector('#anywhere').classList.toggle('on', !a.sgg.length);
          ctx.changed(true);
        }));
      },
      valid: () => true,
      summary(a, ctx) {
        if (!a.sgg.length) return '🗺️ 수도권 전체';
        const names = (ctx.meta.sigungu || []).filter(s => a.sgg.includes(s.code)).map(s => s.name);
        return '🗺️ ' + names.slice(0, 2).join('·') + (names.length > 2 ? ' 외 ' + (names.length - 2) : '');
      },
    },

    // 6 ─ 중요한 것
    {
      key: 'priorities', icon: '⭐', hue: 284, label: '중요한 것',
      title: '무엇이 가장 중요하세요?',
      sub: '최대 3개까지 골라 주세요. 고른 순서와 관계없이 같은 비중으로 반영합니다.',
      render: a => '<div class="opts opts-5">' + PRIORITIES.map(o =>
        opt(a.priorities.includes(o.key), o, true)).join('') + '</div>' +
        '<p class="hint" id="prioHint">' + a.priorities.length + ' / 3 선택</p>',
      bind(el, a, ctx) {
        el.querySelectorAll('.opt').forEach(b => b.addEventListener('click', () => {
          const k = b.dataset.k;
          if (a.priorities.includes(k)) a.priorities = a.priorities.filter(x => x !== k);
          else if (a.priorities.length < 3) a.priorities = a.priorities.concat(k);
          else { b.classList.add('shake'); setTimeout(() => b.classList.remove('shake'), 400); return; }
          a._touched.priorities = true;
          el.querySelectorAll('.opt').forEach(x => {
            const on = a.priorities.includes(x.dataset.k);
            x.classList.toggle('on', on); x.setAttribute('aria-checked', String(on));
          });
          el.querySelector('#prioHint').textContent = a.priorities.length + ' / 3 선택';
          ctx.changed(true);
        }));
      },
      valid: a => a.priorities.length > 0,
      summary: a => '⭐ ' + PRIORITIES.filter(p => a.priorities.includes(p.key)).map(p => p.t).join('·'),
    },
  ];

  return { list, PRIORITIES, PYEONG_GROUPS };
})();
