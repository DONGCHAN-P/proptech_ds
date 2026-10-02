"""호갱노노 스타일 수도권 아파트 실거래 지도 — FastAPI 백엔드.

web/cache/ 의 파케이 인덱스를 DuckDB로 조회한다. 캐시가 없으면 기동 시
build_index.py 를 자동 실행한다.

실행:  .venv\\Scripts\\python.exe -m uvicorn web.main:app --reload
       또는 web\\run.bat
"""
from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
import threading
from datetime import date
from pathlib import Path
from typing import Any

import duckdb
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
CACHE = HERE / "cache"
STATIC = HERE / "static"
DB_PATH = BASE / "legacy" / "realestate.db"
EXPORTS = BASE / "exports" / "daily"

APT = (CACHE / "apt_index.parquet").as_posix()
PYEONG = (CACHE / "apt_pyeong.parquet").as_posix()
TRADES = (CACHE / "trades.parquet").as_posix()
REGION = (CACHE / "region_index.parquet").as_posix()

PYEONG_ORDER = ["10P", "15P", "20P", "25P", "30P", "35P", "40P", "50P", "60P+"]
PYEONG_LABEL = {
    "10P": "~10평", "15P": "10~15평", "20P": "15~20평", "25P": "20~25평",
    "30P": "25~30평", "35P": "30~35평", "40P": "35~40평",
    "50P": "40~50평", "60P+": "50평~",
}

ATTRIB = "실거래가 출처 국토교통부"

# 배경 지도. 기본은 키가 필요 없는 OSM.
# VWorld 를 쓰려면 환경변수 VWORLD_MAP_KEY 를 넣는다 (vworld.kr 에서 발급한
# 키에 접속 도메인이 등록돼 있어야 하고, localhost 도 따로 등록해야 한다).
# CARTO basemaps 는 등록되지 않은 도메인에 "API KEY REQUIRED" 워터마크가
# 찍힌 타일을 내려주므로 쓰지 않는다.
def tile_config() -> dict:
    key = os.environ.get("VWORLD_MAP_KEY", "").strip()
    if key:
        return {
            "url": f"https://api.vworld.kr/req/wmts/1.0.0/{key}/Base/{{z}}/{{y}}/{{x}}.png",
            "attribution": f"&copy; VWorld · {ATTRIB}",
            "maxZoom": 18,
        }
    return {
        "url": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        "attribution": f"&copy; OpenStreetMap contributors · {ATTRIB}",
        "maxZoom": 19,
    }


app = FastAPI(title="수도권 아파트 실거래 지도", default_response_class=JSONResponse)

_con: duckdb.DuckDBPyConnection | None = None
_lock = threading.Lock()


# ── 부팅 ──────────────────────────────────────────────────────────────
def ensure_cache() -> None:
    if (CACHE / "apt_index.parquet").exists():
        return
    print("[web] 캐시 없음 — build_index.py 실행", flush=True)
    subprocess.run([sys.executable, str(HERE / "build_index.py")], check=True)


def con() -> duckdb.DuckDBPyConnection:
    """요청별 커서. DuckDB 커넥션은 스레드 간 공유가 안전하지 않다."""
    global _con
    if _con is None:
        with _lock:
            if _con is None:
                ensure_cache()
                _con = duckdb.connect()
    return _con.cursor()


def rows(sql: str, params: list[Any] | None = None) -> list[dict]:
    df = con().execute(sql, params or []).df()
    return clean(df.to_dict(orient="records"))


def clean(recs: list[dict]) -> list[dict]:
    """NaN/NaT/numpy 타입을 JSON 직렬화 가능한 형태로."""
    out = []
    for r in recs:
        d = {}
        for k, v in r.items():
            if v is None:
                d[k] = None
            elif hasattr(v, "isoformat"):
                d[k] = v.isoformat()[:10]
            elif isinstance(v, float):
                d[k] = None if v != v else round(v, 4)
            elif hasattr(v, "item"):
                try:
                    d[k] = v.item()
                except Exception:
                    d[k] = str(v)
            else:
                d[k] = v
        out.append(d)
    return out


