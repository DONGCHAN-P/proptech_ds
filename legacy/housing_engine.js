/* THE AI HOUSING ENGINE — v2 intuitive scoring */

let ALL = [];
let FILTERED = [];
let PRICED = [];
let state = {
  filter: "all",
  sort: "ai",
  selected: null,
  pricedOnly: true,
  syncMap: true,
  pageSize: 60,
  rendered: 0,
  currentPb: 0,   // index of pyeong bucket shown in chart
};

let map, clusterLayer, priceChart, donutChart;
let markerByAptId = new Map();

const TIER_PALETTE = {
  S: { bg: "rgba(200,255,0,.18)", bd: "#C8FF00", fg: "#C8FF00", glow: "rgba(200,255,0,.45)" },
  A: { bg: "rgba(0,229,255,.16)", bd: "#00E5FF", fg: "#00E5FF", glow: "rgba(0,229,255,.35)" },
  B: { bg: "rgba(108,140,140,.14)", bd: "#6C8C8C", fg: "#B6BFBF", glow: "transparent" },
  C: { bg: "rgba(60,75,75,.14)", bd: "#3D5050", fg: "#7A8585", glow: "transparent" },
};

const fmtPrice = (v) => v == null ? "—" : (v >= 100 ? v.toFixed(0) : v.toFixed(1));
const stars = (n) => "★".repeat(n) + "☆".repeat(5 - n);
const truncName = (n, max=7) => (!n) ? "—" : (n.length > max ? n.slice(0, max) + "…" : n);

function deltaInfo(history) {
  if (!history || history.length < 2) return { pct: 0, kind: "flat" };
  const last = history[history.length - 1][1];
  const prev = history[0][1];
  if (!prev) return { pct: 0, kind: "flat" };
  const pct = ((last - prev) / prev) * 100;
  if (Math.abs(pct) < 0.2) return { pct: 0, kind: "flat" };
  return { pct: pct.toFixed(1), kind: pct >= 0 ? "up" : "down" };
}

function filterList() {
  let arr = ALL;
  if (state.filter === "hot") arr = arr.filter(a => a.hot);
  else if (state.filter === "value") arr = arr.filter(a => a.gr === "S" || a.gr === "A");
  else if (state.filter === "S") arr = arr.filter(a => a.aiT === "S");
  else if (state.filter === "A") arr = arr.filter(a => a.aiT === "A");
  else if (state.filter !== "all") arr = arr.filter(a => a.rg === state.filter);
  if (state.pricedOnly) arr = arr.filter(a => a.p != null);
  const q = document.getElementById("searchInput").value.trim().toLowerCase();
  if (q) {
    arr = arr.filter(a =>
      (a.n||"").toLowerCase().includes(q) ||
      (a.gu||"").toLowerCase().includes(q) ||
      (a.st||"").toLowerCase().includes(q)
    );
  }
  if (state.sort === "ai") arr = [...arr].sort((a,b) => (b.ai||0) - (a.ai||0));
  else if (state.sort === "price") arr = [...arr].sort((a,b) => (a.p||1e9) - (b.p||1e9));
  else if (state.sort === "price_desc") arr = [...arr].sort((a,b) => (b.p||-1) - (a.p||-1));
  else if (state.sort === "growth") arr = [...arr].sort((a,b) => (b.grS||0) - (a.grS||0));
  return arr;
}

