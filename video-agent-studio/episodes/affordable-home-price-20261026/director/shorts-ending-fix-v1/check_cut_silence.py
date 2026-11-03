"""Regression check: noncontiguous edits must end in measured silence."""
from pathlib import Path
import argparse, json, subprocess, wave
import numpy as np

HERE = Path(__file__).resolve().parent
EP = HERE.parents[1]
ROOT = EP.parents[2]
FF = ROOT / "video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe"
parser = argparse.ArgumentParser()
parser.add_argument("--revision", choices=["v4", "v5"], required=True)
args = parser.parse_args()
plan = json.loads((EP / "editor/jun-quality-v2/shorts/edit_plan.json").read_text(encoding="utf-8-sig"))
rows = []
for p in plan["shorts"]:
    stem = p["name"] if args.revision == "v4" else p["name"].replace("_v4", "_v5")
    out = EP / "outputs/jun-quality-v2/shorts"
    if args.revision == "v5": out = out / "v5-ending-fix"
    video = out / (stem + ".mp4")
    wav = HERE / (stem + "_regression.wav")
    subprocess.run([str(FF), "-v", "error", "-y", "-i", str(video), "-vn", "-ac", "1", "-ar", "44100", "-c:a", "pcm_s16le", str(wav)], check=True)
    with wave.open(str(wav), "rb") as w:
        rate = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(float) / 32768
    for r in p["ranges"]:
        if r["scene_id"] == "S13": continue  # contiguous same-source audio
        end = r["output_start_s"] + r["source_out_s"] - r["source_in_s"]
        z = x[round((end - .045) * rate):round((end - .008) * rate)]
        db = float(20 * np.log10(max(1e-8, np.sqrt(np.mean(z*z)))))
        rows.append({"short": p["id"], "scene": r["scene_id"], "cut_s": end, "rms_dbfs": round(db, 2), "passed": db < -60})
(HERE / (args.revision + "_cut_silence_check.json")).write_text(json.dumps(rows, indent=2), encoding="utf-8")
print(json.dumps(rows), flush=True)
assert all(r["passed"] for r in rows), "Speech energy remains at one or more outgoing edit points"