# ── 필터 → SQL ────────────────────────────────────────────────────────
class Filters:
    """쿼리스트링을 WHERE 절 + 파라미터로 옮긴다.

    평형(pyeong)이 지정되면 마커 가격의 기준이 대표 평형에서 선택 평형으로
    바뀌므로, price/ppy 관련 조건은 apt 테이블이 아니라 조인된 평형 행에
    걸어야 한다. 그 분기는 apt_source() 가 담당한다.
    """

    def __init__(
        self,
        region: str | None = None,
        sgg: str | None = None,
        pyeong: str | None = None,
        price_min: float | None = None,
        price_max: float | None = None,
        built_from: int | None = None,
        built_to: int | None = None,
        walk_max: float | None = None,
        infra_min: float | None = None,
        redv: bool = False,
        gtx: bool = False,
        chg_min: float | None = None,
        active_only: bool = False,
        q: str | None = None,
    ):
        self.region = region
        self.sgg = [s for s in (sgg or "").split(",") if s]
        self.pyeong = [p for p in (pyeong or "").split(",") if p in PYEONG_ORDER]
        self.price_min, self.price_max = price_min, price_max
        self.built_from, self.built_to = built_from, built_to
        self.walk_max, self.infra_min = walk_max, infra_min
        self.redv, self.gtx = redv, gtx
        self.chg_min = chg_min
        self.active_only = active_only
        self.q = (q or "").strip()

    def apt_source(self) -> tuple[str, list, list]:
        """(FROM 절, WHERE 조건 리스트, 파라미터). 평형 필터 시 서브쿼리로 감싼다."""
        params: list[Any] = []
        where: list[str] = []

        if self.pyeong:
            ph = ", ".join("?" * len(self.pyeong))
            params.extend(self.pyeong)
            src = f"""(
                SELECT a.* EXCLUDE (rep_pyeong, rep_area, rep_price, rep_ppy,
                                    rep_ppy_1y, chg_1y, chg_3y, vs_peak,
                                    trade_1y, trade_3m, peak_price, peak_date),
                       s.pyeong_bucket AS rep_pyeong, s.area_m2 AS rep_area,
                       s.last_price AS rep_price, s.last_ppy AS rep_ppy,
                       s.ppy_1y AS rep_ppy_1y, s.chg_1y, s.chg_3y, s.vs_peak,
                       s.trade_1y, s.trade_3m, s.peak_price, s.peak_date,
                       s.last_date AS rep_last_date
                FROM '{APT}' a
                JOIN (
                    SELECT *, row_number() OVER (PARTITION BY apt_id
                              ORDER BY trade_1y DESC, trade_total DESC) AS rn
                    FROM '{PYEONG}' WHERE pyeong_bucket IN ({ph})
                ) s ON s.apt_id = a.apt_id AND s.rn = 1
            )"""
        else:
            src = f"(SELECT *, last_date AS rep_last_date FROM '{APT}')"

        if self.region:
            where.append("region = ?")
            params.append(self.region)
        if self.sgg:
            where.append(f"sigungu_code IN ({', '.join('?' * len(self.sgg))})")
            params.extend(self.sgg)
        if self.price_min is not None:
            where.append("rep_price >= ?")
            params.append(self.price_min)
        if self.price_max is not None:
            where.append("rep_price <= ?")
            params.append(self.price_max)
        if self.built_from is not None:
            where.append("build_year >= ?")
            params.append(self.built_from)
        if self.built_to is not None:
            where.append("build_year <= ?")
            params.append(self.built_to)
        if self.walk_max is not None:
            where.append("walk_min <= ?")
            params.append(self.walk_max)
        if self.infra_min is not None:
            where.append("infra_score >= ?")
            params.append(self.infra_min)
        if self.redv:
            where.append("redv_nearby > 0")
        if self.gtx:
            where.append("gtx_dist > 0 AND gtx_dist <= 3000")
        if self.chg_min is not None:
            where.append("chg_1y >= ?")
            params.append(self.chg_min)
        if self.active_only:
            where.append("trade_1y > 0")
        if self.q:
            where.append("(apt_name ILIKE ? OR legal_dong_name ILIKE ? OR sigungu_name ILIKE ?)")
            params.extend([f"%{self.q}%"] * 3)
        return src, where, params


def bbox_clause(bbox: str | None, where: list[str], params: list) -> None:
    if not bbox:
        return
    try:
        s, w, n, e = (float(x) for x in bbox.split(","))
    except ValueError:
        return
    where.append("lat BETWEEN ? AND ? AND lng BETWEEN ? AND ?")
    params.extend([s, n, w, e])


