"""Transcribe the corrected, encoded files locally; no human-listening claim."""
from pathlib import Path
import os, sys, json, socket, subprocess
HERE = Path(__file__).resolve().parent
EP = HERE.parents[1]
ROOT = EP.parents[2]
SOURCE = ROOT / "video-agent-studio/episodes/housing-choice-networth-20261020/qa/private-production-v1/asr"
sys.path[:0] = [str(SOURCE / "deps"), str(SOURCE)]
os.environ.update(HF_HUB_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1", DO_NOT_TRACK="1", TOKENIZERS_PARALLELISM="false", HF_HOME=str(HERE / "cache"))
def refuse(*args, **kwargs): raise RuntimeError("Offline only")
socket.socket.connect = refuse
socket.socket.connect_ex = refuse
socket.create_connection = refuse
import onnxruntime
onnxruntime.disable_telemetry_events()
from faster_whisper import WhisperModel
model = WhisperModel(str(SOURCE / "models/medium"), device="cpu", compute_type="int8", cpu_threads=4, num_workers=1, local_files_only=True)
FF = ROOT / "video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe"
rows = []
for stem in ["01_promo_jun_v5", "02_summary_jun_v5"]:
    source = EP / "outputs/jun-quality-v2/shorts/v5-ending-fix" / (stem + ".mp4")
    wav = HERE / (stem + "_asr.wav")
    subprocess.run([str(FF), "-v", "error", "-y", "-i", str(source), "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(wav)], check=True)
    segments, info = model.transcribe(str(wav), language="ko", beam_size=5, temperature=0, vad_filter=True, vad_parameters={"min_silence_duration_ms": 200}, condition_on_previous_text=False, initial_prompt=None, word_timestamps=True)
    ss = list(segments)
    row = {"file": str(source), "transcript": " ".join(s.text.strip() for s in ss), "segments": [{"start": s.start, "end": s.end, "text": s.text} for s in ss], "actual_listening": False, "external_upload": False}
    rows.append(row)
    (HERE / "v5_full_asr.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(row, ensure_ascii=False), flush=True)
