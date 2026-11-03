"""Integrate the final regional research packet; leave every price field unfilled."""
import hashlib
import json
from pathlib import Path


def integrate_features(scenes, claims, versions, ep):
    relroot = "research/top20-explain-v3/regions"
    names = ["facts.json", "narration_suggestions.json", "region_features.md", "handoff.json", "validation.json"]
    loaded = {}
    for name in names:
        path = ep / relroot / name
        versions[f"{relroot}/{name}"] = {"sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        loaded[name] = path.read_text(encoding="utf-8-sig")
    facts = json.loads(loaded["facts.json"])
    suggestions = json.loads(loaded["narration_suggestions.json"])
    validation = json.loads(loaded["validation.json"])
    handoff = json.loads(loaded["handoff.json"])
    assert validation["passed"] and validation["region_count"] == 20
    for record in validation["outputs"]:
        assert record["sha256"] == versions[f"{relroot}/{record['file']}"]["sha256"], record["file"]
    region_facts = {r["region_id"]: r for r in facts["regions"]}
    suggestions_by_id = {r["region_id"]: r for r in suggestions["regions"]}
    for region in region_facts.values():
        for claim in region["claims"]:
            assert claim["status"] == "verified", claim["claim_id"]
            claims[claim["claim_id"]] = {**claim, "input_path": f"{relroot}/facts.json", "input_revision": facts["revision"], "writer_verification": "최종 리서치 패킷의 검증 범위·시점 승계; 이번 writer 원문 재검수 아님"}

    supplement_rel = "research/top20-explain-v3/director_supplement.json"
    supplement_bytes = (ep / supplement_rel).read_bytes()
    versions[supplement_rel] = {"sha256": hashlib.sha256(supplement_bytes).hexdigest()}
    supplement = json.loads(supplement_bytes.decode("utf-8-sig"))
    housing_supplement = next(c for c in supplement["claims"] if c["claim_id"] == "V3-R18-DIR-H03")
    assert housing_supplement["status"] == "verified"
    claims[housing_supplement["claim_id"]] = {**housing_supplement, "input_path": supplement_rel, "writer_verification": "부모의 공식 본문 직접 검증 근거 승계;writer가 새 원문 열람을 수행한 것은 아님"}

    # Editorial changes stay inside the verified claims. Years/counts are used
    # only when they help explain the housing fabric, rather than as a list.
    overrides = {
        "R20": [
            ("원미구는 중동과 상동에 걸쳐 형성된 중동신도시의 아파트 생활권을 포함합니다.", ["V3-R20-H01"], "verified_fact"),
            ("부천시 정비기본계획은 공동주택 블록과 마을 단위를 함께 다뤄, 개별 단지와 주변 주거지를 같이 살펴볼 기준이 됩니다.", ["V3-R20-H01", "V3-R20-H02"], "editorial_interpretation"),
            ("부천중앙공원은 중동신도시 개발과 함께 조성된 근린공원입니다.", ["R20-F01"], "verified_fact"),
        ],
        "R18": [
            (housing_supplement["text"], ["V3-R18-DIR-H03"], "verified_fact"),
            ("구성역은 GTX-A와 수인분당선이 만나는 거점입니다.", ["V3-R18-H02"], "verified_fact"),
            ("동백과 구성역 주변은 서로 다른 생활권이므로, 단지와 역 위치를 함께 살펴보겠습니다.", ["V3-R18-H01", "V3-R18-H02"], "editorial_application"),
        ],
        "R17": [
            ("연수구에는 연수2동의 아파트·중심상가 생활권과 송도의 국제업무·바이오산업 개발 권역이 함께 있습니다.", ["V3-R17-H01", "V3-R17-H02"], "verified_fact"),
            ("송도 센트럴파크는 해수를 활용한 공원으로, 산책정원과 수로 주변 여가시설이 도심의 휴식 공간을 이룹니다.", ["V3-R17-L01"], "verified_fact"),
        ],
        "R16": [
            ("남동구 논현동에는 논현웰카운티처럼 2000년대에 입주한 아파트 단지가 있습니다.", ["V3-R16-H01"], "verified_fact"),
            ("소래습지생태공원은 갯벌과 습지, 탐방데크를 갖춘 생태공원입니다.", ["V3-R16-L01"], "verified_fact"),
            ("공원 안에는 옛 염전을 활용한 학습장도 있어 해안의 생태환경과 염전의 흔적을 함께 살펴볼 수 있습니다.", ["V3-R16-L01", "V3-R16-L02"], "verified_fact"),
        ],
        "R15": [
            ("구로구 신도림동에는 신도림로와 경인로 주변으로 대림·동아·우성 등 여러 아파트 단지가 분포합니다.", ["V3-R15-H01"], "verified_fact"),
            ("신도림역은 1호선과 2호선이 만나는 환승역입니다.", ["V3-R15-L01"], "verified_fact"),
            ("한편 구로동에는 금천구 가산동과 이어지는 G밸리 산업지역이 있어, 신도림 주거권과 구로동 업무권을 나눠 살펴볼 수 있습니다.", ["V3-R15-H02", "V3-R15-H01"], "fact_with_editorial_application"),
        ],
        "R14": [
            ("은평구 진관동의 은평뉴타운은 상림마을과 우물골 등 마을 단위로 나눠 조성된 주거지입니다.", ["V3-R14-H01"], "verified_fact"),
            ("우물골 단지 옆에는 진관동 주민센터가 있어, 마을과 단지 이름을 함께 놓고 생활권을 살펴볼 수 있습니다.", ["V3-R14-H01", "V3-R14-L01"], "fact_with_editorial_application"),
        ],
        "R13": [
            ("권선구는 기존 도심 주거지와 서수원 호매실·당수의 택지개발 생활권이 함께 있는 지역입니다.", ["V3-R13-H01"], "verified_fact"),
            ("권선동의 수원종합버스터미널은 도시 간 버스 이동을 연결하는 생활권의 거점입니다.", ["V3-R13-L01"], "verified_fact"),
        ],
        "R10": [
            ("미추홀구에는 도시개발사업으로 조성된 도화동 주거지와 주안역을 중심으로 한 기존 철도 생활권이 함께 있습니다.", ["V3-R10-H01", "V3-R10-H02"], "verified_fact"),
            ("주안역은 수도권 1호선과 인천2호선을 연결하는 환승 거점입니다.", ["V3-R10-H02"], "verified_fact"),
            ("문학경기장은 2002년 월드컵 경기를 개최한 지역 체육시설입니다.", ["V3-R10-L01"], "verified_fact"),
        ],
        "R08": [
            ("영등포구에는 금융 업무가 모인 여의도와 문래동6가의 e편한세상 문래 에듀플라츠 같은 아파트 주거지가 함께 있습니다.", ["V3-R08-H01", "V3-R08-H02"], "verified_fact"),
            ("여의도 업무권과 문래 주거권은 위치가 다르므로, 같은 구 안에서도 직장과 집을 어느 권역에 둘지 나누어 비교하는 방식이 유용합니다.", ["V3-R08-H01", "V3-R08-H02"], "editorial_application"),
        ],
        "R07": [
            ("강동구 고덕·상일권에서는 재건축으로 아파트 주거지가 새로 조성된 사례를 볼 수 있습니다.", ["V3-R07-H01"], "verified_fact"),
            ("상일동의 옛 고덕주공7단지가 재건축을 거쳐 준공인가를 받은 사례입니다.", ["V3-R07-H01"], "verified_fact"),
            ("고덕역은 5호선을 이용하는 생활 교통의 거점입니다.", ["V3-R07-L01"], "verified_fact"),
        ],
        "R06": [
            ("강남구 개포동에는 1980년대에 사용승인된 개포주공6단지와 2020년대에 승인된 개포자이프레지던스가 함께 있습니다.", ["V3-R06-H01", "V3-R06-H02"], "verified_fact"),
            ("같은 개포동 안에서도 아파트가 조성된 시기가 크게 다릅니다.", ["V3-R06-H01", "V3-R06-H02"], "editorial_interpretation"),
            ("양재천 산책로는 주거지 주변의 수변 보행 공간입니다.", ["V3-R06-L01"], "verified_fact"),
        ],
        "R05": [
            ("부평구에는 부평역 주변 상업 생활권과 택지개발로 대단위 아파트가 형성된 삼산2동 주거지가 함께 있습니다.", ["V3-R05-H01", "V3-R05-H02"], "verified_fact"),
            ("부평역은 수도권 1호선과 인천1호선이 만나는 환승 거점입니다.", ["V3-R05-L01"], "verified_fact"),
        ],
        "R04": [
            ("강서구 마곡은 주거단지와 산업·업무단지, 공원 구역을 나눠 계획한 지역입니다.", ["V3-R04-H01"], "verified_fact"),
            ("서울식물원은 식물 전시와 야외 공원을 함께 갖춘 생활권의 여가 공간입니다.", ["V3-R04-L01"], "verified_fact"),
        ],
        "R03": [
            ("덕양구 삼송은 택지개발지구의 아파트·오피스텔과 역 주변의 기존 단독주택이 함께 있는 생활권입니다.", ["V3-R03-H01"], "verified_fact"),
            ("삼송로 일대는 3호선 삼송역과 생활 공공시설을 중심으로 위치를 살펴볼 수 있습니다.", ["V3-R03-L01"], "fact_with_editorial_application"),
        ],
        "R02": [
            ("송파구 잠실권에는 잠실2·3단지처럼 2000년대 재건축을 거쳐 다시 조성된 아파트 단지들이 있습니다.", ["V3-R02-H01"], "verified_fact"),
            ("석촌호수는 동호와 서호, 산책로가 있는 도심 수변 여가 공간입니다.", ["V3-R02-L01"], "verified_fact"),
        ],
        "R01": [
            ("2024년 통계의 인천 서구에는 청라와 검단이 함께 들어갑니다.", ["V3-R01-H01", "V3-R01-G01"], "verified_fact"),
            ("청라는 업무·주거·문화·레저 기능을 함께 배치하도록 계획된 지역이며, 청라호수공원은 산책과 여가를 위한 공간입니다.", ["V3-R01-H01", "V3-R01-L01"], "verified_fact"),
            ("현재는 아라뱃길 남쪽 서해구와 북쪽 검단구로 나뉩니다.", ["V3-R01-G01"], "verified_fact"),
        ],
    }
    scenes[:] = [s for s in scenes if s["scene_id"] != "I003"]
    for s in scenes:
        s["estimated_duration_s"] = None
        s["duration_basis"] = "가격 문장 통합 후 estimate 산정; 정보량 우선, 실제 음성 이후 시간 확정"
        s["status"] = "FEATURES_INTEGRATED_PRICES_PENDING" if s["region_id"] else "text_review_pending_script_gate"
        if s["scene_id"] == "O002":
            x = next(x for x in s["sentences"] if x["sentence_id"] == "O002-06")
            x["text"] = "이후 입주와 이사로 거주 분포가 달라질 수 있어, 2024년의 출발점으로 살펴보겠습니다."
            x["display_text"] = x["text"]
            x["anchor_string"] = "2024년의 출발점"
            x["onscreen_purpose"] = "2024 관측 시점과 그 이후의 변화 가능성을 직접 설명. 다음 가격 계약기간 슬롯과 분리."
            x["statement_type"] = "data_scope_explanation"
        if not s["region_id"]:
            continue
        rid = s["region_id"]
        rf = region_facts[rid]
        assert rf["scene_id"] == s["scene_id"]
        baseline = suggestions_by_id[rid]
        revised = overrides.get(rid, [(x["text"], x["claim_ids"], "verified_fact") for x in baseline["sentences"]])
        assert 2 <= len(revised) <= 3, rid
        price_slots = [x for x in s["sentences"] if x.get("slot_kind") in ["region_price_median", "representative_complex_price"]]
        rank_sentence = s["sentences"][0]
        new_sentences = []
        for index, (text, cids, kind) in enumerate(revised, 2):
            for cid in cids:
                assert cid in claims, cid
            new_sentences.append({
                "sentence_id": f"{s['scene_id']}-{index:02}", "text": text, "claim_ids": cids,
                "statement_type": kind, "display_text": text, "reading_text": text,
                "display_notes": "숫자·고유명사·동 이름을 의미 단위로 보존. 자료사진은 촬영연도/자료사진 여부를 해당 컷에 표시.",
                "reading_notes": "합니다/입니다 평서문. 승인 전 합성 금지. 계획·준공·사용승인·현재 운영의 범위를 바꾸지 않음.",
                "onscreen_purpose": "주거지 형성과 실제 장소의 기능을 이해하도록 지역 내부의 대상을 구분해 제시",
                "anchor_string": text, "material_type": "map", "visual_role": "explanation",
                "status": "ready_for_parent_text_review", "narration_ready": False,
                "source_revision": facts["revision"],
            })
        s["sentences"] = [rank_sentence] + new_sentences + price_slots
        s["regional_explanation_sentence_ids"] = [x["sentence_id"] for x in new_sentences]
        s["feature_input"] = {"path": f"{relroot}/facts.json", "revision": facts["revision"], "claim_ids": [c["claim_id"] for c in rf["claims"]], "writer_changes": "해석·활용 문장을 구분하고 반복 연도/세대수/사진 소개 문장을 줄임", "housing_feature_claim_ids": rf["housing_feature_claim_ids"], "landmark_function_claim_ids": rf["landmark_function_claim_ids"]}
        if rid == "R18":
            s["feature_input"]["claim_ids"].append("V3-R18-DIR-H03")
            s["feature_input"]["housing_feature_claim_ids"].append("V3-R18-DIR-H03")
            s["feature_input"]["director_supplement"] = supplement_rel
        for x in price_slots:
            x["onscreen_purpose"] += " 가격 문장은 지역 중위값1문장·단지 사례1문장을 우선하며 실제 지역명/동 이름으로 공간 범위를 구분."
            if x["slot_kind"] == "representative_complex_price":
                x["required_fields"] += ["neighborhood_name", "landmark_vs_complex_same_or_different_living_area"]
            x["reading_notes"] += " 총괄의 기간·정규화data lock 전 금액을 넣지 않으며, 이후 사용자 새 대본 승인 전에도 합성 금지."
        s["photo_binding"] = rf["photo"]
        s["requested_photo_places"] = [rf["photo"]["actual_place"]]
        s["photo_requirements"] = {
            "asset_id": rf["photo"]["asset_id"], "actual_place": rf["photo"]["actual_place"],
            "photo_capture_year": rf["photo"]["photo_capture_year"], "caption_ko": rf["photo"]["caption_ko"],
            "prior_inspection_reused": rf["photo"]["prior_inspection_reused"],
            "writer_pixel_review_performed": False, "writer_new_license_review_performed": False,
            "editorial_cautions": rf["editorial_cautions"],
            "landmark_and_price_case_location_policy": "사진 장소와 대표가격 단지는 다른 생활권일 수 있음. 가격 단지는 실제 동 이름과 별도 지도 구도로 전환하며 동일 장소로 합성·연결하지 않음.",
        }
        s["editorial_cautions"] = rf["editorial_cautions"]
        s["map_requirements"]["complex_neighborhood_label_required"] = True
        s["map_requirements"]["landmark_complex_same_place_assumption_allowed"] = False
        s["map_requirements"]["all_new_point_locations_require_verified_coordinates"] = True
        s["screen_beats"] = [
            {"beat_id": f"{s['scene_id']}-B1", "sentence_ids": [rank_sentence["sentence_id"]], "purpose": "scope_and_resident_count", "asset_type": "map", "action": "구 윤곽·이름과2024 거주 수를 제시. 가격의 기준연도와 혼합하지 않음.", "anchor_string": rank_sentence["anchor_string"]},
            {"beat_id": f"{s['scene_id']}-B2", "sentence_ids": s["regional_explanation_sentence_ids"], "purpose": "housing_formation_and_separate_living_areas", "asset_type": "map", "action": "발화한 주거권·업무권·역을 실제 주소와 검증 공간 자료로 구분. 동 이름을 지도 가까이에 표시하고 계획 이력을 현재 사업 완료로 확대하지 않음.", "anchor_string": new_sentences[0]["text"]},
            {"beat_id": f"{s['scene_id']}-B3", "sentence_ids": s["regional_explanation_sentence_ids"], "purpose": "actual_landmark_context", "asset_type": "real_photo", "action": f"{rf['photo']['asset_id']} / {rf['photo']['caption_ko']}. 이 실제 장소를 설명할 때만 사진을 연결. 사진의 촬영연도와 현재 노선·개발 상태를 구분.", "anchor_string": None, "asset_id": rf["photo"]["asset_id"], "binding_basis": "리서치 최종 사진명세 승계; 문자열 앵커는 아래 개별 정책에 따라 실제 장소 언급과 연결"},
            {"beat_id": f"{s['scene_id']}-B4", "sentence_ids": [x["sentence_id"] for x in price_slots], "purpose": "regional_and_complex_price", "asset_type": "map", "action": "랜드마크 설명을 마친 뒤 실제 가격 집계구역으로 전환. 지역 중위값/지역n과 대표 단지/동 이름/단지n을 분리. 기간·면적·취소 처리 유지. 단지가 사진 장소와 다른 생활권이면 명시적으로 구분하고 새 지도 구도를 사용.", "anchor_string": None, "status": "pending_parent_price_period_and_normalized_data_lock"},
        ]
        photo_anchors = {"R01": "청라호수공원", "R02": "석촌호수", "R03": "삼송로", "R04": "서울식물원", "R05": "부평역", "R06": "양재천 산책로", "R07": "고덕역", "R08": "여의도", "R09": "제1판교테크노밸리", "R10": "문학경기장", "R11": "경춘선숲길", "R12": "원천호수", "R13": "수원종합버스터미널", "R14": "은평뉴타운", "R15": "신도림역", "R16": "소래습지생태공원", "R17": "센트럴파크", "R18": "구성역", "R19": "신내역", "R20": "상동"}
        photo_anchor = photo_anchors[rid]
        photo_sentences = [x for x in new_sentences if photo_anchor in x["text"]]
        assert photo_sentences, (rid, photo_anchor)
        s["screen_beats"][2]["anchor_string"] = photo_anchor
        s["screen_beats"][2]["sentence_ids"] = [x["sentence_id"] for x in photo_sentences]
        for x in photo_sentences:
            x["anchor_string"] = photo_anchor
            x["material_type"] = "real_photo"
            x["onscreen_purpose"] = f"{rf['photo']['actual_place']}의 기능을 설명; 사진 범위를 주거지나 가격 단지 전체로 확대하지 않음"
        if rid == "R20":
            s["screen_beats"][2]["action"] = "PHOTO_R20은2025년 상동 도시 가로 사진으로만 제시. 부천중앙공원 문장은 별도 지도 텍스트/주소 대조 영역에 연결. 공원 사진으로 라벨을 바꾸거나 합성하지 않음. 새 핀은 좌표 검증 전 표시하지 않음."
            x = next(x for x in new_sentences if "부천중앙공원" in x["text"])
            x["anchor_string"] = "부천중앙공원"
            x["onscreen_purpose"] = "검증된 공식 소재지를 바탕으로 별도 지도 텍스트로 공원 소개. 상동 거리사진과 분리."
        if rid == "R19":
            s["screen_beats"][2]["action"] += " 2015년 신내역 사진에는 현재6호선 표지·환승 정보를 합성하지 않음. 현재 경춘선·6호선 설명은 사진을 벗어난 별도 현재 지도 레이어에서 제시."
            s["screen_beats"][2]["current_operating_lines_overlay_allowed"] = False
        if rid in ["R18", "R08"]:
            s["screen_beats"][1]["action"] += " 동백 주거지와 구성역 / 문래 주거권과 여의도 업무권을 각각 다른 설명 대상으로 나누며, 정확한 거리·통근시간은 추가하지 않음."

    def shorten(sid, suffixes):
        s = next(s for s in scenes if s["scene_id"] == sid)
        s["sentences"] = [x for x in s["sentences"] if x["sentence_id"].split("-")[-1] in suffixes]
        return s

    i = shorten("I001", {"01", "02", "04"})
    i["sentences"][-1]["text"] = "여기에는 새로운 혼인과 혼인 5년 경과에 따른 집계 변화도 함께 반영되므로, 거주 규모와 그 증감은 구분해 살펴보겠습니다."
    i["sentences"][-1]["display_text"] = i["sentences"][-1]["text"]
    i["sentences"][-1]["anchor_string"] = "거주 규모와 그 증감"
    i["message"] = "같은 출발점의 두 지역 사례로 규모와 증감을 짧게 구분"
    i = shorten("I002", {"01", "02", "04"})
    i["message"] = "비슷한 전체 규모에도 초혼 구성이 다름을 한 사례로 설명"
    c = shorten("C001", {"02", "03", "04", "05"})
    c["message"] = "집계 범위·생활권·가격 비교 조건을 짧게 정리"
    return {"revision": facts["revision"], "source_paths": [f"{relroot}/{name}" for name in names] + [supplement_rel], "sources": facts["sources"], "director_supplement": supplement, "region_claims": {r["region_id"]: r["claims"] for r in facts["regions"]}, "open_research_issues": facts["open_issues"], "research_validation": validation, "research_handoff_status": handoff["status"], "source_note": suggestions["source_note"], "writer_original_source_review_performed": False, "writer_photo_pixel_review_performed": False, "script_gate": {"current_authorization": "기획·자료·대본 보강", "approval_target": "완성 원고와 대표 시안을 전달한 해당 새 버전", "user_new_script_approval": "pending", "tts_allowed": False, "main_render_allowed": False, "price_period_and_normalized_data_lock": "pending_parent"}}
