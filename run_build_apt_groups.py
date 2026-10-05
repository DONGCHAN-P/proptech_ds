"""T10 — 단지키 2차 검증: 과분할 해소 (apt_group_id).

T6 에서 apt_id 는 `법정동 + 정규화단지명 + 도로명주소` 로 정했다. 주소를
넣은 덕에 같은 이름의 다른 단지는 안전하게 갈렸지만, 반대로 **출입구가 여럿인
한 단지가 주소별로 쪼개진다**. 개포주공1단지가 개포로·선릉로로 갈리는 식이다.

apt_id 를 다시 바꾸지는 않는다. 바꾸면 또 전량 재생성이고, 무엇보다 주소 단위
식별자는 그 자체로 쓸모가 있다. 대신 **묶음 식별자 `apt_group_id`** 를 따로
만든다.

    apt_id        주소 단위 — 정밀, 변하지 않음
    apt_group_id  단지 단위 — 집계·표시용

병합 판정은 **좌표 거리**로 한다. 이름이 같고 준공년이 같아도 멀리 떨어져
있으면 다른 단지다. 같은 이름의 "주공"이 한 법정동에 여럿 있을 수 있다.

산출물:
  master/apt_groups.parquet        apt_id -> apt_group_id (전 단지)
  exports/daily/apt_merge_YYYYMMDD.csv    병합된 묶음
  exports/daily/apt_unmerged_YYYYMMDD.csv 거리 때문에 못 묶은 건 (수동 검토용)

실행:
  .venv\\Scripts\\python.exe run_build_apt_groups.py
  .venv\\Scripts\\python.exe run_build_apt_groups.py --max-dist 500
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from common import DIRS  # noqa: E402

TRADE = DIRS["master"] / "trade_events.parquet"
# 좌표는 master/apt_id_map 이 정본이다 (T10a 이후). web/cache 는
# 서빙용 파생물이라 거기에 의존하면 웹 빌드 순서에 묶인다.
GEO = DIRS["master"] / "apt_id_map.parquet"
OUT = DIRS["master"] / "apt_groups.parquet"

# 같은 단지의 출입구 사이 거리.
#
# 300m 로 시작했더니 해소율 88% 로 로드맵 기준(90%)에 못 미쳤다. 남은 쌍을 보니
# 300~500m 구간(75쌍)이 전부 같은 단지였다 — 우만주공2단지가 같은 길 54번과
# 92번, 상계주공1단지가 고층·저층으로 갈린 식이다. 대단지는 단지 폭 자체가
# 400m 를 넘는다. 500m 로 넓혀 92.5% 를 해소했다.
#
# 더 넓히면(600m 에서 93.4%) 옆 단지를 삼킬 위험이 커지는 데 비해 얻는 게 적다.
# 1km 넘게 떨어진 41쌍은 같은 이름의 다른 단지이거나 좌표 오류이므로 묶지 않고
# apt_unmerged CSV 로 남겨 사람이 본다.
MAX_DIST_M = 500


def haversine_m(lat1, lng1, lat2, lng2) -> np.ndarray:
    r = 6371000.0
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dp = p2 - p1
    dl = np.radians(lng2) - np.radians(lng1)
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(a))


def load() -> pd.DataFrame:
    tr = pd.read_parquet(TRADE, columns=[
        "apt_id", "legal_dong_code", "legal_dong_name", "sigungu_name",
        "apt_name_norm", "apt_name_raw", "build_year", "road_address"])
    agg = (tr.groupby("apt_id")
             .agg(legal_dong_code=("legal_dong_code", "first"),
                  legal_dong_name=("legal_dong_name", "first"),
                  sigungu_name=("sigungu_name", "first"),
                  apt_name_norm=("apt_name_norm", "first"),
                  apt_name_raw=("apt_name_raw", "first"),
                  build_year=("build_year", "max"),
                  road_address=("road_address", "first"),
                  deals=("apt_id", "size"))
             .reset_index())
    if GEO.exists():
        geo = pd.read_parquet(GEO, columns=["apt_id", "lat", "lng"])
        agg = agg.merge(geo, on="apt_id", how="left")
    else:
        agg["lat"] = np.nan
        agg["lng"] = np.nan
    return agg


def build_groups(df: pd.DataFrame, max_dist: int) -> tuple[pd.DataFrame, list, list]:
    """같은 (법정동, 정규화명, 준공년) 안에서 가까운 것끼리 묶는다.

    단일 연결(single-linkage)로 이어붙인다. A-B 가 가깝고 B-C 가 가까우면
    A-C 가 다소 멀어도 한 단지로 본다. 출입구가 일렬로 늘어선 대단지를
    고려한 선택이다.
    """
    df = df.copy()
    df["apt_group_id"] = df["apt_id"]
    merged, unmerged = [], []

    keys = ["legal_dong_code", "apt_name_norm", "build_year"]
    for key, g in df.groupby(keys, dropna=False):
        if len(g) < 2:
            continue
        idx = g.index.to_list()
        lat = g["lat"].to_numpy()
        lng = g["lng"].to_numpy()

        parent = {i: i for i in idx}

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a, b):
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[rb] = ra

        far_pairs = []
        for a in range(len(idx)):
            for b in range(a + 1, len(idx)):
                if np.isnan(lat[a]) or np.isnan(lat[b]):
                    continue
                d = float(haversine_m(lat[a], lng[a], lat[b], lng[b]))
                if d <= max_dist:
                    union(idx[a], idx[b])
                else:
                    far_pairs.append((idx[a], idx[b], round(d)))

        # 묶음별 대표: 거래가 가장 많은 apt_id
        clusters: dict = {}
        for i in idx:
            clusters.setdefault(find(i), []).append(i)
        for members in clusters.values():
            if len(members) < 2:
                continue
            rep = max(members, key=lambda i: df.at[i, "deals"])
            for i in members:
                df.at[i, "apt_group_id"] = df.at[rep, "apt_id"]
            merged.append({
                "apt_group_id": df.at[rep, "apt_id"],
                "시군구": df.at[rep, "sigungu_name"],
                "법정동": df.at[rep, "legal_dong_name"],
                "단지명": df.at[rep, "apt_name_raw"],
                "준공년": key[2],
                "병합_수": len(members),
                "거래_합": int(df.loc[members, "deals"].sum()),
                "주소들": " | ".join(sorted(set(df.loc[members, "road_address"]))),
            })

        # 거리 때문에 못 묶은 쌍 — 다른 단지일 수도, 좌표 오류일 수도 있다
        for a, b, d in far_pairs:
            if find(a) != find(b):
                unmerged.append({
                    "시군구": df.at[a, "sigungu_name"],
                    "법정동": df.at[a, "legal_dong_name"],
                    "단지명": df.at[a, "apt_name_raw"],
                    "준공년": key[2],
                    "거리_m": d,
                    "주소_A": df.at[a, "road_address"],
                    "주소_B": df.at[b, "road_address"],
                    "거래_A": int(df.at[a, "deals"]),
                    "거래_B": int(df.at[b, "deals"]),
                })
    return df, merged, unmerged


def main() -> int:
    ap = argparse.ArgumentParser(description="T10 과분할 해소")
    ap.add_argument("--max-dist", type=int, default=MAX_DIST_M,
                    help="같은 단지로 볼 최대 거리(m)")
    args = ap.parse_args()

    if not TRADE.exists():
        print("trade_events 없음")
        return 1

    print(f"\n{'=' * 60}\n  단지 묶음 생성  {datetime.now():%Y-%m-%d %H:%M}\n{'=' * 60}")
    df = load()
    print(f"  단지(주소 단위): {len(df):,}  |  좌표 보유 {df['lat'].notna().mean() * 100:.1f}%")

    df, merged, unmerged = build_groups(df, args.max_dist)

    n_groups = df["apt_group_id"].nunique()
    n_merged_ids = (df["apt_group_id"] != df["apt_id"]).sum()
    print(f"\n  병합 묶음: {len(merged):,}개  (흡수된 apt_id {n_merged_ids:,}개)")
    print(f"  최종 단지(묶음 단위): {n_groups:,}  ({len(df) - n_groups:,}개 감소)")
    print(f"  거리 초과로 못 묶은 쌍: {len(unmerged):,}")

    DIRS["master"].mkdir(parents=True, exist_ok=True)
    df[["apt_id", "apt_group_id"]].to_parquet(OUT, index=False, compression="zstd")

    stamp = datetime.now().strftime("%Y%m%d")
    ed = DIRS["exports_daily"]
    ed.mkdir(parents=True, exist_ok=True)
    if merged:
        pd.DataFrame(merged).sort_values("거래_합", ascending=False).to_csv(
            ed / f"apt_merge_{stamp}.csv", index=False, encoding="utf-8-sig")
    if unmerged:
        pd.DataFrame(unmerged).sort_values("거리_m").to_csv(
            ed / f"apt_unmerged_{stamp}.csv", index=False, encoding="utf-8-sig")

    print(f"\n  저장: {OUT}")
    print(f"        {ed / f'apt_merge_{stamp}.csv'}")
    print(f"        {ed / f'apt_unmerged_{stamp}.csv'}")
    print(f"{'=' * 60}\n")

    if merged:
        top = pd.DataFrame(merged).nlargest(5, "거래_합")
        print("병합 상위 5:")
        print(top[["시군구", "법정동", "단지명", "병합_수", "거래_합"]]
              .to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
