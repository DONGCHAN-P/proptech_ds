"""Writer-owned initial v6 scaffold. No synthesis, remote access, or shared-state writes."""
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

OWN = Path(__file__).resolve().parent
sys.path.insert(0, str(OWN))
EP = OWN.parents[1]


def read(rel):
    return json.loads((EP / rel).read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(name, data):
    (OWN / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


top = read("research/top20-8min-v2/top20.json")
facts = read("research/top20-8min-v2/combined_facts.json")
old = read("director/top20-enhance-v2/scene_proposals_v5.json")
by_id = {r["region_id"]: r for r in facts["regions"]}
old_scenes = {s["scene_id"]: s for s in old["scenes"]}
inputs = [
    "director/top20-enhance-v2/script_v5.md",
    "director/top20-enhance-v2/scene_proposals_v5.json",
    "research/top20-8min-v2/combined_facts.json",
    "research/top20-8min-v2/top20.json",
    "director/top20-explain-v3/requirements.json",
    "director/top20-explain-v3/제작계획.md",
]
versions = {p: {"sha256": sha(EP / p)} for p in inputs}
claims = {}
for r in facts["regions"]:
    for c in r.get("all_claim_records", []):
        claims[c["claim_id"]] = {**c, "input_path": "research/top20-8min-v2/combined_facts.json"}
    rid = r["region_id"]
    for suffix, field in [("TOTAL", "newlywed_couples"), ("FIRST", "first_marriage_couples"), ("REMARRIED", "remarried_couples")]:
        claims[f"T2024-{rid}-{suffix}"] = {
            "statement": f"{r['region']} / {field} = {r[field]}",
            "status": "reused_verified_input",
            "source_path": "research/top20-8min-v2/top20.json",
            "source_url": r["source_url"],
            "reference_date": "2024-11-01",
            "verification_scope": "기존 검증 수치 재사용; 이번 원표 재열람 아님",
        }
    if r.get("comparison_available"):
        claims[f"CALC-{rid}-YOY"] = {
            "status": "derived_from_reused_verified_input",
            "inputs": {k: r[k] for k in ["count2023", "count2024", "change_couples", "change_percent_display"]},
            "source_path": "research/top20-8min-v2/combined_facts.json",
            "formula": "(count2024-count2023)/count2023*100; display one decimal",
            "causal_decomposition_performed": False,
        }

claims.update({
    "DEF-2024": {"status": "reused_verified_old_core", "statement": "2024-11-01 기준; 혼인신고 후 5년 미경과·혼인관계 유지·적어도 한 명 국내 거주; 초혼·재혼 포함; 단위 쌍", "source_path": "director/top20-enhance-v2/scene_proposals_v5.json", "scene_id": "O002"},
    "SCOPE-53": {"status": "reused_verified_input", "statement": "2024 통계구역 수도권 53개 구 중 전체 신혼부부 수 TOP20", "source_path": "research/top20-8min-v2/top20.json"},
    "STAT-PUBLISHER": {"status": "reused_source_metadata", "statement": "통계청 2024년 신혼부부통계", "source_path": "research/top20-8min-v2/combined_facts.json", "source_urls": sorted({r["source_url"].split("#")[0] for r in facts["regions"]})},
    "STOCK-MECHANISM": {"status": "reused_verified_old_core", "statement": "혼인 5년 경과에 따른 집계 이탈과 신규 혼인 등이 함께 반영됨; 순유입·선호·주택가격 원인으로 분해하지 않음", "source_path": "director/top20-enhance-v2/scene_proposals_v5.json", "scene_id": "I001"},
    "DIRECTION-19": {"status": "derived_from_reused_verified_input", "statement": "동일 범위 비교 가능 19개 지역 중 증가 6곳·감소 13곳", "source_path": "research/top20-8min-v2/combined_facts.json", "json_pointer": "/summary"},
    "COMPOSITION-PAIR": {"status": "derived_from_reused_verified_input", "statement": "영통/권선 전체 차이59쌍; 초혼7634/6746쌍; 재혼733/1563쌍", "source_path": "research/top20-8min-v2/top20.json", "region_ids": ["R12", "R13"], "rounding_note": "원표의 전체·초혼·재혼은 개별 공표값; 초혼+재혼을 전체와 정확히 일치하는 누적 막대로 만들지 않음"},
    "PROVINCE-COUNTS": {"status": "derived_from_reused_verified_input", "statement": "TOP20 지역 수 서울9·경기6·인천5", "source_path": "research/top20-8min-v2/combined_facts.json", "json_pointer": "/summary/province_district_counts"},
    "METHOD-MEDIAN": {"status": "statistical_definition", "statement": "거래금액을 정렬했을 때의 가운데 값; 짝수 표본은 가운데 두 값의 산술평균; 거래건 기준, 단지별 중위값의 중위값 아님"},
})

scenes = []


def scene(sid, title, message, seconds, rid=None, materials=None):
    s = {"scene_id": sid, "region_id": rid, "rank": by_id[rid]["rank"] if rid else None,
         "title": title, "message": message, "sentences": [], "material_types": materials or ["data_chart"],
         "script_revision": "v6", "status": "scaffold_pending_verified_packets", "estimated_duration_s": seconds,
         "duration_basis": "producer_planning_estimate_only; includes unfilled slots; not a measured reading",
         "start_s": None, "end_s": None, "actual_duration_s": None, "audio_revision": None,
         "timing_basis": "estimate_not_audio_aligned", "timing_locked": False,
         "asset_ids": [], "asset_status": "proposal_only_no_new_assets_reviewed", "screen_beats": []}
    scenes.append(s)
    return s


def sentence(s, suffix, text, cids=None, typ="verified_fact", anchor=None, purpose="", note="", reading=None, material="data_chart"):
    item = {"sentence_id": f"{s['scene_id']}-{suffix}", "text": text,
            "claim_ids": cids or [], "statement_type": typ,
            "display_text": text, "reading_text": reading or text,
            "display_notes": note or "숫자·단위·고유명사를 의미 단위로 보존",
            "reading_notes": "합니다/입니다의 평서문. 숫자 읽기는 pronunciation_dictionary를 적용하며 표시문에 역전사하지 않음.",
            "onscreen_purpose": purpose, "anchor_string": anchor or text,
            "material_type": material, "visual_role": "explanation",
            "status": "ready_for_parent_text_review", "narration_ready": False}
    s["sentences"].append(item)
    return item


def pending(s, suffix, kind, requirement, fields, owner):
    s["sentences"].append({
        "sentence_id": f"{s['scene_id']}-{suffix}", "text": None, "claim_ids": [],
        "statement_type": "pending_verified_fact_slot", "slot_kind": kind,
        "display_text": None, "reading_text": None, "anchor_string": None,
        "display_notes": "미확인 값을 화면·자막에 표시하지 않음. 검증 패킷 통합 후 실제 숫자와 조건을 표시.",
        "reading_notes": "미작성 슬롯이며 낭독 대상이 아님. 확정 전 TTS 입력 금지.",
        "onscreen_purpose": requirement, "required_fields": fields,
        "material_type": "map" if "price" in kind or kind == "regional_feature" else "editorial_card",
        "visual_role": "explanation", "status": "pending_final_verified_bundle", "narration_ready": False,
        "input_owner": owner,
    })


o = scene("O001", "거주 순위에 생활권과 가격을 연결합니다", "거주 규모·지역 특징·가격이라는 비교 축을 안내", 20, materials=["map", "real_photo"])
sentence(o, "01", "신혼부부가 많이 사는 지역을 살펴보면, 주거지를 비교할 출발점을 찾을 수 있습니다.", typ="editorial_framing", anchor="주거지를 비교할 출발점", purpose="수도권 전체에서 이번에 설명하는 지역들을 읽을 수 있는 크기로 제시", material="map")
sentence(o, "02", "오늘은 수도권 53개 구 가운데 신혼부부 거주 수 상위 스무 곳을 20위부터 1위까지 살펴보겠습니다.", ["SCOPE-53"], anchor="20위부터 1위까지", purpose="53개 구라는 모집단과 TOP20의 범위를 구분", material="map")
sentence(o, "03", "각 지역의 주거 환경과 실제 랜드마크를 짚고, 같은 조건의 아파트 거래가격을 지도에 연결하겠습니다.", typ="editorial_plan", anchor="아파트 거래가격을 지도에 연결", purpose="지역 윤곽→실제 장소→가격으로 이어지는 설명 순서를 예고", material="map")

o = scene("O002", "2024년 거주 통계와 가격의 시점", "통계 출처·대상·2024 한계와 가격의 별도 기준을 처음에 설명", 74, materials=["data_chart", "editorial_card"])
sentence(o, "01", "순위의 출처는 통계청의 2024년 신혼부부통계입니다.", ["STAT-PUBLISHER"], anchor="통계청의 2024년 신혼부부통계", purpose="자료명·기관·원문 링크를 도입부에 한 번 제시", note="통계 출처를 소개하는 이 장면에 자료명을 표시. 지역별 화면에 동일 출처 꼬리표를 반복하지 않음.")
sentence(o, "02", "기준일은 2024년 11월 1일이며, 당시 행정구역을 기준으로 비교합니다.", ["DEF-2024", "SCOPE-53"], anchor="2024년 11월 1일", purpose="거주 통계의 기준일과 구역 기준을 같은 줄로 제시")
sentence(o, "03", "대상은 혼인신고 후 5년이 지나지 않았고 혼인관계를 유지하며, 부부 중 적어도 한 명이 국내에 거주하는 부부입니다.", ["DEF-2024"], anchor="혼인신고 후 5년", purpose="집계 대상을 짧은 정의 문장으로 안내")
sentence(o, "04", "초혼과 재혼을 포함한 전체 수이며, 단위는 쌍입니다.", ["DEF-2024"], anchor="단위는 쌍", purpose="세대·명·혼인신고 건수와 혼동하지 않도록 집계 단위를 제시")
sentence(o, "05", "이 순위는 2024년의 거주 현황을 보여줍니다.", ["DEF-2024"], anchor="2024년의 거주 현황", purpose="자료의 관측 시점을 명확히 고정")
sentence(o, "06", "그 이후의 입주와 이사, 행정구역 개편까지 반영한 현재의 순위로 읽을 수는 없습니다.", ["DEF-2024"], typ="data_limitation", anchor="현재의 순위로 읽을 수는 없습니다", purpose="2024 관측값 이후 구간을 별도 영역으로 표시; 인구 이동량·새 순위를 만들어 표시하지 않음")
pending(o, "07", "price_period", "거주 순위의 2024 기준과 별개로, 가격의 실제 계약기간·조회일·완결월·면적·취소 처리·실거래 여부를 확정 문장으로 삽입", ["contract_start", "contract_end", "retrieved_at", "complete_months", "area_min_sqm", "area_max_sqm", "cancellation_policy", "statistic", "raw_max_contract_date", "coverage_caveat"], "research/top20-explain-v3/prices")
sentence(o, "08", "중위값은 거래금액을 낮은 순서대로 놓았을 때 가운데에 해당하는 값입니다.", ["METHOD-MEDIAN"], typ="method_definition", anchor="가운데에 해당하는 값", purpose="정렬한 거래 점의 가운데를 표시; 실제 지역 가격이 확정되기 전 수치 없는 방법 도해", note="짝수 표본은 가운데 두 값의 평균. 예시값을 실제 지역의 거래로 오인하게 표시하지 않음.")
sentence(o, "09", "지역의 거래 수준과 대표 단지의 가격은 구분하고, 각각의 거래 건수도 함께 보겠습니다.", typ="editorial_method", anchor="각각의 거래 건수", purpose="지역 중위값과 단지 중위값을 나란히 두되 공간 범위와 표본을 분리")

# Only statements supported by the designated, already verified old-core packets.
regional = {
    "R20": [("원미구는 2024년 1월 1일 다시 설치된 구입니다.", ["R20-F02"], "2024년 1월 1일"), ("중동신도시 개발과 함께 조성된 부천중앙공원은 원미구 소향로에 있습니다.", ["R20-F01"], "부천중앙공원")],
    "R19": [("중랑구 묵동에는 중랑장미공원이 있습니다.", ["R19-F01"], "중랑장미공원")],
    "R18": [("동백호수공원은 호수 주변 산책로를 갖춘 기흥구의 생활 여가 공간입니다.", ["R18-F01"], "동백호수공원"), ("용인시 안내에는 신갈천 자전거도로와의 연결도 소개돼 있습니다.", ["R18-F02"], "신갈천 자전거도로")],
    "R17": [("송도동의 센트럴파크는 해수를 이용한 공원으로, 보트하우스와 산책정원 등이 있습니다.", ["R17-F01"], "센트럴파크")],
    "R16": [("소래습지생태공원은 갯벌과 습지, 탐방데크를 갖춘 남동구의 생태공원입니다.", ["R16-F01"], "소래습지생태공원"), ("공원에는 폐염전을 활용한 염전 학습장도 있습니다.", ["R16-F02"], "염전 학습장")],
    "R15": [("구로동과 금천구 가산동에 걸친 G밸리는 산업지역입니다.", ["R15-F01"], "G밸리"), ("구로동 G타워에는 이 지역의 산업을 다루는 G밸리산업박물관이 있습니다.", ["R15-F02"], "G밸리산업박물관")],
    "R14": [("진관동에는 은평뉴타운의 주거 단지와 은평한옥마을이 있습니다.", ["R14-F01", "R14-F02"], "은평뉴타운"), ("한옥마을은 은평구 진관동의 실제 장소로, 지역을 이해하는 한 가지 기준점입니다.", ["R14-F02"], "은평구 진관동")],
    "R13": [("금곡동에는 종합체육시설인 서수원칠보체육관이 있습니다.", ["R13-F01"], "서수원칠보체육관")],
    "R12": [("영통구 하동의 광교호수공원에는 수변 보행데크와 커뮤니티 숲 등이 조성돼 있습니다.", ["R12-F01", "R12-F02"], "광교호수공원")],
    "R11": [("화랑대 철도공원 안에는 전시실과 야외무대를 갖춘 경춘선숲길 갤러리가 있습니다.", ["R11-F01"], "경춘선숲길 갤러리")],
    "R10": [("수봉산 자락의 수봉공원에는 자연학습 공간과 체육시설, 문화예술시설이 있습니다.", ["R10-F01"], "수봉공원")],
    "R09": [("삼평동에는 판교테크노밸리의 창업 지원시설인 스타트업 캠퍼스가 있습니다.", ["R09-F02"], "스타트업 캠퍼스")],
    "R08": [("여의도한강공원에는 서울시가 운영 상태로 안내하는 공공 체육시설이 있습니다.", ["R08-F01"], "여의도한강공원")],
    "R07": [("둔촌동의 일자산 자연공원에는 잔디광장과 놀이터, 운동시설이 있습니다.", ["R07-F01"], "일자산 자연공원"), ("허브천문공원에는 허브원과 전망데크, 산책 공간이 마련돼 있습니다.", ["R07-F02"], "허브천문공원")],
    "R06": [("강남구는 양재천의 영동6교에서 대치교까지 소단길을 연결하는 공사를 2022년 12월 마쳤다고 발표했습니다.", ["R06-F01"], "영동6교에서 대치교까지")],
    "R05": [("부평문화의거리는 지하상가와 전통시장 등 주변 상권이 연결되는 보행 중심의 상업 공간입니다.", ["R05-F02"], "부평문화의거리"), ("부평역과 백운역 사이의 부평공원에는 산책과 운동을 위한 공간도 있습니다.", ["R05-F01"], "부평공원")],
    "R04": [("마곡의 서울식물원에는 열대와 지중해 기후를 주제로 한 온실 전시가 있습니다.", ["R04-F01"], "서울식물원")],
    "R03": [("스타필드 고양은 고양시 덕양구 고양대로에 있는 상업시설입니다.", ["R03-F03"], "스타필드 고양")],
    "R02": [("석촌호수는 동호와 서호, 산책로를 갖춘 송파구의 도심 호수공원입니다.", ["R02-F01"], "석촌호수")],
    "R01": [("2024년 서구의 범위는 2026년 7월 1일 서해구와 검단구로 나뉘었습니다.", ["R01-ADM"], "서해구와 검단구"), ("청라호수공원은 이 옛 서구 안에 있는 생활 여가 공간입니다.", ["R01-F01", "R01-ADM"], "청라호수공원")],
}

queries = {
    "R20": "중동·상동 등 실제 주거 생활권과 아파트 형성의 차이. 부천중앙공원이 속한 범위를 구체화.",
    "R19": "묵동 등 구 내부 주거권의 특징 1~2개. 중랑장미공원 소재지와 실제 주거·생활 동선을 연결.",
    "R18": "기흥구 안의 생활권별 주거 성격 1~2개. 동백의 주거와 동백호수공원 관계를 확인.",
    "R17": "송도와 다른 연수구 생활권의 주거 성격 차이. 센트럴파크가 구 전체를 대표하지 않도록 구체화.",
    "R16": "남동구 주거 생활권별 특징 1~2개. 소래습지 인근권과 다른 권역을 구분.",
    "R15": "G밸리 업무권과 구 내부 주거권의 관계. 모든 구로구 주택을 직주근접으로 묶지 않는 공간 설명.",
    "R14": "진관동 은평뉴타운과 다른 구 내부 주거권의 특성. 확인된 주택 유형·형성 시점 중심.",
    "R13": "권선구 주거 생활권과 금곡동 체육관 주변 주거 맥락. 호매실 여부는 신규 공식 근거 확인 후 채택.",
    "R12": "영통구 내부 주거권 특성 1~2개. 광교호수공원 하동 구간과 실제 비교단지 생활권을 구분.",
    "R11": "노원구 주거권의 형성·주택 유형·연식 특성. 공릉동 공원과 노원구 전체를 구분.",
    "R10": "미추홀구 주거 유형·생활권 특성. 수봉공원 소재권과 대표 단지의 실제 주거 맥락을 구분.",
    "R09": "분당구의 주거권과 판교 업무권 관계. 분당구 전체를 판교로 설명하지 않는 지역 구분.",
    "R08": "여의도 외 주거 생활권도 포함한 영등포구 주거 특징. 업무시설의 실제 운영·위치가 확인된 내용만 채택.",
    "R07": "강동구 주거권·아파트 형성의 차이 1~2개. 일자산과 허브천문공원의 실제 소재권을 구분.",
    "R06": "강남구 내부 주거 성격·주택 유형·연식의 차이. 양재천 구간과 대표 단지의 위치 관계를 확인.",
    "R05": "부평구의 주거·상권 관계 1~2개. 부평문화의거리와 다른 주거권을 구분.",
    "R04": "강서구의 주거 생활권·주택 형성 특성. 마곡의 주거·업무·식물원 관계는 신규 공식 근거로 확인.",
    "R03": "덕양구 안의 주거 생활권 특성 1~2개. 스타필드 고양이 있는 권역과 다른 주거권을 구분.",
    "R02": "송파구 주거 생활권·아파트 형성의 차이. 석촌호수 인근과 다른 권역을 구분.",
    "R01": "청라·검단 등 옛 서구 내부 주거 특성과 현재 두 구의 경계. 현재 가격을 2024 옛 구에 잘못 붙이지 않음.",
}

for tr in reversed(top["regions"]):
    rid, sid = tr["region_id"], tr["scene_id"]
    r = by_id[rid]
    region = "2024년 당시 인천 서구" if rid == "R01" else (r["province"] + " " + r["region"] if r["province"] in ["서울", "인천"] else r["region"])
    s = scene(sid, f"{r['rank']}위 {region}", "거주 규모 → 주거·생활권 특징 → 실제 랜드마크 → 지역 거래 중위값·대표 단지", 40 if rid == "R01" else 33, rid, ["map", "real_photo", "data_chart"])
    s["statistical_geography"] = {"reference_date": "2024-11-01", "label": region, "current_price_geography": None}
    sentence(s, "01", f"{r['rank']}위는 {region}, {r['newlywed_couples']:,}쌍입니다.", [f"T2024-{rid}-TOTAL", "SCOPE-53"], anchor=f"{r['newlywed_couples']:,}쌍", purpose="이번 지역의 윤곽·이름·거주 수를 함께 제시. 수를 현재 가격과 같은 연도의 값처럼 배치하지 않음", material="map")
    pending(s, "02", "regional_feature", queries[rid], ["1_to_2_housing_or_living_area_features", "verified_claim_ids", "source_url", "evidence_location", "reference_date", "facility_or_project_status", "actual_landmark_relation"], "research/top20-explain-v3/regions")
    for n, (text, cids, anchor) in enumerate(regional[rid], 3):
        sentence(s, f"{n:02}", text, cids, anchor=anchor, purpose=f"{region}의 실제 장소·소재 범위를 설명. 확보 사진이 해당 발화 장소와 일치할 때만 사용", material="map" if rid == "R01" and n == 3 else "real_photo")
    pending(s, "20", "region_price_median", "주거·랜드마크 설명 다음에 동일 전용면적 범위의 지역 실거래 중위값·기간·n을 한 문장 또는 두 문장으로 설명", ["actual_region_label", "current_boundary_or_harmonized_boundary", "contract_start", "contract_end", "retrieved_at", "apartment_only", "area_min_sqm", "area_max_sqm", "cancellation_policy", "transaction_count", "median_krw", "collection_completeness", "claim_ids"], "research/top20-explain-v3/prices")
    pending(s, "21", "representative_complex_price", "지역 중위값과 별개로 대표 단지명·동일 조건 단지 가격·n·선정 근거를 설명", ["complex_name", "complex_id", "address", "selection_reason", "same_window_and_area", "statistic_type", "price_krw", "transaction_count", "floor_scope", "coordinate_status", "verified_coordinates_or_no_pin", "claim_ids"], "research/top20-explain-v3/prices")
    s["screen_beats"] = [
        {"beat_id": f"{sid}-B1", "sentence_ids": [f"{sid}-01"], "purpose": "scope_and_resident_count", "action": "구 윤곽과 지역명·2024 거주 수를 안정적으로 제시", "asset_type": "map", "anchor_string": f"{r['newlywed_couples']:,}쌍"},
        {"beat_id": f"{sid}-B2", "sentence_ids": [f"{sid}-02"], "purpose": "housing_and_living_area", "action": queries[rid], "asset_type": "map", "anchor_string": None, "status": "pending_final_verified_bundle"},
        {"beat_id": f"{sid}-B3", "sentence_ids": [x["sentence_id"] for x in s["sentences"] if x.get("material_type") == "real_photo"], "purpose": "actual_landmark_context", "action": "해당 장소의 실사와 같은 장소를 가리키는 지도를 연결. 계절·촬영일·사진 크레딧은 개별 자산 기록을 유지.", "asset_type": "real_photo", "anchor_string": regional[rid][-1][2]},
        {"beat_id": f"{sid}-B4", "sentence_ids": [f"{sid}-20", f"{sid}-21"], "purpose": "regional_and_complex_price", "action": "지역 중위값을 실제 집계구역에 연결하고 대표 단지는 검증 좌표가 있을 때만 핀으로 연결. 계약기간·면적·실거래·중위값·각 n을 유지.", "asset_type": "map", "anchor_string": None, "status": "pending_final_verified_bundle"},
    ]
    s["map_requirements"] = {"arbitrary_coordinates_allowed": False, "geography_lock_required": True, "repeated_zoom": False, "current_region_locator": True, "price_conditions_visible": ["actual_region", "contract_period", "area_range", "statistic", "cancellation_policy", "region_n", "complex_n"], "special_geography_note": "옛 서구의 순위와 현재 서해구·검단구 가격을 분리. 집계 방식이 검증된 경우에만 통합 중위값 표시." if rid == "R01" else "통계 구역과 가격 집계 구역의 일치 확인 필요"}
    s["photo_requirements"] = {"old_binding_reused_automatically": False, "narrated_landmark_statements": [{"text": text, "claim_ids": ids} for text, ids, _ in regional[rid]], "candidates_from_verified_old_facts": r.get("image_suggestions", []), "candidate_caution": "이전 후보는 이번 발화 장소와 다를 수 있음. 특히 덕양구 스타필드·분당구 스타트업 캠퍼스는 이전 공원 사진에 자동 연결 금지.", "status": "pixel_and_license_verification_owned_by_visual_or_parent", "fallback": "사진 권리·장소가 맞지 않으면 출처를 확인한 공간 자료 지도에서 동일 설명을 수행"}
    if rid == "R16":
        i = scene("I001", "거주 규모와 전년 변화", "같은 출발점의 두 지역이 반대 방향으로 변한 사례와 집계의 의미", 36)
        sentence(i, "01", "기흥구와 연수구는 2023년 신혼부부 수가 각각 7,797쌍으로 같았습니다.", ["R18-C2023", "R17-C2023"], anchor="각각 7,797쌍", purpose="두 지역의 2023 값과 같은 출발점을 정렬")
        sentence(i, "02", "2024년에는 기흥구가 111쌍 줄고, 연수구는 78쌍 늘었습니다.", ["CALC-R18-YOY", "CALC-R17-YOY"], anchor="111쌍 줄고", purpose="2023→2024 변화량만 같은 축으로 비교")
        sentence(i, "03", "이번 스무 곳 중 같은 범위로 전년과 비교할 수 있는 열아홉 곳에서는 여섯 곳이 늘고 열세 곳이 줄었습니다.", ["DIRECTION-19"], anchor="여섯 곳이 늘고 열세 곳이 줄었습니다", purpose="비교 가능 지역 수19를 명시하고 원미구를 변화 비교에서 제외")
        sentence(i, "04", "새로 혼인한 부부가 집계에 들어오고, 혼인 5년이 지난 부부가 빠지는 변화도 함께 반영됩니다.", ["STOCK-MECHANISM"], anchor="혼인 5년이 지난 부부", purpose="거주 통계의 집계 진입·이탈을 도해; 실제 순유입 인원으로 표시하지 않음")
        sentence(i, "05", "따라서 이 수의 증감을 이사 수요나 지역 선호의 변화 하나로 설명할 수는 없습니다.", ["STOCK-MECHANISM"], typ="data_limitation", anchor="변화 하나로 설명할 수는 없습니다", purpose="원인 분석 미실시의 한계를 단정적 원인 문장 없이 전달")
    if rid == "R11":
        i = scene("I002", "전체 수와 부부의 구성", "전체 규모가 비슷한 권선·영통도 초혼·재혼 구성이 다름", 35)
        sentence(i, "01", "수원 영통구와 권선구의 전체 신혼부부 수 차이는 59쌍입니다.", ["COMPOSITION-PAIR"], anchor="59쌍", purpose="두 구의 전체 공표값을 나란히 표시")
        sentence(i, "02", "초혼 부부는 영통구 7,634쌍, 권선구 6,746쌍입니다.", ["T2024-R12-FIRST", "T2024-R13-FIRST"], anchor="초혼 부부", purpose="전체 막대와 별도로 초혼 값 두 개를 비교")
        sentence(i, "03", "재혼 부부는 영통구 733쌍, 권선구 1,563쌍으로 권선구가 더 많습니다.", ["T2024-R12-REMARRIED", "T2024-R13-REMARRIED"], anchor="재혼 부부", purpose="재혼 값 두 개를 같은 범주에서 비교. 초혼+재혼을 전체와 일치하는 누적 막대로 만들지 않음")
        sentence(i, "04", "전체 수가 비슷해도 어떤 부부를 포함하는지에 따라 지역의 모습은 달라집니다.", ["COMPOSITION-PAIR"], typ="editorial_interpretation", anchor="어떤 부부를 포함하는지", purpose="동일 집계 기준으로 비교한다는 결론으로 닫음")
    if rid == "R06":
        i = scene("I003", "수도권 안의 서로 다른 주거 후보", "서울·경기·인천 분포를 짧게 정리하고 상위5곳으로 연결", 15, materials=["map"])
        sentence(i, "01", "이번 상위 스무 곳은 서울 아홉 곳, 경기 여섯 곳, 인천 다섯 곳입니다.", ["PROVINCE-COUNTS"], anchor="서울 아홉 곳", purpose="TOP20에 해당하는 구만 지도에서 구분. 전체 신혼부부 비중으로 바꾸지 않음", material="map")
        sentence(i, "02", "이제 1만 쌍을 넘는 상위 다섯 곳의 생활권과 거래 수준을 이어서 살펴보겠습니다.", ["T2024-R05-TOTAL"], typ="editorial_transition", anchor="상위 다섯 곳", purpose="상위5지역 구간으로 설명을 연결", material="map")

c = scene("C001", "주거지를 비교하는 기준", "과거 거주 규모·현재 비교조건·생활권을 구분해 마무리", 35, materials=["map", "data_chart"])
sentence(c, "01", "2024년 거주 규모 1위인 옛 서구는 전년보다 1.3퍼센트 줄었고, 강남구는 9.4퍼센트 늘었습니다.", ["T2024-R01-TOTAL", "CALC-R01-YOY", "CALC-R06-YOY"], anchor="거주 규모 1위", purpose="거주 규모와 전년 변화를 다른 축으로 마지막 한 번 비교")
sentence(c, "02", "거주 규모와 증감, 부부의 구성은 서로 다른 정보를 제공합니다.", ["STOCK-MECHANISM", "COMPOSITION-PAIR"], typ="editorial_interpretation", anchor="서로 다른 정보", purpose="기존 통계 분석을 세 가지 기준으로 짧게 닫음")
sentence(c, "03", "주거지를 좁힐 때에는 두 사람의 직장 위치와 필요한 면적, 예산을 생활권 지도에 함께 놓고 비교하는 방식이 유용합니다.", typ="editorial_application", anchor="직장 위치와 필요한 면적, 예산", purpose="지금까지 설명한 실제 생활권을 비교 기준에 연결", material="map")
sentence(c, "04", "가격을 비교할 때에는 지역과 단지의 범위를 구분하고, 같은 계약기간과 면적 조건, 거래 건수를 확인해야 합니다.", typ="editorial_method", anchor="같은 계약기간과 면적 조건", purpose="화면에서 유지한 가격 비교 조건을 마무리에 연결")
sentence(c, "05", "이어지는 지역 비교도 함께 살펴보실 분들은 구독과 좋아요를 부탁드립니다.", typ="editorial_cta", anchor="구독과 좋아요", purpose="현재 채널 CTA 양식으로 마무리. 후속 영상 일정·특정 단지 수익을 약속하지 않음")
e = scene("E001", "마지막 발화 뒤 여백", "실제 발화 끝을 확인한 뒤 CTA 화면 유지", 3, materials=["editorial_card"])
e["status"] = "silent_outro_proposal"
e["screen_beats"] = [{"beat_id": "E001-B1", "purpose": "silent_closing_hold", "action": "실제 마지막 발화 종료 후 최소3초 확보. 빈 흰 자막 박스는 숨김. 실제 음성 전에는 시작 시각 고정 금지.", "anchor_string": None}]

from integrate_features_v6 import integrate_features

feature_payload = integrate_features(scenes, claims, versions, EP)
from integrate_prices_v6 import integrate_prices, reading_form, finalize_packet
price_payload = integrate_prices(scenes, claims, versions, EP)

# Add full-sentence reading strings for numbers already fixed in the designated inputs.
digit = "영일이삼사오육칠팔구"


def sino(n):
    n = int(n)
    if n == 0:
        return "영"
    out = ""
    for unit, label in [(10000, "만"), (1000, "천"), (100, "백"), (10, "십"), (1, "")]:
        q, n = divmod(n, unit)
        if q:
            out += ("" if q == 1 and unit in [1000, 100, 10] else digit[q]) + label
    return out


for s in scenes:
    for x in s["sentences"]:
        if x["text"] is None:
            continue
        t = x["text"]
        t = re.sub(r"([0-9,]+)쌍", lambda m: sino(m[1].replace(",", "")) + " 쌍", t)
        t = re.sub(r"([0-9]+)위", lambda m: sino(m[1]) + " 위", t)
        t = re.sub(r"([0-9]+)년", lambda m: sino(m[1]) + " 년", t)
        t = re.sub(r"([0-9]+)월", lambda m: sino(m[1]) + " 월", t)
        t = re.sub(r"([0-9]+)일", lambda m: sino(m[1]) + " 일", t)
        t = re.sub(r"([0-9]+)교", lambda m: sino(m[1]) + " 교", t)
        t = re.sub(r"([0-9]+)\.([0-9]+)퍼센트", lambda m: sino(m[1]) + " 점 " + " ".join(digit[int(v)] for v in m[2]) + " 퍼센트", t)
        t = t.replace("53개 구", "쉰세 개 구").replace("1만 쌍", "일만 쌍").replace("G밸리", "지밸리").replace("G타워", "지타워")
        x["reading_text"] = reading_form(t, sino)
    ready = [x for x in s["sentences"] if x["text"] is not None]
    pending_ids = [x["sentence_id"] for x in s["sentences"] if x["text"] is None]
    s["verified_core_text"] = "\n".join(x["text"] for x in ready)
    s["narration_text"] = None if pending_ids else s["verified_core_text"]
    s["narration_ready"] = False
    s["pending_sentence_ids"] = pending_ids
    s["claim_ids"] = sorted({cid for x in ready for cid in x["claim_ids"]})
    s["anchors"] = [{"sentence_id": x["sentence_id"], "anchor_string": x["anchor_string"], "timing_basis": "text_only_actual_audio_required"} for x in ready]

packet = {
    "schema_version": "1.1-writer-scaffold", "episode_id": "newlywed-apartment-picks-20261101",
    "revision": "v6", "project_revision": "top20-explain-v3", "owner": "writer",
    "status": "FEATURES_INTEGRATED_PRICES_PENDING", "source_event": "718066312", "narration_ready": False,
    "created_at": datetime.now().astimezone().isoformat(), "input_versions": versions,
    "title": "신혼부부가 많이 사는 수도권 TOP20 · 생활권과 아파트 가격",
    "duration_target_range_s": [780, 960], "duration_target_is_provisional": True, "required_actual_duration_s_greater_than": 480, "total_estimated_duration_s": None,
    "duration_method": "정보량과 실제 발화 우선.13~16분은 잠정 목표이며 반복으로 채우지 않음. 가격 문장 통합 후 estimate를 산정하고 실제 음성 이후 확정. 사용자8분 초과 조건 유지.",
    "timing_locked": False, "timing_basis": "estimate_only_actual_audio_first", "actual_duration_s": None,
    "source_geography_reference_date": "2024-11-01", "price_window": None,
    "price_freshness_note": "최종 가격기간/정규화data는 총괄 lock 대기. final-api-20261103-v1 사용금지; 정상행 보존·cdealType 또는Day 표시 해제행만 제외하는 수정v2와 부모 QA lock 전 가격값 통합 금지.",
    "blocked_price_revisions": ["final-api-20261103-v1"],
    "integration_rule": "20지역 최종 특징팩은 통합. 가격은 수정v2를 포함해 총괄이 명시한 최종 기간·구역·정규화data lock 이후에만 통합. 수집 완료/담당 검증만으로 가격 통합 금지.",
    "script_gate": feature_payload["script_gate"],
    "display_policy": {
        "statistical_source": "O002에서 통계청 자료명·기준일 설명. 지역별 본문에 반복 Stats footer 금지.",
        "map_attribution": "SGIS 등 지도 원출처·라이선스는 통합 크레딧/설명란과 내부 원장에 보존. 개별 자료의 필수 이용조건을 누락하지 않음.",
        "price_conditions": "실제 집계구역·계약기간·전용면적·실거래 중위값·취소 처리·지역n·단지n·사례단지 동 이름 유지",
        "landmark_vs_complex": "랜드마크와 단지의 생활권이 다르면 별도 지도 구도와 동 이름으로 구분. 서로 같은 장소처럼 연결하지 않음.",
        "brand": "기존 크림/네이비/파랑·Pretendard·고정 흰 의미 자막 계승",
        "no_boilerplate_badges": ["공식지수아님", "AI개념이미지"],
        "visual_default": "설명 목적의 실제 지도·실사·거래 분포. 분위기만의 임의 도시 사진을 근거로 사용하지 않음",
    },
    "pronunciation_dictionary": {"53개 구": "쉰세 개 구", "83~85㎡": "팔십삼에서 팔십오 제곱미터", "84㎡": "팔십사 제곱미터", "중위값": "중윗값", "G밸리": "지밸리", "G타워": "지타워", "GTX-A": "지티엑스 에이", "수인분당선": "수인분당선", "백현주공9단지": "백현주공 구 단지", "개포주공6단지": "개포주공 육 단지", "잠실2·3단지": "잠실 이 단지와 삼 단지", "고덕주공7단지": "고덕주공 칠 단지", "문래동6가": "문래동 육 가", "e편한세상 문래 에듀플라츠": "이편한세상 문래 에듀플라츠", "SGIS": "에스지아이에스(크레딧 표기; 본문 낭독 없음)", "원미구": "원미구", "미추홀구": "미추홀구", "서해구": "서해구", "검단구": "검단구", "가격과 n": "실제 가격·건수 확정 후 숫자 읽기표 추가 필요"},
    "emphasis_words": ["2024년", "거주 수", "단위는 쌍", "생활권", "실거래", "중위값", "같은 계약기간", "같은 면적", "거래 건수"],
    "scene_id_policy": "R01..R20 및 S003..S022 유지. O001/O002/I001/I002/C001/E001 사용. I003 및 N001/N002는 지역 설명 흐름과 중복을 고려해 생략.",
    "removed_old_scenes": [{"scene_id": sid, "reason": "통계 예시와 지도 요약의 반복을 줄이고20지역 주거 형성/생활권 설명의 흐름 유지"} for sid in ["I003", "N001", "N002"]],
    "changed_narration_scene_ids": [s["scene_id"] for s in scenes if s["scene_id"] != "E001"],
    "shared_scenes_action": "총괄 병합용 제안. 공통 scenes/state/decisions 및 이전 승인 미디어를 수정하지 않음.",
    "claim_registry": claims,
    "internal_source_and_rights_ledger": {
        "sources": facts["sources"],
        "region_sources": {r["region_id"]: r.get("sources", []) for r in facts["regions"]},
        "image_place_and_rights_records": {r["region_id"]: r.get("image_suggestions", []) for r in facts["regions"]},
        "old_photo_manifest_reference": old.get("photo_binding_manifest"),
        "old_photo_manifest_read_this_task": False,
        "final_regional_packet": feature_payload,
        "verification_scope": "지정된 최종 지역팩의 텍스트·출처·권리/사진명세와 기존 검증 기록 승계. 웹 원문·사진 픽셀·좌표·실제 음성은 writer가 이번에 재검수하지 않음.",
    },
    "scenes": scenes,
}
finalize_packet(packet, price_payload)
dump("scene_proposals_v6.json", packet)

lines = ["# 신혼부부 TOP20 · 설명 보강 대본 v6", "", "> 최종 지역팩과 부모LOCK 가격v2를 통합한 새 대본 승인 대기본입니다.",
         "> 문장 작성은 완료했으며, 완성 원고·대표 시안에 대한 사용자 새 승인 전 TTS·본편 렌더에 사용할 수 없습니다.",
         "> 13~16분은 총괄의 제작 목표 estimate입니다. 현재 원고나 실제 음성을 측정한 시간이 아닙니다.", "",
         "> 정보량과 실제 발화를 우선하며 반복으로 길이를 채우지 않습니다. 사용자 요청의8분 초과 조건은 유지합니다.",
         "> 완성 원고와 대표 시안을 전달하고 해당 새 대본을 사용자에게 승인받은 뒤에만 TTS·본편 렌더로 진행합니다.", "",
         "자료 기준: 거주 순위는2024-11-01·수도권 당시53개 구입니다.가격은2026-05-01~10-31 계약·2026-11-03 조회·전용83~85㎡ 양끝 포함입니다.10월 신고는 진행 중입니다.",
         "", "통계 출처는 도입부에서 설명합니다. 반복 출처 꼬리표를 본문에 넣지 않으며, 전체 출처·사진 이용조건·지도 크레딧은 내부 장면표와 통합 크레딧/설명란에 보존합니다.",
         "", "문장 ID와 화면 전환 ID는 자료 연결용이며 낭독 대상이 아닙니다.", ""]
for s in scenes:
    lines += [f"## {s['scene_id']} · {s['title']}", "", f"- 메시지: {s['message']}", f"- 자료: {', '.join(s['material_types'])} · 설명용", "- 예상 길이: 가격 문장 통합 후 estimate 산정 · 실제 타임록 없음", ""]
    for x in s["sentences"]:
        if x["text"] is None:
            lines += [f"> **검증 대기 · {x['sentence_id']} · {x['slot_kind']}**", f"> {x['onscreen_purpose']}", "> 문장·수치·앵커 미작성. 최종 패킷 통합 전 낭독·화면 표시 금지.", ""]
        else:
            lines += [f"**[{x['sentence_id']}]** {x['text']}", ""]
    if s["screen_beats"]:
        lines += ["화면 연결 제안:", ""]
        for b in s["screen_beats"]:
            lines += [f"- {b['beat_id']}: {b['action']}"]
        lines.append("")
lines += ["## 통합 메모", "", "- R01~R20과 기존 지역 장면 ID는 유지합니다.", "- 최종 지역팩과 부모LOCK 가격v2의20지역/20단지 가격을 통합했습니다.원문·사진 픽셀·원XML·좌표의 새 독립 검수는 writer가 수행하지 않았습니다.", "- I001/I002는 짧게 유지하고 I003/N001/N002는 생략했습니다.", "- 확정문·표시문·읽기문·claim·화면 전환ID는 scene_proposals_v6.json에 기록했습니다.", "- 랜드마크와 가격 단지가 다른 생활권이면 별도 지도 구도와 실제 동 이름으로 구분합니다.", "- 완성 원고·대표 시안 전달 후 사용자 새 대본 승인 전에는 TTS·본편 렌더를 진행하지 않습니다.", "- 실제 음성·정렬 이후에만 초 단위 타이밍을 확정합니다.", ""]
(OWN / "script_v6.md").write_text("\n".join(lines), encoding="utf-8")

pending_ids = [x["sentence_id"] for s in scenes for x in s["sentences"] if x["text"] is None]
dump("issue_V6_FACT_INTEGRATION.json", {
    "issue_id": "V6_FACT_INTEGRATION", "status": "resolved_by_final_features_and_parent_locked_prices_v2",
    "scene_ids": ["O002"] + [r["scene_id"] for r in top["regions"]],
    "problem": "이전 자료통합 대기는 해결.현재 완성원고·대표시안 전달 및 새 대본 승인 대기",
    "evidence": ["이번 task packet", "director/top20-explain-v3/제작계획.md", "director/top20-explain-v3/requirements.json"],
    "proposal": "총괄이 최신 v6 JSON으로 검토용 읽기MD와 대표시안/formal script결정을 준비.새 사용자 승인 전 TTS/본편렌더 없음.",
    "impact": "특징·랜드마크 통합 원고는 준비. 가격 포함 완성 원고·대표시안 전달/사용자 새 대본 승인 전 TTS·본편 렌더 불가.",
    "pending_sentence_ids": pending_ids, "next_owner": "director", "direct_agent_message_tool_available": False,
    "feature_bundle_integrated": {"path": "research/top20-explain-v3/regions/facts.json", "revision": feature_payload["revision"]},
    "required_price_bundle": "부모 lock을 받은 동일 계약기간·83~85㎡ 우선 검토·지역 중위값/n+대표 단지 가격/n·실제 동 이름·선정 근거·주소/ID·좌표검증상태·누락/신고시차·현재 행정구역。취소는정상행보존/cdealType또는Day표시해제행만제외",
    "special_scope": "R01은2024 옛 서구 순위와2026 현재 두 구의 가격 구역을 분리; 도입부에 실제 확정 계약기간을 별도로 설명",
})
print(json.dumps({"status": packet["status"], "scenes": len(scenes), "region_scenes": 20, "pending_slots": len(pending_ids), "estimated_duration_s": packet["total_estimated_duration_s"], "outputs": ["script_v6.md", "scene_proposals_v6.json", "issue_V6_FACT_INTEGRATION.json"]}, ensure_ascii=False))
