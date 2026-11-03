"""지정된 로컬 입력으로 writer 소유 대본과 제안만 생성합니다."""
from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
EP = HERE.parents[1]
ROOT = EP.parents[2]

PATHS = {
    "brief": EP / "brief.json",
    "state": EP / "state.json",
    "design": EP / "director/top20-split-v4/제작설계.md",
    "prices": EP / "research/top20-split-v4/prices/region_insights.json",
    "legend": EP / "research/top20-split-v4/prices/legend.json",
    "coverage": EP / "research/top20-split-v4/prices/coverage.json",
    "facts": EP / "research/top20-explain-v3/regions/facts.json",
    "supplement": EP / "research/top20-explain-v3/director_supplement.json",
    "ranking": EP / "research/top20-8min-v2/top20.json",
    "context": EP / "research/top20-split-v4/context_notes.json",
    "context_request": HERE / "request_receipt_v1.json",
    "cohort_code": EP / "research/top20-split-v4/prices/build_region_insights.py",
    "baseline_script": ROOT / "영상/신혼부부_지역별아파트/수정안_v3/대본_v6.md",
    "copy": HERE / "region_copy_v1.json",
}


def read(p):
    return json.loads(p.read_text(encoding="utf-8-sig"))


def rel(p):
    return str(p.relative_to(ROOT)).replace("\\", "/")


def dump(p, data):
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def money(x):
    x = int(x)
    a, b = divmod(x, 10000)
    return (f"{a}억" if a else "") + (f"{b:,}만원" if b else "원")


facts = read(PATHS["facts"])
prices = read(PATHS["prices"])
ranks = read(PATHS["ranking"])
context = read(PATHS["context"])
legend = read(PATHS["legend"])
coverage = read(PATHS["coverage"])
copy = read(PATHS["copy"])
FR = {r["region_id"]: r for r in facts["regions"]}
PR = {r["region_id"]: r for r in prices["regions"]}
RR = {r["region_id"]: r for r in ranks["regions"]}
CR = {r["region_id"]: r for r in context["regions"]}
registry = {}


def field(key, ptr, value=None, **kw):
    return {"path": rel(PATHS[key]), "field": ptr, "value": value, **kw}


def claim(cid, kind, sources, **kw):
    registry[cid] = {"claim_id": cid, "kind": kind, "source_fields": sources, **kw}
    return cid


METH = claim("W4-METHOD", "inherited_local_price_method", [
    field("legend", "/period", legend["period"]),
    field("legend", "/retrieved_date", legend["retrieved_date"]),
    field("legend", "/area_m2", legend["area_m2"]),
    field("legend", "/statistic", legend["statistic"]),
    field("legend", "/point", legend["point"]),
    field("legend", "/sample_rule", legend["sample_rule"]),
    field("coverage", "/additional_normal_trade_deduplication", False),
], caution="원자료의 해제 제외 등을 계승합니다. 이번에 별도 정상거래 판정·중복제거는 하지 않았습니다.")
LEGEND = claim("W4-LEGEND", "fixed_visual_encoding", [
    field("legend", "/bands", legend["bands"]),
    field("legend", "/boundary_rule", legend["boundary_rule"]),
    field("legend", "/school_symbol", legend["school_symbol"]),
    field("legend", "/station_symbol", legend["station_symbol"]),
    field("legend", "/commerce_symbol", legend["commerce_symbol"]),
])
RANK_SCOPE = claim("W4-RANK-SCOPE", "inherited_ranking_scope", [
    field("ranking", "/scope", ranks["scope"]),
    field("ranking", "/statistic_reference_date", ranks["statistic_reference_date"]),
    field("brief", "/ranking_basis"),
    field("baseline_script", "heading:2024년 거주 통계와 가격의 시점"),
], source_url=ranks["regions"][0]["source_url"])
COVERAGE = claim("W4-COVERAGE", "sum_of_existing_region_counts", [
    field("coverage", "/observed_complexes", coverage["observed_complexes"]),
    field("coverage", "/mapped_complexes", coverage["mapped_complexes"]),
    field("coverage", "/transaction_n", coverage["transaction_n"]),
    field("prices", "/regions/*/mapped_transaction_n", sum(r["mapped_transaction_n"] for r in PR.values())),
], independently_verified_new_research=False)
DESIGN = claim("W4-DESIGN", "authorized_design_request", [
    field("design", "document", "두 편 분리·지역 설명 확대·범례·전체와 상세 지도 연결"),
    field("context_request", "/layout", read(PATHS["context_request"])["layout"]),
    field("context_request", "/context_usage_bounds"),
])

