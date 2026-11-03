/* 랭킹 패널 — 저평가(step7) / 신고가(step8) / 1년 급등 */
window.RANK = (function () {

  const DESC = {
    undervalue: '같은 지역·평형의 거래가격과 주변 생활시설을 함께 비교한 목록입니다. ' +
                '동·층·거래 시점에 따라 가격 차이가 있으므로 개별 거래도 함께 확인해 주세요.',
    newhigh:    '최근 수집분에서 같은 평형 직전 평균 대비 크게 높게 체결된 거래입니다. ' +
                '거래가 적거나 층·거래 조건이 다르면 가격 차이가 클 수 있습니다.',
    surge:      '최근 1년 평단가가 그 직전 1년 대비 가장 많이 오른 단지입니다. 1년 거래 3건 이상만 집계합니다.',
  };
  const TITLE = { undervalue: '저평가 단지 TOP', newhigh: '신고가·특이거래', surge: '1년 상승률 TOP' };

  let cur = null;
  let onPick = null;

  function init(opts) {
    onPick = opts.onPick;
    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', () => toggle(btn.dataset.rank));
    });
    document.getElementById('rankClose').addEventListener('click', close);
  }

  function toggle(kind) {
    if (cur === kind) { close(); return; }
    open(kind);
  }

  function close() {
    cur = null;
    document.getElementById('rankpane').hidden = true;
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('on'));
  }

  async function open(kind) {
    cur = kind;
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('on', b.dataset.rank === kind));
    document.getElementById('rankpane').hidden = false;
    document.getElementById('rankTitle').textContent = TITLE[kind];
    document.getElementById('rankDesc').textContent = DESC[kind];
    document.getElementById('rankBody').innerHTML = '<div class="empty">불러오는 중…</div>';

    try {
      const d = await U.get('/api/rankings?' + U.qs({ kind, limit: 60 }), 'rank');
      if (cur === kind) render(kind, d.items);
    } catch (error) {
      if (error.name !== 'AbortError' && cur === kind)
        document.getElementById('rankBody').innerHTML = '<div class="empty">목록을 불러오지 못했습니다. 잠시 후 다시 선택해 주세요.</div>';
    }
  }

  function render(kind, items) {
    const body = document.getElementById('rankBody');
    if (!items.length) {
      body.innerHTML = '<div class="empty">현재 집계된 결과가 없습니다.<br>다른 목록이나 지도에서 단지를 찾아보세요.</div>';
      return;
    }
    body.innerHTML = items.map((d, idx) => {
      let price, sub, reason;
      if (kind === 'newhigh') {
        price = U.won(d.deal_amount);
        sub = U.esc(d.sigungu_name) + ' ' + U.esc(d.legal_dong_name) +
              ' · ' + (d.area_m2 != null ? d.area_m2.toFixed(0) + '㎡' : '') +
              ' · ' + (d.floor ?? '-') + '층 · ' + U.fmtDate(d.deal_date);
        reason = '직전 평균 ' + U.won(d.ref_avg) + ' 대비 ' +
                 '<b class="up">+' + Math.round(d.deviation_pct) + '%</b> (' + d.ref_count + '건 기준)';
      } else if (kind === 'undervalue') {
        price = U.won(d.last_price);
        sub = U.esc(d.sigungu_name) + ' ' + U.esc(d.legal_dong_name || '') +
              ' · ' + U.esc(d.pyeong_bucket) + ' · 평당 ' + U.ppy(d.ppy) + '만';
        reason = d.price_vs_median != null
          ? '지역·평형 거래 중간값의 ' + Math.round(d.price_vs_median) + '% 수준'
          : '같은 지역·평형의 거래가격 비교';
      } else {
        price = U.won(d.rep_price);
        sub = U.esc(d.sigungu_name) + ' ' + U.esc(d.legal_dong_name) +
              ' · ' + U.esc(d.rep_pyeong) + ' · 평당 ' + U.ppy(d.ppy) + '만';
        reason = '1년 평단가 ' + U.chgHtml(d.chg_1y) + ' · 전고점 대비 ' + U.chgHtml(d.vs_peak) +
                 ' · 1년 ' + d.trade_1y + '건';
      }
      return '<div class="rank-row" data-id="' + (d.apt_id || '') +
             '" data-lat="' + (d.lat ?? '') + '" data-lng="' + (d.lng ?? '') + '">' +
          '<div class="rank-no">' + (idx + 1) + '</div>' +
          '<div class="rank-main">' +
            '<div class="ar-top"><span class="ar-name">' + U.esc(d.apt_name) + '</span>' +
              '<span class="ar-price">' + price + '</span></div>' +
            '<div class="ar-sub">' + sub + '</div>' +
            '<div class="rank-reason">' + reason + '</div>' +
          '</div>' +
        '</div>';
    }).join('');

    body.querySelectorAll('.rank-row').forEach(el => {
      el.addEventListener('click', () => {
        const id = el.dataset.id, lat = el.dataset.lat, lng = el.dataset.lng;
        if (!id) { U.toast('이 항목은 지도 단지와 연결되지 않았습니다'); return; }
        onPick(id, lat ? parseFloat(lat) : null, lng ? parseFloat(lng) : null);
      });
    });
  }

  return { init, close };
})();
