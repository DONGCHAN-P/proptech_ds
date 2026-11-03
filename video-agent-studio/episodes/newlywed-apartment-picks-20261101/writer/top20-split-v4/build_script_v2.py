"""v1을 보존하고 지역 설명 중심의 v2 대본과 장면 제안을 만듭니다."""
from copy import deepcopy
import hashlib
import json
import math
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
EP = HERE.parents[1]
ROOT = EP.parents[2]
read = lambda p: json.loads(p.read_text(encoding="utf-8-sig"))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rel = lambda p: str(p.relative_to(ROOT)).replace("\\", "/")


def dump(p, obj):
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")


old_names = ["build_script_v1.py", "finalize_handoff_v1.py", "handoff.json", "issue_W4-CONTEXT-MATCH.json", "issue_W4-INDEPENDENT-SCRIPT-QA.json", "part1_script_v1.md", "part2_script_v1.md", "preflight_writer_v1.json", "region_copy_v1.json", "request_receipt_v1.json", "scene_proposals_v1.json", "validation_v1.json", "verify_script_v1.py"]
preserve_path = HERE/"v1_preservation_manifest.json"
if not preserve_path.exists():
    dump(preserve_path, {"purpose":"v2 생성 전 v1 파일 보존 해시", "files":[{"path":n,"sha256":sha(HERE/n)} for n in old_names]})
assert all(sha(HERE/x["path"])==x["sha256"] for x in read(preserve_path)["files"])

paths = {
    "v1":HERE/"scene_proposals_v1.json", "copy":HERE/"region_copy_v2.json", "request":HERE/"request_receipt_v2.json",
    "prices":EP/"research/top20-split-v4/prices/region_insights.json", "context":EP/"research/top20-split-v4/context_notes.json",
    "maps":EP/"visual/top20-split-v4/map_assets.json", "facts":EP/"research/top20-explain-v3/regions/facts.json",
    "supplement":EP/"research/top20-explain-v3/director_supplement.json", "ranking":EP/"research/top20-8min-v2/top20.json",
    "legend":EP/"research/top20-split-v4/prices/legend.json", "cohort_code":EP/"research/top20-split-v4/prices/build_region_insights.py",
    "baseline_script":ROOT/"영상/신혼부부_지역별아파트/수정안_v3/대본_v6.md", "builder":Path(__file__).resolve(),
}
v1 = read(paths["v1"])
copy = read(paths["copy"])
prices = read(paths["prices"])
context = read(paths["context"])
maps = read(paths["maps"])
P = {r["region_id"]:r for r in prices["regions"]}
C = {r["region_id"]:r for r in context["regions"]}
M = {r["region_id"]:r for r in maps["assets"] if r["mode"]=="prices"}
V = {r["region_id"]:r for r in v1["scenes"] if r["scene_kind"]=="region"}
registry = deepcopy(v1["claim_registry"])
new_request = "W4V2-REQUEST"
registry[new_request] = {"claim_id":new_request,"kind":"current_user_revision_request", "source_fields":[{"path":rel(paths["request"]),"field":"/intro"},{"path":rel(paths["request"]),"field":"/regional_narration"},{"path":rel(paths["request"]),"field":"/map_matching_rule"}]}
norm = lambda s:s.removesuffix("역")


def field(key, pointer, value=None):
    out = {"path":rel(paths[key]),"field":pointer}
    if value is not None:
        out["value"] = value
    return out


def register(cid, kind, fields, **kw):
    registry[cid] = {"claim_id":cid,"kind":kind,"source_fields":fields,**kw}
    return cid


def money(value):
    a,b = divmod(int(value),10000)
    return (f"{a}억" if a else "")+(f"{b:,}만원" if b else "원")