ALIASES = {}
for rid, r in FR.items():
    i = facts["regions"].index(r)
    alias = {}
    for j, c in enumerate(r["claims"]):
        claim(c["claim_id"], "inherited_verified_claim", [field("facts", f"/regions/{i}/claims/{j}")],
              statement=c["statement"], original_source=c.get("original_source"),
              source_ids=c.get("source_ids"), reference_date=c.get("reference_date"),
              checked_date=c.get("checked_date"), verification_scope=c.get("verification_scope"),
              verification_mode=c.get("verification_mode"), source_status=c["status"],
              current_writer_web_reverification=False)
        alias[c["claim_id"].split(f"V3-{rid}-")[-1]] = c["claim_id"]
    alias["photo"] = claim(f"W4-{rid}-PHOTO", "inherited_photo_metadata_and_editorial_limits", [
        field("facts", f"/regions/{i}/photo"), field("facts", f"/regions/{i}/editorial_cautions")],
        new_pixel_or_license_inspection=False)
    n = ranks["regions"].index(RR[rid])
    alias["rank"] = claim(f"W4-{rid}-RANK", "inherited_rank_and_couple_count", [field("ranking", f"/regions/{n}")])
    n = prices["regions"].index(PR[rid])
    alias["region_price"] = claim(f"W4-{rid}-PRICE", "inherited_transaction_median", [
        field("prices", f"/regions/{n}/region_median_manwon", PR[rid]["region_median_manwon"]),
        field("prices", f"/regions/{n}/transaction_n", PR[rid]["transaction_n"]),
    ], denominator="all recorded qualifying regional transactions; not mapped-complex counts")
    alias["bands"] = claim(f"W4-{rid}-BANDS", "inherited_one_point_per_mapped_complex_counts", [
        field("prices", f"/regions/{n}/mapped_bands", PR[rid]["mapped_bands"]),
        field("prices", f"/regions/{n}/mapped_complexes", PR[rid]["mapped_complexes"]),
        field("prices", f"/regions/{n}/observed_complexes", PR[rid]["observed_complexes"]),
        field("prices", f"/regions/{n}/mapped_transaction_n", PR[rid]["mapped_transaction_n"]),
    ], denominator="location-verified complexes; each complex counted once")
    alias["contrast"] = claim(f"W4-{rid}-CONTRAST", "writer_comparison_of_existing_computed_groups", [
        field("prices", f"/regions/{n}/dong_prices_by_transaction_count", PR[rid]["dong_prices_by_transaction_count"]),
        field("prices", f"/regions/{n}/build_cohorts", PR[rid]["build_cohorts"]),
        field("prices", f"/regions/{n}/interpretation_limit", PR[rid]["interpretation_limit"]),
        field("cohort_code", "line:for lo,hi,label", "첫 집단은 buildYear.between(0,2000): 2000년 포함"),
    ], inference="관측 집단 간 비교입니다. 입지·연식·교통의 가격 인과효과 추정이 아닙니다.",
       statement=copy[rid]["contrast"], independently_verified_new_research=False)
    for dong in copy[rid]["dongs"]:
        rows = PR[rid]["dong_prices_by_transaction_count"]
        j = next(j for j, row in enumerate(rows) if row["dong"] == dong)
        row = rows[j]
        assert row["transaction_n"] >= 20
        alias[dong] = claim(f"W4-{rid}-DONG-{j:02d}", "inherited_dong_transaction_median", [
            field("prices", f"/regions/{n}/dong_prices_by_transaction_count/{j}", row)],
            denominator="qualifying transactions in the named legal dong; each transaction counted once")
    n = context["regions"].index(CR[rid])
    selected = []
    for key, names in [("schools_shown_near_representative", copy[rid]["schools"]),
                       ("stations_shown_near_representative", copy[rid]["stations"])]:
        for name in names:
            j = next(j for j, row in enumerate(CR[rid][key]) if row["name"] == name)
            selected.append(field("context", f"/regions/{n}/{key}/{j}", CR[rid][key][j]))
    alias["context"] = claim(f"W4-{rid}-CONTEXT", "supplied_facility_location_records", [
        field("context", f"/regions/{n}/representative", CR[rid]["representative"]), *selected,
        field("context", "/school_source", context["school_source"]),
        field("context", "/station_source", context["station_source"]),
        field("context", f"/regions/{n}/usage", CR[rid]["usage"]),
    ], scope="표시 대상의 실제 위치·명칭만. 배정·도보시간·완전한 최근접 판정·현재 모든 노선 검증 아님.",
       exact_name_and_rendered_map_match="pending_visual_and_independent_QA")
    ALIASES[rid] = alias

supp = read(PATHS["supplement"])["claims"][0]
claim(supp["claim_id"], "inherited_verified_director_supplement", [field("supplement", "/claims/0")],
      statement=supp["text"], verification_scope=supp["scope"], source_url=supp["source_url"])
ALIASES["R18"]["DIR-H03"] = supp["claim_id"]

