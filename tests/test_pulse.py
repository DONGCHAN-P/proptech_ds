"""평소지도 검증.

웹이라고 기준이 달라지지 않는다. 화면에 뜨는 수와 문구도 발행물이다.

여기서 막는 것
  ① 사이트와 SNS 가 **같은 주에 다른 수**를 말하는 것 — 이게 제일 무섭다.
     둘 다 그럴듯해 보여서 아무도 못 알아챈다
  ② 투자 권유로 읽히는 문구가 UI 에 섞이는 것
  ③ 표본이 얇은 값을 그냥 내보내는 것
  ④ σ·표준편차가 화면에 새는 것
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

duckdb = pytest.importorskip("duckdb")
from pulse import build_pulse as B  # noqa: E402
from content.validator import check_banned  # noqa: E402
from content.design import JARGON  # noqa: E402

CACHE = ROOT / "pulse" / "cache"
STATIC = ROOT / "pulse" / "static"
pytestmark = pytest.mark.skipif(
    not (CACHE / "sgg_now.parquet").exists(),
    reason="pulse 캐시 없음 — python -m pulse.build_pulse")


@pytest.fixture(scope="module")
def con():
    c = duckdb.connect()
    for p in CACHE.glob("*.parquet"):
        c.execute(f"CREATE VIEW {p.stem} AS SELECT * FROM read_parquet('{p.as_posix()}')")
    yield c
    c.close()


@pytest.fixture(scope="module")
def metrics() -> dict:
    files = sorted((ROOT / "output").glob("metrics_*.json"))
    if not files:
        pytest.skip("지표 JSON 없음")
    return json.loads(files[-1].read_text(encoding="utf-8"))


# ── ① 사이트와 SNS 가 같은 수를 말한다 ───────────────────────────────────
def test_기준_주가_같다(con, metrics):
    """둘 다 신고 지연만큼 물린 같은 주를 봐야 한다."""
    site = con.execute("SELECT DISTINCT week_start FROM sgg_now").fetchone()[0]
    sns = metrics["weekly"]["sgg_zscore"][0]["week_start"]
    assert str(site) == sns, f"사이트 {site} / SNS {sns}"


def test_거래_건수가_한_건도_다르지_않다(con, metrics):
    """같은 주의 같은 시군구인데 건수가 다르면 둘 중 하나는 거짓말이다.

    처음엔 사이트가 web/cache 사본을 읽어 오산시가 91건으로 나왔다. 같은 주를
    인스타 카드는 98건이라고 말하고 있었다. 지금은 양쪽 다 정본(master)을
    읽고 metrics.filters 를 거친다.
    """
    site = {r[0]: r[1] for r in
            con.execute("SELECT name, deals FROM sgg_now").fetchall()}
    bad = []
    for r in metrics["weekly"]["sgg_zscore"]:
        n = site.get(r["sigungu_name"])
        if n is not None and n != r["week_deals"]:
            bad.append(f'{r["sigungu_name"]} 사이트 {n} / SNS {r["week_deals"]}')
    assert not bad, bad[:5]


def test_평소_기준도_같다(con, metrics):
    """'평소'가 0.8건만 달라도 화면엔 57건과 58건으로 다르게 찍힌다.

    SNS 쪽은 소수 첫째 자리로 반올림해 저장하므로 **원값과 비교**한다.
    반올림한 값끼리 보면 104.25 가 파이썬에서는 104.2, DuckDB 에서는 104.3 이
    돼 멀쩡한 값이 불일치로 잡힌다 (반올림 방식이 다르다).
    """
    site = {r[0]: r[1] for r in
            con.execute("SELECT name, deals_avg FROM sgg_now").fetchall()}
    bad = []
    for r in metrics["weekly"]["sgg_zscore"]:
        a, b = site.get(r["sigungu_name"]), r["deals_avg_52w"]
        if a is not None and abs(a - b) > 0.051:
            bad.append(f'{r["sigungu_name"]} 사이트 {a:.2f} / SNS {b}')
    assert not bad, bad[:5]


def test_비교창이_SNS와_같은_상수다():
    from metrics import build_metrics as M
    assert B.LAG_DAYS == M.WEEKLY_LAG_DAYS
    assert B.HIST_WEEKS == M.ZSCORE_HIST_WEEKS


def test_해제건_필터를_공통_관문으로_쓴다():
    """자기 WHERE 를 쓰면 언젠가 한쪽만 고쳐진다 (step8 이 그렇게 뚫렸다)."""
    src = (ROOT / "pulse" / "build_pulse.py").read_text(encoding="utf-8")
    assert "from metrics.filters import trades_cte" in src
    assert "is_canceled" not in src, "필터를 직접 쓰고 있다"


def test_정본을_읽는다():
    src = (ROOT / "pulse" / "build_pulse.py").read_text(encoding="utf-8")
    assert 'master" / "trade_events.parquet"' in src, "서빙용 사본을 읽고 있다"


# ── ② 투자 권유 금지 ─────────────────────────────────────────────────────
import re  # noqa: E402

_COMMENT = [
    re.compile(r"/\*.*?\*/", re.S),      # js 블록 주석
    re.compile(r"(?m)^\s*//.*$"),        # js 줄 주석
    re.compile(r"(?m)\s//.*$"),          # js 꼬리 주석 (. 은 줄바꿈을 안 먹는다)
    re.compile(r"<!--.*?-->", re.S),     # html 주석
    re.compile(r'"""[\s\S]*?"""'),       # py 독스트링
    re.compile(r"(?m)^\s*#.*$"),         # py 줄 주석
    re.compile(r"(?m)\s#.*$"),           # py 꼬리 주석
]


def ui_text() -> str:
    """화면에 나가는 한국어만 모은다.

    주석까지 긁으면 이 테스트가 **코드 설명을 발행 문구로 착각한다**. 실제로
    "표준편차를 화면에 쓰지 않는다"고 적은 주석 때문에 통계 용어 검사가
    걸렸다. 설계 의도를 적은 글이 그 의도를 위반한 걸로 잡히는 꼴이다.
    """
    blobs = []
    for p in [*STATIC.rglob("*.html"), *STATIC.rglob("*.js"),
              ROOT / "pulse" / "main.py"]:
        t = p.read_text(encoding="utf-8")
        for pat in _COMMENT:
            t = pat.sub(" ", t)
        blobs += re.findall(r"[가-힣][가-힣\s·‘’,.%()~/·]{2,}", t)
    return " ".join(blobs)


def test_UI_문구에_금지표현이_없다():
    hits = check_banned(ui_text())
    assert not hits, hits


@pytest.mark.parametrize("word", [
    "저평가", "유망", "매수 적기", "급등주", "추천", "지금이 기회", "떡상",
])
def test_권유로_읽히는_단어가_없다(word):
    """상태 라벨은 서술이지 권유가 아니다. '달아오름'은 되고 '매수 적기'는 안 된다.

    면책 문구에는 "매수·매도를 추천하거나 ... 않으며" 가 들어 있으므로 그
    문장은 빼고 본다 — content.validator.check_banned 와 같은 처리다.
    """
    from templates.disclaimers import ALL_DISCLAIMERS
    t = ui_text()
    for fixed in ALL_DISCLAIMERS.values():
        t = t.replace(fixed, " ")
    assert word not in t, f"'{word}' 가 화면 문구에 있다"


def test_상태_라벨이_전부_서술이다():
    from pulse.main import STATES
    for k, v in STATES.items():
        assert not check_banned(v["label"] + " " + v["desc"]), k


def test_면책을_손으로_다시_쓰지_않는다():
    """화면용으로 짧게 고쳐 쓰면 '변경 금지' 문구가 조용히 갈라진다.

    승인된 문구를 API 가 그대로 내려보내고 프런트는 받아 쓴다.
    """
    from fastapi.testclient import TestClient
    from pulse.main import app
    from templates.disclaimers import DISCLAIMER_SOCIAL
    m = TestClient(app).get("/api/meta").json()
    assert m["disclaimer"] == DISCLAIMER_SOCIAL
    js = " ".join(p.read_text(encoding="utf-8")
                  for p in STATIC.rglob("*.js"))
    assert "META.disclaimer" in js, "프런트가 면책을 받아 쓰지 않는다"


# ── ③ 표본 ───────────────────────────────────────────────────────────────
def test_표본이_적으면_색을_칠하지_않는다(con):
    bad = con.execute(f"""
        SELECT name, deals, state FROM sgg_now
        WHERE deals < {B.MIN_DEALS} AND state NOT IN ('thin', 'unknown')
    """).fetchall()
    assert not bad, bad[:5]


def test_판단기준이_캐러셀_헤드라인과_같다():
    """지도도 헤드라인이다. 연천군 7건으로 전국 1위가 되면 안 된다."""
    from content import carousel as C
    assert B.MIN_DEALS >= C.MIN_SAMPLE


def test_과거가_모자라면_판단하지_않는다(con):
    bad = con.execute(f"""
        SELECT name, hist_weeks FROM sgg_now
        WHERE hist_weeks < {B.MIN_HIST_WEEKS} AND state <> 'unknown'
    """).fetchall()
    assert not bad, bad[:5]


def test_단지_표본이_얇으면_표시된다(con):
    bad = con.execute(f"""
        SELECT apt_name, n_recent, n_prior FROM apt_now
        WHERE (n_recent < {B.APT_MIN_DEALS} OR n_prior < {B.APT_MIN_DEALS})
          AND NOT thin
    """).fetchall()
    assert not bad, bad[:5]


def test_표본_배지를_UI가_실제로_그린다():
    js = (STATIC / "js" / "panel.js").read_text(encoding="utf-8")
    assert "a.thin" in js and "표본 적음" in js


# ── ④ 통계 용어 노출 금지 ────────────────────────────────────────────────
def test_화면에_표준편차가_새지_않는다():
    """σ 는 분류에만 쓰고 내보내지 않는다 (content/design.py 와 같은 규칙)."""
    m = JARGON.search(ui_text())
    assert not m, f"통계 용어 노출: {m.group(0)}"


def test_z값은_API_응답에서_빠진다():
    """z_deals/z_ppy 는 방향·배수로 바꿔서 내보낸다. 날것이 나가면 화면에 샌다."""
    from fastapi.testclient import TestClient
    from pulse.main import app
    r = TestClient(app).get("/api/regions?level=sgg").json()
    assert r["items"], "비어 있다"
    for it in r["items"][:20]:
        assert "z_deals" not in it and "z_ppy" not in it, it
        assert "dir" in it and "ratio" in it


# ── 가격은 수준이 아니라 속도 ────────────────────────────────────────────
def test_가격은_변화율로_비교한다(con):
    """수준으로 재면 상승장에서 전 지역이 '평소보다 높음'이 된다.

    실측: 수준 비교일 때 82곳 중 15곳이 thin_rise 였다. 시장 전체에 대한
    정보지 지역에 대한 정보가 아니다.
    """
    n = con.execute(
        "SELECT count(*) FROM sgg_now WHERE state = 'thin_rise'").fetchone()[0]
    total = con.execute("SELECT count(*) FROM sgg_now").fetchone()[0]
    assert n / total < 0.15, f"{n}/{total} 이 얇은 상승 — 추세를 못 걷어냈다"


def test_평소_변화율도_같이_내보낸다(con):
    """'+14.2%' 만 보여주면 많은지 적은지 알 수 없다. 평소 몇 %인지 같이 준다."""
    cols = [r[0] for r in con.execute("DESCRIBE sgg_now").fetchall()]
    assert "ppy_chg" in cols and "chg_avg" in cols


# ── API ──────────────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    from pulse.main import app
    return TestClient(app)


@pytest.mark.parametrize("url", [
    "/api/meta", "/api/regions?level=sgg", "/api/regions?level=dong",
    "/api/extremes?level=sgg", "/api/extremes?level=dong",
    "/api/apts", "/api/search?q=오산", "/api/health",
])
def test_엔드포인트가_응답한다(client, url):
    assert client.get(url).status_code == 200


def test_양_끝을_같이_준다(client):
    """붐빈 쪽만 주면 '거래가 늘고 있다'로 읽힌다 (캐러셀 3장과 같은 원칙)."""
    j = client.get("/api/extremes?level=sgg&n=5").json()
    assert j["busy"] and j["quiet"]
    assert j["busy"][0]["ratio"] > j["quiet"][0]["ratio"]


def test_잘못된_레벨은_거절한다(client):
    assert client.get("/api/regions?level=시도").status_code == 400


def test_없는_지역은_404(client):
    assert client.get("/api/region/sgg/00000").status_code == 404


def test_NaN이_JSON으로_새지_않는다(client):
    """NaN 은 표준 JSON 이 아니라 프런트에서 조용히 파싱이 깨진다."""
    raw = client.get("/api/regions?level=dong").text
    assert "NaN" not in raw and "Infinity" not in raw


# ── 단지 레벨 ────────────────────────────────────────────────────────────
#
# "현재 실거래가"를 보여주기 시작하면 틀릴 수 있는 방식이 늘어난다.
# 평형을 빼먹는 것, 오래된 거래를 현재가로 찍는 것, 추정가와 섞이는 것.
def test_평형_없는_가격을_내보내지_않는다(client):
    """같은 단지에서 15평과 40평이 두 배 넘게 차이 난다.

    평형 없는 "현재 실거래가"는 어느 쪽을 보는 사람에게든 틀린 값이다.
    """
    items = client.get("/api/apts?limit=50").json()["items"]
    assert items
    for a in items:
        assert a["last_price"] is not None
        assert a["pyeong_bucket"], a
        # 마커에 박히는 짧은 평형 — 실제 거래 면적에서 환산한다
        assert a["pyeong_short"], a["apt_name"]


def test_마커가_평형을_실제로_그린다():
    """API 가 내려줘도 화면이 안 쓰면 소용없다."""
    js = (STATIC / "js" / "map.js").read_text(encoding="utf-8")
    assert "pyeong_short" in js, "마커가 평형을 안 쓴다"
    css = (STATIC / "css" / "style.css").read_text(encoding="utf-8")
    assert ".apt-mk.compact .py{display:none}" not in css, "줌에 따라 평형을 숨기고 있다"


def test_오래된_거래를_현재가로_찍지_않는다(con):
    """5년 전 거래 한 건을 '현재 실거래가'라고 지도에 올리면 그 자체가 거짓이다."""
    old = con.execute(f"""
        SELECT apt_name, last_date FROM apt_now
        WHERE last_date <= (SELECT max(last_date) FROM apt_now)
                           - INTERVAL {B.APT_MAP_MAX_AGE_DAYS} DAY
    """).fetchall()
    assert not old, old[:5]


def test_마커_가격은_추정이_아니라_신고값이다(con):
    """last_price 는 실제 신고된 거래 금액이어야 한다 — 평균도 보간도 아니다."""
    src = (ROOT / "pulse" / "build_pulse.py").read_text(encoding="utf-8")
    assert "arg_max(deal_amount, deal_date) AS last_price" in src
    for 금지 in ("avg(deal_amount)", "median(deal_amount)"):
        assert 금지 not in src, f"마커 가격에 {금지} 를 쓰고 있다"


def test_평형별로_접지_않는다(client, con):
    """한 단지를 한 숫자로 요약하면 어느 평형을 보는 사람에게든 틀린 값이 된다."""
    aid = con.execute("""
        SELECT apt_id FROM apt_pyeong_now
        GROUP BY 1 HAVING count(*) >= 3 LIMIT 1""").fetchone()
    if not aid:
        pytest.skip("평형이 여럿인 단지 없음")
    d = client.get(f"/api/apt/{aid[0]}").json()
    assert len(d["pyeongs"]) >= 3
    assert len({p["pyeong_bucket"] for p in d["pyeongs"]}) == len(d["pyeongs"])


def test_단지_상세가_지역_맥락을_같이_준다(client, con):
    """단지만 보면 동네가 통째로 움직인 건지 이 단지만인지 알 수 없다."""
    aid = con.execute("SELECT apt_id FROM apt_now LIMIT 1").fetchone()[0]
    d = client.get(f"/api/apt/{aid}").json()
    assert "region" in d


def test_평형_필터가_값을_바꾼다(client):
    """평형을 고르면 마커 가격도 그 평형 기준으로 바뀌어야 한다."""
    a = client.get("/api/apts?pyeong=20P&limit=30").json()["items"]
    b = client.get("/api/apts?pyeong=40P&limit=30").json()["items"]
    assert a and b
    assert all(x["pyeong_bucket"] == "20P" for x in a)
    assert all(x["pyeong_bucket"] == "40P" for x in b)


def test_잘못된_평형은_거절한다(client):
    assert client.get("/api/apts?pyeong=99평").status_code == 400


def test_얇은_표본은_변화율을_감춘다(client):
    """마지막 거래가는 사실이라 그대로 두되, 3건으로 뽑은 변화율은 가린다."""
    items = client.get("/api/apts?limit=200").json()["items"]
    for a in items:
        if a["thin"]:
            assert a["dir"] == "thin", a["apt_name"]


def test_겹치는_말풍선을_솎아낸다():
    """70px 말풍선을 전부 그리면 도심에서 숫자가 서로를 덮는다."""
    js = (STATIC / "js" / "map.js").read_text(encoding="utf-8")
    assert "declutter" in js
    assert "latLngToContainerPoint" in js, "화면 좌표로 솎아내지 않는다"
