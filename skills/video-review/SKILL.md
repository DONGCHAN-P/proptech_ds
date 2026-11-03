---
name: video-review
description: Inspect rendered videos for clipped text, subtitle timing, visual repetition, map accuracy, motion discontinuities, and audio problems. Use for video QA or watch-style review; distinguish sampled frames from continuous playback and actual listening.
---

# Video review

Review the final media, not only its source code. Report defects by timecode with evidence and a concrete fix. This skill organizes inspection; it does not add native video or audio perception.

## Inspect

1. Identify the intended MP4, script, timing plan, and user feedback. Use the existing render; do not incur paid generation for inspection.
2. Use ffprobe to inspect duration, resolution, frame rate, and audio streams. An audio stream alone does not prove audible narration or correct speech.
3. Extract representative frames from the actual MP4 with ffmpeg and inspect them with view_image. Include every scene, relevant user timecodes, scene boundaries, and maximum zoom states. Save QA artifacts separately.
4. For suspected stutter, extract closely spaced frames around the affected interval and inspect continuity. If supported browser/player control is available, also inspect continuous playback. Do not claim continuous viewing from sparse stills.
5. Compare caption boundaries with narration segments and check for cuts, missing intervals, or overlap. When audio listening/transcription is available, compare actual speech with the approved script; otherwise mark this check unverified. ASR is supporting evidence, not a naturalness score.

## Visual checks

- Keep titles, captions, and source credits outside background zoom transforms. Inspect safe margins and mobile readability.
- Geographic explanations should use actual map geometry and correctly projected location markers. Identify representative regional pins, schematic routes, planned infrastructure, and AI conceptual imagery accurately.
- Check source credits and whether the asset depicts the named place. Attribution is not itself permission to reuse an image.
- Compare chart periods, area groups, units, denominators, and sample sizes. Do not invent comparator values to fill a chart.
- Flag repeated imagery in adjacent scenes, unexplained whitespace, oversized labels, and chart numbers that contradict narration.
- For three-reason summaries, follow the user's chosen layout. For the realestate_reco video, use meaningful icons on the left and three concise reasons on the right.
- Animate deterministic frame-based values. Avoid repeated data fetching/calculation inside frames and unintended spring overshoot.

## Tools and output

Prefer installed ffmpeg/ffprobe. In realestate_reco, bundled binaries may be under video/node_modules/@remotion/compositor-win32-x64-msvc/. These binaries may lack filters or output formats; check capabilities before relying on volumedetect, astats, tile, or PCM extraction. Choose a supported alternative if unavailable.

Basic still extraction: ffmpeg -ss TIME -i INPUT.mp4 -frames:v 1 OUTPUT.png. Verify successful output and inspect the image. A Remotion still is useful for layout iteration but is not proof of the final encoded frame.

Write a brief QA report with inspected intervals, confirmed defects, remaining unchecked areas, and reproduction evidence. Distinguish stream presence, measured audio activity, speech verification, and human listening. Never claim full audiovisual review unless it actually occurred.

Fix defects within the user's authorized editing scope, then verify changed intervals in the new render. Preserve the approved voice and script unless the user requests changes or a factual correction is necessary. Reuse existing generated assets; do not submit new paid API requests just to review.
