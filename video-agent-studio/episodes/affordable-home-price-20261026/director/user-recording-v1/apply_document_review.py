"""Apply the bounded r1 document findings while retaining the user manuscript."""
from pathlib import Path
import hashlib
import json

PACK = Path(__file__).resolve().parent


def main():
    path = PACK / "scene_plan.json"
    plan = json.loads(path.read_text(encoding="utf-8"))
    assert hashlib.sha256(path.read_bytes()).hexdigest() == "8ba157a2e873c05ddef4bfc1318283c3a3a3260d87ce3d611e408f6721c5fdab"
    by_id = {s["scene_id"]: s for s in plan["scenes"]}

    def beat(anchor, action):
        return {"anchor": anchor, "action": action, "start": None, "end": None}

    def replace(sid, old_anchor, new):
        s = by_id[sid]
        i = next(i for i, b in enumerate(s["beats"]) if b["anchor"] == old_anchor)
        s["beats"][i:i + 1] = [beat(a, b) for a, b in new]

    replace("S07", "5억이면 6천만 원", [
        ("3억이면 4천만 원", "3억−4000만원→집값 투입2억6000만원"),
        ("4억이면 5천만 원", "4억−5000만원→집값 투입3억5000만원"),
        ("5억이면 6천만 원", "5억−6000만원→집값 투입4억4000만원"),
    ])
    replace("S22", "5억 원은", [
        ("3억 원은", "현금3억의 LTV70%6.6억↔40%4.33억 관측점"),
        ("4억 원은", "현금4억의 LTV70%7.5억↔40%5.83억 관측점"),
        ("5억 원은", "현금5억의 LTV70%8.4억↔40%7.33억 관측점"),
    ])
    replace("S27", "5억 원이면", [
        ("4억 원이면", "넷째 행 집값7.5억·자기자금3.5억·대출4억"),
        ("5억 원이면", "다섯째 행 집값8.4억·자기자금4.4억·대출4억"),
    ])
    by_id["S06"]["beats"].append(beat("항목별로 견적", "금액을 채우지 않은 항목별 견적칸을 연결"))
    by_id["S11"]["scope_label"] = "일반 무주택자·처분조건부1주택자의 주택구입 기준; 생애최초 별도"
    for b in by_id["S11"]["beats"]:
        if b["anchor"] in {"비규제지역은 70퍼센트", "규제지역은 40퍼센트"}:
            b["action"] += "; 무주택자·처분조건부1주택자 주택구입 표제 유지"
    for s in plan["scenes"]:
        for b in s["beats"]:
            assert b["anchor"] in s["narration_text"], (s["scene_id"], b["anchor"])
    count = sum(len(s["beats"]) for s in plan["scenes"])
    assert count == 101
    plan["design_revision"] = "user-recording-guide-v1-r2"
    plan["literal_anchor_count"] = count
    path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    recording = PACK / "녹음용_문단표.md"
    lines = recording.read_text(encoding="utf-8").splitlines()
    sid = None
    for i, line in enumerate(lines):
        if line.startswith("### S"):
            sid = line.split(" · ", 1)[0][4:]
        if line.startswith("[화면이 반응할 말]"):
            lines[i] = "[화면이 반응할 말] " + " / ".join(b["anchor"] for b in by_id[sid]["beats"])
    recording.write_text("\n".join(lines) + "\n", encoding="utf-8")
    changes = {"status": "applied_pending_independent_delta_review", "source_manuscript_changed": False, "timing_still_unmeasured": True, "changes": {"URV1-R01": "Guide definition changed to equity+loan; reserve outside price.", "URV1-R02": "P029 optional rewrite explicitly remains a hypothetical no-additional-constraint case.", "URV1-R03": "S07/S22/S27 add5 separate original-script anchors; each5억 action now only5억.", "URV1-C01": "S06 adds exact P017 quotation anchor and blank item-level estimate states.", "URV1-C02": "Guide and S11 preserve original eligible borrower scope."}, "literal_anchor_count": count}
    (PACK / "review_changes_r2.json").write_text(json.dumps(changes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "changes_applied", "anchors": count, "user_manuscript_changed": False}, ensure_ascii=False))


if __name__ == "__main__":
    main()
