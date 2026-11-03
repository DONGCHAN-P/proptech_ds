"""Register local, hash-scoped pending reviews. Does not send messages."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(ROOT))
from notify import video_decisions as vd

E = ROOT / "video-agent-studio/episodes/newlywed-apartment-picks-20261101"
D = Path(__file__).resolve().parent
N = E / "narration/top20-split-v4/longform-natural-v5-20261104"
W = E / "writer/top20-split-v4/longform-natural-v5-20261104"
REVISION = "top20-split-v4/longform-natural-v5-20261104"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def artifact(path):
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def main():
    receipt = D / "pending_review_decisions.json"
    if receipt.exists():
        print(json.dumps(read(receipt), ensure_ascii=False))
        return
    budget = read(D / "budget_proposal.json")
    manifest = read(N / "narration_manifest.json")
    assert budget["input_characters"] == 3158 and budget["revision_credit_cap"] == 3800
    stamp = datetime.now(timezone.utc).isoformat()
    state = read(E / "state.json")
    vd.write(D / "state_before_revision.json", state)
    script_artifacts = [artifact(W / name) for name in
                        ["script_v5.md", "sentence_mapping.json", "sentence_patches.json", "phonetics.json"]]
    script_artifacts += [artifact(E / "qa/top20-split-v4/longform-natural-v5-20261104/final_report.md")]
    script_gate = vd.create(E.name, "script", "v5 문구 수정안: 채널 목적·2024년 신혼부부 거주 통계의 활용 이유, 일상적인 지하철·장보기 표현, 상계2차 중앙하이츠 낭독 분리. 90문장 중47변경, 순위·가격·조건 보존. 문구 QA critical/required 0; 새 음성·영상 미생성.")
    script_gate.update(artifact_revision=REVISION, artifacts=script_artifacts,
                       generation_authorized=False, upload_authorized=False)
    vd.write(vd.STORE / "decisions" / (script_gate["id"] + ".json"), script_gate)
    budget_artifacts = [artifact(D / "budget_proposal.json"), artifact(N / "narration_manifest.json")]
    budget_artifacts += [artifact(ROOT / c["path"]) for c in manifest["chunks"]]
    budget_artifacts += [artifact(ROOT / "config/video_language.json"), artifact(ROOT / "video-agent-studio/lib/narration_reading.py")]
    budget_gate = vd.create(E.name, "budget", "v5의 변경47문장만 Jun 재생성: 12요청·3,158자, 예상3,158크레딧, 수정여유 포함 최대3,800. 기존2,208과 합계최대6,008로 기존6,500이내. 잔여14,456(11/4 01:13KST조회). 추가결제·충전·초과0, 자동재시도없음. 미변경43문장·CTA2재사용. 2편·업로드·Claude전송제외.")
    budget_gate.update(artifact_revision=REVISION, artifacts=budget_artifacts,
                       required_script_decision_id=script_gate["id"],
                       manifest_sha256=budget["manifest_sha256"], revision_credit_cap=3800,
                       cumulative_max_credits=6008, additional_cash_cap_krw=0,
                       top_up_authorized=False, automatic_retry=False, upload_authorized=False)
    vd.write(vd.STORE / "decisions" / (budget_gate["id"] + ".json"), budget_gate)
    previous_gate_path = vd.STORE / "decisions/f1c59d4d4dca.json"
    previous = read(previous_gate_path)
    if previous["status"] == "pending":
        vd.write(D / "previous_completed_decision.json", previous)
        previous.update(status="revision_requested", revised_at=stamp,
                        revision_source="same_conversation_direct_user_five_point_feedback_20261104",
                        successor_script_decision_id=script_gate["id"],
                        note="새 문구와 발음 수정 요청을 반영한다. 기존 영상·검수 기록은 보존한다.")
        vd.write(previous_gate_path, previous)
    state.update(phase="awaiting_longform_natural_v5_script_and_budget_review",
                 requested_revision=REVISION, updated_at=stamp,
                 active_script_proposal=artifact(W / "script_v5.md")["path"],
                 pending_decision_id=script_gate["id"],
                 pending_decision_ids={"script": script_gate["id"], "budget": budget_gate["id"]},
                 natural_language_revision={
                     "revision": REVISION, "generation_authorized": False,
                     "tts_post_calls": 0, "script_qa_required": 0, "script_qa_critical": 0,
                     "old_main_and_shorts_preserved": True, "reading_replacements": 47,
                     "proposed_credit_cap": 3800, "upload_authorized": False,
                     "actual_listening": False, "continuous_playback": False})
    state["active_approval_status"].update(script="pending:" + script_gate["id"],
                                            budget="pending:" + budget_gate["id"],
                                            completed="revision_requested:longform-natural-v5",
                                            pre_upload="not_reached_longform_natural_v5")
    vd.write(E / "state.json", state)
    history = read(E / "decisions.json")
    history["decisions"].append({"id": "D-NATURAL-V5-20261104", "at": stamp, "revision": REVISION,
                                 "source": "same_conversation_direct_user_five_point_feedback",
                                 "choice": "adopt reviewed v5 as pending script; request exact incremental budget",
                                 "status": "local_work_done_pending_scoped_script_and_budget",
                                 "owner": "director", "script_decision_id": script_gate["id"],
                                 "budget_decision_id": budget_gate["id"], "paid_calls": 0,
                                 "git_checkpoint": "da514555f7e3d5613de61a8d9ba5e830067bfa50"})
    vd.write(E / "decisions.json", history)
    cfg_path = ROOT / "config/video_shelf.json"
    cfg = read(cfg_path)
    entry = next(e for e in cfg["entries"] if e["workspace"].endswith(E.name) and e["name"] == "신혼부부_TOP20_1편")
    entry["status"] = "Jun 본편·UI v2 쇼츠 유지 / v5 표현·발음 수정안 검수 완료 / 새 음성 생성 승인 대기"
    entry["files"].update({
        "대본_v5_수정안.md": artifact(W / "script_v5.md")["path"],
        "표현_발음_수정내역.md": artifact(D / "수정안과생성범위.md")["path"],
        "대본_v5_검수.md": artifact(E / "qa/top20-split-v4/longform-natural-v5-20261104/final_report.md")["path"]})
    vd.write(cfg_path, cfg)
    vd.write(receipt, {"revision": REVISION, "script_decision_id": script_gate["id"],
                       "budget_decision_id": budget_gate["id"], "status": "pending",
                       "created_at": stamp, "messages_sent": 0,
                       "generation_authorized": False, "upload_authorized": False})
    print(json.dumps(read(receipt), ensure_ascii=False))


if __name__ == "__main__":
    main()
