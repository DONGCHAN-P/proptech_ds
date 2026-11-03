"""실측 본편v2의 연결·가격phase·자막을 검사한다. 최종MP4 판정은 별도다."""
import collections
import datetime
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
EDITOR = ROOT / "editor/top20-explain-v3"
SOURCE = EDITOR / "main/v2"
NOW = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat()


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def norm(text):
    return re.sub(r"[^가-힣a-zA-Z0-9]", "", text)


class Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


pointer = load(EDITOR / "production/active_project.json")
lock_path = ROOT / "director/top20-explain-v3/locked_timing.json"
lock = load(lock_path)
scenes = {s["scene_id"]: s for s in lock["scenes"]}
approved = load(ROOT / "writer/top20-explain-v3/scene_proposals_v6.json")
canonical = {x["sentence_id"]: x for s in approved["scenes"] for x in s["sentences"]}
ledger = load(ROOT / "narration/top20-explain-v3/pronunciation_ledger.json")
ledger_index = {x["sentence_id"]: x for x in ledger["sentences"]}
targets = load(OUT / "price_timing_targets.json")["events"]
phase = load(SOURCE / "phase_audit.json")
anchors = load(SOURCE / "anchor_audit.json")
caption = load(SOURCE / "caption_mapping.json")
placements = load(SOURCE / "placement.json")
price_audit = load(SOURCE / "price_audit.json")
photo_audit = load(SOURCE / "photo_audit.json")
frozen = load(SOURCE / "source_freeze.json")
inputs = load(SOURCE / "input_freeze.json")
parser = Tags()
parser.feed((SOURCE / "index.html").read_text(encoding="utf-8-sig"))
clips = {attrs["id"]: attrs for tag,attrs in parser.tags if attrs.get("id") in scenes}
videos = [attrs for tag,attrs in parser.tags if tag == "video"]
audio = [attrs for tag,attrs in parser.tags if tag == "audio" and attrs.get("id") == "main-narration"]
checks = {
    "최종승인v6연결": inputs["source_script_sha256"] == lock["scene_json_sha256"] and inputs["source_markdown_sha256"] == lock["script_md_sha256"] and inputs["approval_decision_id"] == "e9baa3107ede",
    "26장면실측배치": set(clips) == set(scenes) and len(placements) == 26 and all(abs(float(clips[sid]["data-start"]) - s["start_s"]) < 1e-6 and abs(float(clips[sid]["data-duration"]) - s["end_s"] + s["start_s"]) < 1e-6 for sid,s in scenes.items()),
    "전체WAV단일연결": len(audio) == 1 and sha(SOURCE / audio[0]["src"]) == lock["audio_sha256"],
    "브랜드중복오디오차단": len(videos) == 2 and all("muted" in v for v in videos),
    "source_freeze현재일치": all(sha(SOURCE / f["path"]) == f["sha256"] for f in frozen["files"]),
    "자산47개freeze일치": len(inputs["staged_assets"]) == 47 and all(sha(Path(x["path"])) == x["sha256"] for x in inputs["staged_assets"]),
    "20사진실제binding": len(photo_audit) == 20 and all(x["final_binding"] for x in photo_audit),
    "가격phase20개": len(phase) == 20 and all(x["timing_locked"] and abs(x["switch_s"] - (next(t["sentence_start_s"] for t in targets if t["scene_id"] == x["scene_id"] and t["role"] == "지역") - scenes[x["scene_id"]]["start_s"])) < 1e-5 and x["switch_s"] >= x["feature_last_word_end_s"] for x in phase),
}
anchor_checks = []
for target in targets:
    key = "region_median" if target["role"] == "지역" else "complex_median"
    matches = [a for a in anchors if a["scene_id"] == target["scene_id"] and a["key"] == key]
    expected = target["amount_start_s"] - scenes[target["scene_id"]]["start_s"]
    ok = len(matches) == 1 and abs(matches[0]["local_s"] - expected) < 1e-5
    anchor_checks.append({"scene_id": target["scene_id"], "sentence_id": target["sentence_id"], "key": key, "expected_global_s": target["amount_start_s"], "expected_local_s": expected, "actual_local_s": matches[0]["local_s"] if len(matches)==1 else None, "pass": ok})
checks["40금액actualword_reveal앵커"] = len(anchor_checks) == 40 and all(x["pass"] for x in anchor_checks)
caption_groups = collections.defaultdict(list)
for cue in caption["cues"]:
    caption_groups[cue["sentence_id"]].append(cue)