function renderList(reset = true) {
  if (reset) {
    FILTERED = filterList();
    state.rendered = 0;
    document.getElementById("listScroll").innerHTML = "";
  }
  document.getElementById("totalCount").textContent = FILTERED.length.toLocaleString();
  const slice = FILTERED.slice(state.rendered, state.rendered + state.pageSize);
  const c = document.getElementById("listScroll");
  const wrap = document.createElement("div");
  wrap.innerHTML = slice.map((a, idx) => {
    const i = state.rendered + idx;
    const tier = a.aiT || "C";
    const histAll = (a.pb && a.pb[0]) ? a.pb[0].tr : null;
    const d = histAll ? deltaInfo(histAll) : { kind: "flat" };
    const priceHtml = a.p != null
      ? '<span class="apt-price">' + fmtPrice(a.p) + '</span><span class="apt-price-unit">억</span>'
      : '<span class="apt-price dim">시세조회</span>';
    const deltaHtml = a.p != null && histAll && histAll.length >= 2
      ? '<span class="apt-delta ' + d.kind + '">' + (d.kind === "up" ? "▲" : d.kind === "down" ? "▼" : "—") + ' ' + (d.kind==="flat" ? "보합" : Math.abs(d.pct)+"%") + '</span>'
      : '<span class="apt-delta flat">' + (a.p != null ? "1건" : "미정") + '</span>';
    const ptBadge = a.ptE ? '<span class="badge price-tier"><span class="emoji">' + a.ptE + '</span>' + a.ptL + '</span>' : '';
    return ''
      + '<div class="apt-card tier-' + tier + ' ' + (a.i === state.selected ? "selected" : "") + '" data-id="' + a.i + '">'
      +   '<div class="rank-badge tier-bg-' + tier + '">' + (i < 3 ? "TOP " + (i+1) : tier) + '</div>'
      +   '<div class="apt-name">' + (a.n||"—") + '</div>'
      +   '<div class="apt-loc">' + (a.gu||"—") + (a.st ? " · " + a.st + (a.wm ? "역 " + a.wm + "분" : "역") : "") + '</div>'
      +   '<div class="apt-price-row">' + priceHtml + deltaHtml + '</div>'
      +   '<div class="apt-badges">'
      +     ptBadge
      +     '<span class="badge"><span class="stars">' + stars(a.lf||0) + '</span> 라이프 ' + (a.lf||0) + '</span>'
      +     '<span class="badge grade-' + (a.gr||"D") + '">미래 ' + (a.gr||"D") + '</span>'
      +   '</div>'
      +   '<div class="apt-meta">'
      +     (a.pb && a.pb[0] ? '<span>📐 ' + a.pb[0].py + ' · ' + a.pb[0].cnt + '건</span>' : (a.ar ? '<span>📐 ' + a.ar + '㎡</span>' : ""))
      +     (a.by ? '<span>🏢 ' + a.by + '년</span>' : "")
      +     (a.tg||[]).slice(0,2).map(t => '<span class="hash">#' + t + '</span>').join("")
      +   '</div>'
      + '</div>';
  }).join("");
  while (wrap.firstChild) c.appendChild(wrap.firstChild);
  state.rendered += slice.length;
  const existing = c.querySelector(".load-more");
  if (existing) existing.remove();
  if (state.rendered < FILTERED.length) {
    const btn = document.createElement("button");
    btn.className = "load-more";
    btn.textContent = "더 보기 (+" + Math.min(state.pageSize, FILTERED.length - state.rendered) + ")  ·  총 " + FILTERED.length.toLocaleString();
    btn.onclick = () => renderList(false);
    c.appendChild(btn);
  }
  c.querySelectorAll(".apt-card").forEach(el => {
    el.onclick = () => {
      state.selected = el.dataset.id;
      state.currentPb = 0;
      renderList();
      renderDetail();
      if (state.syncMap) flyToSelected();
      refreshSelectedMarker();
    };
  });
}

function initMap() {
  map = L.map('map', { zoomControl: true, attributionControl: true, preferCanvas: true }).setView([37.5350, 127.000], 11);
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png', {
    attribution: '© OSM · © CARTO', subdomains: 'abcd', maxZoom: 19
  }).addTo(map);
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_only_labels/{z}/{x}/{y}{r}.png', {
    subdomains: 'abcd', maxZoom: 19
  }).addTo(map);
  clusterLayer = L.markerClusterGroup({
    chunkedLoading: true,
    showCoverageOnHover: false,
    maxClusterRadius: (z) => z >= 15 ? 30 : z >= 13 ? 50 : 80,
    spiderfyOnMaxZoom: false,
    disableClusteringAtZoom: 16,
  });
  map.addLayer(clusterLayer);
}

function markerHtml(a, selected) {
  const tier = a.aiT || "C";
  const cls = "apt-marker tier-" + tier + (selected ? " selected" : "") + (a.p == null ? " no-price" : "");
  const nameHtml = '<span class="m-name">' + truncName(a.n) + '</span>';
  const priceHtml = a.p != null ? '<span class="m-price">' + fmtPrice(a.p) + '억</span>' : '<span class="m-price m-dim">시세조회</span>';
  return '<div class="' + cls + '">' + nameHtml + priceHtml + '</div>';
}

