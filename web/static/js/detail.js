/* 단지 상세 패널 — 시세 추이 차트, 평형별 시세, 실거래 내역, 주변 인프라 */
window.DETAIL = (function () {

  let cur = null;          // {info, pyeongs}
  let curPyeong = null;    // 선택된 평형 bucket (null = 전체)
  let chart = null;
  let onClose = null;

  function init(opts) {
    onClose = opts.onClose;
    document.getElementById('detailClose').addEventListener('click', close);
  }

  async function open(aptId) {
    const el = document.getElementById('detail');
    el.hidden = false;
    document.getElementById('detailInner').innerHTML =
      '<div class="empty">불러오는 중…</div>';

    const d = await U.get('/api/apt/' + aptId, 'detail');
    cur = d;
    curPyeong = d.info.rep_pyeong;
    render();
    M.showPoi(d.info.nearby);
    loadChart();
    loadTrades();
  }

  function close() {
    document.getElementById('detail').hidden = true;
    if (chart) { chart.destroy(); chart = null; }
    M.clearPoi();
    cur = null;
    onClose && onClose();
  }

  function headTags(i) {
    const out = [];
    if (i.nearest_station) {
      out.push('<span class="tag rail">🚇 ' + U.esc(i.nearest_station) +
        (i.nearest_line ? ' (' + U.esc(i.nearest_line) + ')' : '') +
        (i.walk_min != null ? ' 도보 ' + Math.round(i.walk_min) + '분' : '') + '</span>');
    }
    if (i.redv_nearby > 0) {
      out.push('<span class="tag redv">재개발 ' + i.redv_nearby + '곳' +
        (i.redv_status_best ? ' · ' + U.esc(i.redv_status_best) : '') + '</span>');
    }
    if (i.gtx_dist > 0 && i.gtx_dist <= 3000) {
      out.push('<span class="tag new">GTX ' + U.esc(i.gtx_line || '') + ' ' +
        (i.gtx_dist / 1000).toFixed(1) + 'km</span>');
    }
    out.push('<span class="tag">' + (i.build_year || '?') + '년 · ' + U.age(i.build_year) + '</span>');
    out.push('<span class="tag">인프라 ' + (i.infra_score != null ? i.infra_score.toFixed(0) : '-') + '점</span>');
    return out.join('');
  }

  function selPyeong() {
    return cur.pyeongs.find(p => p.pyeong_bucket === curPyeong) || cur.pyeongs[0];
  }

  function render() {
    const i = cur.info;
    const p = selPyeong();

    const pyTabs = cur.pyeongs.map(x =>
      '<button class="py-tab' + (x.pyeong_bucket === curPyeong ? ' on' : '') +
      '" data-py="' + x.pyeong_bucket + '">' + U.esc(x.label) +
      ' <span style="opacity:.65">' + (x.trade_total) + '</span></button>').join('');

    const pyRows = cur.pyeongs.map(x =>
      '<tr' + (x.pyeong_bucket === curPyeong ? ' class="high"' : '') + '>' +
        '<td>' + U.esc(x.label) + '</td>' +
        '<td class="num">' + (x.area_m2 ? x.area_m2.toFixed(0) + '㎡' : '-') + '</td>' +
        '<td class="num">' + U.won(x.last_price) + '</td>' +
        '<td class="num">' + U.ppy(x.last_ppy) + '</td>' +
        '<td class="num">' + U.chgHtml(x.chg_1y) + '</td>' +
        '<td class="num muted">' + U.fmtDate(x.last_date) + '</td>' +
      '</tr>').join('');

    const nb = i.nearby || {};
    const nbList = (arr, emoji) => (arr || []).slice(0, 4).map(x =>
      '<div class="infra-item"><span>' + emoji + ' ' + U.esc(x.name) + '</span><b>' +
      x.dist_m.toLocaleString() + 'm</b></div>').join('') || '<div class="muted small">정보 없음</div>';

    document.getElementById('detailInner').innerHTML = '' +
      '<div class="dt-head">' +
        '<div class="dt-name">' + U.esc(i.apt_name) + '</div>' +
        '<div class="dt-addr">' + U.esc(i.sigungu_name) + ' ' + U.esc(i.legal_dong_name) +
          ' · ' + U.esc(i.road_address || '') + '</div>' +
        '<div class="dt-tags">' + headTags(i) + '</div>' +
      '</div>' +

      '<div class="dt-price">' +
        '<div class="dt-price-label">' + U.esc(p.label) + ' 최근 실거래 · ' + U.fmtDate(p.last_date) + '</div>' +
        '<div class="dt-price-main">' + U.won(p.last_price) + '</div>' +
        '<div class="dt-price-sub">' +
          '평당 ' + U.ppy(p.last_ppy) + '만원 · ' +
          (p.last_area_m2 ? p.last_area_m2.toFixed(1) + '㎡ ' : '') +
          (p.last_floor != null ? p.last_floor + '층' : '') +
        '</div>' +
      '</div>' +

      '<div class="dt-kpis">' +
        '<div class="kpi"><div class="kpi-v ' + U.chg(p.chg_1y).cls + '">' + U.chg(p.chg_1y).text + '</div><div class="kpi-l">1년 평단가</div></div>' +
        '<div class="kpi"><div class="kpi-v ' + U.chg(p.chg_3y).cls + '">' + U.chg(p.chg_3y).text + '</div><div class="kpi-l">3년 평단가</div></div>' +
        '<div class="kpi"><div class="kpi-v ' + U.chg(p.vs_peak).cls + '">' + U.chg(p.vs_peak).text + '</div><div class="kpi-l">전고점 대비</div></div>' +
      '</div>' +

      '<div class="dt-sec">' +
        '<div class="dt-sec-title">평형 선택</div>' +
        '<div class="py-tabs">' + pyTabs + '</div>' +
        '<div class="chart-wrap"><canvas id="dtChart"></canvas></div>' +
      '</div>' +

      '<div class="dt-sec">' +
        '<div class="dt-sec-title">평형별 시세<span class="muted small">전고점 ' +
          U.won(p.peak_price) + ' (' + U.fmtDate(p.peak_date) + ')</span></div>' +
        '<table class="tbl"><thead><tr>' +
          '<th>평형</th><th class="num">면적</th><th class="num">최근가</th>' +
          '<th class="num">평당</th><th class="num">1년</th><th class="num">거래일</th>' +
        '</tr></thead><tbody>' + pyRows + '</tbody></table>' +
      '</div>' +

      '<div class="dt-sec">' +
        '<div class="dt-sec-title">실거래 내역<span class="muted small" id="tradeScope"></span></div>' +
        '<div class="scroll-y"><table class="tbl"><thead><tr>' +
          '<th>계약일</th><th class="num">거래가</th><th class="num">평당</th>' +
          '<th class="num">면적</th><th class="num">층</th>' +
        '</tr></thead><tbody id="tradeBody">' +
          '<tr><td colspan="5" class="muted">불러오는 중…</td></tr>' +
        '</tbody></table></div>' +
      '</div>' +

      '<div class="dt-sec">' +
        '<div class="dt-sec-title">주변 인프라</div>' +
        '<div class="infra-grid">' +
          '<div><div class="muted small" style="margin-bottom:4px">지하철</div>' + nbList(nb.stations, '🚇') + '</div>' +
          '<div><div class="muted small" style="margin-bottom:4px">학교</div>' + nbList(nb.schools, '🏫') + '</div>' +
        '</div>' +
        '<div style="margin-top:12px"><div class="muted small" style="margin-bottom:4px">공원</div>' +
          nbList(nb.parks, '🌳') + '</div>' +
        '<div class="infra-grid" style="margin-top:14px">' +
          '<div class="infra-item"><span>초등학교 1km</span><b>' + (i.elem_school_cnt_1km ?? '-') + '개</b></div>' +
          '<div class="infra-item"><span>가장 가까운 공원</span><b>' + (i.park_dist != null ? Math.round(i.park_dist) + 'm' : '-') + '</b></div>' +
          '<div class="infra-item"><span>상권 점수</span><b>' + (i.commerce_score != null ? i.commerce_score.toFixed(0) : '-') + '</b></div>' +
          '<div class="infra-item"><span>병원 수</span><b>' + (i.hospital_cnt ?? '-') + '개</b></div>' +
        '</div>' +
      '</div>' +

      '<div class="dt-sec" style="border:none">' +
        '<div class="muted small">국토교통부 실거래가 공개시스템 기준 · 해제(취소) 건 제외 · ' +
          '총 ' + (i.trade_total || 0).toLocaleString() + '건 누적</div>' +
      '</div>';

    document.getElementById('detailInner').querySelectorAll('.py-tab').forEach(el => {
      el.addEventListener('click', () => {
        curPyeong = el.dataset.py;
        render();
        loadChart();
        loadTrades();
      });
    });
  }

  async function loadChart() {
    const d = await U.get('/api/apt/' + cur.info.apt_id + '/series?pyeong=' + curPyeong, 'series');
    const cv = document.getElementById('dtChart');
    if (!cv) return;
    if (chart) chart.destroy();

    const pts = d.items;
    if (!pts.length) {
      cv.parentElement.innerHTML = '<div class="empty">이 평형의 거래 이력이 없습니다.</div>';
      return;
    }

    chart = new Chart(cv, {
      type: 'line',
      data: {
        labels: pts.map(p => p.ym),
        datasets: [{
          label: '평균 실거래가',
          data: pts.map(p => p.price),
          borderColor: '#ff5a5f',
          backgroundColor: 'rgba(255,90,95,.10)',
          borderWidth: 2,
          pointRadius: pts.length > 60 ? 0 : 2.5,
          pointHoverRadius: 5,
          fill: true,
          tension: .25,
          spanGaps: true,
        }],
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: c => U.won(c.parsed.y) + '  (' + pts[c.dataIndex].cnt + '건)',
            },
          },
        },
        scales: {
          x: { ticks: { maxTicksLimit: 7, font: { size: 10 } }, grid: { display: false } },
          y: {
            ticks: { font: { size: 10 }, callback: v => U.wonShort(v) },
            grid: { color: '#f0f2f5' },
          },
        },
      },
    });
  }

  async function loadTrades() {
    const d = await U.get('/api/apt/' + cur.info.apt_id + '/trades?pyeong=' + curPyeong + '&limit=100', 'trades');
    const tb = document.getElementById('tradeBody');
    if (!tb) return;
    document.getElementById('tradeScope').textContent =
      selPyeong().label + ' · 최근 ' + d.items.length + '건';

    if (!d.items.length) {
      tb.innerHTML = '<tr><td colspan="5" class="muted">거래 내역이 없습니다.</td></tr>';
      return;
    }
    // 신고가 표시: 그 시점까지의 최고가를 갱신한 거래
    const asc = d.items.slice().reverse();
    let peak = 0;
    const highs = new Set();
    asc.forEach(t => { if (t.deal_amount > peak) { peak = t.deal_amount; highs.add(t.deal_date + '|' + t.deal_amount + '|' + t.floor); } });

    tb.innerHTML = d.items.map(t => {
      const isHigh = highs.has(t.deal_date + '|' + t.deal_amount + '|' + t.floor);
      return '<tr' + (isHigh ? ' class="high"' : '') + '>' +
        '<td>' + U.fmtDate(t.deal_date) + (isHigh ? ' <span class="up" style="font-size:10px">신고가</span>' : '') + '</td>' +
        '<td class="num"><b>' + U.won(t.deal_amount) + '</b></td>' +
        '<td class="num">' + U.ppy(t.ppy) + '</td>' +
        '<td class="num">' + (t.area_m2 != null ? t.area_m2.toFixed(1) : '-') + '</td>' +
        '<td class="num">' + (t.floor ?? '-') + '</td>' +
      '</tr>';
    }).join('');
  }

  return { init, open, close };
})();
