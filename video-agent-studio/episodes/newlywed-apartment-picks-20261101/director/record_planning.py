"""Record versioned research, narrative plans and the draft's decision boundary."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
STUDIO = ROOT / "video-agent-studio"
EP = Path(__file__).resolve().parent.parent


def read_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8-sig"))


def write_json(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    rank_path = ROOT / "analysis/newlywed_region_2024/rankings.json"
    ranking = read_json(rank_path)
    candidates = read_json(EP / "research/transaction_candidates.json")
    script = EP / "writer/대본초안_v1.md"
    notes = script.read_text(encoding="utf-8").split("## 제작 메모", 1)[0]
    blocks = re.findall(r"## (S\d{3})\. ([^\n]+)\n\n(.*?)(?=\n## |\Z)", notes, re.S)
    assert len(blocks) == 7
    visuals = {
        "S001": ("내 예산에서 실제 단지 선택으로 연결", "verified_area_plan_comparison", [], ["동일 가격대의 실제59/84㎡ 평면", "현재 비교 가격"]),
        "S002": ("2024 구 순위를 탐색 지역과 연결", "ranked_map_then_boundary_crosswalk", ["NW-RANK"], ["2024 수도권 구 경계", "현재 인천 서해·검단 범위"]),
        "S003": ("면적·가격을 맞추면 연식과 생활권을 비교할 수 있다", "price_year_pair_and_commute_routes", ["PX-Q3-SAME59"], ["두 단지 실제 사진", "단지에서 역 출입구까지 실제 경로"]),
        "S004": ("비슷한 돈으로 면적·생활권을 바꾸는 선택", "matched_budget_actual_floorplans", ["PX-HALFYEAR-AREA"], ["힐데스하임59 평면", "모아미래도84 평면"]),
        "S005": ("같은 단지 안에서 면적 예산을 비교", "within_complex_area_price_then_daily_map", ["PX-FORENA"], ["포레나59/84 평면", "가정동 생활시설 실제 위치"]),
        "S006": ("매물 조건과 실거래를 연결해 실제 선택", "verified_listing_card_and_transaction_distribution", [], ["현재 확인 매물 원자료", "동층·수리·입주일", "사진 이용조건"]),
        "S007": ("개인 조건 세 가지로 후보를 좁힌다", "household_condition_filter_and_cta", [], ["확인된 최종 후보3곳", "각 후보의 적용 조건"]),
    }
    scenes = []
    for scene_id, title, text in blocks:
        message, typ, claims, required = visuals[scene_id]
        scenes.append({"scene_id": scene_id, "title": title, "message": message,
                       "narration_text": text.strip(), "claim_ids": claims, "visual_type": typ,
                       "asset_ids": [], "required_assets": required, "asset_status": "to_acquire",
                       "script_revision": "draft-v1", "audio_revision": None,
                       "start_s": None, "end_s": None, "timing_basis": "not_locked_no_audio",
                       "status": "proposed", "literal_anchors": []})
    write_json(EP / "scenes.json", {"episode_id": EP.name, "revision": "planning-v1", "scenes": scenes})

    def subset(apt_id: str, area: str):
        return next(r for r in candidates if r["apt_id"] == apt_id and r["area_band"] == area)
    first = [subset("9a8b510f914bcc5d", "59"), subset("9755291bfda5e7ee", "59")]
    second = [subset("a0b8a75dc38d3a38", "59"), subset("33daedb345f6cca1", "84")]
    third = [subset("8c36915adefc2a67", "59"), subset("8c36915adefc2a67", "84")]
    assert all(r["q3_n"] >= 5 and r["q3_median_manwon"] == 49000 for r in first)
    assert second[1]["median_manwon"] - second[0]["median_manwon"] == 150
    assert third[1]["median_manwon"] - third[0]["median_manwon"] == 7900
    write_json(EP / "research/claims_v1.json", {"revision": "planning-v1", "claims": [
        {"claim_id": "NW-RANK", "status": "source_transcribed_pending_independent_review",
         "description": "2024 수도권53개구 신혼부부 전체 수 순위", "top5": ranking["capital_gu_ranking"][:5],
         "evidence_path": str(rank_path.relative_to(ROOT)), "source_url": ranking["metadata"]["source_url"]},
        {"claim_id": "PX-Q3-SAME59", "status": "local_reproduced_aggregate", "window": ["2026-07-01", "2026-09-30"],
         "description": "두59㎡ 후보의3개월 중위값4억9000만원 동일, 준공연도2011/2023", "rows": first},
        {"claim_id": "PX-HALFYEAR-AREA", "status": "local_reproduced_aggregate", "window": ["2026-04-01", "2026-09-30"],
         "description": "청라59와 검단84의6개월 중위값 차150만원", "rows": second},
        {"claim_id": "PX-FORENA", "status": "local_reproduced_aggregate", "window": ["2026-04-01", "2026-09-30"],
         "description": "포레나루원59/84 중위값 차7900만원", "rows": third}
    ], "source_snapshots": read_json(EP / "research/candidate_method.json")["source_files"]})

    qa_path = EP / "qa/ranking_source_review.json"
    if qa_path.exists():
        qa = read_json(qa_path)
        assert qa["verdict"]["required_count"] == 0
        assert qa["verdict"]["critical_count"] == 0
        assert qa["checked_revision"]["tsv_sha256"] == sha(ROOT / "analysis/newlywed_region_2024/source/capital_rows.tsv")
        assert qa["checked_revision"]["rankings_sha256"] == sha(rank_path)
        md = ROOT / "analysis/newlywed_region_2024/수도권_신혼부부_순위.md"
        md_text = md.read_text(encoding="utf-8")
        assert md_text.count("2024 통계구역 기준 수도권") == 3
        assert "각 시군구에 0.5 가중치" in md_text
        claims = read_json(EP / "research/claims_v1.json")
        claims["claims"][0]["status"] = "independent_source_review_passed"
        claims["claims"][0]["qa"] = "qa/ranking_source_review.json"
        write_json(EP / "research/claims_v1.json", claims)
        write_json(EP / "director/qa_resolution_v1.json", {
          "base_review": "qa/ranking_source_review.json", "source_rows_checked": 86, "numeric_cells_checked": 258,
          "critical": 0, "required": 0, "original_source_and_rankings_unchanged": True,
          "resolutions": [
            {"id": "RANK-SOURCE-001", "status": "implemented_and_director_checked", "change": "각 표 제목에2024 통계구역·거주 규모 명시"},
            {"id": "RANK-SOURCE-002", "status": "implemented_and_director_checked", "change": "독립 문서에0.5가중치·합계 반올림 가능성 설명 추가"}
          ], "document_sha256_after": sha(md), "new_independent_recheck_claimed": False,
          "scope": "Numeric QA applies to unchanged TSV/rankings. Director checked documentation-only changes. No video/audio review performed."
        })

    public_fields = EP / "research/public_page_checks/aipartner_article_fields.json"
    if public_fields.exists():
        fields = read_json(public_fields)
        assert fields["tradePrice"] == 51000 and fields["useMeter"] == 59.86
        assert fields["dongNm"] == "216" and fields["corrpFlr"] == 5
        public_quote = {
            "source_url": "https://town.aipartner.com/memul/T272013181", "observed_date": "2026-11-01",
            "evidence_type": "public_advertisement_fields_observed", "http_status": 200,
            "fields": fields, "source_html_sha256": sha(public_fields.parent / "aipartner_T272013181.html"),
            "method": "Read public page's serialized JSON without executing JavaScript or bypassing access controls.",
            "registration_or_update_absolute_date": None, "seller_availability_confirmed": False,
            "images_downloaded_or_reused": False, "use": "S006 dated public-ad example, separate from historical medians and confirmed availability."
        }
        write_json(EP / "research/public_page_checks/observation.json", public_quote)
        claims = read_json(EP / "research/claims_v1.json")
        claims["claims"].append({"claim_id": "AD-CH59", "status": "public_ad_fields_observed",
          "source": "research/public_page_checks/observation.json", "price_gap_from_q3_median_manwon": 2000})
        write_json(EP / "research/claims_v1.json", claims)
        for row in scenes:
            if row["scene_id"] == "S006":
                row["claim_ids"] = ["AD-CH59", "PX-Q3-SAME59"]
                row["asset_ids"] = ["public_page_checks/aipartner_T272013181.html"]
                row["asset_status"] = "one_ad_fields_verified_other_listings_and_rights_pending"
        write_json(EP / "scenes.json", {"episode_id": EP.name, "revision": "planning-v1", "scenes": scenes})

    preflight = read_json(STUDIO / "templates/episode_preflight.json")
    preflight.update({"status": "planning_filled_production_checks_pending", "episode_id": EP.name})
    preflight["input_contract"].update({"narration_mode": "not_selected", "original_user_script": None,
      "proposed_script_changes": "writer/대본초안_v1.md", "timing_basis": "not_locked_no_audio",
      "episode_specific_choices": ["2024 신혼부부 거주 규모로 탐색 지역 선정", "현재 단지는 현재 행정구역으로 표시", "매매 단지 및 실제 매물 비교 제안"],
      "superseded_historical_defaults": ["새 편에 과거 Jun 예산·음성을 자동 승계하지 않음", "신도시 블록별 소개 순서를 강제하지 않음"]})
    current = read_json(ROOT / "config/current_video.json")
    previous_script = ROOT / current["script"]
    preflight["baseline"].update({"previous_video": current.get("youtube_url"), "current_video": None,
      "script_revision": str(previous_script.relative_to(ROOT)), "previous_script_sha256": sha(previous_script),
      "previous_outro_checked": "예산 다음 실제 아파트 선택, 같은5억대·7억대 입지/단지 비교 예고 본문 확인"})
    preflight["approvals"]["topic"].update({"decision_id": "direct-user-20261101-newlywed-apartment", "status": "authorized_by_direct_user",
        "artifact_hashes": {"rankings.json": sha(rank_path)}})
    preflight["approvals"]["script"].update({"status": "draft_for_review_not_approved", "artifact_hashes": {"writer/대본초안_v1.md": sha(script)}})
    preflight["approvals"]["budget"].update({"status": "not_requested_not_authorized", "automatic_retry_allowed": False})
    preflight["story"].update({"opening_question": "같은 예산이면 어느 생활권의 어떤 아파트를 선택할까?",
      "previous_episode_reference": "현금1억부터5억까지, 얼마짜리 집을 살 수 있을까?",
      "next_episode_promise": "다음 구에서도 같은 기준으로 단지 비교; 세부 순서는 제안",
      "order": ["budget_to_choice", "regional_rank_context", "same_size_price_different_year", "same_budget_different_area", "within_complex_area_choice", "live_listing_conditions", "household_fit"],
      "candidate_scope": "conditional_resale_apartment_candidates_with_live_listing_verification_pending"})
    preflight["representative_previews"] = ["same_price_same_area_pair", "actual_floorplan_area_tradeoff", "verified_map_and_listing_evidence"]
    preflight["facts_required"] = ["newlywed_scope_and_old_boundary", "current_administrative_crosswalk", "apartment_identity_and_actual_plan", "price_area_floor_period_n_cancellations", "current_listing_status_and_quote", "actual_commute_and_facility_status", "source_rights"]
    preflight["qa"]["required_open_issues"] = None
    preflight["release"]["longform"] = "planning_only"
    write_json(EP / "episode_preflight.json", preflight)
    write_json(EP / "decisions.json", {"episode_id": EP.name, "revision": "planning-v1", "decisions": [
      {"id": "D001", "choice": "신혼부부 수 순위와 아파트 선택 시리즈 착수", "basis": "current user instruction", "status": "authorized"},
      {"id": "D002", "choice": "2024 수도권 구53개 주표 및 시군자치구66개/세부79개 별도 보존", "basis": "prevent parent-child double counts and keep city-only regions", "status": "director_research_method"},
      {"id": "D003", "choice": "한 권역에서 같은 예산·면적의 후보 비교", "basis": "channel predecessor outro and observed data contrasts", "status": "proposal_not_user_confirmed"},
      {"id": "D004", "choice": "현재 매물·평면·통근 검증 후 추천 문장과 화면 확정", "basis": "historical transaction prices and 2024 stock counts serve different purposes", "status": "required_before_production"},
      {"id": "D005", "choice": "음성·렌더·업로드와 외부 Claude 전송 단계는 미실행", "basis": "new script/voice/budget/release scope not yet decided", "status": "current_boundary"}
    ]})

    scope = ROOT / "analysis/newlywed_region_2024/validation.json"
    live_path = EP / "research/listing_evidence_v1.json"
    state = read_json(EP / "state.json")
    state.update({"phase": "script_direction_review_pending", "script": "writer/대본초안_v1.md",
        "script_sha256": sha(script), "planning_document": "director/제작기획안_v1.md",
        "candidate_pairs": len(candidates), "candidate_complexes": len({r["apt_id"] for r in candidates}),
        "rank_counts": ranking["metadata"]["scope_counts"], "hyperframes_usage": {"status": "unknown", "reason": "usage_request_failed"},
        "current_listing_evidence": str(live_path.relative_to(EP)) if live_path.exists() else "in_progress",
        "ranking_independent_review": str(qa_path.relative_to(EP)) if qa_path.exists() else "pending",
        "public_ad_examples_observed": 1 if public_fields.exists() else 0,
        "seller_availability_confirmed": False,
        "open_research_items": ["other candidate listing details and availability", "actual floorplans and reuse rights", "commute routes and daily facilities"],
        "updated_at": datetime.now().astimezone().isoformat()})
    write_json(EP / "state.json", state)
    write_json(EP / "director/script_review_request.json", {
      "decision_id": "newlywed-apartment-20261101-script-direction-v1", "gate": "script", "status": "pending",
      "script": "writer/대본초안_v1.md", "sha256": sha(script),
      "planning_document": "director/제작기획안_v1.md", "planning_sha256": sha(EP / "director/제작기획안_v1.md"),
      "decision_scope": "첫 편을 청라·검단·루원 생활권의 같은 돈/면적/연식 비교 흐름으로 진행할지 확인. 현재 광고 관찰과 실거래를 구분한 초안. 미확인 매물/평면/통근 근거는 추가 보완.",
      "permissions_not_included": ["new paid voice/image generation", "external Claude packet transfer", "upload or public release"],
      "source": "AGENTS.md script(대본 전달) 결정 단계"
    })

    # Preserve previous shelf entries, add this preproduction workspace once.
    shelf_path = ROOT / "config/video_shelf.json"
    shelf = read_json(shelf_path)
    entry = {
      "name": "신혼부부_지역별아파트",
      "status": "자료·기획·대본 초안 v1 — 2024 기준 순위, 현재 매물/지도 검증 진행. 영상·음성 제작 전",
      "workspace": str(EP.relative_to(ROOT)).replace("\\", "/"),
      "files": {
        "지역순위.md": "analysis/newlywed_region_2024/수도권_신혼부부_순위.md",
        "구순위.csv": "analysis/newlywed_region_2024/capital_gu_ranking.csv",
        "시군구순위.csv": "analysis/newlywed_region_2024/capital_municipality_ranking.csv",
        "기획안.md": str((EP / "director/제작기획안_v1.md").relative_to(ROOT)).replace("\\", "/"),
        "대본초안.md": str(script.relative_to(ROOT)).replace("\\", "/"),
        "단지후보.csv": str((EP / "research/transaction_candidates.csv").relative_to(ROOT)).replace("\\", "/")
      }
    }
    prior = [e for e in shelf["entries"] if e["name"] == entry["name"]]
    if prior:
        prior[0].update(entry)
    else:
        shelf["entries"].append(entry)
    write_json(shelf_path, shelf)
    print(json.dumps({"scene_count": len(scenes), "spoken_characters_rough": sum(len(b[2].strip()) for b in blocks),
      "script_sha256": sha(script), "phase": state["phase"], "shelf_name": entry["name"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
