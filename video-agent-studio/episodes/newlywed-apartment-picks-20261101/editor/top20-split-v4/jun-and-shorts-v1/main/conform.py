"""Accepted-picture conformer. No TTS, alignment, audio editing, or director writes.

Decode the accepted picture once in source-frame order, select whole 1080p YUV
frames through the director's piecewise anchors, then encode picture and captioned
delivery from that same raw stream. No crop/scale/optical-flow or old source audio.
"""
from __future__ import annotations
import argparse
import bisect
import hashlib
import html
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import time

HERE = Path(__file__).resolve().parent
EPISODE = HERE.parents[3]
ROOT = EPISODE.parents[2]
OUTPUT = EPISODE / 'outputs/top20-split-v4/jun-and-shorts-v1/main'
DIRECTOR = EPISODE / 'director/top20-split-v4/part1-jun-and-shorts-v1'
LOCK = DIRECTOR / 'locked_timing.json'
ACCEPTED = EPISODE / 'outputs/top20-split-v4/map-clean-v1/part1_map_clean_photo_v1.mp4'
ACCEPTED_SHA = 'a8d7771668848fe406d76e429db85026f1b300e634d6096b0a780390a9a2a064'
OLD_LOCK = EPISODE / 'director/top20-split-v4/part1-map-clean-v1/locked_timing.json'
INTRO_LOCK = EPISODE / 'director/top20-split-v4/part1-intro-v3/locked_timing.json'
TRANSITIONS = EPISODE / 'director/top20-split-v4/part1-map-clean-v1/transition_plan.json'
MANIFEST = EPISODE / 'narration/top20-split-v4/jun-and-shorts-v1/narration_manifest.json'
FF = ROOT / 'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
FP = ROOT / 'video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe'
FPS, WIDTH, HEIGHT = 30, 1920, 1080
FRAME_BYTES = WIDTH * HEIGHT * 3 // 2
RAIL_Y = 922
NO_WINDOW = getattr(subprocess, 'CREATE_NO_WINDOW', 0)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(2**20), b''):
            h.update(b)
    return h.hexdigest()


def owned(path):
    p = Path(path).resolve()
    if not any(p.is_relative_to(r.resolve()) for r in (HERE, OUTPUT)):
        raise ValueError(f'Out-of-scope output: {p}')
    return p


