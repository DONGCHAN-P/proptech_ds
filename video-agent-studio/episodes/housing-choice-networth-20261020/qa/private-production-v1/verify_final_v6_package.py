"""Read-only package audit. All output stays in this QA directory."""
import hashlib
import html
import json
import math
import re
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

QA = Path(__file__).resolve().parent
EP = QA.parents[1]
DEST = QA / 'encoded-v6/final-v1'
SOURCE = EP / 'outputs/private-production-v2'
RELEASE = EP / 'outputs/private-release-v2'
sys.path.insert(0, str(QA / 'asr/deps'))
import av

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def compact(text):
    return re.sub(r'\s+', '', html.unescape(text))

class Captions(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self.current = None
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'p' and 'cue' in a.get('class', '').split():
            self.current = [float(a['data-start']), float(a['data-duration']), '']
    def handle_data(self, data):
        if self.current is not None:
            self.current[2] += data
    def handle_endtag(self, tag):
        if tag == 'p' and self.current is not None:
            self.rows.append(self.current)
            self.current = None

def main():
    manifest = read(DEST / 'input_and_frames.json')
    receipt_path = EP / 'editor/private-production-v2/render_receipt.json'
    receipt = read(receipt_path)
    video = Path(receipt['final_file'])
    timing_path = EP / 'narration/free-tts-v1/final_timing.v6.json'
    timing = read(timing_path)
    edl_path = SOURCE / 'assembly_edl.json'
    edl = read(edl_path)
    plan = read(SOURCE / 'render_plan.json')
    script = EP / 'outputs/script-final-v6/script_v6.md'
    srt_path = SOURCE / 'captions_measured.srt'
    metadata_path = RELEASE / 'metadata_measured.json'
    description_path = RELEASE / 'description_measured.md'
    thumbnail_path = RELEASE / 'thumbnail.png'
    paths = dict(script=script, video=video, subtitles=srt_path, metadata=metadata_path,
                 description=description_path, thumbnail=thumbnail_path, edl=edl_path,
                 narration_timing=timing_path)
    pins = {k + '_sha256': sha(v) for k, v in paths.items()}
    assert pins['script_sha256'] == timing['script_sha256'] == plan['script_sha256'] == manifest['script_sha256']
    assert pins['video_sha256'] == receipt['final_sha256'] == manifest['video_sha256']
    assert pins['subtitles_sha256'] == manifest['subtitles_sha256']
    assert pins['edl_sha256'] == manifest['EDL_sha256']
    assert manifest['independent_full_decode_returncode'] == 0
    assert not (DEST / 'full_decode.log').read_text(encoding='utf-8').strip()
    with av.open(str(video)) as container:
        streams = []
        for s in container.streams:
            c = s.codec_context
            row = dict(type=s.type, codec=c.name, time_base=str(s.time_base),
                       start_s=float(s.start_time * s.time_base), duration_s=float(s.duration * s.time_base))
            if s.type == 'video':
                row.update(width=c.width, height=c.height, pix_fmt=c.format.name,
                           fps=float(s.average_rate), frame_count=s.frames)
                assert (c.name, c.width, c.height, c.format.name, float(s.average_rate)) == ('h264', 1920, 1080, 'yuv420p', 30.0)
                assert s.frames == round(edl['total_seconds'] * 30)
            elif s.type == 'audio':
                row.update(sample_rate=c.sample_rate, channels=c.channels, layout=c.layout.name)
                assert c.name == 'aac' and c.sample_rate == 48000 and c.channels == 2
            streams.append(row)
        duration = container.duration / av.time_base
    assert len(streams) == 2 and abs(duration - edl['total_seconds']) < .002
    assert abs(streams[0]['duration_s'] - streams[1]['duration_s']) < 1/30

    actual = []
    def seconds(value):
        h, m, s, ms = map(int, re.split('[:,]', value))
        return h * 3600 + m * 60 + s + ms / 1000
    for block in re.split(r'\n\s*\n', srt_path.read_text(encoding='utf-8-sig').strip()):
        lines = block.splitlines()
        start, end = lines[1].split(' --> ')
        actual.append((seconds(start), seconds(end), ' '.join(lines[2:])))
    expected = []
    source_checks = []
    display_holds = []
    for chapter in timing['chapters']:
        n = chapter['chapter']
        directory = SOURCE / f'ch{n:02}'
        source_timing_path = directory / 'timing.json'
        source_timing = read(source_timing_path)
        parser = Captions()
        parser.feed((directory / 'index.html').read_text(encoding='utf-8-sig'))
        assert len(parser.rows) == len(source_timing['cues']) == len(chapter['cues'])
        for j, (raw, source, rendered) in enumerate(zip(chapter['cues'], source_timing['cues'], parser.rows)):
            assert raw['id'] == source['id'] and compact(raw['text']) == compact(source['text']) == compact(rendered[2])
            assert abs(raw['start_s'] - source['start_s']) < 1e-6 and abs(raw['end_s'] - source['end_s']) < 1e-6
            assert abs(rendered[0] - raw['start_s']) < 1.1e-6
            # Burned captions intentionally linger up to 80 ms, capped at the next cue.
            display_end = sum(rendered[:2])
            expected_display_end = raw['end_s'] + .08
            if j + 1 < len(chapter['cues']):
                expected_display_end = min(expected_display_end, chapter['cues'][j+1]['start_s'])
            assert abs(display_end - expected_display_end) < 1.1e-6
            display_holds.append(display_end - raw['end_s'])
            matches = [m for m in edl['offset_map'] if m['chapter'] == n and raw['start_s'] >= m['local_start_s'] - 1e-6 and raw['end_s'] <= m['local_end_s'] + 1e-6]
            assert len(matches) == 1
            offset = matches[0]['global_offset_s']
            expected.append((raw['start_s'] + offset, raw['end_s'] + offset, raw['text']))
        source_checks.append(dict(chapter=n, cues=len(parser.rows), html_sha256=sha(directory/'index.html'), timing_sha256=sha(source_timing_path)))
    for current in source_checks:
        rendered_chapter = next(x for x in receipt['chapters'] if x['chapter'] == current['chapter'])
        assert rendered_chapter['html_sha256'] == current['html_sha256']
    assert len(actual) == len(expected) == 342
    errors = []
    for i, (a, b) in enumerate(zip(expected, actual)):
        assert compact(a[2]) == compact(b[2]) and b[0] < b[1]
        assert i == 0 or b[0] >= actual[i-1][1]
        errors.extend([abs(a[0]-b[0]), abs(a[1]-b[1])])
        assert max(errors[-2:]) <= .0011
        for interval in edl['caption_hidden_intervals']:
            assert b[1] <= interval['start_s'] + .0011 or b[0] >= interval['end_s'] - .0011
    source_receipt = read(QA / 'source_v6_pass_receipt.json')
    for item in source_receipt['current_HTML_pins']:
        current = next(x for x in source_checks if x['chapter'] == item['chapter'])
        assert current['html_sha256'] == item['html_sha256'] and current['timing_sha256'] == item['timing_sha256']

    meta = read(metadata_path)
    description = description_path.read_text(encoding='utf-8-sig')
    assert '\ufffd' not in description + srt_path.read_text(encoding='utf-8-sig') + json.dumps(meta, ensure_ascii=False)
    assert meta['visibility'] == 'private' and meta['published'] is False and meta['scheduled'] is False
    assert meta['edl_sha256'] == pins['edl_sha256']
    assert meta['description'] == description_path.name
    # The existing receipt counts LF-normalized UTF-8; pin the real CRLF file separately.
    assert meta['description_bytes'] == len(description.encode('utf-8'))
    chapter_checks = []
    for c in meta['chapters']:
        n = c['chapter']
        start = 0 if n == 1 else next(x['global_start_s'] for x in edl['segments'] if x['id'] == f'chapter_{n}')
        assert abs(c['start_s']-start) < 1e-6
        timestamp = f'{math.floor(start)//60:02}:{math.floor(start)%60:02}'
        assert c['timestamp'] == timestamp and f"{timestamp} {c['title']}" in description
        chapter_checks.append(dict(chapter=n, exact_start_s=start, published_timestamp=timestamp))
    main_receipt_path = EP / 'director/two-episode-production-v1/edl_review_v6.json'
    main_receipt = read(main_receipt_path)
    assert main_receipt['script_sha256'] == pins['script_sha256'] and main_receipt['edl_sha256'] == pins['edl_sha256'] and main_receipt['subtitles_sha256'] == pins['subtitles_sha256']
    last = timing['chapters'][-1]
    offset = next(x['global_offset_s'] for x in edl['offset_map'] if x['chapter'] == 10)
    speech = offset + last['last_speech_end_s']
    outro = next(x['global_start_s'] for x in edl['segments'] if x['id'] == 'clean_brand_outro')
    assert outro - speech >= 3
    dsp_receipt_path = EP / 'director/two-episode-production-v1/final_signal_v6/receipt.json'
    dsp_log_path = dsp_receipt_path.parent / 'analysis.log'
    dsp = read(dsp_receipt_path)
    log = dsp_log_path.read_text(encoding='utf-8-sig')
    assert dsp['exit_code'] == 0 and dsp['video_sha256'] == pins['video_sha256'] and dsp['ffmpeg_sha256'] == manifest['ffmpeg_sha256']
    for term in ['-17.2 LUFS', '4.1 LU', '-2.8 dBFS', '-2.851937', 'Number of NaNs: 0', 'Number of Infs: 0', 'Number of denormals: 0']:
        assert term in log
    report = dict(status='pass_programmatic_package_checks', checked_at=datetime.now(timezone.utc).isoformat(),
                  **pins, artifact_paths={k:str(v.relative_to(EP)) for k,v in paths.items()},
                  code_sha256=sha(Path(__file__)), video_bytes=video.stat().st_size, duration_s=duration, streams=streams,
                  independent_full_AV_decode=dict(returncode=0, stderr_empty=True, log='encoded-v6/final-v1/full_decode.log', log_sha256=sha(DEST/'full_decode.log')),
                  source_HTML_timing_final_SRT=dict(checked_cues=342, html_timing_chapters=source_checks, current_HTMLs_match_completed_render_receipt=True, text_matches=True, max_rounding_error_s=max(errors), nonoverlap=True, SRT_brand_caption_hidden_intervals=True, HTML_display_end_rule='native cue end + up to 0.080s, capped at next cue; SRT retains native boundaries', HTML_display_hold_min_s=min(display_holds), HTML_display_hold_max_s=max(display_holds), actual_encoded_cue_visual_check='sampled separately; not all 342 cues visually inspected'),
                  metadata_chapter_alignment=chapter_checks, private_metadata_flags_checked=True,
                  description_length=dict(actual_file_bytes=description_path.stat().st_size, LF_normalized_UTF8_bytes=len(description.encode('utf-8')), metadata_description_bytes_basis='LF-normalized UTF-8; raw-file SHA is pinned independently'),
                  last_speech=dict(global_end_estimate_s=speech, basis=last['last_speech_end_basis'], outro_start_s=outro, gap_s=outro-speech, visual_hold_samples='input_and_frames.json', actual_listening=False),
                  reused_main_EDL_receipt=dict(path=str(main_receipt_path.relative_to(EP)), sha256=sha(main_receipt_path), input_pins_match=True),
                  reused_main_DSP=dict(receipt=str(dsp_receipt_path.relative_to(EP)), receipt_sha256=sha(dsp_receipt_path), log_sha256=sha(dsp_log_path), same_video_sha256=True, integrated_LUFS=-17.2, loudness_range_LU=4.1, true_peak_dBFS=-2.8, sample_peak_dBFS=-2.851937, nan_inf_denormal_each=0, own_DSP_rerun=False, actual_listening=False))
    (DEST/'package_checks.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(status=report['status'], cues=342, duration_s=duration, pins=pins), ensure_ascii=False))

if __name__ == '__main__':
    main()
