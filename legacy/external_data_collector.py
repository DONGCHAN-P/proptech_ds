"""
외부 데이터 수집 파이프라인 (로컬 버전)
=========================================
프로젝트 구조:
  REALESTATE_RECO/
    config/secrets.json     ← API 키
    raw/
      school/               ← 학교 CSV (NEIS API)
      shop/                 ← 상권 CSV (소상공인 data.go.kr)
      park/                 ← 공원 CSV (전국도시공원정보표준데이터) ★ 신규
      subway/               ← 지하철 CSV (t-data 역사마스터)       ★ 신규
    realestate.db           ← SQLite (외부 점수 저장)

실행:
  cd REALESTATE_RECO
  python external_data_collector.py           # 전체 실행
  python external_data_collector.py --step 1  # 지하철만
  python external_data_collector.py --step 2  # 학교만
  python external_data_collector.py --step 3  # 공원만
  python external_data_collector.py --step 4  # 정비구역만
  python external_data_collector.py --step 5  # 상권만
  python external_data_collector.py --score   # 단지별 점수 산출만

CSV 파일 준비:
  raw/park/전국도시공원정보표준데이터.csv
    → data.go.kr/data/15012890 (무료, cp949)
  raw/shop/소상공인시장진흥공단_상가(상권)정보.csv
    → data.go.kr/data/15083033 (무료, utf-8, 수백MB)

⏰ API 키 만료일: 2028-04-30 (발급일 2026-04-30 기준 2년)
   만료 임박 시 실행 시 자동 경고 출력
"""

import os
import csv
import sys
import json
import math
import time
import sqlite3
import argparse
import requests
from pathlib import Path
from datetime import datetime, date, timedelta
from collections import defaultdict

try:
    from tqdm import tqdm
except ImportError:
    # tqdm 없으면 더미로 대체
    def tqdm(iterable, **kwargs):
        return iterable

# ─────────────────────────────────────────────────────
# 경로 설정 (프로젝트 루트 기준)
# ─────────────────────────────────────────────────────

ROOT     = Path(__file__).parent
CONFIG   = ROOT / "config" / "secrets.json"
# 이 파일이 legacy/ 로 옮겨지면서 ROOT 가 legacy/ 가 됐는데, 원본 데이터는
# 프로젝트 루트의 raw/ 에 있다. legacy/raw/ 도 **폴더만** 남아 있어서
# "폴더가 있나"로 고르면 빈 쪽을 집는다. 실제로 그래서 "raw/shop/ 에 CSV
# 없음" 으로 조용히 건너뛰었다 — 루트에 CSV 17개가 멀쩡히 있는데도.
# 내용물이 있는 쪽을 고른다.
def _pick_raw() -> Path:
    for base in (ROOT / "raw", ROOT.parent / "raw"):
        if base.is_dir() and any(p.is_file() for p in base.rglob("*")):
            return base
    return ROOT / "raw"


RAW      = _pick_raw()
DB_PATH  = ROOT / "realestate.db"

RAW_SUBWAY  = RAW / "subway"
RAW_SCHOOL  = RAW / "school"
RAW_PARK    = RAW / "park"
RAW_SHOP    = RAW / "shop"

# 필요한 폴더 자동 생성
for folder in [RAW_SUBWAY, RAW_SCHOOL, RAW_PARK, RAW_SHOP]:
    folder.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────────────
# API 키 로딩 (config/secrets.json)
# ─────────────────────────────────────────────────────

def load_secrets() -> dict:
    """
    config/secrets.json 구조 예시:
    {
        "TDATA_API_KEY":   "YOUR-TDATA-KEY-HERE",
        "NEIS_API_KEY":    "YOUR-KEY-HERE",
        "VWORLD_API_KEY":  "YOUR-VWORLD-KEY-HERE"
    }
    """
    if not CONFIG.exists():
        print(f"⚠️  {CONFIG} 없음 → 환경변수에서 키 로드 시도")
        return {}
    with open(CONFIG, encoding="utf-8") as f:
        return json.load(f)

_secrets = load_secrets()

def get_key(name: str) -> str:
    return _secrets.get(name) or os.getenv(name, "")

API_KEYS = {
    "tdata":  get_key("TDATA_API_KEY"),
    "neis":   get_key("NEIS_API_KEY"),
    "vworld": get_key("VWORLD_API_KEY"),
}


# ─────────────────────────────────────────────────────
# ⏰ API 키 만료일 관리
# ─────────────────────────────────────────────────────