BASE_PHASES = {
    "full_district": ("구 전체 가격 점과 범례를 왼쪽에 고정하고, 현재 지역 경계를 읽힐 크기로 강조합니다.", "오른쪽은 전체 구 위치와 상세 대상 사각형을 먼저 보여줍니다."),
    "focused_feature": ("왼쪽 전체 구와 가격 점을 유지하고, 발화한 생활권만 차례로 강조합니다.", "오른쪽을 실제 도로·하천·공원·공동주택 맥락이 있는 고정 상세도로 연결합니다. 역사·업무·주거 대상이 다르면 locator도 바꿉니다."),
    "landmark_photo": ("왼쪽 구 전체 지도와 현재 생활권 locator를 유지합니다.", "오른쪽에 지역 특성 설명 직후 실제 장소 사진을 독립된 호흡으로 보여줍니다. 촬영연도·실제 피사체·크레딧을 표시합니다."),
    "regional_price": ("전체 가격 분포 위에 구 거래 중위값·건수·기간을 붙입니다. 단지 분포의 중위값으로 표기하지 않습니다.", "사진 뒤에는 가격 비교 상태로 전환하고 이전 빈 지도/완성 차트를 재삽입하지 않습니다."),
    "dong_price_compare": ("발화한 동 이름과 그 동에 속하는 실제 단지 점만 강조하며 구 전체는 남깁니다.", "거래 중위값·n을 지도에 연결한 작은 비교 표기로 읽습니다. 동 가격을 대표단지 가격으로 붙이지 않습니다."),
    "complex_band_distribution": ("해당 가격대 점의 윤곽을 강조하고 분자/지도에 연결된 단지 수를 함께 표시합니다.", "대표 생활권의 실제 단지 배치를 유지하며 거래 표본수와 단지수 범례를 분리합니다."),
    "observed_contrast": ("왼쪽 구 전체 분포를 유지합니다.", "발화한 동/연식 집단의 값만 순차로 추가하고 거래 n·기간·면적을 함께 표시합니다. 연식값은 지역의 거래 집단 통계이며 특정 단지·학교 핀에 붙이지 않습니다. 첫 집단은 2000년을 포함하므로 '2000년까지 준공'으로 표시합니다."),
    "focused_context": ("왼쪽 전체 지도에서 대표단지 상세 범위를 표시합니다.", "오른쪽 실제 대표단지 주변에 선택한 학교·역의 원자료 명칭을 표시합니다. 도로·공원·상업 맥락은 확보·정합 확인 후만 배치합니다."),
    "two_budget_conditions": ("두 예산 조건에서 비교 출발점으로 언급한 동을 왼쪽에 순서대로 강조합니다.", "조건별 동·예산만 짧게 표시하고, 실제 매물/대출 가능액이나 그 예산의 모든 단지 이용 보장으로 표현하지 않습니다."),
    "decision_context": ("전체 구 가격 분포와 상세 범위를 유지합니다.", "학교·역·상권 중 이번 결론의 확인 대상을 한 번씩 강조하고 장면 종료까지 유지합니다."),
}


def sentence(sid, text, ids, phase, purpose, kind="fact", action=None):
    ids = list(dict.fromkeys(ids))
    if phase in BASE_PHASES:
        left, right = BASE_PHASES[phase]
    else:
        left, right = "두 편 공통 지도·범례의 의미를 유지합니다.", "발화에 맞는 지도/원자료만 순차로 강조합니다."
    return {
        "sentence_id": sid, "text": text, "narration_text": text,
        "claim_ids": ids, "source_fields": [{"claim_id":cid, "path":f["path"], "field":f["field"]} for cid in ids for f in registry[cid]["source_fields"]],
        "statement_type": kind, "map_phase": phase,
        "material_types": ["real_photo"] if phase == "landmark_photo" else ["map"],
        "visual_purpose": purpose, "screen_role": "explanation",
        "screen_direction": {"left_map": left, "right_panel": right, "speech_linked_action": action or purpose},
        "asset_status": "proposal_only_not_rendered; inherited_sources_available; v4_context_map_pending",
        "fallback": "명명된 시설·맥락 레이어가 검증되지 않으면 임의 점으로 대체하지 않고 visual 이슈로 남깁니다. 기존 실제 사진은 같은 정보 목적·크레딧 범위에서만 사용합니다.",
    }


# v6 원고 문자수 / state의 실제 음성 길이로 잡은 계획용 속도. 새 음성을 측정한 값이 아닙니다.
baseline = PATHS["baseline_script"].read_text(encoding="utf-8-sig")
base_spoken = "".join(l for l in baseline.splitlines() if l and not l.startswith("#"))
base_duration = read(PATHS["state"])["active_measured_duration_s"]
READ_RATE = len(re.sub(r"\s", "", base_spoken)) / base_duration


