"""기존검사결과·추가medium4건·v2 정적표본 검토범위를 묶어 인수인계한다."""
import datetime
import hashlib
import json
import re
from pathlib import Path
from PIL import Image

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
D = ROOT / "director/top20-explain-v3"
EDITOR = ROOT / "editor/top20-explain-v3"
NOW = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat()


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def mix_number(text):
    tokens = re.findall(r"\d+|억|만|천|백|십", text.replace(",", ""))
    total = section = number = 0
    for token in tokens:
        if token.isdigit():
            number = int(token)
        elif token in {"천", "백", "십"}:
            section += (number or 1) * {"천":1000,"백":100,"십":10}[token]
            number = 0
        else:
            total += (section + number or 1) * {"억":100000000,"만":10000}[token]
            section = number = 0
    return total + section + number


audio = load(OUT / "audio_timing_review.json")
source = load(OUT / "main_v2_source_review.json")
asr = load(OUT / "asr_review.json")
lock = load(D / "locked_timing.json")
si = {s["scene_id"]:s for s in lock["scenes"]}
medium = {}
for path in (D / "evidence/audio-asr/medium").glob("*.json"):
    report = load(path)
    if "scene_id" in report:
        assert report["audio_sha256"] == si[report["scene_id"]]["audio_sha256"]
        medium[report["scene_id"]] = (path,report)
remaining = []
delta = []
for row in asr["remaining_candidates"]:
    sid = row["scene_id"]
    if sid not in medium:
        remaining.append(row)
        continue
    path,report = medium[sid]
    text = re.sub(r"\s|,", "", report["recognized"])
    if sid == "S008":
        ok = bool(re.search(r"8016(?:쌍|상)",text))
        observation = "medium:8016상 → 원고8,016쌍과 수치 일치. 쌍/상의 ASR표기 차이"
    elif sid == "S013":
        ok = text.startswith("10위는")
        observation = "medium:10위는 → 원고10위와 일치"
    else:
        amounts = [mix_number(x[0]) for x in re.finditer(r"[0-9,억만천백십\s]+원",report["recognized"])]
        expected = 1352500000 if sid == "S015" else 1215000000
        ok = bool(amounts) and amounts[-1] == expected
        observation = "medium 단지가격 정규화=" + (str(amounts[-1]) if amounts else "해석미완료") + "원, 기대=" + str(expected) + "원"
    result = {**row, "medium_available": True, "medium_report": str(path.relative_to(ROOT)).replace("\\", "/"), "medium_report_sha256": sha(path), "medium_observation": observation, "status": "resolved_ASR_support_value_matches" if ok else "unresolved_ASR_ambiguity_actual_listening_unchecked", "actual_speech_error_confirmed": False}
    delta.append(result)
    if not ok:
        remaining.append(result)
asr["checked_at"] = NOW
asr["medium_scenes"] = sorted(medium)
asr["additional_medium_results"] = delta
asr["remaining_candidates"] = remaining
asr["status"] = "ASR_support_review_complete_no_confirmed_speech_defect" if not remaining else "ASR_support_review_pending_remaining_ambiguity"
asr["summary_subset_policy"] = "medium/summary.json은 마지막subset만일 수 있어 개별JSON과 WAV SHA로7건 확인"
write("asr_review.json", asr)
issue = load(OUT / "issue_QA-AUDIO-REC-001.json")
issue["status"] = "closed_medium_support_candidates_resolved" if not remaining else "awaiting_remaining_ASR_or_actual_listening"
issue["medium_results"] = delta
issue["closure_scope"] = "추가ASR 수치차이 후보 제안을 닫음. 실제청취·발음자연스러움 통과 판정 아님"
write("issue_QA-AUDIO-REC-001.json", issue)

png_dir = EDITOR / "production/quality-v2/png"
pngs = sorted(png_dir.glob("frame-*.png"))
sheet_paths = sorted(png_dir.glob("contact-sheet-*.jpg"))
visual_inputs = []
for path in pngs:
    with Image.open(path) as im:
        im.load()
        dimensions = list(im.size)
    t = float(re.search(r"at-([0-9.]+)s",path.name)[1])
    visual_inputs.append({"path": str(path.relative_to(ROOT)).replace("\\", "/"), "sha256": sha(path), "size": dimensions, "time_s":t, "inspection":"6개 contact sheet의 축소표본으로 실제 확인"})
