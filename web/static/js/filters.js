/* 상단 필터바 — 드롭다운 열고 닫기, 값 반영, 라벨 갱신 */
window.FILTERS = (function () {

  let onChange = null;

  function init(meta, opts) {
    onChange = opts.onChange;

    // 평형 칩
    const pc = document.getElementById('pyeongChips');
    pc.innerHTML = meta.pyeong.map(p =>
      '<button class="chip" data-py="' + p.key + '">' + p.label + '</button>').join('');
    pc.querySelectorAll('.chip').forEach(el => {
      el.addEventListener('click', () => {
        const k = el.dataset.py;
        const arr = S.state.filters.pyeong;
        const i = arr.indexOf(k);
        if (i >= 0) arr.splice(i, 1); else arr.push(k);
        el.classList.toggle('on', i < 0);
        S.setFilter({ pyeong: arr });
      });
    });

    // 가격 프리셋
    document.querySelectorAll('#priceChips .chip').forEach(el => {
      el.addEventListener('click', () => {
        const on = el.classList.contains('on');
        document.querySelectorAll('#priceChips .chip').forEach(x => x.classList.remove('on'));
        if (on) {
          document.getElementById('priceMin').value = '';
          document.getElementById('priceMax').value = '';
          S.setFilter({ price_min: null, price_max: null });
          return;
        }
        el.classList.add('on');
        const mn = el.dataset.min ? +el.dataset.min : null;
        const mx = el.dataset.max ? +el.dataset.max : null;
        document.getElementById('priceMin').value = mn ?? '';
        document.getElementById('priceMax').value = mx ?? '';
        S.setFilter({ price_min: mn, price_max: mx });
      });
    });
    ['priceMin', 'priceMax'].forEach(id => {
      document.getElementById(id).addEventListener('change', () => {
        document.querySelectorAll('#priceChips .chip').forEach(x => x.classList.remove('on'));
        S.setFilter({
          price_min: numOrNull('priceMin'),
          price_max: numOrNull('priceMax'),
        });
      });
    });

    // 연식 프리셋
    document.querySelectorAll('#builtChips .chip').forEach(el => {
      el.addEventListener('click', () => {
        const on = el.classList.contains('on');
        document.querySelectorAll('#builtChips .chip').forEach(x => x.classList.remove('on'));
        if (on) {
          document.getElementById('builtFrom').value = '';
          document.getElementById('builtTo').value = '';
          S.setFilter({ built_from: null, built_to: null });
          return;
        }
        el.classList.add('on');
        const fr = el.dataset.from ? +el.dataset.from : null;
        const to = el.dataset.to ? +el.dataset.to : null;
        document.getElementById('builtFrom').value = fr ?? '';
        document.getElementById('builtTo').value = to ?? '';
        S.setFilter({ built_from: fr, built_to: to });
      });
    });
    ['builtFrom', 'builtTo'].forEach(id => {
      document.getElementById(id).addEventListener('change', () => {
        document.querySelectorAll('#builtChips .chip').forEach(x => x.classList.remove('on'));
        S.setFilter({ built_from: numOrNull('builtFrom'), built_to: numOrNull('builtTo') });
      });
    });

    // 추가 조건
    document.getElementById('optRedv').addEventListener('change', e => S.setFilter({ redv: e.target.checked }));
    document.getElementById('optGtx').addEventListener('change', e => S.setFilter({ gtx: e.target.checked }));
    document.getElementById('optActive').addEventListener('change', e => S.setFilter({ active_only: e.target.checked }));

    const walk = document.getElementById('optWalk');
    walk.addEventListener('input', () => {
      const v = +walk.value;
      document.getElementById('lblWalk').textContent = v >= 30 ? '제한 없음' : v + '분 이내';
    });
    walk.addEventListener('change', () => {
      const v = +walk.value;
      S.setFilter({ walk_max: v >= 30 ? null : v });
    });

    const infra = document.getElementById('optInfra');
    infra.addEventListener('input', () => {
      const v = +infra.value;
      document.getElementById('lblInfra').textContent = v <= 0 ? '제한 없음' : v + '점 이상';
    });
    infra.addEventListener('change', () => {
      const v = +infra.value;
      S.setFilter({ infra_min: v <= 0 ? null : v });
    });

    // 드롭다운 토글
    document.querySelectorAll('.fbtn[data-panel]').forEach(btn => {
      btn.addEventListener('click', e => {
        e.stopPropagation();
        const id = 'dd-' + btn.dataset.panel;
        const dd = document.getElementById(id);
        const wasOpen = !dd.hidden;
        closeAll();
        if (!wasOpen) {
          dd.hidden = false;
          const r = btn.getBoundingClientRect();
          dd.style.left = Math.min(r.left, window.innerWidth - dd.offsetWidth - 12) + 'px';
        }
      });
    });
    document.querySelectorAll('.dropdown').forEach(dd =>
      dd.addEventListener('click', e => e.stopPropagation()));
    document.addEventListener('click', closeAll);
    document.addEventListener('keydown', e => { if (e.key === 'Escape') closeAll(); });

    document.getElementById('btnReset').addEventListener('click', reset);

    S.on('filters', () => { updateLabels(); onChange(); });
    updateLabels();
  }

  function numOrNull(id) {
    const v = document.getElementById(id).value;
    return v === '' ? null : +v;
  }

  function closeAll() {
    document.querySelectorAll('.dropdown').forEach(d => { d.hidden = true; });
  }

  function reset() {
    S.resetFilters();
    document.querySelectorAll('.chip').forEach(c => c.classList.remove('on'));
    ['priceMin', 'priceMax', 'builtFrom', 'builtTo'].forEach(id => {
      document.getElementById(id).value = '';
    });
    ['optRedv', 'optGtx', 'optActive'].forEach(id => {
      document.getElementById(id).checked = false;
    });
    document.getElementById('optWalk').value = 30;
    document.getElementById('lblWalk').textContent = '제한 없음';
    document.getElementById('optInfra').value = 0;
    document.getElementById('lblInfra').textContent = '제한 없음';
    document.getElementById('searchInput').value = '';
  }

  function updateLabels() {
    const f = S.state.filters;

    const py = f.pyeong.length
      ? (f.pyeong.length === 1 ? f.pyeong[0] : f.pyeong.length + '개')
      : '전체';
    setLabel('lblPyeong', 'pyeong', py, f.pyeong.length > 0);

    let pr = '전체';
    if (f.price_min != null || f.price_max != null) {
      pr = (f.price_min != null ? U.wonShort(f.price_min) : '') + '~' +
           (f.price_max != null ? U.wonShort(f.price_max) : '');
    }
    setLabel('lblPrice', 'price', pr, pr !== '전체');

    let bt = '전체';
    if (f.built_from != null || f.built_to != null) {
      bt = (f.built_from ?? '') + '~' + (f.built_to ?? '');
    }
    setLabel('lblBuilt', 'built', bt, bt !== '전체');

    const extras = [f.redv, f.gtx, f.active_only, f.walk_max != null, f.infra_min != null]
      .filter(Boolean).length;
    setLabel('lblExtra', 'extra', extras ? extras + '개' : '전체', extras > 0);
  }

  function setLabel(id, panel, text, on) {
    document.getElementById(id).textContent = text;
    document.querySelector('.fbtn[data-panel="' + panel + '"]').classList.toggle('on', on);
  }

  return { init, reset, closeAll };
})();