def estimate(items):
    n = len(re.sub(r"\s", "", "".join(s["text"] for s in items)))
    sec = round(n / READ_RATE, 1)
    return {"status": "estimate", "seconds": sec,
            "range_seconds": [math.floor(sec * .85), math.ceil(sec * 1.15)],
            "basis": "기존 v6 원고의 공백 제외 문자수 / state.active_measured_duration_s 참고. 새 음성·문장 정렬 미실시, 숫자 낭독·호흡 차이 존재.",
            "nonspace_characters": n}


scenes = []


def intro(part):
    pid = f"P{part:02d}-INTRO"
    opening = ("신혼부부가 많이 사는 곳에서도, 같은 구 안의 아파트 가격과 생활권은 다릅니다." if part == 1 else
               "앞편의 20~11위에서는 같은 구 안에서도 예산과 생활권이 갈렸으며, 이번에는 10위부터 1위까지 이어서 살펴보겠습니다.")
    rows = [
        (opening, [DESIGN], "intro_hook", "구 전체 지도와 두 생활권의 가격 점을 연결해 질문을 제시합니다.", "editorial"),
        (("이번 편은 20위부터 11위까지이며, 순위는 국가데이터처의 2024년 신혼부부통계, 수도권 53개 구 가운데 거주 부부 수 기준입니다." if part == 1 else
          "순위는 국가데이터처의 2024년 신혼부부통계, 수도권 53개 구 가운데 거주 부부 수 기준이며, 앞편을 보지 않아도 지도를 읽을 수 있습니다."), [RANK_SCOPE], "intro_scope", "출처·범위·해당 편 순서를 한 번 표기합니다.", "inherited_fact"),
        ("2024년 11월 1일, 혼인신고 후 5년이 지나지 않은 초혼·재혼 부부를 합친 값으로, 지금의 선호도나 집을 산 부부 수와는 구분합니다.", [RANK_SCOPE], "intro_scope", "거주지 통계 기준일·쌍 단위와 가격 관측시점을 분리합니다.", "interpretation"),
        ("왼쪽은 구 전체 가격 분포, 오른쪽은 대표 생활권의 학교·역·상권을 읽는 상세 지도입니다.", [DESIGN], "intro_layout", "왼쪽 전체→오른쪽 상세 범위를 연결한 후 고정합니다.", "authorized_design"),
        ("가격 점 하나는 위치가 확인된 아파트 한 단지이며, 색은 전용83~85제곱미터의 2026년 5~10월 거래를 11월 3일 조회한 단지별 중위값입니다.", [METH], "intro_point", "실제 한 단지 점을 강조하고 면적·계약기간·조회일을 고정 표시합니다.", "method"),
        ("색은 5억 미만, 5억~7억, 7억~10억, 10억~15억, 15억~20억, 20억 이상 여섯 단계이며, 경계 금액은 그 금액부터 시작하는 구간에 들어갑니다.", [LEGEND], "intro_legend", "동일 여섯 색을 낮은 가격부터 순차 강조합니다. 표시는 5≤가격<7 등 상한 미포함을 명확히 합니다.", "method"),
        ("거래 한 건인 점도 있어 건수를 함께 보며, 동별 중위값은 단지마다 한 표가 아니라 거래마다 한 표를 주어 계산합니다.", [METH, COVERAGE], "intro_denominator", "단지 점·단지 n과 동 거래 n을 각각 한 번 시연합니다.", "method"),
        ("학교는 네모, 역은 둥근 네모, 상권은 마름모로 구분하며, 학교 위치가 배정이나 도보시간을 뜻하지는 않습니다.", [LEGEND, DESIGN], "intro_facility_symbols", "가격은 원형 색점, 시설은 형태로 구별하고 학교·역·상업 맥락의 자료기준일을 붙입니다.", "method"),
        ("학교·역 자료의 기준일은 서로 다르고, 가격도 10월 신고와 이후 정정·해제로 바뀔 수 있으므로 관측 시점을 함께 읽겠습니다.", [METH, ALIASES["R20" if part == 1 else "R10"]["context"]], "intro_date_caveat", "거주 기준일/가격 조회일/학교·역 원자료일을 분리한 작은 주석을 유지합니다.", "scope_caution"),
    ]
    items = [sentence(f"{pid}-{i:02d}", t, ids, phase, purpose, kind) for i,(t,ids,phase,purpose,kind) in enumerate(rows,1)]
    scene = {"scene_id": pid, "part": part, "scene_kind": "intro", "title": "거주 순위와 두 지도 읽는 법",
             "key_message": "거주 수 순위·관측 가격·단지 점·시설 표시를 서로 다른 기준으로 읽습니다.",
             "sentences": items, "claim_ids": list(dict.fromkeys(cid for s in items for cid in s["claim_ids"])),
             "estimate": estimate(items), "approval_status": "script_gate_pending_not_approved"}
    scenes.append(scene)


