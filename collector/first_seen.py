"""거래 최초 관측일 원장 (T5a).

RTMS API 는 **공개일을 주지 않는다**. 응답에 있는 날짜는 계약일(deal_date)과
해제사유발생일뿐이다. 그래서 "오늘 새로 뜬 거래"를 알려면 우리가 직접
"언제 처음 봤는지"를 기록해야 한다.

원장: master/deal_first_seen.parquet
    deal_hash              거래 고유 해시 (common.make_deal_hash)
    first_seen_date        처음 관측한 날
    is_estimate            True = 과거분을 수집 메타로 역산한 추정값

최초 1회는 역산한다. raw/rtms_trade/**/*.meta.json 의 fetched_at 을 보고
"(시군구, 계약연월) 조합을 언제 처음 받았나"를 구해 그 날짜를 붙인다.
이미 쌓인 450만 건을 소급해 정확히 알 길은 없으므로 이건 **상한선**이다 —
"늦어도 이 날에는 갖고 있었다"는 뜻이지 "이 날 공개됐다"가 아니다.

원장이 생긴 다음부터는 추정이 아니다. step3 가 돌 때마다 원장에 없는
deal_hash 는 그날 처음 본 것이므로 실행일을 그대로 적고 is_estimate=False 로
남긴다. T9 의 일간 지표는 이 플래그가 False 인 행만 "신규"로 취급해야 한다.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd

LEDGER_NAME = "deal_first_seen.parquet"


def _meta_first_fetch(raw_trade_dir: Path) -> dict[tuple[str, str], str]:
    """(시군구코드, YYYYMM) -> 가장 이른 fetched_at 날짜(YYYY-MM-DD)."""
    out: dict[tuple[str, str], str] = {}
    for p in raw_trade_dir.rglob("*.meta.json"):
        try:
            m = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        code, ym = str(m.get("sigungu_code", "")), str(m.get("ym", ""))
        fetched = str(m.get("fetched_at", ""))[:10]
        if not (code and ym and fetched):
            continue
        key = (code, ym)
        if key not in out or fetched < out[key]:
            out[key] = fetched
    return out


def attach_first_seen(df: pd.DataFrame, master_dir: Path,
                      raw_trade_dir: Path, run_date: date | None = None
                      ) -> tuple[pd.DataFrame, dict]:
    """df 에 first_seen_date·first_seen_is_estimate 를 붙이고 원장을 갱신한다.

    df 는 deal_hash·sigungu_code·deal_date 를 갖고 있어야 한다.
    반환: (컬럼이 붙은 df, 통계 dict)
    """
    run_date = run_date or date.today()
    ledger_path = master_dir / LEDGER_NAME
    seeding = not ledger_path.exists()

    if seeding:
        ledger = pd.DataFrame(columns=["deal_hash", "first_seen_date", "is_estimate"])
    else:
        ledger = pd.read_parquet(ledger_path)

    known = set(ledger["deal_hash"]) if len(ledger) else set()
    new_mask = ~df["deal_hash"].isin(known)
    n_new = int(new_mask.sum())

    if n_new:
        new = df.loc[new_mask, ["deal_hash", "sigungu_code", "deal_date"]].copy()
        if seeding:
            # 과거분 역산: 해당 (시군구, 계약연월)을 처음 받은 날
            fetch_map = _meta_first_fetch(raw_trade_dir)
            ym = pd.to_datetime(new["deal_date"]).dt.strftime("%Y%m")
            keys = list(zip(new["sigungu_code"].astype(str), ym))
            fallback = run_date.isoformat()
            new["first_seen_date"] = [fetch_map.get(k, fallback) for k in keys]
            new["is_estimate"] = True
        else:
            new["first_seen_date"] = run_date.isoformat()
            new["is_estimate"] = False

        add = new[["deal_hash", "first_seen_date", "is_estimate"]].drop_duplicates("deal_hash")
        ledger = pd.concat([ledger, add], ignore_index=True) if len(ledger) else add

    # 사라진 거래(해제 후 삭제 등)가 있어도 원장은 남긴다 — 이력이므로 지우지 않는다
    ledger = ledger.drop_duplicates("deal_hash", keep="first")
    master_dir.mkdir(parents=True, exist_ok=True)
    tmp = ledger_path.with_suffix(".parquet.tmp")
    ledger.to_parquet(tmp, index=False, compression="zstd")
    tmp.replace(ledger_path)

    merged = df.merge(ledger, on="deal_hash", how="left")
    merged = merged.rename(columns={"is_estimate": "first_seen_is_estimate"})
    merged["first_seen_date"] = pd.to_datetime(merged["first_seen_date"])
    merged["first_seen_is_estimate"] = merged["first_seen_is_estimate"].fillna(True).astype(bool)

    stats = {
        "seeded": seeding,
        "ledger_rows": len(ledger),
        "new_hashes": n_new,
        "estimated": int(merged["first_seen_is_estimate"].sum()),
    }
    return merged, stats
