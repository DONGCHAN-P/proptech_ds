"""신도시 비교 분석 — 롱폼 1편의 근거.

대본의 주장("강남 접근성 1순위 · 일자리 2순위 · 주변 공급은 브레이크")이
데이터로 서는지 본다. Pre-Mortem 에 적힌 대로, 차트를 먼저 그려 보고
대본을 확정한다.

평당가 중위값을 쓴다. 평균은 한두 건의 초고가가 끌어올리고, 총액은 평형
구성이 바뀌면 흔들린다.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from metrics.filters import trades_cte  # noqa: E402

TRADE = (ROOT / "master" / "trade_events.parquet").as_posix()

# 신도시 경계는 법정동으로 잡는다. 시군구 단위로 잡으면 구도심이 섞여
# "신도시가 올랐나"가 아니라 "그 시가 올랐나"를 재게 된다.
TOWNS = {
    "광교":      ("수원영통구", ["이의동", "하동"]),
    "동탄2":     ("화성동탄구", ["청계동", "영천동", "산척동", "목동",
                               "여울동", "오산동", "신동", "송동",
                               "방교동", "장지동", "중동"]),
    "동탄1":     ("화성동탄구", ["반송동", "석우동", "능동"]),
    "인천 검단": ("검단구", ["원당동", "당하동", "마전동", "불로동",
                            "왕길동", "오류동"]),
    "김포 한강": ("김포시", ["장기동", "구래동", "마산동", "운양동"]),
    "파주 운정": ("파주시", ["와동동", "야당동", "목동동", "동패동",
                            "다율동"]),
    "양주 옥정": ("양주시", ["옥정동", "회천동"]),
}


def con():
    import duckdb
    return duckdb.connect()


def yearly(c, where: str, pyeong: str | None = "30P") -> dict[int, tuple]:
    pf = f"AND pyeong_bucket='{pyeong}'" if pyeong else ""
    rows = c.execute(f"""
        {trades_cte(TRADE)}
        SELECT year(deal_date) AS y, count(*) AS n,
               round(median(price_per_pyeong)) AS ppy
        FROM trades
        WHERE price_per_pyeong > 0 {pf} AND ({where})
        GROUP BY 1 ORDER BY 1
    """).fetchall()
    return {int(y): (int(n), int(p)) for y, n, p in rows if p}


def town_where(town: str) -> str:
    sgg, dongs = TOWNS[town]
    inlist = ",".join(f"'{d}'" for d in dongs)
    return f"sigungu_name='{sgg}' AND legal_dong_name IN ({inlist})"


def main() -> None:
    c = con()
    base = yearly(c, "1=1")          # 수도권 전체
    years = [2015, 2018, 2019, 2021, 2022, 2024, 2025, 2026]

    print("=" * 78)
    print("  30평대 중위 평당가 (만원) · 괄호는 그해 거래 건수")
    print("=" * 78)
    hdr = "  " + "구분".ljust(12) + "".join(f"{y:>9}" for y in years)
    print(hdr)
    rows = {"수도권 전체": base}
    for t in TOWNS:
        rows[t] = yearly(c, town_where(t))
    for name, d in rows.items():
        line = "  " + name.ljust(12)
        for y in years:
            v = d.get(y)
            line += f"{v[1]:>9,}" if v else f"{'-':>9}"
        print(line)
        line2 = "  " + "".ljust(12)
        for y in years:
            v = d.get(y)
            line2 += f"{'(' + str(v[0]) + ')':>9}" if v else f"{'':>9}"
        print(line2)
    print()

    # 핵심: 수도권 평균 대비 초과 상승률
    print("=" * 78)
    print("  수도권 대비 초과 상승률 (각 구간, %p)")
    print("=" * 78)
    spans = [(2015, 2021, "상승기 2015→2021"),
             (2021, 2026, "조정 이후 2021→2026"),
             (2015, 2026, "전체 2015→2026"),
             (2019, 2026, "2019→2026")]
    print("  " + "구분".ljust(12) + "".join(f"{lab:>22}" for _, _, lab in spans))
    for name, d in rows.items():
        line = "  " + name.ljust(12)
        for a, b, _ in spans:
            if d.get(a) and d.get(b):
                g = (d[b][1] / d[a][1] - 1) * 100
                bg = (base[b][1] / base[a][1] - 1) * 100
                ex = g - bg
                line += f"{g:>+10.0f}% ({ex:>+5.0f}p)" if name != "수도권 전체" \
                    else f"{g:>+10.0f}%{'':>8}"
            else:
                line += f"{'-':>22}"
        print(line)


def composition(c) -> None:
    """검단의 +47% 가 진짜 회복인가, 새 집이 섞인 것인가.

    신도시는 입주가 끝날 때까지 **거래되는 집 자체가 바뀐다.** 중위값이
    올라도 "같은 집이 올랐다"는 뜻이 아니다.
    """
    print("\n" + "=" * 78)
    print("  2026년 거래의 준공 연도 구성 (30평대)")
    print("=" * 78)
    for t in TOWNS:
        rows = c.execute(f"""
            {trades_cte(TRADE)}
            SELECT CASE WHEN build_year >= 2020 THEN '2020년 이후 준공'
                        ELSE '그 이전' END AS g,
                   count(*) AS n, round(median(price_per_pyeong)) AS ppy
            FROM trades
            WHERE year(deal_date)=2026 AND pyeong_bucket='30P'
              AND price_per_pyeong>0 AND ({town_where(t)})
            GROUP BY 1 ORDER BY 1
        """).fetchall()
        tot = sum(r[1] for r in rows) or 1
        bits = [f"{g} {n}건({n / tot * 100:.0f}%) 평당 {p:,}" for g, n, p in rows]
        print(f"  {t.ljust(10)} " + " · ".join(bits))


def same_apt(c) -> None:
    """**같은 단지만** 추적한다.

    구성 변화를 걷어내는 가장 확실한 방법이다. 두 해 모두 거래가 있었던
    단지만 남기고, 단지별 상승률의 중앙값을 본다.
    """
    print("\n" + "=" * 78)
    print("  같은 단지만 추적한 상승률 중앙값 (30평대)")
    print("=" * 78)
    spans = [(2015, 2026), (2019, 2026), (2021, 2026)]
    print("  " + "구분".ljust(12) + "".join(
        f"{str(a) + '→' + str(b):>18}" for a, b in spans))
    for name, where in [("수도권 전체", "1=1")] + [
            (t, town_where(t)) for t in TOWNS]:
        line = "  " + name.ljust(12)
        for a, b in spans:
            r = c.execute(f"""
                {trades_cte(TRADE)},
                g AS (SELECT apt_id,
                        median(CASE WHEN year(deal_date)={a}
                               THEN price_per_pyeong END) AS p0,
                        median(CASE WHEN year(deal_date)={b}
                               THEN price_per_pyeong END) AS p1
                      FROM trades
                      WHERE pyeong_bucket='30P' AND price_per_pyeong>0
                        AND ({where})
                      GROUP BY 1)
                SELECT count(*), round(median(p1/p0) * 100 - 100)
                FROM g WHERE p0>0 AND p1>0
            """).fetchone()
            line += f"{(str(int(r[1])) + '% (' + str(r[0]) + '곳)'):>18}" \
                if r and r[0] else f"{'-':>18}"
        print(line)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", default="all",
                    choices=["all", "table", "comp", "same"])
    a = ap.parse_args()
    _c = con()
    if a.part in ("all", "table"):
        main()
    if a.part in ("all", "comp"):
        composition(_c)
    if a.part in ("all", "same"):
        same_apt(_c)
