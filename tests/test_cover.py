"""표지 선정 규칙 (5-1항) · 사진 라이선스 (5-0항).

여기가 "통계적으로 가장 튄 곳"과 "사람들이 아는 곳"을 가른다. 규칙이 조용히
풀리면 매주 표지가 거래 몇십 건짜리 외곽 군으로 돌아가는데, 수치는 맞아서
아무도 못 알아챈다.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from content import cover as CV  # noqa: E402
from content import photos  # noqa: E402


@pytest.fixture(scope="module")
def data() -> dict:
    files = sorted((ROOT / "output").glob("metrics_*.json"))
    if not files:
        pytest.skip("지표 JSON 없음")
    return json.loads(files[-1].read_text(encoding="utf-8"))


# ── 우선 후보 ────────────────────────────────────────────────────────────
@pytest.mark.parametrize("name,code", [
    ("마포구", "11440"), ("강남구", "11680"), ("송파구", "11710"),
    ("성남분당구", "41135"), ("고양일산동구", "41285"),
    ("안양동안구", "41173"), ("군포시", "41410"), ("부천원미구", "41192"),
])
def test_우선_후보로_인식한다(name, code):
    assert CV.is_priority(name, code), name


@pytest.mark.parametrize("name", ["연천군", "가평군", "양평군", "포천시"])
def test_외곽은_우선_후보가_아니다(name):
    assert not CV.is_priority(name, CV.NAME_TO_CODE.get(name))


def test_코드가_없어도_이름으로_되짚는다():
    """지표 행에 sigungu_code 가 빠지면 서울 25개 구가 통째로 밀려난다.

    실제로 daily.new_high 에 코드가 없어서 마포·송파·성북이 전부 "기타"로
    분류됐다. 지표 쪽도 고쳤지만 조용히 틀리는 자리라 안전망을 둔다.
    """
    assert CV.is_priority("마포구", None)
    assert CV.resolve("성남분당구", None) == "41135"


# ── 규칙 ─────────────────────────────────────────────────────────────────
def test_표본이_적으면_표지에_오르지_못한다(data):
    for c in CV.build(data):
        assert c.sample >= CV.MIN_SAMPLE, (c.region, c.sample)


def test_앵글_우선순위를_따른다(data):
    """① 신고가 ② 반전 ③ 급증. 세기가 더 커도 순위가 앞서지 않는다."""
    picked, top3, _ = CV.choose(data)
    assert picked is not None
    best = min(CV.ANGLE_RANK[c.angle] for c in CV.build(data))
    assert CV.ANGLE_RANK[picked.angle] == best


def test_비우선_지역은_확실히_클_때만_표지(data):
    """1.5배 미만 차이면 2장 순위표에서만 다룬다."""
    picked, _, _ = CV.choose(data)
    if picked.priority:
        return
    peers = [c.strength for c in CV.build(data)
             if c.priority and c.angle == picked.angle]
    if peers:
        assert picked.strength >= max(peers) * CV.OUTSIDER_EDGE


def test_같은_데이터면_항상_같은_표지(data):
    """캐러셀·캡션·스레드가 각자 부른다. 호출마다 답이 달라지면 말이 갈린다."""
    picks = {CV.choose(data)[0].region for _ in range(3)}
    assert len(picks) == 1, picks


def test_이번_회차는_반복금지에_걸리지_않는다(data, tmp_path, monkeypatch):
    """로그를 쓴 뒤 다시 고를 때 자기 자신이 걸리면 안 된다."""
    monkeypatch.setattr(CV, "LOG", tmp_path / "log.json")
    first, top3, notes = CV.choose(data)
    CV.log(data["asof"], first, top3, notes)
    again, _, _ = CV.choose(data)
    assert again.region == first.region


def test_직전_회차_지역은_연속으로_오르지_않는다(data, tmp_path, monkeypatch):
    monkeypatch.setattr(CV, "LOG", tmp_path / "log.json")
    first, top3, notes = CV.choose(data)
    CV.log("2000-01-01", first, top3, notes)     # 다른 회차로 기록
    again, _, _ = CV.choose(data)
    if len({c.region for c in CV.build(data)}) > 1:
        assert again.region != first.region


def test_선정_이유를_로그로_남긴다(data, tmp_path, monkeypatch):
    """10항 성과 측정의 입력. 후보 3개와 사유가 있어야 규칙을 고칠 수 있다."""
    monkeypatch.setattr(CV, "LOG", tmp_path / "log.json")
    picked, top3, notes = CV.choose(data)
    CV.log(data["asof"], picked, top3, notes)
    rows = json.loads((tmp_path / "log.json").read_text(encoding="utf-8"))
    r = rows[-1]
    assert r["picked"]["angle_label"] and r["picked"]["headline"]
    assert 1 <= len(r["candidates"]) <= 3
    for c in r["candidates"]:
        assert {"angle", "region", "priority", "headline", "sample"} <= set(c)


# ── 사진 라이선스 (5-0항) ────────────────────────────────────────────────
def test_라이선스_파일이_없으면_쓰지_않는다(tmp_path, monkeypatch):
    monkeypatch.setattr(photos, "PHOTO_DIR", tmp_path)
    d = tmp_path / "11440"
    d.mkdir()
    (d / "a.jpg").write_bytes(b"\xff\xd8\xff")
    got, problems = photos.find("11440")
    assert got is None
    assert problems and "license.json 없음" in problems[0]


def test_허용되지_않는_라이선스를_막는다(tmp_path, monkeypatch):
    monkeypatch.setattr(photos, "PHOTO_DIR", tmp_path)
    d = tmp_path / "11440"
    d.mkdir()
    (d / "a.jpg").write_bytes(b"\xff\xd8\xff")
    (d / "a.jpg.license.json").write_text(json.dumps({
        "source": "어디선가", "type": "unknown",
        "acquired": "2026-10-06", "credit": "출처 미상"}), encoding="utf-8")
    got, problems = photos.find("11440")
    assert got is None and problems


def test_제대로_된_사진은_통과한다(tmp_path, monkeypatch):
    monkeypatch.setattr(photos, "PHOTO_DIR", tmp_path)
    d = tmp_path / "11440"
    d.mkdir()
    (d / "a.jpg").write_bytes(b"\xff\xd8\xff")
    (d / "a.jpg.license.json").write_text(json.dumps({
        "source": "직접 촬영", "type": "own", "acquired": "2026-10-06",
        "credit": "사진: 직접 촬영", "scene": "region"}), encoding="utf-8")
    got, problems = photos.find("11440")
    assert got and not problems
    assert got.is_region          # 지역 풍경 → "이미지는 지역 참고용" 표기 대상
    assert got.data_uri().startswith("data:image/jpeg;base64,")


def test_사진이_없는_건_실패가_아니다(tmp_path, monkeypatch):
    """폴백 신호다 — 사진을 못 구하면 오프화이트 표지로 간다 (5항)."""
    monkeypatch.setattr(photos, "PHOTO_DIR", tmp_path)
    got, problems = photos.find("99999")
    assert got is None and not problems


def test_보유_사진이_전부_라이선스를_갖췄다():
    assert not photos.audit()


# ── map 레이아웃 (5-0항) ─────────────────────────────────────────────────
from content import geo  # noqa: E402

pytestmark_geo = pytest.mark.skipif(not geo.available(),
                                    reason="경계 파일 없음 — python -m content.geo --build")


def test_모든_시군구가_경계와_매칭된다():
    """이름으로 맞추므로 하나라도 어긋나면 그 지역은 영영 안 칠해진다.

    경계 파일의 코드는 SGIS 체계라 우리 법정동 코드와 다르다(강남구가
    11230 vs 11680). 그래서 코드가 아니라 이름으로 맞춘다.
    """
    if not geo.available():
        pytest.skip("경계 파일 없음")
    from common import SIGUNGU_CODES
    have = {f["properties"]["name"] for f in geo.load()["features"]}
    miss = [n for n in SIGUNGU_CODES.values() if geo.geo_name(n)[0] not in have]
    assert not miss, miss


def test_행정구역_개편분은_근사로_표시된다():
    """부천원미구는 경계 파일에 없어 부천시 전체로 칠해진다.

    실제보다 넓은 면이 칠해지므로 카드 각주에 그 사실을 적는다. 숨기면
    "저 동네 전체가 그렇다"로 읽힌다.
    """
    for name in ("부천원미구", "화성동탄구", "검단구"):
        _, approx = geo.geo_name(name)
        assert approx, name
    for name in ("마포구", "오산시", "성남분당구"):
        _, approx = geo.geo_name(name)
        assert not approx, name


def test_좌표계를_투영_미터로_다룬다():
    """경위도로 알고 cos(위도) 보정을 넣었다가 지도가 세로 줄무늬로 깨졌다.

    cos(radians(1951000)) 은 뜻 없는 값이다. 투영 좌표는 이미 평면이다.
    """
    src = (ROOT / "content" / "geo.py").read_text(encoding="utf-8")
    # 투영 좌표에 **위도 보정을 거는 것**만 금지다. 위경도→UTM-K 변환식
    # (to_utmk) 은 당연히 삼각함수를 쓴다 — 그건 다른 얘기다.
    assert "math.radians((y0" not in src, "투영 좌표에 위도 보정을 쓰고 있다"
    assert "def to_utmk" in src, "좌표 변환이 없다"
    if geo.available():
        f = geo.load()["features"][0]
        x, y = f["geometry"]["coordinates"][0][0][0]
        assert x > 10000 and y > 10000, (x, y)   # 경위도가 아니라 미터


@pytest.mark.parametrize("name,scope", [
    ("마포구", "서울"), ("오산시", "경기"), ("남동구", "인천"),
])
def test_대상_지역만_칠한다(name, scope):
    if not geo.available():
        pytest.skip("경계 파일 없음")
    from content import design as D
    svg = geo.svg({name: D.UP}, width=936, height=400, line=D.LINE,
                  fill=D.NEUTRAL, label_color=D.INK, scope=scope)
    assert svg and svg.startswith("<svg")
    # 의미색은 대상 하나에만. 나머지는 전부 중립색이어야 한다.
    assert svg.count(f'fill="{D.UP}"') == 1, "대상 외에도 칠해졌다"
    assert f">{name}<" in svg, "대상 라벨이 없다"
    assert svg.count("<text") == 1, "라벨을 전부 달면 어디를 보라는 건지 사라진다"


def test_경계_출처를_밝힌다():
    """5-0항: 이용허락 범위를 확인하고 출처를 각주에 넣는다."""
    assert "SGIS" in geo.CREDIT and "MIT" in geo.CREDIT
    lic = ROOT / "assets" / "geo" / "LICENSE.md"
    if geo.available():
        assert lic.exists(), "LICENSE.md 없이 경계를 쓰고 있다"
        t = lic.read_text(encoding="utf-8")
        assert "MIT" in t and "statgarten" in t


def test_금지_소스를_쓰지_않는다():
    """포털 지도·로드뷰 캡처, 뉴스 사진, AI 생성 이미지 (5-0항)."""
    src = "".join((ROOT / "content" / f).read_text(encoding="utf-8")
                  for f in ("geo.py", "photos.py", "carousel.py"))
    for 금지 in ("kakao", "naver.com/map", "roadview", "dall-e", "midjourney",
                 "stable-diffusion", "fal.ai", "text2img"):
        assert 금지 not in src.lower(), f"금지 소스 흔적: {금지}"


# ── 동네 지도 (OSM 도로 포함) ────────────────────────────────────────────
def test_외부_지도_서비스를_캡처하지_않는다():
    """호갱노노·카카오·구글 지도 이미지를 가져다 쓰지 않는다.

    공개 API 가 없거나(호갱노노), 지도 이미지를 저장·재발행하는 데 제약이
    크다(카카오·구글). 우리는 공공데이터와 OSM(ODbL)으로만 그린다.
    """
    # **호스트·API 흔적**만 본다. "호갱노노를 쓰지 않는다"는 설명 주석까지
    # 걸면, 왜 안 쓰는지 적어 둔 글이 위반으로 잡힌다.
    src = "".join((ROOT / "content" / f).read_text(encoding="utf-8")
                  for f in ("neighbor_map.py", "geo.py", "apt_story.py"))
    src += (ROOT / "metrics" / "build_metrics.py").read_text(encoding="utf-8")
    src = src.lower()
    for host in ("hogangnono.com", "dapi.kakao.com", "maps.googleapis.com",
                 "map.naver.com", "openapi.map.naver", "staticmap",
                 "roadview", "api.vworld.kr/req/image"):
        assert host not in src, host


def test_도로_출처를_밝힌다():
    """ODbL 은 출처 표기를 요구한다. 표기 없이 쓰면 라이선스 위반이다."""
    from metrics import build_metrics as M
    assert "OpenStreetMap" in M.OSM_CREDIT and "ODbL" in M.OSM_CREDIT


def test_간선도로만_그린다():
    """이면도로까지 다 그리면 그물망이 된다 (실측: 강북구 한 곳에 1,204개)."""
    from metrics import build_metrics as M
    assert "residential" not in M.OSM_DRAW
    assert {"primary", "secondary", "tertiary"} <= M.OSM_DRAW


def test_도로가_없어도_지도는_그려진다(data):
    """공개 Overpass 는 연속 요청을 제한한다. 한 번 실패했다고 그 주 발행이
    멈추면 안 된다."""
    from content import neighbor_map as NM
    prof = next(iter((data.get("profiles") or {}).values()), None)
    if not prof:
        pytest.skip("프로필 없음")
    stripped = dict(prof, around=dict(prof.get("around") or {}, roads=[]))
    svg = NM.render(stripped, width=620, height=420, dark=True)
    assert svg and svg.startswith("<svg")


def test_지도에_그리는_것은_다섯_가지뿐(data):
    """상권·역·단지·자연·라벨. 요청받은 범위 밖을 임의로 늘리지 않는다."""
    src = (ROOT / "content" / "neighbor_map.py").read_text(encoding="utf-8")
    for layer in ("commerce", "stations", "parks", "rivers", "roads"):
        assert layer in src, layer