# ── 엔드포인트 ────────────────────────────────────────────────────────
@app.get("/api/meta")
def meta() -> dict:
    sgg = rows(f"""
        SELECT sigungu_code AS code, any_value(sigungu_name) AS name,
               any_value(region) AS region, count(*) AS cnt
        FROM '{APT}' GROUP BY 1 ORDER BY 3, 2
    """)
    stat = rows(f"""
        SELECT count(*) AS apt_cnt,
               max(last_date) AS last_trade,
               min(build_year) AS built_min, max(build_year) AS built_max
        FROM '{APT}'
    """)[0]
    tot = rows(f"SELECT count(*) AS n, min(deal_date) AS first FROM '{TRADES}'")[0]
    return {
        "sigungu": sgg,
        "regions": ["서울", "경기", "인천"],
        "pyeong": [{"key": k, "label": PYEONG_LABEL[k]} for k in PYEONG_ORDER],
        "stat": {**stat, "trade_cnt": tot["n"], "first_trade": tot["first"]},
        "tiles": tile_config(),
    }


@app.get("/api/map")
def map_data(
    zoom: float = Query(11),
    bbox: str | None = Query(None),
    limit: int = Query(800, le=3000),
    region: str | None = Query(None),
    sgg: str | None = Query(None),
    pyeong: str | None = Query(None),
    price_min: float | None = Query(None),
    price_max: float | None = Query(None),
    built_from: int | None = Query(None),
    built_to: int | None = Query(None),
    walk_max: float | None = Query(None),
    infra_min: float | None = Query(None),
    redv: bool = Query(False),
    gtx: bool = Query(False),
    chg_min: float | None = Query(None),
    active_only: bool = Query(False),
    q: str | None = Query(None),
) -> dict:
    """줌 레벨에 따라 시군구 → 읍면동 → 단지 말풍선을 돌려준다."""
    flt = Filters(region, sgg, pyeong, price_min, price_max, built_from, built_to,
                  walk_max, infra_min, redv, gtx, chg_min, active_only, q)
    src, where, params = flt.apt_source()

    has_filter = bool(where)
    level = "apt" if zoom >= 14 else ("dong" if zoom >= 12 else "sgg")

    # 필터가 걸리면 사전 집계 테이블을 못 쓰므로 그때그때 집계한다.
    if level == "apt":
        bbox_clause(bbox, where, params)
        w = ("WHERE " + " AND ".join(where)) if where else ""
        data = rows(f"""
            SELECT apt_id, apt_name, sigungu_name, legal_dong_name, lat, lng,
                   build_year, rep_pyeong, rep_area, rep_price,
                   coalesce(rep_ppy_1y, rep_ppy) AS ppy,
                   chg_1y, vs_peak, trade_1y, walk_min, nearest_station,
                   infra_score, redv_nearby, rep_last_date
            FROM {src} {w}
            ORDER BY trade_1y DESC, rep_price DESC
            LIMIT {limit}
        """, params)
        total = rows(f"SELECT count(*) AS n FROM {src} {w}", params)[0]["n"]
        return {"level": level, "total": total, "items": data}

    group = "sigungu_code" if level == "sgg" else "legal_dong_code"
    name = "sigungu_name" if level == "sgg" else "legal_dong_name"
    if not has_filter and not bbox:
        lvl = "sgg" if level == "sgg" else "dong"
        data = rows(f"""
            SELECT code, name, parent, region, apt_cnt, trade_1y, ppy, chg_1y, lat, lng
            FROM '{REGION}' WHERE level = ? ORDER BY apt_cnt DESC LIMIT {limit}
        """, [lvl])
        return {"level": level, "total": len(data), "items": data}

    bbox_clause(bbox, where, params)
    w = ("WHERE " + " AND ".join(where)) if where else ""
    data = rows(f"""
        SELECT {group} AS code, any_value({name}) AS name,
               any_value(sigungu_name) AS parent, any_value(region) AS region,
               count(*) AS apt_cnt, sum(trade_1y) AS trade_1y,
               round(median(coalesce(rep_ppy_1y, rep_ppy))) AS ppy,
               round(median(chg_1y), 1) AS chg_1y,
               avg(lat) AS lat, avg(lng) AS lng
        FROM {src} {w}
        GROUP BY 1 ORDER BY apt_cnt DESC LIMIT {limit}
    """, params)
    return {"level": level, "total": len(data), "items": data}


