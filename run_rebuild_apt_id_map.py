"""T10a — apt_id_map 재생성 (구버전 apt_id 체계 청산).

`master/apt_id_map.parquet` 과 `legacy/realestate.db` 는 2026-05-03 이전
apt_id(법정동코드가 가짜 sha5)로 만들어져 있다. 그 뒤 `make_legal_dong_code()`
가 실제 umdCd 를 쓰도록 바뀌면서 해시 입력이 달라졌고, 결과적으로
`trade_events` 의 apt_id 와 **한 건도 겹치지 않는다**.

그래서 `run_step7_undervalue.py` 의 인프라 조인이 전부 빈 값이 됐다. 저평가
점수에서 인프라 가중치 0.35 가 5개월째 무효였다 (2026-05 ~ 10).

여기서 하는 일:
  1. trade_events 의 **신규 apt_id** 기준으로 apt_id_map 을 다시 만든다
  2. 좌표는 재지오코딩하지 않는다. 기존 좌표를 이름·주소 브리지로 옮겨온다
     — API 2만 건을 다시 태울 이유가 없다
  3. T6b 에서 받아둔 K-apt 목록을 bjdCode(법정동코드 10자리)로 붙인다.
     기존 step2 의 매칭은 시군구 + 이름 유사도뿐이라 후보가 수백 개였는데,
     법정동으로 좁히면 수십 분의 1이 된다
  4. T10 의 apt_group_id 도 함께 싣는다

실행:
  .venv\\Scripts\\python.exe run_rebuild_apt_id_map.py
  이어서: run_populate_apt_master.py -> external_data_collector.py --score
"""
from __future__ import annotations

import sys
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from common import DIRS  # noqa: E402

TRADE = DIRS["master"] / "trade_events.parquet"
GEO = ROOT / "web" / "cache" / "apt_geo.parquet"
GROUPS = DIRS["master"] / "apt_groups.parquet"
OUT = DIRS["master"] / "apt_id_map.parquet"

KAPT_MATCH_MIN = 0.85     # 자동 매칭 하한
KAPT_REVIEW_MIN = 0.70    # 이 아래는 매칭하지 않는다


def latest_kapt() -> pd.DataFrame | None:
    files = sorted(DIRS["staged_apt_info"].glob("kapt_list_*.parquet"))
    if not files:
        return None
    return pd.read_parquet(files[-1])


def build() -> pd.DataFrame:
    tr = pd.read_parquet(TRADE, columns=[
        "apt_id", "sigungu_code", "legal_dong_code", "legal_dong_name",
        "apt_name_norm", "apt_name_raw", "road_address"])
    base = (tr.groupby("apt_id")
              .agg(sigungu_code=("sigungu_code", "first"),
                   legal_dong_code=("legal_dong_code", lambda s: s.mode().iat[0]),
                   legal_dong_name=("legal_dong_name", lambda s: s.mode().iat[0]),
                   apt_name_norm=("apt_name_norm", "first"),
                   apt_name_raw=("apt_name_raw", lambda s: s.mode().iat[0]),
                   road_address=("road_address", lambda s: s.mode().iat[0]),
                   trade_count=("apt_id", "size"))
              .reset_index())
    print(f"  단지: {len(base):,}")

    # 좌표 — 재지오코딩 없이 기존 값을 브리지로 옮긴다
    if GEO.exists():
        geo = pd.read_parquet(GEO, columns=["apt_id", "lat", "lng"])
        base = base.merge(geo, on="apt_id", how="left")
    else:
        base["lat"] = base["lng"] = pd.NA
    print(f"  좌표 부착: {base['lat'].notna().sum():,} "
          f"({base['lat'].notna().mean() * 100:.1f}%)")

    # 묶음 id
    if GROUPS.exists():
        base = base.merge(pd.read_parquet(GROUPS), on="apt_id", how="left")
        base["apt_group_id"] = base["apt_group_id"].fillna(base["apt_id"])
    else:
        base["apt_group_id"] = base["apt_id"]

    # K-apt 매칭 — 법정동코드로 후보를 좁히고 이름 유사도로 고른다
    base["kapt_code"] = None
    base["match_score"] = 0.0
    base["match_status"] = "rtms_only"
    kapt = latest_kapt()
    if kapt is None:
        print("  K-apt 목록 없음 — 매칭 생략")
        return base

    kapt = kapt.dropna(subset=["bjdCode"]).copy()
    kapt["bjdCode"] = kapt["bjdCode"].astype(str)
    by_dong: dict[str, list[tuple[str, str]]] = {}
    for r in kapt.itertuples():
        by_dong.setdefault(r.bjdCode, []).append((r.kaptCode, str(r.kaptName)))

    auto = review = 0
    for i, r in enumerate(base.itertuples()):
        cands = by_dong.get(str(r.legal_dong_code))
        if not cands:
            continue
        name = str(r.apt_name_raw)
        best_code, best_score = None, 0.0
        for code, kname in cands:
            sc = SequenceMatcher(None, name, kname).ratio()
            if sc > best_score:
                best_code, best_score = code, sc
        if best_score >= KAPT_MATCH_MIN:
            base.at[i, "kapt_code"] = best_code
            base.at[i, "match_score"] = round(best_score, 3)
            base.at[i, "match_status"] = "auto_matched"
            auto += 1
        elif best_score >= KAPT_REVIEW_MIN:
            base.at[i, "match_score"] = round(best_score, 3)
            base.at[i, "match_status"] = "review_needed"
            review += 1

    print(f"  K-apt 매칭: 자동 {auto:,} / 검토필요 {review:,} / "
          f"미매칭 {len(base) - auto - review:,}")
    return base


def main() -> int:
    if not TRADE.exists():
        print("trade_events 없음")
        return 1
    print(f"\n{'=' * 60}\n  apt_id_map 재생성  {datetime.now():%Y-%m-%d %H:%M}\n{'=' * 60}")

    if OUT.exists():
        bak = OUT.with_name(f"apt_id_map.legacy_{datetime.now():%Y%m%d_%H%M%S}.parquet")
        OUT.replace(bak)
        print(f"  기존 파일 보관: {bak.name}")

    df = build()
    cols = ["apt_id", "apt_group_id", "sigungu_code", "legal_dong_code",
            "legal_dong_name", "apt_name_norm", "apt_name_raw", "road_address",
            "trade_count", "kapt_code", "match_score", "match_status",
            "lat", "lng"]
    df[cols].to_parquet(OUT, index=False, compression="zstd")
    print(f"\n  저장: {OUT} ({len(df):,}행)")
    print(f"  다음: run_populate_apt_master.py → "
          f"legacy/external_data_collector.py --score → run_step7_undervalue.py")
    print(f"{'=' * 60}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
