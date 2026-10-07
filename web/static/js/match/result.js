/* 결과 화면 — 좁혀지는 연출, Top5 카드, 무채색 지도 위 순위 핀 */
window.RES = (function () {

  const RANK_COLORS = ['#7c5cff', '#ff5c8a', '#ff9f43', '#1fbf8f', '#2d9cff'];
  const $ = id => document.getElementById(id);
  let map = null, layers = null, data = null, ans = null, onOpen = null, hoverLines = [];
  const pins = {};

  // ── 좁혀지는 연출 ───────────────────────────────────────────────────
  function searching(count) {
    const box = $('dots');
    const n = 64;
    box.innerHTML = '';
    const dots = [];
    for (let i = 0; i < n; i++) {
      const d = document.createElement('i');
      d.style.left = (8 + Math.random() * 84) + '%';
      d.style.top = (10 + Math.random() * 80) + '%';
      d.style.transitionDelay = (Math.random() * 0.25) + 's';
      box.appendChild(d);
      dots.push(d);
    }
    $('searching').hidden = false;
    $('searchingT').textContent = (count ? count.toLocaleString() + '곳 가운데 ' : '') + '조건에 맞는 단지를 고르는 중…';
    requestAnimationFrame(() => box.classList.add('scatter'));
    return new Promise(res => setTimeout(() => {
      box.classList.add('narrow');
      dots.forEach((d, i) => {
        if (i < 5) {
          d.className = 'keep';
          d.style.left = (30 + i * 10) + '%';
          d.style.top = '40%';
          d.style.background = RANK_COLORS[i];
          d.textContent = i + 1;
        } else d.className = 'gone';
      });
      $('searchingT').textContent = '5곳을 찾았어요';
      setTimeout(res, 750);
    }, 1050));
  }

  // ── 지도 ────────────────────────────────────────────────────────────
  function ensureMap(tiles) {
    if (map) return;
    map = L.map('map', { zoomControl: false, attributionControl: true });
    L.control.zoom({ position: 'bottomright' }).addTo(map);
    L.tileLayer(tiles.url, { attribution: tiles.attribution, maxZoom: tiles.maxZoom }).addTo(map);
    layers = L.layerGroup().addTo(map);
  }

  function pinIcon(rank, big) {
    return L.divIcon({
      className: 'rpin-wrap',
      html: '<div class="rpin' + (big ? ' big' : '') + '" style="--c:' + RANK_COLORS[rank - 1] + '">' +
        '<span class="rpin-pulse"></span><span class="rpin-n">' + rank + '</span></div>',
      iconSize: [40, 40], iconAnchor: [20, 20],
    });
  }

  function drawMap() {
    layers.clearLayers();
    Object.keys(pins).forEach(k => delete pins[k]);
    const topIds = new Set(data.items.map(i => i.apt_id));
    data.points.filter(p => !topIds.has(p.apt_id)).forEach(p => {
      L.circleMarker([p.lat, p.lng], {
        radius: 3.5, weight: 0, fillOpacity: 0.35 + Math.min(0.4, (p.score || 0) / 250),
        fillColor: 'var(--dot)', className: 'cand',
      }).addTo(layers);
    });
    const bounds = [];
    works().forEach(([w, ic]) => {
      L.marker([w.lat, w.lng], {
        icon: L.divIcon({ className: 'work-wrap', html: '<div class="workpin">' + ic + '<b>' + U.esc(w.name) + '</b></div>',
          iconSize: [0, 0], iconAnchor: [0, 0] }),
        zIndexOffset: 500,
      }).addTo(layers);
      bounds.push([w.lat, w.lng]);
    });
    data.items.forEach((it, i) => {
      const m = L.marker([it.lat, it.lng], { icon: pinIcon(i + 1), zIndexOffset: (6 - i) * 1000 })  // Leaflet 은 위도로도 z 를 매긴다 — 순위가 이기게 크게
        .addTo(layers)
        .on('click', () => onOpen(it))
        .on('mouseover', () => highlight(it.apt_id, true))
        .on('mouseout', () => highlight(it.apt_id, false));
      pins[it.apt_id] = { m, rank: i + 1, it };
      bounds.push([it.lat, it.lng]);
    });
    if (bounds.length) map.fitBounds(bounds, { padding: [70, 70], maxZoom: 14 });
  }

  function highlight(id, on) {
    const p = pins[id];
    if (!p) return;
    p.m.setIcon(pinIcon(p.rank, on));
    document.querySelectorAll('.rcard').forEach(c => c.classList.toggle('hl', on && c.dataset.id === id));
    hoverLines.forEach(l => layers.removeLayer(l));
    hoverLines = [];
    if (on) {
      hoverLines = works().map(([w], k) => L.polyline([[p.it.lat, p.it.lng], [w.lat, w.lng]], {
        color: RANK_COLORS[p.rank - 1], weight: 3, dashArray: k ? '2 7' : '6 8', opacity: 0.9, className: 'commute-line',
      }).addTo(layers));
    }
  }

  /** [[근무지, 아이콘]] — 나 · 함께 사는 분 */
  function works() {
    const out = [];
    if (ans.work) out.push([ans.work, '🏢']);
    if (ans.work && ans.work2) out.push([ans.work2, '👥']);
    return out;
  }

  function freshness(it) {
    const months = it.last_date ? Math.round((Date.now() - new Date(it.last_date)) / 2.63e9) : null;
    const when = months == null ? '-' : months <= 0 ? '이번 달' : months + '개월 전';
    const n = it.trade_1y || 0;
    return '<span class="rc-fresh' + (n === 0 ? ' warn' : '') + '" title="' +
      (n === 0 ? '최근 1년 사이 같은 평형 거래가 없어 지금 시세와 다를 수 있어요' : '같은 평형 기준') + '">' +
      '최근 거래 ' + when + ' · 1년 ' + n + '건' + (n === 0 ? ' · 시세 확인 필요' : '') + '</span>';
  }

  function focus(id) {
    const p = pins[id];
    if (p) map.flyTo([p.it.lat, p.it.lng], Math.max(map.getZoom(), 15), { duration: 0.6 });
  }

  // ── 카드 ────────────────────────────────────────────────────────────
  function card(it, i) {
    const c = it.commute;
    return '<li class="rcard" data-id="' + U.esc(it.apt_id) + '" style="--c:' + RANK_COLORS[i] + ';--d:' + (i * 90) + 'ms">' +
      '<button type="button" class="rcard-btn">' +
      '<span class="rank">' + (i + 1) + '</span>' +
      '<span class="rc-main">' +
      '<span class="rc-name">' + U.esc(it.apt_name) + '</span>' +
      '<span class="rc-loc">' + U.esc(it.sigungu_name) + ' ' + U.esc(it.legal_dong_name || '') +
      ' · ' + (it.build_year || '-') + '년</span>' +
      '<span class="rc-price"><b>' + U.won(it.last_price) + '</b><small>전용 ' + Math.round(it.area_m2 || 0) + '㎡</small></span>' +
      freshness(it) +
      '<span class="rc-why">' + (it.reasons || []).map(r => '<i>' + U.esc(r) + '</i>').join('') + '</span>' +
      '</span>' +
      '<span class="rc-side">' +
      '<span class="fit"><svg viewBox="0 0 36 36"><circle class="fit-bg" cx="18" cy="18" r="15.5"/>' +
      '<circle class="fit-fg" cx="18" cy="18" r="15.5" style="--p:' + it.score + '"/></svg>' +
      '<b>' + Math.round(it.score) + '</b></span>' +
      '<span class="fit-l">적합도</span>' +
      (c ? '<span class="rc-commute">🏢 ' + c.minutes + '분' + (c.source === 'odsay' ? '' : '<sup>추정</sup>') + '</span>' : '') +
      (it.commute2 ? '<span class="rc-commute">👥 ' + it.commute2.minutes + '분</span>' : '') +
      '</span></button></li>';
  }

  function render(d, a, opts) {
    data = d; ans = a; onOpen = opts.onOpen;
    const onEdit = opts.onEdit;
    $('result').hidden = false;
    ensureMap(opts.tiles);
    setTimeout(() => map.invalidateSize(), 30);

    $('rEyebrow').textContent = d.count.toLocaleString() + '곳 가운데 조건 적합도 순';
    // 조건 칩 — 누르면 그 질문으로 돌아가 하나만 고칠 수 있다
    $('sumChips').innerHTML = STEPS.list.map((s, i) => {
      const t = s.valid(a) && s.summary(a, opts.ctx);
      return t ? '<button type="button" class="tchip" data-i="' + i + '" title="이 조건 바꾸기">' + U.esc(t) + '</button>' : '';
    }).join('');
    $('sumChips').querySelectorAll('.tchip').forEach(b => b.addEventListener('click', () => onEdit(+b.dataset.i)));

    const relax = { commute: '출근 시간을 15분 늘렸어요', budget: '예산을 10% 넓혔어요' };
    const notes = [];
    if (d.relaxed.length) notes.push('✳︎ 딱 맞는 곳이 5곳보다 적어 ' + d.relaxed.map(k => relax[k]).join(', '));
    // 적합도가 전반적으로 낮을 때 — 어느 조건이 가장 덜 채워졌는지 말해 준다
    const STEP_OF = { price: 1, commute: 3 };
    if (d.weak) {
      const si = STEP_OF[d.weak.key] != null ? STEP_OF[d.weak.key] : 5;
      notes.push('ℹ︎ 고르신 조건을 한꺼번에 만족하는 곳이 드물어요. 특히 <b>' + U.esc(d.weak.label) +
        '</b> 점수가 낮아요 (5곳 평균 ' + d.weak.avg + '점). ' +
        '<button type="button" class="link" id="weakEdit" data-i="' + si + '">이 조건 바꾸기</button>');
    }
    $('relaxed').hidden = !notes.length;
    $('relaxed').innerHTML = notes.join('<br>');
    const we = document.getElementById('weakEdit');
    we && we.addEventListener('click', () => onEdit(+we.dataset.i));

    if (!d.items.length) {
      const b = d.blocker;
      $('cards').innerHTML = '<li class="empty-res"><b>조건에 맞는 단지가 없어요</b>' +
        (b ? '<p><b>' + U.esc(b.label) + '</b> 조건을 풀면 ' + b.count.toLocaleString() + '곳이 있어요.</p>' : '') + '</li>';
      layers && layers.clearLayers();
      return;
    }
    $('cards').innerHTML = d.items.map(card).join('');
    document.querySelectorAll('.rcard').forEach(el => {
      const it = d.items.find(x => x.apt_id === el.dataset.id);
      el.addEventListener('mouseenter', () => highlight(it.apt_id, true));
      el.addEventListener('mouseleave', () => highlight(it.apt_id, false));
      el.querySelector('button').addEventListener('click', () => { focus(it.apt_id); onOpen(it); });
    });
    drawMap();
  }

  function hide() { $('result').hidden = true; }

  return { searching, render, hide, focus, RANK_COLORS, map: () => map };
})();
