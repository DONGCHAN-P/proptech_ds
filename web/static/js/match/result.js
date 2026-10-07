/* 결과 화면 — 좁혀지는 연출, Top5 카드, 무채색 지도 위 순위 핀 */
window.RES = (function () {

  const RANK_COLORS = ['#7c5cff', '#ff5c8a', '#ff9f43', '#1fbf8f', '#2d9cff'];
  const $ = id => document.getElementById(id);
  let map = null, layers = null, data = null, ans = null, onOpen = null, hoverLine = null;
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
    if (ans.work) {
      L.marker([ans.work.lat, ans.work.lng], {
        icon: L.divIcon({ className: 'work-wrap', html: '<div class="workpin">🏢<b>' + U.esc(ans.work.name) + '</b></div>',
          iconSize: [0, 0], iconAnchor: [0, 0] }),
        zIndexOffset: 500,
      }).addTo(layers);
      bounds.push([ans.work.lat, ans.work.lng]);
    }
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
    if (hoverLine) { layers.removeLayer(hoverLine); hoverLine = null; }
    if (on && ans.work) {
      hoverLine = L.polyline([[p.it.lat, p.it.lng], [ans.work.lat, ans.work.lng]], {
        color: RANK_COLORS[p.rank - 1], weight: 3, dashArray: '6 8', opacity: 0.9, className: 'commute-line',
      }).addTo(layers);
    }
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
      '<span class="rc-why">' + (it.reasons || []).map(r => '<i>' + U.esc(r) + '</i>').join('') + '</span>' +
      '</span>' +
      '<span class="rc-side">' +
      '<span class="fit"><svg viewBox="0 0 36 36"><circle class="fit-bg" cx="18" cy="18" r="15.5"/>' +
      '<circle class="fit-fg" cx="18" cy="18" r="15.5" style="--p:' + it.score + '"/></svg>' +
      '<b>' + Math.round(it.score) + '</b></span>' +
      '<span class="fit-l">적합도</span>' +
      (c ? '<span class="rc-commute">🚇 ' + c.minutes + '분' + (c.source === 'odsay' ? '' : '<sup>추정</sup>') + '</span>' : '') +
      '</span></button></li>';
  }

  function render(d, a, opts) {
    data = d; ans = a; onOpen = opts.onOpen;
    $('result').hidden = false;
    ensureMap(opts.tiles);
    setTimeout(() => map.invalidateSize(), 30);

    const sum = [];
    sum.push(U.won(d.effective.budget || a.budget) + ' 이하');
    if (a.work) sum.push(a.work.name + ' ' + d.effective.commute_max + '분 안');
    $('rEyebrow').textContent = d.count.toLocaleString() + '곳 중에서 · ' + sum.join(' · ');

    const relax = { commute: '출근 시간을 15분 늘렸어요', budget: '예산을 10% 넓혔어요' };
    $('relaxed').hidden = !d.relaxed.length;
    $('relaxed').innerHTML = d.relaxed.length
      ? '✳︎ 딱 맞는 곳이 5곳보다 적어 ' + d.relaxed.map(k => relax[k]).join(', ') : '';

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