aliases = {}
selected_context = {}
comparisons = {}
for rid, old in V.items():
    p = P[rid]
    n = prices["regions"].index(p)
    spec = copy[rid]["price"]
    if spec["type"]=="dong_pair":
        rows = [d for name in spec["dongs"] for d in p["dong_prices_by_transaction_count"] if d["dong"]==name]
        assert len(rows)==2 and all(d["transaction_n"]>=20 for d in rows)
        fields = [field("prices",f"/regions/{n}/dong_prices_by_transaction_count/{p['dong_prices_by_transaction_count'].index(d)}",d) for d in rows]
        denominator = "법정동별 수록 거래마다 한 표를 주는 중위값"
    elif spec["type"]=="cohort_pair":
        rows = [d for label in spec["labels"] for d in p["build_cohorts"] if d["label"]==label]
        assert len(rows)==2 and all(d["transaction_n"]>=20 for d in rows)
        fields = [field("prices",f"/regions/{n}/build_cohorts/{p['build_cohorts'].index(d)}",d) for d in rows]
        denominator = "준공 시기별 수록 거래마다 한 표를 주는 중위값; 2000년까지 집단은 2000년 포함"
    else:
        rows = [p["mapped_bands"][i] for i in spec["indices"]]
        fields = [field("prices",f"/regions/{n}/mapped_bands/{i}",p["mapped_bands"][i]) for i in spec["indices"]]
        fields += [field("prices",f"/regions/{n}/mapped_complexes",p["mapped_complexes"])]
        denominator = "위치가 연결된 단지마다 한 점; 단지별 거래 중위값의 가격 구간"
    priceid = register(f"W4V2-{rid}-PRICE-SELECTED", "existing_computed_price_comparison", fields,
                       statement=spec["text"], denominator=denominator, inference="관측 집단 간 대비. 가격 인과효과나 기대수익 추정 없음")
    comparisons[rid] = {"type":spec["type"],"claim_id":priceid,"spoken_text":spec["text"],"rows":rows,"denominator":denominator,
                        "period":["2026-05-01","2026-10-31"],"area_m2_inclusive":[83,85],"retrieved_date":"2026-11-03",
                        "screen_annotation":"선택한 비교마다 집단명·거래 n(분포는 단지 n)·기간·면적·중위값을 표시"}
    oldctx = deepcopy(old["context_selection"])
    if rid=="R09": oldctx["source_station_names"] = ["수내역"]
    if rid=="R10": oldctx["spoken_schools"] = ["용현중학교","용현여자중학교","인항고등학교"]
    ci = context["regions"].index(C[rid])
    mi = maps["assets"].index(M[rid])
    cfields = [field("context",f"/regions/{ci}/representative",C[rid]["representative"])]
    selected = []
    for key, names in [("schools_shown_near_representative",oldctx["spoken_schools"]),("stations_shown_near_representative",oldctx["source_station_names"])]:
        for name in names:
            row = next(x for x in C[rid][key] if x["name"]==name)
            actual = next(label for label in M[rid]["displayed_detail_labels"] if norm(label)==norm(name))
            j = C[rid][key].index(row)
            cfields.append(field("context",f"/regions/{ci}/{key}/{j}",row))
            selected.append({"type":"school" if key.startswith("schools") else "station", "source_name":name,"displayed_label":actual,
                             "spoken_name": {"용마산(용마폭포공원)":"용마산역","잠실(송파구청)":"잠실역","아라(북부법원, 검찰청)":"아라역"}.get(name,actual),
                             "source_record_date":row["source_record_date"], "straight_distance_m":row["straight_distance_m"]})
    cfields.append(field("maps",f"/assets/{mi}/displayed_detail_labels",M[rid]["displayed_detail_labels"]))
    contextid = register(f"W4V2-{rid}-CONTEXT-MATCHED", "source_names_matched_to_displayed_label_manifest",cfields,
                          match_scope="공식 위치자료와 map_assets의 실제 표시명 목록 대조; 이번 담당의 지도 픽셀 검수 아님",
                          usage_bounds="학교 배정·도보시간·완전한 최인접역 판정 없음")
    selected_context[rid] = {"representative_complex":C[rid]["representative"],"selected_facilities":selected,
                             "matched_price_map":M[rid]["file"],"map_manifest_field":f"/assets/{mi}",
                             "displayed_detail_labels":M[rid]["displayed_detail_labels"],
                             "matching_status":"selected_facilities_all_matched_in_label_manifest",
                             "commerce_labels_screen_only":[x for x in M[rid]["displayed_detail_labels"] if x.startswith("상업:")],
                             "source_osm_available":M[rid]["source_osm_available"],"pixel_inspection_performed_by_writer":False}
    a = {cid.split(f"V3-{rid}-")[-1]:cid for cid in registry if cid.startswith(f"V3-{rid}-")}
    a.update({"photo":f"W4-{rid}-PHOTO","rank":f"W4-{rid}-RANK","context":contextid,"price":priceid})
    aliases[rid]=a

