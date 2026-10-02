"""
run_step2_rent.py — 전월세 raw XML → staged parquet

산출물: staged/rent/{year}/{month}/{sigungu}/{code}_{ym}.parquet
  컬럼: apt_id, apt_seq, sigungu_code, legal_dong_code, legal_dong_name,
         apt_name_raw, deal_date, area_m2, area_m2_key, pyeong_bucket, floor,
         build_year, deposit, monthly_rent, contract_type, is_jeonse,
         deposit_per_m2, rent_ratio

실행:
  python run_step2_rent.py
  python run_step2_rent.py --force      # 기존 staged도 재처리
  python run_step2_rent.py --ym 202608  # 단일 월만
"""
import sys
import hashlib
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import BASE, DIRS, normalize_apt_name

import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
from datetime import datetime

CODE_VERSION = "v1.0-rent"

COL_RENAME = {
    "aptNm":        "apt_name_raw",
    "aptSeq":       "apt_seq",
    "buildYear":    "build_year_raw",
    "sggCd":        "sigungu_code",
    "umdNm":        "legal_dong_name",
    "excluUseAr":   "area_m2_raw",
    "dealYear":     "year_raw",
    "dealMonth":    "month_raw",
    "dealDay":      "day_raw",
    "floor":        "floor_raw",
    "jibun":        "jibun",
    "deposit":      "deposit_raw",
    "monthlyRent":  "monthly_rent_raw",
    "contractType": "contract_type",
    "contractTerm": "contract_term",
    "preDeposit":   "pre_deposit_raw",
    "preMonthlyRent": "pre_monthly_rent_raw",
    "roadnm":       "road_name",
    "roadnmbonbun": "road_main_no",
}


def parse_amount(s: str) -> float | None:
    if not s or not isinstance(s, str):
        return None
    try:
        return float(s.replace(",", "").strip())
    except ValueError:
        return None


def clean_rent_xml(xml_path: Path) -> pd.DataFrame:
    try:
        xml_text = xml_path.read_text(encoding="utf-8")
        root = ET.fromstring(xml_text)
    except Exception as e:
        print(f"  XML 파싱 오류: {xml_path.name} — {e}")
        return pd.DataFrame()

    items = root.findall(".//item")
    if not items:
        return pd.DataFrame()

    rows = [{c.tag: (c.text or "").strip() for c in item} for item in items]
    df   = pd.DataFrame(rows).rename(columns=COL_RENAME)

    # 날짜
    df["deal_date"] = pd.to_datetime(
        df["year_raw"].astype(str).str.zfill(4) + "-" +
        df["month_raw"].astype(str).str.zfill(2) + "-" +
        df["day_raw"].astype(str).str.zfill(2),
        errors="coerce",
    )

    # 숫자형
    df["area_m2"]        = pd.to_numeric(df.get("area_m2_raw",   pd.Series(dtype=str)), errors="coerce")
    df["floor"]          = pd.to_numeric(df.get("floor_raw",     pd.Series(dtype=str)), errors="coerce").astype("Int64")
    df["build_year"]     = pd.to_numeric(df.get("build_year_raw",pd.Series(dtype=str)), errors="coerce").astype("Int64")
    df["deposit"]        = df.get("deposit_raw",      pd.Series(dtype=str)).apply(parse_amount)
    df["monthly_rent"]   = df.get("monthly_rent_raw", pd.Series(dtype=str)).apply(parse_amount)
    df["pre_deposit"]    = df.get("pre_deposit_raw",  pd.Series(dtype=str)).apply(parse_amount)
    df["pre_monthly_rent"] = df.get("pre_monthly_rent_raw", pd.Series(dtype=str)).apply(parse_amount)

    # 전세/월세 구분
    df["is_jeonse"] = df["monthly_rent"].fillna(0) == 0

    # 면적 버킷
    from common import to_pyeong_bucket
    df["pyeong_bucket"] = df["area_m2"].apply(
        lambda x: to_pyeong_bucket(x) if pd.notna(x) else None
    )
    df["area_m2_key"] = df["area_m2"].round(2)

    # 전세가율 피처 (월세 전환: 전세환산보증금 = 보증금 + 월세/0.04*12)
    df["deposit_per_m2"] = df["deposit"] / df["area_m2"].replace(0, np.nan)
    monthly_eps = df["monthly_rent"].fillna(0)
    df["jeonse_equiv"]   = df["deposit"] + monthly_eps / 0.04 * 12   # 전세환산 보증금
    df["jeonse_per_m2"]  = df["jeonse_equiv"] / df["area_m2"].replace(0, np.nan)

    # apt_id: sigungu + apt_seq (apt_seq 있으면 활용, 없으면 sha256)
    df["apt_name_norm"] = df["apt_name_raw"].apply(normalize_apt_name)
    sgg = df["sigungu_code"].fillna("").astype(str).str.zfill(5).str[:5]

    # apt_seq가 있으면 그대로 키로 사용 (trade와 일관성 유지)
    has_seq = df.get("apt_seq", pd.Series([""] * len(df))).fillna("").str.strip().ne("")
    df["apt_id"] = has_seq.map(
        {True: None, False: None}   # 아래에서 계산
    )
    if "apt_seq" in df.columns and has_seq.any():
        # apt_seq 있는 행: "sigungu-seq" 형태로 apt_id 생성
        df.loc[has_seq, "apt_id"] = sgg[has_seq] + "-" + df.loc[has_seq, "apt_seq"].str.split("-").str[-1]
    # apt_seq 없는 행: sha256 기반
    road_nm  = df.get("road_name",    pd.Series([""] * len(df))).fillna("").astype(str)
    road_no  = df.get("road_main_no", pd.Series([""] * len(df))).fillna("").astype(str)
    road_addr = (road_nm + " " + road_no).str.strip()
    raw_keys = (sgg + "|" + df["apt_name_norm"].fillna("") + "|" + road_addr.str[:30])
    df.loc[~has_seq, "apt_id"] = raw_keys[~has_seq].map(
        lambda k: hashlib.sha256(k.encode("utf-8")).hexdigest()[:16]
    )

    keep = [
        "apt_id", "apt_seq", "sigungu_code", "legal_dong_name",
        "apt_name_raw", "apt_name_norm",
        "deal_date", "area_m2", "area_m2_key", "pyeong_bucket",
        "floor", "build_year",
        "deposit", "monthly_rent", "is_jeonse",
        "deposit_per_m2", "jeonse_equiv", "jeonse_per_m2",
        "pre_deposit", "pre_monthly_rent",
        "contract_type", "contract_term",
    ]
    return df[[c for c in keep if c in df.columns]]