def save(path, value):
    p = owned(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def write(path, value):
    p = owned(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(value, encoding='utf-8')


def resolve_input(value):
    if isinstance(value, dict):
        value = value.get('path', value.get('file'))
    p = Path(value)
    if p.is_absolute():
        return p
    for r in (ROOT, EPISODE, DIRECTOR):
        if (r / p).exists():
            return r / p
    raise FileNotFoundError(value)


def input_pair(d, key):
    value = d[key]
    digest = value.get('sha256') if isinstance(value, dict) else None
    digest = digest or d.get(key + '_sha256') or d.get(key + '_sha')
    if not digest:
        raise ValueError(f'Missing {key}_sha256')
    p = resolve_input(value)
    if sha(p) != digest:
        raise ValueError(f'Input hash mismatch: {key}')
    return p, digest


def probe(path):
    p = subprocess.run([str(FP), '-v', 'error', '-show_streams', '-show_format',
                        '-of', 'json', str(path)], capture_output=True, check=True,
                       creationflags=NO_WINDOW)
    return json.loads(p.stdout)


def native_sentences():
    """Only assemble an index of existing accepted timestamps; never align Jun."""
    old, intro = read(OLD_LOCK), read(INTRO_LOCK)
    candidates = intro['intro_sentences'] + old['criteria_sentences']
    candidates += [s for sc in old['body_scenes'] for s in sc['sentences']]
    by_id = {s['sentence_id']: s for s in candidates}
    # The two inherited legend sentences moved after the 12.8s accepted insert.
    result = []
    for m in read(MANIFEST)['sentences']:
        if m.get('kind') != 'accepted_main':
            continue
        s = dict(by_id[m['sentence_id']])
        if s['sentence_id'] in ('P01-INTRO-V3-07', 'P01-INTRO-V3-08'):
            for k in ('start_s', 'end_s'):
                s[k] += old['insert_duration_s']
        if normalize(s.get('text', s.get('display_text', ''))) != normalize(m['text']):
            raise ValueError(f'Accepted sentence mismatch: {m["sentence_id"]}')
        result.append(s)
    if len(result) != 90:
        raise ValueError('Expected exactly 90 accepted main sentences')
    return result


def normalize(text):
    return ''.join(str(text).split())


class Warp:
    def __init__(self, rows, total_s, source_total_s):
        self.rows = []
        for row in rows:
            s, t = float(row['source_s']), float(row['target_s'])
            if not all(math.isfinite(x) and x >= 0 for x in (s, t)):
                raise ValueError('Non-finite/negative anchor')
            if self.rows and (s < self.rows[-1]['source_s'] - 1e-8 or
                              t < self.rows[-1]['target_s'] - 1e-8):
                raise ValueError(f'Non-monotonic anchors: {self.rows[-1]} -> {row}')
            if self.rows and s == self.rows[-1]['source_s'] and t == self.rows[-1]['target_s']:
                continue
            self.rows.append(dict(row, source_s=s, target_s=t))
        if len(self.rows) < 2:
            raise ValueError('Need actual source/target anchor pairs')
        self.source = [r['source_s'] for r in self.rows]
        self.target = [r['target_s'] for r in self.rows]
        tol = 1 / FPS + 1e-6
        if abs(self.source[0]) > 1e-6 or abs(self.target[0]) > 1e-6:
            raise ValueError('Parent must supply the (0,0) pose boundary')
        if abs(self.source[-1] - source_total_s) > tol or abs(self.target[-1] - total_s) > tol:
            raise ValueError('Parent must supply the actual source/target end boundary')

    @staticmethod
    def interpolate(x, xs, ys):
        i = max(0, min(len(xs) - 2, bisect.bisect_right(xs, x) - 1))
        if xs[i + 1] == xs[i]:
            return ys[i + 1]
        u = min(1., max(0., (x - xs[i]) / (xs[i + 1] - xs[i])))
        return ys[i] + u * (ys[i + 1] - ys[i])

    def source_at(self, target_s):
        return self.interpolate(target_s, self.target, self.source)

    def target_at(self, source_s):
        return self.interpolate(source_s, self.source, self.target)


def windows(d):
    bi, bo = d['brand_intro'], d['brand_outro']
    return [(0., float(bi['start_s'])),
            (float(bi['start_s']) + 5., float(bo['start_s']))]


def check_contract(d, *, source_smoke=False):
    old = read(OLD_LOCK)
    if not source_smoke and d.get('status') is not None and 'locked' not in d['status']:
        raise ValueError('Canonical actual Jun timing lock is not ready')
    source, source_sha = input_pair(d, 'source_video')
    if source_sha != ACCEPTED_SHA:
        raise ValueError('Only the user-accepted a8d777 source is authorized')
    audio, audio_sha = (None, None) if source_smoke else input_pair(d, 'master_audio')
    p = probe(source)
    v = next(s for s in p['streams'] if s['codec_type'] == 'video')
    if (v['width'], v['height'], v['r_frame_rate']) != (WIDTH, HEIGHT, '30/1'):
        raise ValueError('Accepted full-frame 1080p/30 source required')
    expected = [s['sentence_id'] for s in read(MANIFEST)['sentences'] if s.get('kind') == 'accepted_main']
    new, before = d['main_sentences'], d['source_old_sentences']
    if [s['sentence_id'] for s in new] != expected or [s['sentence_id'] for s in before] != expected:
        raise ValueError('Source and target must contain the same ordered 90 main sentences; no Shorts CTA')
    for a, b in zip(before, new):
        for key in ('text', 'reading_text'):
            if key in a and key in b and normalize(a[key]) != normalize(b[key]):
                raise ValueError(f'Changed main content: {a["sentence_id"]}/{key}')
        if not 0 <= b['start_s'] < b['end_s'] <= d['last_spoken_end_s'] + .05:
            raise ValueError(f'Bad actual sentence timing: {b["sentence_id"]}')
        if not source_smoke and not b.get('words'):
            raise ValueError(f'Native Jun words missing: {b["sentence_id"]}')
    bi, bo = d['brand_intro'], d['brand_outro']
    if abs(bi['duration_s'] - 5) > 1e-6 or abs(bo['duration_s'] - 10) > 1e-6:
        raise ValueError('Brand duration must be exactly 5s / 10s')
    if abs(bo['start_s'] - (d['last_spoken_end_s'] + 3)) > 1/FPS + 1e-6:
        raise ValueError('Outro must start at actual last spoken end + 3s (natural tail included)')
    if abs(d['total_s'] - bo['start_s'] - 10) > 1/FPS + 1e-6:
        raise ValueError('Total duration must end after one 10s brand outro')
    w = Warp(d['source_to_target_anchors'], d['total_s'], float(p['format']['duration']))
    checks = []
    for k, duration in [('brand_intro', 5), ('brand_outro', 10)]:
        s0, t0 = old[k]['start_s'], d[k]['start_s']
        deviations = [abs(w.source_at(t0 + u) - (s0 + u)) for u in [0, duration*.25, duration*.5, duration*.75, duration-.034]]
        if max(deviations) > 2 / FPS:
            raise ValueError(f'{k} is stretched or displaced: {max(deviations):.6f}s')
        checks.append({'check': k + '_unit_rate', 'max_error_s': max(deviations)})
    # Read-only reuse of the accepted photo transition plan; do not regenerate it.
    for photo in read(TRANSITIONS)['photos']:
        for label, s0, length in [('entry', photo['final_start_s'], .52),
                                  ('exit', photo['final_end_s'] - .55, .55)]:
            actual = w.target_at(s0 + length) - w.target_at(s0)
            if abs(actual - length) > 2 / FPS:
                raise ValueError(f'P01-R{photo["rank"]} photo {label} stretched: {actual:.6f}s')
            checks.append({'check': f'R{photo["rank"]}_{label}_fixed', 'length_s': actual})
    captions = d['captions']
    if not captions:
        raise ValueError('Actual meaning-unit captions required')
    last_end = -1.
    by_sentence = {}
    for cue in captions:
        start, end = float(cue['start_s']), float(cue['end_s'])
        if end <= start or start < last_end - .001:
            raise ValueError('Overlapping/empty native caption cues')
        if cue['sentence_id'] not in expected:
            raise ValueError('Caption is not one of the 90 main sentences')
        if not any(start >= a - .001 and end <= b + .001 for a, b in windows(d)):
            raise ValueError('Caption overlaps brand picture / lies outside narration rail')
        by_sentence.setdefault(cue['sentence_id'], []).append(cue['text'])
        last_end = end
    for sentence in new:
        text = sentence.get('display_text', sentence.get('text'))
        if normalize(''.join(by_sentence.get(sentence['sentence_id'], []))) != normalize(text):
            raise ValueError(f'Caption content missing/changed: {sentence["sentence_id"]}')
    return {'source': source, 'source_sha': source_sha, 'audio': audio, 'audio_sha': audio_sha,
            'source_probe': p, 'source_frames': int(v['nb_frames']), 'warp': w,
            'checks': checks, 'mask_windows': windows(d)}


def copy_asset(source, dest):
    dest = owned(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        shutil.copyfile(source, dest)
    elif sha(source) != sha(dest):
        raise ValueError(f'Asset collision: {dest}')


def assets(project):
    from PIL import Image, ImageDraw
    a = project / 'assets'
    a.mkdir(parents=True, exist_ok=True)
    base = EPISODE / 'editor/top20-split-v4/part1-production-v1/final-v3/assets'
    for name in ('gsap.min.js', 'Pretendard-Regular.woff2', 'Pretendard-Bold.woff2'):
        copy_asset(base / name, a / name)
    ttf = ROOT / 'video-agent-studio/episodes/capital-10eok-map-20261017/visual/map-preview-v1/Pretendard-Regular.ttf'
    copy_asset(ttf, a / 'Pretendard-Regular.ttf')
    copy_asset(ttf, a / 'fonts/Pretendard-Regular.ttf')
    image = Image.new('RGB', (WIDTH, HEIGHT - RAIL_Y), '#f6f4ef')
    ImageDraw.Draw(image).rounded_rectangle((96, 20, 1823, 129), radius=18, fill='white')
    image.save(owned(a / 'caption_rail.png'))


def wrap_text(text, font_path):
    from PIL import ImageFont
    font = ImageFont.truetype(str(font_path), 39)
    lines = ['']
    for word in text.split():
        candidate = (lines[-1] + ' ' + word).strip()
        # No negative tracking, so both native HTML and libass share these widths.
        if font.getlength(candidate) > 1644:
            if not lines[-1] or len(lines) == 2:
                raise ValueError(f'Caption does not fit two full-size lines: {text}')
            lines.append(word)
        else:
            lines[-1] = candidate
    if any(font.getlength(line) > 1644 for line in lines):
        raise ValueError('Protected long token overflows caption rail')
    return lines


def ass_time(seconds):
    ticks = round(seconds * 100)
    return f'{ticks//360000}:{ticks//6000%60:02d}:{ticks//100%60:02d}.{ticks%100:02d}'


def emit_project(d, info, project, offset=0., duration=None, picture='assets/conformed_picture.mp4'):
    project = owned(project)
    project.mkdir(parents=True, exist_ok=True)
    assets(project)
    duration = d['total_s'] - offset if duration is None else duration
    masks = [(max(0., a-offset), min(duration, b-offset)) for a,b in info['mask_windows'] if b > offset and a < offset+duration]
    cues = []
    for cue in d['captions']:
        a, b = max(0., cue['start_s']-offset), min(duration, cue['end_s']-offset)
        if b > a:
            cues.append(dict(cue, start_s=a, end_s=b,
                             lines=wrap_text(cue['text'], project/'assets/Pretendard-Regular.ttf')))
    css = """@font-face{font-family:Pretendard;src:url('assets/Pretendard-Regular.woff2')}
*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;background:#f6f4ef}
#root{position:relative;width:100%;height:100%;overflow:hidden}
.picture{position:absolute;inset:0;width:100%;height:100%;object-fit:contain}
.rail{position:absolute;left:0;top:922px;width:1920px;height:158px}
.caption{position:absolute;left:138px;top:945px;width:1644px;height:104px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;color:#173348;font-family:Pretendard,sans-serif;font-size:39px;line-height:1.3;white-space:pre}
.line{height:50.7px;flex-shrink:0}
"""
    h = ["<!doctype html><html lang='ko'><head><meta charset='utf-8'><script src='assets/gsap.min.js'></script><link rel='stylesheet' href='style.css'></head><body>",
         f"<div id='root' data-composition-id='jun-main' data-width='1920' data-height='1080' data-duration='{duration:.9f}'>",
         f"<video id='accepted-picture-conformed' class='clip picture' src='{html.escape(picture)}' data-start='0' data-duration='{duration:.9f}' data-track-index='0' muted playsinline></video>"]
    for i, (a,b) in enumerate(masks):
        h.append(f"<img id='old-caption-mask-{i}' class='clip rail' src='assets/caption_rail.png' data-start='{a:.9f}' data-duration='{b-a:.9f}' data-track-index='1'/>")
    for i, c in enumerate(cues):
        lines = ''.join(f"<span class='line'>{html.escape(line)}</span>" for line in c['lines'])
        h.append(f"<div id='jun-caption-{i}' class='clip caption' data-sentence-id='{html.escape(c['sentence_id'])}' data-start='{c['start_s']:.9f}' data-duration='{c['end_s']-c['start_s']:.9f}' data-track-index='2' data-layout-allow-caption-zone>{lines}</div>")
    if info['audio']:
        dest = owned(project/'assets/master_audio.wav')
        if not dest.exists():
            os.link(info['audio'], dest)
        if not os.path.samefile(info['audio'], dest):
            raise ValueError('HF master must be a read-only reference to parent audio')
        h.append(f"<audio id='parent-master-audio' src='assets/master_audio.wav' data-start='0' data-media-start='{offset:.9f}' data-duration='{duration:.9f}' data-track-index='3'></audio>")
    h.append("</div><script>const tl=gsap.timeline({paused:true});window.__timelines['jun-main']=tl;</script></body></html>")
    write(project/'index.html', '\n'.join(h))
    write(project/'style.css', css)
    save(project/'hyperframes.json', {'name':'accepted-main-Jun-conform-v1','width':WIDTH,'height':HEIGHT,'fps':FPS})
    save(project/'native_captions.json', cues)
    save(project/'mask_windows.json', masks)
    # CSS font-size uses em units; libass uses the font's ascent+descent.
    # Match the shipped Pretendard hhea metrics instead of making delivery text
    # ~16% smaller than the native editable HF layer.
    from fontTools.ttLib import TTFont
    font = TTFont(project/'assets/Pretendard-Regular.ttf')
    ass_size = 39 * (font['hhea'].ascent - font['hhea'].descent) / font['head'].unitsPerEm
    font.close()
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Main,Pretendard,FONT_SIZE,&H00483317,&H00483317,&H00FFFFFF,&H00FFFFFF,0,0,0,0,100,100,0,0,1,0,0,5,138,138,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    header = header.replace('FONT_SIZE', f'{ass_size:.6f}')
    for c in cues:
        for i, line in enumerate(c['lines']):
            text = line.replace('{', r'\{').replace('}', r'\}')
            y = 997 + (i-(len(c['lines'])-1)/2) * 50.7
            header += f"Dialogue: 0,{ass_time(c['start_s'])},{ass_time(c['end_s'])},Main,,0,0,0,,{{\\an5\\pos(960,{y:.3f})}}{text}\n"
    write(project/'captions.ass', header)
    return cues, masks


def exact_read(stream, size):
    data = bytearray()
    while len(data) < size:
        chunk = stream.read(size-len(data))
        if not chunk:
            raise EOFError(f'Decoder ended midframe ({len(data)}/{size})')
        data.extend(chunk)
    return data


def encode(d, info, project, destination, offset=0., duration=None):
    """Both encodes consume identical unscaled source frames; audio is only remuxed/encoded."""
    destination = owned(destination)
    if destination.exists():
        raise FileExistsError(f'Preserve existing version: {destination}')
    requested_duration = d['total_s']-offset if duration is None else duration
    frames = math.ceil(requested_duration*FPS-1e-7)
    duration = frames/FPS
    emit_project(d, info, project, offset, duration)
    pic = owned(project/'assets/conformed_picture.mp4')
    if pic.exists():
        raise FileExistsError(pic)
    destination.parent.mkdir(parents=True, exist_ok=True)
    logs = project/'logs'; logs.mkdir(exist_ok=True)
    source_frames = [min(info['source_frames']-1, max(0, math.floor(info['warp'].source_at(offset+i/FPS)*FPS+1e-7))) for i in range(frames)]
    if source_frames != sorted(source_frames):
        raise ValueError('Frame map regresses')
    save(project/'frame_map.json', {'fps':FPS,'target_offset_s':offset,'source_frame_indices':source_frames,
                                   'sampling':'floor(source_s*30); nearest preceding whole source frame; no interpolation'})
    seek_frame = source_frames[0]
    dec = [str(FF),'-v','error','-ss',f'{seek_frame/FPS:.9f}','-i',str(info['source']),
           '-an','-sn','-dn','-pix_fmt','yuv420p','-fps_mode','passthrough','-f','rawvideo','pipe:1']
    masks = read(project/'mask_windows.json')
    expr = '+'.join(f'between(n,{math.ceil(a*FPS-1e-7)},{math.ceil(b*FPS-1e-7)-1})' for a,b in masks) or '0'
    filters = f"[0:v]split=2[picture][base];[base][2:v]overlay=x=0:y={RAIL_Y}:enable='{expr}'[clean];[clean]ass=filename=captions.ass:fontsdir=assets/fonts[delivery]"
    enc = [str(FF),'-v','warning','-nostdin','-f','rawvideo','-pixel_format','yuv420p',
           '-video_size',f'{WIDTH}x{HEIGHT}','-framerate',str(FPS),'-i','pipe:0']
    if info['audio']:
        enc += ['-ss',f'{offset:.9f}','-i',str(info['audio'])]
    else:
        enc += ['-f','lavfi','-i','anullsrc=r=48000:cl=stereo']
    enc += ['-loop','1','-framerate',str(FPS),'-i','assets/caption_rail.png',
            '-filter_complex',filters,
            '-map','[picture]','-an','-c:v','libx264','-preset','fast','-crf','16','-threads','3',
            '-pix_fmt','yuv420p','-frames:v',str(frames),'-movflags','+faststart',str(pic),
            '-map','[delivery]','-map','1:a:0','-c:v','libx264','-preset','fast','-crf','16','-threads','3',
            '-pix_fmt','yuv420p','-c:a','aac','-b:a','320k','-ar','48000','-ac','2',
            '-frames:v',str(frames),'-t',f'{duration:.9f}','-movflags','+faststart',str(destination)]
    save(project/'render_command.json', {'decoder':dec,'encoder':enc,'encoder_cwd':str(project),
        'source_sampling':'frame_map.json','no_crop':True,'no_scale':True,'old_audio_used':False,
        'master_processing':'No timing/gain/mix changes. PCM -> AAC 320k delivery only.'})
    started = time.monotonic()
    with (logs/'decode.stderr.log').open('wb') as dl, (logs/'encode.stderr.log').open('wb') as el:
        decoder = subprocess.Popen(dec,stdout=subprocess.PIPE,stderr=dl,creationflags=NO_WINDOW)
        encoder = subprocess.Popen(enc,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=el,cwd=project,creationflags=NO_WINDOW)
        current, raw = seek_frame-1, None
        try:
            for wanted in source_frames:
                while current < wanted:
                    raw = exact_read(decoder.stdout, FRAME_BYTES)
                    current += 1
                encoder.stdin.write(raw)
            encoder.stdin.close()
            code = encoder.wait()
            decoder.stdout.close()
            decoder.terminate()
            decoder.wait()
            if code:
                raise RuntimeError(f'Encoder exit {code}; see {logs}')
        except BaseException:
            for process in (decoder, encoder):
                if process.poll() is None:
                    process.terminate()
                    process.wait()
            raise
    p = probe(destination)
    video = next(s for s in p['streams'] if s['codec_type']=='video')
    if (video['width'],video['height'],video['r_frame_rate'],int(video['nb_frames'])) != (WIDTH,HEIGHT,'30/1',frames):
        raise ValueError('Actual encoded video specification mismatch')
    decode = [str(FF),'-v','error','-xerror','-i',str(destination),'-map','0:v:0','-map','0:a:0','-f','null','-']
    with (logs/'delivery_decode.stderr.log').open('wb') as log:
        result = subprocess.run(decode,stdout=subprocess.DEVNULL,stderr=log,creationflags=NO_WINDOW)
    if result.returncode:
        raise RuntimeError('Strict delivery decode failed')
    receipt = {'status':'encoded_and_strict_decode_passed','video':str(destination),'video_sha256':sha(destination),
               'picture':str(pic),'picture_sha256':sha(pic),'probe':p,'target_offset_s':offset,'duration_s':frames/FPS,
               'frames':frames,'requested_duration_s':requested_duration,'end_quantization_s':duration-requested_duration,
               'elapsed_s':round(time.monotonic()-started,3),'source_video_sha256':info['source_sha'],
               'master_audio_sha256':info['audio_sha'],'crop_or_scale':False,'frame_interpolation':False,
               'new_paid_calls':0,'actual_listening':False,'continuous_playback':False}
    save(project/'render_receipt.json',receipt)
    return receipt


def proof_ranges(d, w):
    bi = d['brand_intro']
    p = read(TRANSITIONS)['photos'][0]
    price = next(s for s in d['main_sentences'] if s['sentence_id']=='P01-R20-V2-05')
    ranges = [('question_brand',0.,bi['start_s']+5.+.25),
              ('photo_to_map',w.target_at(p['final_start_s'])-.15,w.target_at(p['final_end_s'])+1.),
              ('new_price_focus',price['start_s']-.2,price['end_s']+.3)]
    return [(name,max(0,math.floor(a*FPS))/FPS,math.ceil(b*FPS)/FPS) for name,a,b in ranges]


def proofs(d, info, version, *, source_smoke=False):
    result=[]
    for name,a,b in proof_ranges(d,info['warp']):
        project=HERE/version/name
        out=OUTPUT/version/f'{name}.mp4'
        receipt=encode(d,info,project,out,a,b-a)
        times=[min(b-a-1/FPS,(b-a)*.25),min(b-a-1/FPS,(b-a)*.75)]
        for i,t in enumerate(times):
            frame=owned(project/f'proof_{i+1}.jpg')
            subprocess.run([str(FF),'-v','error','-i',str(out),'-ss',f'{t:.9f}',
                            '-frames:v','1','-q:v','2',str(frame)],check=True,creationflags=NO_WINDOW)
        result.append({'name':name,'start_s':a,'end_s':b,'receipt':str(project/'render_receipt.json'),
                       'video':str(out),'sha256':receipt['video_sha256']})
    save(HERE/version/'proofs.json',{'status':'awaiting_internal_frame_review',
         'source_smoke_only':source_smoke,'not_Jun_timing':source_smoke,'proofs':result,
         'lock_sha256':None if source_smoke else sha(LOCK)})
    return result


def prepare():
    OUTPUT.mkdir(parents=True,exist_ok=True)
    original=read(OLD_LOCK)
    if sha(ACCEPTED)!=ACCEPTED_SHA:
        raise ValueError('Accepted video hash mismatch')
    p=probe(ACCEPTED)
    old=native_sentences()
    save(HERE/'source_input_manifest.json',{'task_id':'accepted-main-Jun-conform-v1','source_video':str(ACCEPTED),
         'source_video_sha256':ACCEPTED_SHA,'source_probe':p,
         'accepted_timing_sha256':sha(OLD_LOCK),'intro_timing_sha256':sha(INTRO_LOCK),
         'transition_plan_sha256':sha(TRANSITIONS),'narration_manifest_sha256':sha(MANIFEST),
         'source_sentence_ids':[s['sentence_id']for s in old],
         'accepted_brand_intro':original['brand_intro'],'accepted_brand_outro':original['brand_outro'],
         'rail_mask_rect':[0,922,1920,158],'map_footer_and_photo_credit_preserved_above_y':922,
         'crop_or_scale':False,'tts_or_paid_api':False})
    save(HERE/'issue_INPUTLOCK.json',{'issue_id':'INPUTLOCK','scene_id':'P01-ALL',
         'problem':'최종 Jun 마스터와 총괄의 실제 시간표가 아직 준비되지 않음',
         'evidence':{'canonical_lock':str(LOCK),'exists_at_prepare':LOCK.exists()},
         'proposal':'총괄이 canonical lock 작성 후 compile → proofs → 내부 프레임검토 → render 실행',
         'impact':'현재는 원본 실제 타이밍의 파이프라인 실증만 가능. 새 Jun 시간 추정 금지.',
         'next_role':'director/narration'})
    save(HERE/'handoff.json',{'task_id':'accepted-main-Jun-conform-v1','role':'editor',
         'status':'conformer_prepared_awaiting_parent_actual_lock','input_revisions':{'source_sha256':ACCEPTED_SHA},
         'outputs':[str(HERE/'conform.py'),str(HERE/'source_input_manifest.json')],
         'affected_scene_ids':['P01-ALL'],'checks':[{'check':'accepted_source_hash_and_probe','result':'passed','evidence':str(HERE/'source_input_manifest.json')}],
         'open_issue_ids':['INPUTLOCK'],'next_role':'director'})
    return {'status':'prepared','canonical_lock_exists':LOCK.exists(),'main_sentence_count':len(old)}


def source_smoke(version='source-smoke-v1'):
    old=read(OLD_LOCK)
    d={'status':'source_validation_only_NOT_Jun','source_video':str(ACCEPTED),'source_video_sha256':ACCEPTED_SHA,
       'source_old_sentences':native_sentences(),'main_sentences':native_sentences(),
       'captions':old['captions'],'brand_intro':old['brand_intro'],'brand_outro':old['brand_outro'],
       'last_spoken_end_s':old['last_spoken_end_s'],'total_s':old['total_s'],
       'source_to_target_anchors':[{'source_s':0.,'target_s':0.,'kind':'source_validation_origin'},
          {'source_s':old['total_s'],'target_s':old['total_s'],'kind':'source_validation_end'}]}
    save(HERE/version/'contract_NOT_Jun.json',d)
    info=check_contract(d,source_smoke=True)
    return proofs(d,info,version,source_smoke=True)


def compile_lock(version):
    if not LOCK.exists():
        raise FileNotFoundError(f'Parent actual timing lock pending: {LOCK}')
    d=read(LOCK)
    info=check_contract(d)
    project=HERE/version/'project'
    emit_project(d,info,project)
    manifest={'task_id':'accepted-main-Jun-conform-v1','lock':str(LOCK),'lock_sha256':sha(LOCK),
       'source_video':str(info['source']),'source_video_sha256':info['source_sha'],
       'master_audio':str(info['audio']),'master_audio_sha256':info['audio_sha'],
       'anchor_count':len(info['warp'].rows),'main_sentences':90,'caption_count':len(d['captions']),
       'total_s':d['total_s'],'mask_windows':info['mask_windows'],'checks':info['checks'],
       'render_route':'whole_source_frames_piecewise_parent_anchors_shared_raw_YUV_two_encodes',
       'not_rendered_yet':True,'actual_listening':False,'continuous_playback':False}
    save(HERE/version/'input_manifest.json',manifest)
    return d,info


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('action',choices=['prepare','source-smoke','compile','proofs','render'])
    ap.add_argument('--version',default='jun-v1')
    args=ap.parse_args()
    if '/' in args.version or '\\' in args.version or args.version in ('.','..'):
        raise ValueError('Version must be one directory name')
    if args.action=='prepare':
        result=prepare()
    elif args.action=='source-smoke':
        result=source_smoke('source-smoke-v1' if args.version=='jun-v1' else args.version)
    else:
        d,info=compile_lock(args.version)
        lock_digest=sha(LOCK)
        if args.action=='compile':
            result={'status':'compiled_actual_parent_lock','lock_sha256':sha(LOCK)}
        elif args.action=='proofs':
            result=proofs(d,info,args.version+'-proofs')
        else:
            review=read(HERE/(args.version+'-proofs')/'proof_review.json')
            proof=read(HERE/(args.version+'-proofs')/'proofs.json')
            if review.get('status')!='passed' or review.get('lock_sha256')!=sha(LOCK) or proof['lock_sha256']!=sha(LOCK):
                raise ValueError('Three actual-Jun proofs must pass internal review for this lock before full render')
            for row in proof['proofs']:
                if sha(row['video'])!=row['sha256']:
                    raise ValueError('Proof changed after review')
            result=encode(d,info,HERE/args.version/'project',OUTPUT/f'part1_Jun_conform_{args.version}.mp4')
            if sha(LOCK)!=lock_digest or sha(info['audio'])!=info['audio_sha']:
                raise ValueError('Parent input changed during render; do not deliver this version')
            result['lock_sha256']=lock_digest
            save(HERE/args.version/'render_receipt.json',result)
    print(json.dumps(result,ensure_ascii=False),flush=True)


if __name__=='__main__':
    main()