intro(1)
for rank in range(20, 0, -1):
    rid = f"R{rank:02d}"
    if rank == 10:
        # 1편 결말은 순회 뒤 순서 정렬로 배치합니다.
        intro(2)
    part = 1 if rank >= 11 else 2
    sid = f"P{part:02d}-{rid}"
    r, p, c, a = RR[rid], PR[rid], copy[rid], ALIASES[rid]
    seq = []

    def add(text, aliases, phase, purpose, kind="fact"):
        ids = [a.get(x, x) for x in aliases]
        seq.append(sentence(f"{sid}-{len(seq)+1:02d}", text, ids, phase, purpose, kind))

    title_region = f"{r['province']} {r['region']}"
    if rid == "R01":
        title_region = "2024년 당시 인천 서구"
    add(f"{rank}위는 {title_region}, {r['newlywed_couples']:,}쌍입니다.", ["rank"], "full_district", "전체 구와 대표 생활권 상세 범위를 먼저 확인합니다.")
    for text, aliases, phase in c["features"]:
        add(text, aliases, phase, "주거지 형성·업무·교통과 실제 장소의 기능을 연결합니다.", "inherited_fact_or_bounded_synthesis")
    label = "옛 서구 범위의 " if rid == "R01" else ""
    add(f"2026년 5~10월 같은 면적의 {label}거래 {p['transaction_n']:,}건 중위값은 {money(p['region_median_manwon'])}입니다.",
        ["region_price", METH], "regional_price", "구 전체 거래가격의 가운데 값과 표본 수를 제시합니다.")
    dong_rows = {d["dong"]: d for d in p["dong_prices_by_transaction_count"]}
    for j, dong in enumerate(c["dongs"]):
        d = dong_rows[dong]
        text = f"{'같은 기간·면적에서 ' if j == 0 else ''}{dong}은 {d['transaction_n']:,}건의 중위값이 {money(d['median_manwon'])}입니다."
        add(text, [dong, METH], "dong_price_compare", f"법정동 {dong}의 거래 n과 중위값을 표시합니다. 대표단지 가격과 분리합니다.")
    b = max(p["mapped_bands"], key=lambda b:b["complex_n"])
    bandphrase = {"5억 미만":"5억원 미만", "5~7억":"5억원 이상 7억원 미만", "7~10억":"7억원 이상 10억원 미만",
                  "10~15억":"10억원 이상 15억원 미만", "15~20억":"15억원 이상 20억원 미만", "20억 이상":"20억원 이상"}[b["label"]]
    add(f"지도에 연결된 {p['mapped_complexes']}개 단지 중 {b['complex_n']}곳은 단지 중위값이 {bandphrase}입니다.",
        ["bands", LEGEND], "complex_band_distribution", "가장 많은 가격대의 단지 점과 분모를 강조합니다. 거래 건수로 읽지 않습니다.")
    extra = ["contrast", "region_price", "bands"]
    if rid == "R06": extra += ["H01", "H02"]
    contrast_text = c["contrast"].replace("2000년 이전 준공", "2000년까지 준공").replace("2000년 이전", "2000년까지 준공")
    add(contrast_text, extra, "observed_contrast", "같은 구 안에서 놓치기 쉬운 거래구성·연식·생활권 차이를 설명합니다.", "descriptive_comparison_not_causal")
    add(c["context_text"], ["context"], "focused_context", "대표단지와 선택한 시설의 원자료 명칭·실제 좌표·지도 표시를 연결합니다.", "bounded_location_description")
    add(c["conditions"], [*c["dongs"], "contrast"], "two_budget_conditions", "두 예산에서 조사할 동의 출발점을 구별합니다.", "editorial_comparison_criterion_not_listing_or_recommendation_guarantee")
    selected = registry[a["context"]]["source_fields"]
    scenes.append({
        "scene_id": sid, "legacy_scene_id": r["scene_id"], "part": part, "scene_kind": "region",
        "rank": rank, "region_id": rid, "title": f"{rank}위 {title_region}",
        "key_message": f"{c['dongs'][0]}·{c['dongs'][1]}의 거래가격과 대표 생활권 배치를 구분해 두 예산 조건으로 비교합니다.",
        "sentences": seq, "narration_text": "\n\n".join(s["text"] for s in seq),
        "claim_ids": list(dict.fromkeys(cid for s in seq for cid in s["claim_ids"])),
        "material_types": ["map", "real_photo"], "screen_role": "explanation",
        "estimate": estimate(seq), "approval_status": "script_gate_pending_not_approved",
        "price_comparison": {
            "area_m2_inclusive": [83, 85], "contract_period": legend["period"], "retrieved_date": legend["retrieved_date"],
            "regional_transaction_n": p["transaction_n"], "regional_median_manwon": p["region_median_manwon"],
            "dong_comparisons": [dong_rows[d] for d in c["dongs"]], "dong_denominator": "one vote per qualifying transaction",
            "mapped_complexes": p["mapped_complexes"], "observed_complexes": p["observed_complexes"],
            "mapped_transaction_n": p["mapped_transaction_n"], "mapped_bands": p["mapped_bands"],
            "dot_denominator": "one location-verified complex median per point",
            "not_inferred": ["가격 차이의 원인", "집값 상승률", "신혼부부의 자가 구입가격", "현재 매물 가능 여부"],
        },
        "context_selection": {
            "representative_complex": CR[rid]["representative"], "spoken_schools": c["schools"],
            "source_station_names": c["stations"],
            "station_spoken_aliases": {"용마산(용마폭포공원)":"용마산역", "잠실(송파구청)":"잠실역", "아라(북부법원, 검찰청)":"아라역"},
            "source_fields": selected, "school_date_label": "2026-10-01",
            "station_date_label_rule": "선택한 역 레코드의 source_record_date 그대로; 미기재는 미기재",
            "verified_commerce_names_spoken": (["부평문화의거리", "지하상가", "전통시장"] if rid == "R05" else []),
            "commerce_map_status": "OSM 보완 진행 중이라는 상위 전달만 수신; 이번 담당 확보/검수 안 함",
            "rendered_label_match": "pending_visual_and_independent_QA",
            "nearest_station_determined": False, "walking_minutes_claimed": False, "school_assignment_claimed": False,
        },
        "landmark_photo": {"asset_id": FR[rid]["photo"]["asset_id"], "path": FR[rid]["photo"]["absolute_file"],
                           "caption": FR[rid]["photo"]["caption_ko"], "source_metadata": rel(PATHS["facts"]),
                           "source_field": f"/regions/{facts['regions'].index(FR[rid])}/photo",
                           "timing": "지역 특성 발화 다음에 사진 호흡; 새 타임록 이후 실제 hold 길이 확정",
                           "new_pixel_or_license_inspection": False},
        "visual_requirements": ["왼쪽 구 전체 가격 분포+오른쪽 대표 생활권 상세 고정", "전체 위치를 먼저 읽은 뒤 상세로 연결",
                                "실제 도로·공원·단지 외곽과 시설 위치 정합", "두 동 가격을 대표단지 가격으로 표기 금지",
                                "자막·범례·출처는 카메라와 분리", "시설명·말하는 대상·강조점 일치", "빈 차트·옛 지도 단발 재등장 금지"],
        "editorial_cautions": FR[rid]["editorial_cautions"],
    })


