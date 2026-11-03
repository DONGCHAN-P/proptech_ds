"""새 WAV/발음입력/실제경계만 독립검수한다. ASR 실행·외부전송·공유파일 수정 없음."""
import collections
import datetime
import hashlib
import json
import re
import wave
from decimal import Decimal
from pathlib import Path
import numpy as np

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
PROJECT = ROOT.parents[2]
N = ROOT / "narration/top20-explain-v3"
D = ROOT / "director/top20-explain-v3"
SCENE_SHA = "8beec59448e180617327f17913aaa25277b3152769a1815cbdc493351003803e"
MD_SHA = "4259f50a9c5cadbadd864d838559a16f85e07316818ddcb31ce40939fbccac38"
LOCK_SHA = "62c379c0b4d3d73e4ee3f9b17a0ecf6cab18edc2e38151df7b98369a23f206e6"
NOW = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat()
INPUTS = {}


def resolve(value):
    p = Path(value)
    return p if p.is_absolute() else PROJECT / p


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record(path, scope):
    path = Path(path)
    INPUTS[str(path)] = {"path": str(path), "sha256": sha(path), "bytes": path.stat().st_size, "scope": scope}


def load(path, scope="실제 입력내용 검토"):
    record(path, scope)
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normal(text):
    return re.sub(r"[^가-힣A-Za-z0-9]", "", text)


def knum(value):
    value = re.sub(r"[\s원,]", "", value)
    if value == "시월":
        return 10
    ones = {"하나": 1, "한": 1, "둘": 2, "두": 2, "셋": 3, "세": 3, "넷": 4, "네": 4, "다섯": 5, "여섯": 6, "일곱": 7, "여덟": 8, "아홉": 9, "열": 10}
    if value in ones:
        return ones[value]
    for prefix, number in {"열": 10, "스물": 20, "스무": 20, "서른": 30, "마흔": 40, "쉰": 50, "예순": 60, "일흔": 70, "여든": 80, "아흔": 90}.items():
        if value == prefix:
            return number
        if value.startswith(prefix) and value[len(prefix):] in ones:
            return number + ones[value[len(prefix):]]
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
            raise ValueError(repr(value))
    return total + section + digit


def money_digits(value):
    value = re.sub(r"[\s,원]", "", value)
    total = Decimal(0)
    for match in re.finditer(r"([0-9]+(?:\.[0-9]+)?)(억|천만|백만|만)?", value):
        total += Decimal(match[1]) * {None: 1, "억": 100000000, "천만": 10000000, "백만": 1000000, "만": 10000}[match[2]]
    return total


def wav(path):
    with wave.open(str(path), "rb") as stream:
        rate, channels, width, frames = stream.getframerate(), stream.getnchannels(), stream.getsampwidth(), stream.getnframes()
        pcm = stream.readframes(frames)
    assert channels == 1 and width == 2
    return rate, np.frombuffer(pcm, dtype="<i2"), frames


approval = load(D / "script_approval.json")
authorization = load(D / "production_authorization.json")
lock_path = D / "locked_timing.json"
lock = load(lock_path)
parent = load(D / "actual_timing_verification.json", "부모133문장·1496단어 전수coverage 검증을 SHA 연결로 재사용")
handoff = load(N / "handoff.json")
verification = load(N / "verification.json", "제작자 기술검사 범위·제약 참조")
load(N / "integrity_audit.json", "제작자 샘플배치/coverage 자체검수; 독립판정으로 승격하지 않음")
manifest = load(N / "narration_manifest.json")
ledger = load(N / "pronunciation_ledger.json")
load(N / "pronunciation_change_receipt.json")
words_data = load(D / "words_for_editor.json")
words = words_data["words"]
approved = load(ROOT / "writer/top20-explain-v3/scene_proposals_v6.json", "기승인 문장·수치와 새읽기문 대응만; 새대본 품질검수 반복 없음")
load(ROOT / "qa/top20-explain-v3/independent-review/script_review.json", "기존 원고·가격 독립pass 재사용")
checks = {
    "최종lock_SHA": sha(lock_path) == LOCK_SHA == parent["locked_timing_sha256"],
    "승인원고_SHA": approval["scene_json_sha256"] == authorization["scene_json_sha256"] == SCENE_SHA == sha(ROOT / "writer/top20-explain-v3/scene_proposals_v6.json"),
    "승인MD_SHA": approval["script_md_sha256"] == MD_SHA == sha(ROOT / "writer/top20-explain-v3/script_v6.md"),
    "부모coverage근거연결": parent["status"] == "passed" and parent["sentences"] == 133 and parent["words"] == 1496 and parent["editor_words_sha256"] == sha(D / "words_for_editor.json") and parent["source_words_sha256"] == sha(N / "words.json"),
    "유료업로드권한확대없음": authorization["cash_cap_krw"] == 0 and authorization["youtube_upload_authorized"] is False,
}
canonical = {x["sentence_id"]: x for s in approved["scenes"] for x in s["sentences"]}
li = {x["sentence_id"]: x for x in ledger["sentences"]}
wi = collections.defaultdict(list)
for word in words:
    wi[word["sentence_id"]].append(word)
