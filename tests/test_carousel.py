"""T16 — 캐러셀 검증.

이미지에 박히는 글자도 발행되는 문구다. 텍스트와 같은 기준으로 검사한다.

썸네일(16:9)은 이 모듈에서 빠졌다. 지시사항상 16:9 는 유튜브 전용이고,
유튜브는 T13(영상)에서 다룬다. 그 전까지 쓰지 않는 규격을 만들지 않는다.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from content import carousel as C  # noqa: E402
from content import design as D  # noqa: E402
from content.validator import check_banned, check_floor_exposure, validate  # noqa: E402


@pytest.fixture(scope="module")
def data() -> dict:
    files = sorted((ROOT / "output").glob("metrics_*.json"))
    if not files:
        pytest.skip("지표 JSON 없음")
    return json.loads(files[-1].read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def outdir(data) -> Path:
    return ROOT / "output" / data["asof"]


@pytest.fixture(scope="module")
def cards(data, outdir) -> list[dict]:
    c = C.build_cards(data, outdir)
    if not c:
        pytest.skip("재료 부족")
    return c


# ── 장수·규격 ────────────────────────────────────────────────────────────
def test_캐러셀은_5에서_8장(cards):
    """로드맵 규격. 너무 적으면 밀도가 없고 많으면 안 넘긴다."""
    assert 5 <= len(cards) <= 8, len(cards)


def test_캔버스가_4대5():
    """피드에서 1:1 보다 세로를 20% 더 차지한다."""
    assert (D.W, D.H) == (1080, 1350)
    assert abs(D.W / D.H - 4 / 5) < 0.01


def test_핵심요소가_프로필_크롭_안에_들어간다():
    """프로필 그리드는 3:4 로 자른다 — 1350 높이면 가운데 1012px 만 남는다.

    좌우 여백이 그보다 좁으면 글자가 잘린다. 본문 폭이 SAFE_CORE 안에
    들어가는지로 본다.
    """
    assert D.SAFE_CORE <= round(D.H * 3 / 4) + 1, "안전폭이 3:4 크롭보다 넓다"
    assert D.W - 2 * D.PAD_X <= D.SAFE_CORE, "본문이 크롭 밖으로 나간다"


# ── 레이아웃 ─────────────────────────────────────────────────────────────
def test_같은_레이아웃이_연속되지_않는다(cards):
    """7장이 같은 틀이면 넘길 이유가 없어진다."""
    assert not C.check_layout_variety(cards)


def test_레이아웃이_최소_네_종류(cards):
    assert len({c["layout"] for c in cards}) >= 4


# ── 문구 안전 ────────────────────────────────────────────────────────────
def test_이미지_문구에_금지표현이_없다(cards):
    for c in cards:
        t = C.strip_html(c["html"])
        assert not check_banned(t), f"{c['name']}: {check_banned(t)}"


def test_이미지_문구에_정확한_층수가_없다(cards):
    for c in cards:
        t = C.strip_html(c["html"])
        assert not check_floor_exposure(t), c["name"]


def test_이미지_숫자가_전부_출처가_있다(cards):
    for c in cards:
        t = C.strip_html(c["html"])
        r = validate(t, c["facts"], require_disclaimer=False)
        assert r.ok, f"{c['name']}: {r.reasons}"


def test_카드에_통계용어가_없다(cards):
    """σ·표준편차는 '평소의 1.7배'로 번역해 쓴다."""
    for c in cards:
        D.assert_no_jargon(C.strip_html(c["html"]), c["name"])


def test_자극적인_수식어가_없다(cards):
    assert not C.check_copy(cards)


def test_마지막_카드에_면책이_있다(cards):
    from templates.disclaimers import DISCLAIMER_SOCIAL
    last = C.strip_html(cards[-1]["html"])
    assert DISCLAIMER_SOCIAL.replace(" ", "") in last.replace(" ", "")


def test_출처가_모든_카드에_있다(cards):
    """마지막 장은 면책이 출처를 대신한다."""
    for c in cards[:-1]:
        assert "국토교통부" in C.strip_html(c["html"]), c["name"]


def test_모든_카드에_계정_핸들이_있다(cards):
    """캡처되어 퍼져도 출처 계정을 알 수 있어야 한다."""
    for c in cards:
        assert D.HANDLE in c["html"], c["name"]


# ── 반대 지표 (핵심) ─────────────────────────────────────────────────────
def test_캐러셀에_반대지표_카드가_있다(cards):
    names = [c["name"] for c in cards]
    assert any("counter" in n for n in names), names


def test_표본을_숨기지_않는다(cards):
    """비율·배수를 쓴 장은 **그 수가 몇 건으로 나온 건지** 같이 적는다.

    표본 경고를 따로 한 장으로 두던 걸 뺐다 — 같은 단지가 3장 연속이 돼서
    (지시사항 5항: 한 대상 최대 2장). 대신 각 장이 자기 표본을 들고 다닌다.
    빠뜨리면 여기서 걸린다.
    """
    want = {"05_compare": ("top", "deals_recent"),
            "06_newhigh": ("new_high", "history_count")}
    seen = 0
    for c in cards:
        key = want.get(c["name"])
        if not key:
            continue
        row = (c["facts"]["card"] or {}).get(key[0])
        if not row:
            continue
        n = row[key[1]]
        text = C.strip_html(c["html"])
        assert f"{n:,}건" in text or f"{n}건" in text, f"{c['name']}: 표본 {n} 누락"
        seen += 1
    assert seen, "표본을 들고 다녀야 할 장이 하나도 없다"


def test_비교에는_양쪽_값을_모두_쓴다(cards):
    """지시사항 9항. '거래 9건'만 쓰면 늘었는지 줄었는지 알 수 없다."""
    c = next((c for c in cards if c["name"] == "05_compare"), None)
    if c is None:
        pytest.skip("비교 장 없음")
    s = c["facts"]["card"]["top"]
    text = C.strip_html(c["html"])
    assert f'{s["deals_prior"]}건 → {s["deals_recent"]}건' in text, text[:200]


def test_큰숫자_장은_표본이_충분한_값만_쓴다(data):
    """연천군 7건으로 '평소의 2.4배'를 뽑으면 거짓말이 된다."""
    t = C.pick(data)
    if t is None:
        pytest.skip("재료 부족")
    z = data["weekly"]["sgg_zscore"]
    if any(r["week_deals"] >= C.MIN_SAMPLE for r in z if r.get("deals_avg_52w")):
        assert t["busiest"]["week_deals"] >= C.MIN_SAMPLE


# ── 이미지 출처 ──────────────────────────────────────────────────────────
def test_생성_이미지를_쓰지_않는다():
    """실사풍 건물 이미지는 실제 단지 오인을 부른다 (로드맵 규칙)."""
    src = (ROOT / "content" / "carousel.py").read_text(encoding="utf-8")
    for 금지 in ("fal.ai", "fal_client", "FAL_KEY", "dall-e", "midjourney",
                 "stable-diffusion", "text2img"):
        assert 금지 not in src, f"이미지 생성 흔적: {금지}"


def test_외부_이미지를_참조하지_않는다(cards):
    """렌더 시점에 네트워크를 타면 그날 발행이 네트워크에 걸린다."""
    for c in cards:
        for m in re.finditer(r'src="([^"]+)"', c["html"]):
            assert not m.group(1).startswith("http"), (
                f"{c['name']} 외부 이미지 참조: {m.group(1)[:40]}")


def test_카드에_차트PNG를_끼우지_않는다(cards):
    """완성된 4:5 차트를 카드에 넣으면 제목·출처가 중복되고 높이가 안 맞는다.

    T11 의 단독 차트는 스레드에 붙이는 1~2장으로 쓴다.
    """
    for c in cards:
        assert "<img" not in c["html"], f"{c['name']} 에 이미지가 들어갔다"


def test_같은_그래프를_두_번_보여주지_않는다(cards):
    """지역 순위를 2장과 4장에 각각 그리던 시절의 회귀를 막는다."""
    bars = [c["name"] for c in cards if c["layout"] == "ranked_bars"]
    assert len(bars) <= 1, bars


def test_양_끝을_같이_보여준다(cards):
    """붐빈 쪽만 보여주면 '수도권 거래가 늘었다'로 읽힌다."""
    ex = next((c for c in cards if c["name"] == "03_extremes"), None)
    assert ex is not None, [c["name"] for c in cards]
    html = ex["html"]
    assert 'class="v up"' in html and 'class="v down"' in html, (
        "증감 양쪽이 같은 장에 없다")


# ── 렌더 산출물 ──────────────────────────────────────────────────────────
def test_렌더된_파일이_존재한다(outdir, cards):
    missing = [c["name"] for c in cards
               if not (outdir / f"{c['name']}.png").exists()]
    if missing:
        pytest.skip(f"아직 렌더 안 됨: {missing[:3]}")
    for c in cards:
        p = outdir / f"{c['name']}.png"
        assert p.stat().st_size > 8_000, f"{p.name} 이 너무 작다 (빈 이미지?)"


# ── 지시사항 적합성 (한 번 고친 건 다시 무너지지 않게) ──────────────────
def test_계정_핸들이_인스타에서_쓸_수_있는_형식(cards):
    """인스타 사용자명은 영문·숫자·_·. 만 된다. 한글·공백 핸들은 존재할 수 없다."""
    assert re.fullmatch(r"@[A-Za-z0-9._]+", D.HANDLE), D.HANDLE
    for c in cards:
        assert D.HANDLE in c["html"], c["name"]


def test_한_장에_의미색이_둘을_넘지_않는다(cards):
    """빨강·파랑·형광펜을 한 장에 다 쓰면 '증감'이라는 신호가 묻힌다 (3항)."""
    for c in cards:
        h = c["html"]
        used = set()
        if re.search(r'class="[^"]*\bup\b', h):
            used.add("up")
        if re.search(r'class="[^"]*\bdown\b', h):
            used.add("down")
        if 'class="mark"' in h:
            used.add("accent")
        assert len(used) <= 2, f"{c['name']}: 의미색 {used}"


def test_같은_대상이_3장_연속_나오지_않는다(cards):
    """세 장째면 "아직도 이 단지야?"가 된다 (5항: 한 대상 최대 2장)."""
    def subjects(c) -> set:
        out = set()
        for v in (c["facts"]["card"] or {}).values():
            if isinstance(v, dict):
                out |= {v[k] for k in ("apt_name", "sigungu_name") if v.get(k)}
        return out
    subs = [subjects(c) for c in cards]
    for i in range(len(subs) - 2):
        common = subs[i] & subs[i + 1] & subs[i + 2]
        assert not common, f"{cards[i]['name']}~{cards[i+2]['name']}: {common}"


def test_내부_평형코드가_화면에_새지_않는다(cards):
    """'15P' 가 무슨 뜻인지 아는 건 이 파이프라인을 만든 사람뿐이다."""
    for c in cards:
        m = re.search(r"\b\d{2}P\b", C.strip_html(c["html"]))
        assert not m, f"{c['name']}: 평형 코드 '{m.group(0)}' 노출"


@pytest.mark.parametrize("bucket,label", [
    ("10P", "10평대"), ("15P", "10평대 후반"), ("30P", "30평대"),
    ("35P", "30평대 후반"), ("60P+", "60평 이상"), ("", ""),
])
def test_평형_라벨_변환(bucket, label):
    assert D.pyeong(bucket) == label


def test_타입_스케일이_지시사항_범위_안(cards):
    """2항: 헤드라인 88~104, 대형 숫자 220~280. 그 아래로는 **넘칠 때만** 간다."""
    css = D.base_css()
    for sel, lo, hi in [(r"\.h1\{\{?font-size:(\d+)px", 88, 104),
                        (r"\.h1\.sm\{font-size:(\d+)px", 88, 104),
                        (r"\.big\{font-size:(\d+)px", 220, 280),
                        (r"\.big\.sm\{font-size:(\d+)px", 220, 280),
                        (r"\.big\.xs\{font-size:(\d+)px", 220, 280)]:
        m = re.search(sel, css)
        assert m, sel
        v = int(m.group(1))
        assert lo <= v <= hi, f"{sel} = {v}px (허용 {lo}~{hi})"


# 지시사항이 **직접 크기를 지정한** 요소들. 24px 하한의 예외다.
#   워드마크 22px (4항) · "이미지는 지역 참고용" 20px (5-0항)
SPEC_SMALL = {".mark-brand span": 22, ".pc-note": 20}


def test_출처_글자가_24px_미만이_아니다():
    """24px 미만 금지 (2항). 폰에서 안 읽힌다.

    지시사항이 값을 직접 박아 둔 두 요소만 예외다 — 거기까지 24px 로 올리면
    지시사항과 어긋난다. 예외를 목록으로 못 박아 두면 "작게 쓸 자리"가
    슬그머니 늘어난다.
    """
    css = D.base_css()
    for sel, px in SPEC_SMALL.items():
        pat = re.escape(sel) + r"\{[^}]*font-size:(\d+)px"
        m = re.search(pat, css)
        assert m and int(m.group(1)) == px, f"{sel} 가 {px}px 가 아니다"
        css = re.sub(pat, sel + "{font-size:24px", css)
    small = [int(n) for n in re.findall(r"font-size:(\d+)px", css) if int(n) < 24]
    assert not small, f"24px 미만: {small}"


def test_여백이_8px_그리드를_따른다():
    """1항. 8의 배수가 아니면 장마다 미세하게 어긋나 보인다."""
    vals = [int(n) for n in re.findall(
        r"(?:gap|margin-top|margin-bottom):(\d+)px", D.base_css())]
    bad = sorted({v for v in vals if v % 8})
    assert not bad, f"8의 배수가 아닌 여백: {bad}"


# ── 렌더 결과 (느리지만 여기가 실제 보증) ───────────────────────────────
def test_렌더가_세로배치_규칙을_통과한다(cards, outdir, tmp_path):
    """5항: y=200에서 시작, 하단 빈 공간 300px 이하, 표지 숫자 폭 70% 이상.

    렌더러가 직접 재서 보고한다. 정적 검사로는 못 잡는 항목들이다 —
    글자 수가 바뀌면 같은 CSS 로도 결과가 달라진다.
    """
    _, problems = C.render(cards, tmp_path)
    assert not problems, problems


# ── 새 레이아웃 · 공통 요소 (2026-10-06 지시사항) ───────────────────────
def test_브랜드_마크가_모든_장에_있다(cards):
    """9항: 모든 장의 **같은 좌표**. 장마다 붙이면 새 장을 만들 때 빠뜨린다."""
    for c in cards:
        assert 'class="mark-brand' in c["html"], c["name"]
    assert c["html"].count('class="mark-brand') == 1, "마크가 두 번 들어갔다"


def test_브랜드_마크_좌표가_CSS로_고정돼_있다():
    css = D.base_css()
    m = re.search(r"\.mark-brand\{([^}]*)\}", css)
    assert m, "마크 규칙이 없다"
    assert f"right:{D.PAD_X}px" in m.group(1)
    assert f"bottom:{D.PAD_BOTTOM - 48}px" in m.group(1)


def test_조건_라벨이_헤드라인_위에_있다(cards):
    """4항: 대괄호 라벨 1개. 독자가 알아야 할 조건·범위를 적는다."""
    for c in cards:
        if c["layout"] == "summary_cta":
            continue
        t = C.strip_html(c["html"])
        assert re.search(r"\[[^\]]+\]", t), f"{c['name']}: 조건 라벨 없음"


def test_조건_라벨에_마케팅_문구가_없다(cards):
    from content.validator import check_banned
    for c in cards:
        for m in re.finditer(r"\[([^\]]+)\]", C.strip_html(c["html"])):
            txt = m.group(1)
            assert not check_banned(txt), f"{c['name']}: {txt}"
            for w in ("필수", "꼭 보", "놓치", "지금"):
                assert w not in txt, f"{c['name']}: 마케팅 문구 '{w}' — {txt}"


def test_순위표가_10행을_넘지_않는다(cards):
    """9항. 넘으면 글자를 줄이는 게 아니라 행을 줄인다."""
    rt = next((c for c in cards if c["layout"] == "ranking_table"), None)
    if rt is None:
        pytest.skip("순위표 없음")
    assert rt["html"].count('class="rt-row') <= 10
    assert C.RT_ROWS_MIN <= rt["rows_max"] <= 10


def test_순위표_글자가_28px_이상():
    css = D.base_css()
    for sel in (".rt-rank", ".rt-name", ".rt-val", ".rt-chg"):
        m = re.search(re.escape(sel) + r"\{font-size:(\d+)px", css)
        assert m and int(m.group(1)) >= 28, f"{sel} 가 28px 미만"


def test_순위표_강조행이_하나뿐(cards):
    """여러 행을 칠하면 '강조'가 아니게 된다 (5항)."""
    rt = next((c for c in cards if c["layout"] == "ranking_table"), None)
    if rt is None:
        pytest.skip("순위표 없음")
    assert rt["html"].count('rt-row hi') == 1


def test_표와_타일을_붙여놓지_않는다(cards):
    """같은 계열이라 연속하면 두 장이 한 장처럼 읽힌다 (5항)."""
    pairs = [(a["layout"], b["layout"]) for a, b in zip(cards, cards[1:])]
    assert ("ranking_table", "tile_grid") not in pairs
    assert ("tile_grid", "ranking_table") not in pairs
    assert ("rows", "compare_bars") not in pairs
    assert ("compare_bars", "rows") not in pairs


def test_타일은_여러_단지를_보여준다(cards):
    """한 단지만 크게 쓰면 '이 주의 신고가는 한 곳뿐'처럼 읽힌다."""
    tg = next((c for c in cards if c["layout"] == "tile_grid"), None)
    if tg is None:
        pytest.skip("타일 장 없음")
    names = {r["apt_name"] for r in tg["facts"]["card"]["new_highs"]}
    assert len(names) >= C.TILE_MIN


def test_표지_단지가_타일에_다시_나오지_않는다(cards, data):
    tg = next((c for c in cards if c["layout"] == "tile_grid"), None)
    if tg is None:
        pytest.skip("타일 장 없음")
    t = C.pick(data)
    if t["cover"].angle != "new_high":
        pytest.skip("표지가 신고가 앵글이 아님")
    cov = t["cover"].data["apt_name"]
    assert cov not in {r["apt_name"] for r in tg["facts"]["card"]["new_highs"]}


def test_사진이_없으면_오프화이트_표지로_간다(cards):
    """5항 폴백. 라이선스 있는 사진이 없는데 photo_cover 를 내면 안 된다."""
    c = cards[0]
    if c["layout"] == "photo_cover":
        assert c.get("photo"), "사진 경로 없이 photo_cover 를 썼다"
    else:
        assert c["layout"] == "hero_number", c["layout"]
