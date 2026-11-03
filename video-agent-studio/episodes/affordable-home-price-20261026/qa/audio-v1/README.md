This directory is the only writable scope for this ASR task. All source, narration,
authorization and shared dependency/model files are read-only. All money is KRW.

From C:/projects/realestate_reco, with the existing Python 3.11 installation:

```
tools/python311/python.exe -B -X utf8 video-agent-studio/episodes/affordable-home-price-20261026/qa/audio-v1/test_checks.py
tools/python311/python.exe -B -X utf8 video-agent-studio/episodes/affordable-home-price-20261026/qa/audio-v1/run_asr.py check-ready --chapters 1 2 3 4 5 6 7 8 9 10
tools/python311/python.exe -B -X utf8 video-agent-studio/episodes/affordable-home-price-20261026/qa/audio-v1/run_asr.py small --chapters 1 2 3 4 5 6 7 8 9 10
```

Completed chapter JSON and exact actual WAV SHA are mandatory. Gate checks bind
the frozen script, both content receipts, main authorization and original run
inputs. Native word events, cue source spans and assembled PCM bytes are checked.
Small results are saved incrementally under runs; progress.json indexes them.
The entire decoded chapter is fed to ASR, with no VAD, prompt or hotwords.

For a numeric/coreterm discrepancy in an actual small report, run:

```
tools/python311/python.exe -B -X utf8 video-agent-studio/episodes/affordable-home-price-20261026/qa/audio-v1/run_asr.py medium --small-report <absolute report.json path> --scenes <flagged scene ID>
```

Medium receives only the discrepant paragraph and up to 0.4 seconds of context
on each side. No full-episode medium pass. Silence-only clips are refused.
Timestamp assignment, word spacing, terminology and numeral normalization can
produce false differences. A report marked unresolved needs evidence review;
it is not a confirmed listening error. Both model transcripts remain evidence.

The fixed Systran multilingual small and medium CT2 caches are reused read-only
from the first episode. Revisions, every model file SHA, upstream MIT license
and package versions are recorded in config.json and preparation_proof.json.
CPU int8 is requested; the runtime may report int8_float32 for its CPU backend.
No weights copied, packages installed, network ASR or paid calls. The first
episode's audio and transcripts are not reused.

preparation_proof.json describes the preparation step before audio inference;
it does not describe later runs. Actual audio SHA/decoded duration/native/DSP
coverage is in each new report. ASR and DSP are not listening. Naturalness,
continuous playback, final BGM mix, visual/source and final media approval are
outside this task's current scope. Never change narration or script from QA.