API_KEY_META = {
    "tdata": {
        "name":       "지하철역 GEOM (t-data.seoul.go.kr)",
        "issued_at":  date(2026, 4, 30),
        "expires_in": 730,
        "renew_url":  "https://t-data.seoul.go.kr/userguide/guideopenapi.do",
    },
    "neis": {
        "name":       "학교알리미 (open.neis.go.kr)",
        "issued_at":  date(2026, 4, 30),
        "expires_in": 730,
        "renew_url":  "https://open.neis.go.kr/portal/mypage/keyIssue.do",
    },
    "vworld": {
        "name":       "V-World WFS (vworld.kr)",
        "issued_at":  date(2026, 4, 30),
        "expires_in": 730,
        "renew_url":  "https://www.vworld.kr/dev/v4dv_openapilist_s002.do",
    },
}

def check_api_expiry():
    today = date.today()
    print("\n  [API 키 만료일 확인]")
    for key, meta in API_KEY_META.items():
        expire = meta["issued_at"] + timedelta(days=meta["expires_in"])
        left   = (expire - today).days
        if   left <= 0:   status = f"❌ 만료됨 ({expire}) — 즉시 재발급 필요"
        elif left <= 30:  status = f"⚠️  {left}일 후 만료 ({expire})"
        elif left <= 90:  status = f"🔔 {left}일 후 만료 ({expire})"
        else:             status = f"✅ {left}일 남음 ({expire})"
        print(f"    {meta['name']:35s}: {status}")
        if left <= 30:
            print(f"      재발급 → {meta['renew_url']}")
    print()


# ─────────────────────────────────────────────────────
# 유틸: 거리 계산
# ─────────────────────────────────────────────────────

def haversine(lat1, lng1, lat2, lng2) -> float:
    """두 좌표 간 거리 (미터)"""
    R = 6_371_000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a  = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


# ─────────────────────────────────────────────────────
# DB 초기화
# ─────────────────────────────────────────────────────

def init_db():
    con = sqlite3.connect(DB_PATH)
    con.executescript("""
    CREATE TABLE IF NOT EXISTS subway_stations (
        station_id   TEXT PRIMARY KEY,
        station_name TEXT,
        line         TEXT,
        line_grade   INTEGER,
        lat          REAL,
        lng          REAL,
        updated_at   TEXT
    );
    CREATE TABLE IF NOT EXISTS schools (
        school_id    TEXT PRIMARY KEY,
        school_name  TEXT,
        school_type  TEXT,
        gu_code      TEXT,
        lat          REAL,
        lng          REAL,
        updated_at   TEXT
    );
    CREATE TABLE IF NOT EXISTS parks (
        park_id      TEXT PRIMARY KEY,
        park_name    TEXT,
        park_type    TEXT,
        area_m2      REAL,
        lat          REAL,
        lng          REAL,
        updated_at   TEXT
    );
    CREATE TABLE IF NOT EXISTS rivers (
        river_id     TEXT PRIMARY KEY,
        river_name   TEXT,
        lat          REAL,
        lng          REAL,
        updated_at   TEXT
    );
    CREATE TABLE IF NOT EXISTS redevelopment_zones (
        zone_id          TEXT PRIMARY KEY,
        zone_name        TEXT,
        zone_type        TEXT,
        status           TEXT,
        gu_code          TEXT,
        lat              REAL,
        lng              REAL,
        area_m2          REAL,
        permit_year      INTEGER,
        updated_at       TEXT
    );
    CREATE TABLE IF NOT EXISTS commerce_zones (
        grid_id          TEXT PRIMARY KEY,
        lat              REAL,
        lng              REAL,
        total_stores     INTEGER,
        restaurant_cnt   INTEGER,
        cafe_cnt         INTEGER,
        hospital_cnt     INTEGER,
        pharmacy_cnt     INTEGER,
        convenience_cnt  INTEGER,
        commerce_score   REAL,
        updated_at       TEXT
    );
    CREATE TABLE IF NOT EXISTS apt_external (
        apt_seq                TEXT PRIMARY KEY,
        nearest_station        TEXT,
        nearest_station_dist   REAL,
        nearest_line           TEXT,
        line_grade             INTEGER,
        walk_min               REAL,
        elem_school_cnt_1km    INTEGER,
        nearest_school_dist    REAL,
        park_dist              REAL,
        river_dist             REAL,
        green_score            REAL,
        redv_nearby            INTEGER,
        redv_status_best       TEXT,
        gtx_dist               REAL,
        gtx_line               TEXT,
        commerce_score         REAL,
        hospital_cnt           INTEGER,
        infra_score            REAL,
        updated_at             TEXT
    );
    """)
    con.commit()
    con.close()
    print(f"  ✅ DB 초기화: {DB_PATH}")


# ─────────────────────────────────────────────────────
# STEP 1. 지하철역
#   우선순위: CSV(raw/subway/) > API(t-data)
# ─────────────────────────────────────────────────────

