"""부모 로컬 ASR 결과만 해석한다. 모델 실행/다운로드/오디오전송 없음."""
import datetime
import hashlib
import json
import re
from decimal import Decimal
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
D = ROOT / "director/top20-explain-v3"
NOW = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat()


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def amounts(text):
    pattern = r"\d[\d,]*(?:\.\d+)?\s*(?:억|천만|백만|만)(?:\s*\d[\d,]*(?:\.\d+)?\s*(?:억|천만|백만|만))*\s*원"
    result = []
    for match in re.finditer(pattern, text):
        expression = re.sub(r"[\s,원]", "", match[0])
        value = sum((Decimal(x[1]) * {"억": 100000000, "천만": 10000000, "백만": 1000000, "만": 10000}[x[2]] for x in re.finditer(r"(\d+(?:\.\d+)?)(억|천만|백만|만)", expression)), Decimal(0))
        result.append({"asr_expression": match[0], "won": int(value)})
    return result


lock = load(D / "locked_timing.json")
scenes = {s["scene_id"]: s for s in lock["scenes"] if s.get("audio_path")}
reports, manifest = {}, []
for model in ["small", "medium"]:
    reports[model] = {}
    for path in sorted((D / "evidence/audio-asr" / model).glob("*.json")):
        report = load(path)
        if "scene_id" not in report:
            continue
        sid = report["scene_id"]
        assert report["audio_sha256"] == scenes[sid]["audio_sha256"], sid
        assert report["external_audio_transfer"] is False
        reports[model][sid] = report
        manifest.append({"scene_id": sid, "model": model, "path": str(path.relative_to(ROOT)).replace("\\", "/"), "sha256": sha(path), "audio_sha256": report["audio_sha256"], "timing_metadata_sha256": report["timing_sha256"], "timing_sha_policy": "초기6466/최종62c 메타SHA 차이는 허용하고 실제WAV SHA 일치 우선"})
assert set(reports["small"]) == set(scenes) and len(scenes) == 25
targets = load(OUT / "price_timing_targets.json")["events"]
price_comparison = []
for sid in sorted(s for s in scenes if s.startswith("S")):
    report = reports["small"][sid]
    parsed = amounts(report["recognized"])
    pair = parsed[-2:]
    expected = [t for t in targets if t["scene_id"] == sid]
    expected.sort(key=lambda t: t["sentence_id"])
    ok = len(pair) == 2 and [x["won"] for x in pair] == [int(x["expected_manwon"] * 10000) for x in expected]
    price_comparison.append({"scene_id": sid, "asr_last_two_money": pair, "expected_won": [int(x["expected_manwon"] * 10000) for x in expected], "literal_numeric_equivalent": ok, "interpretation": "ASR 보조 가격값 일치. 실제청취 통과 의미 아님" if ok else "ASR 값차이 후보. medium/실음 집중확인 전 발음결함으로 단정하지 않음"})
resolved = [
    {"scene_id": "O002", "small_ambiguity": "면적 설명 뒤 단독 '입니다' 추가 인식", "medium_observation": "추가 인식은 재현되지 않음. 2026년5~10월/11월3일/83~85㎡는 입력값과 일치", "verdict": "small만의 보조근거 차이로 분리. 실제 중복발화로 단정하지 않음"},
    {"scene_id": "S003", "small_ambiguity": "20위는→22는", "medium_observation": "20위는/7365쌍·699건/7억500·8건/7억450 인식", "verdict": "기존 순위 의심은 medium 보조범위에서 해소"},
    {"scene_id": "S017", "small_ambiguity": "235건→230억원", "medium_observation": "235건/30억3천만원·10건/31억9500만원 인식", "verdict": "기존 지역n 의심은 medium 보조범위에서 해소. 9320일상은9321쌍의 문자 분할 후보"},
]
# 실제로 내용을 읽은 ASR3건만 보조범위 의심 해소로 기록한다.
for row in resolved:
    assert row["scene_id"] in reports["medium"]
candidate_specs = [
    ("S008", "S008-01", "8,016쌍", "816상", "거주수"),
    ("S013", "S013-01", "10위", "12위", "순위"),
    ("S015", "S015-21", "13억5,250만원", "13억5200만 원", "단지가격"),
    ("S019", "S019-21", "12억1,500만원", "12억5500만원", "단지가격"),
]
candidates = []
for scene_id, sentence_id, expected, small, kind in candidate_specs:
    scene = scenes[scene_id]
    sentence = next(x for x in scene["sentences"] if x["sentence_id"] == sentence_id)
    candidates.append({"scene_id": scene_id, "sentence_id": sentence_id, "kind": kind, "expected_display": expected, "expected_reading": sentence["reading_text"], "small_recognition": small, "medium_available": scene_id in reports["medium"], "global_range_s": [sentence["start_s"], sentence["end_s"]], "scene_local_range_s": [sentence["local_start_s"], sentence["local_end_s"]], "audio_file": scene["audio_path"], "audio_sha256": scene["audio_sha256"], "status": "unconfirmed_ASR_difference_not_proven_speech_error"})
write("asr_review.json", {"checked_at": NOW, "status": "supporting_ASR_review_complete_additional_candidates_pending", "small_scenes": 25, "medium_scenes": sorted(reports["medium"]), "WAV_identity_verified": True, "reports": manifest, "price_comparison": price_comparison, "resolved_initial_ambiguities": resolved, "remaining_candidates": candidates, "normalization_examples": ["218500만원=21억8500만원", "1만1750이/1만1450이·1150이건은 일의자리 이(2)가 한글로 분리된 표기 후보", "110일상은111쌍의 '일'이 한글로 분리된 후보. 실제값 차이로 확정하지 않음"], "name_variants": "GDXA·헤링텀·개포레미암프레스트 등 고유명사 ASR 오기와 발음입력은 구분. 오기만으로 실제발음결함 판정 없음", "numeric_reading_evidence": "pronunciation_values.json 183개 수치값 보존 검증", "actual_listening_performed": False, "continuous_playback_performed": False, "new_ASR_executed_by_QA": False, "external_audio_transfer": False})
issue = {"issue_id": "QA-AUDIO-REC-001", "scene_id": [x[0] for x in candidate_specs], "timecode": [{"sentence_id": x["sentence_id"], "global_range_s": x["global_range_s"], "scene_local_range_s": x["scene_local_range_s"]} for x in candidates], "severity": "recommended", "문제": "small ASR의 추가 수치차이 후보4개. 실제발음 오류가 입증된 필수수정으로 취급하지 않습니다.", "evidence": candidates, "수정안": "부모가 캐시된medium으로 S008/S013/S015/S019를 선별 재검증하고, 값차이가 유지될 때만 해당실음 집중확인. 지금은 발화 재생성/원고수정/외부전송 없음", "owner": "director/parent local ASR 담당", "status": "awaiting_optional_medium_or_actual_listening", "checked_revision": {"scene_json_sha256": lock["scene_json_sha256"], "locked_timing_sha256": sha(D / "locked_timing.json"), "audio_sha256": lock["audio_sha256"]}}
write("issue_QA-AUDIO-REC-001.json", issue)
print(json.dumps({"small": 25, "medium": sorted(reports["medium"]), "initial_3_ambiguities": "보조범위 해소", "additional_candidates": [x[0] for x in candidate_specs], "price_ASR_numeric_matches": sum(x["literal_numeric_equivalent"] for x in price_comparison)}, ensure_ascii=False))