def ending(part):
    sid = f"P{part:02d}-OUTRO"
    if part == 1:
        rows = [
            ("20위부터 11위까지 살펴보니, 구 이름과 거주 수만으로는 예산에 맞는 생활권을 정하기 어려웠습니다.", [DESIGN], "editorial"),
            ("거래가 많은 동의 가격과 단지마다 한 점인 지도를 나눠 읽고, 두 사람의 직장·학교·장보기 경로를 실제 후보 단지에 연결하는 방식이 유용합니다.", [METH, DESIGN], "editorial"),
            ("다음 편은 미추홀구부터 2024년 당시 인천 서구까지, 10위에서 1위를 같은 가격 범례로 비교하겠습니다.", [ALIASES["R10"]["rank"], ALIASES["R01"]["rank"], LEGEND], "preview"),
            ("이어서 상위 열 곳의 생활권과 가격 차이도 살펴보실 분들은 구독과 좋아요를 부탁드립니다.", [DESIGN], "CTA"),
        ]
    else:
        rows = [
            ("거주 수 1위와 우리 부부에게 맞는 집은 서로 다른 질문이며, 같은 구 안에서도 거래가격과 생활권의 선택 폭은 달랐습니다.", [DESIGN], "editorial"),
            ("먼저 감당할 집값과 월 주거비를 정하고, 두 사람의 직장까지 이동할 경로로 후보 동을 좁히는 방식입니다.", [DESIGN], "editorial"),
            ("다음으로 같은 면적의 단지 가격과 건수, 준공연도·수리 상태를 비교하고, 학교·역·상점은 단지 출입구에서 실제로 이용할 길을 확인합니다.", [METH, DESIGN], "editorial"),
            ("이 과정에서 동별 거래 중위값과 단지 점의 분모를 구분하고, 학교 배정과 현재 매물 조건은 별도로 확인해야 합니다.", [METH, DESIGN], "editorial"),
            ("앞편의 20~11위도 함께 비교해 보시고, 다음 지역 비교를 이어 보실 분들은 구독과 좋아요를 부탁드립니다.", [DESIGN], "CTA"),
        ]
    items = [sentence(f"{sid}-{i:02d}", t, ids, "outro_decision", "실제 후보 지도 위에서 예산→생활권→단지→시설 순서만 강조합니다.", kind) for i,(t,ids,kind) in enumerate(rows,1)]
    scenes.append({"scene_id": sid, "part": part, "scene_kind": "outro", "title": "생활권 비교 기준과 다음 연결",
                   "key_message": "예산과 생활 동선을 같은 후보 단지에 연결합니다.", "sentences": items,
                   "claim_ids": list(dict.fromkeys(cid for s in items for cid in s["claim_ids"])),
                   "estimate": estimate(items), "approval_status": "script_gate_pending_not_approved",
                   "silent_tail": "마지막 발화 후 3초는 실제 타임록에서 확보; 무음 브랜드에는 흰 자막 박스 없음"})


