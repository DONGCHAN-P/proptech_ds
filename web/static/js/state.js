/* 앱 상태 — 필터 값과 선택 단지를 한 곳에 모으고, 변경을 구독자에게 알린다. */
window.S = (function () {

  const state = {
    filters: {
      pyeong: [],        // ['25P','30P']
      price_min: null,
      price_max: null,
      built_from: null,
      built_to: null,
      walk_max: null,    // 분
      infra_min: null,
      redv: false,
      gtx: false,
      active_only: false,
      q: '',
    },
    sort: 'trade',
    selected: null,      // apt_id
    meta: null,
  };

  const subs = { filters: [], selected: [] };

  function on(evt, fn) { (subs[evt] || (subs[evt] = [])).push(fn); }
  function emit(evt) { (subs[evt] || []).forEach(fn => fn(state)); }

  /** 서버로 넘길 필터 파라미터 (빈 값은 U.qs 가 걸러낸다) */
  function params() {
    const f = state.filters;
    return {
      pyeong: f.pyeong,
      price_min: f.price_min,
      price_max: f.price_max,
      built_from: f.built_from,
      built_to: f.built_to,
      walk_max: f.walk_max,
      infra_min: f.infra_min,
      redv: f.redv,
      gtx: f.gtx,
      active_only: f.active_only,
      q: f.q,
    };
  }

  function setFilter(patch) {
    Object.assign(state.filters, patch);
    emit('filters');
  }

  function resetFilters() {
    state.filters = {
      pyeong: [], price_min: null, price_max: null, built_from: null, built_to: null,
      walk_max: null, infra_min: null, redv: false, gtx: false, active_only: false, q: '',
    };
    emit('filters');
  }

  function activeCount() {
    const f = state.filters;
    let n = 0;
    if (f.pyeong.length) n++;
    if (f.price_min != null || f.price_max != null) n++;
    if (f.built_from != null || f.built_to != null) n++;
    if (f.walk_max != null || f.infra_min != null || f.redv || f.gtx || f.active_only) n++;
    return n;
  }

  function select(aptId) {
    state.selected = aptId;
    emit('selected');
  }

  return { state, on, params, setFilter, resetFilters, activeCount, select };
})();
