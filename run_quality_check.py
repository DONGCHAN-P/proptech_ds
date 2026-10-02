"""
run_quality_check.py — 데이터 품질 8종 sanity 검사 + Slack 알림

검사 항목:
  Q1  unified_apt_pyeong_daily.parquet 존재 여부
  Q2  최신 deal_date가 D-3 이내 (stale data 감지)
  Q3  행 수 임계값 이상 (shrinkage 감지)
  Q4  핵심 컬럼 NaN 비율 10% 이하
  Q5  가격 이상치 비율 1% 이하 (price_per_m2 < 50 or > 20000 만원/㎡)
  Q6  단지 수 전일 대비 -5% 이상 감소 감지
  Q7  trade_events.parquet 행 수 급감 감지
  Q8  파일 크기 급감 (전일 대비 -20% 이하)

실행:
  python run_quality_check.py            # 검사 후 결과 출력 + (Slack 설정 시) 알림
  python run_quality_check.py --strict   # 실패 항목 있으면 exit code 1
"""
import sys
import json
import argparse
import traceback
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import BASE, DIRS, load_secrets

BASELINE_FILE = DIRS["logs"] / "quality_baseline.json"
LOG_FILE      = DIRS["logs"] / "quality_check_log.jsonl"

# ── 임계값 ────────────────────────────────────────────────────────────────
MIN_ROWS        = 50_000       # unified 최소 행 수
MAX_NAN_RATIO   = 0.10         # 핵심 컬럼 NaN 허용 비율
PRICE_LOW       = 50           # 만원/㎡ 하한
PRICE_HIGH      = 20_000       # 만원/㎡ 상한
MAX_PRICE_RATIO = 0.01         # 이상치 비율 상한
APT_SHRINK      = 0.05         # 단지 수 감소 허용 비율
TRADE_SHRINK    = 0.10         # 거래 수 감소 허용 비율
FILE_SHRINK     = 0.20         # 파일 크기 감소 허용 비율
STALE_DAYS      = 3            # 최신 거래일 허용 지연 (영업일 기준 최대)

KEY_COLS = ["trade_last_per_m2", "area_m2_key", "apt_id", "trade_last_date"]


# ── 결과 클래스 ─────────────────────────────────────────────────────────
class CheckResult:
    def __init__(self, code: str, name: str):
        self.code    = code
        self.name    = name
        self.passed  = True
        self.message = ""
        self.detail  = {}

    def fail(self, msg: str, **detail):
        self.passed  = False
        self.message = msg
        self.detail  = detail
        return self

    def ok(self, msg: str = "", **detail):
        self.message = msg
        self.detail  = detail
        return self

    def __str__(self):
        icon = "✅" if self.passed else "❌"
        return f"{icon} [{self.code}] {self.name}: {self.message}"


# ── 개별 검사 함수 ──────────────────────────────────────────────────────
def q1_file_exists() -> CheckResult:
    r = CheckResult("Q1", "파일 존재 여부")
    p = DIRS["master"] / "unified_apt_pyeong_daily.parquet"
    if not p.exists():
        return r.fail("unified_apt_pyeong_daily.parquet 없음")
    age = datetime.now().timestamp() - p.stat().st_mtime
    age_h = age / 3600
    return r.ok(f"파일 존재 (최종수정 {age_h:.1f}시간 전, {p.stat().st_size/1e6:.1f}MB)",
                size_mb=round(p.stat().st_size/1e6, 2), age_hours=round(age_h, 1))


def q2_staleness(df: pd.DataFrame) -> CheckResult:
    r = CheckResult("Q2", "최신 거래일 staleness")
    # unified는 trade_last_date, trade_events는 deal_date
    col = next((c for c in ["trade_last_date", "deal_date", "snapshot_date"]
                if c in df.columns), None)
    if col is None:
        return r.fail("날짜 컬럼 없음 (trade_last_date / deal_date 중 하나 필요)")
    max_date = pd.to_datetime(df[col]).max()
    gap = (datetime.now() - max_date).days
    threshold = STALE_DAYS + 60   # 공표 시차 + 여유 60일
    if gap > threshold:
        return r.fail(f"최신 {col} {max_date.date()} — {gap}일 이전 (임계: {threshold}일)",
                      col=col, max_date=str(max_date.date()), gap_days=gap)
    return r.ok(f"최신 {col} {max_date.date()} ({gap}일 전)",
                col=col, max_date=str(max_date.date()), gap_days=gap)


def q3_row_count(df: pd.DataFrame) -> CheckResult:
    r = CheckResult("Q3", "행 수 임계값")
    n = len(df)
    if n < MIN_ROWS:
        return r.fail(f"행 수 {n:,} < 임계값 {MIN_ROWS:,}", rows=n)
    return r.ok(f"{n:,}행", rows=n)


