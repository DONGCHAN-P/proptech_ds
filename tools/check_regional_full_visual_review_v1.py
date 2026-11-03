"""Inspect a real encoded visual-review file; never imply speech or playback QA."""
from pathlib import Path
import argparse, datetime as dt, hashlib, json, math, re, subprocess
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
EP = ROOT / 'video-agent-studio/episodes/regional-price-recovery-20261022'
OUT = EP / 'outputs/production-v1-jun'

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def rel(path):
    return path.relative_to(ROOT).as_posix()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--video', required=True)
    parser.add_argument('--revision', default='v1')
    args = parser.parse_args()
    assert re.fullmatch(r'v\d+', args.revision)
    video = (ROOT / args.video).resolve()
    video.relative_to(EP)
    timing = read(OUT / 'project/timing_resolved.json')
    display_path = OUT / 'checks/visual-review/captions.json'
    display = read(display_path)
    assert timing['timing_locked'] is False, 'This inspector is for provisional visual review'
    assert timing['script_sha256'] == '99b40e8730ee0f8fdf74402cffbe04b5b418540344e6d2a7175e6a01c3054664'
    assert display['timing_locked'] is False and display['body_offset'] == 5
    assert not (EP / 'narration/production-v1/authorization.json').exists()
    decision = read(ROOT / 'output/video_decisions/decisions/5fe307eed02c.json')
    assert decision.get('resolution') == 'deferred_by_user'
    assets = read(OUT / 'reusable_assets/manifest.json')
    ff, probe = assets['ffmpeg'], assets['ffprobe']
    dest = EP / 'director/production-v1' / ('full_visual_review_' + args.revision)
    dest.mkdir(parents=True, exist_ok=True)
    frames = dest / 'frames'
    frames.mkdir(exist_ok=True)
    info = json.loads(subprocess.check_output([probe, '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(video)], text=True, encoding='utf8'))
    vs = [s for s in info['streams'] if s['codec_type'] == 'video']
    aus = [s for s in info['streams'] if s['codec_type'] == 'audio']
    assert len(vs) == 1 and len(aus) == 1
    assert [vs[0]['width'], vs[0]['height']] == [1920, 1080]
    assert vs[0]['r_frame_rate'] == '30/1'
    body_end = max(b['end'] for b in timing['beats'])
    expected_frames = 150 + math.ceil((body_end + 3) * 30 - 1e-6) + 300
    assert int(vs[0]['nb_frames']) == expected_frames, (vs[0]['nb_frames'], expected_frames)
    assert abs(float(info['format']['duration']) - expected_frames / 30) < .1
    decoded = subprocess.run([ff, '-v', 'error', '-i', str(video), '-f', 'null', '-'], capture_output=True, text=True, encoding='utf8', errors='replace')
    (dest / 'decode.log').write_text(decoded.stderr, encoding='utf8')
    assert decoded.returncode == 0 and not decoded.stderr.strip(), 'Full decode errors'
    print(json.dumps({'phase':'stream_and_full_decode_pass','duration':expected_frames/30}), flush=True)
    samples = []
    for beat in timing['beats']:
        samples.append((beat['beat_id'] + '_middle', 5 + (beat['start'] + beat['end']) / 2, 'beat_middle'))
    cuts = [('intro_body', 5.0)]
    for beat in timing['beats']:
        if beat['start'] > 0:
            cuts.append((beat['beat_id'] + '_start', 5 + beat['start']))
    cuts.append(('body_hold', 5 + body_end))
    cuts.append(('hold_outro', 5 + (expected_frames - 450) / 30))
    for name, point in cuts:
        for n, delta in enumerate([-1/30, 0, 1/30]):
            samples.append((name + '_' + str(n), point + delta, 'boundary_triplet'))
    longest = sorted([(c, c['beat_id']) for c in display['captions']], key=lambda item:len(item[0]['text']), reverse=True)[:5]
    for index, (cue, beat) in enumerate(longest):
        samples.append((f'long_caption_{index}_{beat}', 5 + (cue['start'] + cue['end']) / 2, 'long_caption'))
    samples += [('intro_middle', 2.5, 'brand'), ('outro_middle', expected_frames / 30 - 5, 'brand')]
    evidence = []
    for name, point, kind in samples:
        path = frames / (name + '.png')
        subprocess.run([ff, '-v', 'error', '-y', '-ss', f'{point:.8f}', '-i', str(video), '-frames:v', '1', str(path)], check=True, capture_output=True)
        with Image.open(path) as im:
            assert im.size == (1920, 1080)
        evidence.append({'name':name,'seconds':round(point,8),'kind':kind,'path':rel(path),'sha256':sha(path)})
    sheets = []
    for page in range(math.ceil(len(evidence) / 16)):
        items = evidence[page*16:(page+1)*16]
        canvas = Image.new('RGB', (1920, 1208), '#eeeae3')
        draw = ImageDraw.Draw(canvas)
        for i, item in enumerate(items):
            x, y = (i % 4) * 480, (i // 4) * 302
            draw.text((x+4,y+3), f"{item['name']} @ {item['seconds']:.3f}s", fill='#173348')
            with Image.open(ROOT/item['path']) as im:
                canvas.paste(im.resize((480,270)), (x,y+25))
        path = dest / f'contact_sheet_{page+1:02d}.png'
        canvas.save(path)
        sheets.append(rel(path))
    # Signal measurements are separate from actual listening.
    sound = subprocess.run([ff, '-hide_banner', '-i', str(video), '-vn', '-af', 'volumedetect', '-f', 'null', '-'], capture_output=True, text=True, encoding='utf8', errors='replace')
    assert sound.returncode == 0
    (dest/'audio_signal.log').write_text(sound.stderr, encoding='utf8')
    values = dict(re.findall(r'(mean_volume|max_volume):\s*([^\s]+) dB', sound.stderr))
    assert 'max_volume' in values and math.isfinite(float(values['max_volume']))
    assert 'mean_volume' in values and math.isfinite(float(values['mean_volume']))
    report = {'at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'status':'technical_pass_visual_inspection_pending',
        'video':{'path':rel(video),'sha256':sha(video),'bytes':video.stat().st_size,'duration':expected_frames/30,'frames':expected_frames,'resolution':[1920,1080],'fps':30},
        'stream_info':info,'full_decode':'pass','audio_signal_db':values,'narration_generated':False,'timing_locked':False,
        'timing_sha256':sha(OUT/'project/timing_resolved.json'),'display_captions_sha256':sha(display_path),'body_offset_seconds':5,'last_caption_end':5+body_end,
        'outro_start':5+(expected_frames-450)/30,'caption_to_outro_gap':3,
        'samples':evidence,'contact_sheets':sheets,'actual_listening_performed':False,'continuous_playback_performed':False,
        'not_verified':['narration alignment and naturalness: voice deferred','continuous playback','mobile playback','public release official index crosscheck']}
    (dest/'technical.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    print(json.dumps({'status':report['status'],'samples':len(evidence),'sheets':sheets,'video_sha256':report['video']['sha256']}, ensure_ascii=False))

if __name__ == '__main__':
    main()
