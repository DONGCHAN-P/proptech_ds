"""Check final writer text against the current parent lock, not raw-source QA."""
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

own = Path(__file__).resolve().parent
ep = own.parents[1]
read = lambda path: json.loads(path.read_text(encoding="utf-8-sig"))
p = read(own / "scene_proposals_v6.json")
panel = read(ep / "director/top20-explain-v3/price_panel_data.json")
top = read(ep / "research/top20-8min-v2/top20.json")
features = read(ep / "research/top20-explain-v3/regions/facts.json")
script = (own / "script_v6.md").read_text(encoding="utf-8")
allx = [x for s in p["scenes"] for x in s["sentences"]]
regions = [s for s in p["scenes"] if s["region_id"]]
checks = []


def check(name, ok, detail):
    checks.append({"check": name, "result": "pass" if ok else "fail", "detail": detail})


check("20개 지역/장면ID와20→1 순서", len(regions) == 20 and [s["rank"] for s in regions] == list(range(20, 0, -1)) and all(any(s["scene_id"] == r["scene_id"] and s["region_id"] == r["region_id"] for s in regions) for r in top["regions"]), "R01..R20 / S003..S022")
check("2024 거주 수 원값 보존", all(f"{r['newlywed_couples']:,}쌍" in next(s for s in regions if s["region_id"] == r["region_id"])["sentences"][0]["text"] for r in top["regions"]), "지정 top20.json과 대조")
check("문장ID 유일/대기슬롯0", len({x["sentence_id"] for x in allx}) == len(allx) and all(isinstance(x["text"], str) and x["text"] for x in allx) and not any(s["pending_sentence_ids"] for s in p["scenes"]), len(allx))
required = {"sentence_id", "text", "claim_ids", "statement_type", "display_text", "reading_text", "display_notes", "reading_notes", "onscreen_purpose", "anchor_string", "screen_switch_id"}
check("문장별 필수 자료연결 필드", all(required <= set(x) for x in allx), sorted(required))
check("문체·질문형 제거", all(x["text"].endswith("다.") and x["reading_text"].endswith("다.") and not re.search(r"요[.!?]|까[.!?]|[?？]", x["text"]) for x in allx), "합니다체 평서문")
check("claim 해소/qualified 확정문 미사용", all(c in p["claim_registry"] and p["claim_registry"][c].get("status") != "qualified" for x in allx for c in x["claim_ids"]), "리서치 제한된 검증 범위 승계")
check("20지역 특징2~3문장", all(2 <= len(s["regional_explanation_sentence_ids"]) <= 3 for s in regions) and all(any(c.startswith("V3-" + s["region_id"] + "-H") for x in s["sentences"] for c in x["claim_ids"]) for s in regions), "주거 형성/생활권+실제 장소")
check("최종 사진명세20곳 정확 승계", all(next(r for r in features["regions"] if r["region_id"] == s["region_id"])["photo"]["sha256"] == s["photo_binding"]["sha256"] for s in regions), "새 픽셀검수·새 파일해시 계산 아님;명세 기록 대조")
check("가격 v2만 사용/총14303유효행", p["price_input_lock"]["revision"] == "final-api-20261103-v2" and sum(s["price_panel_data"]["n"] for s in regions) == 14303, "부모 XML독립 재집계 근거 승계;writer는 패널/전달값 대조")
price_errors = []
for s in regions:
    r = next(r for r in panel["regions"] if r["region_id"] == s["region_id"])
    a = r["representative"]
    x = next(x for x in s["sentences"] if x.get("price_role") == "region_price_median")
    y = next(x for x in s["sentences"] if x.get("price_role") == "representative_complex_price")
    if not (r["display_price"] in x["text"] and f"{r['n']:,}건" in x["text"] and a["display_price"] in y["text"] and f"{a['n']:,}건" in y["text"] and a["apt_name"] in y["text"] and a["legal_dong_name"] in y["text"] and r == s["price_panel_data"]):
        price_errors.append(s["region_id"])
check("20지역/20단지 정확표시·n·동명", not price_errors, price_errors)
def price_beat(s):
    return next(b for b in s["screen_beats"] if b["purpose"] == "separate_complex_price_example")