# v1과 동일한 계획용 속도. 새 원고의 실제 음성은 아직 없습니다.
baseline = paths["baseline_script"].read_text(encoding="utf-8-sig")
baseline_chars = len(re.sub(r"\s","","".join(l for l in baseline.splitlines() if l and not l.startswith("#"))))
rate = baseline_chars / 736.9497052154195


def estimate(sentences):
    chars = len(re.sub(r"\s","","".join(s["text"] for s in sentences)))
    sec = round(chars/rate,1)
    return {"status":"estimate_only_not_TTS_measured","seconds":sec,"range_seconds":[math.floor(sec*.85),math.ceil(sec*1.15)],"nonspace_characters":chars,
            "basis":"기존 v6 원고 공백 제외 문자수와 기존 실제 음성 길이 참고; 새 발음·호흡·사진 hold·브랜드 길이에 따라 변경"}


def make_sentence(sceneid, number, text, ids, role, phase):
    ids = list(dict.fromkeys(ids))
    instruction = {
        "full_district":"왼쪽 구 전체와 가격 점을 먼저 보여주고 오른쪽 대표 생활권 상세 범위를 연결합니다.",
        "focused_feature":"발화한 주거·업무·교통 권역만 강조합니다. 대표단지 밖 장소는 왼쪽 전체지도 또는 검증된 별도 위치 자료에 연결합니다.",
        "landmark_photo":"지역 특성 설명 직후 오른쪽에 실제 장소 사진을 읽을 호흡으로 보여줍니다. 실제 피사체·촬영연도·크레딧을 유지하고 왼쪽 전체 위치는 남깁니다.",
        "focused_context":"오른쪽 실제 대표단지 상세에서 선택 시설 라벨을 발화 순서대로 강조합니다. 상업시설은 이미 표시된 마름모를 생활 동선의 확인 대상으로 읽고 새 영업 사실은 덧붙이지 않습니다.",
        "price_selected":"가격 대비 한 개만 발화 순서대로 추가합니다. 집단명·금액·거래 n 또는 단지 n·면적·기간은 화면에 함께 표시합니다.",
        "decision_context":"생활권·직장·학교·철도·장보기 중 말하는 대상의 관계를 설명합니다. 확인할 경로는 비교 기준으로 제시하고 실제 소요시간을 만들지 않습니다.",
        "intro":"한 문장에 해당하는 범례/출처/레이어만 순서대로 강조합니다. 설명 주석은 화면·근거로 분리하고 낭독을 늘리지 않습니다.",
        "outro":"지도 위 예산→출근 목적지→학교·상권 비교 순서를 짧게 정리하고 다음 편/CTA를 연결합니다.",
    }[phase]
    return {"sentence_id":f"{sceneid}-V2-{number:02d}","text":text,"narration_text":text,"claim_ids":ids,
            "source_fields":[{"claim_id":cid,"path":f["path"],"field":f["field"]} for cid in ids for f in registry[cid]["source_fields"]],
            "statement_type":role,"interpretation_explicit":role=="interpretation","map_phase":phase,
            "material_types":["real_photo"] if phase=="landmark_photo" else ["map"],"screen_role":"explanation",
            "screen_direction":{"layout":"왼쪽 구 전체 가격분포+오른쪽 대표 생활권 상세 고정","speech_linked_action":instruction},
            "asset_status":"기존 실제 사진·완성 지도판 메타데이터에 연결; writer 픽셀 검수 미실시"}


