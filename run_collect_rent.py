"""
run_collect_rent.py — 전월세 RTMS 수집 (수도권 전 시군구)

API: RTMSDataSvcAptRent (아파트 전월세 실거래가)
산출물: raw/rtms_rent/{year}/{month}/{code}_{ym}.xml

실행:
  python run_collect_rent.py                    # 최근 2개월
  python run_collect_rent.py --months 6         # 최근 6개월
  python run_collect_rent.py --from 202001      # 특정 월부터 (히스토리 수집)
  python run_collect_rent.py --ym 202608        # 단일 월
"""
import sys
import os
import argparse
import json
import time
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import BASE, DIRS, SIGUNGU_CODES, load_secrets

RENT_API_BASE = (
    "https://apis.data.go.kr/1613000/RTMSDataSvcAptRent/getRTMSDataSvcAptRent"
)


def target_months(n: int) -> list[str]:
    today = datetime.now()
    seen, result = set(), []
    for i in range(n + 2):
        d = (today.replace(day=1) - timedelta(days=i * 28)).replace(day=1)
        ym = d.strftime("%Y%m")
        if ym not in seen:
            seen.add(ym)
            result.append(ym)
        if len(result) == n:
            break
    return sorted(result)


def months_from(start_ym: str) -> list[str]:
    start = datetime.strptime(start_ym, "%Y%m")
    today = datetime.now().replace(day=1)
    result = []
    cur = start
    while cur <= today:
        result.append(cur.strftime("%Y%m"))
        # 다음 달
        if cur.month == 12:
            cur = cur.replace(year=cur.year + 1, month=1)
        else:
            cur = cur.replace(month=cur.month + 1)
    return result


def fetch_rent_xml(service_key: str, sigungu_code: str, ym: str,
                   timeout: int = 30) -> str:
    url = (
        f"{RENT_API_BASE}?serviceKey={service_key}"
        f"&LAWD_CD={sigungu_code}&DEAL_YMD={ym}&numOfRows=1000&pageNo=1"
    )
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def parse_row_count(xml_text: str) -> int:
    try:
        root = ET.fromstring(xml_text)
        tc = root.find(".//totalCount")
        return int(tc.text) if tc is not None and tc.text else 0
    except Exception:
        return -1


def collect(ym_list: list[str], service_key: str,
            skip_existing: bool = True, sleep: float = 0.35) -> dict:
    total   = len(ym_list) * len(SIGUNGU_CODES)
    done    = errors = skipped = 0
    t0      = time.time()

    for ym in ym_list:
        yr, mo = ym[:4], ym[4:]
        out_dir = DIRS["raw_rent"] / yr / mo
        out_dir.mkdir(parents=True, exist_ok=True)

        for code, name in SIGUNGU_CODES.items():
            xml_path  = out_dir / f"{code}_{ym}.xml"
            meta_path = out_dir / f"{code}_{ym}.meta.json"

            if skip_existing and xml_path.exists():
                skipped += 1
                done    += 1
                continue

            last_err = None
            for attempt in range(1, 4):
                try:
                    xml_text = fetch_rent_xml(service_key, code, ym)
                    rows     = parse_row_count(xml_text)
                    xml_path.write_text(xml_text, encoding="utf-8")
                    meta_path.write_text(
                        json.dumps({
                            "sigungu_code": code, "sigungu_name": name,
                            "ym": ym, "rows": rows,
                            "fetched_at": datetime.now().isoformat(),
                            "type": "rent",
                        }, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )
                    time.sleep(sleep)
                    last_err = None
                    break
                except Exception as e:
                    last_err = e
                    if attempt < 3:
                        time.sleep(2 ** attempt)

            if last_err:
                errors += 1
                print(f"  오류: {ym} {code} {name} → {last_err}")

            done += 1
            if done % 200 == 0:
                elapsed = time.time() - t0
                eta = elapsed / done * (total - done)
                pct = done / total * 100
                print(f"  [{done:,}/{total:,}] {pct:.0f}%  오류: {errors}  남은: {eta:.0f}s")

    elapsed = time.time() - t0
    print(f"\n  수집 완료: {done:,}건 처리  |  오류: {errors}  |  스킵: {skipped}  |  {elapsed:.0f}s")
    return {"done": done, "errors": errors, "skipped": skipped}


def main():
    parser = argparse.ArgumentParser(description="전월세 RTMS 수집")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--months",   type=int,  default=2,    help="최근 N개월 (기본 2)")
    group.add_argument("--from",     dest="from_ym", metavar="YYYYMM", help="이 달부터 현재까지 전부")
    group.add_argument("--ym",       metavar="YYYYMM",                  help="단일 월만")
    parser.add_argument("--no-skip", action="store_true", help="기존 파일도 재수집")
    args = parser.parse_args()

    secrets     = load_secrets()
    service_key = secrets["data_go_kr_service_key"]

    if args.ym:
        ym_list = [args.ym]
    elif args.from_ym:
        ym_list = months_from(args.from_ym)
    else:
        ym_list = target_months(args.months)

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*60}")
    print(f"  전월세 RTMS 수집  {ts}")
    print(f"  대상: {ym_list}  ({len(ym_list)}개월 × {len(SIGUNGU_CODES)}개 시군구)")
    print(f"{'='*60}\n")

    DIRS["raw_rent"].mkdir(parents=True, exist_ok=True)
    collect(ym_list, service_key, skip_existing=not args.no_skip)

    print(f"\n저장 위치: {DIRS['raw_rent']}")


if __name__ == "__main__":
    main()
