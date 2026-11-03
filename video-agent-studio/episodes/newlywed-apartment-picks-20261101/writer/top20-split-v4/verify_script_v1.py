"""원고를 입력값·분모·시설명·필드 경로와 대조하고 자체 검증 범위를 기록합니다."""
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
EP = HERE.parents[1]
ROOT = EP.parents[2]
read = lambda p: json.loads(p.read_text(encoding="utf-8-sig"))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
data = read(HERE / "scene_proposals_v1.json")
regions = [s for s in data["scenes"] if s["scene_kind"] == "region"]
inputs = {x["key"]: x for x in data["input_revisions"]}
price = {r["region_id"]: r for r in read(ROOT / inputs["prices"]["path"])["regions"]}
rank = {r["region_id"]: r for r in read(ROOT / inputs["ranking"]["path"])["regions"]}
context = {r["region_id"]: r for r in read(ROOT / inputs["context"]["path"])["regions"]}
facts = read(ROOT / inputs["facts"]["path"])
checks = []


def check(name, result, evidence=None):
    checks.append({"check": name, "result": "pass" if result else "fail", "evidence": evidence})


check("두 편 각 10지역의 순서", all([s["rank"] for s in regions if s["part"]==part] == list(range(20 if part==1 else 10, 10 if part==1 else 0, -1)) for part in [1,2]))
check("지역별 8~11문장", all(8<=len(s["sentences"])<=11 for s in regions))
check("지역별 예상 길이 50~75초", all(50<=s["estimate"]["seconds"]<=75 for s in regions), "추정값만 검사; 실제 새 음성 길이 검사 아님")
check("새 대본 승인 미승계", data["approval"]["script"]=="pending_new_decision_not_approved" and data["approval"]["prior_v6_approval_inherited"] is False)
check("단지·거래 커버리지 합계", (sum(r["mapped_complexes"] for r in price.values()), sum(r["observed_complexes"] for r in price.values()), sum(r["mapped_transaction_n"] for r in price.values()), sum(r["transaction_n"] for r in price.values())) == (2094,2304,12829,14303))
used = {cid for s in data["scenes"] for t in s["sentences"] for cid in t["claim_ids"]}
fact_ids = {c["claim_id"] for r in facts["regions"] for c in r["claims"]}
check("기존 검증 주장 51개와 기흥구 보충 근거 연결", len(fact_ids)==51 and fact_ids <= used and "V3-R18-DIR-H03" in used)

all_ids = [t["sentence_id"] for s in data["scenes"] for t in s["sentences"]]
check("문장 ID 고유성", len(all_ids)==len(set(all_ids)))
json_cache = {}
field_errors = []
for cid, c in data["claim_registry"].items():
    for f in c["source_fields"]:
        p = ROOT / f["path"]
        if not p.is_file():
            field_errors.append([cid,"missing_file",f["path"]]);continue
        pointer = f["field"]
        if p.suffix == ".json" and pointer.startswith("/"):
            try:
                obj = json_cache.setdefault(str(p), read(p))
                if "*" in pointer:
                    head, tail = pointer.split("/*/",1)
                    for key in head.strip("/").split("/"):
                        obj = obj[int(key)] if isinstance(obj,list) else obj[key]
                    vals = [r[tail] for r in obj]
                    assert all(isinstance(n,int) for n in vals)
                else:
                    for key in pointer.strip("/").split("/"):
                        obj = obj[int(key)] if isinstance(obj,list) else obj[key]
                    if "value" in f and f["value"] is not None:
                        assert obj == f["value"], f"value mismatch {pointer}"
            except Exception as e:
                field_errors.append([cid,str(e),pointer])
        elif pointer.startswith("heading:"):
            if pointer.split(":",1)[1] not in p.read_text(encoding="utf-8-sig"):
                field_errors.append([cid,"heading_missing",pointer])
        elif pointer.startswith("line:"):
            if pointer.split(":",1)[1] not in p.read_text(encoding="utf-8-sig"):
                field_errors.append([cid,"line_missing",pointer])
check("출처 파일·JSON 필드·기록값 연결", not field_errors, field_errors)

