"""영상 설계를 JSON 으로 내보낸다 — 파이썬은 데이터, 렌더는 Remotion.

왜 가르나
    지금은 한 모듈이 숫자도 뽑고 HTML 도 만들고 프레임도 찍는다. 그래서
    움직임을 바꾸려면 쿼리 옆의 좌표를 고쳐야 하고, 프레임 타이밍 같은
    렌더 문제가 분석 코드까지 흔든다. 실제로 25fps 타임베이스 하나 때문에
    영상이 끊겼고, 브라우저 페이지가 눌려 렌더가 통째로 날아갔다.

    **파이썬은 "무엇을 보여 줄지"까지만 정한다.** 어떻게 그리고 어떻게
    움직일지는 Remotion 이 맡는다.

내보내는 것
    장면 목록(길이·내레이션·음성 파일), 장(章), 그리고 각 장면이 쓰는
    **데이터**. 지도의 SVG 가 아니라 핀 좌표를, 차트의 막대 HTML 이 아니라
    행 값을 넘긴다.

실행:
  python analysis/export_video.py            # 전체
  python analysis/export_video.py --voice    # 음성 길이까지 반영
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from analysis import newtown1_video as V  # noqa: E402
from analysis import newtown_charts as NC  # noqa: E402
from analysis import newtown_scenes as SC  # noqa: E402
from content import design as D  # noqa: E402
from content import longvideo as LV  # noqa: E402

OUT = ROOT / "video" / "public" / "plan.json"


def rel(p: Path | str | None) -> str | None:
    """Remotion 의 public/ 기준 상대 경로로."""
    if not p:
        return None
    p = Path(p)
    try:
        return p.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return p.as_posix()


def scene_data() -> dict:
    """움직이는 장면들이 쓰는 숫자. 그림이 아니라 값만 넘긴다."""
    c = NC.con()
    return {
        "flags": SC.load_flags(),
        "flagsAll": SC.load_all_flags(),
        "split": SC.load_split(),
        "cmp": SC.load_compare(),
        "mix": {k: v for k, v in SC.load_mix().items()},
        "movein": SC.load_movein(),
        "bars": {k: NC.rows_level(c) if k == "level"
                 else NC.rows_naive(c) if k == "naive"
                 else NC.rows_same(c) if k == "same"
                 else NC.rows_peak(c)
                 for k in ("level", "naive", "same", "peak")},
        "barSpec": {k: {kk: vv for kk, vv in s.items() if kk != "legend"}
                    for k, s in V.SPEC.items()},
        "counter": SC.COUNTER, "won": SC.WON, "dirs": SC.DIRS,
        "gen1": SC.GEN1, "gangnam": SC.GANGNAM,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="영상 설계 내보내기")
    ap.add_argument("--voice", action="store_true")
    a = ap.parse_args()

    bs = V.beats()
    if a.voice:
        from content import voice as VO
        got = VO.speak([b.text for b in bs], V.VOICE_DIR)
        for b, g in zip(bs, got):
            b.audio, b.adur = g["path"], g["dur"]
    for b in bs:
        b.measure()

    beats = []
    for i, b in enumerate(bs):
        key = (b.visual.split("/", 1)[1]
               if b.visual.startswith("cards/") else None)
        item: dict = {
            "i": i, "dur": round(b.dur, 4), "chapter": b.chapter,
            "text": b.text, "motion": b.motion, "section": b.section,
            "hold": b.hold, "audio": rel(b.audio),
            "adur": round(b.adur, 4),
        }
        if key:
            kind, kw = V._cards[key]
            # 그리는 함수는 넘길 수 없다. 종류와 인자만 넘기고 React 가
            # 같은 이름의 장면을 그린다.
            item["card"] = {"name": key, "kind": kind,
                            "props": {k: v for k, v in kw.items()
                                      if k not in ("html", "n")}}
            if kind == "custom":
                item["card"]["scene"] = V.SCENE_OF.get(key, key)
        else:
            item["asset"] = rel(V.ART / b.visual)
        beats.append(item)

    plan = {
        "fps": LV.FPS, "width": LV.OUT_W, "height": LV.OUT_H,
        "content": {"w": LV.W, "h": LV.H,
                    "x": (LV.OUT_W - LV.W) // 2, "y": 76},
        "subZone": LV.SUB_ZONE, "pad": LV.PAD, "fade": LV.FADE,
        "channel": D.CHANNEL, "series": "신도시 시리즈 · ",
        "source": "국토교통부 실거래가 · 해제 건 제외",
        "chapters": V.CHAPTERS,
        "music": rel(V.MUSIC) if V.MUSIC.exists() else None,
        "beats": beats,
        "data": scene_data(),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(plan, ensure_ascii=False, indent=1,
                              default=str), encoding="utf-8")
    total = sum(b["dur"] for b in beats)
    print(f"  장면 {len(beats)}개 · {int(total // 60)}분 {int(total % 60)}초")
    print(f"  저장 {OUT}  ({OUT.stat().st_size / 1024:.0f}KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