scenes = []
for part in [1,2]:
    sid = f"P{part:02d}-INTRO"
    rows = [
        ("같은 예산에서 어느 생활권까지 비교할 수 있는지, 신혼부부 거주 순위와 지도로 살펴보겠습니다." if part==1 else
         "앞편의 20~11위에 이어, 이번에는 상위 열 곳에서 예산과 생활권의 차이를 살펴보겠습니다.", [new_request],"editorial"),
        (f"국가데이터처의 2024년 11월 1일 신혼부부 거주 수 기준으로, 수도권 53개 구 중 {'20위부터 11위' if part==1 else '10위부터 1위'}까지 소개합니다.",["W4-RANK-SCOPE"],"inherited_fact"),
        ("점 하나는 위치가 확인된 아파트 한 단지의 중위가격이며, 색은 5억 미만·5~7억·7~10억·10~15억·15~20억·20억 이상 여섯 구간입니다.",["W4-METHOD","W4-LEGEND"],"method"),
        ("왼쪽은 구 전체 가격, 오른쪽은 학교·역·상업시설 상세이며, 가격은 전용83~85제곱미터의 2026년 5~10월 계약을 11월 3일 조회한 값입니다.",["W4-METHOD","W4-LEGEND",new_request],"method"),
        (f"10월 계약은 조회일까지의 신고분을 기준으로, {'20위 원미구' if part==1 else '10위 미추홀구'}부터 시작하겠습니다.",["W4-METHOD",new_request],"positive_date_condition"),
    ]
    items = [make_sentence(sid,i,t,ids,role,"intro") for i,(t,ids,role) in enumerate(rows,1)]
    scenes.append({"scene_id":sid,"part":part,"scene_kind":"intro","title":"가격과 생활권을 읽는 짧은 도입",
                   "sentences":items,"narration_text":"\n\n".join(t["text"] for t in items),"estimate":estimate(items),
                   "key_message":"거주 순위와 단지 가격 점을 생활권 상세 지도에 연결합니다.","approval_status":"pending_new_script_gate"})
    for rank in range(20 if part==1 else 10, 10 if part==1 else 0, -1):
        rid=f"R{rank:02d}"
        old=V[rid]
        sid=old["scene_id"]
        a=aliases[rid]
        items=[make_sentence(sid,1,old["sentences"][0]["text"],[a["rank"]],"inherited_fact","full_district")]
        for row in copy[rid]["sentences"]:
            if row[0]=="@price":
                text=copy[rid]["price"]["text"]
                ids=[a["price"],"W4-METHOD"]
                role,phase="observed_comparison","price_selected"
            else:
                text,role,keys,phase=row
                ids=[a[k] for k in keys]
            items.append(make_sentence(sid,len(items)+1,text,ids,role,phase))
        s={"scene_id":sid,"legacy_scene_id":old["legacy_scene_id"],"revision":"writer-v2","part":part,"scene_kind":"region",
           "rank":rank,"region_id":rid,"title":old["title"],"key_message":copy[rid]["price"]["text"] if copy[rid]["sentences"][-1][0]=="@price" else copy[rid]["sentences"][-1][0],
           "sentences":items,"narration_text":"\n\n".join(t["text"] for t in items),"estimate":estimate(items),
           "spoken_price_comparison":comparisons[rid],"context_selection":selected_context[rid],
           "material_types":["map","real_photo"],"landmark_photo":old["landmark_photo"],
           "screen_values_only":{"all_observed_prices":P[rid],"basis":"scene_proposals_v1.json 및 region_insights.json의 지역·동·준공집단·6구간 수치 보존",
                                  "display_rule":"해당 해석에 필요한 값만 화면에서 선택. 나머지 수치의 연속 낭독·완성 차트 재삽입 없음",
                                  "price_statistic_labels":{"region_dong_cohort":"거래 중위값·거래 n","point_band":"단지별 중위값·지도 연결 단지 n"}},
           "production_notes_only":{"editorial_cautions":old["editorial_cautions"],"source_date_rule":"거주2024-11-01/가격2026-05~10·조회11-03/학교2026-10-01/역 레코드 날짜 각각 표기",
                                    "denominator_rule":"구·동·준공집단은 거래마다 한 표; 지도는 위치 확인 단지마다 한 점",
                                    "scope_bounds":"학교 배정·도보시간·완전한 최인접역·가격 원인·현재 매물·미래 수익 판단으로 확대하지 않음",
                                    "cohort_display":"2000년 이전이라는 입력 라벨의 실제 연산은 2000년 포함; 화면은 2000년까지 준공",
                                    "photo_rule":"사진의 자료연도·실제 장소 유지. 현재 시설을 과거 사진에 합성하지 않음"},
           "approval_status":"pending_new_script_gate","tts_generated":False}
        scenes.append(s)
    sid=f"P{part:02d}-OUTRO"
    rows = ([
        "같은 구 안에서도 예산과 철도 이용 방향, 학교와 장보기 동선에 따라 비교할 생활권은 달라집니다.",
        "다음 편은 미추홀구부터 2024년 당시 인천 서구까지, 10위에서 1위를 같은 지도 범례로 이어 보겠습니다.",
        "상위 열 곳의 생활권과 가격도 함께 비교하실 분들은 구독과 좋아요를 부탁드립니다.",
    ] if part==1 else [
        "집을 고를 때는 감당할 예산으로 후보 동을 좁히고, 두 사람의 실제 직장 주소에서 집까지 연결해 보는 순서가 유용합니다.",
        "그다음 학교·역·장보기 동선과 집의 연식·현재 상태를 함께 맞추면, 우리 부부에게 필요한 조건이 구체화됩니다.",
        "앞편의 20~11위도 같은 가격 범례로 비교해 보시고, 이어지는 지역 비교도 보실 분들은 구독과 좋아요를 부탁드립니다.",
    ])
    items=[make_sentence(sid,i,t,[new_request],"interpretation" if i<3 else "CTA","outro") for i,t in enumerate(rows,1)]
    scenes.append({"scene_id":sid,"part":part,"scene_kind":"outro","title":"비교 기준과 다음 연결","sentences":items,
                   "narration_text":"\n\n".join(t["text"] for t in items),"estimate":estimate(items),
                   "key_message":"예산·출근·생활 동선으로 후보를 좁힙니다.","approval_status":"pending_new_script_gate",
                   "silent_tail":"마지막 발화 뒤3초는 실제 타임록에서 확보"})