assert len(pngs) == 48 and len(sheet_paths) == 6
write("main_v2_static_visual_review.json", {"status":"sampled_static_review_complete_interim_v2", "checked_at":NOW, "project":str(EDITOR / "main/v2"), "inputs":visual_inputs, "contact_sheets":[{"path":str(p.relative_to(ROOT)).replace("\\", "/"),"sha256":sha(p)} for p in sheet_paths], "coverage":"26장면 및 지역별 특징/가격 등을 담은 정적PNG48개를 contact sheet6장으로 확인. S005 긴단지명 가격화면·S017 특징화면은 원본PNG도 직접 열람", "full_resolution_directly_viewed":["frame-08-at-145.013s.png","frame-33-at-530.537s.png"], "observations":["지역·단지 거래건수 분리와 지역/사진 명칭·자료시점 표시 유지", "가격원발화 전 금액이 비어 있는 표본은 source actualword reveal와 대응하므로 누락 결함으로 취급하지 않음", "표본에서 뚜렷한 자막·긴단지명 잘림이나 검은화면 확인되지 않음. 실제MP4/전체경계/최대줌 검수는 별도"], "actual_MP4_frames":False, "continuous_playback_performed":False, "confirmed_required_findings":[]})

technical_ok = not audio["failed_checks"] and not source["failed_checks"]
write("findings.json", {"checked_at":NOW, "checked_revision":audio["checked_revision"], "scope":"새음성/타이밍·ASR 보조·interim v2 소스/정적표본. 최종v2-bgm MP4 제외", "findings":[issue], "open_counts":{"critical":0,"required":0,"recommended":1 if remaining else 0}, "confirmed_audio_required_open_count":0, "unverified_scope":["실제청취·음운동기", "최종BGM 믹스", "실제MP4 decode/전장면·경계·40가격reveal"]})
write("coverage.json", {"new_WAVs":"25개 SHA/header/decode/양끝실제PCM 배치 확인", "numeric_reading":"183개 수치값·40가격/40거래건수 새발음입력 일치", "provider_word_coverage":"부모133문장/1496단어 전수coverage receipt SHA 연결 재사용", "ASR":"로컬small25·medium개별"+str(len(medium))+"건 확인. QA 새모델실행/다운로드/전송 없음", "main_v2_source":"26scene/206cue/40금액원단어reveal/20phase/20사진 및브랜드mute 연결 검사", "main_v2_static":"48PNG contact sheet6장 및원본2장 확인; 실제MP4 아님", "actual_listening_performed":False, "continuous_playback_performed":False, "actual_MP4_review":"unchecked; 부모 최종v2-bgm MP4 전달 대기", "BGM_final_mix":"unchecked", "phoneme_sync":"unchecked; provider/1.35 환산과 실제음운 검증 구분"})
write("handoff.json", {"task_id":"top20-explain-v3-production-QA", "role":"qa", "status":"pre_render_checks_complete_waiting_final_MP4" if technical_ok and not remaining else "pre_render_partial_remaining_review", "checked_revision":audio["checked_revision"], "project_reviewed":"editor/top20-explain-v3/main/v2 (interim)", "final_media_project":"v2-bgm 예정; 부모 최종입력으로 확정 필요", "outputs":["audio_timing_review.json","audio_boundary_review.json","pronunciation_values.json","price_timing_targets.json","asr_review.json","findings.json","main_v2_source_review.json","main_v2_static_visual_review.json","mp4_review_plan.json","input_manifest.json","coverage.json"], "validation":"새WAV25·736.949705초·183수치·40가격/n·실제PCM경계 검사 통과. v2 26장면/206cue/40reveal source 및정적48표본 확인. 실제청취/MP4 통과 아님", "confirmed_audio_required_open_count":0, "ASR_candidates_open":len(remaining), "ASR_medium_scenes":sorted(medium), "unresolved":"최종v2-bgm 실제MP4 decode·26장면/경계·40금액reveal·BGM믹스 검수 대기. 실제청취·연속재생 미실시", "next_owner":"director: 최종active project/MP4/렌더receipt SHA 전달 → qa:257표본계획과40원단어reveal 검수", "actual_listening_performed":False, "continuous_playback_performed":False, "external_transfer_or_upload_performed":False, "paid_calls":0, "full_media_pass":False})

for name in ["asr_review.json","findings.json","coverage.json","handoff.json","main_v2_static_visual_review.json"]:
    text=(OUT/name).read_text(encoding="utf-8")
    json.loads(text)
    assert not re.search(r"\?{2,}",text),name
print(json.dumps({"technical_ok":technical_ok,"medium_scenes":sorted(medium),"remaining_ASR_candidates":len(remaining),"confirmed_audio_required_open_count":0,"static_PNGs":48,"status":"최종MP4대기"},ensure_ascii=False))
