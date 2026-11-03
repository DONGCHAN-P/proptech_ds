"""Freeze a local revision packet. This script has no network/generation path."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
EP = ROOT / "video-agent-studio/episodes/newlywed-apartment-picks-20261101"
REV = "longform-natural-v5-20261104"
DIRECTOR = Path(__file__).resolve().parent
WRITER = EP / "writer/top20-split-v4" / REV
OLD = EP / "narration/top20-split-v4/jun-and-shorts-v1"
NEW = EP / "narration/top20-split-v4" / REV


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path):
    return path.relative_to(ROOT).as_posix()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    spec = importlib.util.spec_from_file_location(
        "narration_reading", ROOT / "video-agent-studio/lib/narration_reading.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    old = read(OLD / "narration_manifest.json")
    original = {s["sentence_id"]: s for s in old["sentences"]}
    current = read(WRITER / "sentence_mapping.json")["sentences"]
    patches = {p["sentence_id"]: p for p in read(WRITER / "sentence_patches.json")["patches"]}
    timing = read(OLD / "timing_proposals.json")
    old_timing = {s["sentence_id"]: s for s in timing["sentences"]}
    old_chunks = {s["asset_id"]: s for s in timing["chunks"]}
    assert len(current) == 90 and len(patches) == 47
    main_ids = [s["sentence_id"] for s in old["sentences"] if s["kind"] == "accepted_main"]
    assert [s["sentence_id"] for s in current] == main_ids
    changed = []
    reuse = []
    assembly = []
    for sentence in current:
        ident = sentence["sentence_id"]
        source = original[ident]
        reading = module.apply_name_readings(sentence["reading_text"])
        # Writer's reviewed reading already includes the protected-name policy.
        assert reading == sentence["reading_text"], ident
        is_changed = (source["text"], source["reading_text"]) != (sentence["text"], reading)
        assert is_changed == sentence["changed"] == (ident in patches), ident
        if is_changed:
            patch = patches[ident]
            assert (patch["old_text"], patch["old_reading_text"]) == (source["text"], source["reading_text"])
            assert (patch["new_text"], patch["new_reading_text"]) == (sentence["text"], reading)
            changed.append({"sentence_id": ident, "text": sentence["text"], "reading_text": reading,
                            "scene_id": sentence["scene_id"], "main_order": sentence["main_order"]})
        else:
            reuse.append(ident)
        source_timing = old_timing[ident]
        assembly.append({
            "sentence_id": ident,
            "main_order": sentence["main_order"],
            "source": "replacement_pending" if is_changed else "reuse_existing_native_Jun",
            "old_asset_id": source_timing["asset_id"],
            "old_wav": source_timing["wav_path"],
            "old_wav_sha256": old_chunks[source_timing["asset_id"]]["wav_sha256"],
            "old_sentence_local_span_s": [source_timing["chunk_local_start_s"], source_timing["chunk_local_end_s"]],
            "new_span_s": None if is_changed else "preserve_native_source_span_until_assembly",
            "boundary_policy": "inspect_original_silence_and_adjacent_syllables_before_cutting",
        })
    assert len(reuse) == 43
    changed_by_id = {s["sentence_id"]: s for s in changed}
    chunks = []
    for source_chunk in old["chunks"]:
        selected = [changed_by_id[i] for i in source_chunk["sentence_ids"] if i in changed_by_id]
        if not selected:
            continue
        asset_id = "NATV5-" + source_chunk["asset_id"]
        text = "\n\n".join(s["reading_text"] for s in selected)
        path = NEW / "inputs" / (asset_id + ".txt")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        spans = []
        cursor = 0
        for s in selected:
            spans.append({"sentence_id": s["sentence_id"], "start_char": cursor,
                          "end_char": cursor + len(s["reading_text"])})
            cursor += len(s["reading_text"]) + 2
        chunks.append({"asset_id": asset_id, "original_asset_id": source_chunk["asset_id"],
                       "sentence_ids": [s["sentence_id"] for s in selected], "characters": len(text),
                       "path": rel(path), "sha256": sha(path), "sentence_spans": spans})
        for s in selected:
            next(row for row in assembly if row["sentence_id"] == s["sentence_id"])["new_asset_id"] = asset_id
    chars = sum(c["characters"] for c in chunks)
    assert chars == sum(len(s["reading_text"]) for s in changed) + 2 * (len(changed) - len(chunks))
    manifest = {
        "revision": REV, "status": "review_packet_not_generation_authorized", "sentences": changed,
        "chunks": chunks, "main_sentence_count": 90, "replacement_sentence_count": len(changed),
        "reuse_main_sentence_count": len(reuse), "reuse_shared_CTA_count": 2,
        "input_characters_to_send": chars, "planned_requests": len(chunks),
        "script_path": rel(WRITER / "script_v5.md"), "script_sha256": sha(WRITER / "script_v5.md"),
        "sentence_mapping_sha256": sha(WRITER / "sentence_mapping.json"),
        "language_registry_sha256": sha(ROOT / "config/video_language.json"),
        "name_normalizer_path": "video-agent-studio/lib/narration_reading.py",
        "name_normalizer_sha256": sha(ROOT / "video-agent-studio/lib/narration_reading.py"),
        "old_manifest_path": rel(OLD / "narration_manifest.json"),
        "old_manifest_sha256": sha(OLD / "narration_manifest.json"),
        "voice_id": "4p6UA7mnodF5q7JFFrnW", "model": "eleven_v4",
        "voice_settings": {"stability": 0.6, "similarity_boost": 0.95, "style": 1,
                           "speed": 0.97, "use_speaker_boost": True},
        "generation_authorized": False, "tts_post_calls": 0, "automatic_retry": False,
        "cash_cap_krw": 0, "top_up_authorized": False,
    }
    write(NEW / "narration_manifest.json", manifest)
    account = read(NEW / "account_readonly.json")
    cap = math.ceil(chars * 1.2 / 100) * 100
    assert 2208 + cap <= 6500
    budget = {
        "revision": REV, "status": "proposed_not_approved", "input_characters": chars,
        "changed_sentence_characters": sum(len(s["reading_text"]) for s in changed),
        "paragraph_separator_characters": chars - sum(len(s["reading_text"]) for s in changed),
        "planned_requests": len(chunks), "conservative_credits_per_character": 1,
        "first_pass_estimated_credits": chars, "revision_credit_cap": cap,
        "manual_revision_reserve_proposed": cap - chars,
        "old_actual_credits": 2208, "old_cap": 6500, "cumulative_max_credits": 2208 + cap,
        "included_remaining_at_readonly_check": account["subscription"]["included_remaining"],
        "account_check_at_utc": account["checked_at_utc"], "account_evidence": rel(NEW / "account_readonly.json"),
        "additional_cash_cap_krw": 0, "top_up_authorized": False,
        "overage_authorized": False, "automatic_retry": False,
        "old_approval_covers_new_manifest": False, "generation_authorized": False,
        "manifest_path": rel(NEW / "narration_manifest.json"),
        "manifest_sha256": sha(NEW / "narration_manifest.json"),
        "scope": "part1 changed47 only; unchanged43 and sharedCTA2 reuse; noPart2/noUpload",
    }
    write(DIRECTOR / "budget_proposal.json", budget)
    short_impacts = []
    for path in sorted((EP / "director/top20-split-v4/shorts-ui-v2-20261104/shorts").glob("*/locked_timing.json")):
        data = read(path)
        ids = [s["sentence_id"] for s in data["sentences"]]
        affected = [i for i in ids if i in changed_by_id]
        short_impacts.append({"short_id": data["short_id"], "current_timing": rel(path),
                              "current_timing_sha256": sha(path), "sentence_ids": ids,
                              "changed_sentence_ids": affected,
                              "voice_edit_needed": bool(affected), "render_edit_needed": bool(affected),
                              "current_mp4_modified": False})
    write(DIRECTOR / "shorts_impact_current_ui_v2.json", {"basis": "current_UI_v2_locks_not_old_plan", "shorts": short_impacts})
    write(DIRECTOR / "voice_assembly_plan.json", {
        "status": "plan_pending_approval_actual_new_voice_and_timing",
        "main_sequence": assembly, "reuse_main_sentence_ids": reuse,
        "reuse_shared_CTA_sentence_ids": [s["sentence_id"] for s in old["sentences"] if s["kind"] != "accepted_main"],
        "timing_policy": "new_provider_alignment_and_actual_PCM_then_relock_all_downstream_offsets",
        "tempo_scaling": False, "old_timeline_used_as_new_timing": False,
        "listening_targets": ["channel_name", "sanggye_second_jungang_heights", "all_replaced_sentence_boundaries"],
        "screen_targets": ["intro_statistics_rationale", "replaced_display_text", "caption_semantic_units", "numeric_reveal_anchors"],
        "actual_listening": False, "continuous_playback": False, "generation_calls": 0,
    })
    write(DIRECTOR / "input_preflight.json", {
        "status": "local_input_packet_passed_not_audio_verified", "changed_sentences": len(changed),
        "reused_main": len(reuse), "requests": len(chunks), "api_input_characters": chars,
        "protected_name_normalizer_applied": True, "writer_readings_changed_by_normalizer": 0,
        "all_chunk_hashes_match": all(sha(ROOT / c["path"]) == c["sha256"] for c in chunks),
        "old_bad_protected_reading_in_new_inputs": any("상계이 차중앙하이츠" in s["reading_text"] for s in changed),
        "actual_listening": False, "tts_post_calls": 0,
    })
    print(json.dumps({"changed": len(changed), "reused": len(reuse), "requests": len(chunks),
                      "characters": chars, "proposed_cap": cap, "cumulative_cap": 2208 + cap,
                      "short_impacts": [{"id": s["short_id"], "changed_ids": s["changed_sentence_ids"]} for s in short_impacts]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