numeric = []
for sentence in ledger["sentences"]:
    sid = sentence["sentence_id"]
    assert sentence["display_text"] == canonical[sid]["display_text"]
    for transform in sentence["transformations"]:
        values = transform["independent_values"]
        if not values:
            continue
        source, spoken = transform["source_text"], transform["spoken_text"]
        if len(values) == 2 and source in {"제2·3판교테크노밸리", "잠실2·3단지"}:
            parsed = [2, 3] if ("제이" in spoken and "제삼" in spoken) or ("이 단지와 삼 단지" in spoken) else []
        else:
            parsed = [knum(spoken)]
        expected = [Decimal(v["source_value"]) for v in values]
        source_values = [Decimal(v) for v in re.findall(r"\d+", source)] if len(values) == 2 else [money_digits(source) if values[0].get("unit") == "KRW" else Decimal(source.replace(",", "").replace("월", ""))]
        numeric.append({"sentence_id": sid, "source": source, "reading": spoken, "source_values": [str(v) for v in source_values], "parsed_reading_values": parsed, "pass": parsed == expected == source_values})
checks["새발음원장183수치값"] = sum(len(x["parsed_reading_values"]) for x in numeric) == 183 and all(x["pass"] for x in numeric)
price_events = []
for scene in approved["scenes"]:
    if not scene.get("region_id"):
        continue
    for tail in ["20", "21"]:
        sid = scene["scene_id"] + "-" + tail
        s = li[sid]
        value = scene["price_panel_data"] if tail == "20" else scene["price_panel_data"]["representative"]
        mt = next(t for t in s["transformations"] if t["reason"] == "whole_money_expression_value_preserved")
        ct = next(t for t in s["transformations"] if re.fullmatch(r"[0-9,]+", t["source_text"]) and t["source_end"] < mt["source_start"] and s["display_text"][t["source_end"]:].startswith("건"))
        price_words = [w for w in wi[sid] if w["display_char_start"] < mt["source_end"] and w["display_char_end"] > mt["source_start"]]
        count_words = [w for w in wi[sid] if w["display_char_start"] < ct["source_end"] and w["display_char_end"] > ct["source_start"]]
        assert price_words and count_words
        price_events.append({"scene_id": scene["scene_id"], "region_id": scene["region_id"], "sentence_id": sid, "role": "지역" if tail == "20" else "단지", "display_price": value["display_price"], "expected_manwon": value["median_manwon"], "reading_won": knum(mt["spoken_text"]), "expected_n": value["n"], "reading_n": knum(ct["spoken_text"]), "sentence_start_s": wi[sid][0]["start_s"], "sentence_end_s": wi[sid][-1]["end_s"], "amount_start_s": min(w["start_s"] for w in price_words), "amount_end_s": max(w["end_s"] for w in price_words), "n_start_s": min(w["start_s"] for w in count_words), "n_end_s": max(w["end_s"] for w in count_words), "timing_basis": "새provider 경계/1.35 + 실측WAV 장면시작; 실제음운동기 오차 미측정", "pass": knum(mt["spoken_text"]) == value["median_manwon"] * 10000 and knum(ct["spoken_text"]) == value["n"]})
