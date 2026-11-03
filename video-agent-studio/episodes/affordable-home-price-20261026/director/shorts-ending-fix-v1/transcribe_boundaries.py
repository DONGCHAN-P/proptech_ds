"""Offline ASR of the encoded endings and original cut neighborhoods."""
from pathlib import Path
import os, sys, socket, json, subprocess, time

HERE = Path(__file__).resolve().parent
EP = HERE.parents[1]
ROOT = EP.parents[2]
SOURCE = ROOT / "video-agent-studio/episodes/housing-choice-networth-20261020/qa/private-production-v1/asr"
sys.path[:0] = [str(SOURCE / "deps"), str(SOURCE)]
os.environ.update(HF_HUB_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1", DO_NOT_TRACK="1", TOKENIZERS_PARALLELISM="false", HF_HOME=str(HERE / "cache"))

def refuse(*args, **kwargs):
    raise RuntimeError("Offline ASR: no network")

socket.socket.connect = refuse
socket.socket.connect_ex = refuse
socket.create_connection = refuse
import onnxruntime
onnxruntime.disable_telemetry_events()
from faster_whisper import WhisperModel

FF = ROOT / "video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe"
plan = json.loads((EP / "editor/jun-quality-v2/shorts/edit_plan.json").read_text(encoding="utf-8-sig"))
model = WhisperModel(str(SOURCE / "models/medium"), device="cpu", compute_type="int8", cpu_threads=4, num_workers=1, local_files_only=True)
items = []
for p in plan["shorts"]:
    items.append((p["id"] + "_encoded_end", EP / "outputs/jun-quality-v2/shorts" / (p["name"] + ".mp4"), max(0, p["speech_cut_end_s"] - 9), 11))
    for r in p["ranges"]:
        items.append((p["id"] + "_source_" + r["scene_id"], Path(r["path"]), max(0, r["source_out_s"] - 2.5), 4.5))
rows = []
for name, source, start, duration in items:
    wav = HERE / (name + ".wav")
    subprocess.run([str(FF), "-v", "error", "-y", "-ss", str(start), "-t", str(duration), "-i", str(source), "-vn", "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", str(wav)], check=True)
    began = time.monotonic()
    segments, info = model.transcribe(str(wav), language="ko", beam_size=5, temperature=0, word_timestamps=True, vad_filter=False, condition_on_previous_text=False, initial_prompt=None)
    ss = list(segments)
    row = {"id": name, "source": str(source), "offset_s": start, "transcript": " ".join(s.text.strip() for s in ss), "elapsed_s": time.monotonic() - began,
           "words": [{"start_s": start + w.start, "end_s": start + w.end, "word": w.word, "probability": w.probability} for s in ss for w in (s.words or [])],
           "actual_listening": False, "external_upload": False}
    rows.append(row)
    (HERE / "asr_boundaries.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: row[k] for k in ["id", "transcript", "elapsed_s"]}, ensure_ascii=False), flush=True)