ending(1)
ending(2)
scenes.sort(key=lambda s:(s["part"], 0 if s["scene_kind"]=="intro" else 100 if s["scene_kind"]=="outro" else 21-s["rank"]))

pronunciation = [
    {"display":"GTX-A", "read":"지티엑스 에이"}, {"display":"G밸리", "read":"지 밸리"},
    {"display":"e편한세상", "read":"이편한세상"}, {"display":"Y CITY(와이시티)", "read":"와이시티"},
    {"display":"83~85㎡", "read":"팔십삼 제곱미터 이상 팔십오 제곱미터 이하"},
    {"display":"중위값", "read":"중위깝"}, {"display":"계남", "read":"계남"},
    {"display":"용마산(용마폭포공원)", "read":"용마산역", "map_label":"용마산(용마폭포공원)"},
    {"display":"잠실(송파구청)", "read":"잠실역", "map_label":"잠실(송파구청)"},
    {"display":"아라(북부법원, 검찰청)", "read":"아라역", "map_label":"아라(북부법원, 검찰청)"},
    {"display":"연수2동", "read":"연수 이 동"}, {"display":"삼산2동", "read":"삼산 이 동"},
    {"display":"문래동6가", "read":"문래동 육 가"},
    {"display":"5~7억", "read":"오억원 이상 칠억원 미만", "note":"다른 구간도 하한 포함·상한 미포함"},
]

inputs = [{"key":k, "path":rel(p), "sha256":sha(p)} for k,p in PATHS.items()]
payload = {
    "revision":"top20-split-v4-writer-v1", "task_id":"two-part-v4-script", "created_date":"2026-11-03",
    "status":"draft_complete_for_director_review_script_gate_pending_not_approved",
    "ownership":"writer/top20-split-v4 only; director scenes/state/decisions unchanged by this writer",
    "input_revisions":inputs,
    "approval":{"script":"pending_new_decision_not_approved", "decision_id":None, "prior_v6_approval_inherited":False,
                "tts_performed":False, "paid_generation_performed":False, "upload_performed":False, "external_export_performed":False},
    "scope":{"part1_ranks":[20,11], "part2_ranks":[10,1], "register":"합니다/입니다", "new_web_facts":False},
    "price_and_map_contract": {
        "legend":legend, "coverage":{"observed_complexes":2304,"mapped_complexes":2094,"observed_transactions":14303,"mapped_transactions":12829},
        "coverage_screen_note":"위치 확인 단지만 점으로 표시합니다. 미연결 210단지·1,474건을 가격 0으로 채우지 않습니다.",
        "layout":"왼쪽: 통계구역 전체 가격 분포 고정 / 오른쪽: 대표 생활권의 실제 맥락 레이어와 학교·역·상업시설 상세",
        "dot_statistic":"one recorded qualifying transaction median per location-verified complex",
        "dong_statistic":"transaction-weighted median; each trade counted once, not mean of complex medians",
        "dong_comparison_minimum_transactions":20,
        "source_date_caveats":"2024 residence rank versus 2026 trade observation; October reporting incomplete; school and station record dates differ",
        "noncausal":True, "placeholder_coordinates_allowed":False,
    },
    "claim_registry":registry, "scenes":scenes,
    "narration_handoff":{"voice_intent":"기존 방침: 무료 InJoon; 이번 작업에서는 생성하지 않음", "pronunciation_dictionary":pronunciation,
                         "emphasis":["점 하나는 한 단지", "거래 건수와 단지 수", "같은 기간·면적", "두 예산 조건", "2024년 당시 서구"],
                         "delivery":"차분한 합니다체. 숫자와 단위를 붙여 읽고 금액·시설명 사이에 호흡을 둡니다. 화면지시·근거·예상 길이·각주는 낭독하지 않습니다.",
                         "timing_basis":"estimate_only_no_new_audio; actual_timing_required_after_script_gate"},
    "open_issue_ids":["W4-CONTEXT-MATCH", "W4-INDEPENDENT-SCRIPT-QA"],
}

