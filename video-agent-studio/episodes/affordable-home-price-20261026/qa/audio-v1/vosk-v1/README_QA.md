This QA runner owns only its code, prepared PCM, results and evidence here.
Main alone provisions deps/ and model-cache/. The runner does not install,
download, modify model files, synthesize speech or alter original audio.

Preparation, already safe before Vosk is provisioned:

```
tools/python311/python.exe -B -X utf8 video-agent-studio/episodes/affordable-home-price-20261026/qa/audio-v1/vosk-v1/run_vosk.py prepare
```

It uses the existing pinned FFmpeg to convert only production-injoon-v3 raw
S019/S024 to PCM WAV:16000Hz,16bit,mono. It records source/resampled SHA,
headers, exact FFmpeg command and binary/version. No inference is performed.

After main supplies a successful completed provision receipt, QA must inspect
that receipt, its model/package SHA evidence and local Vosk API. Then run:

```
tools/python311/python.exe -B -X utf8 video-agent-studio/episodes/affordable-home-price-20261026/qa/audio-v1/vosk-v1/run_vosk.py run --receipt <actual receipt path> --receipt-sha256 <verified SHA256> --model <actual model-cache/vosk-model-small-ko-0.22 path>
```

The whole two paragraphs are decoded with local Kaldi/Vosk0.3.45. Model receives
only the local model_path; KaldiRecognizer receives only(model,16000).
SetWords(True) retains recognized words/confidence. No grammar argument,
SetGrammar, expected-number list, hotwords, prompt, numeric token suppression
or source-text bias. Every PCM frame is consumed; Result and FinalResult JSON
are preserved. Numeric comparison runs after recognition. Python sockets are
blocked and local imports use dont_write_bytecode so deps remains read-only.

Main reports official Korean model vosk-model-small-ko-0.22,82M,Apache2.0,
reported WER28.1. These facts are provenance from main until matched with the
provision receipt and shipped metadata. Model files/tree SHA and actual
package/license metadata are recorded at runtime. A different ASR family is
independent evidence; the model size or family does not establish accuracy.

Existing standard Whisper and failed no-digit evidence stays preserved. Two
Vosk result files are raw evidence, not automatic approval. Review the actual
Hangul numerals, omissions and unit/digit differences before issuing a new
independent review. The existing numeric hold remains open during preparation.
Actual listening, naturalness, continuous playback and final mix are unchecked.
No optional cue re-decodes are scheduled in this prepared bounded runner.
