/* 조립.
 *
 * 레벨(시군구/읍면동)은 줌으로 자동 전환하되, 버튼으로 고른 경우에는 그
 * 선택을 존중한다. 줌만으로 바꾸면 "방금 읍면동을 봤는데 왜 돌아갔지"가 된다.
 */
(async function () {
  const AUTO_ZOOM = 12;     // 이 줌부터 읍면동
  let META, level = 'sgg', pinned = false;

  META = await U.json('/api/meta');
  Panel.setMeta(META, pickRegion);
  Panel.limits(META);

  U.$('#foot').innerHTML = `
    ${U.esc(META.source)}.<br>
    마지막 거래 ${U.esc(META.asof)} · 기준 주 ${U.esc(META.cur_week)}
    (신고 지연 ${META.lag_days}일 반영).<br><br>
    ${U.esc(META.disclaimer)}`;

  MapView.init(META.palette, r => openRegion(r.code));
  MapView.on('moveend', U.debounce(refresh, 180));

  U.$$('.lv').forEach(b => b.onclick = () => {
    pinned = true;
    setLevel(b.dataset.level);
  });

  U.$('#close').onclick = () => { U.$('#drawer').hidden = true; };

  await refresh();
  await loadExtremes();

  /* ── 지도 갱신 ─────────────────────────────────────────────── */
  async function refresh() {
    if (!pinned) {
      const want = MapView.zoom() >= AUTO_ZOOM ? 'dong' : 'sgg';
      if (want !== level) { level = want; syncButtons(); loadExtremes(); }
    }
    const d = await U.json(`/api/regions?level=${level}&bbox=${MapView.bbox()}`);
    // 읍면동 이름은 배경 타일이 이미 찍어 준다. 우리 라벨까지 얹으면 같은
    // 글자가 두 겹으로 보여 지도가 지저분해진다. 시군구에서만 쓴다.
    MapView.draw(d.items, { labels: level === 'sgg' && MapView.zoom() >= 10 });
    statebar(d);
  }

  function statebar(d) {
    const judged = d.items.filter(r => r.state !== 'thin' && r.state !== 'unknown');
    const odd = judged.filter(r => r.state !== 'normal');
    U.$('#statebar').innerHTML = judged.length
      ? `화면 안 ${META.levels[level].label} ${d.items.length}곳 · 판단 ${judged.length}곳 중
         <b>${odd.length}곳</b>이 평소와 다릅니다 · ${U.esc(d.window)} 기준`
      : `화면 안에 판단할 만큼 거래가 있는 ${META.levels[level].label}이 없습니다.`;
  }

  function setLevel(lv) {
    if (lv === level) return;
    level = lv; syncButtons(); refresh(); loadExtremes();
  }

  function syncButtons() {
    U.$$('.lv').forEach(b => b.classList.toggle('on', b.dataset.level === level));
  }

  /* ── 양 끝 ─────────────────────────────────────────────────── */
  async function loadExtremes() {
    const e = await U.json(`/api/extremes?level=${level}&n=5`);
    Panel.headline(e.distribution, level);
    Panel.ranklist(U.$('#busy'), e.busy, 'busy');
    Panel.ranklist(U.$('#quiet'), e.quiet, 'quiet');
  }

  function pickRegion(code) { openRegion(code); }

  async function openRegion(code) {
    const d = await U.json(`/api/region/${level}/${code}`);
    Panel.detail(d);
    // 레벨에 맞는 줌으로만 간다. 시군구를 열었는데 AUTO_ZOOM 을 넘겨 버리면
    // 지도가 읍면동으로 자동 전환되면서 **왼쪽 목록이 통째로 바뀐다** —
    // 방금 누른 항목이 사라지는 것처럼 보인다.
    if (d.now.lat) MapView.flyTo(d.now.lat, d.now.lng,
      level === 'sgg' ? AUTO_ZOOM - 1 : 13);
  }

  /* ── 검색 ──────────────────────────────────────────────────── */
  const q = U.$('#q'), sug = U.$('#suggest');
  q.oninput = U.debounce(async () => {
    const v = q.value.trim();
    if (v.length < 1) { sug.classList.remove('on'); return; }
    const r = await U.json(`/api/search?q=${encodeURIComponent(v)}&limit=6`);
    const items = [
      ...r.regions.map(x => ({
        t: x.name, s: `${x.region} · ${META.levels[x.level].label}`,
        go: () => { setLevel(x.level); openRegion(x.code); }
      })),
      ...r.apts.map(x => ({
        t: x.apt_name, s: `${x.sigungu_name} ${x.legal_dong_name}`,
        go: () => MapView.flyTo(x.lat, x.lng, 15)
      })),
    ];
    sug.innerHTML = items.length
      ? items.map((it, i) => `<li data-i="${i}">${U.esc(it.t)}<small>${U.esc(it.s)}</small></li>`).join('')
      : '<li><small>결과가 없어요</small></li>';
    sug.classList.add('on');
    U.$$('li[data-i]', sug).forEach(li => li.onclick = () => {
      items[+li.dataset.i].go();
      sug.classList.remove('on'); q.blur();
    });
  });
  document.addEventListener('click', e => {
    if (!U.$('#searchbox').contains(e.target)) sug.classList.remove('on');
  });
})();
