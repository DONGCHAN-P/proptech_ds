/* 지도 — 줌 레벨에 따라 시군구 → 읍면동 → 단지 말풍선을 그린다. */
window.M = (function () {

  let map, layer, poiLayer;
  let markers = {};        // apt_id -> marker
  let lastLevel = null;
  let onSelect = null;     // 단지 클릭 콜백
  let onMoveEnd = null;

  function init(opts) {
    onSelect = opts.onSelect;
    onMoveEnd = opts.onMoveEnd;
    const tiles = opts.tiles;

    map = L.map('map', {
      center: [37.53, 127.02],
      zoom: 11,
      minZoom: 8,
      maxZoom: 18,
      zoomControl: false,
      preferCanvas: true,
    });
    L.control.zoom({ position: 'bottomright' }).addTo(map);

    L.tileLayer(tiles.url, {
      attribution: tiles.attribution,
      subdomains: tiles.subdomains || 'abc',
      maxZoom: tiles.maxZoom || 19,
    }).addTo(map);

    layer = L.layerGroup().addTo(map);
    poiLayer = L.layerGroup().addTo(map);

    map.on('moveend', U.debounce(() => onMoveEnd && onMoveEnd(), 220));
    return map;
  }

  function bbox() {
    const b = map.getBounds();
    return [b.getSouth(), b.getWest(), b.getNorth(), b.getEast()]
      .map(v => v.toFixed(5)).join(',');
  }

  function zoom() { return map.getZoom(); }

  /** 단지 말풍선 — 이름 + 대표 평형 실거래가 */
  function aptIcon(d, selected) {
    const cls = U.ppyClass(d.ppy);
    const sel = selected ? ' sel' : '';
    const html =
      '<div class="bubble ' + cls + sel + '">' +
        '<div class="b-name">' + U.esc(d.apt_name) + '</div>' +
        '<div class="b-price">' + U.wonShort(d.rep_price) + '</div>' +
      '</div>';
    return wrap(html);
  }

  /** 지역 말풍선 — 지역명 + 중위 평당가 + 단지 수 */
  function regionIcon(d) {
    const cls = U.ppyClass(d.ppy);
    const html =
      '<div class="bubble region ' + cls + '">' +
        '<div class="b-name">' + U.esc(d.name) + '</div>' +
        '<div class="b-price">' + U.ppy(d.ppy) + '<span style="font-size:9px">만/평</span></div>' +
        '<div class="b-sub">' + (d.apt_cnt || 0).toLocaleString() + '개 단지</div>' +
      '</div>';
    return wrap(html);
  }

  /** 말풍선을 크기 0인 래퍼에 담는다.

     iconSize 를 주지 않으면 Leaflet 이 만든 .leaflet-marker-icon 이 말풍선보다
     넓게 잡혀 이웃 마커의 클릭을 가로챈다. 래퍼를 0x0 으로 고정하고 말풍선은
     CSS transform 으로 좌표 위에 가운데 맞춤한다. */
  function wrap(html) {
    return L.divIcon({
      html: '<div class="marker-wrap">' + html + '</div>',
      className: 'marker-shell',
      iconSize: [0, 0],
      iconAnchor: [0, 0],
    });
  }

  function render(data, selectedId) {
    layer.clearLayers();
    markers = {};
    lastLevel = data.level;

    data.items.forEach(d => {
      if (d.lat == null || d.lng == null) return;

      if (data.level === 'apt') {
        const m = L.marker([d.lat, d.lng], {
          icon: aptIcon(d, d.apt_id === selectedId),
          riseOnHover: true,
        });
        m.on('click', () => onSelect && onSelect(d.apt_id));
        m.addTo(layer);
        markers[d.apt_id] = m;
        m._data = d;
      } else {
        const m = L.marker([d.lat, d.lng], { icon: regionIcon(d) });
        m.on('click', () => {
          map.flyTo([d.lat, d.lng], data.level === 'sgg' ? 13 : 15, { duration: .6 });
        });
        m.addTo(layer);
      }
    });
  }

  /** 선택 강조만 다시 칠한다 (전체 재요청 없이) */
  function highlight(aptId) {
    Object.entries(markers).forEach(([id, m]) => {
      m.setIcon(aptIcon(m._data, id === aptId));
    });
  }

  function focus(lat, lng, z) {
    map.flyTo([lat, lng], z || Math.max(map.getZoom(), 16), { duration: .7 });
  }

  /** 상세 패널이 열릴 때 주변 시설을 지도에 찍는다 */
  function showPoi(nearby) {
    poiLayer.clearLayers();
    if (!nearby) return;
    const put = (arr, emoji) => (arr || []).forEach(p => {
      if (p.lat == null) return;
      L.marker([p.lat, p.lng], {
        icon: L.divIcon({ html: '<div class="poi-icon">' + emoji + '</div>', className: '', iconSize: [22, 22] }),
      }).bindTooltip(p.name, { direction: 'top' }).addTo(poiLayer);
    });
    put(nearby.stations, '🚇');
    put(nearby.schools, '🏫');
    put(nearby.parks, '🌳');
  }

  function clearPoi() { poiLayer.clearLayers(); }

  return { init, bbox, zoom, render, highlight, focus, showPoi, clearPoi,
           get level() { return lastLevel; } };
})();