function rebuildMarkers() {
  clusterLayer.clearLayers();
  markerByAptId.clear();
  const arr = state.pricedOnly ? ALL.filter(a => a.p != null) : ALL;
  document.getElementById("mapCount").textContent = arr.length.toLocaleString();
  const markers = [];
  arr.forEach(a => {
    const ic = L.divIcon({ className: "", html: markerHtml(a, false), iconSize: null });
    const m = L.marker([a.la, a.ln], { icon: ic });
    m.on('click', () => {
      state.selected = a.i;
      state.currentPb = 0;
      renderList();
      renderDetail();
      if (state.syncMap) flyToSelected();
      refreshSelectedMarker();
    });
    markerByAptId.set(a.i, m);
    markers.push(m);
  });
  clusterLayer.addLayers(markers);
}

function refreshSelectedMarker() {
  if (!state.selected) return;
  const m = markerByAptId.get(state.selected);
  if (!m) return;
  const a = ALL.find(x => x.i === state.selected);
  if (!a) return;
  m.setIcon(L.divIcon({ className: "", html: markerHtml(a, true), iconSize: null }));
}

function flyToSelected() {
  const a = ALL.find(x => x.i === state.selected);
  if (!a) return;
  map.flyTo([a.la, a.ln], Math.max(map.getZoom(), 15), { duration: 0.6 });
}

function checkRow(bd) {
  return bd.map(r => {
    const met = r[1];
    return '<div class="check-row ' + (met ? "met" : "miss") + '"><span class="ck">' + (met ? "✓" : "·") + '</span><span class="cl">' + r[0] + '</span><span class="cv">' + r[2] + '</span></div>';
  }).join("");
}