for scene in scenes:
    scene["claim_ids"] = list(dict.fromkeys(cid for item in scene["sentences"] for cid in item["claim_ids"]))

feature_stations = {"R19":["신내역"],"R18":["구성역"],"R15":["신도림역"],"R10":["주안역"],"R07":["고덕역"],"R03":["삼송역"]}
feature_issues=[]
for rid,names in feature_stations.items():
    feature_issues.append({"scene_id":V[rid]["scene_id"],"region_id":rid,"named_stations":names,
                           "problem":"공식 검증된 지역 특성/사진 대상 역이나 현재 대표단지 확대지도 라벨 목록 밖에 있음",
                           "proposal":"해당 발화는 실제 장소 사진에 연결하고, 필요한 전체지도 위치 라벨은 검증된 좌표로 visual 담당이 추가. 대표단지 상세의 다른 역과 혼합하지 않음",
                           "evidence":["scene_proposals_v2.json#/claim_registry",rel(paths["maps"])],"impact":"추가 지도 표시 확인은 후속 visual/QA 항목"})
dump(HERE/"issue_W4V2-FEATURE-STATION-LABELS.json", {"issue_id":"W4V2-FEATURE-STATION-LABELS","status":"open_visual_followup","to":["director","visual"],"items":feature_issues,
     "resolved_representative_label_changes":[{"scene_id":"P02-R10","removed_spoken":"인천용현남초등학교","replacement":"인항고등학교"},{"scene_id":"P02-R09","removed_spoken":"서현역","replacement":"수내역"}],
     "communication":"직접 peer 메시지 도구 없이 writer 폴더 이슈로 인계"})

