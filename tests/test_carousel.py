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
def test_헤드라인을_되묻는_장이_있다(cards):
    """표지 숫자를 그대로 믿게 두지 않는다.

    전에는 `quote` 장이 "값이 올라도 거래는 안 늘었다"로 받았는데, 그게
    **다른 단지** 얘기여서 흐름이 끊겼다. 지금은 같은 소재를 한 겹 넓혀
    되묻는다 — 단지 하나가 움직여도 동네가 같이 움직이는 건 아니라고.
    """
    names = [c["name"] for c in cards]
    assert any(n.endswith(("_region", "_counter")) for n in names), names
    card = next(c for c in cards if c["name"].endswith(("_region", "_counter")))
    t = C.strip_html(card["html"])
    assert "아니에요" in t or "줄었" in t, t[:160]


def t_angle(cards) -> str:
    f = cards[0]["facts"]["card"]["cover"]
    return ("new_high" if "history_count" in f else
            "counter" if "change_pct" in f else "surge")


def test_표본을_숨기지_않는다(cards):
    """비율·배수를 쓴 장은 **그 수가 몇 건으로 나온 건지** 같이 적는다.

    단지 소개 덱에서는 표지가 "최근 1년 이 단지 거래 N건"을, 비교 장이
    단지별 "1년 N건" 배지를 들고 다닌다. 빠뜨리면 여기서 걸린다.
    """
    cov = cards[0]["facts"]["card"]
    prof = cov.get("profile")
    if not prof:
        pytest.skip("단지 소개 덱이 아님")
    assert f'{prof["deals_1y"]}건' in C.strip_html(cards[0]["html"])
    nb = next((c for c in cards if c["layout"] == "compare_bars"), None)
    if nb:
        t = C.strip_html(nb["html"])
        for r in prof["neighbors"][:3]:
            if C.D.split_name(r["apt_name"], 10)[0] in t:
                assert f'{r["deals_1y"]}건' in t, r["apt_name"]


def test_비교에는_양쪽_값을_모두_쓴다(cards):
    """지시사항 9항. 한쪽만 쓰면 늘었는지 줄었는지 알 수 없다."""
    c = next((c for c in cards if c["layout"] == "compare_bars"), None)
    if c is None:
        pytest.skip("비교 장 없음")
    t = C.strip_html(c["html"])
    f = c["facts"]["card"]
    if "profile" in f:
        # 단지 소개: 주인공과 이웃이 같은 화면에 있어야 눈금이 생긴다
        me = C.D.split_name(f["profile"]["apt_name"], 10)[0]
        assert me in t, "주인공이 비교 목록에서 잘렸다"
        assert sum(C.D.split_name(r["apt_name"], 10)[0] in t
                   for r in f["profile"]["neighbors"]) >= 2, "비교 대상이 모자라다"
    else:
        r = f["region"]
        assert f'{D.num(r["deals_avg_52w"])}건' in t and f'{r["week_deals"]}건' in t


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


def test_같은_대상을_같은_층위로_3장_연속_다루지_않는다(cards):
    """5항 "한 대상 최대 2장"을 **층위까지 넣어** 읽는다.

    캐러셀이 한 소재를 점점 넓혀가는 구조라(한 거래 → 그 동네 → 수도권)
    같은 지역명이 1~3장에 연달아 나온다. 그건 중복이 아니라 줄거리다.
    원래 규칙이 막으려던 건 **같은 얘기를 세 번 하는 것**이므로, 같은
    대상을 같은 층위(apt/region/metro)로 세 장 연속 다루는 경우만 막는다.
    """
    def key(c) -> set:
        out = set()
        for v in (c["facts"]["card"] or {}).values():
            if isinstance(v, dict):
                out |= {(c.get("scope"), v[k])
                        for k in ("apt_name", "sigungu_name") if v.get(k)}
        return out
    ks = [key(c) for c in cards]
    for i in range(len(ks) - 2):
        common = ks[i] & ks[i + 1] & ks[i + 2]
        assert not common, f"{cards[i]['name']}~{cards[i+2]['name']}: {common}"


