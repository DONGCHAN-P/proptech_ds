"""Preserve the old apartment draft; freeze inputs for the requested TOP20 film."""
import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
EP = Path(__file__).resolve().parent.parent
REV = "top20-8min-v2"


def read(p):
    return json.loads(p.read_text(encoding="utf-8-sig"))


def write(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    new_dir = EP / "research" / REV
    new_dir.mkdir(parents=True, exist_ok=True)
    for file in ["brief.json", "state.json", "decisions.json", "scenes.json", "episode_preflight.json"]:
        src = EP / file
        target = EP / "director/planning-v1-preserved" / file
        if src.exists() and not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(src.read_bytes())
    rankings_path = ROOT / "analysis/newlywed_region_2024/rankings.json"
    ranks = read(rankings_path)["capital_gu_ranking"][:20]
    top = []
    for row in ranks:
        top.append({**row, "region_id": f'R{row["rank"]:02d}',
                    "scene_id": f'S{23-row["rank"]:03d}',
                    "suggested_countdown_order": 21-row["rank"]})
    write(new_dir / "top20.json", {"revision": REV, "scope": "2024 수도권53개구 중 신혼부부 전체 수 TOP20",
      "source_path": str(rankings_path.relative_to(ROOT)), "source_sha256": hashlib.sha256(rankings_path.read_bytes()).hexdigest(),
      "statistic_reference_date": "2024-11-01", "unit": "couples", "regions": top})
    brief = read(EP / "brief.json")
    brief.update({"revision": REV, "request": "신혼부부 지역별 순위 TOP20을 보여주는8분 본편; 지역별 자료조사와 사용할 이미지 자료 준비",
      "request_date": "2026-11-01", "target_duration_seconds": 480,
      "active_scope": "2024 통계구역 수도권53개구 중 신혼부부 전체 수 TOP20.20위부터1위까지 소개하는16:9 본편",
      "current_stage": "research_and_real_place_asset_pack",
      "superseded_scope": "첫 편을 청라·검단·루원 단지추천에 한정한 planning-v1 구성. 자료와 원고는 보존.",
      "current_deliverables": ["지역20곳의 공식 근거·설명 포인트", "2023 대비 비교 가능한 신혼부부 수 변화", "지역별 실제 장소 사진 및 출처·이용조건", "지역별 지도 원본 및 PNG", "8분 구성표와 자료화면 안내", "자료 미확보·허락 확인 목록"],
      "paid_generation_authorized": False, "upload_authorized": False})
    write(EP / "brief.json", brief)
    state = read(EP / "state.json")
    state.update({"revision": REV, "phase": "top20_research_and_assets", "duration_target_s": 480,
      "active_ranking_source": f"research/{REV}/top20.json", "previous_script": state.get("script"),
      "script": "new_top20_draft_pending_research", "voice": "not_selected", "render_created": False,
      "updated_at": datetime.now().astimezone().isoformat()})
    write(EP / "state.json", state)
    request = EP / "director/script_review_request.json"
    if request.exists():
        old = read(request)
        old.update({"status": "superseded_by_user", "superseded_reason": "TOP20 eight-minute revision; old three-neighborhood script is preserved, not approved"})
        write(request, old)
    write(EP / "director" / REV / "decision_scope.json", {
      "revision": REV, "topic": "authorized by current direct user", "research_and_asset_preparation": "authorized by latest user",
      "script_gate": "new script to be delivered after research", "paid_generation": "not_authorized", "upload": "not_requested",
      "geography": "2024 data boundaries, current photo date and current administrative crosswalk handled separately",
      "image_rules": ["actual named place verified", "download actual local files when licensed", "record image-specific rights", "do not generate fictional aerials as evidence", "no repeated unrelated image", "keep old script and sources"]})
    print(json.dumps({"revision": REV, "regions": len(top), "duration_target_s": 480,
      "scope": brief["active_scope"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
