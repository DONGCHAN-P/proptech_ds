"""Validate the authored scaffold, not the upstream research or any media."""
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

own = Path(__file__).resolve().parent
ep = own.parents[1]
p = json.loads((own / "scene_proposals_v6.json").read_text(encoding="utf-8"))
top = json.loads((ep / "research/top20-8min-v2/top20.json").read_text(encoding="utf-8-sig"))
script = (own / "script_v6.md").read_text(encoding="utf-8")
checks = []


def check(name, ok, detail):
    checks.append({"check": name, "result": "pass" if ok else "fail", "detail": detail})


regions = [s for s in p["scenes"] if s["region_id"]]
all_sentences = [x for s in p["scenes"] for x in s["sentences"]]
filled = [x for x in all_sentences if x["text"] is not None]
pending = [x for x in all_sentences if x["text"] is None]
check("20개 지역ID와 기존 장면ID 유지", {s["region_id"] for s in regions} == {r["region_id"] for r in top["regions"]} and all(any(s["region_id"] == r["region_id"] and s["scene_id"] == r["scene_id"] for s in regions) for r in top["regions"]), "R01..R20 / S003..S022")
check("20위부터1위 순서", [s["rank"] for s in regions] == list(range(20, 0, -1)), [s["rank"] for s in regions])
check("입력 거주 수 보존", all(f"{r['newlywed_couples']:,}쌍" in next(s for s in regions if s["region_id"] == r["region_id"])["sentences"][0]["text"] for r in top["regions"]), "20개 지역의 새 첫 문장을 지정 top20.json과 대조")
check("문장ID 유일", len({x["sentence_id"] for x in all_sentences}) == len(all_sentences), len(all_sentences))
fields = {"sentence_id", "text", "claim_ids", "statement_type", "display_notes", "reading_notes", "onscreen_purpose", "anchor_string", "display_text", "reading_text"}
check("문장별 필수 필드", all(fields <= set(x) for x in all_sentences), sorted(fields))
check("작성된 문장과 읽기문의 평서문", all(x["text"].endswith("다.") and x["reading_text"].endswith("다.") and not re.search(r"(?:요[.!?]|까[.!?]|[?？])", x["text"] + x["reading_text"]) for x in filled), "요체·의문형·수사의문문 없음")
check("각 문장 앵커가 실제 문구에 존재", all(x["anchor_string"] in x["text"] for x in filled), "시간 앵커가 아닌 문자열 앵커")
check("내레이션·표시문의 claim_id 해소", all(cid in p["claim_registry"] for x in filled for cid in x["claim_ids"]), "상위 검증 원고/입력 참조 또는 통계 정의에 연결")
used = {cid for x in filled for cid in x["claim_ids"]}
check("qualified 사실을 확정 문장으로 미사용", all(p["claim_registry"][cid].get("status") != "qualified" for cid in used), "기존 검증 상태를 재사용; 원문 재검수 아님")
check("61개 대기 슬롯을 낭독문과 분리", len(pending) == 61 and all(x["reading_text"] is None and x["anchor_string"] is None and x["claim_ids"] == [] and x["narration_ready"] is False for x in pending) and all(s["narration_text"] is None for s in p["scenes"] if s["pending_sentence_ids"]), "지역 특징20·지역 중위가격20·대표단지가격20·도입 가격기간1")
check("20지역 설명·가격 슬롯 순서", all([x.get("slot_kind") for x in s["sentences"] if x["text"] is None] == ["regional_feature", "region_price_median", "representative_complex_price"] for s in regions), "거주 수→특징→랜드마크→지역 중위값→단지 가격")
check("20지역 실제 장소의 기존 검증 근거", all(any(x["statement_type"] == "verified_fact" and any(re.fullmatch(r"R\d{2}-F\d+", cid) for cid in x["claim_ids"]) for x in s["sentences"]) for s in regions), "사진 픽셀 검수·사용허락은 별도 미실시")
check("Stats 출처는 도입부에만", all("통계청" not in x["text"] for s in p["scenes"] if s["scene_id"] != "O002" for x in s["sentences"] if x["text"]), "지도의 원출처는 통합 크레딧/설명란과 내부 원장에 유지")
check("2024 한계와 가격기간 분리", p["price_window"] is None and any(x.get("slot_kind") == "price_period" for x in next(s for s in p["scenes"] if s["scene_id"] == "O002")["sentences"]) and "현재의 순위로 읽을 수는 없습니다" in script, "5~10월은 후보일 뿐 확정 기간으로 쓰지 않음")
check("미확인 가격·좌표 필드 미기입", all(x["text"] is None for s in regions for x in s["sentences"] if x.get("slot_kind") in ["region_price_median", "representative_complex_price"]), "가격 금액·단지명·좌표는 최종 패킷 대기")
check("추정과 실측시간 분리", 780 <= p["total_estimated_duration_s"] <= 960 and p["actual_duration_s"] is None and not p["timing_locked"] and all(s["start_s"] is None and s["end_s"] is None and s["actual_duration_s"] is None for s in p["scenes"]), {"producer_allocation_estimate_s": p["total_estimated_duration_s"], "audio_measured": False})
check("초기초안 상태 및 합성 금지", p["status"] == "INITIAL_SCAFFOLD_NOT_FINAL" and not p["narration_ready"] and "최종 대본이 아니며" in script, "최종 요구 완수/승인/TTS 준비로 표시하지 않음")
check("마크다운과 장면표의 작성문 일치", all(f"**[{x['sentence_id']}]** {x['text']}" in script for x in filled), "문장 누락·별도 재작성 없음")
check("고정 입력 SHA 보존", all(hashlib.sha256((ep / path).read_bytes()).hexdigest() == v["sha256"] for path, v in p["input_versions"].items()), "입력 불변 확인만; 소스팩 자체의 독립 검수 재수행 아님")

failed = [x["check"] for x in checks if x["result"] == "fail"]
report = {"status": "scaffold_checks_passed" if not failed else "failed", "created_at": datetime.now().astimezone().isoformat(), "check_scope": "새 대본·장면표의 구조/수치전달/문체/대기슬롯/시간표기 검사. upstream 원문·가격·좌표·독립QA·음성·프레임 검수 아님.", "checks": checks, "failed": failed, "summary": {"regions": len(regions), "scenes": len(p["scenes"]), "written_sentences": len(filled), "pending_slots": len(pending)}, "actual_listening_performed": False, "continuous_playback_performed": False, "render_or_tts_performed": False, "output_sha256": {name: hashlib.sha256((own / name).read_bytes()).hexdigest() for name in ["script_v6.md", "scene_proposals_v6.json"]}}
(own / "verification_v6.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"status": report["status"], "checks": len(checks), "failed": failed, **report["summary"]}, ensure_ascii=False))
raise SystemExit(1 if failed else 0)
