"""고정 MP4/SRT/전역 EDL 증거 수집. 자동 육안 승인·청취·ASR 기능 없음."""
import argparse
import hashlib
import json
import math
import pathlib
import re
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
EP = HERE.parents[2]
ROOT = EP.parents[2]
FFMPEG = ROOT / 'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
FFPROBE = ROOT / 'video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe'
KINDS = {'funding_waterfall', 'ltv_dsr', 'monthly_budget'}


def owned(path):
    path = pathlib.Path(path).resolve()
    if not path.is_relative_to(HERE):
        raise ValueError('QA 소유범위 밖 쓰기: ' + str(path))
    return path


def new_run(path):
    path = owned(path)
    if path.exists():
        raise ValueError('기존 결과 보존: 새 run 경로 필요')
    path.mkdir(parents=True)
    return path


def read(path):
    return json.loads(pathlib.Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    h = hashlib.sha256()
    with pathlib.Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def dump(path, value):
    owned(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf8')


def checked(ref):
    path = pathlib.Path(ref['path'])
    path = (path if path.is_absolute() else EP / path).resolve()
    if not path.is_relative_to(ROOT) or path.name == '.env' or not re.fullmatch('[a-f0-9]{64}', ref.get('sha256', '')):
        raise ValueError('로컬 고정 입력 ref 필요')
    if sha(path) != ref['sha256']:
        raise ValueError('SHA 불일치: ' + str(path))
    return path


def parse_srt(text):
    cues = []
    pattern = r'(\d+):(\d{2}):(\d{2})[,.](\d{3})'
    def seconds(groups):
        h, m, s, ms = map(int, groups)
        if m > 59 or s > 59:
            raise ValueError('SRT 시각 범위')
        return h * 3600 + m * 60 + s + ms / 1000
    for block in re.split(r'\n\s*\n', text.lstrip('\ufeff').replace('\r\n', '\n').strip()):
        lines = block.splitlines()
        if len(lines) < 3:
            raise ValueError('SRT 블록 손상')
        match = re.fullmatch(pattern + r'\s+-->\s+' + pattern, lines[1])
        if not match:
            raise ValueError('SRT 타임코드 손상')
        start, end = seconds(match.groups()[:4]), seconds(match.groups()[4:])
        if start >= end or not ''.join(lines[2:]).strip() or any(x['id'] == lines[0] for x in cues):
            raise ValueError('SRT 시간·텍스트·ID 오류')
        cues.append({'id': lines[0], 'start_s': start, 'end_s': end, 'text': '\n'.join(lines[2:])})
    if any(b['start_s'] < a['end_s'] - .001 for a, b in zip(cues, cues[1:])):
        raise ValueError('SRT 겹침/순서 오류')
    return cues


def make_plan(edl, script_ids, cues, scope='full'):
    if edl['clock'] != 'global_frames' or edl['fps'] != 30:
        raise ValueError('실측 전역 30fps 프레임 EDL 필요')
    total = edl['total_frames']
    if type(total) is not int or total < 1:
        raise ValueError('프레임 수 오류')
    scenes = edl['scenes']
    ids = [s['scene_id'] for s in scenes]
    if len(ids) != len(set(ids)) or ids != [sid for sid in script_ids if sid in ids]:
        raise ValueError('원문 장면 순서/중복 불일치')
    if scope == 'full' and (len(script_ids) != 34 or ids != script_ids):
        raise ValueError('최종은 원문 배열의 34장면 전체 필요')
    if scope not in ['full', 'representatives'] or not ids:
        raise ValueError('검수 scope 오류')
    def interval(row):
        a, b = row['start_frame'], row['end_frame']
        if type(a) is not int or type(b) is not int or not 0 <= a < b <= total:
            raise ValueError('end-exclusive 프레임 구간 오류')
        return a, b
    segments = [interval(s) for s in edl['segments']]
    if not segments or segments[0][0] != 0 or segments[-1][1] != total or any(a[1] != b[0] for a, b in zip(segments, segments[1:])):
        raise ValueError('브랜드/챕터 포함 전체 EDL 구간 누락/겹침')
    intervals = {s['scene_id']: interval(s) for s in scenes}
    if any(a['end_frame'] > b['start_frame'] for a, b in zip(scenes, scenes[1:])):
        raise ValueError('장면 구간 겹침')
    rows = {}
    def add(frame, reason):
        if type(frame) is not int or not 0 <= frame < total:
            raise ValueError('표본 프레임 범위')
        rows.setdefault(frame, []).append(reason)
    for sid, (a, b) in intervals.items():
        add(a, f'scene:{sid}:opening')
        add((a + b - 1) // 2, f'scene:{sid}:mid')
        add(b - 1, f'scene:{sid}:final')
    add(total - 1, 'film:final')
    for scene in scenes:
        a, b = intervals[scene['scene_id']]
        for j, frame in enumerate(scene.get('beat_frames', [])):
            if type(frame) is not int or not a <= frame < b:
                raise ValueError('장면 앵커 범위 오류')
            for delta, phase in [(-1, 'before'), (0, 'onset'), (4, 'motion'), (16, 'settled')]:
                add(max(a, min(b - 1, frame + delta)), f'beat:{scene["scene_id"]}:{j}:{phase}')
    cuts = {a for a, _ in segments[1:]} | {v for bounds in intervals.values() for v in bounds if 0 < v < total}
    for cut in sorted(cuts):
        for frame, label in [(cut - 1, 'before'), (cut, 'after'), (cut + 1, 'next')]:
            if frame < total:
                add(frame, f'cut:{cut}:{label}')
    exact_cues = edl.get('cues')
    if exact_cues is not None and len(exact_cues) != len(cues):
        raise ValueError('EDL/SRT 자막 수 불일치')
    for index, cue in enumerate(cues):
        if exact_cues is not None:
            exact = exact_cues[index]
            first, end = interval(exact)
            expected_text = '\n'.join(exact.get('display_lines', [exact['text']]))
            if (' '.join(expected_text.split()) != ' '.join(cue['text'].split()) or
                    abs(cue['start_s'] - first / 30) > .00051 or
                    abs(cue['end_s'] - end / 30) > .00051):
                raise ValueError('EDL/SRT 자막 내용·전역 프레임 불일치: ' + cue['id'])
            last = end - 1
        else:
            first = math.ceil(cue['start_s'] * 30 - 1e-8)
            last = math.ceil(cue['end_s'] * 30 - 1e-8) - 1
        if first > last or first < 0 or last >= total:
            raise ValueError('실제 표시 프레임이 없는/범위 밖 자막: ' + cue['id'])
        add((first + last) // 2, f'caption:{cue["id"]}:mid')
    progressions = edl['progressions']
    kinds = {x['kind'] for x in progressions}
    if not progressions or len(kinds) != len(progressions) or not kinds <= KINDS:
        raise ValueError('진행 표본 유형/중복 오류')
    if scope == 'full' and kinds != KINDS:
        raise ValueError('3종 진행 표본 명시 필요')
    for row in progressions:
        a, b = intervals[row['scene_id']]
        beats = row['beat_frames']
        if row['timing_basis'] not in ['native_word_boundary', 'forced_alignment', 'manual_audio_verified'] or len(beats) < 2 or beats != sorted(set(beats)) or any(type(f) is not int or not a <= f < b for f in beats):
            raise ValueError('실측 전역 앵커 필요')
        for j, frame in enumerate(beats):
            for delta, phase in [(-1, 'before'), (0, 'onset'), (4, 'motion'), (16, 'settled')]:
                add(max(a, min(b - 1, frame + delta)), f'progression:{row["kind"]}:{j}:{phase}')
    zoom = edl.get('zoom', {})
    if zoom.get('mode') not in ['fixed', 'keyframed'] or (zoom['mode'] == 'keyframed' and not zoom.get('max_frames')):
        raise ValueError('고정 구도 또는 실제 최대 줌 프레임 명시 필요')
    for frame in zoom.get('max_frames', []):
        add(frame, 'max_zoom')
    for frame in edl.get('inspection_frames', []):
        add(frame, 'requested_inspection')
    return [{'frame_index': f, 'reasons': sorted(set(tags))} for f, tags in sorted(rows.items())]


def command(argv, out, err):
    with owned(out).open('w', encoding='utf8') as stdout, owned(err).open('w', encoding='utf8') as stderr:
        result = subprocess.run([str(x) for x in argv], stdout=stdout, stderr=stderr, check=False)
    if result.returncode:
        raise ValueError('도구 실패; 로그: ' + str(err))


def collect(packet_path, run):
    packet_path = pathlib.Path(packet_path).resolve()
    packet = read(packet_path)
    refs = {k: checked(packet[k]) for k in ['script_lock', 'script', 'mp4', 'srt', 'edl', 'render_receipt', 'source_manifest']}
    lock = read(refs['script_lock'])
    if lock.get('approved') is not True or lock['script_sha256'] != packet['script']['sha256']:
        raise ValueError('승인 잠금 대본 SHA 불일치')
    manifest = read(refs['source_manifest'])
    if manifest['script_sha256'] != packet['script']['sha256']:
        raise ValueError('렌더 소스 manifest 대본 SHA 불일치')
    for ref in manifest['files']:
        checked(ref)
    projects = packet['source_projects']
    for row in projects:
        for key in ['html', 'model']:
            checked(row[key])
    script, edl = read(refs['script']), read(refs['edl'])
    if len(projects) != len(edl['scenes']):
        raise ValueError('장면별 소스 수 불일치')
    # Every actual anchor gets encoded before/onset/motion/settled samples,
    # including semantic labels that a geometry pass cannot validate.
    for scene, project in zip(edl['scenes'], projects):
        model = read(checked(project['model']))
        if model.get('template_only') is not False or model['scene_id'] != scene['scene_id']:
            raise ValueError('실제 음성 기반 장면 model/ID 필요')
        scene['beat_frames'] = [scene['start_frame'] + math.ceil(b['start_s'] * 30 - 1e-8) for b in model['beats']]
    cues = parse_srt(refs['srt'].read_text(encoding='utf-8-sig'))
    plan = make_plan(edl, [s['id'] for s in script['scenes']], cues, packet['scope'])
    if [r['scene_id'] for r in projects] != [s['scene_id'] for s in edl['scenes']]:
        raise ValueError('장면별 HTML/model 입력 누락 또는 순서 불일치')
    run = new_run(run)
    receipt = {'status': 'collecting', 'scope': packet['scope'], 'evidence_kind': packet['evidence_kind'], 'packet_sha256': sha(packet_path), 'inputs': {k: packet[k] for k in refs}, 'tools': {str(x): sha(x) for x in [FFMPEG, FFPROBE]}, 'continuous_playback': False, 'actual_listening': False, 'manual_frames_viewed': 0, 'final_independent_media_approval': 'unchecked', 'ASR': 'parent_owned_not_run'}
    try:
        command([FFPROBE, '-v', 'error', '-show_format', '-show_streams', '-of', 'json', refs['mp4']], run/'probe.json', run/'probe.log')
        probe = read(run/'probe.json')
        video = next(s for s in probe['streams'] if s['codec_type'] == 'video')
        audio = next(s for s in probe['streams'] if s['codec_type'] == 'audio')
        if (video['width'], video['height'], video['r_frame_rate'], audio['sample_rate'], audio['channels'], video['codec_name'], audio['codec_name']) != (1920, 1080, '30/1', '48000', 2, 'h264', 'aac'):
            raise ValueError('현행 제작 규격 불일치')
        command([FFMPEG, '-v', 'error', '-xerror', '-i', refs['mp4'], '-map', '0:v:0', '-map', '0:a:0', '-f', 'null', '-'], run/'decode.stdout', run/'decode.log')
        receipt['full_AV_decode'] = 'pass'
        command([FFPROBE, '-v', 'error', '-select_streams', 'v:0', '-show_frames', '-show_entries', 'frame=best_effort_timestamp_time', '-of', 'json', refs['mp4']], run/'frame_pts.json', run/'frame_pts.log')
        frames = read(run/'frame_pts.json')['frames']
        pts = [float(x['best_effort_timestamp_time']) for x in frames]
        if len(pts) != edl['total_frames'] or any(abs(t - i/30) > .0001 for i, t in enumerate(pts)):
            raise ValueError('전역 EDL과 실제 디코드 프레임 수/CFR PTS 불일치')
        (run/'frames').mkdir()
        expression = "select='" + '+'.join(f'eq(n,{r["frame_index"]})' for r in plan) + "',showinfo"
        (run/'select.filter').write_text(expression, encoding='utf8')
        command([FFMPEG, '-n', '-v', 'info', '-i', refs['mp4'], '-map', '0:v:0', '-an', '-filter_script:v', run/'select.filter', '-fps_mode', 'passthrough', run/'frames/%06d.png'], run/'extract.stdout', run/'extract.log')
        images = sorted((run/'frames').glob('*.png'))
        actual = [float(x) for x in re.findall(r'\bpts_time:([\d.e+-]+)', (run/'extract.log').read_text(encoding='utf8'))]
        if len(images) != len(plan) or len(actual) != len(plan) or any(abs(t - pts[r['frame_index']]) > .0001 for r, t in zip(plan, actual)):
            raise ValueError('추출 PNG/실제 PTS 대응 실패')
        for row, image in zip(plan, images):
            row.update(path=str(image), sha256=sha(image), pts_s=pts[row['frame_index']], manual_viewed=False)
        dump(run/'frame_index.json', plan)
        geometry = []
        for scene, project in zip(edl['scenes'], projects):
            times = [(r['frame_index']-scene['start_frame'])/30 for r in plan if scene['start_frame'] <= r['frame_index'] < scene['end_frame']]
            geometry.append({**project, 'html': {**project['html'], 'path': str(checked(project['html']))}, 'model': {**project['model'], 'path': str(checked(project['model']))}, 'times_s': sorted(set([0, *times]))})
        dump(run/'geometry_input.json', {'projects': geometry})
        command(['node', HERE/'geometry_review.cjs', run/'geometry_input.json', run/'geometry_receipt.json'], run/'geometry.stdout', run/'geometry.log')
        from PIL import Image, ImageDraw
        sheets = []
        for start in range(0, len(plan), 30):
            rows = plan[start:start+30]
            canvas = Image.new('RGB', (1920, math.ceil(len(rows)/6)*205), '#dfe2e5')
            draw = ImageDraw.Draw(canvas)
            for i, row in enumerate(rows):
                x, y = i%6*320, i//6*205
                with Image.open(row['path']) as im:
                    canvas.paste(im.convert('RGB').resize((320,180)), (x,y))
                draw.text((x+4,y+183), f'n={row["frame_index"]}  {row["pts_s"]:.3f}s', fill='#172f43')
            target = run/f'contact-{start//30:03}.png'
            canvas.save(target)
            sheets.append({'path':str(target),'sha256':sha(target),'manual_viewed':False})
        # Collection never asserts visual approval, even when technical checks pass.
        for ref in [*packet.values()]:
            if isinstance(ref, dict) and 'path' in ref and 'sha256' in ref:
                checked(ref)
        for ref in manifest['files']:
            checked(ref)
        receipt.update(status='evidence_ready_NOT_visually_reviewed', sampled_frames_extracted=len(plan), caption_midpoints=len(cues), contact_sheets=sheets, geometry_status=read(run/'geometry_receipt.json')['status'], source_to_encoded_binding_review='unchecked', C01='required_pending_visual_review', C04='required_pending_visual_review')
    except Exception as exc:
        receipt.update(status='collection_failed', error=str(exc))
        raise
    finally:
        dump(run/'collection_receipt.json', receipt)
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('packet')
    parser.add_argument('--run', required=True)
    args = parser.parse_args()
    result = collect(args.packet, args.run)
    print(json.dumps({'status': result['status'], 'sampled_frames': result['sampled_frames_extracted'], 'final_media_approval': 'unchecked'}, ensure_ascii=False))
