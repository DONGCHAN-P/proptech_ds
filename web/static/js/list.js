/* 좌측 단지 목록 — 현재 지도 범위 + 필터에 걸린 단지를 정렬해 보여준다. */
window.LIST = (function () {

  const body = () => document.getElementById('listBody');
  let items = [];
  let onSelect = null;
  let loadingMore = false;
  let total = 0;

  function init(opts) {
    onSelect = opts.onSelect;

    document.getElementById('sortSel').addEventListener('change', e => {
      S.state.sort = e.target.value;
      opts.onSortChange();
    });

    document.getElementById('listToggle').addEventListener('click', () => {
      document.querySelector('.stage').classList.toggle('list-collapsed');
      setTimeout(() => window.dispatchEvent(new Event('resize')), 220);
    });

    body().addEventListener('scroll', () => {
      const el = body();
      if (loadingMore || items.length >= total) return;
      if (el.scrollTop + el.clientHeight > el.scrollHeight - 200) {
        opts.onLoadMore(items.length);
      }
    });
  }

  function tags(d) {
    const out = [];
    if (d.nearest_station && d.walk_min != null && d.walk_min <= 10) {
      out.push('<span class="tag rail">🚇 ' + U.esc(d.nearest_station) + ' ' + Math.round(d.walk_min) + '분</span>');
    }
    if (d.redv_nearby > 0) out.push('<span class="tag redv">재개발 인접</span>');
    const a = new Date().getFullYear() - (d.build_year || 0);
    if (d.build_year && a <= 5) out.push('<span class="tag new">신축</span>');
    if (d.trade_1y > 0) out.push('<span class="tag">1년 ' + d.trade_1y + '건</span>');
    else out.push('<span class="tag">1년 거래 없음</span>');
    return out.join('');
  }

  function rowHtml(d) {
    const sel = d.apt_id === S.state.selected ? ' on' : '';
    return '' +
      '<div class="apt-row' + sel + '" data-id="' + d.apt_id + '">' +
        '<div class="ar-top">' +
          '<span class="ar-name">' + U.esc(d.apt_name) + '</span>' +
          '<span class="ar-price">' + U.won(d.rep_price) + '</span>' +
        '</div>' +
        '<div class="ar-sub">' +
          U.esc(d.sigungu_name) + ' ' + U.esc(d.legal_dong_name) +
          ' · ' + U.esc(d.rep_pyeong) + ' · ' + U.age(d.build_year) +
          ' · 평당 ' + U.ppy(d.ppy) + '만 ' + U.chgHtml(d.chg_1y) +
        '</div>' +
        '<div class="ar-meta">' + tags(d) + '</div>' +
      '</div>';
  }

  function render(data, append) {
    total = data.total;
    items = append ? items.concat(data.items) : data.items;
    loadingMore = false;

    document.getElementById('listCount').textContent = total.toLocaleString();
    if (!items.length) {
      body().innerHTML = '<div class="empty">조건에 맞는 단지가 없습니다.<br>필터를 넓히거나 지도를 이동해 보세요.</div>';
      return;
    }
    const html = items.map(rowHtml).join('');
    body().innerHTML = html;
    if (!append) body().scrollTop = 0;

    body().querySelectorAll('.apt-row').forEach(el => {
      el.addEventListener('click', () => onSelect(el.dataset.id));
    });
  }

  function setLoading() {
    loadingMore = true;
  }

  function highlight(aptId) {
    body().querySelectorAll('.apt-row').forEach(el => {
      el.classList.toggle('on', el.dataset.id === aptId);
    });
    const el = body().querySelector('.apt-row.on');
    if (el) el.scrollIntoView({ block: 'nearest' });
  }

  function setHint(text) {
    document.getElementById('listHint').textContent = text;
  }

  return { init, render, highlight, setLoading, setHint, get items() { return items; } };
})();
