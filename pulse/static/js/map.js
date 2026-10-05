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

  return { init, draw, bbox, zoom, flyTo, on };
})();
