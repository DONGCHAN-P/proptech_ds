"""평소지도 — API.

`pulse/build_pulse.py` 가 만든 파케이만 읽는다. 원본 거래를 요청 때마다
스캔하지 않는다.

화면에 나가는 모든 수는 전처리 단계에서 결정된다. 여기서 다시 계산하지
않는 이유는 `content/validator.py` 와 같다 — 숫자가 두 군데서 만들어지면
언젠가 갈라지고, 갈라진 걸 아무도 못 알아챈다.

실행:
  .venv\\Scripts\\python.exe -m uvicorn pulse.main:app --reload
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import duckdb
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
from content import design as D  # noqa: E402
from templates.disclaimers import DISCLAIMER_SOCIAL  # noqa: E402

CACHE = HERE / "cache"
STATIC = HERE / "static"

SGG_NOW = (CACHE / "sgg_now.parquet").as_posix()
DONG_NOW = (CACHE / "dong_now.parquet").as_posix()
SGG_WEEKS = (CACHE / "sgg_weeks.parquet").as_posix()
DONG_WEEKS = (CACHE / "dong_weeks.parquet").as_posix()
APT_NOW = (CACHE / "apt_now.parquet").as_posix()
APT_PY = (CACHE / "apt_pyeong_now.parquet").as_posix()
META = (CACHE / "meta.parquet").as_posix()

SPARK_WEEKS = 52   # 상세 그래프 길이 = 비교 창과 같게

# 평형 표기. "현재 실거래가"를 평형 없이 찍으면 거짓말이 된다 — 같은 단지에서
# 15평과 40평이 두 배 넘게 차이 난다. 마커에도 반드시 같이 적는다.
PYEONG_ORDER = ["10P", "15P", "20P", "25P", "30P", "35P", "40P", "50P", "60P+"]
PYEONG_LABEL = {
    "10P": "10평대", "15P": "10평대 후반", "20P": "20평대", "25P": "20평대 후반",
    "30P": "30평대", "35P": "30평대 후반", "40P": "40평대", "50P": "50평대",
    "60P+": "60평 이상",
}

# 단지 마커 색은 **90일 전과 견준 평당가 변화**를 나타낸다. 지역 마커(거래량)와
# 기준이 달라서 범례를 레벨에 따라 바꿔 단다 — 같은 빨강이 다른 뜻이면
# 범례를 외워야 읽히는 지도가 된다.
APT_DIR_BAND = 1.0   # ±1% 안쪽은 회색. 0.2% 를 빨갛게 칠하지 않는다

LEVELS = {
    "sgg": {"now": SGG_NOW, "weeks": SGG_WEEKS, "label": "시군구",
            "window": "이번 주"},
    "dong": {"now": DONG_NOW, "weeks": DONG_WEEKS, "label": "읍면동",
             "window": "최근 4주"},
}

# ── 상태 ─────────────────────────────────────────────────────────────────
#
# 라벨은 **상태 서술**이지 권유가 아니다. "매수 적기" "저평가" 같은 말을 쓰면
# 그 순간 투자 자문이 된다 (tests/test_pulse.py 가 금지 표현을 막는다).
#
# thin_rise 를 따로 둔 이유: 거래는 줄었는데 값만 오르는 구간이 가장 오해를
# 부른다. 몇 건 안 되는 거래로 중위가가 밀려 올라간 것일 수 있어서, 숫자만
# 보면 "오르는 동네"로 읽힌다. 그래서 이름에 "얇은"을 넣었다.
STATES = {
    "hot":       {"label": "달아오름", "desc": "거래도 값도 평소보다 빠릅니다"},
    "churn":     {"label": "손바뀜",   "desc": "거래는 늘었는데 값은 평소 속도입니다"},
    "thin_rise": {"label": "얇은 상승", "desc": "거래는 안 늘었는데 값만 평소보다 빠릅니다"},
    "quiet":     {"label": "잠잠",     "desc": "거래도 값도 평소보다 조용합니다"},
    "normal":    {"label": "평소대로",  "desc": "평소와 비슷한 범위 안입니다"},
    "thin":      {"label": "표본 부족", "desc": "거래가 너무 적어 판단하지 않습니다"},
    "unknown":   {"label": "기록 부족", "desc": "비교할 과거가 모자랍니다"},
}

# 색은 content/design.py 토큰을 그대로 쓴다. 사이트와 인스타 카드가 같은
# 팔레트를 쓰면 같은 데이터라는 게 눈으로도 읽힌다.
# 빨강/파랑은 증감 전용이라는 규칙은 여기서도 유지한다 — 색은 **거래량**만
# 나타내고, 가격 속도는 테두리로 표시한다.
PALETTE = {"up": D.UP, "down": D.DOWN, "flat": D.NEUTRAL,
           "thin": D.LINE, "ink": D.INK, "sub": D.SUB, "accent": D.ACCENT,
           "bg": D.BG}

app = FastAPI(title="평소지도", docs_url="/api/docs")


def con() -> duckdb.DuckDBPyConnection:
    if not Path(SGG_NOW).exists():
        raise HTTPException(503, "캐시가 없습니다. python -m pulse.build_pulse 먼저 실행하세요.")
    c = duckdb.connect()
    c.execute("PRAGMA threads=4")
    return c


def rows(sql: str, params: list | None = None) -> list[dict]:
    c = con()
    try:
        cur = c.execute(sql, params or [])
        cols = [d[0] for d in cur.description]
        return [clean(dict(zip(cols, r))) for r in cur.fetchall()]
    finally:
        c.close()


def clean(r: dict) -> dict:
    """NaN·Inf 를 None 으로. JSON 으로 나가면 프런트에서 조용히 깨진다."""
    out = {}
    for k, v in r.items():
        if isinstance(v, float) and (v != v or v in (float("inf"), float("-inf"))):
            out[k] = None
        elif hasattr(v, "isoformat"):
            out[k] = v.isoformat()[:10]
        else:
            out[k] = v
    return out


def level_of(level: str) -> dict:
    if level not in LEVELS:
        raise HTTPException(400, f"level 은 {list(LEVELS)} 중 하나")
    return LEVELS[level]


def deal_dir(z) -> str:
    """거래량 방향. 색은 이것만 따른다."""
    if z is None:
        return "flat"
    return "up" if z >= 1 else ("down" if z <= -1 else "flat")


# ── 메타 ─────────────────────────────────────────────────────────────────
@app.get("/api/meta")
def meta() -> dict:
    m = rows(f"SELECT * FROM read_parquet('{META}')")[0]
    dist = rows(f"""
        SELECT state, count(*) AS n FROM read_parquet('{SGG_NOW}')
        GROUP BY 1 ORDER BY 2 DESC""")
    return {
        **m,
        "states": STATES,
        "palette": PALETTE,
        "levels": {k: {"label": v["label"], "window": v["window"]}
                   for k, v in LEVELS.items()},
        "distribution": dist,
        "pyeongs": [{"code": c, "label": PYEONG_LABEL[c]} for c in PYEONG_ORDER],
        "source": "국토교통부 실거래가 공개시스템 · 해제(취소) 건 제외",
        # 면책은 '변경 금지' 고정 문구다. 화면용으로 다시 쓰지 않고 승인된
        # 문구를 그대로 내려보낸다 — 스레드·인스타·캐러셀과 같은 문장이다.
        "disclaimer": DISCLAIMER_SOCIAL,
    }


# ── 지도 ─────────────────────────────────────────────────────────────────
@app.get("/api/regions")
def regions(level: str = Query("sgg"),
            bbox: str | None = Query(None)) -> dict:
    cfg = level_of(level)
    where, params = ["lat IS NOT NULL"], []
    if bbox:
        try:
            w, s, e, n = (float(x) for x in bbox.split(","))
        except ValueError:
            raise HTTPException(400, "bbox 는 'w,s,e,n' 형식")
        where.append("lng BETWEEN ? AND ? AND lat BETWEEN ? AND ?")
        params += [w, e, s, n]
    out = rows(f"""
        SELECT code, name, region, week_start, state,
               deals, round(deals_avg, 1) AS deals_usual,
               round(r_deals, 2) AS ratio,
               round(ppy) AS ppy, round(ppy_chg, 1) AS chg,
               round(chg_avg, 1) AS chg_usual,
               z_deals, z_ppy, lat, lng
        FROM read_parquet('{cfg["now"]}')
        WHERE {' AND '.join(where)}
    """, params)
    for r in out:
        r["dir"] = deal_dir(r.pop("z_deals"))
        r["fast"] = (r["z_ppy"] or 0) >= 1      # 값이 평소보다 빠르게 오름
        r["slow"] = (r.pop("z_ppy") or 0) <= -1
    return {"level": level, "window": cfg["window"], "items": out}


# ── 양 끝 ────────────────────────────────────────────────────────────────
@app.get("/api/extremes")
def extremes(level: str = Query("sgg"), n: int = Query(5, le=20)) -> dict:
    """평소와 가장 많이 달랐던 곳 — 위아래 양쪽.

    위쪽만 보여주면 "거래가 늘고 있다"로 읽힌다. 같은 주에 평소의 절반만
    거래된 곳도 있다. 양 끝을 같은 화면에 둔다 (캐러셀 3장과 같은 원칙).
    """
    cfg = level_of(level)
    base = f"""
        SELECT code, name, region, state, deals,
               round(deals_avg, 1) AS deals_usual, round(r_deals, 2) AS ratio,
               round(ppy_chg, 1) AS chg, round(chg_avg, 1) AS chg_usual
        FROM read_parquet('{cfg["now"]}')
        WHERE state NOT IN ('thin', 'unknown') AND r_deals IS NOT NULL
    """
    return {
        "level": level, "window": cfg["window"],
        # 분포를 같이 실어 보낸다. 헤드라인("82곳 중 57곳은 평소대로")이
        # 레벨을 따라가야 하는데, 따로 받으면 목록만 바뀌고 헤드라인은
        # 시군구에 머문 채로 남는다.
        "distribution": rows(f"""
            SELECT state, count(*) AS n FROM read_parquet('{cfg["now"]}')
            GROUP BY 1 ORDER BY 2 DESC"""),
        "busy": rows(f"{base} ORDER BY ratio DESC LIMIT {n}"),
        "quiet": rows(f"{base} ORDER BY ratio ASC LIMIT {n}"),
    }


# ── 지역 상세 ────────────────────────────────────────────────────────────
@app.get("/api/region/{level}/{code}")
def region(level: str, code: str) -> dict:
    cfg = level_of(level)
    now = rows(f"""
        SELECT code, name, region, week_start, state, deals,
               round(deals_avg, 1) AS deals_usual, round(r_deals, 2) AS ratio,
               round(ppy) AS ppy, round(ppy_chg, 1) AS chg,
               round(chg_avg, 1) AS chg_usual, hist_weeks, z_deals, z_ppy,
               lat, lng
        FROM read_parquet('{cfg["now"]}') WHERE code = ?""", [code])
    if not now:
        raise HTTPException(404, "지역을 찾을 수 없습니다")
    r = now[0]
    r["dir"] = deal_dir(r.pop("z_deals"))
    r["fast"] = (r["z_ppy"] or 0) >= 1
    r["slow"] = (r.pop("z_ppy") or 0) <= -1

    series = rows(f"""
        SELECT week_start, deals, round(deals_avg, 1) AS deals_usual,
               round(ppy) AS ppy, round(ppy_chg, 1) AS chg
        FROM read_parquet('{cfg["weeks"]}')
        WHERE code = ? ORDER BY week_start DESC LIMIT {SPARK_WEEKS}""", [code])
    series.reverse()

    # 단지는 시군구/읍면동 어느 쪽으로도 걸러낼 수 있어야 한다
    col = "sigungu_code" if level == "sgg" else "legal_dong_code"
    apts = rows(f"""
        SELECT apt_id, apt_name, legal_dong_name, build_year,
               n_recent, n_prior, round(ppy_recent) AS ppy,
               round(chg_pct, 1) AS chg, thin, lat, lng
        FROM read_parquet('{APT_NOW}')
        WHERE {col} = ?
        ORDER BY thin ASC, abs(chg_pct) DESC
        LIMIT 60""", [code])
    return {"level": level, "window": cfg["window"], "now": r,
            "series": series, "apts": apts, "state": STATES.get(r["state"], {})}


# ── 단지 ─────────────────────────────────────────────────────────────────
def apt_dir(chg, thin) -> str:
    if thin or chg is None:
        return "thin"
    return "up" if chg >= APT_DIR_BAND else ("down" if chg <= -APT_DIR_BAND else "flat")


M2_PER_PYEONG = 3.305785


def decorate(r: dict) -> dict:
    """마커·목록이 쓸 표시용 필드를 붙인다."""
    r["dir"] = apt_dir(r.get("chg"), r.get("thin"))
    r["pyeong_label"] = PYEONG_LABEL.get(r.get("pyeong_bucket"), r.get("pyeong_bucket"))
    # 마커에 박을 짧은 평형.
    #
    # 버킷 라벨("20평대 후반")은 말풍선에 넣기엔 길고, 범위라 어느 거래를
    # 말하는지도 흐리다. **그 거래의 실제 전용면적**을 평으로 환산해 쓴다 —
    # 가격과 면적이 같은 거래에서 나온 한 쌍이 되므로 더 정확하다.
    a = r.get("last_area")
    r["pyeong_short"] = f"{a / M2_PER_PYEONG:.0f}평" if a else None
    return r


APT_COLS = """
    apt_id, apt_name, sigungu_name, legal_dong_name, build_year,
    pyeong_bucket, last_date, last_price, round(last_ppy) AS last_ppy,
    last_floor, last_area, n_1y, n_recent, n_prior,
    round(chg_pct, 1) AS chg, round(vs_peak_pct, 1) AS vs_peak,
    peak_price, peak_date, thin, lat, lng