SUBWAY_LINE_GRADE = {
    "2호선":1, "5호선":1, "9호선":1, "9호선(연장)":1,
    "신분당선":1, "신분당선(연장)":1, "신분당선(연장2)":1,
    "수도권 광역급행철도":2,
    "3호선":2, "7호선":2, "분당선":2, "수인선":2,
    "경의중앙선":2, "공항철도1호선":2,
    "1호선":3, "4호선":3, "6호선":3, "8호선":3,
    "우이신설선":3, "신림선":3, "김포골드라인":3,
}

def step1_subway():
    print("\n📡 [1/5] 지하철역 수집")

    # CSV 우선 탐색
    csv_files = list(RAW_SUBWAY.glob("*.csv"))
    if csv_files:
        csv_path = csv_files[0]
        print(f"  CSV 발견: {csv_path.name}")
        _subway_from_csv(csv_path)
        return

    # CSV 없으면 API
    api_key = API_KEYS["tdata"]
    if not api_key:
        print("  ⚠️  TDATA_API_KEY 미설정")
        print(f"  → raw/subway/ 에 '지하철역_GEOM__역사마스터_.csv' 파일을 넣어주세요")
        print(f"     다운로드: https://t-data.seoul.go.kr")
        return

    print("  API 호출 (t-data.seoul.go.kr)")
    _subway_from_api(api_key)


