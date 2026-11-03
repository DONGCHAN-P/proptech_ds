"""Freeze an encoded-QA plan; never approve or render media."""
from pathlib import Path
import hashlib
import json
import math
import re
import shutil
from datetime import datetime, timezone

QA = Path(__file__).resolve().parent
EP = QA.parent.parent
ROOT = EP.parents[2]


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, value):
    (QA / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def artifact(path):
    return {"path": path.as_posix(), "sha256": sha(path)}


stamp = datetime.now(timezone.utc).isoformat()
source_path = QA / "source_approval_v4.json"
source = read(source_path)
prod = EP / "outputs/private-production-v1"
release = EP / "outputs/private-release-v2"
edl_path = prod / "assembly_edl.json"
srt_path = prod / "captions_measured.srt"
timing_path = EP / "narration/production-injoon-v3/final_timing.json"
lock_path = EP / "director/production-v1/locked_script.json"
lock = read(lock_path)
script_path = ROOT / lock["script_path"]
edl, timing = read(edl_path), read(timing_path)
video = prod / "renders/measured-v3-visual-v4-r1/affordable_home_price_private_voice_v3_visual_v4.mp4"
assert source["approved"] and not source["required"] and not source["critical"]
assert not video.exists(), "Preparation only: actual MP4 now exists; start an evidence-based review instead."
assert sha(script_path) == lock["script_sha256"] == edl["script_sha256"] == timing["script_sha256"]
assert sha(timing_path) == source["checked_revision"]["timing_sha256"] == edl["timing_sha256"]
assert sha(edl_path) == source["checked_revision"]["edl_sha256"]
for frozen in source["immutable_inputs"]:
    assert sha(Path(frozen["path"])) == frozen["sha256"], frozen["path"]

fps = edl["fps"]
total_frames = round(edl["total_seconds"] * fps)
assert fps == 30 and len(edl["segments"]) == 13
scenes, cues, current_html = [], [], []
for entry in source["postcarve_HTML"]:
    path = Path(entry["path"])
    assert sha(path) == entry["postcarve_html_sha256"], path
    current_html.append(artifact(path))
    match = re.search(r"const SCENES=(.*?);const CUES=(.*?);const BEATS=(.*?);", path.read_text(encoding="utf-8"), re.S)
    scene_rows, cue_rows, _ = map(json.loads, match.groups())
    for row in cue_rows:
        row["chapter"] = entry["chapter"]
    scenes.extend(scene_rows)
    cues.extend(cue_rows)
native = {cue["id"]: cue for ch in timing["chapters"] for cue in ch["cues"]}
assert len(scenes) == 45 and len(cues) == len(native) == 150
for cue in cues:
    for key in ("start_s", "end_s", "display_lines"):
        assert cue[key] == native[cue["id"]][key], (cue["id"], key)


def global_time(chapter, local, side="right"):
    options = [seg for seg in edl["segments"] if seg.get("chapter") == chapter
               and seg["source_start_s"] - 1e-8 <= local <= seg["source_end_s"] + 1e-8]
    assert options, (chapter, local)
    # At the cut CH01's right side belongs after the inserted intro.
    seg = options[-1] if side == "right" else options[0]
    return seg["global_start_s"] + local - seg["source_start_s"]


samples = {}


def add(time_s, category, item_id, check, full_resolution=False):
    frame = max(0, min(total_frames - 1, math.floor(time_s * fps + 0.5)))
    sample = samples.setdefault(frame, {"frame_index": frame, "expected_pts_s": frame / fps,
                                        "full_resolution": False, "targets": []})
    sample["full_resolution"] |= full_resolution
    sample["targets"].append({"category": category, "id": item_id, "requested_s": time_s, "check": check})
    return frame


def boundary(time_s, category, item_id, check, full_resolution=False):
    return [add(time_s + delta / fps, category, item_id + f":{delta:+d}f", check, full_resolution)
            for delta in (-1, 0, 1)]


scene_plan = []
for scene in scenes:
    ch = scene["chapter"]
    start = global_time(ch, scene["clip_start_s"], "right")
    end = global_time(ch, scene["clip_end_s"], "left")
    speech_mid = (max(scene["start_s"], scene["clip_start_s"]) + min(scene["end_s"], scene["clip_end_s"])) / 2
    rep = add(global_time(ch, speech_mid), "scene_representative", scene["scene_id"],
              "실제 영상의 의미·수치·도형·출처·제목·글리프·가독성; 소스 증거와 비교", True)
    boundary(start, "scene_start", scene["scene_id"], "장면 전환·이전 패널 잔류·빈 프레임·잘림")
    boundary(end, "scene_end", scene["scene_id"], "장면 끝과 다음 카드/장면의 연결")
    scene_plan.append({"scene_id": scene["scene_id"], "chapter": ch, "global_visual_start_s": start,
                       "global_visual_end_s": end, "representative_frame": rep,
                       "message": scene["message"], "claim_ids": scene["claim_ids"]})

glyph_rows = {row["cue_id"]: row for row in read(QA / "caption_glyph_review.json")["rows"]}
max_text = sorted(cues, key=lambda cue: max(line["width"] for line in glyph_rows[cue["id"]]["lines"]), reverse=True)[:10]
long_ids = {cue["id"] for cue in max_text}
critical_ids = {"S016", "S018", "S031", "S034R", "S040"}
caption_plan = []
for cue in cues:
    start = global_time(cue["chapter"], cue["start_s"])
    end = global_time(cue["chapter"], cue["end_s"])
    critical = cue["scene_id"] in critical_ids
    rep = add((start + end) / 2, "caption_midpoint", cue["id"],
              "실제로 번인된 의미단위 자막·줄바꿈·수치·글리프·배경상자; SRT 및 고정 display_lines와 대조", critical or cue["id"] in long_ids)
    caption_plan.append({"cue_id": cue["id"], "scene_id": cue["scene_id"], "chapter": cue["chapter"],
                         "global_start_s": start, "global_end_s": end, "representative_frame": rep,
                         "display_lines": cue["display_lines"], "max_text_top10": cue["id"] in long_ids})
    if cue["id"] in long_ids or critical:
        boundary(start, "critical_or_maxtext_caption_start", cue["id"], "실제 자막 등장·포커스·출처/패널 잘림", True)
        boundary(end, "critical_or_maxtext_caption_end", cue["id"], "실제 자막 종료·다음 큐 포커스 및 공백", True)

join_plan = []
for left, right in zip(edl["segments"], edl["segments"][1:]):
    assert abs(left["global_end_s"] - right["global_start_s"]) < 1e-8
    when = right["global_start_s"]
    join_plan.append({"left": left["id"], "right": right["id"], "global_s": when,
                      "frames": boundary(when, "EDL_join", left["id"] + "/" + right["id"],
                                         "접합부 잔상·자막·검정/정지 프레임; 음성 기술 지표는 별도 통합 QA와 대조", True)})

chapter_plan = []
for ch in timing["chapters"]:
    number = ch["chapter"]
    chapter_plan.append({"chapter": number, "title": ch["title"],
                         "frame": add(global_time(number, 1.75), "chapter_title", f"CH{number:02}",
                                      "장 제목/배경·풋터 가독성; 반복·정지·검정 화면 여부", True)})

for scene in scenes:
    if scene["scene_id"] in critical_ids:
        for delta in (0.1, 0.35):
            add(global_time(scene["chapter"], scene["clip_start_s"] + delta), "critical_panel_entry", scene["scene_id"],
                "S016/S018 열린 축 경로 검은 삼각형 없음; S031 상품별 시계; S034R 재설정 조건; S040 포커스/하단 글리프", True)

intro = next(seg for seg in edl["segments"] if seg["id"] == "clean_brand_intro")
outro = next(seg for seg in edl["segments"] if seg["id"] == "clean_brand_outro")
for seg in (intro, outro):
    for ratio in (0.1, 0.5, 0.9):
        add(seg["global_start_s"] + (seg["global_end_s"] - seg["global_start_s"]) * ratio,
            "clean_brand", seg["id"], "승인 브랜딩·자막 상자/이전 본문 오버레이 없음", True)
add(intro["global_end_s"], "post_intro", "S002_visual_anticipation", "28.033333초 첫 본문 프레임 S002; S001 복귀 없음; 음성/자막은 원래 시각 유지", True)
first_s002 = next(cue for cue in caption_plan if cue["scene_id"] == "S002")
boundary(first_s002["global_start_s"], "post_intro_native_caption", first_s002["cue_id"], "S002 첫 native 자막 전에 빈 캡션 상자 없음", True)
for hidden in edl["caption_hidden_intervals"]:
    add((hidden["start_s"] + hidden["end_s"]) / 2, "caption_hidden_interval", hidden.get("reason", "hidden"),
        "브랜드/무음 CTA 구간 자막과 흰 배경상자 모두 숨김", True)
boundary(edl["last_voice_global_end_s"], "CTA_last_voice", "CTA", "마지막 실제 자막 종료·CTA 여유·브랜드 전환", True)
add(total_frames / fps - 1 / fps, "last_frame", "outro_end", "정상 마지막 인코딩 프레임", True)

artifacts = {"script": artifact(script_path), "script_lock": artifact(lock_path), "subtitles": artifact(srt_path),
             "timing": artifact(timing_path), "edl": artifact(edl_path), "source_approval": artifact(source_path),
             "metadata": artifact(release / "metadata_measured.json"),
             "description": artifact(release / "description_measured.md"), "thumbnail": artifact(release / "thumbnail.png")}
assert read(release / "metadata_measured.json")["edl_sha256"] == artifacts["edl"]["sha256"]
audio_gate_path = EP / "qa/audio-v1/audio_gate_v3.json"
render_auth_path = EP / "director/production-v1/render_authorization_v1.json"
audio_consolidation = None
if audio_gate_path.exists():
    gate, auth = read(audio_gate_path), read(render_auth_path)
    assert gate["approved"] and not gate["required_issues"] and not gate["critical_issues"]
    assert gate["script_sha256"] == auth["script_sha256"] == artifacts["script"]["sha256"]
    assert gate["final_timing_sha256"] == auth["timing_sha256"] == artifacts["timing"]["sha256"]
    assert auth["approved"] and auth["edl_sha256"] == artifacts["edl"]["sha256"]
    assert auth["captions_sha256"] == artifacts["subtitles"]["sha256"]
    assert auth["evidence"]["audio_qa"]["sha256"] == sha(audio_gate_path)
    assert auth["evidence"]["source_qa"]["sha256"] == artifacts["source_approval"]["sha256"]
    pins = [row["audio"] for row in gate["all10_current_chapter_audio_pins"]]
    pins += [row["audio"] for row in gate["new4"]]
    pins += [gate[key] for key in ("per_amount_component_proof", "independent_review",
                                 "prior_Whisper_v3_review_preserved", "new4_and_reuse41_manifest")]
    for pin in pins:
        assert sha(Path(pin["path"])) == pin["sha256"], pin["path"]
    audio_consolidation = {"status": "provided_exact_ASR_gate_consolidated_not_heard", "approved": True,
                           "approval_scope": gate["approval_scope"], "at_utc": stamp,
                           "receipt": artifact(audio_gate_path), "render_authorization": artifact(render_auth_path),
                           "validated_input_and_evidence_pins": pins,
                           "required_issues": [], "critical_issues": [],
                           "new_ASR_runs": 0, "actual_listening": False, "continuous_playback": False,
                           "naturalness_approved": False, "final_mix_approved": False, "encoded_video_approved": False,
                           "basis": "Kant 기존 Whisper + 신규4 ASR + 독립 무프롬프트 Vosk 성분 증거 및 재사용41 SHA 범위. 최종 믹스는 별도 실제 MP4 기술 검수 예정."}
    write("audio_gate_consolidation_v3.json", audio_consolidation)
    artifacts["audio_gate_consolidation"] = artifact(QA / "audio_gate_consolidation_v3.json")
    artifacts["audio_gate"] = artifact(audio_gate_path)
    artifacts["render_authorization"] = artifact(render_auth_path)
    for name in ("final_review.json", "final_encoded_qa_prep_handoff.json", "encoded_sampling_plan_v4.json"):
        old, preserved = QA / name, QA / (Path(name).stem + ".pre_audio_gate.json")
        if old.exists() and not preserved.exists():
            shutil.copyfile(old, preserved)
plan = {"status": "prepared_not_executed", "prepared_at_utc": stamp, "planned_video_path": video.as_posix(),
        "video_exists_at_preparation": False, "expected_fps": fps, "expected_dimensions": [1920, 1080],
        "expected_total_frames": total_frames, "expected_seconds": edl["total_seconds"], "artifacts": artifacts,
        "postcarve_HTML": current_html, "scene_representatives": scene_plan, "caption_representatives": caption_plan,
        "chapters": chapter_plan, "EDL_joins": join_plan, "max_text_cue_ids": [cue["id"] for cue in max_text],
        "critical_full_resolution_scenes": sorted(critical_ids), "samples": sorted(samples.values(), key=lambda row: row["frame_index"]),
        "counts": {"scenes": len(scene_plan), "caption_midpoints": len(caption_plan), "chapters": len(chapter_plan),
                   "EDL_joins": len(join_plan), "unique_planned_frames": len(samples)},
        "execution_contract": [
            "실제 MP4 SHA256/ffprobe 스트림·PTS·프레임수·해상도·음성 트랙·끝 시각을 먼저 기록한다.",
            "현재 입력/10 HTML SHA와 실제 렌더 manifest를 대조한다. 다른 버전이면 영향 범위를 재계획한다.",
            "연속 디코딩 frame index와 실제 PTS를 기록한다. seek 파일명만으로 경계 프레임 일치를 단정하지 않는다.",
            "실제 45장면 및 150큐 표본·접합부·중요 장면 원본 해상도 증거를 본 후 결과와 미확인 범위를 기록한다.",
            "통합 최종 음성 QA의 정확한 경로/SHA/판정/청취 범위를 인계받아 영상의 실제 오디오와 연결한다.",
            "메타데이터/설명/썸네일의 내용·버전·타임스탬프·조건 표시를 실제 최종 패키지로 검수한다.",
            "required/critical 미해결 0 및 모든 의존 게이트 증거가 있을 때에만 최종 approved를 true로 쓴다.",
            "샘플 프레임 검수와 연속 재생/실제 청취를 구분한다. 현재 둘 다 미실시다."
        ]}
write("encoded_sampling_plan_v4.json", plan)

review = {"status": "prepared_pending_actual_render_and_encoded_QA" if audio_consolidation else "prepared_pending_actual_render_evidence_and_consolidated_audio_QA", "approved": False,
          "video_sha256": None, "subtitles_sha256": artifacts["subtitles"]["sha256"],
          "script_sha256": artifacts["script"]["sha256"], "metadata_sha256": artifacts["metadata"]["sha256"],
          "description_sha256": artifacts["description"]["sha256"], "thumbnail_sha256": artifacts["thumbnail"]["sha256"],
          "required_issues": [], "critical_issues": [], "burned_in_captions_verified": False,
          "prepared_at_utc": stamp, "planned_video_path": video.as_posix(),
          "pending_gates": ["actual_render_and_provenance", "actual_encoded_frame_evidence_and_review",
                            "encoded_audio_technical_and_provenance_checks", "final_release_package_content_review"]
                           + ([] if audio_consolidation else ["consolidated_final_audio_QA"]),
          "issues_note": "빈 이슈 배열은 확인된 인코딩 결함이 아직 없다는 뜻이며 검수 통과를 뜻하지 않는다.",
          "coverage": {"stage": "preparation_only", "actual_video_opened": False, "encoded_frames_reviewed": 0,
                       "encoded_scenes_reviewed": 0, "encoded_caption_midpoints_reviewed": 0, "EDL_joins_reviewed": 0,
                       "continuous_playback": False, "actual_listening": False, "sampled_review_only": True,
                       "planned": plan["counts"], "inherited_source_approval": artifacts["source_approval"],
                       "inherited_scope": "visual-v4 exact postcarve10HTML 소스만 승인; 인코딩 증거 아님",
                       "release_package_visual_content_reviewed": False,
                       "audio_QA_receipt": audio_gate_path.as_posix() if audio_consolidation else None,
                       "audio_QA_receipt_sha256": sha(audio_gate_path) if audio_consolidation else None,
                       "audio_QA_scope": audio_consolidation["approval_scope"] if audio_consolidation else "pending",
                       "audio_ASR_gate_consolidated": bool(audio_consolidation), "encoded_audio_technical_checks_completed": False,
                       "evidence_manifest": None, "evidence_manifest_sha256": None},
          "artifacts": artifacts, "sampling_plan": artifact(QA / "encoded_sampling_plan_v4.json"),
          "approval_scope": "준비본. 미디어·음성·게시 승인 없음. 불변 금융/정책 내용은 소스 승인 근거 재사용."}
write("final_review.json", review)
handoff = {"status": "final_encoded_QA_prepared_waiting_for_actual_evidence", "owner": "video_qa / qa/source-media-v1",
           "approved": False, "source_v4_approval_preserved": True,
           "audio_ASR_gate_consolidated": bool(audio_consolidation),
           "audio_gate_consolidation": artifacts.get("audio_gate_consolidation"),
           "final_review": artifact(QA / "final_review.json"), "sampling_plan": artifact(QA / "encoded_sampling_plan_v4.json"),
           "counts": plan["counts"], "waiting_for": review["pending_gates"],
           "next": "실제 렌더 완료 영수증·증거를 받으면 해당 MP4 SHA에 연결하여 표본 및 최종 오디오 기술 검수. 통합 ASR 게이트는 연결 완료. 원본 영수증 보존." if audio_consolidation else "실제 렌더·증거·통합 음성 QA를 받아 해당 MP4 SHA에 연결하여 표본 검수.",
           "actual_listening": False, "continuous_playback": False}
write("final_encoded_qa_prep_handoff.json", handoff)
print(json.dumps({"status": handoff["status"], "counts": plan["counts"], "audio_ASR_gate_consolidated": bool(audio_consolidation),
                  "output_files": ["final_review.json", "encoded_sampling_plan_v4.json", "final_encoded_qa_prep_handoff.json"]}, ensure_ascii=False))