@app.get("/api/list")
def apt_list(
    bbox: str | None = Query(None),
    sort: str = Query("trade"),
    limit: int = Query(60, le=300),
    offset: int = Query(0),
    region: str | None = Query(None),
    sgg: str | None = Query(None),
    pyeong: str | None = Query(None),
    price_min: float | None = Query(None),
    price_max: float | None = Query(None),
    built_from: int | None = Query(None),
    built_to: int | None = Query(None),
    walk_max: float | None = Query(None),
    infra_min: float | None = Query(None),
    redv: bool = Query(False),
    gtx: bool = Query(False),
    chg_min: float | None = Query(None),
    active_only: bool = Query(False),
    q: str | None = Query(None),
) -> dict:
    """지도 화면 안의 단지 목록(좌측 리스트)."""
    flt = Filters(region, sgg, pyeong, price_min, price_max, built_from, built_to,
                  walk_max, infra_min, redv, gtx, chg_min, active_only, q)
    src, where, params = flt.apt_source()
    bbox_clause(bbox, where, params)
    w = ("WHERE " + " AND ".join(where)) if where else ""
    order = {
        "trade": "trade_1y DESC, rep_price DESC",
        "price_desc": "rep_price DESC",
        "price_asc": "rep_price ASC",
        "ppy_desc": "coalesce(rep_ppy_1y, rep_ppy) DESC",
        "ppy_asc": "coalesce(rep_ppy_1y, rep_ppy) ASC",
        "chg_desc": "chg_1y DESC NULLS LAST",
        "chg_asc": "chg_1y ASC NULLS LAST",
        "new": "build_year DESC",
        "old": "build_year ASC",
        "recent": "rep_last_date DESC",
    }.get(sort, "trade_1y DESC")
    items = rows(f"""
        SELECT apt_id, apt_name, sigungu_name, legal_dong_name, lat, lng,
               build_year, rep_pyeong, rep_area, rep_price,
               coalesce(rep_ppy_1y, rep_ppy) AS ppy,
               chg_1y, vs_peak, trade_1y, walk_min, nearest_station, nearest_line,
               infra_score, redv_nearby, rep_last_date
        FROM {src} {w} ORDER BY {order} LIMIT {limit} OFFSET {offset}
    """, params)
    total = rows(f"SELECT count(*) AS n FROM {src} {w}", params)[0]["n"]
    return {"total": total, "items": items}


@app.get("/api/apt/{apt_id}")
def apt_detail(apt_id: str) -> dict:
    base = rows(f"SELECT * FROM '{APT}' WHERE apt_id = ?", [apt_id])
    if not base:
        raise HTTPException(404, "단지를 찾을 수 없습니다")
    info = base[0]
    pyeongs = rows(f"""
        SELECT pyeong_bucket, area_m2, last_date, last_price, last_ppy, last_floor,
               last_area_m2, trade_total, trade_1y, trade_3m,
               peak_price, peak_date, ppy_1y, chg_1y, chg_3y, vs_peak
        FROM '{PYEONG}' WHERE apt_id = ?
        ORDER BY array_position({PYEONG_ORDER!r}::VARCHAR[], pyeong_bucket)
    """, [apt_id])
    for p in pyeongs:
        p["label"] = PYEONG_LABEL.get(p["pyeong_bucket"], p["pyeong_bucket"])
    info["nearby"] = nearby(info.get("lat"), info.get("lng"))
    return {"info": info, "pyeongs": pyeongs}


@app.get("/api/apt/{apt_id}/trades")
def apt_trades(
    apt_id: str,
    pyeong: str | None = Query(None),
    limit: int = Query(80, le=500),
) -> dict:
    where = ["apt_id = ?"]
    params: list[Any] = [apt_id]
    if pyeong:
        where.append("pyeong_bucket = ?")
        params.append(pyeong)
    items = rows(f"""
        SELECT deal_date, deal_amount, area_m2, floor, pyeong_bucket,
               round(price_per_pyeong) AS ppy
        FROM '{TRADES}' WHERE {' AND '.join(where)}
        ORDER BY deal_date DESC LIMIT {limit}
    """, params)
    return {"items": items}


