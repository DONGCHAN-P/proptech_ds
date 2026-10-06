/* 지도.
 *
 * 마커 하나가 세 가지를 동시에 말한다.
 *   채움색   거래량이 평소보다 많은가/적은가   (빨강 ↔ 파랑)
 *   테두리   값이 평소보다 빠르게 오르는가     (검은 링)
 *   크기     그 기간 거래 건수 = 표본          (제곱근 비례)
 *
 * 색을 거래량에만 쓰는 이유: content/design.py 의 "빨강/파랑은 증감 전용"
 * 규칙을 지키면서 두 축을 한 마커에 담으려면 두 번째 축은 색이 아닌 걸로
 * 표현해야 한다. 색으로 둘 다 나타내면(예: 보라=얇은 상승) 범례를 외워야
 * 읽히는 지도가 된다.
 */
const MapView = (() => {
  const SEOUL = [37.5519, 126.9918];
  let map, layer, palette = {}, onPick = () => { };

  function init(pal, pick) {
    palette = pal; onPick = pick;
    map = L.map('map', { zoomControl: false, attributionControl: true })
      .setView(SEOUL, 10);
    L.control.zoom({ position: 'bottomright' }).addTo(map);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18, minZoom: 8,
      attribution: '지도 © OpenStreetMap · 실거래가 출처 국토교통부'
    }).addTo(map);
    layer = L.layerGroup().addTo(map);
    return map;
  }

  function color(r) {
    if (r.state === 'thin' || r.state === 'unknown') return null;   // 비워 둔다
    return palette[r.dir] || palette.flat;
  }

  function label(r) {
    const rad = U.radius(r.deals);
    return L.marker([r.lat, r.lng], {
      interactive: false,
      icon: L.divIcon({
        className: '', iconSize: [120, 16], iconAnchor: [60, -rad - 2],
        html: `<div class="mk-label">${U.esc(r.name)}</div>`
      })
    });
  }

  function marker(r) {
    const fill = color(r);
    const rad = U.radius(r.deals);
    const el = L.divIcon({
      className: '',
      iconSize: [rad * 2, rad * 2],
      iconAnchor: [rad, rad],
      html: `<div class="mk" style="
        width:${rad * 2}px;height:${rad * 2}px;
        background:${fill || 'transparent'};
        opacity:${fill ? .82 : 1};
        border:${fill
          ? (r.fast ? `2.5px solid ${palette.ink}` : '1.5px solid rgba(255,255,255,.75)')
          : `1.5px dashed ${palette.flat}`};
      "></div>`
    });
    const m = L.marker([r.lat, r.lng], { icon: el, riseOnHover: true });
    m.bindTooltip(tip(r), { direction: 'top', offset: [0, -rad], opacity: .97 });
    m.on('click', () => onPick(r));
    return m;
  }

  /* 툴팁은 "평소 대비"를 먼저 말한다. 절대 건수를 먼저 쓰면 큰 도시가
     늘 대단해 보이고, 그건 이 지도가 답하려는 질문이 아니다. */
  function tip(r) {
    const thin = (r.state === 'thin' || r.state === 'unknown');
    const head = `<b>${U.esc(r.name)}</b>`;
    if (thin) return `${head}<br>거래 ${r.deals}건 — 판단하기엔 적어요`;
    const d = `거래 평소의 <b>${U.times(r.ratio)}</b>` +
      ` <span style="opacity:.7">(${r.deals}건 / 평소 ${U.num(r.deals_usual)}건)</span>`;
    const p = r.chg == null ? ''
      : `<br>값 3개월 ${U.pct(r.chg)} <span style="opacity:.7">(평소 ${U.pct(r.chg_usual)})</span>`;
    return `${head}<br>${d}${p}`;
  }

  /* ── 단지 말풍선 ─────────────────────────────────────────────
     지도에서 사람이 제일 먼저 찾는 건 가격이라, 가격을 마커에 바로 적는다.
     평형을 같이 적는 건 선택이 아니다 — 같은 단지에서 15평과 40평이 두 배
     넘게 차이 나서, 평형 없는 가격은 어느 쪽을 봐도 틀린 값이 된다. */
  function aptMarker(a, compact) {
    const c = palette[a.dir] || palette.flat;
    const w = compact ? 56 : 68;
    const icon = L.divIcon({
      className: '', iconSize: [w, compact ? 24 : 34],
      iconAnchor: [w / 2, compact ? 26 : 36],
      html: `<div class="apt-mk ${a.thin ? 'thin' : ''} ${compact ? 'compact' : ''}"
                  style="--c:${c}">
        <div class="ln">${U.BLDG}<span class="p">${U.won(a.last_price)}</span></div>
        <div class="py">${U.esc(a.pyeong_short || a.pyeong_label || '')}</div>
      </div>`
    });
    const m = L.marker([a.lat, a.lng], { icon, riseOnHover: true });
    m.bindTooltip(aptTip(a), { direction: 'top', offset: [0, -34], opacity: .97 });
    m.on('click', () => onPick(a));
    return m;
  }

  function aptTip(a) {
    const age = `${U.ymd(a.last_date)} · ${U.esc(a.last_floor || '')}`;
    const chg = a.thin
      ? `<span style="opacity:.75">최근 ${a.n_recent}건 / 직전 ${a.n_prior}건 —
         90일 비교를 하기엔 적어요</span>`
      : `90일 전 대비 <b>${U.pct(a.chg)}</b>
         <span style="opacity:.7">(${a.n_recent}건 / ${a.n_prior}건)</span>`;
    return `<b>${U.esc(a.apt_name)}</b> ${U.esc(a.pyeong_short || '')}
      <span style="opacity:.7">${U.esc(a.pyeong_label || '')}</span>
      <br>마지막 거래 <b>${U.won(a.last_price)}</b>
      <span style="opacity:.7">${age}</span>
      <br>${chg}
      <br>전고점 대비 ${U.pct(a.vs_peak)}
      <span style="opacity:.7">(${U.ymd(a.peak_date)} ${U.won(a.peak_price)})</span>`;
  }

  /* 겹치는 말풍선 솎아내기.
   *
   * 말풍선은 70px 쯤 되는데 서울 도심은 그 안에 단지가 열 개씩 들어간다.
   * 전부 그리면 숫자가 서로를 덮어 **아무것도 안 읽히는 지도**가 된다.
   * 화면 좌표를 격자로 나눠 칸마다 하나만 남긴다. 남길 기준은 거래 건수다 —
   * 지워야 한다면 표본이 얇은 쪽을 지운다.
   */
  function declutter(items, cw = 84, ch = 36) {
    const seen = new Set(), out = [];
    [...items].sort((a, b) => (b.n_1y || 0) - (a.n_1y || 0)).forEach(a => {
      const p = map.latLngToContainerPoint([a.lat, a.lng]);
      const k = `${Math.round(p.x / cw)}:${Math.round(p.y / ch)}`;
      if (seen.has(k)) return;
      seen.add(k);
      out.push(a);
    });
    return out;
  }

  function drawApts(items, zoom) {
    layer.clearLayers();
    const keep = declutter(items);
    // 거래가 적은 쪽을 먼저 그려 뒤로 보낸다. 겹치면 표본이 두터운 쪽이 위로.
    [...keep].sort((a, b) => (a.n_1y || 0) - (b.n_1y || 0))
      .forEach(a => aptMarker(a, zoom < 15).addTo(layer));
    return { drawn: keep.length, hidden: items.length - keep.length };
  }

  function draw(items, { labels = false } = {}) {
    layer.clearLayers();
    // 표본이 적은 곳을 먼저 그려 뒤로 보낸다. 겹쳤을 때 판단 가능한 쪽이
    // 위로 오게 한다.
    const order = [...items].sort((a, b) => U.radius(a.deals) - U.radius(b.deals));
    order.forEach(r => marker(r).addTo(layer));
    // 라벨은 마커를 전부 그린 뒤에 올린다. 섞어서 그리면 나중에 그려진
    // 마커가 앞서 그려진 라벨을 덮어 이름이 반쯤 가려진다.
    if (labels) order.forEach(r => label(r).addTo(layer));
  }

  const bbox = () => {
    const b = map.getBounds();
    return [b.getWest(), b.getSouth(), b.getEast(), b.getNorth()].join(',');
  };
  const zoom = () => map.getZoom();
  const flyTo = (lat, lng, z) => map.flyTo([lat, lng], z ?? Math.max(map.getZoom(), 12), { duration: .6 });
  const on = (ev, fn) => map.on(ev, fn);

  return { init, draw, drawApts, bbox, zoom, flyTo, on };
})();