def q4_nan_ratio(df: pd.DataFrame) -> CheckResult:
    r = CheckResult("Q4", "핵심 컬럼 NaN 비율")
    issues = {}
    for col in KEY_COLS:
        if col not in df.columns:
            issues[col] = "컬럼없음"
            continue
        ratio = df[col].isna().mean()
        if ratio > MAX_NAN_RATIO:
            issues[col] = f"{ratio:.1%}"
    if issues:
        return r.fail(f"NaN 초과: {issues}", nan_details=issues)
    nans = {c: round(float(df[c].isna().mean()), 4) for c in KEY_COLS if c in df.columns}
    return r.ok("모든 핵심 컬럼 정상", nan_ratios=nans)


def q5_price_outlier(df: pd.DataFrame) -> CheckResult:
    r = CheckResult("Q5", "가격 이상치 비율")
    # 컬럼 후보 순서대로 탐색
    col = next((c for c in ["trade_last_per_m2", "trade_90d_avg_per_m2", "price_per_m2"]
                if c in df.columns), None)
    if col is None:
        return r.fail("가격/㎡ 컬럼 없음")
    series  = df[col].dropna()
    outlier = series.lt(PRICE_LOW) | series.gt(PRICE_HIGH)
    ratio   = outlier.mean()
    cnt     = int(outlier.sum())
    if ratio > MAX_PRICE_RATIO:
        return r.fail(f"이상치 {ratio:.2%} ({cnt:,}건) > 허용 {MAX_PRICE_RATIO:.0%} [{col}]",
                      col=col, ratio=round(float(ratio), 4), count=cnt)
    return r.ok(f"이상치 {ratio:.3%} ({cnt:,}건) [{col}]",
                col=col, ratio=round(float(ratio), 4), count=cnt)


def q6_apt_shrinkage(df: pd.DataFrame, baseline: dict) -> CheckResult:
    r = CheckResult("Q6", "단지 수 급감")
    if "apt_id" not in df.columns:
        return r.fail("apt_id 컬럼 없음")
    cur = df["apt_id"].nunique()
    prev = baseline.get("apt_count", cur)
    if prev > 0 and (cur - prev) / prev < -APT_SHRINK:
        return r.fail(f"단지 수 {prev:,} → {cur:,} ({(cur-prev)/prev:+.1%})",
                      cur=cur, prev=prev)
    return r.ok(f"단지 {cur:,}개 (전일 {prev:,})", cur=cur, prev=prev)


def q7_trade_shrinkage(baseline: dict) -> CheckResult:
    r = CheckResult("Q7", "거래 수 급감 (trade_events)")
    p = DIRS["master"] / "trade_events.parquet"
    if not p.exists():
        return r.fail("trade_events.parquet 없음")
    cur  = pd.read_parquet(p, columns=["apt_id"]).shape[0]
    prev = baseline.get("trade_count", cur)
    if prev > 0 and (cur - prev) / prev < -TRADE_SHRINK:
        return r.fail(f"거래 수 {prev:,} → {cur:,} ({(cur-prev)/prev:+.1%})",
                      cur=cur, prev=prev)
    return r.ok(f"거래 {cur:,}건 (전일 {prev:,})", cur=cur, prev=prev)


def q8_file_size(baseline: dict) -> CheckResult:
    r = CheckResult("Q8", "파일 크기 급감")
    p = DIRS["master"] / "unified_apt_pyeong_daily.parquet"
    if not p.exists():
        return r.fail("파일 없음")
    cur  = p.stat().st_size
    prev = baseline.get("unified_size_bytes", cur)
    if prev > 0 and (cur - prev) / prev < -FILE_SHRINK:
        return r.fail(f"크기 {prev/1e6:.1f}MB → {cur/1e6:.1f}MB ({(cur-prev)/prev:+.1%})",
                      cur=cur, prev=prev)
    return r.ok(f"{cur/1e6:.1f}MB (전일 {prev/1e6:.1f}MB)", cur=cur, prev=prev)