check("가격 전환 두 단계와n 지도표시", all(any(b["purpose"] == "regional_price" for b in s["screen_beats"]) and price_beat(s)["region_n"] == s["price_panel_data"]["n"] and price_beat(s)["complex_n"] == s["price_panel_data"]["representative"]["n"] for s in regions), "지역가격→별도 단지사례")
check("화면 전환ID 모두 해소", all(x["screen_switch_id"] in {b["screen_switch_id"] for b in s["screen_beats"]} for s in p["scenes"] for x in s["sentences"]), "초 단위 타임록 아님")
check("문장 앵커 원문 일치", all(x["anchor_string"] in x["text"] for x in allx), "실제 문자열 연결")
check("기관명 정정/지역 반복푸터 없음", any("국가데이터처가 발표한 2024년 신혼부부통계" in x["text"] for x in allx) and all("통계청" not in x["text"] for x in allx), "발표기관 도입1회;내부 과거출처 메타데이터는 보존")
check("2024 설명·혼인5년기준·2026 가격연도 분리", any(x["sentence_id"] == "O002-02" and "혼인신고 후 5년이 지나지 않은 부부" in x["text"] for x in allx) and any("당시의 분포를 출발점" in x["text"] for x in allx) and any("2026년 5월부터 10월까지" in x["text"] and "2026년 11월 3일" in x["text"] for x in allx), "대상기준 짧게 유지;부정회피 대신 직접 설명")
check("10월 신고 진행 도입1회", len([x for x in allx if "신고가 진행 중" in x["text"]]) == 1 and any(x["sentence_id"].startswith("O002") and "신고가 진행 중" in x["text"] for x in allx), "지역별 반복 낭독 없음")
check("필터/정상행 보존방법 정확", p["price_input_lock"]["methodology"]["paired_original_removed_n"] == 0 and p["price_input_lock"]["methodology"]["area_filter"] == "83<=exclusive_m2<=85; 양끝 포함" and "전체 층·중개+직거래" in next(s for s in p["scenes"] if s["scene_id"] == "O002")["screen_beats"][1]["on_screen_conditions"], "표시 해제행만 제외;음성에서 덜어낸 조건은 화면/내부근거 유지")
check("생활권 분리/확정좌표 승계", all(not s["map_requirements"]["landmark_complex_same_place_assumption_allowed"] and s["map_requirements"]["complex_neighborhood_label_required"] and price_beat(s)["coordinate_status"] == "verified" for s in regions), "원래 사진을 가격단지 전경으로 자동 연결하지 않음")
r20 = next(s for s in regions if s["region_id"] == "R20")
check("R20 공원 지도/상동 거리사진 분리", any("부천중앙공원" in x["text"] and x["material_type"] == "map" for x in r20["sentences"]) and "상동 도시 가로" in r20["screen_beats"][2]["action"], "기존 검증 공원문장 유지")
check("R18·R08 권역 구분", "서로 다른 생활권" in next(s for s in regions if s["region_id"] == "R18")["narration_text"] and "어느 권역" in next(s for s in regions if s["region_id"] == "R08")["narration_text"], "동백/구성 및 문래/여의도 구분")
check("신내2015사진에현재노선합성금지", next(s for s in regions if s["region_id"] == "R19")["screen_beats"][2]["current_operating_lines_overlay_allowed"] is False, "리서치 편집주의 반영")
check("추정·실제시간 분리/8분초과조건", p["duration_target_is_provisional"] and p["required_actual_duration_s_greater_than"] == 480 and p["actual_duration_s"] is None and not p["timing_locked"] and all(s["start_s"] is None and s["end_s"] is None for s in p["scenes"]), "13~16분은 잠정목표;실제음성 우선")
check("새 승인 대기/TTS·렌더 금지", p["status"] == "COMPLETE_SCRIPT_DRAFT_AWAITING_NEW_USER_APPROVAL" and not p["script_gate"]["tts_allowed"] and not p["script_gate"]["main_render_allowed"] and not p["narration_ready"], "현재 권한은 기획/자료/대본 보강")
check("MD 작성문 전체 일치", all(f"**[{x['sentence_id']}]** {x['text']}" in script for x in allx) and "가격의 실제 계약기간과 조회일은 미확정" not in script and "lock을 기다립니다" not in script, "낭독문 누락/이전 대기 설명 잔존 없음")
check("최신 입력 해시 유지", all(hashlib.sha256((ep / path).read_bytes()).hexdigest() == v["sha256"] for path, v in p["input_versions"].items()), "현재price_panel_data와 v2최종메타데이터 SHA 포함")
check("최신 부모패널 SHA 직접일치", p["price_input_lock"]["panel_sha256"] == hashlib.sha256((ep / "director/top20-explain-v3/price_panel_data.json").read_bytes()).hexdigest(), p["price_input_lock"]["panel_sha256"])
check("송파 비교범위와20지역 최소최대 회수", any(x["sentence_id"] == "S021-22" and x["claim_ids"] == ["V3_API_PRICE_R02", "V3_API_APT_R02"] for x in allx) and min(panel["regions"], key=lambda r:r["median_manwon"])["region_id"] == "R10" and max(panel["regions"], key=lambda r:r["median_manwon"])["region_id"] == "R06" and any(x["sentence_id"] == "C001-01" and "4억원부터 강남구 30억3,000만원까지" in x["text"] for x in allx), "원인/프리미엄 주장 없음;20지역 중위값 최소최대 검사")
check("마지막 중복·도입 음성 간결화", "1단지 단지 사례" not in next(s for s in regions if s["region_id"] == "R01")["narration_text"] and not any(x["sentence_id"] in ["O002-03", "O002-04", "O002-05", "O002-07C", "O002-09"] for x in allx), "법적정의는 내부근거 유지;실제 도입시간은 음성 승인 이후 확인")
check("기흥 부모 보완근거 통합", any(x["sentence_id"] == "S005-02" and x["text"] == "기흥구는 동백·흥덕의 대규모 택지개발 주거지와 기업·연구시설이 함께 자리한 지역입니다." and x["claim_ids"] == ["V3-R18-DIR-H03"] for x in allx), "부모 공식페이지 L579~585 검증 승계;고용증가/집값원인 추론 없음")
failed = [c["check"] for c in checks if c["result"] == "fail"]
report = {"status": "writer_final_text_checks_passed" if not failed else "failed", "created_at": datetime.now().astimezone().isoformat(), "checks": checks, "failed": failed, "summary": {"regions": len(regions), "scenes": len(p["scenes"]), "written_sentences": len(allx), "pending_slots": 0, "region_and_complex_price_pairs": 20}, "output_sha256": {name: hashlib.sha256((own / name).read_bytes()).hexdigest() for name in ["script_v6.md", "scene_proposals_v6.json"]}, "scope": "새 텍스트·claim·전환ID·40가격/각n·최신입력SHA 검사.독립원XML 재집계·사진픽셀·좌표·음성·실제프레임검수는 writer가 미수행.", "actual_listening_performed": False, "continuous_playback_performed": False, "tts_or_render_performed": False}
(own / "verification_v6.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"status": report["status"], "checks": len(checks), "failed": failed, **report["summary"]}, ensure_ascii=False))
raise SystemExit(1 if failed else 0)
