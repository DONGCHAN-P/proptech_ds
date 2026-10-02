"""T5 — 백필 DB 무결성 검증 리포트.

run_quality_check.py 가 매일 도는 8종 sanity 검사라면, 이쪽은 2006~ 전체
백필을 훑는 심층 점검이다. 수집 공백·중복·결측·이상치를 찾아 보수 태스크의
근거를 만든다.

점검 항목:
  I1  연도별 거래 건수 분포 + 해제 비율
  I2  시군구 x 연월 수집 공백 (raw meta 기준)
  I3  파이프라인 단계별 건수 정합 (raw -> staged -> master)
  I4  핵심 컬럼 결측률
  I5  중복 의심 (거래 동일성 키 기준)
  I6  가격·면적 이상치
  I7  apt_id 일관성 (세대 불일치 탐지 — T10a 근거)

산출물:
  exports/daily/integrity_report_YYYYMMDD.md
  exports/daily/integrity_report_YYYYMMDD.json

실행:
  .venv\\Scripts\\python.exe run_integrity_report.py
  .venv\\Scripts\\python.exe run_integrity_report.py --strict   # 치명 결함 시 exit 1
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import BASE, DIRS, SIGUNGU_CODES  # noqa: E402

TRADE = (DIRS["master"] / "trade_events.parquet").as_posix()
STAGED = (DIRS["staged_trade"] / "**" / "*.parquet").as_posix()
OUT_DIR = DIRS["exports_daily"]

# 거래 동일성 키 — T5a 의 deal_hash 가 들어오기 전까지 쓰는 잠정 기준
DEAL_KEY = "legal_dong_code, apt_name_norm, deal_date, deal_amount, area_m2, floor"

# 치명 판정 임계
MAX_DUP_RATIO = 0.001      # 중복 0.1% 초과면 치명
MAX_NULL_RATIO = 0.05      # 핵심 컬럼 결측 5% 초과면 치명
MIN_COVERAGE = 0.95        # 시군구x연월 커버리지 95% 미만이면 치명


class Report:
    def __init__(self) -> None:
        self.sections: list[dict] = []
        self.critical: list[str] = []

    def add(self, code: str, title: str, body: str, data=None,
            critical: str | None = None) -> None:
        self.sections.append({"code": code, "title": title,
                              "body": body, "data": data})
        if critical:
            self.critical.append(f"[{code}] {critical}")
        mark = "!!" if critical else "OK"
        print(f"  [{mark}] {code} {title}")
        if critical:
            print(f"       -> {critical}")


def fmt_table(rows: list[dict], cols: list[str]) -> str:
    if not rows:
        return "_(해당 없음)_\n"
    head = "| " + " | ".join(cols) + " |"
    sep = "|" + "|".join("---" for _ in cols) + "|"
    body = []
    for r in rows:
        cells = []
        for c in cols:
            v = r.get(c)
            cells.append(f"{v:,}" if isinstance(v, int) else
                         (f"{v:.3f}" if isinstance(v, float) else str(v)))
        body.append("| " + " | ".join(cells) + " |")
    return "\n".join([head, sep, *body]) + "\n"


# ── 개별 점검 ────────────────────────────────────────────────────────────
def i1_yearly(con, rep: Report) -> None:
    rows = con.execute(f"""
        SELECT CAST(year(deal_date) AS INTEGER) AS yr,
               count(*) AS 건수,
               CAST(sum(is_canceled::int) AS INTEGER) AS 해제,
               round(sum(is_canceled::int) * 100.0 / count(*), 2) AS 해제율,
               count(DISTINCT apt_id) AS 단지수,
               count(DISTINCT month(deal_date)) AS 관측월수
        FROM '{TRADE}' GROUP BY 1 ORDER BY 1
    """).df().to_dict("records")

    # 급감이 곧 결함은 아니다. 2022년처럼 시장 전체가 얼어붙으면 거래량이
    # 실제로 1/3 토막 난다. 수집 공백이면 거래가 **특정 월에만** 사라지므로,
    # 월별 편차로 둘을 가른다 — 최저월이 그해 중앙값의 10% 미만이면 공백 의심.
    # 진행 중인 달과 직전 달은 아직 신고가 덜 들어온다 (계약 후 30일 내 신고).
    # 이 둘을 공백으로 잡으면 매일 오탐이 난다.
    today = datetime.now()
    open_months = {(today.year, today.month)}
    pm_y, pm_m = (today.year, today.month - 1) if today.month > 1 else (today.year - 1, 12)
    open_months.add((pm_y, pm_m))

    suspect = []
    for r in rows:
        yr = int(r["yr"])
        m = con.execute(f"""
            SELECT month(deal_date) AS mo, count(*) AS n
            FROM '{TRADE}' WHERE year(deal_date) = {yr}
            GROUP BY 1 ORDER BY 1
        """).df()
        if len(m) < 6:
            continue
        med = float(m["n"].median())
        thin = [int(x) for x, n in zip(m["mo"], m["n"])
                if n < med * 0.1 and (yr, int(x)) not in open_months]
        if thin and med > 0:
            months = ", ".join(f"{x:02d}월" for x in thin)
            suspect.append(f"{yr}년 {months} 거래가 중앙값의 10% 미만 — 수집 공백 의심")

    note = ("\n> 2020년부터 해제율이 0이 아닌 이유: RTMS 가 계약해제 정보를 "
            "2020년부터 공개하기 시작했다. 그 이전 0% 는 결측이지 '해제 없음'이 아니다.\n")
    rep.add("I1", "연도별 분포",
            fmt_table(rows, ["yr", "건수", "해제", "해제율", "단지수"]) + note,
            rows,
            critical=" / ".join(suspect) if suspect else None)


def i2_coverage(con, rep: Report) -> None:
    """raw meta.json 기준 시군구x연월 수집 공백."""
    metas = list((DIRS["raw_trade"]).rglob("*.meta.json"))
    seen: set[tuple[str, str]] = set()
    for p in metas:
        code, ym = p.stem.replace(".meta", "").split("_")
        seen.add((code, ym))

    if not seen:
        rep.add("I2", "수집 커버리지", "_(raw meta 없음 — 점검 불가)_\n", None,
                critical="raw/rtms_trade 에 meta.json 이 없다")
        return

    yms = sorted({ym for _, ym in seen})
    first, last = yms[0], yms[-1]
    expected: list[tuple[str, str]] = []
    y, m = int(first[:4]), int(first[4:])
    while f"{y}{m:02d}" <= last:
        for code in SIGUNGU_CODES:
            expected.append((code, f"{y}{m:02d}"))
        m += 1
        if m > 12:
            y, m = y + 1, 1

    missing = [e for e in expected if e not in seen]
    ratio = 1 - len(missing) / max(len(expected), 1)

    by_sgg: dict[str, int] = {}
    for code, _ in missing:
        by_sgg[code] = by_sgg.get(code, 0) + 1
    worst = sorted(by_sgg.items(), key=lambda x: -x[1])[:10]
    rows = [{"시군구": SIGUNGU_CODES.get(c, c), "코드": c, "누락_월수": n}
            for c, n in worst]

    # 받았는데 0건인 달은 정상이다 (분구 전 신설코드, 거래 없는 군 지역 등).
    # 문제는 "받은 적 없음" — meta 자체가 없는 조합이다.
    empty = 0
    for p in metas:
        try:
            if json.loads(p.read_text(encoding="utf-8")).get("rows", 0) == 0:
                empty += 1
        except Exception:
            pass

    by_year: dict[str, int] = {}
    for _, ym in missing:
        by_year[ym[:4]] = by_year.get(ym[:4], 0) + 1
    year_rows = [{"연도": y, "누락_건": n} for y, n in sorted(by_year.items())]

    body = (f"- 기간: {first} ~ {last}\n"
            f"- 기대: {len(expected):,} (시군구 {len(SIGUNGU_CODES)}개 x 연월)\n"
            f"- 보유: {len(seen):,} (이 중 신고 0건: {empty:,} — 정상)\n"
            f"- **누락: {len(missing):,}** (커버리지 **{ratio * 100:.2f}%**)\n\n"
            f"> 신고 0건으로 받은 달은 공백이 아니다. 분구 전 신설코드나 거래가\n"
            f"> 없는 군 지역이 여기 해당한다. 아래는 **받은 적이 없는** 조합이다.\n"
            f"> 보수: `run_backfill_gaps.py`\n\n"
            "### 연도별 누락\n\n" + fmt_table(year_rows, ["연도", "누락_건"])
            + "\n### 시군구별 누락 상위\n\n"
            + fmt_table(rows, ["시군구", "코드", "누락_월수"]))
    rep.add("I2", "수집 커버리지", body,
            {"coverage": ratio, "missing": len(missing)},
            critical=(f"커버리지 {ratio * 100:.2f}% < {MIN_COVERAGE * 100:.0f}%"
                      if ratio < MIN_COVERAGE else None))


def i3_stage_counts(con, rep: Report) -> None:
    staged = con.execute(f"SELECT count(*) FROM read_parquet('{STAGED}')").fetchone()[0]
    master = con.execute(f"SELECT count(*) FROM '{TRADE}'").fetchone()[0]
    dropped = staged - master
    body = (f"- staged: {staged:,}건\n"
            f"- master: {master:,}건\n"
            f"- 차이: {dropped:,}건 ({dropped / max(staged, 1) * 100:.2f}% — "
            f"step3 중복 제거분)\n")
    rep.add("I3", "단계별 건수 정합", body,
            {"staged": staged, "master": master, "dropped": dropped},
            critical=("master 가 staged 보다 많다 — 중복 유입 의심"
                      if dropped < 0 else None))


def i4_nulls(con, rep: Report) -> None:
    cols = ["apt_id", "deal_date", "deal_amount", "area_m2", "floor",
            "build_year", "legal_dong_code", "sigungu_code", "road_address",
            "apt_name_norm", "price_per_m2"]
    exprs = ", ".join(
        f"round(sum(CASE WHEN {c} IS NULL THEN 1 ELSE 0 END) * 1.0 / count(*), 5) AS \"{c}\""
        for c in cols)
    r = con.execute(f"SELECT {exprs} FROM '{TRADE}'").df().to_dict("records")[0]
    rows = [{"컬럼": k, "결측률": float(v)} for k, v in r.items()]
    bad = [f"{k} {v * 100:.1f}%" for k, v in r.items() if float(v) > MAX_NULL_RATIO]
    rep.add("I4", "핵심 컬럼 결측률", fmt_table(rows, ["컬럼", "결측률"]), r,
            critical=" / ".join(bad) if bad else None)


def i5_duplicates(con, rep: Report) -> None:
    total = con.execute(f"SELECT count(*) FROM '{TRADE}'").fetchone()[0]
    dup = con.execute(f"""
        SELECT count(*) FROM (
            SELECT {DEAL_KEY}, count(*) AS n
            FROM '{TRADE}' GROUP BY {DEAL_KEY} HAVING n > 1
        )
    """).fetchone()[0]
    extra = con.execute(f"""
        SELECT coalesce(sum(n - 1), 0) FROM (
            SELECT {DEAL_KEY}, count(*) AS n
            FROM '{TRADE}' GROUP BY {DEAL_KEY} HAVING n > 1
        )
    """).fetchone()[0]
    ratio = extra / max(total, 1)
    body = (f"- 동일성 키: `{DEAL_KEY}`\n"
            f"- 중복 그룹: {dup:,}개\n"
            f"- 초과 행: {extra:,}건 (전체의 **{ratio * 100:.3f}%**)\n\n"
            f"> 같은 단지·같은 날·같은 금액·같은 면적·같은 층 거래는 현실적으로\n"
            f"> 동일 신고의 중복일 가능성이 높다. T5a 의 `deal_hash` 로 고정할 대상.\n")
    rep.add("I5", "중복 의심", body,
            {"groups": dup, "extra_rows": extra, "ratio": ratio},
            critical=(f"중복 {ratio * 100:.3f}% > {MAX_DUP_RATIO * 100:.1f}%"
                      if ratio > MAX_DUP_RATIO else None))


def i6_outliers(con, rep: Report) -> None:
    r = con.execute(f"""
        SELECT count(*) AS 전체,
               sum(CASE WHEN price_per_m2 < 50 THEN 1 ELSE 0 END) AS 저가이상,
               sum(CASE WHEN price_per_m2 > 20000 THEN 1 ELSE 0 END) AS 고가이상,
               sum(CASE WHEN area_m2 <= 0 OR area_m2 > 500 THEN 1 ELSE 0 END) AS 면적이상,
               sum(CASE WHEN build_year < 1960 OR build_year > year(current_date) + 1
                        THEN 1 ELSE 0 END) AS 준공년이상,
               sum(CASE WHEN floor < -5 OR floor > 90 THEN 1 ELSE 0 END) AS 층이상
        FROM '{TRADE}'
    """).df().to_dict("records")[0]
    total = int(r["전체"])
    rows = [{"항목": k, "건수": int(v),
             "비율": round(int(v) / total * 100, 4)}
            for k, v in r.items() if k != "전체"]
    rep.add("I6", "가격·면적 이상치",
            f"- 전체 {total:,}건 기준\n\n" + fmt_table(rows, ["항목", "건수", "비율"]), r)


def i7_apt_id(con, rep: Report) -> None:
    """apt_id 세대 불일치 — T10a 의 근거."""
    amap = DIRS["master"] / "apt_id_map.parquet"
    if not amap.exists():
        rep.add("I7", "apt_id 일관성", "_(apt_id_map 없음)_\n")
        return
    r = con.execute(f"""
        SELECT (SELECT count(DISTINCT apt_id) FROM '{TRADE}') AS 거래_단지,
               (SELECT count(*) FROM '{amap.as_posix()}') AS 맵_단지,
               (SELECT count(*) FROM '{amap.as_posix()}' m
                 WHERE m.apt_id IN (SELECT apt_id FROM '{TRADE}')) AS 교집합
    """).df().to_dict("records")[0]
    inter = int(r["교집합"])
    body = (f"- trade_events 단지: {int(r['거래_단지']):,}\n"
            f"- apt_id_map 단지: {int(r['맵_단지']):,}\n"
            f"- **교집합: {inter:,}**\n")
    crit = None
    if inter == 0:
        crit = ("apt_id 가 한 건도 겹치지 않는다 — apt_id_map/realestate.db 가 "
                "구버전 해시 체계다 (T10a)")
        body += ("\n> 2026-05-03 `make_legal_dong_code()` 변경(가짜 sha5 -> 실제 umdCd)으로\n"
                 "> 해시 입력이 달라져 좌표·인프라 조인이 전부 끊긴 상태.\n"
                 "> `web/build_index.py` 의 이름·주소 브리지가 임시로 99.5% 를 잇고 있다.\n")
    rep.add("I7", "apt_id 일관성", body, r, critical=crit)


# ── 메인 ─────────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser(description="T5 백필 무결성 검증")
    ap.add_argument("--strict", action="store_true",
                    help="치명 결함이 있으면 exit 1")
    args = ap.parse_args()

    if not Path(TRADE).exists():
        print(f"trade_events 없음: {TRADE}")
        return 1

    ts = datetime.now()
    print(f"\n{'=' * 64}\n  백필 무결성 검증  {ts:%Y-%m-%d %H:%M}\n{'=' * 64}")

    con = duckdb.connect()
    rep = Report()
    for fn in (i1_yearly, i2_coverage, i3_stage_counts,
               i4_nulls, i5_duplicates, i6_outliers, i7_apt_id):
        try:
            fn(con, rep)
        except Exception as e:  # 한 점검 실패가 전체를 막지 않게
            rep.add(fn.__name__[:2].upper(), fn.__name__,
                    f"_(점검 실패: {e})_\n", critical=f"점검 실행 실패: {e}")
    con.close()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = ts.strftime("%Y%m%d")
    md = [f"# 백필 무결성 리포트 — {ts:%Y-%m-%d %H:%M}", "",
          f"- 대상: `master/trade_events.parquet`",
          f"- 치명 결함: **{len(rep.critical)}건**", ""]
    if rep.critical:
        md += ["## 치명 결함", ""] + [f"- {c}" for c in rep.critical] + [""]
    for s in rep.sections:
        md += [f"## {s['code']} {s['title']}", "", s["body"], ""]

    md_path = OUT_DIR / f"integrity_report_{stamp}.md"
    js_path = OUT_DIR / f"integrity_report_{stamp}.json"
    md_path.write_text("\n".join(md), encoding="utf-8")
    js_path.write_text(json.dumps(
        {"generated_at": ts.isoformat(), "critical": rep.critical,
         "sections": [{"code": s["code"], "title": s["title"], "data": s["data"]}
                      for s in rep.sections]},
        ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    print(f"\n{'-' * 64}")
    print(f"  치명 결함 {len(rep.critical)}건")
    print(f"  리포트: {md_path}")
    print(f"          {js_path}")
    print(f"{'=' * 64}\n")

    return 1 if (args.strict and rep.critical) else 0


if __name__ == "__main__":
    sys.exit(main())