# ── Slack 알림 ───────────────────────────────────────────────────────────
def send_slack(webhook: str, results: list[CheckResult], run_ts: str):
    try:
        import urllib.request
        failed = [r for r in results if not r.passed]
        if not failed:
            color = "good"
            title = f"✅ 품질 검사 전체 통과 ({run_ts})"
            text  = "\n".join(f"• {r}" for r in results)
        else:
            color = "danger"
            title = f"❌ 품질 검사 {len(failed)}건 실패 ({run_ts})"
            text  = "\n".join(f"• {r}" for r in results)

        payload = json.dumps({
            "attachments": [{
                "color": color,
                "title": title,
                "text": text,
                "footer": "Real Estate AVM · quality_check",
            }]
        }, ensure_ascii=False).encode()

        req = urllib.request.Request(
            webhook,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                print("  [Slack] 알림 전송 완료")
            else:
                print(f"  [Slack] 응답 비정상: {resp.status}")
    except Exception as e:
        print(f"  [Slack] 알림 실패: {e}")


# ── 베이스라인 저장/로드 ─────────────────────────────────────────────────
def load_baseline() -> dict:
    if BASELINE_FILE.exists():
        return json.loads(BASELINE_FILE.read_text(encoding="utf-8"))
    return {}


def save_baseline(df: pd.DataFrame):
    DIRS["logs"].mkdir(parents=True, exist_ok=True)
    p_unified = DIRS["master"] / "unified_apt_pyeong_daily.parquet"
    p_trade   = DIRS["master"] / "trade_events.parquet"
    data = {
        "saved_at":          datetime.now().isoformat(),
        "apt_count":         int(df["apt_id"].nunique()) if "apt_id" in df.columns else 0,
        "row_count":         len(df),
        "unified_size_bytes": int(p_unified.stat().st_size) if p_unified.exists() else 0,
        "trade_count":       pd.read_parquet(p_trade, columns=["apt_id"]).shape[0]
                             if p_trade.exists() else 0,
    }
    BASELINE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ── 메인 ────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="데이터 품질 8종 sanity 검사")
    parser.add_argument("--strict", action="store_true",
                        help="실패 항목 있으면 exit code 1 반환 (CI/CD용)")
    parser.add_argument("--no-slack", action="store_true",
                        help="Slack 알림 스킵")
    parser.add_argument("--update-baseline", action="store_true",
                        help="베이스라인 갱신만 하고 종료")
    args = parser.parse_args()

    run_ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"\n{'='*60}")
    print(f"  데이터 품질 검사  {run_ts}")
    print(f"{'='*60}\n")

    DIRS["logs"].mkdir(parents=True, exist_ok=True)
    secrets  = load_secrets()
    baseline = load_baseline()
    results  = []

    # Q1: 파일 존재
    r1 = q1_file_exists()
    results.append(r1)
    print(r1)

    # 파일 없으면 나머지 검사 불가
    if not r1.passed:
        _finish(results, baseline, secrets, args, run_ts)
        return

    # 데이터 로드
    try:
        df = pd.read_parquet(DIRS["master"] / "unified_apt_pyeong_daily.parquet")
    except Exception as e:
        print(f"  [오류] parquet 로드 실패: {e}")
        results.append(CheckResult("Q?", "데이터 로드").fail(str(e)))
        _finish(results, baseline, secrets, args, run_ts)
        return

    if args.update_baseline:
        save_baseline(df)
        print(f"\n베이스라인 저장 완료 ({BASELINE_FILE})")
        return

    # Q2~Q8
    for fn, extra in [
        (q2_staleness,      (df,)),
        (q3_row_count,      (df,)),
        (q4_nan_ratio,      (df,)),
        (q5_price_outlier,  (df,)),
        (q6_apt_shrinkage,  (df, baseline)),
        (q7_trade_shrinkage,(baseline,)),
        (q8_file_size,      (baseline,)),
    ]:
        try:
            r = fn(*extra)
        except Exception as e:
            r = CheckResult(fn.__name__, fn.__name__).fail(f"예외: {e}")
        results.append(r)
        print(r)

    _finish(results, baseline, secrets, args, run_ts, df)


def _finish(results, baseline, secrets, args, run_ts, df=None):
    failed  = [r for r in results if not r.passed]
    passed  = len(results) - len(failed)
    n_total = len(results)

    print(f"\n{'─'*60}")
    print(f"  결과: {passed}/{n_total} 통과  |  실패: {len(failed)}건")
    if failed:
        print("  실패 항목:")
        for r in failed:
            print(f"    → [{r.code}] {r.message}")

    # 로그 저장
    log_entry = {
        "ts": run_ts,
        "passed": passed,
        "failed": len(failed),
        "checks": [
            {"code": r.code, "name": r.name, "ok": r.passed,
             "msg": r.message, **r.detail}
            for r in results
        ],
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    print(f"  로그: {LOG_FILE}")

    # 베이스라인 갱신 (통과 시)
    if not failed and df is not None:
        save_baseline(df)
        print(f"  베이스라인 갱신: {BASELINE_FILE}")

    # Slack 알림
    webhook = secrets.get("slack_webhook", "").strip()
    if webhook and not args.no_slack:
        send_slack(webhook, results, run_ts)
    elif not webhook:
        print("  [Slack] webhook 미설정 — 알림 스킵 (config/secrets.json의 slack_webhook 설정 필요)")

    print(f"{'='*60}\n")

    if args.strict and failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