function renderDetail() {
  const a = ALL.find(x => x.i === state.selected);
  const panel = document.getElementById("detailPanel");
  if (!a) {
    panel.innerHTML = '<div class="det-section" style="border-bottom:none; height:100%; display:flex; align-items:center; justify-content:center; flex-direction:column; gap:10px;"><div style="font-size:32px;">🏙️</div><div style="font-size:14px; color: var(--text-2);">왼쪽 매물 카드 또는 지도 마커를 선택해 주세요</div><div style="font-size:11px; color: var(--text-3);">' + ALL.length.toLocaleString() + '개 단지 · 실거래가 ' + PRICED.length.toLocaleString() + '건</div></div>';
    return;
  }

  const tier = a.aiT || "C";
  const pbList = a.pb || [];
  const cur = pbList[state.currentPb] || pbList[0];
  const d = cur ? deltaInfo(cur.tr) : { kind: "flat" };
  const rank = FILTERED.findIndex(x => x.i === a.i) + 1;
  const priceHtml = a.p != null
    ? '<div class="hero-price">' + fmtPrice(a.p) + '</div><div class="hero-price-unit">억' + (a.ar ? " · " + a.ar + "㎡" : "") + '</div>'
      + (cur && cur.tr.length >= 2 ? '<div class="hero-delta ' + d.kind + '">' + (d.kind==="up"?"▲":d.kind==="down"?"▼":"—") + ' ' + (d.kind==="flat"?"보합":Math.abs(d.pct)+"%") + ' (' + cur.py + ')</div>' : '')
    : '<div class="hero-price dim">시세 미확정</div><div class="hero-price-unit">최근 실거래 없음</div>';

  const priorityCommute = a.lg && a.lg <= 2 ? 42 : 32;
  const priorityInfra = 28 + Math.round(((a.cs||50))/100 * 8);
  const priorityValue = a.rv >= 3 ? 22 : 14;
  const priorityEmo = 100 - priorityCommute - priorityInfra - priorityValue;

  let html = ''
    + '<div class="detail-hero tier-bg-' + tier + '">'
    +   '<div class="hero-tag">AI MATCHED · ' + tier + '등급' + (rank>0 ? " · #" + rank + " / " + FILTERED.length : "") + '</div>'
    +   '<div class="hero-name">' + a.n + '</div>'
    +   '<div class="hero-loc">' + a.gu + (a.st ? " · " + a.st + "역" + (a.wm ? " 도보 " + a.wm + "분" : "") : "") + '</div>'
    +   '<div class="hero-price-row">' + priceHtml + '</div>'
    +   '<div class="hero-tags">' + ((a.tg||[]).map(t=>'<span class="hero-tag-pill"># ' + t + '</span>').join("") || '<span class="hero-tag-pill">데이터 보강중</span>') + '</div>'
    + '</div>';

  // tier badges instead of 3 numeric scores
  html += '<div class="ai-tier-grid">'
    + '<div class="tier-cell"><div class="tier-l">LIFE 라이프</div><div class="tier-v"><span class="stars-big">' + stars(a.lf||0) + '</span></div><div class="tier-s">' + (a.lf||0) + ' / 5</div></div>'
    + '<div class="tier-cell"><div class="tier-l">PRICE 가격대</div><div class="tier-v tier-emoji">' + (a.ptE || "—") + '</div><div class="tier-s">' + (a.ptL || "시세 미확정") + (a.ptR ? " · " + a.ptR : "") + '</div></div>'
    + '<div class="tier-cell"><div class="tier-l">GROWTH 성장</div><div class="tier-v grade-letter grade-' + (a.gr||"D") + '">' + (a.gr||"D") + '</div><div class="tier-s">' + (a.grS||0) + ' / 5점</div></div>'
    + '</div>';

  // Per-pyeong chart with tabs
  if (pbList.length > 0) {
    html += '<div class="det-section"><h3>실거래가 추이 (평형별)</h3>';
    html += '<div class="pb-tabs">';
    pbList.forEach((pb, idx) => {
      html += '<button class="pb-tab' + (idx === state.currentPb ? ' active' : '') + '" data-pb="' + idx + '">'
        + pb.py + ' <span class="pb-cnt">(' + pb.cnt + '건)</span> '
        + '<span class="pb-avg">평균 ' + pb.avg + '억</span>'
        + '</button>';
    });
    html += '</div>';
    if (cur) {
      html += '<div class="chart-wrap"><canvas id="priceChart"></canvas></div>'
        + '<div class="pb-meta">'
        +   '<div><span class="pb-meta-l">최근 거래</span><span class="pb-meta-v">' + cur.tr[cur.tr.length-1][0] + '</span></div>'
        +   '<div><span class="pb-meta-l">최근가</span><span class="pb-meta-v lime">' + cur.last + '억</span></div>'
        +   '<div><span class="pb-meta-l">평균가</span><span class="pb-meta-v cyan">' + cur.avg + '억</span></div>'
        +   '<div><span class="pb-meta-l">거래 횟수</span><span class="pb-meta-v">' + cur.cnt + '회</span></div>'
        + '</div>';
    }
    html += '<div class="small">' + (a.by ? a.by + "년 준공" : "연식 미상") + " · 누적 거래 " + (a.tc || 0) + "건 · 단지 내 " + pbList.length + "개 평형대 거래 확인" + '</div></div>';
  }

  // LIFE breakdown
  if (a.lfBd) {
    html += '<div class="det-section"><h3>LIFE 라이프 점수 산정 (' + (a.lf||0) + ' / 5★)</h3>'
      + '<div class="breakdown">' + checkRow(a.lfBd) + '</div>'
      + '<div class="small">조건 충족 = 별 1개. 5가지 기준 모두 충족 시 만점.</div></div>';
  }

  // GROWTH breakdown
  if (a.grBd) {
    html += '<div class="det-section"><h3>GROWTH 성장 등급 산정 (' + (a.gr||"D") + ' · ' + (a.grS||0) + '점)</h3>'
      + '<div class="breakdown">' + checkRow(a.grBd) + '</div>'
      + '<div class="small">등급 기준 — 5점: S · 4점: A · 3점: B · 2점: C · 1점 이하: D</div></div>';
  }

  // Infra detail
  html += '<div class="det-section"><h3>인프라 상세</h3><div class="infra-grid">'
    + '<div class="infra-row"><div class="l">🚇 최근접역</div><div class="v cyan">' + (a.st || "—") + (a.sd ? " (" + (a.sd>=1000?(a.sd/1000).toFixed(1)+"km":a.sd+"m") + ")" : "") + '</div></div>'
    + '<div class="infra-row"><div class="l">🚶 도보 · 노선</div><div class="v">' + (a.wm ? a.wm + "분" : "—") + (a.lg ? " · " + a.lg + "급선" : "") + '</div></div>'
    + '<div class="infra-row"><div class="l">🏫 초등학교 (1km)</div><div class="v">' + (a.sc != null ? a.sc + "개" : "—") + '</div></div>'
    + '<div class="infra-row"><div class="l">🌳 녹지점수</div><div class="v lime">' + (a.gs != null ? a.gs : "—") + '</div></div>'
    + '<div class="infra-row"><div class="l">🛍 상권점수</div><div class="v cyan">' + (a.cs != null ? a.cs : "—") + '</div></div>'
    + '<div class="infra-row"><div class="l">🏗 정비구역</div><div class="v">' + (a.rv && a.rv>=1 ? (a.rvs || "인접") + " · " + a.rv + "건" : "—") + '</div></div>'
    + '<div class="infra-row"><div class="l">🏞 공원거리</div><div class="v">' + (a.pd != null ? (a.pd>=1000?(a.pd/1000).toFixed(1)+"km":a.pd+"m") : "—") + '</div></div>'
    + '<div class="infra-row"><div class="l">🌊 하천거리</div><div class="v">' + (a.rd != null ? (a.rd>=1000?(a.rd/1000).toFixed(1)+"km":a.rd+"m") : "—") + '</div></div>'
    + '</div></div>';

  html += '<div class="det-section"><h3>2030 구매 우선순위 매칭</h3><div class="donut-wrap"><canvas id="donutChart"></canvas></div>'
    + '<div class="priority-legend">'
    +   '<div class="row"><span class="dot" style="background:var(--cyan)"></span>직주근접 & 교통 <span class="pct">' + priorityCommute + '%</span></div>'
    +   '<div class="row"><span class="dot" style="background:var(--lime)"></span>인프라 & 편의성 <span class="pct">' + priorityInfra + '%</span></div>'
    +   '<div class="row"><span class="dot" style="background:#7a8585"></span>시세 차익 기대 <span class="pct">' + priorityValue + '%</span></div>'
    +   '<div class="row"><span class="dot" style="background:#3b4848"></span>기타 감성적 요인 <span class="pct">' + priorityEmo + '%</span></div>'
    + '</div></div>';

  html += '<div class="det-section"><div class="ai-hint"><b>HYPER-PERSONALIZATION</b><br/>과거 검색 패턴 · 클릭 스트림 · 실제 방문 데이터를 학습하여 시간이 갈수록 정교해지는 추천을 제공합니다.</div></div>'
    + '<div class="cta-row"><button class="cta secondary">📋 리포트 받기</button><button class="cta primary">🗓 가상 임장 예약</button></div>';

  panel.innerHTML = html;

  // bind pb tab clicks
  panel.querySelectorAll(".pb-tab").forEach(btn => {
    btn.onclick = () => {
      state.currentPb = parseInt(btn.dataset.pb, 10);
      renderDetail();
    };
  });

  // Chart
  if (cur && cur.tr.length >= 1) {
    const ctx1 = document.getElementById("priceChart");
    if (priceChart) priceChart.destroy();
    const labels = cur.tr.map(t => t[0].slice(2)); // YY-MM-DD short
    const data = cur.tr.map(t => t[1]);
    priceChart = new Chart(ctx1, {
      type: "line",
      data: { labels, datasets: [{
        data,
        borderColor: "#00E5FF",
        backgroundColor: (ctx) => {
          const g = ctx.chart.ctx.createLinearGradient(0, 0, 0, 160);
          g.addColorStop(0, "rgba(0,229,255,0.35)");
          g.addColorStop(1, "rgba(0,229,255,0)");
          return g;
        },
        fill: true, tension: 0.3, borderWidth: 2.5,
        pointRadius: 4, pointBackgroundColor: "#000", pointBorderColor: "#00E5FF", pointBorderWidth: 2,
        pointHoverRadius: 7, pointHoverBackgroundColor: "#C8FF00", pointHoverBorderColor: "#000", pointHoverBorderWidth: 2,
      }]},
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: "#0a1010", borderColor: "#243838", borderWidth: 1,
            titleColor: "#fff", bodyColor: "#C8FF00",
            callbacks: { label: c => c.parsed.y.toFixed(2) + "억원" }
          }
        },
        scales: {
          x: { grid: { display: false }, ticks: { color: "#7A8585", font: { size: 9 }, maxRotation: 0, autoSkipPadding: 12 } },
          y: { grid: { color: "#1B2A2A" }, ticks: { color: "#7A8585", font: { size: 10 }, callback: v => v + "억" } }
        }
      }
    });
  }

  const ctx2 = document.getElementById("donutChart");
  if (donutChart) donutChart.destroy();
  donutChart = new Chart(ctx2, {
    type: "doughnut",
    data: {
      labels: ["직주근접 & 교통", "인프라 & 편의성", "시세 차익", "감성 요인"],
      datasets: [{
        data: [priorityCommute, priorityInfra, priorityValue, priorityEmo],
        backgroundColor: ["#00E5FF", "#C8FF00", "#7A8585", "#3b4848"],
        borderColor: "#000", borderWidth: 3,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false, cutout: "68%",
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "#0a1010", borderColor: "#243838", borderWidth: 1,
          titleColor: "#fff", bodyColor: "#C8FF00",
          callbacks: { label: c => c.label + ": " + c.parsed + "%" }
        }
      }
    },
    plugins: [{
      id: "centerText",
      afterDraw(chart) {
        const { ctx, chartArea } = chart;
        const x = (chartArea.left + chartArea.right) / 2;
        const y = (chartArea.top + chartArea.bottom) / 2;
        ctx.save();
        ctx.fillStyle = "#F2F4F4";
        ctx.font = "bold 11px Inter, Pretendard, sans-serif";
        ctx.textAlign = "center"; ctx.textBaseline = "middle";
        ctx.fillText("MZ PRIORITY", x, y - 4);
        ctx.fillStyle = "#7A8585";
        ctx.font = "9px Inter, Pretendard, sans-serif";
        ctx.fillText("매칭 가중치", x, y + 12);
        ctx.restore();
      }
    }]
  });
}

