"""T6 — 단지 식별키 충돌 리포트.

apt_id 하나가 서로 다른 단지를 삼키고 있는지(과병합), 같은 단지가 여러
apt_id 로 쪼개져 있는지(과분할)를 찾아 목록으로 남긴다.

산출물:
  exports/daily/key_collision_YYYYMMDD.csv   과병합 의심 (한 apt_id, 여러 단지명)
  exports/daily/key_split_YYYYMMDD.csv       과분할 의심 (한 단지, 여러 apt_id)

실행:
  .venv\\Scripts\\python.exe run_key_collision_report.py
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DIRS  # noqa: E402

TRADE = DIRS["master"] / "trade_events.parquet"
OUT = DIRS["exports_daily"]

COLS = ["apt_id", "apt_name_raw", "apt_name_norm", "legal_dong_code",
        "legal_dong_name", "sigungu_name", "road_address", "build_year"]


def overmerge(df: pd.DataFrame) -> pd.DataFrame:
    """한 apt_id 가 여러 단지명을 삼킨 경우.

    apt_name_norm 까지 같다면 동 번호 표기 차이일 뿐 같은 단지다. 정규화된
    이름이 둘 이상인 경우만 진짜 과병합으로 본다.
    """
    g = df.groupby("apt_id").agg(
        norm_n=("apt_name_norm", "nunique"),
        raw_n=("apt_name_raw", "nunique"),
        거래=("apt_name_raw", "size"),
        시군구=("sigungu_name", "first"),
        법정동=("legal_dong_name", "first"),
        주소=("road_address", "first"),
        단지명들=("apt_name_raw", lambda x: " | ".join(sorted(set(x))[:6])),
        정규화명들=("apt_name_norm", lambda x: " | ".join(sorted(set(x))[:6])),
    ).reset_index()
    out = g[g["norm_n"] > 1].copy()
    out["판정"] = "과병합 — 서로 다른 단지가 한 id"
    return out.sort_values("거래", ascending=False)


def oversplit(df: pd.DataFrame) -> pd.DataFrame:
    """같은 (법정동, 정규화 단지명, 준공년)인데 apt_id 가 여럿인 경우.

    도로명주소가 달라 갈린 것이다. 같은 단지의 출입구가 여럿이면 과분할이고,
    신도시 '마을' 이름을 공유하는 별개 단지면 정상이다. 사람이 봐야 갈린다.
    """
    g = df.groupby(["legal_dong_code", "apt_name_norm", "build_year"]).agg(
        id_n=("apt_id", "nunique"),
        거래=("apt_id", "size"),
        시군구=("sigungu_name", "first"),
        법정동=("legal_dong_name", "first"),
        주소들=("road_address", lambda x: " | ".join(sorted(set(x))[:6])),
        단지명들=("apt_name_raw", lambda x: " | ".join(sorted(set(x))[:4])),
    ).reset_index()
    out = g[g["id_n"] > 1].copy()
    out["판정"] = "과분할 의심 — 주소만 다른 같은 단지일 수 있음"
    return out.sort_values("거래", ascending=False)


def main() -> int:
    if not TRADE.exists():
        print("trade_events 없음")
        return 1

    df = pd.read_parquet(TRADE, columns=COLS)
    stamp = datetime.now().strftime("%Y%m%d")
    OUT.mkdir(parents=True, exist_ok=True)

    om, os_ = overmerge(df), oversplit(df)
    p1 = OUT / f"key_collision_{stamp}.csv"
    p2 = OUT / f"key_split_{stamp}.csv"
    om.to_csv(p1, index=False, encoding="utf-8-sig")
    os_.to_csv(p2, index=False, encoding="utf-8-sig")

    print(f"\n{'=' * 60}\n  단지 식별키 충돌 리포트  {datetime.now():%Y-%m-%d %H:%M}\n{'=' * 60}")
    print(f"  전체 단지: {df['apt_id'].nunique():,}")
    print(f"  과병합: {len(om):,}건 (영향 거래 {int(om['거래'].sum()):,})")
    print(f"  과분할 의심: {len(os_):,}건 (영향 거래 {int(os_['거래'].sum()):,})")
    print(f"\n  {p1}\n  {p2}\n{'=' * 60}\n")

    if len(om):
        print("과병합 상위 5:")
        print(om.head(5)[["시군구", "법정동", "단지명들", "거래"]]
              .to_string(index=False, max_colwidth=46))
    return 0


if __name__ == "__main__":
    sys.exit(main())
