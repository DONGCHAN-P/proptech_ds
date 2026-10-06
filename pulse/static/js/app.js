/* 조립.
 *
 * 레벨은 셋이다.
 *   sgg   시군구 · 이번 주      평소 대비 거래량
 *   dong  읍면동 · 최근 4주     "
 *   apt   단지                  마지막 실거래가 + 90일 전 대비
 *
 * 줌으로 자동 전환하되 버튼으로 고른 경우에는 그 선택을 존중한다. 줌만으로
 * 바꾸면 "방금 단지를 보고 있었는데 왜 돌아갔지"가 된다.
 */
(async function () {
  const ZOOM_DONG = 12;     // 이 줌부터 읍면동
  const ZOOM_APT = 14;      // 이 줌부터 단지
  let META, level = 'sgg', pinned = false, pyeong = null;

  META = await U.json('/api/meta');
  Panel.setMeta(META, pick);
  Panel.limits(META);
  Panel.legend(level);
  renderPyeongChips();

  U.$('#foot').innerHTML = `
    ${U.esc(META.source)}.<br>
    마지막 거래 ${U.esc(META.asof)} · 기준 주 ${U.esc(META.cur_week)}
    (신고 지연 ${META.lag_days}일 반영).<br><br>
    ${U.esc(META.disclaimer)}`;

  MapView.init(META.palette, pick);
  MapView.on('moveend', U.debounce(refresh, 180));

  U.$$('.lv').forEach(b => b.onclick = () => {
    pinned = true;
    setLevel(b.dataset.level, true);
  });
  U.$('#close').onclick = () => { U.$('#drawer').hidden = true; };

  await refresh();

  /* ── 갱신 ──────────────────────────────────────────────────── */
  async function refresh() {
    if (!pinned) {
      const z = MapView.zoom();
      const want = z >= ZOOM_APT ? 'apt' : (z >= ZOOM_DONG ? 'dong' : 'sgg');
      if (want !== level) { level = want; afterLevel(); }
    }
    await (level === 'apt' ? drawApts() : drawRegions());
  }

  async function drawRegions() {
    const d = await U.json(`/api/regions?level=${level}&bbox=${MapView.bbox()}`);
    // 읍면동 이름은 배경 타일이 이미 찍어 준다. 겹쳐 쓰면 지저분하다.
    MapView.draw(d.items, { labels: level === 'sgg' && MapView.zoom() >= 10 });
    const judged = d.items.filter(r => r.state !== 'thin' && r.state !== 'unknown');
    const odd = judged.filter(r => r.state !== 'normal');
    U.$('#statebar').innerHTML = judged.length
      ? `화면 안 ${META.levels[level].label} ${d.items.length}곳 · 판단 ${judged.length}곳 중
         <b>${odd.length}곳</b>이 평소와 다릅니다 · ${U.esc(d.window)} 기준`
      : `화면 안에 판단할 만큼 거래가 있는 ${META.levels[level].label}이 없습니다.`;
    await loadExtremes();
  }

  const empty = msg =>
    `<li><div class="nm"><small>${msg}</small></div></li>`;

  async function drawApts() {
    const z = MapView.zoom();
    if (z < ZOOM_APT) {
      // 말풍선은 70px 쯤 된다. 줌 14 아래에서는 화면에 수백 개가 들어와
      // 서로를 덮어 숫자가 하나도 안 읽힌다. 억지로 그리지 않는다.
      MapView.draw([], {});
      U.$('#statebar').innerHTML =
        `단지 가격을 보려면 조금 더 확대하세요. <b>+ 버튼을 ${ZOOM_APT - z}번</b>
         누르면 됩니다 — 말풍선이 겹치지 않을 만큼 들어와야 숫자가 읽힙니다.`;
      U.$('#busy').innerHTML = empty('지도를 확대하면 이 화면의 단지가 나옵니다.');
      U.$('#quiet').innerHTML = '';
      U.$('#busyh').textContent = '단지';
      U.$('#quieth').textContent = '';
      return;
    }
    const qs = `bbox=${MapView.bbox()}` + (pyeong ? `&pyeong=${pyeong}` : '');
    const d = await U.json(`/api/apts?${qs}`);
    const { drawn, hidden } = MapView.drawApts(d.items, z);

    const label = pyeong ? META.pyeongs.find(p => p.code === pyeong).label : '대표 평형';
    const left = d.total - drawn;
    U.$('#statebar').innerHTML = left > 0
      ? `화면 안 단지 ${d.total}곳 중 <b>${drawn}곳</b>을 그렸습니다
         (${U.esc(label)} 기준) · 겹치는 자리는 거래가 많은 단지를 남겼어요.
         더 확대하면 나머지가 보입니다`
      : `화면 안 단지 <b>${d.total}곳</b> · ${U.esc(label)} 기준 마지막 실거래가`;

    // 좌측은 오른 단지 / 내린 단지. **부호로 가른다** — 전부 올랐는데
    // 아래에서 다섯 개를 집어 "많이 내린 단지"라고 달면 그 제목이 거짓말이다.
    const cmp = d.items.filter(a => !a.thin && a.chg != null);
    const up = cmp.filter(a => a.chg > 0).sort((a, b) => b.chg - a.chg).slice(0, 5);
    const dn = cmp.filter(a => a.chg < 0).sort((a, b) => a.chg - b.chg).slice(0, 5);
    U.$('#busyh').textContent = '90일 전보다 오른 단지';
    U.$('#quieth').textContent = '90일 전보다 내린 단지';
    Panel.aptlist(U.$('#busy'), up);
    Panel.aptlist(U.$('#quiet'), dn);
    if (!up.length) U.$('#busy').innerHTML = empty(
      cmp.length ? '이 화면에는 오른 단지가 없어요.'
                 : '이 화면에는 90일 비교가 가능한 단지가 없어요 (거래가 적어서요).');
    if (!dn.length) U.$('#quiet').innerHTML = empty(
      cmp.length ? '이 화면에는 내린 단지가 없어요.' : '');
  }

  async function loadExtremes() {
    const e = await U.json(`/api/extremes?level=${level}&n=5`);
    Panel.headline(e.distribution, level);
    U.$('#busyh').textContent = '평소보다 붐빈 곳';
    U.$('#quieth').textContent = '평소보다 조용한 곳';
    Panel.ranklist(U.$('#busy'), e.busy, 'busy');
    Panel.ranklist(U.$('#quiet'), e.quiet, 'quiet');
  }

  function setLevel(lv, fromClick) {
    if (lv === level) return;
    level = lv; afterLevel();
    // 단지 레벨인데 줌이 낮으면 아무것도 안 보인다. 버튼으로 고른 경우엔
    // 보이는 데까지 데려다준다.
    if (fromClick && lv === 'apt' && MapView.zoom() < ZOOM_APT) {
      MapView.flyTo(...center(), ZOOM_APT);   // 바로 읽히는 줌까지 데려다준다
      return;   // moveend 가 refresh 를 부른다
    }
    refresh();
  }

  function center() {
    const b = MapView.bbox().split(',').map(Number);
    return [(b[1] + b[3]) / 2, (b[0] + b[2]) / 2];
  }

  function afterLevel() {
    U.$$('.lv').forEach(b => b.classList.toggle('on', b.dataset.level === level));
    U.$('#pyeongbar').hidden = level !== 'apt';
    U.$('#headline').hidden = level === 'apt';
    Panel.legend(level);
  }

  /* ── 평형 ──────────────────────────────────────────────────── */
  function renderPyeongChips() {
    const el = U.$('#pyeongs');
    el.innerHTML = `<button class="chip on" data-py="">대표 평형</button>` +
      META.pyeongs.map(p =>
        `<button class="chip" data-py="${p.code}">${U.esc(p.label)}</button>`).join('');
    U.$$('.chip', el).forEach(c => c.onclick = () => {
      pyeong = c.dataset.py || null;
      U.$$('.chip', el).forEach(x => x.classList.toggle('on', x === c));
      U.$('#pyeongnote').innerHTML = pyeong
        ? '이 평형의 거래가 있는 단지만 보입니다.'
        : '단지마다 <b>최근 1년 거래가 가장 많은 평형</b>으로 보여줍니다.';
      refresh();
    });
    U.$('#pyeongnote').innerHTML =
      '단지마다 <b>최근 1년 거래가 가장 많은 평형</b>으로 보여줍니다.';
  }

  /* ── 선택 ──────────────────────────────────────────────────── */
  function pick(x) {
    if (level === 'apt') return openApt(typeof x === 'string' ? x : x.apt_id);
    openRegion(typeof x === 'string' ? x : x.code);
  }

  async function openApt(id) {
    Panel.aptDetail(await U.json(`/api/apt/${id}`));
  }

  async function openRegion(code) {
    const d = await U.json(`/api/region/${level}/${code}`);
    Panel.detail(d);
    // 레벨에 맞는 줌으로만 간다. 넘겨 버리면 지도가 자동 전환되면서 왼쪽
    // 목록이 통째로 바뀌어, 방금 누른 항목이 사라진 것처럼 보인다.
    if (d.now.lat) MapView.flyTo(d.now.lat, d.now.lng,
      level === 'sgg' ? ZOOM_DONG - 1 : ZOOM_APT - 1);
  }

  /* ── 검색 ──────────────────────────────────────────────────── */
  const q = U.$('#q'), sug = U.$('#suggest');
  q.oninput = U.debounce(async () => {
    const v = q.value.trim();
    if (!v) { sug.classList.remove('on'); return; }
    const r = await U.json(`/api/search?q=${encodeURIComponent(v)}&limit=6`);
    const items = [
      ...r.regions.map(x => ({
        t: x.name, s: `${x.region} · ${META.levels[x.level].label}`,
        go: () => { pinned = true; setLevel(x.level); openRegion(x.code); }
      })),
      ...r.apts.map(x => ({
        t: x.apt_name, s: `${x.sigungu_name} ${x.legal_dong_name}`,
        go: () => {
          pinned = true; setLevel('apt'); afterLevel();
          MapView.flyTo(x.lat, x.lng, 16); openApt(x.apt_id);
        }
      })),
    ];
    sug.innerHTML = items.length
      ? items.map((it, i) => `<li data-i="${i}">${U.esc(it.t)}<small>${U.esc(it.s)}</small></li>`).join('')
      : '<li><small>결과가 없어요</small></li>';
    sug.classList.add('on');
    U.$$('li[data-i]', sug).forEach(li => li.onclick = () => {
      items[+li.dataset.i].go(); sug.classList.remove('on'); q.blur();
    });
  });
  document.addEventListener('click', e => {
    if (!U.$('#searchbox').contains(e.target)) sug.classList.remove('on');
  });
})();
