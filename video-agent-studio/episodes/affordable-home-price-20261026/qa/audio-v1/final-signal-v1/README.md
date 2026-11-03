This stage preserves audio_gate_v3.json exactly at
52b3c4284925f68225974aebcde9aa77ae1838d4c8ca32d1925897829164b639.
It writes only this final-signal-v1 directory. No ASR, model, TTS, narration,
editor, source, state or gate updates are performed.

Preparation and synthetic counter/parser tests are complete. These synthetic
tests are not measurements of the current final MP4.

After editor/render_receipt.json has status
rendered_technical_pass_independent_media_review_pending, exact final SHA,
full_AV_decode=true and decode_returncode=0, run from the workspace:

```
tools/python311/python.exe -B -X utf8 video-agent-studio/episodes/affordable-home-price-20261026/qa/audio-v1/final-signal-v1/measure_signal.py analyze
```

The runner checks frozen inputs and MP4 SHA, reuses the existing FFmpeg7.1
binary at its pinned SHA, and performs one audio-only decode. No video frames
are decoded and Carson's full AV decode is not repeated. The same pass feeds
ebur128(true peak), astats and streamed float32 counters. The full-film PCM
stream is not saved. Clipped/rail count means finite sample values with
abs(sample)>=1; it is not astats Peak count. NaN, Inf and float32 denormal
values are counted separately. Duration, rate and channels are recorded.

All12EDLjoins have50ms PCM windows collected in that same pass. Their sample
steps and8ms-before/after RMS/peaks are measurements of encoded signal only.
The source assembly graph's13segments each have an8ms in/out fade and the
end-fade placement is independently audited. Source fades, encoded residual
signal and perceived clicks are distinct claims. AAC can smear exact fades.

Actual results will be signal_receipt.json, analysis.log and handoff.json,
bound to the exact final MP4 SHA. A start marker prevents automatic repeat of
an actual DSP pass after a failure; preserve any partial logs for review.

The first film's-17.2LUFS/-2.8dBTP is context, not an exact required target.
Only observed nonfinite/rail/silence/duration problems block this technical
signal scope. Material level/headroom or large boundary-step observations are
recommendations with their actual values; no normalization or rerender occurs.

Actual listening, continuous playback, perceived voice/music balance and
naturalness remain unchecked. This stage does not approve source visuals,
the full media deliverable, upload, Studio or ContentID.
