"""최종 v6의 실제 표시문/읽기문을 가격 입력과 비교한다. 원거래 재집계 없음."""
import datetime
import hashlib
import json
import re
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
JSON_SHA = "8beec59448e180617327f17913aaa25277b3152769a1815cbdc493351003803e"
MD_SHA = "4259f50a9c5cadbadd864d838559a16f85e07316818ddcb31ce40939fbccac38"
NOW = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat()


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def korean_number(value):
    value = re.sub(r"\s", "", value)
    native = {"한": 1, "두": 2, "세": 3, "네": 4, "다섯": 5, "여섯": 6, "일곱": 7, "여덟": 8, "아홉": 9, "열": 10, "열세": 13, "열여섯": 16, "스무": 20, "스물두": 22, "서른다섯": 35}
    if value in native:
        return native[value]
    digits = dict(zip("영일이삼사오육칠팔구", range(10)))
    small = {"십": 10, "백": 100, "천": 1000}
    total = section = digit = 0
    for char in value:
        if char in digits:
            digit = digits[char]
        elif char in small:
            section += (digit or 1) * small[char]
            digit = 0
        elif char in "만억":
            total += (section + digit or 1) * {"만": 10000, "억": 100000000}[char]
            section = digit = 0
        else:
            raise ValueError("숫자 외 문자가 포함됨: " + repr(value))
    return total + section + digit


jpath = OUT / "reviewed-inputs" / (JSON_SHA + "_scene_proposals_v6.json")
mpath = OUT / "reviewed-inputs" / (MD_SHA + "_script_v6.md")
assert sha(jpath) == JSON_SHA and sha(mpath) == MD_SHA
data = load(jpath)
md = mpath.read_text(encoding="utf-8-sig")
panel_path = ROOT / "director/top20-explain-v3/price_panel_data.json"
panel = load(panel_path)
pi = {x["region_id"]: x for x in panel["regions"]}
top_path = ROOT / "research/top20-8min-v2/top20.json"
top = {x["region_id"]: x for x in load(top_path)["regions"]}
sentences = {x["sentence_id"]: x for s in data["scenes"] for x in s["sentences"]}
md_sentences = {}
for line in md.splitlines():
    match = re.match(r"^\*\*\[([^]]+)\]\*\*\s*(.*)$", line)
    if match:
        md_sentences[match[1]] = match[2].strip()
regional_scenes = [x for x in data["scenes"] if x.get("region_id")]
checks = {
    "md_json_sentence_identity": md_sentences == {k: v["text"] for k, v in sentences.items()},
    "twenty_region_countdown": len(regional_scenes) == 20 and [x["rank"] for x in regional_scenes] == list(range(20, 0, -1)),
    "formal_style": all(x["text"].endswith("니다.") for x in sentences.values()),
    "source_spoken_once_at_opening": sum(x["text"].count("국가데이터처") for x in sentences.values()) == 1 and "국가데이터처" in sentences["O002-01"]["text"],
    "no_repetitive_negative_boilerplate": not any(re.search("아닙니다|아님|읽을 수는 없습니다", x["text"]) for x in sentences.values()),
    "definition_restored": "혼인신고 후 5년이 지나지 않은" in sentences["O002-02"]["text"] and "혼인신고 후 오 년이 지나지 않은" in sentences["O002-02"]["reading_text"] and "초혼과 재혼" in sentences["O002-02"]["text"],
    "price_snapshot_spoken": all(t in sentences["O002-07A"]["text"] for t in ["2026년 5월부터 10월", "2026년 11월 3일", "매매 실거래"]),
    "area_endpoints_spoken": all(t in sentences["O002-07B"]["text"] for t in ["83제곱미터 이상", "85제곱미터 이하"]),
    "october_reporting_spoken": all(t in sentences["O002-07D"]["text"] for t in ["신고가 진행 중", "정정·해제"]),
    "price_input_lock": data["price_input_lock"]["panel_sha256"] == sha(panel_path),
    "all_claim_ids_registered": all(c in data["claim_registry"] for x in sentences.values() for c in x["claim_ids"]),
    "tts_render_gate_closed": data["script_gate"]["tts_allowed"] is False and data["script_gate"]["main_render_allowed"] is False and data["timing_locked"] is False,
}
opening = next(s for s in data["scenes"] if s["scene_id"] == "O002")
conditions = " ".join(x.get("on_screen_conditions", "") for x in opening["screen_beats"])
checks["full_conditions_visible_direction"] = all(x in conditions for x in ["전체 층", "중개+직거래", "해제행 제외", "n=유효 기록 수", "83~85㎡", "2026.11.03"])
rows = []
for scene in regional_scenes:
    p = pi[scene["region_id"]]
    rep = p["representative"]
    t = top[scene["region_id"]]
    si = {x["sentence_id"]: x for x in scene["sentences"]}
    sid = scene["scene_id"]
    local = {"price_panel_same": scene["price_panel_data"] == p, "rank_count": f"{t['newlywed_couples']:,}쌍" in si[sid + "-01"]["text"] and scene["rank"] == t["rank"]}
    prices = []
    for tail, expected_price, expected_n in [("20", p["median_manwon"], p["n"]), ("21", rep["median_manwon"], rep["n"])]:
        s = si[sid + "-" + tail]
        expected_display = p["display_price"] if tail == "20" else rep["display_price"]
        canonical = re.sub(r"\s", "", s["text"])
        amount = re.search(r"중위값[은이]\s+(.+?)원입니다\.$", s["reading_text"])
        count = re.search(r"거래\s+(.+?)\s+건의", s["reading_text"]) if tail == "20" else re.search(r"같은 조건\s+(.+?)\s+건의", s["reading_text"])
        spoken_won = korean_number(amount[1])
        spoken_n = korean_number(count[1])
        ok = expected_display in canonical and f"{expected_n:,}건" in canonical and spoken_won == expected_price * 10000 and spoken_n == expected_n
        local["price_n_display_reading_" + tail] = ok
        prices.append({"sentence_id": s["sentence_id"], "expected_manwon": expected_price, "expected_n": expected_n, "parsed_reading_won": spoken_won, "parsed_reading_n": spoken_n, "pass": ok})
    local["complex_name_and_dong"] = rep["apt_name"] in si[sid + "-21"]["text"] and rep["legal_dong_name"] in si[sid + "-21"]["text"]
    feature_sentences = [x for x in scene["sentences"] if x["sentence_id"].split("-")[-1] in ["02", "03", "04"]]
    rows.append({"region_id": scene["region_id"], "scene_id": sid, "checks": local, "prices": prices, "feature_sentence_ids": [x["sentence_id"] for x in feature_sentences], "feature_claim_ids": sorted({c for x in feature_sentences for c in x["claim_ids"]}), "four_axis_manual_review": "주거특징+실제명소/역/업무권+구중위값+별도단지사례의 실제문장·범위 구분 확인", "photo_binding_scope": "입력검수의 사진20장 metadata/SHA/contact sheet 및 원고 화면연결 지시 재사용; 현장 지오로케이션/신규권리심사 아님"})
    checks[sid] = all(local.values())
