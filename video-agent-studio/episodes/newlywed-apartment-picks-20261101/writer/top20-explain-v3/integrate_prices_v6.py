"""Apply only the parent-locked v2 price packet to the writer's sentences."""
import hashlib
import json
import re
from copy import deepcopy


def integrate_prices(scenes, claims, versions, ep):
    paths = ["director/top20-explain-v3/price_panel_data.json", "research/top20-explain-v3/prices/final-api-20261103-v2/writer_price_values.json", "research/top20-explain-v3/prices/final-api-20261103-v2/methodology.json"]
    data = []
    for rel in paths:
        raw = (ep / rel).read_bytes()
        versions[rel] = {"sha256": hashlib.sha256(raw).hexdigest()}
        data.append(json.loads(raw.decode("utf-8-sig")))
    panel, writer, method = data
    assert writer["revision"] == method["revision"] == "final-api-20261103-v2"
    assert method["valid_area_rows"] == 14303
    by_id = {r["region_id"]: r for r in panel["regions"]}
    writer_by_id = {r["region_id"]: r for r in writer["regions"]}
    assert len(by_id) == len(writer_by_id) == 20
    assert sum(r["n"] for r in by_id.values()) == 14303
    assert min(by_id.values(), key=lambda r: r["median_manwon"])["region_id"] == "R10"
    assert max(by_id.values(), key=lambda r: r["median_manwon"])["region_id"] == "R06"
    claims["V3-PRICE-RANGE-20"] = {"status": "derived_from_parent_locked_v2", "statement": "20지역 중위값의 최소는미추홀구4억원·최대는강남구30억3,000만원", "input_path": paths[0], "input_claim_ids": ["V3_API_PRICE_R10", "V3_API_PRICE_R06"], "comparison_count": 20, "method": "20개 median_manwon 최소/최대 비교;단지 가격의최소최대 아님"}
    claims["V3-PRICE-METHOD"] = {"status": "parent_locked_v2_methodology", "statement": "2026-05-01~10-31 계약;2026-11-03 조회;83<=㎡<=85 양끝 포함;전체층;중개/직거래;표시 해제행만 제외;유효행n;10월 신고 진행", "input_path": paths[2], "methodology": method, "independent_XML_reaggregation": "부모의 전달 근거; writer가 원XML 재집계한 것으로 기록하지 않음"}
    source_path = ep.parents[2] / "analysis/newlywed_region_2024/수도권_신혼부부_순위.md"
    assert source_path.exists()
    versions[str(source_path)] = {"sha256": hashlib.sha256(source_path.read_bytes()).hexdigest()}
    claims["STAT-PUBLISHER"] = {"status": "user_corrected_original_source_metadata", "statement": "국가데이터처가 발표한2024년 신혼부부통계", "source_path": str(source_path), "source_url": "https://mods.go.kr/boardDownload.es?bid=11815&list_no=442387&seq=3#page=32"}
    for s in scenes:
        if s["scene_id"] == "O001":
            s["sentences"] = [x for x in s["sentences"] if x["sentence_id"] != "O001-01"]
        if s["scene_id"] == "O002":
            x = s["sentences"][0]
            x["text"] = "순위의 출처는 국가데이터처가 발표한 2024년 신혼부부통계입니다."
            x["display_text"] = x["text"]
            x["anchor_string"] = "국가데이터처가 발표한 2024년 신혼부부통계"
            x = next(x for x in s["sentences"] if x["sentence_id"] == "O002-02")
            x["text"] = "2024년 11월 1일 거주지를 기준으로, 혼인신고 후 5년이 지나지 않은 부부를 초혼과 재혼을 합쳐 쌍 단위로 비교합니다."
            x["display_text"] = x["text"]
            x["anchor_string"] = "2024년 11월 1일"
            x = next(x for x in s["sentences"] if x["sentence_id"] == "O002-06")
            x["text"] = "이후 입주와 이사로 거주 분포가 달라질 수 있어, 당시의 분포를 출발점으로 살펴보겠습니다."
            x["display_text"] = x["text"]
            x["anchor_string"] = "당시의 분포를 출발점"
            s["sentences"] = [x for x in s["sentences"] if x["sentence_id"] not in ["O002-03", "O002-04", "O002-05"]]
            original = next(x for x in s["sentences"] if x.get("slot_kind") == "price_period")
            intro = [
                ("07A", "가격은 2026년 5월부터 10월까지 계약된 아파트 매매 실거래를 2026년 11월 3일 조회한 자료입니다.", "2026년 5월부터 10월까지"),
                ("07B", "전용면적 83제곱미터 이상 85제곱미터 이하의 거래를 비교합니다.", "83제곱미터 이상 85제곱미터 이하"),
                ("07D", "10월 계약분은 신고가 진행 중이어서, 조회 뒤 추가 신고나 정정·해제에 따라 수치가 달라질 수 있습니다.", "10월 계약분은 신고가 진행 중"),
            ]
            replacements = []
            for suffix, text, anchor in intro:
                item = deepcopy(original)
                item.update({"sentence_id": f"O002-{suffix}", "text": text, "display_text": text, "reading_text": text, "claim_ids": ["V3-PRICE-METHOD"], "statement_type": "price_methodology", "anchor_string": anchor, "status": "complete_text_pending_user_script_approval", "onscreen_purpose": "2024 거주 통계와 별도로2026 가격 계약기간·조회일·집계조건/10월 신고시차를 설명", "display_notes": "조건과 연도는 분리하지 않고 표시.10월 신고 진행 설명은 도입 한 번만 낭독.", "reading_notes": "새 대본 승인 대기. 숫자 읽기와 표시문을 별도 유지."})
                item.pop("slot_kind", None)
                item.pop("required_fields", None)
                replacements.append(item)
            index = s["sentences"].index(original)
            s["sentences"][index:index + 1] = replacements
            x = next(x for x in s["sentences"] if x["sentence_id"] == "O002-09")
            x["text"] = "지역 중위값과 단지 사례는 범위가 다르므로, 각각의 거래 건수를 함께 보겠습니다."
            x["display_text"] = x["text"]
            x["anchor_string"] = "각각의 거래 건수"
            s["sentences"] = [x for x in s["sentences"] if x["sentence_id"] != "O002-09"]
        if s["scene_id"] == "C001":
            x = deepcopy(s["sentences"][0])
            text = "같은 조건의 지역 중위값은 미추홀구 4억원부터 강남구 30억3,000만원까지 넓게 분포했습니다."
            x.update({"sentence_id": "C001-01", "text": text, "display_text": text, "reading_text": text, "claim_ids": ["V3-PRICE-RANGE-20", "V3_API_PRICE_R10", "V3_API_PRICE_R06"], "statement_type": "derived_price_comparison", "anchor_string": "미추홀구 4억원부터 강남구 30억3,000만원까지", "onscreen_purpose": "20지역 중위값 최소/최대 범위를 회수하고 직장·예산의 생활권 지도 활용으로 연결"})
            s["sentences"].insert(0, x)
        if not s["region_id"]:
            continue
        r = by_id[s["region_id"]]
        w = writer_by_id[s["region_id"]]
        a, wa = r["representative"], w["representative"]
        assert r["n"] == w["n"] and r["median_manwon"] == w["median_manwon"]
        assert (a["n"], a["median_manwon"], a["apt_name"], a["legal_dong_name"]) == (wa["n"], wa["median_manwon"], wa["name"], wa["legal_dong_name"])
        assert r["scene_id"] == s["scene_id"]
        for cid, value in [(r["claim_id"], r), (a["claim_id"], a)]:
            claims[cid] = {"status": "parent_locked_v2_exact_value", "input_path": paths[0], "value": value, "methodology_path": paths[2], "writer_scope": "현재 패널과 v2 writer값 대조; 원XML·좌표 재검증은 부모 근거 승계"}
        label = "2024년 옛 서구 범위" if s["region_id"] == "R01" else r["region"]
        texts = [
            ("region_price_median", f"같은 조건으로 집계한 {label} 거래 {r['n']:,}건의 중위값은 {r['display_price']}입니다.", r["claim_id"], r["display_price"]),
            ("representative_complex_price", f"{a['legal_dong_name']}의 {a['apt_name']} 단지 사례는 같은 조건 {a['n']:,}건의 중위값이 {a['display_price']}입니다.", a["claim_id"], a["apt_name"]),
        ]
        if s["region_id"] == "R01":
            texts[1] = ("representative_complex_price", f"{a['legal_dong_name']}의 {a['apt_name']}는 같은 조건 {a['n']:,}건의 중위값이 {a['display_price']}입니다.", a["claim_id"], a["apt_name"])
        for kind, text, cid, anchor in texts:
            x = next(x for x in s["sentences"] if x.get("slot_kind") == kind)
            x.update({"text": text, "display_text": text, "reading_text": text, "claim_ids": [cid, "V3-PRICE-METHOD"], "statement_type": "parent_locked_price_fact", "anchor_string": anchor, "status": "complete_text_pending_user_script_approval", "display_notes": "부모 display_price를 반올림 없이 그대로 표시.지역n과 단지n을 별도로 표시하며 단지는 실제 동 이름을 유지.", "reading_notes": "정확값 낭독.해당 새 대본 승인 전 TTS 금지.", "onscreen_purpose": "지역 집계와 별도 단지 사례의 가격·n을 정확하게 구분"})
            x["price_role"] = x.pop("slot_kind")
            x.pop("required_fields", None)
        s["price_panel_data"] = r
        s["statistical_geography"]["current_price_geography"] = "2024 옛 서구 범위;현행 두 코드 전기간 응답 합산,구코드 미가산" if s["region_id"] == "R01" else r["region"]
        s["status"] = "complete_text_pending_user_script_approval"
        s["screen_beats"][-1].update({"status": "parent_locked_price_values_ready_for_preview", "anchor_string": r["display_price"], "region_price_anchor": r["display_price"], "complex_price_anchor": a["apt_name"], "region_n": r["n"], "complex_n": a["n"], "complex_dong": a["legal_dong_name"], "coordinate_status": a["coordinate_status"], "lat": a["lat"], "lng": a["lng"], "coordinate_source": a["coordinate_source"], "price_condition_label": "2026.05~10 계약 | 11.03 조회 | 83~85㎡ 양끝 포함 | 전층 | 중개+직거래 | 표시 해제행 제외", "region_display_price": r["display_price"], "complex_display_price": a["display_price"]})
        s["screen_beats"][-1]["action"] += f" 지역{r['display_price']}/n={r['n']} → {a['legal_dong_name']} {a['apt_name']} {a['display_price']}/n={a['n']}. 좌표는 부모 verified값 그대로; 원래 사진 장소와 별개 사례로 전환."
        case_beat = deepcopy(s["screen_beats"][-1])
        s["screen_beats"][-1].update({"sentence_ids": [f"{s['scene_id']}-20"], "purpose": "regional_price", "action": f"지역 집계 범위의 중위값{r['display_price']}와 지역n={r['n']}을 제시.2026.05~10/83~85㎡/전층/중개+직거래/표시해제 제외 조건 유지."})
        case_beat.update({"beat_id": f"{s['scene_id']}-B5", "sentence_ids": [f"{s['scene_id']}-21"], "purpose": "separate_complex_price_example", "anchor_string": a["apt_name"]})
        s["screen_beats"].append(case_beat)
        if s["region_id"] == "R02":
            additions = [
                ("22", "구 전체의 중위값과 잠실의 단지 사례는 가격 수준이 다릅니다.", [r["claim_id"], a["claim_id"]], "price_scope_comparison"),
                ("23", "송파구 안에서도 예산에 맞는 동과 단지를 따로 좁혀볼 필요가 있습니다.", [r["claim_id"], a["claim_id"]], "editorial_application"),
            ]
            for suffix, text, cids, kind in additions:
                x = deepcopy(s["sentences"][-1])
                x.update({"sentence_id": f"{s['scene_id']}-{suffix}", "text": text, "display_text": text, "reading_text": text, "claim_ids": cids, "statement_type": kind, "anchor_string": "가격 수준이 다릅니다" if suffix == "22" else "동과 단지를 따로", "onscreen_purpose": "지역/단지의 공간 범위와 집계구성 차이 설명;단지 프리미엄의 원인이나 미래 가격 주장 아님", "price_role": "price_scope_insight"})
                s["sentences"].append(x)
            s["screen_beats"].append({"beat_id": "S021-B6", "sentence_ids": ["S021-22", "S021-23"], "purpose": "regional_vs_complex_scope_insight", "action": "송파구 지역 중위21억8,500만원/n513과 잠실동 사례30억원/n9의 범위·집계 차이를 같은 화면에 회수.특정 단지 프리미엄 원인으로 설명하지 않음.", "anchor_string": "가격 수준이 다릅니다"})
        for i, b in enumerate(s["screen_beats"], 1):
            b["screen_switch_id"] = f"{s['scene_id']}-SW{i:02}"
    return {"panel_path": paths[0], "panel_sha256": versions[paths[0]]["sha256"], "writer_values_path": paths[1], "methodology_path": paths[2], "revision": method["revision"], "contract_period": method["contract_period"], "as_of_date": method["as_of_date"], "methodology": method, "region_count": 20, "complex_count": 20, "valid_area_rows": 14303, "parent_lock_received": True, "writer_original_xml_reaggregation_performed": False, "script_approval": "pending_new_v6", "tts_allowed": False, "render_allowed": False}