checks["가격40건수40_새읽기값"] = len(price_events) == 40 and all(x["pass"] for x in price_events)
write("pronunciation_values.json", {"checked_at": NOW, "numeric_values": 183, "entries": numeric, "actual_pronunciation_listened": False})
write("price_timing_targets.json", {"checked_at": NOW, "locked_timing_sha256": LOCK_SHA, "events": price_events, "note": "실제MP4 수치하이라이트 검수의40개 타깃. 아직 렌더 프레임/발음 통과 근거 아님"})

full_path = resolve(lock["audio_file"])
record(full_path, "새실제WAV SHA·PCM decode·장면/브랜드/무음 경계")
rate, full, frames = wav(full_path)
checks["전체audio_SHA길이"] = sha(full_path) == lock["audio_sha256"] == handoff["audio_sha256"] and abs(frames / rate - lock["total_duration_s"]) < 1 / rate
checks["PCM클리핑없음"] = int(np.max(np.abs(full.astype(np.int32)))) < 32767
audio_rows, intervals, provider_rows = [], [], []
for scene in lock["scenes"]:
    intervals.append({"id": scene["scene_id"], "start_s": scene["start_s"], "end_s": scene["end_s"]})
    if not scene.get("audio_path"):
        continue
    sid = scene["scene_id"]
    path = resolve(scene["audio_path"])
    record(path, "25새WAV SHA·header·신호 및 양끝실제배치 확인")
    sr, pcm, count = wav(path)
    block = round(sr * .01)
    active = np.flatnonzero(np.sqrt(np.mean(pcm[:len(pcm)//block*block].reshape(-1, block).astype(np.float64)**2, axis=1)) >= 32768 * 10**(-45/20))
    start_active, end_active = float(active[0] * .01), float((active[-1] + 1) * .01)
    begin = round(scene["start_s"] * rate)
    edge = min(round(.2 * rate), count)
    native = load(resolve(scene["provider_boundaries_path"]), "provider 원파일 첫·끝 경계 및 장면길이 확인; 전체coverage는 부모receipt 재사용")["boundaries"]
    native = [x for x in native if x["type"] == "WordBoundary"]
    first, last = scene["sentence_times"][0], scene["sentence_times"][-1]
    native_ok = abs(first["local_start_s"] - native[0]["offset"] / 1e7 / 1.35) < 1e-7 and abs(last["local_end_s"] - (native[-1]["offset"] + native[-1]["duration"]) / 1e7 / 1.35) < 1e-7
    duration_ok = sr == rate and abs(count / sr - scene["duration_s"]) < 1 / sr and abs(scene["end_s"] - scene["start_s"] - count / sr) < 1 / sr
    edge_ok = np.array_equal(pcm[:edge], full[begin:begin+edge]) and np.array_equal(pcm[-edge:], full[begin+count-edge:begin+count])
    lexical_ok = all(x["reading_text"] == li[x["sentence_id"]]["reading_text"] for x in scene["sentence_times"])
    row = {"scene_id": sid, "audio_path": str(path), "sha256": sha(path), "duration_s": count / sr, "sample_rate": sr, "channels": 1, "sample_width": 2, "peak_pcm": int(np.max(np.abs(pcm.astype(np.int32)))) , "active_start_local_s": start_active, "active_end_local_s": end_active, "leading_quiet_s": start_active, "trailing_quiet_s": count/sr-end_active, "provider_first_local_s": first["local_start_s"], "provider_last_local_s": last["local_end_s"], "signal_measurement": "10ms RMS -45dBFS 기준. 발음/자연스러움 청취 판정 아님", "checks": {"SHA": sha(path) == scene["audio_sha256"], "실측길이장면대응": duration_ok, "실제양끝PCM배치": edge_ok, "원provider첫끝경계": native_ok, "단어경계_WAV내부": 0 <= first["local_start_s"] < last["local_end_s"] <= count/sr, "새읽기문일치": lexical_ok, "클리핑없음": int(np.max(np.abs(pcm.astype(np.int32)))) < 32767}}
    audio_rows.append(row)
for key in ["brand_intro", "brand_outro"]:
    brand = lock[key]
    path = resolve(brand["audio_path"])
    record(path, "브랜드경계 기존깨끗한WAV 원본과 새합본의 PCM 비교")
    sr, pcm, count = wav(path)
    begin = round(brand["start_s"] * rate)
    checks[key + "_PCM경계"] = sr == rate and np.array_equal(pcm, full[begin:begin+count])
    intervals.append({"id": key, "start_s": brand["start_s"], "end_s": brand["end_s"]})
intervals.sort(key=lambda x: x["start_s"])
gaps = [{"from": a["id"], "to": b["id"], "gap_s": b["start_s"]-a["end_s"]} for a,b in zip(intervals, intervals[1:])]
checks["26장면2브랜드_누락겹침없음"] = len(lock["scenes"]) == 26 and all(abs(x["gap_s"]) < 1/rate for x in gaps) and intervals[0]["start_s"] == 0 and abs(intervals[-1]["end_s"] - frames/rate) < 1/rate
checks["25새음성_실제경계"] = len(audio_rows) == 25 and all(all(x["checks"].values()) for x in audio_rows)
end_scene = next(s for s in lock["scenes"] if s["scene_id"] == "E001")
hold = full[round(end_scene["start_s"]*rate):round(end_scene["end_s"]*rate)]
last_scene = next(s for s in lock["scenes"] if s["scene_id"] == "C001")
last_audio = next(s for s in audio_rows if s["scene_id"] == "C001")
signal_hold = lock["brand_outro"]["start_s"] - last_scene["start_s"] - last_audio["active_end_local_s"]
checks["마지막발화후hold"] = not np.any(hold) and lock["brand_outro"]["start_s"] - lock["last_speech_end_s"] >= 3-1e-6 and signal_hold >= 3
boundary_report = {"checked_at": NOW, "locked_timing_sha256": LOCK_SHA, "audio_sha256": lock["audio_sha256"], "full_wav": {"duration_s": frames/rate, "frames": frames, "sample_rate": rate, "channels": 1, "sample_width": 2}, "scenes": audio_rows, "timeline_boundaries": gaps, "last_provider_word_to_outro_s": lock["brand_outro"]["start_s"] - lock["last_speech_end_s"], "last_RMS_active_to_outro_s": signal_hold, "coverage_limit": "실제PCM decode/샘플경계·신호확인. 실제청취·음운동기·연속재생 검수 아님"}
write("audio_boundary_review.json", boundary_report)
failed = [k for k,v in checks.items() if not v]
write("audio_timing_review.json", {"checked_at": NOW, "status": "technical_and_reading_checks_passed_speech_review_pending" if not failed else "required_correction", "checked_revision": {"scene_json_sha256": SCENE_SHA, "script_md_sha256": MD_SHA, "locked_timing_sha256": LOCK_SHA, "audio_sha256": lock["audio_sha256"], "audio_revision": lock["audio_revision"]}, "checks": checks, "failed_checks": failed, "counts": {"new_wavs": 25, "scenes": 26, "sentences": 133, "provider_words": 1496, "numeric_values": 183, "price_mentions": 40}, "reused": "기승인원고·가격 독립pass 및 부모133문장coverage. 새발음입력 수치·WAV실제경계만 독립 확인", "actual_listening_performed": False, "continuous_playback_performed": False, "phoneme_sync_verification": "unchecked; provider/1.35 환산은 실제음운정렬 검증이 아님", "full_media_pass": False})
write("input_manifest.json", {"checked_at": NOW, "inputs": list(INPUTS.values()), "scope": "새 오디오·타임록·발음원장. 원거래 재수집/재집계·대본 재토론·새ASR 호출 없음"})
print(json.dumps({"status": "audio_timing_audited", "failed_checks": failed, "new_wavs": len(audio_rows), "price_targets": len(price_events), "numeric_value_pass": checks["새발음원장183수치값"], "signal_last_word_hold_s": signal_hold}, ensure_ascii=False))