payload={"revision":"top20-split-v4-writer-v2","task_id":"two-part-v4-script-v2","status":"writer_draft_for_review_pending_new_script_gate",
         "input_revisions":[{"key":k,"path":rel(p),"sha256":sha(p)} for k,p in paths.items()],"v1_preservation_manifest":"v1_preservation_manifest.json",
         "approval":{"script":"pending_new_decision_not_approved","decision_id":None,"v1_or_v6_approval_inherited":False,"tts_generated":False,"new_main_video_generated":False,"paid_calls":0,"uploads":0,"external_exports":0},
         "duration_guidance":{"per_part_seconds":[480,660],"kind":"estimate_guidance_not_duration_lock","read_rate_reference_nonspace_chars_per_second":rate},
         "price_and_map_contract":deepcopy(v1["price_and_map_contract"]),"claim_registry":registry,"scenes":scenes,
         "map_status":{"manifest":rel(paths["maps"]),"static_maps":len(maps["assets"]),"osm_regions_available":sum(x["source_osm_available"] for x in M.values()),
                       "representative_school_station_label_match":"58 selected facilities matched to prices asset displayed_detail_labels with terminal 역 normalization",
                       "writer_pixel_inspection":False,"silent_motion_sample_status":"상위가30초HF렌더/decode완료로 전달; writer 직접 재생/청취 없음"},
         "production_notes_only":{"rank_scope":"2024-11-01 거주·혼인신고후5년미경과·초혼/재혼합계·쌍단위, 53개구 범위",
                                  "price_denominators":"단지 점은 단지별 중위값 하나; 구/동/연식 집단은 거래마다 한 표",
                                  "legend_rule":"하한포함·상한미포함, 두 편 동일 여섯 색",
                                  "facility_symbols":"학교□, 역둥근□, 상업시설◇; 원자료 날짜를 표기",
                                  "cautions":"학교 배정·도보시간·최인접역·가격 인과·현장 최신성 확대를 피하는 제한은 제작 근거에 유지",
                                  "unspoken_values":"20지역의 구·동·연식·단지 분포 원수치를 screen_values_only에 보존"},
         "narration_handoff":deepcopy(v1["narration_handoff"]),
         "open_issue_ids":["W4V2-FEATURE-STATION-LABELS","W4V2-INDEPENDENT-QA-SCRIPT-GATE"]}
payload["narration_handoff"]["delivery"]="차분한 합니다체. 지역 특성→실제 장소 사진→학교·역 공간 관계→선택한 가격 대비를 장면의 흐름에 맞춰 읽습니다. 숫자·주의사항의 연속 낭독을 늘리지 않습니다."
payload["narration_handoff"]["timing_basis"]="v2 estimate only; 새 script 승인 후 실제 음성·사진 hold·브랜드 길이로 타임록"
for entry in payload["narration_handoff"]["pronunciation_dictionary"]:
    if entry["display"] in {"용마산(용마폭포공원)","잠실(송파구청)","아라(북부법원, 검찰청)"}:
        entry["display"] += "역"
        entry["map_label"] = entry["display"]
dump(HERE/"scene_proposals_v2.json",payload)

