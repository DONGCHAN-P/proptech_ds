"""v2 변경 요구·수치·시설 표시명·v1 보존을 산출물에서 대조합니다."""
from collections import Counter
import hashlib
import json
import re
from pathlib import Path

HERE=Path(__file__).resolve().parent
EP=HERE.parents[1]
ROOT=EP.parents[2]
read=lambda p:json.loads(p.read_text(encoding="utf-8-sig"))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
data=read(HERE/"scene_proposals_v2.json")
regions=[s for s in data["scenes"] if s["scene_kind"]=="region"]
prices=read(EP/"research/top20-split-v4/prices/region_insights.json")
P={r["region_id"]:r for r in prices["regions"]}
context=read(EP/"research/top20-split-v4/context_notes.json")
C={r["region_id"]:r for r in context["regions"]}
maps=read(EP/"visual/top20-split-v4/map_assets.json")
M={r["region_id"]:r for r in maps["assets"] if r["mode"]=="prices"}
norm=lambda s:s.removesuffix("역")
ns=lambda s:len(re.sub(r"\s","",s))
checks=[]


def check(name,ok,evidence=None):
    checks.append({"check":name,"result":"pass" if ok else "fail","evidence":evidence})


def money(value):
    a,b=divmod(int(value),10000)
    return (f"{a}억" if a else "")+(f"{b:,}만원" if b else "원")


manifest=read(HERE/"v1_preservation_manifest.json")
check("v1 원고·장면표·검증·인계 등13파일 해시 보존",len(manifest["files"])==13 and all(sha(HERE/f["path"])==f["sha256"] for f in manifest["files"]))
check("두 편·20지역·24장면",len(data["scenes"])==24 and len(regions)==20)
check("20~11위와10~1위 순서",all([s["rank"] for s in regions if s["part"]==p]==list(range(20 if p==1 else 10,10 if p==1 else 0,-1)) for p in [1,2]))
check("새 승인 미승계·TTS/본편 생성 전",data["approval"]["script"]=="pending_new_decision_not_approved" and not data["approval"]["v1_or_v6_approval_inherited"] and not data["approval"]["tts_generated"] and not data["approval"]["new_main_video_generated"])

spoken=" ".join(t["text"] for s in data["scenes"] for t in s["sentences"])
negative_hits=re.findall(r"아니라|아닙|아님|않|못|없|뜻하지|구분합니다|보기 어렵|설명하기 어렵",spoken)
check("낭독의 부정형 회피 표현 제거",not negative_hits,negative_hits)
check("추정통근분·학교배정·상승보장 표현 없음",not re.search(r"도보\s*\d+\s*분|통근\s*\d+\s*분|배정됩니다|진학합니다|반드시 오릅니다|수익률 보장",spoken))

baseline=(ROOT/next(x["path"] for x in data["input_revisions"] if x["key"]=="baseline_script")).read_text(encoding="utf-8-sig")
old_regions={}
for heading,block in re.findall(r"^## (.*?)\n(.*?)(?=^## |\Z)",baseline,re.M|re.S):
    m=re.match(r"(\d+)위",heading)
    if m:old_regions[int(m.group(1))]=block.strip()
