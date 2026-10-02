"""
run_review_queue.py — 신규 단지 월별 검수 큐 생성

현재 apt_id_map과 이전 달 스냅샷을 비교해서
신규로 발견된 단지 목록을 exports/review/ 에 저장.

사람 검수 포인트:
  - 단지명이 이상하거나 중복된 단지
  - 법정동 매핑이 없는 단지
  - 좌표 없는 단지 (지오코딩 필요)
  - 거래량이 갑자기 급증한 단지

실행:
  python run_review_queue.py            # 오늘 기준
  python run_review_queue.py --notify   # Slack 알림 포함
"""
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import BASE, DIRS, load_secrets

REVIEW_DIR   = BASE / "exports" / "review"
SNAPSHOT_DIR = DIRS["logs"] / "apt_map_snapshots"
APT_MAP      = DIRS["master"] / "apt_id_map.parquet"


def load_apt_map() -> pd.DataFrame:
    if not APT_MAP.exists():
        raise FileNotFoundError(f"apt_id_map.parquet 없음: {APT_MAP}")
    return pd.read_parquet(APT_MAP)


def load_prev_snapshot(today_ym: str) -> set[str]:
    """직전 달 apt_id 스냅샷 로드. 없으면 빈 set 반환."""
    yr  = int(today_ym[:4])
    mo  = int(today_ym[4:])
    if mo == 1:
        prev_ym = f"{yr-1}12"
    else:
        prev_ym = f"{yr}{mo-1:02d}"

    snap = SNAPSHOT_DIR / f"apt_ids_{prev_ym}.json"
    if not snap.exists():
        print(f"  직전 스냅샷 없음 ({snap.name}) — 전체를 신규로 간주")
        return set()
    return set(json.loads(snap.read_text(encoding="utf-8")))


def save_snapshot(today_ym: str, apt_ids: set[str]):
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    snap = SNAPSHOT_DIR / f"apt_ids_{today_ym}.json"
    snap.write_text(json.dumps(sorted(apt_ids), ensure_ascii=False), encoding="utf-8")
    print(f"  스냅샷 저장: {snap.name} ({len(apt_ids):,}개 단지)")


def build_review_queue(df: pd.DataFrame, new_ids: set[str]) -> pd.DataFrame:
    """신규 단지 DataFrame + 검수 플래그 부착."""
    new_df = df[df["apt_id"].isin(new_ids)].copy()

    # 검수 플래그
    new_df["flag_no_coord"] = (
        new_df.get("lat", pd.Series([None]*len(new_df))).isna() |
        new_df.get("lon", pd.Series([None]*len(new_df))).isna()
    )
    name_col = "apt_name_raw" if "apt_name_raw" in new_df.columns else "apt_name_norm"
    new_df["flag_suspect_name"] = (
        new_df[name_col].str.contains(r"\d{3,}", regex=True, na=False) |
        new_df[name_col].str.len().lt(2)
    )
    new_df["flag_no_legal_dong"] = (
        new_df.get("legal_dong_code", pd.Series([""] * len(new_df))).fillna("").str.endswith("_NA")
    )
    new_df["review_priority"] = (
        new_df["flag_no_coord"].astype(int) * 3 +
        new_df["flag_suspect_name"].astype(int) * 2 +
        new_df["flag_no_legal_dong"].astype(int)
    )
    return new_df.sort_values("review_priority", ascending=False)


def send_slack_notify(webhook: str, today_ym: str, n_new: int, n_flagged: int):
    try:
        import urllib.request
        text = (
            f"📋 *신규 단지 검수 큐 ({today_ym})*\n"
            f"• 신규 단지: {n_new:,}개\n"
            f"• 검수 필요: {n_flagged:,}개 (좌표없음·이름이상·법정동누락)\n"
            f"• 파일: exports/review/new_apts_{today_ym}.csv"
        )
        payload = json.dumps({"text": text}, ensure_ascii=False).encode()
        req = urllib.request.Request(webhook, data=payload,
                                     headers={"Content-Type": "application/json"},
                                     method="POST")
        with urllib.request.urlopen(req, timeout=10):
            print("  [Slack] 알림 전송 완료")
    except Exception as e:
        print(f"  [Slack] 알림 실패: {e}")


def main():
    parser = argparse.ArgumentParser(description="신규 단지 검수 큐 생성")
    parser.add_argument("--notify", action="store_true", help="Slack 알림")
    args = parser.parse_args()

    today_ym = datetime.now().strftime("%Y%m")
    ts       = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*55}")
    print(f"  신규 단지 검수 큐 생성  {ts}")
    print(f"{'='*55}\n")

    # 현재 단지 목록
    df = load_apt_map()
    cur_ids = set(df["apt_id"].dropna().unique())
    print(f"  현재 apt_id_map: {len(cur_ids):,}개 단지")

    # 이전 달 스냅샷과 비교
    prev_ids = load_prev_snapshot(today_ym)
    new_ids  = cur_ids - prev_ids
    print(f"  직전 스냅샷:     {len(prev_ids):,}개 단지")
    print(f"  신규 단지:       {len(new_ids):,}개")

    # 검수 큐 생성
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    if new_ids:
        review_df = build_review_queue(df, new_ids)
        n_flagged = int((review_df["review_priority"] > 0).sum())

        out_path = REVIEW_DIR / f"new_apts_{today_ym}.csv"
        review_df.to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"\n  검수 필요 단지:  {n_flagged:,}개 (플래그 있음)")
        print(f"  저장:            {out_path}")

        # 우선순위 높은 10개 출력
        if n_flagged > 0:
            print("\n  [우선 검수 대상 (상위 10개)]")
            name_col = "apt_name_raw" if "apt_name_raw" in review_df.columns else "apt_name_norm"
            cols = ["apt_id", name_col, "sigungu_code",
                    "flag_no_coord", "flag_suspect_name", "flag_no_legal_dong"]
            cols = [c for c in cols if c in review_df.columns]
            print(review_df[review_df["review_priority"] > 0][cols].head(10).to_string(index=False))

        # Slack 알림
        if args.notify:
            secrets = load_secrets()
            webhook = secrets.get("slack_webhook", "").strip()
            if webhook:
                send_slack_notify(webhook, today_ym, len(new_ids), n_flagged)
            else:
                print("  [Slack] webhook 미설정")
    else:
        print("\n  신규 단지 없음")

    # 현재 달 스냅샷 저장 (다음 달 비교용)
    save_snapshot(today_ym, cur_ids)

    print(f"\n{'='*55}\n")


if __name__ == "__main__":
    main()