@app.get("/api/apt/{apt_id}/series")
def apt_series(apt_id: str, pyeong: str | None = Query(None)) -> dict:
    """월별 평균 실거래가 추이 (평형 지정 시 해당 평형만)."""
    where = ["apt_id = ?"]
    params: list[Any] = [apt_id]
    if pyeong:
        where.append("pyeong_bucket = ?")
        params.append(pyeong)
    items = rows(f"""
        SELECT strftime(date_trunc('month', deal_date), '%Y-%m') AS ym,
               round(avg(deal_amount)) AS price,
               round(avg(price_per_pyeong)) AS ppy,
               count(*) AS cnt
        FROM '{TRADES}' WHERE {' AND '.join(where)}
        GROUP BY 1 ORDER BY 1
    """, params)
    return {"items": items}


@app.get("/api/search")
def search(q: str = Query(..., min_length=1), limit: int = Query(12, le=40)) -> dict:
    like = f"%{q.strip()}%"
    items = rows(f"""
        SELECT apt_id, apt_name, sigungu_name, legal_dong_name, lat, lng,
               rep_price, coalesce(rep_ppy_1y, rep_ppy) AS ppy, build_year
        FROM '{APT}'
        WHERE apt_name ILIKE ?
        ORDER BY CASE WHEN apt_name ILIKE ? THEN 0 ELSE 1 END, trade_1y DESC
        LIMIT {limit}
    """, [like, f"{q.strip()}%"])
    regions = rows(f"""
        SELECT level, code, name, parent, lat, lng, apt_cnt, ppy
        FROM '{REGION}' WHERE name ILIKE ? ORDER BY apt_cnt DESC LIMIT 6
    """, [like])
    return {"apts": items, "regions": regions}


@app.get("/api/rankings")
def rankings(
    kind: str = Query("undervalue"),
    region: str | None = Query(None),
    sgg: str | None = Query(None),
    limit: int = Query(40, le=200),
) -> dict:
    """저평가(step7) / 신고가·급등(step8) / 급등·급락(자체 집계) 랭킹."""
    if kind == "undervalue":
        return {"kind": kind, "items": load_undervalue(region, sgg, limit)}
    if kind == "newhigh":
        return {"kind": kind, "items": load_newhigh(region, sgg, limit)}

    where = ["trade_1y >= 3", "chg_1y IS NOT NULL"]
    params: list[Any] = []
    if region:
        where.append("region = ?")
        params.append(region)
    if sgg:
        codes = [s for s in sgg.split(",") if s]
        if codes:
            where.append(f"sigungu_code IN ({', '.join('?' * len(codes))})")
            params.extend(codes)
    direction = "DESC" if kind == "surge" else "ASC"
    items = rows(f"""
        SELECT apt_id, apt_name, sigungu_name, legal_dong_name, lat, lng,
               rep_pyeong, rep_price, coalesce(rep_ppy_1y, rep_ppy) AS ppy,
               chg_1y, vs_peak, trade_1y
        FROM '{APT}' WHERE {' AND '.join(where)}
        ORDER BY chg_1y {direction} LIMIT {limit}
    """, params)
    return {"kind": kind, "items": items}


def latest_export(pattern: str) -> Path | None:
    files = sorted(EXPORTS.glob(pattern))
    return files[-1] if files else None


def apt_by_name(keys: str) -> str:
    """이름 기반 조인용 단지 테이블 — 같은 이름이 여러 단지면 거래 많은 쪽 하나만.

    step7/step8 산출물에는 apt_id 가 없거나 구버전이라 이름으로 이어야 하는데,
    한 동에 동명 단지가 여럿이면 랭킹 행이 통째로 복제된다. 미리 접어둔다.
    """
    return f"""(
        SELECT * EXCLUDE (rn) FROM (
            SELECT *, row_number() OVER (PARTITION BY {keys}
                        ORDER BY trade_total DESC, trade_1y DESC) AS rn
            FROM '{APT}'
        ) WHERE rn = 1
    )"""