def _subway_from_csv(csv_path: Path):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    saved = skipped = 0

    with open(csv_path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                lng = float(row["환승역X좌표"])
                lat = float(row["환승역Y좌표"])
                if not lat or not lng:
                    skipped += 1; continue
                line  = row["호선명칭"].strip()
                grade = SUBWAY_LINE_GRADE.get(line, 3)
                cur.execute(
                    "INSERT OR REPLACE INTO subway_stations VALUES (?,?,?,?,?,?,?)",
                    (row["외구간_역_수"], row["역한글명칭"], line, grade,
                     lat, lng, datetime.now().isoformat())
                )
                saved += 1
            except Exception:
                skipped += 1
    con.commit()
    con.close()
    print(f"  ✅ {saved:,}개 저장 (스킵 {skipped})")


def _subway_from_api(api_key: str):
    BASE = "http://t-data.seoul.go.kr/apig/apiman-gateway/tapi/TaimsKsccDvSubwayStationGeom/1.0"
    all_rows, start = [], 1
    while True:
        try:
            res  = requests.get(BASE, params={"apikey": api_key, "startRow": start, "rowCnt": 100}, timeout=10)
            data = res.json()
            batch = data if isinstance(data, list) else data.get("result", [])
            if not batch: break
            all_rows.extend(batch)
            if len(batch) < 100: break
            start += 100
            time.sleep(0.2)
        except Exception as e:
            print(f"  ⚠️  API 오류: {e}"); break

    con = sqlite3.connect(DB_PATH)
    saved = 0
    for row in all_rows:
        try:
            lat   = float(row.get("convY", 0))
            lng   = float(row.get("convX", 0))
            if not lat or not lng: continue
            line  = row.get("lineNm", "").strip()
            grade = SUBWAY_LINE_GRADE.get(line, 3)
            con.execute(
                "INSERT OR REPLACE INTO subway_stations VALUES (?,?,?,?,?,?,?)",
                (str(row.get("outStnNum","")), row.get("stnKrNm",""),
                 line, grade, lat, lng, datetime.now().isoformat())
            )
            saved += 1
        except Exception:
            continue
    con.commit(); con.close()
    print(f"  ✅ {saved:,}개 저장")


# ─────────────────────────────────────────────────────
# STEP 2. 학교
#   우선순위: CSV(raw/school/) > API(NEIS)
# ─────────────────────────────────────────────────────

SCHOOL_KIND_MAP = {"02": "elementary", "03": "middle"}
SCHOOL_KIND_NM_MAP = {"초등학교": "elementary", "중학교": "middle"}
EDU_CODES = {"서울": "B10", "경기": "J10", "인천": "E10"}

def step2_school():
    print("\n📡 [2/5] 학교 정보 수집")

    csv_files = list(RAW_SCHOOL.glob("*.csv"))
    if csv_files:
        print(f"  CSV 발견: {len(csv_files)}개")
        for f in csv_files:
            _school_from_csv(f)
        return

    api_key = API_KEYS["neis"]
    if not api_key:
        print("  ⚠️  NEIS_API_KEY 미설정")
        print(f"  → config/secrets.json 에 NEIS_API_KEY 추가")
        print(f"     발급: https://open.neis.go.kr/portal/mypage/keyIssue.do")
        return

    print("  API 호출 (open.neis.go.kr) — 서울·경기·인천")
    for region, edu_code in EDU_CODES.items():
        print(f"  → {region}")
        _school_from_api(api_key, edu_code)
        time.sleep(0.3)


def _school_from_csv(csv_path: Path):
    """NEIS API 응답을 미리 저장해둔 CSV 파일 처리"""
    con = sqlite3.connect(DB_PATH)
    saved = skipped = 0
    enc = "utf-8-sig"
    try:
        with open(csv_path, encoding=enc) as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    lat = float(row.get("LTTUD") or row.get("위도") or 0)
                    lng = float(row.get("LGTUD") or row.get("경도") or 0)
                    if not lat or not lng: skipped += 1; continue
                    if row.get("ABSCH_YN") == "Y": skipped += 1; continue
                    kind = row.get("SCHUL_KND_SC_CODE","").strip()
                    stype = SCHOOL_KIND_MAP.get(kind, "other")
                    sid  = row.get("SCHUL_CODE","").strip()
                    con.execute(
                        "INSERT OR REPLACE INTO schools VALUES (?,?,?,?,?,?,?)",
                        (sid, row.get("SCHUL_NM",""), stype,
                         str(row.get("ADRCD_CD",""))[:5], lat, lng,
                         datetime.now().isoformat())
                    )
                    saved += 1
                except Exception:
                    skipped += 1
    except UnicodeDecodeError:
        with open(csv_path, encoding="cp949") as f:
            pass  # cp949 fallback
    con.commit(); con.close()
    print(f"  ✅ {csv_path.name}: {saved:,}개 저장")


def _vworld_geocode(address: str) -> tuple:
    """V-World 도로명주소 → (lat, lng). 실패시 (0.0, 0.0)."""
    api_key = API_KEYS.get("vworld", "")
    if not api_key or not address:
        return 0.0, 0.0
    try:
        res = requests.get(
            "https://api.vworld.kr/req/address",
            params={
                "service": "address", "request": "getcoord",
                "version": "2.0", "key": api_key,
                "address": address, "type": "ROAD",
                "simple": "false", "format": "json",
            },
            timeout=10,
        )
        r = res.json().get("response", {})
        if r.get("status") == "OK":
            pt = r["result"]["point"]
            return float(pt["y"]), float(pt["x"])
    except Exception:
        pass
    return 0.0, 0.0


def _school_from_api(api_key: str, edu_code: str):
    BASE  = "https://open.neis.go.kr/hub/schoolInfo"
    page  = 1
    rows  = []
    while True:
        try:
            res  = requests.get(BASE, params={
                "KEY": api_key, "Type": "json",
                "pIndex": page, "pSize": 1000,
                "ATPT_OFCDC_SC_CODE": edu_code,
            }, timeout=15)
            data  = res.json()
            if "RESULT" in data:
                print(f"    ⚠️  API 오류: {data['RESULT'].get('MESSAGE','')}")
                break
            info  = data.get("schoolInfo", [])
            if len(info) < 2: break
            batch = info[1].get("row", [])
            if not batch: break
            rows.extend(batch)
            if len(batch) < 1000: break
            page += 1; time.sleep(0.2)
        except Exception as e:
            print(f"    ⚠️  오류: {e}"); break

    con = sqlite3.connect(DB_PATH)
    saved = geocoded = 0
    for item in rows:
        try:
            schul_knd = item.get("SCHUL_KND_SC_NM", "").strip()
            stype = SCHOOL_KIND_NM_MAP.get(schul_knd)
            if not stype:
                continue  # 초등/중학교 외 제외

            lat = float(item.get("LTTUD", 0) or 0)
            lng = float(item.get("LGTUD", 0) or 0)

            if not lat or not lng:
                address = item.get("ORG_RDNMA", "").strip()
                lat, lng = _vworld_geocode(address)
                if lat:
                    geocoded += 1
                time.sleep(0.1)

            if not lat or not lng:
                continue

            sid = item.get("SD_SCHUL_CODE") or item.get("SCHUL_CODE", "")
            con.execute(
                "INSERT OR REPLACE INTO schools VALUES (?,?,?,?,?,?,?)",
                (sid, item.get("SCHUL_NM", ""), stype, "",
                 lat, lng, datetime.now().isoformat())
            )
            saved += 1
        except Exception:
            continue
    con.commit(); con.close()
    print(f"    {saved:,}개 저장 (지오코딩: {geocoded:,}개)")


# ─────────────────────────────────────────────────────
# STEP 3. 공원·하천
#   raw/park/전국도시공원정보표준데이터.csv (cp949)
# ─────────────────────────────────────────────────────

PARK_TYPE_WEIGHT = {
    "근린공원":1.0, "수변공원":1.2, "체육공원":0.8,
    "문화공원":0.9, "역사공원":0.7, "소공원":0.5,
    "어린이공원":0.6, "기타":0.4,
}

RIVERS = [
    ("R001","한강",    37.5326,126.9903), ("R002","청계천",  37.5705,126.9942),
    ("R003","안양천",  37.5065,126.8880), ("R004","중랑천",  37.5721,127.0721),
    ("R005","홍제천",  37.5833,126.9426), ("R006","불광천",  37.6101,126.9175),
    ("R007","탄천",    37.4767,127.1208), ("R008","도림천",  37.4960,126.9025),
    ("R009","우이천",  37.6362,127.0290), ("R010","경안천",  37.4001,127.2561),
    ("R011","황구지천",37.2980,127.0370), ("R012","수원천",  37.2856,127.0166),
    ("R013","굴포천",  37.5132,126.7490), ("R014","왕숙천",  37.6490,127.2190),
    ("R015","신천",    37.3559,127.1130),
]

def step3_park():
    print("\n📡 [3/5] 공원·하천 수집")

    csv_files = list(RAW_PARK.glob("*.csv"))
    if not csv_files:
        print(f"  ❌ raw/park/ 에 CSV 파일 없음")
        print(f"     다운로드: https://www.data.go.kr/data/15012890/standard.do")
        print(f"     파일명: 전국도시공원정보표준데이터.csv (cp949)")
        _save_river_only()
        return

    csv_path = csv_files[0]
    print(f"  CSV: {csv_path.name}")

    con = sqlite3.connect(DB_PATH)
    saved = skipped = 0

    with open(csv_path, encoding="cp949") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                lat = float(row.get("위도", 0) or 0)
                lng = float(row.get("경도", 0) or 0)
                if not (32 < lat < 39 and 124 < lng < 132):
                    skipped += 1; continue
                park_id = row.get("관리번호","").strip()
                if not park_id: skipped += 1; continue
                con.execute(
                    "INSERT OR REPLACE INTO parks VALUES (?,?,?,?,?,?,?)",
                    (park_id, row.get("공원명",""), row.get("공원구분","기타"),
                     float(row.get("공원면적", 0) or 0),
                     lat, lng, datetime.now().isoformat())
                )
                saved += 1
            except Exception:
                skipped += 1

    for rid, rname, rlat, rlng in RIVERS:
        con.execute(
            "INSERT OR REPLACE INTO rivers VALUES (?,?,?,?,?)",
            (rid, rname, rlat, rlng, datetime.now().isoformat())
        )
    con.commit(); con.close()
    print(f"  ✅ 공원 {saved:,}개 저장 (스킵 {skipped:,})")
    print(f"  ✅ 하천 {len(RIVERS)}개 저장")


def _save_river_only():
    con = sqlite3.connect(DB_PATH)
    for rid, rname, rlat, rlng in RIVERS:
        con.execute(
            "INSERT OR REPLACE INTO rivers VALUES (?,?,?,?,?)",
            (rid, rname, rlat, rlng, datetime.now().isoformat())
        )
    con.commit(); con.close()
    print(f"  ✅ 하천만 저장 ({len(RIVERS)}개)")


# ─────────────────────────────────────────────────────
# STEP 4. 정비구역 (V-World WFS)
# ─────────────────────────────────────────────────────

# WFS 2.0.0 EPSG:4326 BBOX 순서: minLat,minLon,maxLat,maxLon
SUDOGWON_BBOX = "37.10,126.60,37.90,127.70"

STATUS_RANK = {
    "관리처분인가":4, "사업시행인가":3,
    "조합설립인가":2, "구역지정":1, "완료":0,
}

# 수집 대상 레이어: layer → zone_type 매핑
REDV_LAYERS = {
    "lt_c_ud601": "주거환경개선지구",
    "lt_c_ub901": "시장정비구역",
    "lt_c_uq101": "도시재정비촉진지구",
    "lt_c_uq102": "재정비촉진구역",
}

def step4_redevelopment():
    print("\n📡 [4/5] 정비구역 수집 (V-World WFS · 수도권)")

    api_key = API_KEYS["vworld"]
    if not api_key:
        print("  ⚠️  VWORLD_API_KEY 미설정")
        print(f"  → config/secrets.json 에 VWORLD_API_KEY 추가")
        print(f"     발급: https://www.vworld.kr (WMS/WFS API 체크)")
        return

    BASE = "https://api.vworld.kr/req/wfs"
    features = []

    for layer, default_type in REDV_LAYERS.items():
        start = 0
        while True:
            try:
                res = requests.get(BASE, params={
                    "SERVICE": "WFS", "REQUEST": "GetFeature", "VERSION": "2.0.0",
                    "TYPENAME": layer, "SRSNAME": "EPSG:4326",
                    "OUTPUT": "application/json",
                    "BBOX": SUDOGWON_BBOX + ",EPSG:4326",
                    "COUNT": 1000, "STARTINDEX": start,
                    "KEY": api_key,
                }, timeout=30)
                data  = res.json()
                batch = data.get("features", [])
                if not batch:
                    break
                for f in batch:
                    f["_layer_type"] = default_type
                features.extend(batch)
                print(f"  → {layer}: {len(batch)}건")
                if len(batch) < 1000:
                    break
                start += 1000
                time.sleep(0.3)
            except Exception as e:
                print(f"  ⚠️  WFS 오류 ({layer}): {e}")
                break

    con = sqlite3.connect(DB_PATH)
    saved = skipped = 0

    for feat in features:
        try:
            props    = feat.get("properties", {})
            geom     = feat.get("geometry", {})
            lat, lng = _centroid(geom)
            if not lat or not lng:
                skipped += 1
                continue
            zone_id  = props.get("mnum", feat.get("id", f"RD_{saved}"))
            gu_code  = str(props.get("std_sggcd", props.get("sgg_cd", ""))  )[:5]
            ztype    = props.get("uname") or feat.get("_layer_type", "정비구역")
            name     = (props.get("pnm") or props.get("pname") or props.get("jname")
                        or props.get("remark") or props.get("alias") or ztype)
            con.execute(
                "INSERT OR REPLACE INTO redevelopment_zones VALUES (?,?,?,?,?,?,?,?,?,?)",
                (zone_id, name, ztype, "구역지정", gu_code,
                 lat, lng, 0.0, 0, datetime.now().isoformat())
            )
            saved += 1
        except Exception:
            skipped += 1

    con.commit()
    con.close()
    print(f"  ✅ {saved:,}개 저장 (스킵 {skipped:,})")


def _centroid(geom: dict):
    try:
        gtype  = geom.get("type","")
        coords = geom.get("coordinates",[])
        if gtype == "Point":
            return coords[1], coords[0]
        elif gtype == "Polygon":
            ring = coords[0]
            return (sum(p[1] for p in ring)/len(ring),
                    sum(p[0] for p in ring)/len(ring))
        elif gtype == "MultiPolygon":
            pts = [p for poly in coords for ring in poly for p in ring]
            return (sum(p[1] for p in pts)/len(pts),
                    sum(p[0] for p in pts)/len(pts))
    except Exception:
        pass
    return None, None


# ─────────────────────────────────────────────────────
# STEP 5. 상권
#   raw/shop/소상공인시장진흥공단_상가(상권)정보.csv (utf-8)
#   전략: 스트리밍 → 수도권 필터 → 0.005도 격자 집계
# ─────────────────────────────────────────────────────

COMMERCE_KEYWORDS = {
    "restaurant":   ["한식","중식","일식","양식","분식","치킨","피자","고기","찜","탕"],
    "cafe":         ["커피","카페","베이커리","제과","디저트","아이스크림"],
    "hospital":     ["병원","의원","한의원","치과","내과","외과","소아과","피부과"],
    "pharmacy":     ["약국"],
    "convenience":  ["편의점"],
}
GRID_STEP = 0.005  # ≈ 500m

def _grid_id(lat: float, lng: float) -> str:
    return f"{round(lat/GRID_STEP)*GRID_STEP:.4f}_{round(lng/GRID_STEP)*GRID_STEP:.4f}"

def step5_commerce():
    print("\n📡 [5/5] 상권 수집")

    csv_files = list(RAW_SHOP.glob("*.csv"))
    if not csv_files:
        print(f"  ❌ raw/shop/ 에 CSV 파일 없음")
        print(f"     다운로드: https://www.data.go.kr/data/15083033/fileData.do")
        print(f"     최신 분기 ZIP 다운로드 → 압축 해제 → raw/shop/ 에 저장")
        print(f"     파일명 예: 소상공인시장진흥공단_상가(상권)정보_20251231.csv (utf-8)")
        return

    # **모든 CSV 를 읽는다.**
    #
    # 전에는 csv_files[0] 하나만 읽었다. 알파벳순 첫 파일이 "강원"이라
    # 수도권 격자가 가평·양평 언저리 1,281개뿐이었고, 서울·인천은 0개였다.
    # 그 상태로 "주변 상권" 을 그리면 서울 한복판이 상권 없는 동네로 나온다.
    csv_files = sorted(csv_files)
    total_mb = sum(f.stat().st_size for f in csv_files) / (1024**2)
    print(f"  CSV {len(csv_files)}개 ({total_mb:.0f}MB)")
    print(f"  수도권 필터 후 0.005도 격자 집계 중...")

    grids     = defaultdict(lambda: {
        "total":0,"restaurant":0,"cafe":0,
        "hospital":0,"pharmacy":0,"convenience":0,
        "lat":0.0,"lng":0.0
    })
    processed = filtered = 0

    for csv_path in csv_files:
        with open(csv_path, encoding="utf-8") as f:
            reader  = csv.DictReader(f)
            headers = reader.fieldnames or []
            lat_col = next((c for c in headers if "위도" in c), "위도")
            lng_col = next((c for c in headers if "경도" in c), "경도")
            cat_col = next((c for c in headers if "소분류명" in c), "상권업종소분류명")

            for row in reader:
                processed += 1
                if processed % 500_000 == 0:
                    print(f"  → {processed:,}건 처리 중 (격자 {len(grids):,}개)...",
                          flush=True)
                try:
                    lat = float(row.get(lat_col, 0) or 0)
                    lng = float(row.get(lng_col, 0) or 0)
                    if not (36.8 < lat < 38.1 and 126.5 < lng < 127.8):
                        continue
                    gid = _grid_id(lat, lng)
                    g   = grids[gid]
                    g["total"] += 1
                    g["lat"]    = round(lat/GRID_STEP) * GRID_STEP
                    g["lng"]    = round(lng/GRID_STEP) * GRID_STEP
                    cat = row.get(cat_col, "")
                    for key, kws in COMMERCE_KEYWORDS.items():
                        if any(k in cat for k in kws):
                            g[key] += 1; break
                    filtered += 1
                except Exception:
                    continue

    print(f"  처리 완료: {processed:,}건 → 수도권 {filtered:,}건 → {len(grids):,}개 격자")

    con = sqlite3.connect(DB_PATH)
    for gid, g in tqdm(grids.items(), desc="  DB 적재"):
        score = min(100,
            g["restaurant"]*0.5 + g["cafe"]*0.8 +
            g["hospital"]*2.0   + g["pharmacy"]*1.5 +
            g["convenience"]*1.0
        )
        con.execute(
            "INSERT OR REPLACE INTO commerce_zones VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (gid, g["lat"], g["lng"],
             g["total"], g["restaurant"], g["cafe"],
             g["hospital"], g["pharmacy"], g["convenience"],
             round(score,2), datetime.now().isoformat())
        )
    con.commit(); con.close()
    print(f"  ✅ {len(grids):,}개 격자 저장")