def staged_is_fresh(xml_path: Path, out_path: Path) -> bool:
    if not out_path.exists():
        return False
    try:
        if out_path.stat().st_mtime <= xml_path.stat().st_mtime:
            return False
        ver_file = out_path.with_suffix(".parquet.ver")
        return ver_file.exists() and ver_file.read_text().strip() == CODE_VERSION
    except Exception:
        return False


def stage_all(force: bool = False, ym_filter: str | None = None) -> None:
    xml_files = list(DIRS["raw_rent"].rglob("*.xml"))
    if ym_filter:
        xml_files = [f for f in xml_files if ym_filter in f.stem]
    print(f"처리할 전월세 XML: {len(xml_files):,}개 (force={force}, version={CODE_VERSION})")

    processed = skipped = empty = errors = 0
    all_frames = []

    for xf in xml_files:
        # 경로: raw/rtms_rent/year/month/code_ym.xml
        yr  = xf.parent.parent.name
        mo  = xf.parent.name
        out_dir = DIRS["staged_rent"] / yr / mo
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / xf.stem + ".parquet" if False else out_dir / (xf.stem + ".parquet")

        if not force and staged_is_fresh(xf, out_path):
            skipped += 1
            continue

        try:
            df = clean_rent_xml(xf)
        except Exception as e:
            print(f"  오류: {xf.name} — {e}")
            errors += 1
            continue

        if df.empty:
            empty += 1
            out_path.write_bytes(b"")   # 빈 파일로 마킹
            continue

        df.to_parquet(out_path, index=False, compression="zstd")
        out_path.with_suffix(".parquet.ver").write_text(CODE_VERSION)
        all_frames.append(df)
        processed += 1

    print(f"\n  처리: {processed:,}  스킵: {skipped:,}  빈파일: {empty:,}  오류: {errors:,}")

    if all_frames and (ym_filter or processed > 0):
        combined = pd.concat(all_frames, ignore_index=True)
        print(f"  staged 합계: {len(combined):,}건  전세: {combined['is_jeonse'].sum():,}  월세: {(~combined['is_jeonse']).sum():,}")
        return combined

    return None


def main():
    parser = argparse.ArgumentParser(description="전월세 raw XML → staged parquet")
    parser.add_argument("--force", action="store_true", help="기존 staged도 재처리")
    parser.add_argument("--ym", metavar="YYYYMM", default=None, help="단일 월만 처리")
    args = parser.parse_args()

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*60}")
    print(f"  전월세 staged 정제  {ts}")
    print(f"{'='*60}\n")

    result = stage_all(force=args.force, ym_filter=args.ym)

    print(f"\n저장 위치: {DIRS['staged_rent']}")


if __name__ == "__main__":
    main()
