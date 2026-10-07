/* 단지 리포트 — 벤토 그리드 대시보드. 기존 /api/apt/* 를 그대로 쓴다. */
window.REP = (function () {

  const $ = id => document.getElementById(id);
  const LABEL = {
    price: '가격', commute: '출근',
    station: '역세권', school: '학군', new: '신축', green: '녹지', active: '거래 활발',
  };
  let chart = null, ctx = null;

  function init(opts) {
    ctx = opts;
    $('reportClose').addEventListener('click', close);
    document.addEventListener('keydown', e => { if (e.key === 'Escape') close(); });
  }

  function close() {
    $('report').classList.remove('open');
    setTimeout(() => { $('report').hidden = true; }, 320);
    if (chart) { chart.destroy(); chart = null; }
  }

  function css(v) { return getComputedStyle(document.documentElement).getPropertyValue(v).trim(); }

  function kpi(label, value, sub, cls) {
    return '<div class="tile kpi"><span class="kpi-l">' + label + '</span>' +
      '<span class="kpi-v ' + (cls || '') + '">' + value + '</span>' +
      (sub ? '<span class="kpi-s">' + sub + '</span>' : '') + '</div>';
  }

  function bigWon(man) {
    if (man == null) return '-';
    const eok = Math.floor(man / 10000), rest = Math.round(man % 10000);
    if (!eok) return '<b>' + rest.toLocaleString() + '</b><small>만</small>';
    return '<b>' + eok + '</b><small>억</small>' + (rest ? '<b class="b2">' + rest.toLocaleString() + '</b>' : '');
  }

  function fitTile(it, weights) {
    const rows = Object.keys(it.breakdown).map(k => {
      const v = it.breakdown[k];
      return '<div class="bar"><span class="bar-l">' + LABEL[k] + ' <i>' + Math.round(weights[k] * 100) + '%</i></span>' +
        '<span class="bar-t"><span class="bar-f" style="--w:' + v + '%"></span></span>' +
        '<span class="bar-v">' + Math.round(v) + '</span></div>';
    }).join('');
    return '<div class="tile fit-tile"><h3>내 조건 적합도 <b>' + Math.round(it.score) + '</b><small>/100</small></h3>' +
      '<div class="bars">' + rows + '</div>' +
      '<p class="tile-note">항목별 점수는 고정 기준으로 매깁니다 — 역 도보 5분 이내·준공 5년 이내·초등학교 5곳이면 100점, 가격은 예산 활용도와 같은 구 평당가 순위 (괄호는 반영 비중). 최근 1년 거래가 없으면 총점을 조금 낮춥니다.</p></div>';
  }

  function compareTile(it, items) {
    const rows = items.map((x, i) =>
      '<tr class="' + (x.apt_id === it.apt_id ? 'me' : '') + '" data-id="' + U.esc(x.apt_id) + '">' +
      '<td><span class="dot" style="background:' + RES.RANK_COLORS[i] + '">' + (i + 1) + '</span></td>' +
      '<td class="nm">' + U.esc(x.apt_name) + '</td>' +
      '<td class="num">' + U.wonShort(x.last_price) + '</td>' +
      '<td class="num">' + (x.commute ? x.commute.minutes + '분' : '-') + '</td>' +
      '<td class="num">' + Math.round(x.score) + '</td></tr>').join('');
    return '<div class="tile cmp-tile"><h3>다른 후보와 비교</h3>' +
      '<table class="tbl"><thead><tr><th></th><th>단지</th><th>가격</th><th>출근</th><th>적합도</th></tr></thead>' +
      '<tbody>' + rows + '</tbody></table></div>';
  }

  function nearbyTile(nb) {
    const grp = (t, ic, arr, fmt) => !arr || !arr.length ? '' :
      '<div class="nb"><span class="nb-h">' + ic + ' ' + t + '</span>' +
      arr.slice(0, 4).map(x => '<span class="nb-i">' + fmt(x) + '<em>' + x.dist_m.toLocaleString() + 'm</em></span>').join('') + '</div>';
    return '<div class="tile nb-tile"><h3>걸어서 닿는 곳</h3>' +
      grp('지하철', '🚇', nb.stations, x => U.esc(x.name) + ' <small>' + U.esc(x.line) + '</small>') +
      grp('학교', '🎒', nb.schools, x => U.esc(x.name)) +
      grp('공원', '🌳', nb.parks, x => U.esc(x.name)) + '</div>';
  }

  async function open(it, data) {
    const el = $('report');
    el.hidden = false;
    requestAnimationFrame(() => el.classList.add('open'));
    $('reportInner').innerHTML = '<div class="rep-loading"><span></span><span></span><span></span></div>';

    const [d, ser, tr] = await Promise.all([
      U.get('/api/apt/' + encodeURIComponent(it.apt_id), 'rep'),
      U.get('/api/apt/' + encodeURIComponent(it.apt_id) + '/series?pyeong=' + it.pyeong_bucket, 'rep-s'),
      U.get('/api/apt/' + encodeURIComponent(it.apt_id) + '/trades?limit=8&pyeong=' + it.pyeong_bucket, 'rep-t'),
    ]);
    const info = d.info;
    const py = d.pyeongs.find(p => p.pyeong_bucket === it.pyeong_bucket) || {};
    const rank = data.items.findIndex(x => x.apt_id === it.apt_id) + 1;
    const color = RES.RANK_COLORS[rank - 1];
    const c = it.commute;
    const chg = U.chg(py.chg_1y), peak = U.chg(py.vs_peak);

    $('reportInner').innerHTML =
      '<header class="rep-head" style="--c:' + color + '">' +
      '<span class="rep-rank">' + rank + '</span>' +
      '<div><p class="eyebrow">' + U.esc(info.sigungu_name) + ' ' + U.esc(info.legal_dong_name || '') + '</p>' +
      '<h2>' + U.esc(info.apt_name) + '</h2>' +
      '<p class="rep-addr">' + U.esc(info.road_address || '') + '</p>' +
      '<div class="tags">' +
      '<span class="tag">' + Math.round(it.area_m2) + '㎡</span>' +
      '<span class="tag">' + (info.build_year || '-') + '년 · ' + U.age(info.build_year) + '</span>' +
      (info.nearest_station ? '<span class="tag">🚇 ' + U.esc(info.nearest_station) + ' ' + Math.round(info.walk_min) + '분</span>' : '') +
      '</div></div></header>' +

      '<div class="why">' + (it.reasons || []).map(r => '<span>✓ ' + U.esc(r) + '</span>').join('') + '</div>' +
      ((py.trade_1y || 0) === 0 ? '<div class="warn-box">⚠︎ 최근 1년 사이 이 평형 거래가 없어요. 아래 가격은 ' +
        U.fmtDate(py.last_date) + ' 거래라 지금 시세와 다를 수 있어요. 순위도 그만큼 낮춰 반영했어요.</div>' : '') +

      '<div class="bento">' +
      kpi('최근 실거래가', bigWon(py.last_price), U.fmtDate(py.last_date) + ' · ' + (py.last_floor || '-') + '층') +
      kpi('1년 평당가 변화', chg.text, '최근 1년 vs 직전 1년', chg.cls) +
      kpi('역대 최고가 대비', peak.text, '최고 ' + U.won(py.peak_price) + ' (' + U.fmtDate(py.peak_date) + ')', peak.cls) +
      (c ? kpi('출근 · ' + U.esc(ctx.ans().work.name), '<b>' + c.minutes + '</b><small>분</small>' +
          (it.commute2 ? '<small class="kpi-plus"> · 👥 ' + it.commute2.minutes + '분</small>' : ''),
          U.esc(c.route) + (it.commute2 ? '<br>👥 ' + U.esc(ctx.ans().work2.name) + ': ' + U.esc(it.commute2.route) : '') +
          (c.source === 'odsay' ? ' · 실제 경로' : ' · 역 좌표로 추정'))
         : kpi('최근 1년 거래', '<b>' + (py.trade_1y || 0) + '</b><small>건</small>', '같은 평형 기준')) +

      '<div class="tile chart-tile"><h3>시세 추이 <small>' + Math.round(it.area_m2) + '㎡ · 월평균 실거래가</small></h3>' +
      '<div class="chart-box"><canvas id="repChart"></canvas></div></div>' +

      fitTile(it, data.weights) +

      '<div class="tile tr-tile"><h3>최근 실거래</h3><table class="tbl"><tbody>' +
      (tr.items.length ? tr.items.map(t => '<tr><td>' + U.fmtDate(t.deal_date) + '</td><td class="num">' + t.floor + '층</td>' +
        '<td class="num"><b>' + U.won(t.deal_amount) + '</b></td></tr>').join('')
        : '<tr><td class="muted">거래 내역이 없습니다</td></tr>') +
      '</tbody></table></div>' +

      compareTile(it, data.items) +
      nearbyTile(info.nearby || {}) +
      '</div>' +

      '<footer class="rep-foot">' +
      '<a class="btn-ghost" href="/explore.html#' + encodeURIComponent(it.apt_id) + '">지도에서 자세히 보기 →</a>' +
      '<p class="fine">실거래가 출처 국토교통부 · 해제 신고 건 제외. 이 화면은 고르신 조건에 대한 적합도를 보여 줄 뿐 ' +
      '매수·매도를 권유하거나 미래 가격을 예측하지 않습니다.</p></footer>';

    $('reportInner').querySelectorAll('.cmp-tile tr[data-id]').forEach(r => r.addEventListener('click', () => {
      const x = data.items.find(i => i.apt_id === r.dataset.id);
      if (x && x.apt_id !== it.apt_id) { RES.focus(x.apt_id); open(x, data); }
    }));
    $('reportInner').scrollTop = 0;
    drawChart(ser.items, color);
  }

  function drawChart(items, color) {
    if (chart) { chart.destroy(); chart = null; }
    const cv = $('repChart');
    if (!cv || !items.length) return;
    const g = cv.getContext('2d').createLinearGradient(0, 0, 0, 220);
    g.addColorStop(0, color + '55');
    g.addColorStop(1, color + '00');
    chart = new Chart(cv, {
      type: 'line',
      data: {
        labels: items.map(x => x.ym),
        datasets: [{
          data: items.map(x => x.price), borderColor: color, backgroundColor: g, fill: true,
          borderWidth: 2, pointRadius: 0, pointHoverRadius: 4, tension: 0.3, spanGaps: true,
        }],
      },
      options: {
        responsive: true, maintainAspectRatio: false, animation: { duration: 700 },
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: c => ' ' + U.won(c.parsed.y) + ' (' + items[c.dataIndex].cnt + '건)' } },
        },
        scales: {
          x: { grid: { display: false }, ticks: { color: css('--ink-3'), maxTicksLimit: 6, maxRotation: 0 } },
          y: { grid: { color: css('--grid') }, border: { display: false },
               ticks: { color: css('--ink-3'), callback: v => U.wonShort(v), maxTicksLimit: 5 } },
        },
      },
    });
  }

  return { init, open, close };
})();
