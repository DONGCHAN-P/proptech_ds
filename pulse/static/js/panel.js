/* 좌측 패널과 상세 서랍의 그리기.
 *
 * 여기서 지키는 것
 *   · 표본(n)을 뺀 숫자를 그리지 않는다
 *   · "평소"가 무엇인지 같은 화면에 적는다
 *   · 양 끝을 같이 보여준다 — 붐빈 쪽만 보여주면 "거래가 늘고 있다"로 읽힌다
 */
const Panel = (() => {
  let META = {}, onPick = () => { };

  const setMeta = (m, pick) => { META = m; onPick = pick; };

  const stateColor = r =>
    (r.state === 'thin' || r.state === 'unknown')
      ? META.palette.flat : META.palette[r.dir];

  /* ── 헤드라인 ──────────────────────────────────────────────────
     이 사이트가 하는 말을 한 문장으로. 대부분의 지역이 "평소대로"라는 게
     보통의 진실인데, 그걸 말하는 부동산 서비스가 거의 없다. */
  function headline(dist, level) {
    const total = dist.reduce((s, d) => s + d.n, 0);
    const byState = Object.fromEntries(dist.map(d => [d.state, d.n]));
    const lv = META.levels[level];
    const normal = (byState.normal || 0);
    const judged = total - (byState.thin || 0) - (byState.unknown || 0);

    const order = ['hot', 'churn', 'thin_rise', 'quiet', 'normal', 'thin', 'unknown'];
    // 달아오름과 손바뀜은 둘 다 "거래가 늘었다"라 같은 빨강 계열이되,
    // 값까지 빠른 쪽(hot)을 진하게 둬서 구분한다.
    const col = { hot: META.palette.up, churn: META.palette.up + 'B0',
                  thin_rise: META.palette.accent,
                  quiet: META.palette.down, normal: META.palette.flat,
                  thin: META.palette.thin, unknown: META.palette.thin };

    const bars = order.filter(s => byState[s]).map(s =>
      `<i style="flex:${byState[s]};background:${col[s]}"></i>`).join('');
    const chips = order.filter(s => byState[s]).map(s =>
      `<span><em style="background:${col[s]}"></em>${U.esc(META.states[s].label)} ${byState[s]}</span>`
    ).join('');

    U.$('#headline').innerHTML = `
      <div class="big">${U.esc(lv.window)} 수도권 ${lv.label} ${total}곳 가운데<br>
        <b>${normal}곳은 평소대로</b>였어요.</div>
      <div class="sub">판단한 ${judged}곳 중 ${judged - normal}곳만 자기 평소 범위를
        벗어났습니다. ‘평소’는 그 지역의 지난 ${META.hist_weeks}주예요 —
        다른 지역과 비교한 값이 아닙니다.</div>
      <div class="bars">${bars}</div>
      <div class="dist">${chips}</div>`;
  }

  /* ── 순위 목록 ─────────────────────────────────────────────── */
  function ranklist(el, items, kind) {
    el.innerHTML = items.map(r => {
      const cls = kind === 'busy' ? 'up' : 'down';
      return `<li data-code="${U.esc(r.code)}">
        <div class="nm">${U.esc(r.name)}
          <small>${U.esc(r.region)} · 거래 ${r.deals}건 (평소 ${U.num(r.deals_usual)}건)</small>
        </div>
        <div class="val ${cls}">평소의 ${U.times(r.ratio)}
          <small>${U.esc(META.states[r.state]?.label || '')}</small>
        </div>
      </li>`;
    }).join('');
    U.$$('li', el).forEach(li =>
      li.onclick = () => onPick(li.dataset.code));
  }

  /* ── 스파크라인 ────────────────────────────────────────────────
     막대 = 주간 거래 건수, 가로선 = 그 시점의 "평소". 선을 넘은 막대만
     진하게 칠한다 — 초과분이 읽혀야 "평소와 다르다"가 보인다. */
  function spark(series) {
    const S = series.filter(d => d.deals != null);
    if (S.length < 4) return '<p class="spark-cap">그릴 만큼의 기록이 없어요.</p>';
    const W = 372, H = 92, pad = 4;
    const max = Math.max(...S.map(d => Math.max(d.deals, d.deals_usual || 0))) || 1;
    const bw = (W - pad * 2) / S.length;
    const y = v => H - 14 - (v / max) * (H - 24);

    const bars = S.map((d, i) => {
      const over = d.deals_usual != null && d.deals > d.deals_usual;
      const h = Math.max(1, (H - 14) - y(d.deals));
      return `<rect x="${(pad + i * bw).toFixed(1)}" y="${y(d.deals).toFixed(1)}"
        width="${Math.max(1, bw - 1).toFixed(1)}" height="${h.toFixed(1)}" rx="1"
        fill="${over ? META.palette.up : META.palette.flat}"
        opacity="${over ? .9 : .65}"></rect>`;
    }).join('');

    const line = S.map((d, i) => d.deals_usual == null ? null
      : `${i ? 'L' : 'M'}${(pad + i * bw + bw / 2).toFixed(1)},${y(d.deals_usual).toFixed(1)}`)
      .filter(Boolean).join(' ');

    return `<svg class="spark" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none">
      ${bars}
      <path d="${line}" fill="none" stroke="${META.palette.ink}"
            stroke-width="1.5" stroke-dasharray="3 3" opacity=".65"/>
    </svg>
    <p class="spark-cap">막대 = 주간 거래 건수 · 점선 = 그때의 ‘평소’.
      최근 ${S.length}주 — 비교에 쓰는 구간과 같습니다. 왼쪽이 과거예요.</p>`;
  }

  /* ── 상세 ──────────────────────────────────────────────────── */
  function detail(d) {
    const r = d.now, st = META.states[r.state] || {};
    const thin = r.state === 'thin' || r.state === 'unknown';

    const apts = d.apts.slice(0, 12).map(a => `
      <li class="${a.thin ? 'thin' : ''}">
        <div class="nm">${U.esc(a.apt_name)}
          <small>${U.esc(a.legal_dong_name || '')}${a.build_year ? ' · ' + a.build_year + '년' : ''}
            · 최근 ${a.n_recent}건 / 직전 ${a.n_prior}건${a.thin ? '<span class="badge">표본 적음</span>' : ''}</small>
        </div>
        <div class="val ${U.dirOf(a.chg, .5)}">${U.pct(a.chg)}
          <small>평당 ${U.ppy(a.ppy)}</small>
        </div>
      </li>`).join('');

    U.$('#detail').innerHTML = `
      <div class="d-kicker">${U.esc(r.region || '')} · ${U.esc(d.window)} (${U.esc(r.week_start)} 기준)</div>
      <div class="d-name">${U.esc(r.name)}</div>

      <div class="d-state"><i style="background:${stateColor(r)}"></i>${U.esc(st.label || '')}</div>
      <div class="d-desc">${U.esc(st.desc || '')}</div>

      <div class="d-rows">
        <div class="d-row">
          <div class="k">거래 건수<small>평소 ${U.num(r.deals_usual)}건</small></div>
          <div class="v ${thin ? 'flat' : r.dir}">${U.num(r.deals)}건
            <small>${thin ? '판단 보류' : '평소의 ' + U.times(r.ratio)}</small></div>
        </div>
        <div class="d-row">
          <div class="k">평단가 3개월 변화<small>이 지역의 평소 변화는 ${U.pct(r.chg_usual)}</small></div>
          <div class="v ${U.dirOf(r.chg, .5)}">${U.arrow(r.chg)}${U.pct(r.chg)}
            <small>지금 ${U.ppy(r.ppy)}/평</small></div>
        </div>
        <div class="d-row">
          <div class="k">비교에 쓴 과거<small>자기 과거만 씁니다</small></div>
          <div class="v">${r.hist_weeks}주</div>
        </div>
      </div>

      <div class="d-h">주간 거래 건수</div>
      ${spark(d.series)}

      <div class="d-h">이 안의 단지 — 최근 90일 vs 직전 90일</div>
      ${apts ? `<ul class="aptlist">${apts}</ul>`
        : '<p class="spark-cap">최근 90일과 직전 90일 모두에 거래가 있는 단지가 없어요.</p>'}

      <p class="disc">${U.esc(META.source)}.
        계약 후 30일 안에 신고라 최근 주는 집계가 덜 찹니다.
        그래서 ${META.lag_days}일 물린 주를 봅니다.<br><br>
        ${U.esc(META.disclaimer)}</p>`;
    U.$('#drawer').hidden = false;
  }

  /* ── 범례 — 레벨마다 색의 뜻이 다르다 ─────────────────────────
     지역에서는 색이 거래량, 단지에서는 90일 전 대비 값의 변화다. 같은 빨강이
     다른 뜻이면 범례를 외워야 읽히는 지도가 되므로, 지금 뭘 보고 있는지에
     맞춰 범례를 바꿔 단다. */
  const LEGEND = {
    region: {
      rows: [
        ['dot up', '거래가 평소보다 <b>많음</b>'],
        ['dot flat', '평소 수준'],
        ['dot down', '거래가 평소보다 <b>적음</b>'],
        ['dot thin', '거래가 적어 판단 보류'],
        ['dot ring', '테두리 = 값이 평소보다 <b>빠르게</b> 오름'],
        ['dot size', '원 크기 = 그 기간 거래 건수'],
      ],
      note: '색은 거래량만 나타냅니다. 값의 움직임은 테두리로 따로 표시합니다.',
    },
    apt: {
      rows: [
        ['dot up', '90일 전보다 평당가 <b>오름</b>'],
        ['dot flat', '거의 그대로 (±1% 안)'],
        ['dot down', '90일 전보다 평당가 <b>내림</b>'],
        ['dot thin', '거래가 적어 비교 보류 (점선)'],
      ],
      note: '말풍선 숫자는 <b>그 평형의 마지막 실거래가</b>입니다. 추정가가 '
          + '아니라 신고된 금액이에요. 평형이 다르면 가격도 달라서 평형을 '
          + '같이 적습니다.',
    },
  };

  function legend(level) {
    const L = LEGEND[level === 'apt' ? 'apt' : 'region'];
    U.$('#legend ul').innerHTML = L.rows
      .map(([c, t]) => `<li><i class="${c}"></i> ${t}</li>`).join('');
    U.$('#legend .note').innerHTML = L.note;
  }

  /* ── 단지 상세 — 평형을 접지 않는다 ────────────────────────── */
  function aptDetail(d) {
    const a = d.apt;
    const rows = d.pyeongs.map(p => `
      <div class="pyrow ${p.thin ? 'thin' : ''}">
        <div class="k">${U.esc(p.pyeong_label)}
          <small>${p.last_area ? p.last_area.toFixed(0) + '㎡ · ' : ''}${U.esc(p.last_floor || '')}
            · ${U.ymd(p.last_date)} · 1년 ${p.n_1y}건</small>
        </div>
        <div class="pr">${U.won(p.last_price)}
          <small>평당 ${U.ppy(p.last_ppy)}</small>
        </div>
        <div class="ch ${p.thin ? 'flat' : p.dir}">
          ${p.thin ? '–' : U.pct(p.chg)}
          <small>${p.thin ? `${p.n_recent}/${p.n_prior}건` : '90일 전'}</small>
        </div>
      </div>`).join('');

    const r = d.region;
    const ctx = r ? `<div class="hint">
        이 단지가 있는 <b>${U.esc(r.name)}</b>은 최근 4주 거래가
        <b>평소의 ${U.times(r.ratio)}</b>예요
        (${r.deals}건 / 평소 ${U.num(r.deals_usual)}건) —
        ${U.esc(d.region_state.label || '')}.
        단지만 보면 동네가 통째로 움직인 건지 이 단지만 움직인 건지 알 수 없어요.
      </div>` : '';

    U.$('#detail').innerHTML = `
      <div class="d-kicker">${U.esc(a.sigungu_name)} ${U.esc(a.legal_dong_name || '')}${a.build_year ? ' · ' + a.build_year + '년 준공' : ''}</div>
      <div class="d-name">${U.esc(a.apt_name)}</div>

      <div class="d-rows">
        <div class="d-row">
          <div class="k">마지막 실거래<small>${U.esc(a.pyeong_label)} · ${U.esc(a.last_floor || '')} · ${U.ymd(a.last_date)}</small></div>
          <div class="v">${U.won(a.last_price)}<small>평당 ${U.ppy(a.last_ppy)}</small></div>
        </div>
        <div class="d-row">
          <div class="k">전고점 대비<small>${U.ymd(a.peak_date)} ${U.won(a.peak_price)}</small></div>
          <div class="v ${U.dirOf(a.vs_peak, .5)}">${U.pct(a.vs_peak)}</div>
        </div>
      </div>

      <div class="d-h">평형별 — 마지막 실거래와 90일 전 대비</div>
      <div class="pytable">${rows}</div>
      ${ctx}

      <p class="disc">${U.esc(META.source)}.
        표에 적힌 금액은 <b>신고된 실거래가</b>이고 추정가가 아닙니다.
        같은 평형이어도 층·향·수리 상태로 갈립니다.<br><br>
        ${U.esc(META.disclaimer)}</p>`;
    U.$('#drawer').hidden = false;
  }

  /* ── 단지 목록 (좌측) ──────────────────────────────────────── */
  function aptlist(el, items) {
    el.innerHTML = items.map(a => `
      <li data-apt="${U.esc(a.apt_id)}" class="${a.thin ? 'thin' : ''}">
        <div class="nm">${U.esc(a.apt_name)}
          <small>${U.esc(a.legal_dong_name || '')} · ${U.esc(a.pyeong_label)}
            · ${U.ymd(a.last_date)} · 1년 ${a.n_1y}건</small>
        </div>
        <div class="val">${U.won(a.last_price)}
          <small class="${a.thin ? '' : a.dir}">${a.thin ? '비교 보류' : U.pct(a.chg) + ' (90일)'}</small>
        </div>
      </li>`).join('');
    U.$$('li', el).forEach(li => li.onclick = () => onPick(li.dataset.apt));
  }

  function limits(meta) {
    U.$('#limits ul').innerHTML = [
      `<b>가격 수준이 아니라 변화 속도</b>를 봅니다. 비싼 동네인지 싼 동네인지는
       이 지도로 알 수 없어요.`,
      `거래 ${meta.min_deals}건 미만인 곳은 색을 칠하지 않습니다. 몇 건 차이로
       ‘평소의 3배’가 되기 때문이에요.`,
      `<b>배수가 커도 ‘평소대로’일 수 있어요.</b> 원래 주마다 들쭉날쭉한 지역은
       1.3배쯤은 평소 범위 안입니다. 그 지역이 평소 얼마나 흔들렸는지까지
       같이 보기 때문이에요.`,
      `읍면동은 주간 거래가 한 자릿수라 <b>${meta.dong_window}일</b>로 묶어 봅니다.
       시군구(7일)와 창이 달라요.`,
      `전세·월세는 들어 있지 않습니다. 매매 신고분만이에요.`,
      `해제(취소)된 신고는 빠져 있습니다. 재건축·분양권은 포함되지 않아요.`,
      `앞으로 오를지 내릴지는 말하지 않습니다. 지난 기록이 평소와 어떻게
       다른지만 보여줍니다.`,
    ].map(t => `<li>${t}</li>`).join('');
  }

  return { setMeta, headline, ranklist, detail, limits,
           legend, aptDetail, aptlist };
})();