checks["206cue_133문장보존"] = len(caption["cues"]) == 206 and set(caption_groups) == set(canonical) and all(norm("".join(c["text"] for c in group)) == norm(canonical[sid]["display_text"]) for sid,group in caption_groups.items())
checks["자막브랜드무발화hold비노출"] = caption["brand_intersections"] == 0 and caption["E001_captions"] == 0 and abs(caption["caption_background_windows"][-1][1] - lock["last_speech_end_s"]) < 1e-6
checks["cue범위겹침없음"] = all(0 <= c["start_s"] < c["end_s"] <= lock["total_duration_s"] for c in caption["cues"]) and all(a["end_s"] <= b["start_s"] + 1e-7 for a,b in zip(caption["cues"],caption["cues"][1:]))
protected = []
for sid, group in caption_groups.items():
    source = canonical[sid]["display_text"]
    spans = []
    for t in ledger_index[sid]["transformations"]:
        if t["reason"] == "whole_money_expression_value_preserved":
            spans.append((t["source_start"], t["source_end"], "금액"))
    if sid.endswith("-21"):
        scene = next((s for s in approved["scenes"] if s["scene_id"] == sid.split("-")[0] and s.get("region_id")), None)
        if scene:
            name = scene["price_panel_data"]["representative"]["apt_name"]
            pos = source.find(name)
            if pos >= 0:
                spans.append((pos, pos+len(name), "단지명"))
    for start,end,kind in spans:
        ns,ne = len(norm(source[:start])),len(norm(source[:end]))
        cuts = [c["display_normalized_range"][1] for c in group[:-1] if ns < c["display_normalized_range"][1] < ne]
        protected.append({"sentence_id": sid, "kind": kind, "text": source[start:end], "split_inside": cuts, "pass": not cuts})
checks["금액단지명_보호구간자막분할"] = all(x["pass"] for x in protected)
quality_path = EDITOR / "production/quality-v2/quality_receipt.json"
quality = load(quality_path)
checks["editor자동quality_v2근거"] = quality["status"] == "passed" and quality["layout"]["totalIssueCount"] == 0
failed = [k for k,v in checks.items() if not v]
files = [SOURCE / n for n in ["index.html", "build_receipt.json", "input_freeze.json", "source_freeze.json", "anchor_audit.json", "phase_audit.json", "caption_mapping.json", "photo_audit.json", "price_audit.json"]]
write("main_v2_source_review.json", {"checked_at": NOW, "status": "source_checks_passed_interim_v2" if not failed else "source_required_correction", "project": str(SOURCE), "active_pointer_observed": pointer, "final_media_project": "미확정; 부모 v2-bgm 복제·BGM 적용 후 실제MP4 별도검수", "checks": checks, "failed_checks": failed, "price_anchor_checks": anchor_checks, "protected_caption_spans": protected, "inputs": [{"path": str(p), "sha256": sha(p)} for p in files], "editor_quality_receipt": {"path": str(quality_path), "sha256": sha(quality_path), "browser_samples": quality["sample_count"], "inspection": "producer 자동검사 근거 읽음. 해당브라우저71프레임을 QA가 모두 봤다는 뜻 아님"}, "actual_listening_performed": False, "continuous_playback_performed": False, "actual_MP4_inspected": False})
samples = []
def sample(time_s, purpose, scene_id=None):
    samples.append({"time_s": max(0, min(float(time_s), lock["total_duration_s"]-1/30)), "purpose": purpose, "scene_id": scene_id})
for sid,scene in scenes.items():
    sample((scene["start_s"]+scene["end_s"])/2, "모든26장면 대표·고정scale 상태", sid)
    sample(scene["start_s"]-1/30, "컷 직전", sid)
    sample(scene["start_s"]+1/30, "컷 직후", sid)
for p in phase:
    t = scenes[p["scene_id"]]["start_s"] + p["switch_s"]
    sample(t-1/30, "특징사진→가격 phase 직전", p["scene_id"])
    sample(t+1/30, "특징사진→가격 phase 직후", p["scene_id"])
for event in targets:
    for offset,purpose in [(-1/30,"금액 원발화 reveal 직전"),(1/30,"금액 원발화 reveal 직후"),(.23,"금액 강조 표시 완료")]:
        sample(event["amount_start_s"]+offset, purpose, event["scene_id"])
for name in ["brand_intro", "brand_outro"]:
    for t in [lock[name]["start_s"],lock[name]["end_s"]]:
        sample(t-1/30,"브랜드 경계 직전",name)
        sample(t+1/30,"브랜드 경계 직후",name)
for sid,group in caption_groups.items():
    if sid in {max(caption_groups, key=lambda k:len(canonical[k]["display_text"])), "S005-21", "S017-21", "O002-02", "C001-05"}:
        for cue in group:
            sample((cue["start_s"]+cue["end_s"])/2,"긴자막·긴단지명·최종CTA",sid.split("-")[0])
write("mp4_review_plan.json", {"status": "awaiting_final_v2_bgm_MP4", "locked_timing_sha256": sha(lock_path), "reference_project": str(SOURCE), "samples": samples, "requirements": ["실제MP4 decode/stream/길이 검사", "26장면·컷/브랜드·가격phase·긴자막 샘플프레임 직접확인", "40금액 reveal를 실제원단어 시간과 대조", "최종BGM 포함 오디오 스트림 및 base narration 연결 확인", "최대줌/모션 상태가 추가되면 해당상태 추가 확인", "샘플프레임·연속재생·실제청취를 구분"], "prohibited_claim": "소스/자동검사만으로 최종미디어·청취·연속재생 통과 선언 금지"})
print(json.dumps({"status": "main_v2_source_checked", "failed_checks": failed, "money_anchors": len(anchor_checks), "caption_protection_failures": [x for x in protected if not x["pass"]], "planned_MP4_samples": len(samples)}, ensure_ascii=False))