minimum = min(panel["regions"], key=lambda p: p["median_manwon"])
maximum = max(panel["regions"], key=lambda p: p["median_manwon"])
checks["closing_minmax"] = (minimum["region_id"], maximum["region_id"]) == ("R10", "R06") and all(x in sentences["C001-01"]["text"] for x in ["미추홀구 4억원", "강남구 30억3,000만원", "지역 중위값"])
supp_path = ROOT / "research/top20-explain-v3/director_supplement.json"
supp = load(supp_path)["claims"][0]
checks["giheung_supplement_scope"] = sentences["S005-02"]["text"] == supp["text"] and sentences["S005-02"]["claim_ids"] == ["V3-R18-DIR-H03"] and not any(t in sentences["S005-02"]["text"] for t in ["고용 증가", "가격 상승", "명", "%"])
previous = load(OUT / "reviewed-inputs/401e2ade1a5d0eecb44aa8e033e09432baaedbfe3d80dcf6b66930884360e9ef_scene_proposals_v6.json")
before = {x["sentence_id"]: x["text"] for s in previous["scenes"] for x in s["sentences"]}
delta = [k for k in set(before) | set(sentences) if before.get(k) != sentences.get(k, {}).get("text")]
checks["last_delta_only_O002_02"] = delta == ["O002-02"]
failed = [k for k, passed in checks.items() if not passed]
report = {"checked_at": NOW, "revision": "final-v6-script-independent-review", "status": "passed" if not failed else "failed", "checked_revision": {"script_md_sha256": MD_SHA, "scene_json_sha256": JSON_SHA, "price_panel_sha256": sha(panel_path), "director_supplement_sha256": sha(supp_path)}, "method": "20地域 actual canonical/reading text review and independent parsing of spoken amounts/counts; no raw transaction/coordinate recalculation", "counts": {"regional_scenes": len(rows), "price_values": 40, "transaction_counts": 40, "population_values": 20, "sentences": len(sentences)}, "checks": checks, "failed_checks": failed, "regions": rows, "last_delta": delta, "semantic_review": {"all_20_four_axes": "검토완료", "source_and_asof": "국가데이터처 첫출처1회·2024 거주기준·2026 가격조회 분리", "giheung": "부모 공식페이지 검증의 지정 보완문구만 반영; 고용규모/인과관계 주장 없음; 새 외부검증 승계로 표시", "songpa": "구전체21억8500만원/n513와 잠실단지30억원/n9의 범위·구성 차이; 지역전형가격/매수추천으로 확대 없음", "closing": "20개지역 중위값 범위4억~30억3000만원; 모든 단지 또는 개별주택 최저/최고가로 표현하지 않음", "planning_vs_actual": "청라 계획기능·정비기본계획·과거준공·현재노선 구분; 새 미확인개통/취업/가격원인 확정 없음", "photo_and_place": "신내2015사진/현재노선·청라/검단·여의도/문래/신길·사진명소/단지별개 전환 지시 확인"}, "scope_limits": ["실제 음성 청취/발음/속도/실측타이밍 미검수", "실제MP4·연속재생·전체장면/경계/최대줌 미검수", "대표시안의 현재 이슈는 findings.json으로 분리", "대본 검수 통과는 사용자 script 승인 또는 TTS/본편렌더/업로드 권한이 아님"]}
write("script_review.json", report)
if failed:
    raise RuntimeError("최종 v6 검사실패: " + ", ".join(failed))
print(json.dumps({"status": report["status"], "counts": report["counts"], "failed_checks": failed, "last_delta": delta}, ensure_ascii=False))
