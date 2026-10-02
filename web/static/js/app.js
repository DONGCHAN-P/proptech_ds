/* 앱 조립 — 지도/목록/필터/상세/랭킹을 연결한다. */
(function () {

  let meta = null;

  async function boot() {
    meta = await U.get('/api/meta');
    S.state.meta = meta;
    renderLegend();

    M.init({ onSelect: pick, onMoveEnd: refresh, tiles: meta.tiles });
    LIST.init({ onSelect: pick, onSortChange: loadList, onLoadMore: loadMore });
    DETAIL.init({ onClose: () => { S.select(null); M.highlight(null); LIST.highlight(null); } });
    RANK.init({ onPick: pickFromRank });
    FILTERS.init(meta, { onChange: refresh });
    initSearch();

    const st = meta.stat;
    U.toast(st.apt_cnt.toLocaleString() + '개 단지 · 실거래 ' +
      (st.trade_cnt / 10000).toFixed(0) + '만건 (' +
      String(st.first_trade).slice(0, 4) + '~' + U.fmtDate(st.last_trade) + ')', 4200);

    refresh();
  }

  function renderLegend() {
    document.getElementById('lgScale').innerHTML = U.PPY_LABELS.map((l, i) =>
      '<div class="lg-cell p' + (i + 1) + '">' + l + '</div>').join('');
  }

  /** 지도 + 목록을 현재 상태로 다시 불러온다 */
  function refresh() {
    loadMap();
    loadList();
  }

  /** 줌이 낮을수록 말풍선이 겹치므로 거래 많은 순으로 솎아낸다. */
  function markerLimit(z) {
    if (z >= 17) return 900;
    if (z >= 16) return 600;
    if (z >= 15) return 380;
    return 220;
  }

  async function loadMap() {
    const url = '/api/map?' + U.qs(Object.assign({
      zoom: M.zoom(), bbox: M.bbox(), limit: markerLimit(M.zoom()),
    }, S.params()));
    try {
      const d = await U.get(url, 'map');
      M.render(d, S.state.selected);
      LIST.setHint(d.level === 'apt'
        ? '지도를 움직이면 목록이 갱신됩니다'
        : '확대하면 단지별 시세가 표시됩니다 (현재 ' +
          (d.level === 'sgg' ? '시군구' : '읍면동') + ' 단위)');
      if (d.level === 'apt' && d.total > d.items.length) {
        U.toast('범위 내 ' + d.total.toLocaleString() + '개 중 ' +
                d.items.length.toLocaleString() + '개만 표시 — 확대하거나 필터를 좁혀보세요');
      }
    } catch (e) {
      if (e.name !== 'AbortError') U.toast('지도 데이터를 불러오지 못했습니다');
    }
  }

  async function loadList(offset) {
    const url = '/api/list?' + U.qs(Object.assign({
      bbox: M.bbox(), sort: S.state.sort, limit: 60, offset: offset || 0,
    }, S.params()));
    try {
      const d = await U.get(url, offset ? 'list-more' : 'list');
      LIST.render(d, !!offset);
    } catch (e) {
      if (e.name !== 'AbortError') U.toast('목록을 불러오지 못했습니다');
    }
  }

  function loadMore(offset) {
    LIST.setLoading();
    loadList(offset);
  }

  /** 단지 선택 — 지도 강조 + 목록 강조 + 상세 열기 */
  function pick(aptId) {
    S.select(aptId);
    M.highlight(aptId);
    LIST.highlight(aptId);
    DETAIL.open(aptId);
  }

  /** 랭킹에서 선택 — 지도를 그 위치로 옮긴 뒤 연다 */
  function pickFromRank(aptId, lat, lng) {
    if (lat != null && lng != null && !isNaN(lat)) M.focus(lat, lng, 16);
    pick(aptId);
  }

  // ── 검색 ────────────────────────────────────────────
  function initSearch() {
    const input = document.getElementById('searchInput');
    const box = document.getElementById('searchResults');

    const run = U.debounce(async () => {
      const q = input.value.trim();
      if (q.length < 1) { box.hidden = true; return; }
      try {
        const d = await U.get('/api/search?q=' + encodeURIComponent(q), 'search');
        renderSearch(d, box);
      } catch (e) { /* 취소된 요청 무시 */ }
    }, 220);

    input.addEventListener('input', run);
    input.addEventListener('focus', () => { if (input.value.trim()) run(); });
    document.addEventListener('click', e => {
      if (!document.getElementById('search').contains(e.target)) box.hidden = true;
    });
    input.addEventListener('keydown', e => {
      if (e.key === 'Escape') { box.hidden = true; input.blur(); }
      if (e.key === 'Enter') {
        const first = box.querySelector('.sr-item');
        if (first) first.click();
      }
    });
  }

  function renderSearch(d, box) {
    const parts = [];
    if (d.regions.length) {
      parts.push('<div class="sr-group">지역</div>');
      d.regions.forEach(r => {
        parts.push('<div class="sr-item" data-kind="region" data-lat="' + r.lat +
          '" data-lng="' + r.lng + '" data-level="' + r.level + '">' +
          '<div class="sr-name">' + U.esc(r.name) + '</div>' +
          '<div class="sr-sub">' + (r.parent ? U.esc(r.parent) + ' · ' : '') +
          r.apt_cnt.toLocaleString() + '개 단지 · 평당 ' + U.ppy(r.ppy) + '만</div></div>');
      });
    }
    if (d.apts.length) {
      parts.push('<div class="sr-group">단지</div>');
      d.apts.forEach(a => {
        parts.push('<div class="sr-item" data-kind="apt" data-id="' + a.apt_id +
          '" data-lat="' + a.lat + '" data-lng="' + a.lng + '">' +
          '<div class="sr-name">' + U.esc(a.apt_name) + '</div>' +
          '<div class="sr-sub">' + U.esc(a.sigungu_name) + ' ' + U.esc(a.legal_dong_name) +
          ' · ' + U.won(a.rep_price) + ' · ' + U.age(a.build_year) + '</div></div>');
      });
    }
    if (!parts.length) parts.push('<div class="empty">검색 결과가 없습니다</div>');

    box.innerHTML = parts.join('');
    box.hidden = false;
    box.querySelectorAll('.sr-item').forEach(el => {
      el.addEventListener('click', () => {
        box.hidden = true;
        const lat = parseFloat(el.dataset.lat), lng = parseFloat(el.dataset.lng);
        if (el.dataset.kind === 'apt') {
          M.focus(lat, lng, 16);
          pick(el.dataset.id);
        } else {
          M.focus(lat, lng, el.dataset.level === 'sgg' ? 13 : 15);
        }
      });
    });
  }

  boot().catch(e => {
    document.getElementById('listBody').innerHTML =
      '<div class="empty">서버에 연결하지 못했습니다.<br>' + U.esc(e.message) + '</div>';
  });
})();