def load_undervalue(region: str | None, sgg: str | None, limit: int) -> list[dict]:
    p = latest_export("undervalue_top5_*.parquet")
    if p is None:
        return []
    where, params = [], []
    if region:
        where.append("u.region = ?")
        params.append(region)
    if sgg:
        codes = [s for s in sgg.split(",") if s]
        if codes:
            where.append(f"u.sigungu_code IN ({', '.join('?' * len(codes))})")
            params.extend(codes)
    w = ("WHERE " + " AND ".join(where)) if where else ""
    # step7 산출물은 구버전 apt_id 이므로 (시군구, 단지명, 평형)으로 다시 잇는다.
    return rows(f"""
        SELECT u.apt_name, u.sigungu_name, u.region, u.pyeong_bucket, u.rank,
               u.last_price, u.price_per_pyeong AS ppy, u.rel_value_pct,
               u.price_vs_median, u.yoy_change, u.infra_score, u.reason,
               u.snapshot_date, a.apt_id, a.lat, a.lng, a.legal_dong_name,
               a.build_year, a.chg_1y
        FROM '{p.as_posix()}' u
        LEFT JOIN {apt_by_name('sigungu_code, apt_name')} a
               ON a.sigungu_code = u.sigungu_code
              AND a.apt_name = u.apt_name
        {w}
        ORDER BY u.value_score DESC LIMIT {limit}
    """, params)


def load_newhigh(region: str | None, sgg: str | None, limit: int) -> list[dict]:
    p = latest_export("new_trades_notable_*.csv")
    if p is None:
        return []
    where, params = [], []
    if sgg:
        # csv 에는 시군구 코드가 없어 이름으로 거른다.
        names = rows(
            f"SELECT DISTINCT sigungu_name AS n FROM '{APT}' WHERE sigungu_code IN "
            f"({', '.join('?' * len(sgg.split(',')))})", sgg.split(","))
        vals = [x["n"] for x in names]
        if vals:
            where.append(f"n.sigungu_name IN ({', '.join('?' * len(vals))})")
            params.extend(vals)
    if region:
        where.append("a.region = ?")
        params.append(region)
    w = ("WHERE " + " AND ".join(where)) if where else ""
    return rows(f"""
        SELECT n.sigungu_name, n.legal_dong_name, n.apt_name_raw AS apt_name,
               n.area_m2, n.floor, n.deal_date, n.deal_amount, n.ref_avg,
               n.ref_count, n.deviation_pct,
               a.apt_id, a.lat, a.lng, a.build_year, a.chg_1y, a.rep_ppy_1y AS ppy
        FROM read_csv_auto('{p.as_posix()}') n
        LEFT JOIN {apt_by_name('sigungu_name, legal_dong_name, apt_name')} a
               ON a.sigungu_name = n.sigungu_name
              AND a.legal_dong_name = n.legal_dong_name
              AND a.apt_name = n.apt_name_raw
        {w}
        ORDER BY n.deviation_pct DESC LIMIT {limit}
    """, params)


def nearby(lat: float | None, lng: float | None) -> dict:
    """반경 1.2km 내 지하철역·학교·공원. sqlite 는 요청마다 열고 닫는다."""
    empty = {"stations": [], "schools": [], "parks": []}
    if lat is None or lng is None or not DB_PATH.exists():
        return empty
    d = 0.014  # 위도 약 1.5km
    dl = d / 0.79  # 경도 보정(위도 37.5도)
    box = (lat - d, lat + d, lng - dl, lng + dl)
    dist = ("((lat-?)*111.0)*((lat-?)*111.0) + ((lng-?)*88.0)*((lng-?)*88.0)")
    dparams = (lat, lat, lng, lng)
    try:
        cx = sqlite3.connect(f"file:{DB_PATH.as_posix()}?mode=ro", uri=True)
        cx.row_factory = sqlite3.Row

        def near(table: str, cols: str, n: int) -> list[dict]:
            sql = (f"SELECT {cols}, {dist} AS d2 FROM {table} "
                   f"WHERE lat BETWEEN ? AND ? AND lng BETWEEN ? AND ? "
                   f"ORDER BY d2 LIMIT {n}")
            out = []
            for r in cx.execute(sql, dparams + box):
                item = dict(r)
                item["dist_m"] = round((item.pop("d2") ** 0.5) * 1000)
                out.append(item)
            return out

        res = {
            "stations": near("subway_stations", "station_name AS name, line, lat, lng", 5),
            "schools": near("schools", "school_name AS name, school_type AS type, lat, lng", 6),
            "parks": near("parks", "park_name AS name, park_type AS type, area_m2, lat, lng", 4),
        }
        cx.close()
        return res
    except Exception:
        return empty


@app.get("/api/health")
def health() -> dict:
    return {
        "ok": (CACHE / "apt_index.parquet").exists(),
        "cache": {p.name: p.stat().st_size for p in CACHE.glob("*.parquet")},
        "today": date.today().isoformat(),
    }


app.mount("/", StaticFiles(directory=STATIC, html=True), name="static")