for part in [1,2]:
    ss = [s for s in scenes if s["part"]==part]
    est = estimate([x for s in ss for x in s["sentences"]])
    text = [f"# 신혼부부 거주 TOP20 — {part}편 {'20~11위' if part==1 else '10~1위'} 대본 v1", "",
            "새 대본 검토본입니다. **script 게이트 승인 대기이며, 기존 v6 승인을 승계하지 않습니다.**", "",
            f"예상 길이: **약 {est['seconds']/60:.1f}분 · estimate**. 새 음성을 만들거나 청취·정렬한 값이 아닙니다. 지역별 추정은 아래 표를 참고합니다.", "",
            "문체: 합니다/입니다 · 낭독할 문장과 제작 지시를 분리했습니다. 읽는 원고의 숫자는 표시 표기이며, 발음 사전은 장면 제안 JSON에 있습니다.", "",
            "공통 화면: **왼쪽 구 전체 가격 분포 + 오른쪽 대표 생활권 상세 고정 구도**. 전체 구와 상세 범위를 먼저 읽고, 특성 설명 뒤 실제 장소 사진을 넣은 다음 가격 비교·시설 상세로 연결합니다.", "",
            "가격 주석: 2026년 5~10월 계약, 11월 3일 조회, 전용83~85㎡. 수록 거래의 해제 제외 등 기존 집계 조건을 계승하며 이번에 별도 정상거래 판정·중복제거는 하지 않았습니다. 동은 거래마다 한 표, 지도는 위치 확인 단지마다 한 점입니다.", "",
            "시설 주석: 학교는 2026-10-01 자료, 역은 선택 레코드별 기준일을 표시합니다. 학교 배정·도보시간·최인접역을 판정하지 않았습니다. OSM 도로·공원·상업시설 보완은 진행 상태 전달만 받았고, 이 대본 담당이 확보·검수한 결과로 기록하지 않습니다.", "",
            "지도 범례: 파랑 <5억 / 청록 5≤가격<7억 / 황색 7≤가격<10억 / 주황 10≤가격<15억 / 빨강 15≤가격<20억 / 보라 ≥20억. 학교 □ / 역 둥근 □ / 상권 ◇. 가격 점은 원형입니다.", "",
            "지도 커버리지(두 편 전체): 관측 2,304단지·14,303건 중 위치 연결 2,094단지·12,829건. 미연결 단지를 지도에서 가격 0으로 채우지 않습니다. 지역별 분모는 장면 제안에 있습니다.", "",
            "|장면|문장 수|지역 설명 예상 길이|", "|---|---:|---:|"]
    for s in ss:
        text.append(f"|{s['scene_id']} · {s['title']}|{len(s['sentences'])}|{s['estimate']['seconds']:.0f}초 · estimate|")
    for s in ss:
        text += ["", f"## {s['scene_id']} · {s['title']}", "", "### 낭독 원고", ""]
        for item in s["sentences"]:
            text += [item["text"], ""]
        text += ["### 화면·근거 메모 — 낭독 제외", "", f"- 핵심 메시지: {s['key_message']}",
                 f"- 문장 ID: {s['sentences'][0]['sentence_id']} ~ {s['sentences'][-1]['sentence_id']}",
                 "- 문장별 claim_ids·source_fields·map_phase: `scene_proposals_v1.json`의 동일 장면."]
        if s["scene_kind"]=="region":
            cs = s["context_selection"]
            ds = [f["value"]["name"]+" "+f["value"]["source_record_date"] for f in cs["source_fields"] if isinstance(f.get("value"),dict) and "name" in f["value"]]
            text += [f"- 사진: {s['landmark_photo']['caption']} · 기존 사진 메타데이터 재사용, 새 픽셀 검수 없음.",
                     f"- 상세 중심: {cs['representative_complex']} · 시설 원자료일: {' / '.join(ds)}.",
                     "- 왼쪽에서 동별 가격 두 곳을 비교한 뒤, 오른쪽 대표단지 주변의 선택 시설만 강조합니다. 가격 비교 동과 대표단지가 다르면 locator·동 이름을 명시합니다.",
                     "- 상업시설·도로·공원은 실제 확보와 이름·좌표 정합 확인 후 사용합니다. 확인 전 임의 도형·시설명을 넣지 않습니다."]
            for caution in s["editorial_cautions"]:
                text.append(f"- 주의: {caution}")
    text += ["", "제작 인계: 새 script 결정과 독립 대본 QA → visual의 시설명·지도 표시 매칭 → 승인 후 narration의 실제 음성·타임록 순서입니다. 현재 새 음성·영상·게시 결과물은 없습니다.", ""]
    (HERE / f"part{part}_script_v1.md").write_text("\n".join(text), encoding="utf-8")

dump(HERE / "scene_proposals_v1.json", payload)
print(json.dumps({"scenes":len(scenes),"region_scenes":20,"sentences":sum(len(s["sentences"]) for s in scenes),
                  "parts":[{"part":part,"estimate_seconds":round(sum(s['estimate']['seconds'] for s in scenes if s['part']==part),1)} for part in [1,2]],
                  "regional_estimates":[[s['region_id'],s['estimate']['seconds']] for s in scenes if s['scene_kind']=='region'],
                  "read_rate_nonspace_per_second":round(READ_RATE,4)}, ensure_ascii=False))
