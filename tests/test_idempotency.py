"""T7 — 일일 증분 수집 멱등성 검증.

"두 번 돌려도 같은 결과"가 지켜지는지 본다. 깨지면 매일 돌 때마다 중복이
쌓이거나 행이 사라진다.

API 를 두드리는 수집 단계는 여기서 다루지 않는다 (호출 한도·네트워크 의존).
대신 수집 이후 결정론 구간 — staged 재생성과 trade_events 빌드 — 을 본다.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from common import DIRS  # noqa: E402

TRADE = DIRS["master"] / "trade_events.parquet"
PY = ROOT / ".venv" / "Scripts" / "python.exe"


@pytest.fixture(scope="module")
def trades() -> pd.DataFrame:
    if not TRADE.exists():
        pytest.skip("trade_events.parquet 없음")
    return pd.read_parquet(TRADE, columns=[
        "deal_hash", "apt_id", "deal_date", "deal_amount", "area_m2", "floor",
        "first_seen_date", "first_seen_is_estimate"])


# ── 결과물 자체의 멱등 조건 ──────────────────────────────────────────────
def test_deal_hash가_유일하다(trades):
    """재수집 upsert 의 기준키. 중복이 있으면 멱등성이 성립하지 않는다."""
    dup = len(trades) - trades["deal_hash"].nunique()
    assert dup == 0, f"deal_hash 중복 {dup:,}건 — upsert 기준키로 못 쓴다"


def test_first_seen_원장이_거래와_일대일(trades):
    ledger = DIRS["master"] / "deal_first_seen.parquet"
    if not ledger.exists():
        pytest.skip("원장 없음")
    led = pd.read_parquet(ledger)
    assert led["deal_hash"].is_unique, "원장에 deal_hash 중복"
    미등록 = (~trades["deal_hash"].isin(set(led["deal_hash"]))).sum()
    assert 미등록 == 0, f"원장에 없는 거래 {미등록:,}건"


def test_원장은_거래보다_작아지지_않는다(trades):
    """해제·정정으로 거래가 빠져도 원장은 이력이라 남아야 한다."""
    ledger = DIRS["master"] / "deal_first_seen.parquet"
    if not ledger.exists():
        pytest.skip("원장 없음")
    led = pd.read_parquet(ledger)
    assert len(led) >= trades["deal_hash"].nunique()


def test_staged_버전표식이_모두_같다():
    """CODE_VERSION 이 섞여 있으면 일부만 구버전 로직으로 만들어진 것이다."""
    vers = {p.read_text().strip()
            for p in DIRS["staged_trade"].rglob("*.parquet.ver")}
    assert len(vers) <= 1, f"staged 에 버전이 섞여 있다: {sorted(vers)}"


def test_staged_가_master보다_오래되지_않았다():
    """master 가 staged 보다 먼저 만들어졌으면 반영이 안 된 것이다."""
    if not TRADE.exists():
        pytest.skip("master 없음")
    newest = max((p.stat().st_mtime
                  for p in DIRS["staged_trade"].rglob("*.parquet")), default=0)
    assert TRADE.stat().st_mtime >= newest - 1, (
        "staged 가 trade_events 보다 최신이다 — step3 를 다시 돌려야 한다")


# ── 실제 재실행 (느림) ───────────────────────────────────────────────────
@pytest.mark.slow
def test_step2_재실행시_신규0건():
    """step2 를 다시 돌려도 새로 만들어지는 staged 가 없어야 한다."""
    r = subprocess.run([str(PY), str(ROOT / "run_step2.py"), "--skip-map"],
                       capture_output=True, text=True, encoding="utf-8",
                       env={"PYTHONIOENCODING": "utf-8", "PATH": ""},
                       cwd=str(ROOT), timeout=3600)
    assert r.returncode == 0, r.stderr[-500:]
    line = [l for l in r.stdout.splitlines() if "정제 완료" in l]
    assert line, f"정제 완료 줄 없음: {r.stdout[-300:]}"
    # "정제 완료: OK=0, SKIP=21000, 신규 행=0건"
    ok = int(line[-1].split("OK=")[1].split(",")[0])
    assert ok == 0, f"2회차에 {ok:,}개 파일이 다시 만들어졌다 — 멱등성 깨짐"