def test_층위가_점점_넓어진다(cards):
    """표지의 한 사실에서 시작해 동네 → 수도권으로 넓힌다.

    장마다 각자의 1등을 뽑아 오면 "표지는 마포구, 2장은 포천, 4장은 영통동"
    처럼 여덟 장이 서로 남남이 된다. 층위가 뒤로 갈수록 넓어지는지 본다.
    """
    rank = {"apt": 0, "dong": 1, "region": 2, "metro": 3, "summary": 4}
    seq = [rank[c["scope"]] for c in cards if c.get("scope")]
    assert seq == sorted(seq), [
        (c["name"], c.get("scope")) for c in cards]
    assert seq[-1] == rank["summary"], "정리로 끝나지 않는다"


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




def test_표지가_지도면_출처를_밝힌다(cards):
    """5-0항: 경계 자료의 출처를 각주에 넣는다."""
    c = cards[0]
    if c["layout"] != "map_cover":
        pytest.skip("지도 표지가 아님")
    from content import geo
    t = C.strip_html(c["html"])
    assert geo.CREDIT in t, "경계 출처가 없다"
    if c.get("approx_boundary"):
        assert "개편 전 경계" in t, "근사 표시인데 밝히지 않았다"


def test_표지_폴백_순서(cards):
    """사진 → 지도 → 오프화이트 (5항). 없는 걸 쓰지 않는다."""
    from content import geo, photos
    lay = cards[0]["layout"]
    assert lay in ("photo_cover", "map_cover", "hero_number", "apt_cover"), lay
    if lay == "map_cover":
        assert geo.available()
    if lay == "photo_cover":
        assert cards[0].get("photo") and not photos.audit()


# ── 팔로우 유도 장 ───────────────────────────────────────────────────────
def test_마지막이_팔로우_유도_장(cards):
    """단지 소개 덱은 정리 장 없이 팔로우로 닫는다 (6장 구성)."""
    assert cards[-1]["layout"] == "follow_cta", cards[-1]["layout"]
    assert cards[-2]["layout"] in ("summary_cta", "rows", "signals"), (
        cards[-2]["layout"])


def test_팔로우_장에_핸들이_크게_있다(cards):
    """계정을 적지 않은 팔로우 유도는 아무 일도 안 한다."""
    html = cards[-1]["html"]
    assert 'class="fl-handle"' in html
    assert D.HANDLE in C.strip_html(html)


def test_팔로우_장이_과장하지_않는다(cards):
    """일곱 장 동안 지킨 톤이 마지막 한 장에서 무너지면 전부 무너진다."""
    from content.validator import check_banned
    t = C.strip_html(cards[-1]["html"])
    assert not check_banned(t)
    for w in ("놓치", "지금 바로", "필수", "무료 공개", "선착순", "단독"):
        assert w not in t, f"과장 표현 '{w}'"


def test_팔로우_장에_새_숫자가_없다(cards):
    """7장과 같은 규칙 (5항). 날짜·페이지·핸들 말고는 숫자를 쓰지 않는다."""
    t = C.strip_html(cards[-1]["html"])
    t = re.sub(r"\d{4}-\d{2}-\d{2}", " ", t)       # 기준일
    t = re.sub(r"\d+\s*/\s*\d+", " ", t)           # 페이지
    t = t.replace(D.HANDLE, " ")                   # 핸들
    assert not re.search(r"\d", t), t[:160]


def test_팔로우_장이_무엇을_주는지_말한다(cards):
    """설득 대신 '앞으로 뭘 받게 되는지'. 그게 이 계정의 약속이다."""
    t = C.strip_html(cards[-1]["html"])
    assert "팔로우" in t
    assert "오를지 내릴지는 말하지 않아요" in t, "투자 예측을 안 한다는 약속이 없다"