"""


@app.get("/api/apts")
def apts(bbox: str | None = Query(None), q: str | None = Query(None),
         pyeong: str | None = Query(None),
         limit: int = Query(220, le=600)) -> dict:
    """지도 마커용 단지 목록.

    `pyeong` 을 주면 그 평형 기준으로 값이 바뀐다 — 평형을 고르면 마커 가격도
    같이 바뀌어야 한다. 안 주면 대표 평형(최근 1년 거래가 가장 많은 평형)이다.
    """
    src, where, params = APT_NOW, ["lat IS NOT NULL"], []
    if pyeong:
        want = [p for p in pyeong.split(",") if p in PYEONG_ORDER]
        if not want:
            raise HTTPException(400, f"pyeong 은 {PYEONG_ORDER} 중에서")
        src = APT_PY
        where.append("pyeong_bucket IN (" + ",".join("?" * len(want)) + ")")
        params += want
        where.append("last_date > current_date - INTERVAL 730 DAY")
    if bbox:
        try:
            w, s_, e, n = (float(x) for x in bbox.split(","))
        except ValueError:
            raise HTTPException(400, "bbox 는 'w,s,e,n' 형식")
        where.append("lng BETWEEN ? AND ? AND lat BETWEEN ? AND ?")
        params += [w, e, s_, n]
    if q:
        where.append("apt_name ILIKE ?")
        params.append(f"%{q}%")
    # 거래가 많은 단지를 먼저 남긴다. 겹쳐서 잘릴 때 표본이 두터운 쪽이 살아야 한다.
    items = rows(f"""SELECT {APT_COLS} FROM read_parquet('{src}')
        WHERE {' AND '.join(where)}
        ORDER BY n_1y DESC, last_date DESC LIMIT {limit}""", params)
    total = rows(f"""SELECT count(*) AS n FROM read_parquet('{src}')
        WHERE {' AND '.join(where)}""", params)[0]["n"]
    return {"items": [decorate(r) for r in items], "total": total,
            "truncated": total > len(items), "pyeong": pyeong}


@app.get("/api/apt/{apt_id}")
def apt_detail(apt_id: str) -> dict:
    """단지 상세 — 평형을 전부 펼친다.

    한 단지를 한 숫자로 요약하지 않는다. 평형마다 가격도 거래도 다르고,
    그걸 접으면 어느 평형을 보는 사람에게든 틀린 값이 된다.
    """
    py = rows(f"""SELECT {APT_COLS}, n_total FROM read_parquet('{APT_PY}')
        WHERE apt_id = ?""", [apt_id])
    if not py:
        raise HTTPException(404, "단지를 찾을 수 없습니다")
    py.sort(key=lambda r: PYEONG_ORDER.index(r["pyeong_bucket"])
            if r["pyeong_bucket"] in PYEONG_ORDER else 99)
    head = max(py, key=lambda r: (r["n_1y"], r["n_total"]))
    # 이 단지가 속한 지역이 지금 평소와 다른지도 같이 보여준다 — 단지만 보면
    # 동네 전체가 움직인 건지 이 단지만 움직인 건지 알 수 없다.
    region = rows(f"""
        SELECT name, state, deals, round(deals_avg, 1) AS deals_usual,
               round(r_deals, 2) AS ratio
        FROM read_parquet('{DONG_NOW}')
        WHERE code = (SELECT legal_dong_code FROM read_parquet('{APT_PY}')
                      WHERE apt_id = ? LIMIT 1)""", [apt_id])
    return {"apt": decorate(head), "pyeongs": [decorate(r) for r in py],
            "region": region[0] if region else None,
            "region_state": STATES.get(region[0]["state"], {}) if region else {}}


@app.get("/api/search")
def search(q: str = Query(..., min_length=1), limit: int = Query(10, le=30)) -> dict:
    like = f"%{q}%"
    reg = rows(f"""
        SELECT 'sgg' AS level, code, name, region, lat, lng
        FROM read_parquet('{SGG_NOW}') WHERE name ILIKE ?
        UNION ALL
        SELECT 'dong', code, name, region, lat, lng
        FROM read_parquet('{DONG_NOW}') WHERE name ILIKE ?
        LIMIT {limit}""", [like, like])
    apt = rows(f"""
        SELECT apt_id, apt_name, sigungu_name, legal_dong_name, lat, lng
        FROM read_parquet('{APT_NOW}')
        WHERE apt_name ILIKE ? ORDER BY n_recent DESC LIMIT {limit}""", [like])
    return {"regions": reg, "apts": apt}


@app.get("/api/health")
def health() -> dict:
    files = {p.name: p.stat().st_size for p in CACHE.glob("*.parquet")} \
        if CACHE.exists() else {}
    return {"ok": bool(files), "cache": files}


# ── 정적 ─────────────────────────────────────────────────────────────────
@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


# 폰트는 SNS 이미지와 같은 파일을 쓴다 (assets/fonts). 사이트만 다른 글꼴이면
# 같은 데이터라는 느낌이 끊긴다.
FONTS = ROOT / "assets" / "fonts"
if FONTS.exists():
    app.mount("/fonts", StaticFiles(directory=FONTS), name="fonts")

app.mount("/", StaticFiles(directory=STATIC), name="static")
