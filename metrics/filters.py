"""T8/T9 — 지표 계산 공통 필터.

모든 지표는 여기를 통과해야 한다. 각자 WHERE 를 쓰면 하나씩 빠뜨린다.
실제로 step8(신규 거래 요약)이 해제 필터 없이 돌아서 **해제된 거래가
특이거래 Top 100 에 올라가 있었다** — 발행됐으면 "신고가"라고 소개한 거래가
취소된 건이었을 것이다.

쓰는 법 두 가지:

    # pandas
    from metrics.filters import apply_filters
    df = apply_filters(df)                       # 해제 제외 (기본)
    df = apply_filters(df, min_households=300)   # + 300세대 미만 제외

    # DuckDB SQL — 모든 지표 쿼리의 FROM 에 이걸 넣는다
    from metrics.filters import TRADES_CTE
    con.sql(f"{TRADES_CTE} SELECT ... FROM trades WHERE ...")
"""
from __future__ import annotations

import pandas as pd

# 가격 이상치 경계 (만원/㎡). run_quality_check.py 와 같은 값을 쓴다.
PRICE_PER_M2_MIN = 50
PRICE_PER_M2_MAX = 20_000

# 층 구간화 경계
FLOOR_LOW_MAX = 3
FLOOR_HIGH_MIN = 16


def floor_band(floor) -> str:
    """층을 저/중/고로 묶는다.

    발행 콘텐츠에 정확한 층을 쓰면 특정 세대가 식별된다. 동·호수 미표기와
    같은 취지다.
    """
    if floor is None or floor != floor:
        return "미상"
    f = int(floor)
    if f <= FLOOR_LOW_MAX:
        return "저층"
    if f >= FLOOR_HIGH_MIN:
        return "고층"
    return "중층"


def apply_filters(
    df: pd.DataFrame,
    *,
    exclude_cancelled: bool = True,
    exclude_price_outliers: bool = True,
    min_households: int | None = None,
    households_col: str = "households",
) -> pd.DataFrame:
    """지표 계산 전 공통 필터.

    min_households 를 주면 세대수가 **확인된** 단지만 걸러낸다. 세대수를
    모르는 단지(K-apt 미등록)는 남긴다 — "미등록 = 소규모"가 아니기 때문이다.
    모르는 걸 작다고 단정하면 멀쩡한 대단지가 통째로 사라진다.
    """
    out = df
    if exclude_cancelled and "is_canceled" in out.columns:
        out = out[out["is_canceled"].fillna(False) == False]  # noqa: E712
    if exclude_price_outliers and "price_per_m2" in out.columns:
        p = out["price_per_m2"]
        out = out[p.isna() | ((p >= PRICE_PER_M2_MIN) & (p <= PRICE_PER_M2_MAX))]
    if min_households is not None and households_col in out.columns:
        h = out[households_col]
        out = out[h.isna() | (h >= min_households)]
    return out.copy()


def trades_cte(path: str, *, min_households: int | None = None) -> str:
    """지표 SQL 의 앞에 붙이는 공통 CTE.

    DuckDB 쿼리는 전부 `FROM trades` 로 시작하게 만들어, 개별 쿼리가 필터를
    빠뜨릴 여지를 없앤다.
    """
    conds = [
        "NOT coalesce(is_canceled, false)",
        "deal_amount > 0",
        f"(price_per_m2 IS NULL OR price_per_m2 BETWEEN "
        f"{PRICE_PER_M2_MIN} AND {PRICE_PER_M2_MAX})",
    ]
    if min_households is not None:
        conds.append(f"(households IS NULL OR households >= {min_households})")
    return (f"WITH trades AS (\n"
            f"    SELECT *, CASE WHEN floor IS NULL THEN '미상'\n"
            f"                   WHEN floor <= {FLOOR_LOW_MAX} THEN '저층'\n"
            f"                   WHEN floor >= {FLOOR_HIGH_MIN} THEN '고층'\n"
            f"                   ELSE '중층' END AS floor_band\n"
            f"    FROM '{path}'\n"
            f"    WHERE {' AND '.join(conds)}\n"
            f")\n")