# ─────────────────────────────────────────────────────
# 단지별 외부 점수 산출
#   apt_master 테이블 (실거래 파이프라인에서 생성) 기준
# ─────────────────────────────────────────────────────

def compute_scores():
    print("\n⚙️  단지별 외부 점수 산출")

    con = sqlite3.connect(DB_PATH)

    # apt_master 존재 여부 확인
    has_master = con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='apt_master'"
    ).fetchone()

    if not has_master:
        print("  ⚠️  apt_master 테이블 없음 → 실거래 수집 파이프라인을 먼저 실행하세요")
        print("     (step1a_collect_all_history.ipynb 또는 run_collect_history.py)")
        con.close()
        return

    apts      = con.execute(
        "SELECT apt_seq, apt_name, lat, lng FROM apt_master WHERE lat IS NOT NULL AND lng IS NOT NULL"
    ).fetchall()
    stations  = con.execute("SELECT station_name, line, line_grade, lat, lng FROM subway_stations").fetchall()
    schools   = con.execute("SELECT lat, lng FROM schools WHERE school_type='elementary'").fetchall()
    parks     = con.execute("SELECT lat, lng, area_m2 FROM parks").fetchall()
    rivers    = con.execute("SELECT lat, lng FROM rivers").fetchall()
    redvs     = con.execute("SELECT lat, lng, status FROM redevelopment_zones").fetchall()
    commerce  = con.execute("SELECT lat, lng, commerce_score, hospital_cnt FROM commerce_zones").fetchall()

    print(f"  단지: {len(apts):,}개 | 역: {len(stations):,} | 학교: {len(schools):,} | "
          f"공원: {len(parks):,} | 정비: {len(redvs):,} | 상권격자: {len(commerce):,}")

    saved = 0
    for apt_seq, apt_name, alat, alng in tqdm(apts, desc="  점수 산출"):
        try:
            # 지하철
            st = sorted([(haversine(alat,alng,s[3],s[4]),s) for s in stations], key=lambda x:x[0])
            st_dist  = st[0][0] if st else 99999
            st_name  = st[0][1][0] if st else ""
            st_line  = st[0][1][1] if st else ""
            st_grade = st[0][1][2] if st else 3
            walk_min = round(st_dist / 67, 1)

            # 학교
            elem_1km   = sum(1 for s in schools if haversine(alat,alng,s[0],s[1]) <= 1000)
            sc_dists   = sorted([haversine(alat,alng,s[0],s[1]) for s in schools])
            nearest_sc = sc_dists[0] if sc_dists else 99999

            # 공원·하천
            pk_dist  = min((haversine(alat,alng,p[0],p[1]) for p in parks),  default=99999)
            rv_dist  = min((haversine(alat,alng,r[0],r[1]) for r in rivers), default=99999)
            green_sc = round(max(0,50-pk_dist/100) + max(0,50-rv_dist/200), 1)

            # 정비구역
            redv_500  = [(haversine(alat,alng,r[0],r[1]),r[2]) for r in redvs
                         if haversine(alat,alng,r[0],r[1]) <= 500]
            redv_cnt  = len(redv_500)
            redv_best = max(redv_500, key=lambda x: STATUS_RANK.get(x[1],0))[1] if redv_500 else ""

            # 상권 (격자 스냅)
            cm = sorted([(haversine(alat,alng,c[0],c[1]),c) for c in commerce], key=lambda x:x[0])
            cm_score = cm[0][1][2] if cm else 0
            hosp_cnt = cm[0][1][3] if cm else 0

            # 종합 인프라 점수
            grade_w   = {1:1.0, 2:0.8, 3:0.6}.get(st_grade, 0.6)
            infra     = round(min(100, max(0,
                max(0, 35 - st_dist/100) * grade_w +   # 역세권 35점
                min(25, elem_1km * 8) +                # 학군   25점
                min(15, green_sc * 0.15) +             # 녹지   15점
                min(15, cm_score * 0.15) +             # 상권   15점
                max(0, 10 - len(redv_500)*(-2))        # 호재   10점 (정비구역 있으면 가산)
            )), 1)

            con.execute("""
                INSERT OR REPLACE INTO apt_external VALUES
                (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                apt_seq, st_name, round(st_dist), st_line, st_grade, walk_min,
                elem_1km, round(nearest_sc), round(pk_dist), round(rv_dist),
                green_sc, redv_cnt, redv_best,
                0.0, "",   # GTX: 지하철역 GEOM에 포함됨
                round(cm_score,1), hosp_cnt, infra,
                datetime.now().isoformat()
            ))
            saved += 1

        except Exception:
            continue

    con.commit(); con.close()
    print(f"  ✅ {saved:,}개 단지 점수 저장")


# ─────────────────────────────────────────────────────
# 결과 요약
# ─────────────────────────────────────────────────────

def print_summary():
    con  = sqlite3.connect(DB_PATH)
    print("\n" + "="*55)
    print("📊 DB 현황 요약")
    print("="*55)
    tables = [
        ("subway_stations",    "지하철역"),
        ("schools",            "학교"),
        ("parks",              "공원"),
        ("rivers",             "하천"),
        ("redevelopment_zones","정비구역"),
        ("commerce_zones",     "상권 격자"),
        ("apt_external",       "단지 외부점수"),
    ]
    for tbl, label in tables:
        try:
            cnt = con.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        except Exception:
            cnt = 0
        print(f"  {label:12s}: {cnt:>8,}건")

    # 인프라 점수 TOP5
    try:
        rows = con.execute("""
            SELECT m.apt_name, e.nearest_station, e.walk_min,
                   e.elem_school_cnt_1km, e.infra_score
            FROM apt_external e
            JOIN apt_master m ON e.apt_seq = m.apt_seq
            ORDER BY e.infra_score DESC LIMIT 5
        """).fetchall()
        if rows:
            print("\n  [인프라 점수 TOP5]")
            for r in rows:
                print(f"  {r[0]:20s} | {r[1]}역 도보{r[2]}분 | 초교{r[3]}개 | {r[4]}점")
    except Exception:
        pass

    print("="*55)
    con.close()


# ─────────────────────────────────────────────────────
# 진입점
# ─────────────────────────────────────────────────────

def run_all():
    print("🚀 외부 데이터 수집 파이프라인\n")
    print(f"  프로젝트 루트: {ROOT}")
    print(f"  DB 경로:       {DB_PATH}")
    print(f"  실행일:        {date.today()}")

    check_api_expiry()

    print("  [API 키 상태]")
    for k, v in API_KEYS.items():
        print(f"    {k:8s}: {'✅ 설정됨' if v else '⚠️  미설정'}")

    init_db()
    step1_subway()
    step2_school()
    step3_park()
    step4_redevelopment()
    step5_commerce()
    compute_scores()
    print_summary()
    print("\n✅ 완료!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="외부 데이터 수집 파이프라인")
    parser.add_argument("--step",  type=int, choices=[1,2,3,4,5],
                        help="특정 스텝만 실행 (1=지하철 2=학교 3=공원 4=정비구역 5=상권)")
    parser.add_argument("--score", action="store_true",
                        help="단지별 점수 산출만 실행")
    args = parser.parse_args()

    if args.score:
        init_db()
        compute_scores()
        print_summary()
    elif args.step:
        init_db()
        [None, step1_subway, step2_school, step3_park,
         step4_redevelopment, step5_commerce][args.step]()
    else:
        run_all()