growth=[]
allmatches=[]
for s in regions:
    rid=s["region_id"]
    comp=s["spoken_price_comparison"]
    price_lines=[t for t in s["sentences"] if t["map_phase"]=="price_selected"]
    check(rid+" 낭독 가격 대비 정확히1개",len(price_lines)==1 and price_lines[0]["text"]==comp["spoken_text"])
    check(rid+" 다른 문장의 금액 연속 낭독 제거",all(not re.search(r"\d+(?:억|만원)",t["text"]) for t in s["sentences"] if t["map_phase"]!="price_selected"))
    if comp["type"] in {"dong_pair","cohort_pair"}:
        source=P[rid]["dong_prices_by_transaction_count" if comp["type"]=="dong_pair" else "build_cohorts"]
        ok=len(comp["rows"])==2 and all(row in source and row["transaction_n"]>=20 and money(row["median_manwon"]) in comp["spoken_text"] for row in comp["rows"])
    else:
        ok=all(row in P[rid]["mapped_bands"] for row in comp["rows"]) and str(P[rid]["mapped_complexes"]) in comp["spoken_text"] and all(str(row["complex_n"]) in comp["spoken_text"] for row in comp["rows"])
    check(rid+" 선택 대비의 원수치·건수·분모",ok)
    check(rid+" 나머지 가격 원수치 화면용 보존",s["screen_values_only"]["all_observed_prices"]==P[rid])
    check(rid+" 설명 문자비중70% 이상",sum(ns(t["text"]) for t in s["sentences"] if t["map_phase"] not in {"price_selected","full_district"})/ns(s["narration_text"])>=.70)
    check(rid+" 실제 장소 사진은 특성 설명 뒤",next(i for i,t in enumerate(s["sentences"]) if t["map_phase"]=="landmark_photo")>=2)
    check(rid+" 사실·해석·문장별근거·지도단계",all(t["statement_type"] and t["source_fields"] and t["claim_ids"] and t["map_phase"] and t["screen_direction"]["speech_linked_action"] for t in s["sentences"]))
    matches=s["context_selection"]["selected_facilities"]
    focused=" ".join(t["text"] for t in s["sentences"] if t["map_phase"]=="focused_context")
    unmatched=[]
    for f in matches:
        key="schools_shown_near_representative" if f["type"]=="school" else "stations_shown_near_representative"
        if not(any(x["name"]==f["source_name"] and x["source_record_date"]==f["source_record_date"] for x in C[rid][key]) and norm(f["source_name"])==norm(f["displayed_label"]) and f["displayed_label"] in M[rid]["displayed_detail_labels"] and f["displayed_label"] in focused):
            unmatched.append(f)
        allmatches.append({"scene_id":s["scene_id"],**f})
    check(rid+" 실제 표시 학교·역58곳 부분 매칭",not unmatched,unmatched)
    prior=ns(old_regions[s["rank"]])
    current=ns(s["narration_text"])
    growth.append({"region_id":rid,"old_v6_nonspace_chars":prior,"v2_nonspace_chars":current,"ratio":round(current/prior,2)})
    check(rid+" oldv6보다 지역설명 확대",current>prior)

check("가격 대비 구성3종으로 변경",set(s["spoken_price_comparison"]["type"] for s in regions)=={"dong_pair","cohort_pair","band_distribution"})
check("지역별 문장수 변화",len({len(s["sentences"]) for s in regions})>=3)
check("지역별 가격 대비의 배치 변화",len({next(i for i,t in enumerate(s["sentences"]) if t["map_phase"]=="price_selected") for s in regions})>=3)
check("40지도판·20/20 OSM 목록과 실제 파일 존재",len(maps["assets"])==40 and len(M)==20 and all(a["source_osm_available"] and (EP/a["file"].replace("\\","/")).is_file() for a in maps["assets"]))
check("가격 지도 점 합계2094",sum(x["point_count"] for x in M.values())==2094)
check("미추홀 인항고·분당 수내역 교체",all(("인항고등학교" in s["narration_text"] and "인천용현남초등학교" not in s["narration_text"]) if s["region_id"]=="R10" else ("수내역" in s["narration_text"] and "서현역" not in s["narration_text"]) if s["region_id"]=="R09" else True for s in regions))
feature_issue=read(HERE/"issue_W4V2-FEATURE-STATION-LABELS.json")
check("대표 상세 밖의 지역 특성 역6곳 이슈 인계",len(feature_issue["items"])==6 and {x["region_id"] for x in feature_issue["items"]}=={"R19","R18","R15","R10","R07","R03"})

field_errors=[]
cache={}
for cid,claim in data["claim_registry"].items():
    for f in claim["source_fields"]:
        p=ROOT/f["path"]
        if not p.is_file():field_errors.append([cid,"missing_file",f["path"]]);continue
        ptr=f["field"]
        try:
            if p.suffix==".json" and ptr.startswith("/"):
                if str(p) not in cache:cache[str(p)]=read(p)
                obj=cache[str(p)]
                if "*" in ptr:
                    head,tail=ptr.split("/*/",1)
                    for key in head.strip("/").split("/"):obj=obj[int(key)] if isinstance(obj,list) else obj[key]
                    assert all(isinstance(r[tail],int) for r in obj)
                else:
                    for key in ptr.strip("/").split("/"):obj=obj[int(key)] if isinstance(obj,list) else obj[key]
                    if "value" in f and f["value"] is not None:assert obj==f["value"]
            elif ptr.startswith("heading:") or ptr.startswith("line:"):
                assert ptr.split(":",1)[1] in p.read_text(encoding="utf-8-sig")
        except Exception as e:field_errors.append([cid,ptr,str(e)])