for s in regions:
    rid = s["region_id"]
    p = price[rid]
    pc = s["price_comparison"]
    c = s["context_selection"]
    check(rid+" 순위와 거주쌍 일치", s["rank"]==rank[rid]["rank"] and f"{rank[rid]['newlywed_couples']:,}쌍" in s["sentences"][0]["text"])
    check(rid+" 구 거래 중위값·건수", pc["regional_median_manwon"]==p["region_median_manwon"] and pc["regional_transaction_n"]==p["transaction_n"])
    check(rid+" 두 동 거래 중위값·건수·최소20건", len(pc["dong_comparisons"])==2 and all(d in p["dong_prices_by_transaction_count"] and d["transaction_n"]>=20 for d in pc["dong_comparisons"]))
    check(rid+" 지도 분모·6구간", pc["mapped_complexes"]==p["mapped_complexes"] and len(pc["mapped_bands"])==6 and sum(b["complex_n"] for b in pc["mapped_bands"])==pc["mapped_complexes"] and all(b["denominator"]==pc["mapped_complexes"] for b in pc["mapped_bands"]))
    check(rid+" 시설2~3곳·명칭 일치", 2<=len(c["spoken_schools"])+len(c["source_station_names"])<=3 and all(n in {r["name"] for r in context[rid]["schools_shown_near_representative"]} for n in c["spoken_schools"]) and all(n in {r["name"] for r in context[rid]["stations_shown_near_representative"]} for n in c["source_station_names"]))
    check(rid+" 전체지도→특성상세→사진→가격→시설상세", [t["map_phase"] for t in s["sentences"]] == ["full_district","focused_feature","landmark_photo","regional_price","dong_price_compare","dong_price_compare","complex_band_distribution","observed_contrast","focused_context","two_budget_conditions"])
    check(rid+" 문장별 근거·자료유형·동작", all(t["source_fields"] and t["claim_ids"] and t["material_types"] and t["screen_direction"]["speech_linked_action"] for t in s["sentences"]))
    check(rid+" 2000년 포함 범위 명확화", "2000년 이전" not in s["narration_text"])

doc_checks = []
for part in [1,2]:
    p = HERE / f"part{part}_script_v1.md"
    text = p.read_text(encoding="utf-8")
    ss = [s for s in data["scenes"] if s["part"]==part]
    # 원고 단락만 추출하여 장면 제안과 공백·수치까지 대조합니다.
    blocks = re.findall(r"### 낭독 원고\n\n(.*?)\n### 화면·근거 메모",text,re.S)
    expected = ["\n\n".join(t["text"] for t in s["sentences"]) for s in ss]
    check(f"{part}편 읽는 원고와 장면 제안 동일", [b.strip() for b in blocks]==expected)
    spoken = " ".join(t["text"] for s in ss for t in s["sentences"])
    check(f"{part}편 통계범위 한 번·공통범례·분모·주의", spoken.count("53개 구")==1 and all(x in spoken for x in ["2024년 신혼부부통계","2026년 5~10월","11월 3일","20억 이상","거래마다 한 표","배정이나 도보시간"]))
    check(f"{part}편 유입·다음 연결", "구독과 좋아요" in spoken and ("다음 편" if part==1 else "앞편의 20~11위") in spoken)
    doc_checks.append({"part":part,"path":str(p.relative_to(ROOT)).replace("\\","/"),"sha256":sha(p),"scenes":len(ss),"sentences":sum(len(s["sentences"]) for s in ss),"estimate_seconds":round(sum(s["estimate"]["seconds"] for s in ss),1)})

script_text = " ".join(t["text"] for s in data["scenes"] for t in s["sentences"])
check("원고에 도보분·배정·미래가격 보장 표현 없음", not re.search(r"도보\s*\d+\s*분|배정됩니다|진학합니다|반드시 오릅니다|수익률을 보장",script_text))
changed_inputs = [i["path"] for i in data["input_revisions"] if sha(ROOT/i["path"])!=i["sha256"]]
check("생성 입력 해시 고정",not changed_inputs,changed_inputs)

report = {
    "task_id":"two-part-v4-script", "status":"pass" if all(x["result"]=="pass" for x in checks) else "fail",
    "verification_kind":"writer_self_check_not_independent_QA",
    "checked_artifact_sha256":sha(HERE/"scene_proposals_v1.json"),
    "counts":{"parts":2,"scenes":len(data["scenes"]),"regions":len(regions),"sentences":len(all_ids),"existing_verified_claims_used":len(fact_ids & used),"director_supplement_claims_used":1,"facility_mentions":sum(len(s["context_selection"]["spoken_schools"])+len(s["context_selection"]["source_station_names"]) for s in regions),"checks":len(checks),"failed_checks":sum(x["result"]!="pass" for x in checks)},
    "parts":doc_checks,"checks":checks,
    "not_performed":["새 웹 사실조사", "독립 대본 QA", "시설 좌표와 실제 v4 지도 표시 매칭", "OSM 레이어 확보·완전성 검사", "새 사진 픽셀·권리 재검수", "TTS·음성 청취·실측 타이밍", "렌더·연속 재생", "유료 호출·업로드·외부 내보내기"],
}
(HERE/"validation_v1.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"status":report["status"],"counts":report["counts"],"parts":doc_checks,"failures":[x for x in checks if x["result"]!="pass"]},ensure_ascii=False))
raise SystemExit(0 if report["status"]=="pass" else 1)