document.getElementById("chipFilters").addEventListener("click", (e) => {
  const t = e.target.closest(".chip");
  if (!t) return;
  document.querySelectorAll("#chipFilters .chip").forEach(c => c.classList.remove("active"));
  t.classList.add("active");
  state.filter = t.dataset.filter;
  renderList();
});
document.querySelectorAll(".sort-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".sort-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    state.sort = btn.dataset.sort;
    renderList();
  });
});
let searchTO;
document.getElementById("searchInput").addEventListener("input", () => {
  clearTimeout(searchTO);
  searchTO = setTimeout(() => renderList(), 180);
});
document.getElementById("priceToggle").addEventListener("click", () => {
  state.pricedOnly = !state.pricedOnly;
  document.getElementById("priceToggle").classList.toggle("on", state.pricedOnly);
  renderList();
  rebuildMarkers();
});
document.getElementById("syncToggle").addEventListener("click", () => {
  state.syncMap = !state.syncMap;
  document.getElementById("syncToggle").classList.toggle("on", state.syncMap);
});

async function bootstrap() {
  const sub = document.getElementById("loaderSub");
  sub.textContent = "데이터 초기화 중...";
  try {
    const t0 = performance.now();
    if (!window.APTS_DATA) {
      sub.textContent = "apts.json 다운로드 중...";
      const r = await fetch("./apts.json");
      if (!r.ok) throw new Error("apts.json fetch failed: " + r.status);
      ALL = await r.json();
    } else {
      ALL = window.APTS_DATA;
    }
    PRICED = ALL.filter(a => a.p != null);
    const ms = Math.round(performance.now() - t0);
    sub.textContent = ALL.length.toLocaleString() + "개 단지 로드 완료 (" + ms + "ms)";
    document.getElementById("dsTotal").textContent = ALL.length.toLocaleString();
    document.getElementById("dsPriced").textContent = PRICED.length.toLocaleString();
    const sorted = [...PRICED].sort((a,b) => (b.ai||0) - (a.ai||0));
    state.selected = sorted[0] ? sorted[0].i : (ALL[0] ? ALL[0].i : null);
    initMap();
    rebuildMarkers();
    renderList();
    renderDetail();
    if (state.syncMap) flyToSelected();
    refreshSelectedMarker();
    setTimeout(() => {
      const ld = document.getElementById("loader");
      if (!ld) return;
      ld.style.transition = "opacity 0.3s";
      ld.style.opacity = "0";
      setTimeout(() => ld.remove(), 350);
    }, 200);
  } catch (e) {
    sub.textContent = "데이터 로드 실패 — " + e.message;
    sub.style.color = "var(--danger)";
    console.error(e);
  }
}

bootstrap();
