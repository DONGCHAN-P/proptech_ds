"""T5 보수 — 수집 공백(시군구 x 연월) 재수집.

run_integrity_report.py 의 I2 가 찾아낸 누락 조합만 골라 RTMS API 에서 다시
받는다. 이미 받은 조합은 건드리지 않으므로 몇 번을 돌려도 안전하다.

누락 판정 기준은 `raw/rtms_trade/{YYYY}/{MM}/{시군구}_{YYYYMM}.meta.json`
존재 여부다. 거래가 0건이어도 meta 는 남으므로, meta 가 없다는 건 "받은 적
없음"을 뜻한다.

실행:
  .venv\\Scripts\\python.exe run_backfill_gaps.py --dry-run   # 목록만
  .venv\\Scripts\\python.exe run_backfill_gaps.py             # 전체 보수
  .venv\\Scripts\\python.exe run_backfill_gaps.py --year 2011 # 특정 연도만
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DIRS, SIGUNGU_CODES, load_secrets  # noqa: E402

RTMS_BASE = ("https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev"
             "/getRTMSDataSvcAptTradeDev")


def observed() -> set[tuple[str, str]]:
    out: set[tuple[str, str]] = set()
    for p in DIRS["raw_trade"].rglob("*.meta.json"):
        try:
            code, ym = p.stem.replace(".meta", "").split("_")
        except ValueError:
            continue
        out.add((code, ym))
    return out


def month_range(first: str, last: str) -> list[str]:
    yms, y, m = [], int(first[:4]), int(first[4:])
    while f"{y}{m:02d}" <= last:
        yms.append(f"{y}{m:02d}")
        m += 1
        if m > 12:
            y, m = y + 1, 1
    return yms


def find_gaps(year: str | None) -> list[tuple[str, str]]:
    seen = observed()
    if not seen:
        return []
    yms = sorted({ym for _, ym in seen})
    gaps = [(c, ym) for ym in month_range(yms[0], yms[-1])
            for c in SIGUNGU_CODES if (c, ym) not in seen]
    if year:
        gaps = [g for g in gaps if g[1].startswith(year)]
    return sorted(gaps, key=lambda g: (g[1], g[0]))


def fetch_one(code: str, ym: str, key: str, sleep: float) -> tuple[bool, int]:
    """(성공여부, 신고건수). 실패 시 (False, 0)."""
    out_dir = DIRS["raw_trade"] / ym[:4] / ym[4:]
    out_dir.mkdir(parents=True, exist_ok=True)
    url = (f"{RTMS_BASE}?serviceKey={key}&LAWD_CD={code}&DEAL_YMD={ym}"
           f"&numOfRows=1000&pageNo=1")
    for attempt in range(1, 4):
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            root = ET.fromstring(resp.text)
            rc = root.find(".//resultCode")
            if rc is not None and rc.text not in ("000", "00"):
                msg = root.find(".//resultMsg")
                raise RuntimeError(f"API {rc.text} {msg.text if msg is not None else ''}")
            tc = root.find(".//totalCount")
            rows = int(tc.text) if tc is not None and tc.text else 0

            (out_dir / f"{code}_{ym}.xml").write_text(resp.text, encoding="utf-8")
            (out_dir / f"{code}_{ym}.meta.json").write_text(
                json.dumps({"sigungu_code": code,
                            "sigungu_name": SIGUNGU_CODES.get(code, code),
                            "ym": ym, "rows": rows,
                            "fetched_at": datetime.now().isoformat(),
                            "source": "backfill_gaps"},
                           ensure_ascii=False, indent=2), encoding="utf-8")
            time.sleep(sleep)
            return True, rows
        except Exception as e:
            if attempt == 3:
                print(f"  실패 {ym} {code} {SIGUNGU_CODES.get(code, '')}: {e}")
                return False, 0
            time.sleep(2 ** attempt)
    return False, 0


def main() -> int:
    ap = argparse.ArgumentParser(description="수집 공백 재수집")
    ap.add_argument("--dry-run", action="store_true", help="목록만 출력")
    ap.add_argument("--year", help="특정 연도만 (예: 2011)")
    ap.add_argument("--sleep", type=float, default=0.35, help="호출 간격(초)")
    ap.add_argument("--limit", type=int, help="최대 호출 수")
    args = ap.parse_args()

    gaps = find_gaps(args.year)
    if not gaps:
        print("수집 공백 없음.")
        return 0

    from collections import Counter
    by_year = Counter(ym[:4] for _, ym in gaps)
    print(f"\n{'=' * 60}\n  수집 공백 {len(gaps):,}건\n{'=' * 60}")
    for y, n in sorted(by_year.items()):
        months = sorted({ym[4:] for _, ym in gaps if ym.startswith(y)})
        print(f"  {y}: {n:>5,}건  (월: {', '.join(months)})")

    if args.dry_run:
        print("\n--dry-run — 수집하지 않음")
        return 0

    if args.limit:
        gaps = gaps[:args.limit]

    key = load_secrets()["data_go_kr_service_key"]
    t0 = time.time()
    ok = fail = total_rows = 0
    print(f"\n수집 시작 ({len(gaps):,}건, 예상 {len(gaps) * args.sleep / 60:.1f}분)\n")

    for i, (code, ym) in enumerate(gaps, 1):
        good, rows = fetch_one(code, ym, key, args.sleep)
        if good:
            ok += 1
            total_rows += rows
        else:
            fail += 1
        if i % 100 == 0 or i == len(gaps):
            el = time.time() - t0
            eta = el / i * (len(gaps) - i)
            print(f"  [{i:,}/{len(gaps):,}] 성공 {ok:,} 실패 {fail} "
                  f"신고 {total_rows:,}건 | 남은 {eta / 60:.1f}분")

    print(f"\n{'=' * 60}")
    print(f"  완료 — 성공 {ok:,} / 실패 {fail} / 신고 {total_rows:,}건 "
          f"({(time.time() - t0) / 60:.1f}분)")
    print(f"  다음: run_step2.py --skip-map -> run_step3.py -> run_step4_unified_daily.py")
    print(f"{'=' * 60}\n")
    return 1 if fail and not ok else 0


if __name__ == "__main__":
    sys.exit(main())
