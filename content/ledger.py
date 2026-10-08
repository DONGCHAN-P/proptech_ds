"""발행 원장 — 무엇을 **실제로 올렸는지** (T20b).

왜 따로 두나
    `cover_log.json` 은 **고른 기록**이다. 캐러셀을 돌릴 때마다 쌓인다.
    봇이 생기면서 고른 것과 올린 것이 갈라졌다 — 하루에 영상을 셋 만들어도
    올리는 건 하나다. 고른 기록으로 "2주 연속 같은 지역 금지"를 판단하면,
    만들기만 하고 버린 지역이 다음 주를 막는다.

    그리고 수동 업로드라서, **올렸다는 사실은 사람만 안다.** 알려줄 통로가
    없으면 시스템은 영영 모른다. 봇의 /done 이 그 통로다.

여기 쌓인 것이 중복 방지의 근거가 된다 (cover.recent_regions).

    published  올렸다        → 그 지역은 다음 회차 표지에서 뺀다
    skipped    안 올렸다     → 막지 않는다. 다시 권해도 된다
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# output/ 은 git 에서 빠져 있다. 지표는 raw/ 에서 다시 만들 수 있지만
# "무엇을 올렸나"는 되살릴 길이 없다 — 사람 머릿속에만 있던 사실이다.
# 버전 관리되는 자리에 둔다.
LOG = ROOT / "config" / "publish_log.json"

PUBLISHED = "published"
SKIPPED = "skipped"


def rows() -> list[dict]:
    """원장 전체. 깨져 있으면 빈 목록 — 읽다 멈추면 발행이 막힌다."""
    try:
        out = json.loads(LOG.read_text(encoding="utf-8"))
        return out if isinstance(out, list) else []
    except Exception:
        return []


def record(asof: str, info: dict, status: str = PUBLISHED,
           platforms: list[str] | None = None, note: str = "") -> dict:
    """한 줄 남긴다. 같은 회차·같은 단지면 **덮어쓴다**.

    /done 을 두 번 눌렀다고 두 줄이 되면 "몇 번 올렸나"가 틀어진다.
    """
    entry = {
        "at": datetime.now().isoformat(timespec="seconds"),
        "asof": asof,
        "status": status,
        "key": info.get("key") or "",
        "apt_name": info.get("apt_name") or "",
        "region": info.get("region") or "",
        "pyeong": info.get("pyeong") or "",
        "platforms": platforms or [],
        "note": note,
    }
    cur = [r for r in rows()
           if not (r.get("asof") == asof and r.get("key") == entry["key"])]
    cur.append(entry)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.write_text(json.dumps(cur, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    return entry


def published(n: int = 2) -> list[dict]:
    """최근 n개 회차에서 **올린** 것만. 회차(asof) 기준으로 센다."""
    done = [r for r in rows() if r.get("status") == PUBLISHED]
    if not done:
        return []
    weeks = sorted({r.get("asof") for r in done if r.get("asof")})[-n:]
    return [r for r in done if r.get("asof") in weeks]


def regions(n: int = 2, exclude_asof: str | None = None) -> set[str]:
    """최근 n개 회차에 올린 지역.

    exclude_asof 는 이번 회차다. 안 빼면 오늘 올린 걸 기록한 뒤 다시 고를 때
    자기 자신이 걸려서 다른 지역이 나온다.
    """
    out = [r for r in published(n + 1) if r.get("asof") != exclude_asof]
    weeks = sorted({r["asof"] for r in out})[-n:]
    return {r["region"] for r in out if r["asof"] in weeks and r.get("region")}


def recent(n: int = 10) -> list[dict]:
    return rows()[-n:]


def has_any() -> bool:
    """원장이 쓰이기 시작했나. 비어 있으면 옛 기록(cover_log)으로 돌아간다."""
    return bool(rows())
