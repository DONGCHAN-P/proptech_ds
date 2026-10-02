"""T6b — 공동주택 단지정보(K-apt) 수집.

세대수가 없으면 T9 의 "300세대 미만 제외" 필터가 동작하지 않는다. RTMS
실거래 응답에는 세대수가 없으므로 K-apt 쪽에서 따로 받아 붙인다.

2단계로 받는다.
  [1] 단지 목록   AptListService4/getSigunguAptList4   시군구당 1회
  [2] 기본 정보   AptBasisInfoServiceV5/getAphusBassInfoV5   단지당 1회
      -> kaptdaCnt(세대수) kaptUsedate(사용승인일) doroJuso(도로명주소)
         kaptDongCnt(동수) kaptTopFloor(최고층) kaptBcompany(시공사) ...

엔드포인트 주의: 구버전(AptListService2/3, AptBasisInfoServiceV3)은 전부
폐기돼 NO_OPENAPI_SERVICE_ERROR 를 돌려준다. 2026-10 기준 v4/V5 가 유효하다.

산출물:
  staged/apt_info_snapshots/kapt_list_YYYYMMDD.parquet    목록
  staged/apt_info_snapshots/kapt_basis_YYYYMMDD.parquet   기본정보

실행:
  .venv\\Scripts\\python.exe run_collect_kapt.py --list-only   # 목록만 (빠름)
  .venv\\Scripts\\python.exe run_collect_kapt.py              # 목록 + 기본정보
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DIRS, SIGUNGU_CODES, load_secrets  # noqa: E402

BASE = "http://apis.data.go.kr/1613000"
LIST_URL = f"{BASE}/AptListService4/getSigunguAptList4"
BASIS_URL = f"{BASE}/AptBasisInfoServiceV5/getAphusBassInfoV5"

OUT_DIR = DIRS["staged_apt_info"]

BASIS_COLS = [
    "kaptCode", "kaptName", "bjdCode", "kaptAddr", "doroJuso", "zipcode",
    "kaptdaCnt", "hoCnt", "kaptDongCnt", "kaptUsedate",
    "kaptTopFloor", "kaptBaseFloor", "kaptTarea", "kaptMarea", "privArea",
    "kaptMparea60", "kaptMparea85", "kaptMparea135", "kaptMparea136",
    "codeSaleNm", "codeHeatNm", "codeHallNm", "codeAptNm",
    "kaptBcompany", "kaptAcompany", "kaptdEcntp",
]


def get_json(url: str, params: dict, tries: int = 3) -> dict | None:
    """serviceKey 는 URL 에 직접 붙인다.

    공공데이터포털 키는 이미 퍼센트 인코딩된 문자열이다(`...%3D%3D`).
    requests 의 params= 에 넣으면 `%` 를 `%25` 로 또 인코딩해 키가 망가지고,
    서버는 SERVICE_KEY_IS_NOT_REGISTERED_ERROR(403) 를 돌려준다. 키가 틀린
    것처럼 보여서 원인을 찾기 어려우니 주의.
    """
    key = params.pop("serviceKey")
    rest = "&".join(f"{k}={v}" for k, v in {**params, "_type": "json"}.items())
    full = f"{url}?serviceKey={key}&{rest}"
    for i in range(1, tries + 1):
        try:
            r = requests.get(full, timeout=30)
            r.raise_for_status()
            return r.json()
        except Exception:
            if i == tries:
                return None
            time.sleep(2 ** i)
    return None


def collect_list(key: str, sleep: float) -> pd.DataFrame:
    """시군구별 단지 목록. 페이지네이션 포함."""
    rows: list[dict] = []
    total = len(SIGUNGU_CODES)
    t0 = time.time()
    for i, (code, name) in enumerate(SIGUNGU_CODES.items(), 1):
        page, got = 1, 0
        while True:
            d = get_json(LIST_URL, {"serviceKey": key, "sigunguCode": code,
                                    "numOfRows": 1000, "pageNo": page})
            if not d:
                print(f"  실패 {code} {name} p{page}")
                break
            body = (d.get("response") or {}).get("body") or {}
            items = body.get("items") or []
            if isinstance(items, dict):
                items = items.get("item") or []
            if isinstance(items, dict):
                items = [items]
            for it in items:
                rows.append({**it, "sigungu_code": code, "sigungu_name": name})
            got += len(items)
            if got >= int(body.get("totalCount") or 0) or not items:
                break
            page += 1
            time.sleep(sleep)
        time.sleep(sleep)
        if i % 20 == 0 or i == total:
            el = time.time() - t0
            print(f"  [{i}/{total}] 누적 {len(rows):,}개 단지 "
                  f"| 남은 {el / i * (total - i):.0f}s")
    return pd.DataFrame(rows)


QUOTA_ERRORS = ("LIMITED_NUMBER_OF_SERVICE_REQUESTS_EXCEEDS",
                "SERVICE_KEY_IS_NOT_REGISTERED", "HTTP_ERROR")


def quota_hit(d: dict | None) -> bool:
    """일일 호출 한도를 넘었는지.

    포털은 한도 초과를 깔끔한 코드로 주지 않는다. 한도를 넘기면 그 서비스가
    통째로 HTTP_ERROR(04) 를 뱉기 시작한다 — 직전까지 멀쩡히 응답하던
    kaptCode 도 똑같이 실패한다. 키가 틀린 것처럼 보이지만 다른 서비스
    (RTMS) 는 정상이므로 서비스별 한도로 보는 게 맞다.
    """
    if not d:
        return False
    hdr = (d.get("OpenAPI_ServiceResponse") or {}).get("cmmMsgHeader") or {}
    return any(e in str(hdr.get("errMsg", "")) for e in QUOTA_ERRORS)


def collect_basis(key: str, codes: list[str], sleep: float,
                  checkpoint: Path | None = None, prev: pd.DataFrame | None = None
                  ) -> tuple[pd.DataFrame, bool]:
    """단지별 기본정보. 세대수는 여기에만 있다.

    반환: (수집분, 한도초과로 중단했는지)

    한도에 걸리면 바로 멈춘다. 계속 두드려봐야 전부 실패하고 다음 날 한도만
    축낸다. 200건마다 체크포인트를 저장해 중단돼도 이어받을 수 있게 한다.
    """
    rows: list[dict] = []
    fails = consecutive = 0
    stopped = False
    t0 = time.time()

    def save() -> None:
        if checkpoint is None or not rows:
            return
        cur = pd.DataFrame(rows)
        out = pd.concat([prev, cur], ignore_index=True) if prev is not None and len(prev) else cur
        out.drop_duplicates("kaptCode").to_parquet(checkpoint, index=False, compression="zstd")

    for i, kc in enumerate(codes, 1):
        d = get_json(BASIS_URL, {"serviceKey": key, "kaptCode": kc})
        if quota_hit(d):
            consecutive += 1
            if consecutive >= 10:
                print(f"\n  ⚠️ 일일 호출 한도 초과로 보입니다 — {i:,}번째에서 중단")
                print(f"     {consecutive}회 연속 HTTP_ERROR. 내일 다시 실행하면 이어받습니다.")
                stopped = True
                break
            fails += 1
            time.sleep(sleep)
            continue
        consecutive = 0

        item = None
        if d:
            item = ((d.get("response") or {}).get("body") or {}).get("item")
        if isinstance(item, list):
            item = item[0] if item else None
        if item:
            rows.append({c: item.get(c) for c in BASIS_COLS})
        else:
            fails += 1
        time.sleep(sleep)
        if i % 200 == 0 or i == len(codes):
            save()
            el = time.time() - t0
            print(f"  [{i:,}/{len(codes):,}] 수집 {len(rows):,} 실패 {fails} "
                  f"| 남은 {el / i * (len(codes) - i) / 60:.1f}분")
    save()
    return pd.DataFrame(rows), stopped


def main() -> int:
    ap = argparse.ArgumentParser(description="K-apt 단지정보 수집")
    ap.add_argument("--list-only", action="store_true", help="목록만 수집")
    ap.add_argument("--sleep", type=float, default=0.12, help="호출 간격(초)")
    ap.add_argument("--limit", type=int, help="기본정보 수집 상한(시험용)")
    args = ap.parse_args()

    key = load_secrets()["kapt_service_key"]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d")
    list_path = OUT_DIR / f"kapt_list_{stamp}.parquet"

    print(f"\n{'=' * 60}\n  K-apt 단지정보 수집  {datetime.now():%Y-%m-%d %H:%M}\n{'=' * 60}")

    if list_path.exists():
        df_list = pd.read_parquet(list_path)
        print(f"\n[1] 목록: 기존 파일 재사용 ({len(df_list):,}개 단지)")
    else:
        print(f"\n[1] 단지 목록 수집 ({len(SIGUNGU_CODES)}개 시군구)...")
        df_list = collect_list(key, args.sleep)
        if df_list.empty:
            print("목록 수집 실패")
            return 1
        df_list = df_list.drop_duplicates("kaptCode")
        df_list.to_parquet(list_path, index=False, compression="zstd")
        print(f"  저장: {list_path} ({len(df_list):,}개 단지)")

    if args.list_only:
        print("\n--list-only — 기본정보 생략")
        return 0

    basis_path = OUT_DIR / f"kapt_basis_{stamp}.parquet"
    done: set[str] = set()
    if basis_path.exists():
        prev = pd.read_parquet(basis_path)
        done = set(prev["kaptCode"])
        print(f"\n[2] 기본정보: 기존 {len(done):,}건 이어받기")
    else:
        prev = pd.DataFrame()

    todo = [c for c in df_list["kaptCode"] if c not in done]
    if args.limit:
        todo = todo[:args.limit]
    if not todo:
        print("\n[2] 기본정보: 수집 완료 상태")
        return 0

    print(f"\n[2] 기본정보 수집 ({len(todo):,}건, 예상 {len(todo) * args.sleep / 60:.0f}분)...")
    df_new, stopped = collect_basis(key, todo, args.sleep,
                                    checkpoint=basis_path, prev=prev)
    df = pd.concat([prev, df_new], ignore_index=True) if len(prev) else df_new
    df = df.drop_duplicates("kaptCode")
    if len(df):
        df.to_parquet(basis_path, index=False, compression="zstd")

    cnt = pd.to_numeric(df["kaptdaCnt"], errors="coerce") if len(df) else pd.Series(dtype=float)
    print(f"\n{'=' * 60}")
    print(f"  저장: {basis_path} ({len(df):,}건 / 전체 {len(df_list):,})")
    if len(cnt):
        print(f"  세대수 보유: {int((cnt > 0).sum()):,}건 "
              f"(중앙값 {cnt[cnt > 0].median():.0f}세대)")
    if stopped:
        print(f"  남은 {len(df_list) - len(df):,}건 — 한도가 풀리면 같은 명령으로 이어받습니다.")
    print(f"{'=' * 60}\n")
    return 2 if stopped else 0


if __name__ == "__main__":
    sys.exit(main())