for part in [1,2]:
    ss=[s for s in scenes if s["part"]==part]
    total=estimate([t for s in ss for t in s["sentences"]])
    md=[f"# 신혼부부 거주 TOP20 — {part}편 {'20~11위' if part==1 else '10~1위'} 대본 v2","",
        "**새 대본 승인 대기 검토본입니다. v1은 보존했습니다.**","",
        f"전체 예상 약 **{total['seconds']/60:.1f}분 · estimate**. 8~11분은 편성 가이드이며 실제 음성·사진 호흡·브랜드 길이로 확정합니다.","",
        "도입은 5문장, 지역은 생활권 설명을 중심으로 구성했습니다. 지역당 가격 대비 한 개를 낭독하며, 전체 원수치와 주의사항은 장면 제안 JSON의 화면값·제작 근거에 있습니다.","",
        "## 낭독 원고"," "]
    for s in ss:
        md += [f"### {s['scene_id']} · {s['title']}", ""]
        for t in s["sentences"]:md += [t["text"],""]
    md += ["## 제작 메모 — 낭독 제외","",
           "왼쪽은 구 전체 가격분포, 오른쪽은 대표 생활권의 실제 학교·역·상업시설 상세입니다. 전체 위치를 먼저 읽고 상세로 연결하며, 지역 특성 뒤 실제 장소 사진을 보여줍니다.","",
           "표시: 5억 미만 / 5≤가격<7억 / 7≤가격<10억 / 10≤가격<15억 / 15≤가격<20억 / 20억 이상. 학교□ / 역둥근□ / 상업시설◇. 면적·기간·건수와 자료 기준일을 화면에 붙입니다.","",
           "기준: 가격2026년5~10월계약·11월3일조회·전용83~85㎡. 동/연식 중위값은 거래마다 한 표, 지도 분포는 위치확인 단지마다 한 점입니다. 관측2304단지14303건 중 지도2094단지12829건입니다.","",
           "학교 배정·도보시간·완전한 최인접역 판정 및 가격 인과·현재 매물·미래 수익으로의 확대는 제작 근거에서 제한합니다. 사진의 실제 피사체·촬영연도와 기존 검증 범위를 계승합니다.","",
           "지도40판·OSM20/20은 전달받은 완료 상태와 자산 목록으로 확인했습니다. 이 writer는 지도 픽셀이나 30초 모션 시안을 직접 재생·검수하지 않았습니다.","",
           "대표 상세도 시설명은 map_assets.json의 prices 자산 displayed_detail_labels와 대조했습니다. 미추홀구는 인항고등학교, 분당구는 수내역으로 낭독을 교체했습니다. 별도 지역 특성 역의 전체지도 추가 표시는 issue_W4V2-FEATURE-STATION-LABELS.json으로 인계합니다.","",
           "|장면|문장 수|예상 길이|가격 대비|","|---|---:|---:|---|"]
    for s in ss:
        kind=s.get("spoken_price_comparison",{}).get("type","—")
        md.append(f"|{s['scene_id']}|{len(s['sentences'])}|{s['estimate']['seconds']:.0f}초·estimate|{kind}|")
    md += ["","문장별 claim_ids·source_fields·map_phase·해석 구분과 선택 시설의 원자료 날짜는 scene_proposals_v2.json에 있습니다. 새 script 결정·독립 QA 이후 narration 담당이 실제 음성과 타임록을 진행합니다.",""]
    (HERE/f"part{part}_script_v2.md").write_text("\n".join(md),encoding="utf-8")

assert all(sha(HERE/x["path"])==x["sha256"] for x in read(preserve_path)["files"])
print(json.dumps({"parts":[{"part":part,"sentences":sum(len(s['sentences']) for s in scenes if s['part']==part),"estimate_seconds":round(sum(s['estimate']['seconds'] for s in scenes if s['part']==part),1),"intro_seconds":next(s['estimate']['seconds'] for s in scenes if s['part']==part and s['scene_kind']=='intro')} for part in [1,2]],
                  "region_seconds":[[s['region_id'],len(s['sentences']),s['estimate']['seconds']] for s in scenes if s['scene_kind']=='region']},ensure_ascii=False))