check("출처 파일·JSON 필드·기록값 일치",not field_errors,field_errors)
check("최종생성 입력 해시 고정",all(sha(ROOT/x["path"])==x["sha256"] for x in data["input_revisions"]))

parts=[]
for part in [1,2]:
    ss=[s for s in data["scenes"] if s["part"]==part]
    intro=ss[0]
    check(f"{part}편 INTRO5문장·35~45초 추정",len(intro["sentences"])==5 and 35<=intro["estimate"]["seconds"]<=45)
    sp=" ".join(t["text"] for s in ss for t in s["sentences"])
    check(f"{part}편 범위·면적기간·6가격대·시설 설명",all(x in intro["narration_text"] for x in ["2024년 11월 1일","53개 구","5억 미만","5~7억","7~10억","10~15억","15~20억","20억 이상","학교·역·상업시설","83~85","2026년 5~10월","11월 3일"]) and sp.count("53개 구")==1)
    check(f"{part}편 10월조건 한 번·긍정형",sp.count("10월 계약은 조회일까지의 신고분을 기준으로")==1)
    text=(HERE/f"part{part}_script_v2.md").read_text(encoding="utf-8")
    spoken_area=text.split("## 낭독 원고",1)[1].split("## 제작 메모",1)[0]
    blocks=re.findall(r"^### .*?\n\n(.*?)(?=^### |\Z)",spoken_area,re.M|re.S)
    check(f"{part}편 읽는원고와 장면제안 동일",[b.strip() for b in blocks]==[s["narration_text"] for s in ss])
    seconds=round(sum(s["estimate"]["seconds"] for s in ss),1)
    check(f"{part}편 8~11분 편성 가이드 추정",480<=seconds<=660,"실제TTS 길이·최종본 길이 통과 판정 아님")
    check(f"{part}편 CTA·다음 연결","구독과 좋아요" in sp and ("다음 편" if part==1 else "앞편의 20~11위") in sp)
    parts.append({"part":part,"path":f"part{part}_script_v2.md","sha256":sha(HERE/f"part{part}_script_v2.md"),"scenes":len(ss),"sentences":sum(len(s["sentences"]) for s in ss),"estimate_seconds":seconds,"intro_estimate_seconds":intro["estimate"]["seconds"]})

report={"task_id":"two-part-v4-script-v2","status":"pass" if all(c["result"]=="pass" for c in checks) else "fail",
        "verification_kind":"writer_self_check_not_independent_QA","scene_proposals_sha256":sha(HERE/"scene_proposals_v2.json"),
        "counts":{"parts":2,"regions":20,"scenes":24,"sentences":sum(len(s["sentences"]) for s in data["scenes"]),"selected_facility_labels_matched":len(allmatches),"checks":len(checks),"failed_checks":sum(c["result"]!="pass" for c in checks)},
        "parts":parts,"price_comparison_types":dict(Counter(s["spoken_price_comparison"]["type"] for s in regions)),
        "v6_comparison":growth,"facility_label_matches":allmatches,"checks":checks,
        "not_performed":["독립 QA", "지도 픽셀·30초 모션의 시각 검수/연속 재생", "새 TTS·음성 청취·실측 타임록", "새 본편 렌더", "유료 호출·외부 전송·업로드"],
        "open_issue_ids":data["open_issue_ids"]}
(HERE/"validation_v2.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"status":report["status"],"counts":report["counts"],"parts":parts,"price_comparison_types":report["price_comparison_types"],"v6_growth_range":[min(x["ratio"] for x in growth),max(x["ratio"] for x in growth)],"failures":[c for c in checks if c["result"]!="pass"]},ensure_ascii=False))
raise SystemExit(0 if report["status"]=="pass" else 1)
