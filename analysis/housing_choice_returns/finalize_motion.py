"""Verify the rendered insert, then record its source and user-facing paths."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parents[2]
EP = ROOT / "video-agent-studio/episodes/housing-choice-networth-20261020"
OUT = EP / "outputs/returns-motion-v1"
VIDEO = OUT / "returns_motion_v1.mp4"
FFDIR = ROOT / "video/node_modules/@remotion/compositor-win32-x64-msvc"


def read(path):
    return json.loads(path.read_text(encoding="utf8"))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf8")


def relative(path):
    return path.relative_to(ROOT).as_posix()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


probe = subprocess.run(
    [str(FFDIR / "ffprobe.exe"), "-v", "error", "-count_frames", "-show_streams",
     "-show_format", "-of", "json", str(VIDEO)],
    check=True, capture_output=True, text=True,
)
assert not probe.stderr.strip(), probe.stderr
media = json.loads(probe.stdout)
assert len(media["streams"]) == 1, "Expected a silent video with one stream"
stream = media["streams"][0]
assert (stream["width"], stream["height"], stream["r_frame_rate"]) == (1920, 1080, "30/1")
assert int(stream["nb_read_frames"]) == 1620
assert float(media["format"]["duration"]) == 54.0

source = ROOT / "analysis/housing_choice_returns/comparison.json"
checks = read(OUT / "data_checks.json")
assert checks["source_sha256"] == digest(source) == digest(OUT / "data.json")
assert len(checks["summary_checks"]) == 6
assert all(row["matches_source"] for row in checks["summary_checks"])
captions = (OUT / "returns_motion_v1.srt").read_text(encoding="utf8")
assert captions.count(" --> ") == 12
assert "00:00:54,000" in captions

qa = OUT / "qa/final"
qa.mkdir(parents=True, exist_ok=True)
times = [3, 6, 15, 17.9667, 18.0333, 33, 35.9667, 36.0333, 42, 51]
for time in times:
    subprocess.run(
        [str(FFDIR / "ffmpeg.exe"), "-v", "error", "-y", "-ss", str(time), "-i", str(VIDEO),
         "-frames:v", "1", "-c:v", "png", str(qa / f"render-{time}s.png")],
        check=True, capture_output=True,
    )
write(qa / "probe.json", media)
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
write(qa / "qa.json", {
    "checked_at": now, "output": relative(VIDEO), "sha256": digest(VIDEO),
    "duration_seconds": 54, "size_bytes": VIDEO.stat().st_size,
    "resolution": [1920, 1080], "fps": 30, "decoded_frame_count": 1620,
    "decode_errors": 0, "audio_streams": 0, "source_checks": checks,
    "sample_times": times,
    "visual_review": "Final extracted frames pending inspection by agent",
    "continuous_playback": False, "listening": False,
    "limitations": ["Silent explanatory captions; no narration or music",
                    "Housing annual-average matched transactions versus S&P year-end price levels",
                    "S&P price index in USD, dividends and FX excluded; historical comparison"],
})

cfg_path = ROOT / "config/video_shelf.json"
cfg = read(cfg_path)
entry = next(row for row in cfg["entries"] if row["name"] == "housing-choice")
entry["files"]["수익률비교.mp4"] = relative(VIDEO)
entry["files"]["수익률비교.srt"] = relative(OUT / "returns_motion_v1.srt")
entry["status"] = "3·5·10년 꺾은선 비교 모션그래픽 v1 · 54초 · 설명 자막 포함 무음본 / 기존 본편 검토본 보존"
write(cfg_path, cfg)
subprocess.run([str(ROOT / "tools/python311/python.exe"), "-X", "utf8",
                str(ROOT / "tools/refresh_video_shelf.py")], check=True, cwd=ROOT)
assert os.path.samefile(ROOT / "영상/housing-choice/수익률비교.mp4", VIDEO)

state_path = EP / "state.json"
state = read(state_path)
state.setdefault("motion_graphics", {})["returns_comparison"] = {
    "status": "rendered_silent_review", "version": "v1", "updated_at": now,
    "output": relative(VIDEO), "captions": relative(OUT / "returns_motion_v1.srt"),
    "qa": relative(qa / "qa.json"), "duration_seconds": 54, "windows_years": [3, 5, 10],
    "voice": "not generated", "integrated_into_full_episode": False,
}
state["updated_at"] = now
write(state_path, state)
decisions_path = EP / "decisions.json"
decisions = read(decisions_path)
decision_id = "returns-line-motion-v1-20261022"
if not any(row["id"] == decision_id for row in decisions["decisions"]):
    decisions["decisions"].append({
        "id": decision_id, "gate": "script", "episode": state["episode_id"],
        "status": "directly_requested_local_motion_insert_rendered",
        "approval_basis": "User requested a motion-graphics video explaining 3/5/10 years using line charts, instead of an HTML deliverable. Prior direction: local housing data since 2006; US S&P index instead of domestic ETF. Scope = standalone silent insert; no paid narration or upload.",
        "output": relative(VIDEO), "sha256": digest(VIDEO), "created_at": now,
    })
    write(decisions_path, decisions)
print(json.dumps({"video": str(VIDEO), "decoded_frames": 1620, "source_checks": 6,
                  "captions": 12, "shelf_link_verified": True}, ensure_ascii=False))
