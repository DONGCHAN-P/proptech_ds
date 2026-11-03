from pathlib import Path
import hashlib, json, math, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
EP = HERE.parents[1]
ROOT = EP.parents[2]
FF = ROOT / "video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe"
PROBE = ROOT / "video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe"
plan = json.loads((HERE / "edit_plan.json").read_text(encoding="utf-8"))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
cfg = json.loads((ROOT / "config/vertical_video_safe_area.json").read_text(encoding="utf-8-sig"))
rect = cfg["profiles"]["youtube_portrait_full_frame_v2"]["critical_rect"]
bounds = json.loads((HERE / "layout_bounds.json").read_text(encoding="utf-8"))["elements"]
overflows = [x for x in bounds if x["bbox"][0] < rect["left"] or x["bbox"][1] < rect["top"] or x["bbox"][2] > rect["right"] or x["bbox"][3] > rect["bottom"]]
assert not overflows, overflows
rows = []
for p in plan["shorts"]:
    video = EP / "outputs/jun-quality-v2/shorts/v5-ending-fix" / (p["name"] + ".mp4")
    probe = json.loads(subprocess.check_output([str(PROBE), "-v", "error", "-show_streams", "-show_format", "-of", "json", str(video)]))
    v = next(x for x in probe["streams"] if x["codec_type"] == "video")
    assert (v["width"], v["height"], v["r_frame_rate"], int(v["nb_frames"])) == (1080, 1920, "30/1", p["frames"])
    assert abs(float(probe["format"]["duration"]) - p["duration_s"]) < .01
    decoded = subprocess.run([str(FF), "-v", "error", "-xerror", "-i", str(video), "-map", "0:v:0", "-map", "0:a:0", "-f", "null", "-"], capture_output=True)
    (HERE / (p["id"] + "_v5_decode.log")).write_bytes(decoded.stdout + decoded.stderr)
    assert decoded.returncode == 0
    old_srt = EP / "outputs/jun-quality-v2/shorts" / (p["name"].replace("_v5", "_v4") + ".srt")
    assert sha(old_srt) == sha(video.with_suffix(".srt"))
    wav = HERE / (p["name"] + "_regression.wav")
    with wave.open(str(wav), "rb") as w:
        rate = w.getframerate()
        pcm = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2")
    assert int(np.max(np.abs(pcm[round((p["speech_cut_end_s"] + .05)*rate):].astype(float)))) == 0
    times = [p["speech_cut_end_s"] - 1/30 + i/30 for i in range(14)]
    times += [p["duration_s"] - 1, p["duration_s"] - 1/30]
    for r in p["ranges"][1:]: times += [r["output_start_s"] - 1/30, r["output_start_s"], r["output_start_s"] + 1/30]
    frames = []
    tiles = []
    for i, t in enumerate(times):
        dest = HERE / f"{p['id']}_v5_{i:02}_{t:06.3f}.jpg"
        subprocess.run([str(FF), "-v", "error", "-y", "-ss", str(t), "-i", str(video), "-frames:v", "1", "-q:v", "2", str(dest)], check=True)
        im = Image.open(dest).convert("RGB")
        assert np.asarray(im).mean() > 10
        tile = Image.new("RGB", (180, 344), "white")
        tile.paste(im.resize((180, 320)), (0, 24))
        ImageDraw.Draw(tile).text((5, 6), f"{t:.3f}s", fill="black")
        tiles.append(tile)
        frames.append({"time_s": t, "path": str(dest.relative_to(ROOT))})
    sheet = Image.new("RGB", (180*7, 344*math.ceil(len(tiles)/7)), "#dddddd")
    for i, tile in enumerate(tiles): sheet.paste(tile, (180*(i%7), 344*(i//7)))
    sheet.save(HERE / (p["id"] + "_v5_encoded_contact.jpg"))
    rows.append({"id": p["id"], "video": str(video.relative_to(ROOT)), "sha256": sha(video), "duration_s": float(probe["format"]["duration"]), "frames": int(v["nb_frames"]), "full_decode": True,
                 "captions_unchanged": True, "silent_tail_verified": True, "tail_transition_s": .35, "actual_listening": False, "continuous_playback": False, "frames_sampled": frames})
report = {"revision": "v5-ending-fix", "items": rows, "glyph_bounds_count": len(bounds), "glyph_overflows": 0, "new_paid_calls": 0, "uploaded": False}
(HERE / "v5_technical_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"full_decode": True, "captions_unchanged": True, "glyph_overflows": 0, "sampled_frames": sum(len(r["frames_sampled"]) for r in rows)}))
