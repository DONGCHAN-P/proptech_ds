"""Correct measured audio cut points; preserve v4 layout, captions and duration."""
from pathlib import Path
import importlib.util, hashlib, json, math, wave
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
EP = HERE.parents[1]
BASE = EP / "editor/jun-quality-v2/shorts/build_shorts.py"
spec = importlib.util.spec_from_file_location("preserved_v4_shorts", BASE)
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)
b.HERE = HERE
b.OUT = EP / "outputs/jun-quality-v2/shorts/v5-ending-fix"
b.SPECS = [{**p, "name": p["name"].replace("_v4", "_v5")} for p in b.SPECS]
original_visual = b.visual
quiet = json.loads((HERE / "quiet_candidates.json").read_text(encoding="utf-8"))
cut_lookup = {(r["id"], r["scene_id"]): r["quiet_intervals"][-1][1] - .025 for r in quiet}


def fixed_audio(p):
    rate = 44100
    arr = np.zeros(round(p["duration_s"] * rate), dtype="<i2")
    receipts = []
    for r in p["ranges"]:
        source = Path(r["path"])
        assert b.sha(source) == r["sha256"]
        clean_end = r["source_out_s"] if r["scene_id"] == "S13" else cut_lookup[(p["id"], r["scene_id"])]
        with wave.open(str(source), "rb") as w:
            assert (w.getnchannels(), w.getsampwidth(), w.getframerate()) == (1, 2, rate)
            first = round(r["source_in_s"] * rate)
            w.setpos(first)
            pcm = w.readframes(round(clean_end * rate) - first)
        x = np.frombuffer(pcm, dtype="<i2").copy()
        if r["scene_id"] != "S13":
            tail = x[-round(.02 * rate):].astype(float) / 32768
            db = float(20 * np.log10(max(1e-8, np.sqrt(np.mean(tail*tail)))))
            assert db < -55, (p["id"], r["scene_id"], clean_end, db)
        fade = min(round(.003 * rate), len(x) // 2)
        x[:fade] = (x[:fade] * np.linspace(0, 1, fade)).astype("<i2")
        x[-fade:] = (x[-fade:] * np.linspace(1, 0, fade)).astype("<i2")
        at = round(r["output_start_s"] * rate)
        arr[at:at+len(x)] = x
        r["clean_audio_source_out_s"] = clean_end
        r["suppressed_next_sentence_seconds"] = round(r["source_out_s"] - clean_end, 6)
        receipts.append({"scene": r["scene_id"], "source_in_s": r["source_in_s"], "original_source_out_s": r["source_out_s"], "clean_source_out_s": clean_end,
                         "source_pcm_sha256": hashlib.sha256(pcm).hexdigest(), "silence_padding_to_original_edit_point": True})
    dest = HERE / (p["name"] + "_audio.wav")
    with wave.open(str(dest), "wb") as w:
        w.setparams((1, 2, rate, 0, "NONE", "not compressed"))
        w.writeframes(arr.tobytes())
    b.save(HERE / (p["id"] + "_audio_fix_receipt.json"), {
        "sources": receipts, "speed": 1, "pitch_shift": 0, "new_TTS": False,
        "actual_listening": False, "audio_naturalness_verified": False,
        "correction": "Outgoing cut moved into measured sentence pause; shot/caption clocks preserved with silence padding",
    })
    return dest


def fixed_visual(p, t):
    im = original_visual(p, t)
    tail = p["speech_cut_end_s"]
    if tail <= t < tail + .35:
        previous = original_visual(p, tail - 1 / b.FPS)
        im = Image.blend(previous, im, b.ease((t-tail)/.35))
    return im


b.audio = fixed_audio
b.visual = fixed_visual
b.OUT.mkdir(parents=True, exist_ok=True)
b.setup_fonts()
plans = b.make_plan()
for p in plans:
    b.render(p)
    original = EP / "outputs/jun-quality-v2/shorts" / (p["name"].replace("_v5", "_v4") + ".srt")
    assert b.sha(original) == b.sha(b.OUT / (p["name"] + ".srt")), "Caption text/timing changed"
b.save(HERE / "edit_plan.json", {"revision": "portrait-shorts-v5-ending-fix", "shorts": plans, "fps": b.FPS, "tail_transition_s": .35, "tail_hold_s": 3})
b.save(HERE / "layout_bounds.json", {"elements": list(b.BOUNDS.values())})
b.save(HERE / "input_versions.json", {
    "base_build": str(BASE), "base_build_sha256": b.sha(BASE),
    "wrapper_sha256": b.sha(Path(__file__)),
    "prior_revision": "portrait-shorts-v4-wood-house", "new_paid_calls": 0,
})
print(json.dumps({"status": "rendered_v5", "outputs": [{"id": p["id"], "path": str(b.OUT / (p["name"] + ".mp4")), "sha256": b.sha(b.OUT / (p["name"] + ".mp4"))} for p in plans]}), flush=True)