def reading_form(text, sino):
    text = re.sub(r"([0-9]+)억([0-9,]+)만원", lambda m: sino(m[1]) + " 억 " + sino(m[2].replace(",", "")) + " 만 원", text)
    text = re.sub(r"([0-9]+)억원", lambda m: sino(m[1]) + " 억 원", text)
    units = ["", "한", "두", "세", "네", "다섯", "여섯", "일곱", "여덟", "아홉"]
    tens = ["", "열", "스물", "서른", "마흔", "쉰", "예순", "일흔", "여든", "아흔"]
    def count(m):
        n = int(m[1].replace(",", ""))
        return ("스무" if n == 20 else (tens[n // 10] + units[n % 10]) if n < 100 else sino(n)) + " 건"
    text = re.sub(r"([0-9,]+)건", count, text)
    text = re.sub(r"([0-9]+)제곱미터", lambda m: sino(m[1]) + " 제곱미터", text)
    for a, b in {"GTX-A": "지티엑스 에이", "백현주공9단지": "백현주공 구 단지", "개포주공6단지": "개포주공 육 단지", "잠실2·3단지": "잠실 이 단지와 삼 단지", "고덕주공7단지": "고덕주공 칠 단지", "문래동6가": "문래동 육 가", "Y CITY(와이시티)": "와이시티", "e편한세상": "이편한세상", "미리내마을(롯데2)": "미리내마을 롯데 이", "우미린파크뷰1단지": "우미린파크뷰 일 단지", "별빛마을(건영)10": "별빛마을 건영 십", "현대1": "현대 일", "용현2단지금호타운": "용현 이 단지 금호타운", "상계2차중앙하이츠": "상계 이 차 중앙하이츠", "망포마을쌍용1차": "망포마을 쌍용 일 차", "효자촌(삼환)": "효자촌 삼환"}.items():
        text = text.replace(a, b)
    return text


def finalize_packet(packet, price_payload):
    packet.update({"status": "COMPLETE_SCRIPT_DRAFT_AWAITING_NEW_USER_APPROVAL", "price_input_lock": price_payload, "price_window": {"start": "2026-05-01", "end": "2026-10-31", "retrieved_at": "2026-11-03", "reporting_complete": False, "october_reporting_ongoing": True}, "price_freshness_note": "부모LOCK v2·14303유효행;정상행 보존,표시해제행만 제외.원XML 재집계는 부모 근거 승계.", "integration_rule": "최종 특징/부모LOCK 가격v2 통합 완료.완성원고·대표시안 전달 및 새 대본 사용자 승인 전 TTS/본편렌더 금지."})
    packet["script_gate"]["price_period_and_normalized_data_lock"] = "parent_locked_final-api-20261103-v2"
    packet["display_policy"]["statistical_source"] = "O002에서 국가데이터처 발표자료명·기준일 설명.지역별 본문에 반복 출처 footer 금지."
    for s in packet["scenes"]:
        if not s["region_id"] and not s["screen_beats"]:
            s["screen_beats"] = [{"beat_id": f"{s['scene_id']}-B1", "screen_switch_id": f"{s['scene_id']}-SW01", "sentence_ids": [x["sentence_id"] for x in s["sentences"]], "purpose": s["message"], "action": "문장별 앵커에 맞춘 설명용 지도/데이터 비교; 실제 음성 전 초 단위 고정 금지."}]
        if s["scene_id"] == "O002":
            s["screen_beats"] = [{"beat_id": f"O002-B{n}", "screen_switch_id": f"O002-SW{n:02}", "sentence_ids": [x["sentence_id"] for x in s["sentences"] if (2 if "-07" in x["sentence_id"] else 3 if x["sentence_id"] in ["O002-08", "O002-09"] else 1) == n], "purpose": purpose, "action": purpose} for n, purpose in [(1, "국가데이터처2024 통계출처·대상·한계"), (2, "2026 가격 계약기간·조회일·집계조건·10월 신고시차"), (3, "중위값과 지역/단지 범위·각 n 정의")]]
        for i, b in enumerate(s["screen_beats"], 1):
            b.setdefault("screen_switch_id", f"{s['scene_id']}-SW{i:02}")
        for x in s["sentences"]:
            x["status"] = "complete_text_pending_user_script_approval"
            number = 4 if x.get("price_role") == "region_price_median" else 5 if x.get("price_role") == "representative_complex_price" else 3 if s["region_id"] and x["material_type"] == "real_photo" else 1 if x["sentence_id"].endswith("-01") or not s["region_id"] else 2
            if s["scene_id"] == "O002":
                number = 2 if "-07" in x["sentence_id"] else 3 if x["sentence_id"] in ["O002-08", "O002-09"] else 1
            x["screen_switch_id"] = f"{s['scene_id']}-SW{number:02}"
            if x.get("price_role") == "price_scope_insight":
                x["screen_switch_id"] = f"{s['scene_id']}-SW06"
        if s["scene_id"] == "O002":
            s["screen_beats"][0]["internal_definition"] = packet["claim_registry"]["DEF-2024"]
            s["screen_beats"][1]["on_screen_conditions"] = "2026.05~10 계약·2026.11.03 조회·83~85㎡ 양끝 포함·전체 층·중개+직거래·표시 해제행 제외·n=유효 기록 수"
    packet["reading_display_mapping"] = [{"sentence_id": x["sentence_id"], "display_text": x["display_text"], "reading_text": x["reading_text"], "reason": "숫자/금액/고유명사 읽기 정규화;표시문 원값 보존"} for s in packet["scenes"] for x in s["sentences"] if x["display_text"] != x["reading_text"]]
