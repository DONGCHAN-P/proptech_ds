"""Read-only final MP4 validation and independent local frame evidence."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageFont, ImageStat

QA = Path(__file__).resolve().parent
EP = QA.parent.parent
ROOT = EP.parents[2]
PROD = EP / 'outputs/private-production-v1'
OUT = QA / 'encoded-evidence-independent-v1'
OUT.mkdir(exist_ok=True)


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


plan = read(QA / 'encoded_sampling_plan_v4.json')
receipt_path = EP / 'editor/render_receipt.json'
receipt = read(receipt_path)
producer_path = PROD / 'encoded_frame_plan.json'
producer = read(producer_path)
critical_path = PROD / 'encoded_critical_frames.json'
critical = read(critical_path)
video = Path(receipt['final_file'])
actual_sha = sha(video)
assert actual_sha == receipt['final_sha256'] == producer['final_sha256'] == critical['final_sha256'] == 'ad9df5989c019395e9ea9eb7877c81300cf78e9ab611536ebcc7431c8fc3609a'
assert video.stat().st_size == 58010976
assert receipt['full_AV_decode'] and receipt['decode_returncode'] == producer['extract_returncode'] == 0
for value in plan['artifacts'].values():
    assert sha(value['path']) == value['sha256'], value['path']
source = read(QA / 'source_approval_v4.json')
for actual, approved in zip(receipt['chapters'], source['postcarve_HTML']):
    assert actual['chapter'] == approved['chapter']
    assert actual['html_sha256'] == sha(approved['path']) == approved['postcarve_html_sha256']
manifest_path = Path(receipt['input_manifest_file'])
assert sha(manifest_path) == receipt['input_manifest_sha256']
manifest = read(manifest_path)
assert manifest['script_sha256'] == plan['artifacts']['script']['sha256']
assert manifest['timing_sha256'] == plan['artifacts']['timing']['sha256']
assert manifest['EDL_sha256'] == plan['artifacts']['edl']['sha256']
assert manifest['SRT_sha256'] == plan['artifacts']['subtitles']['sha256']
producer_files = {}
for item in producer['samples'] + producer['contact_sheets'] + [producer['contact_overview']] + critical['frames']:
    path = PROD / item['file']
    assert sha(path) == item['sha256'], path
    producer_files[path.as_posix()] = item['sha256']
assert len({item['global_frame'] for item in producer['samples']}) == 185

ffmpeg = ROOT / 'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
ffprobe = ROOT / 'video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe'
assert sha(ffmpeg) == producer['ffmpeg_sha256']
probe_run = subprocess.run([str(ffprobe), '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(video)], capture_output=True, check=True)
probe = json.loads(probe_run.stdout)
dump(OUT / 'ffprobe.json', probe)
v = next(s for s in probe['streams'] if s['codec_type'] == 'video')
a = next(s for s in probe['streams'] if s['codec_type'] == 'audio')
assert (v['width'], v['height'], v['r_frame_rate'], int(v['nb_frames'])) == (1920, 1080, '30/1', 35581)
assert v['codec_name'] == 'h264' and a['codec_name'] == 'aac' and int(a['sample_rate']) == 48000 and a['channels'] == 2
assert abs(float(probe['format']['duration']) - plan['expected_seconds']) < 1 / 30
assert abs(float(v['duration']) - float(a['duration'])) < 1 / 30

targets = sorted(s['frame_index'] for s in plan['samples'])
expression = '+'.join(f'eq(n\\,{index})' for index in targets)
command = [str(ffmpeg), '-hide_banner', '-nostdin', '-v', 'info', '-xerror', '-threads', '2', '-i', str(video),
           '-map', '0:v:0', '-an', '-vf', 'select=' + expression + ',showinfo', '-fps_mode', 'vfr',
           '-start_number', '0', '-y', str(OUT / '%05d.png')]
with (OUT / 'extract.log').open('w', encoding='utf-8') as log:
    result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
assert result.returncode == 0
log_text = (OUT / 'extract.log').read_text(encoding='utf-8')
observed = re.findall(r'\bn:\s*(\d+)\s+pts:\s*(-?\d+)\s+pts_time:([0-9.\-]+)', log_text)
assert len(observed) == len(targets) == 552, len(observed)
numerator, denominator = map(int, v['time_base'].split('/'))
rows = []
for i, (index, observed_row) in enumerate(zip(targets, observed)):
    output_n, pts, printed_time = observed_row
    assert int(output_n) == i
    actual_pts_s = int(pts) * numerator / denominator
    assert abs(actual_pts_s - index / 30) < 1e-8, (i, index, observed_row)
    path = OUT / f'{i:05}.png'
    image = Image.open(path)
    assert image.size == (1920, 1080)
    rows.append({'frame_index': index, 'actual_pts': int(pts), 'time_base': v['time_base'],
                 'actual_pts_s': actual_pts_s, 'file': path.as_posix(), 'sha256': sha(path),
                 'mean_luma': ImageStat.Stat(image.convert('L')).mean[0],
                 'luma_stddev': ImageStat.Stat(image.convert('L')).stddev[0]})
by_frame = {r['frame_index']: r for r in rows}
font = ImageFont.truetype('C:/Windows/Fonts/malgun.ttf', 19)
sheet_manifest = []


def sheets(label, items, columns, width, height, per_sheet, crop=None):
    for batch_start in range(0, len(items), per_sheet):
        batch = items[batch_start:batch_start + per_sheet]
        row_count = (len(batch) + columns - 1) // columns
        sheet = Image.new('RGB', (columns * width, row_count * (height + 30)), 'white')
        draw = ImageDraw.Draw(sheet)
        included = []
        for i, (frame_row, description) in enumerate(batch):
            image = Image.open(frame_row['file']).convert('RGB')
            if crop:
                image = image.crop(crop)
            image = image.resize((width, height), Image.Resampling.LANCZOS)
            x, y = (i % columns) * width, (i // columns) * (height + 30)
            sheet.paste(image, (x, y + 30))
            draw.text((x + 4, y + 3), description, font=font, fill='#17354a')
            included.append(frame_row['frame_index'])
        filename = OUT / f'{label}_{batch_start // per_sheet + 1:02}.png'
        sheet.save(filename)
        sheet_manifest.append({'group': label, 'path': filename.as_posix(), 'sha256': sha(filename),
                               'frame_indices': included, 'crop': crop})


caption_items = [(by_frame[c['representative_frame']], c['cue_id'] + f"  {c['representative_frame']/30:.3f}s")
                 for c in plan['caption_representatives']]
sheets('captions150', caption_items, 1, 1200, 92, 20, (96, 872, 1824, 1004))
join_items = []
for join in plan['EDL_joins']:
    for frame in join['frames']:
        join_items.append((by_frame[frame], f"{join['right']}  f{frame} / {frame/30:.3f}s"))
sheets('joins12', join_items, 3, 480, 270, 12)
chapter_items = [(by_frame[ch['frame']], f"CH{ch['chapter']:02}  {ch['frame']/30:.3f}s") for ch in plan['chapters']]
sheets('chapter10', chapter_items, 2, 640, 360, 10)
producer_boundary = []
for sample in producer['samples']:
    if sample['role'] in ('scene_after_start', 'scene_before_end'):
        producer_boundary.append(({'file': str(PROD / sample['file']), 'frame_index': sample['global_frame']},
                                  f"{sample['scene_id']} {sample['role']} / {sample['global_time_s']:.3f}s"))
sheets('scene_boundaries90', producer_boundary, 3, 480, 270, 15)
special_items = []
for frame in plan['samples']:
    categories = {target['category'] for target in frame['targets']}
    if categories & {'clean_brand', 'post_intro', 'caption_hidden_interval', 'CTA_last_voice', 'last_frame'}:
        special_items.append((by_frame[frame['frame_index']], f"{','.join(sorted(categories))} / {frame['frame_index']/30:.3f}s"))
sheets('brand_CTA', special_items, 2, 640, 360, 10)

evidence = {'status': 'actual_frames_extracted_pending_visual_judgment', 'at_utc': datetime.now(timezone.utc).isoformat(),
            'video': {'path': video.as_posix(), 'sha256': actual_sha, 'bytes': video.stat().st_size},
            'render_receipt': {'path': receipt_path.as_posix(), 'sha256': sha(receipt_path)},
            'producer_manifest': {'path': producer_path.as_posix(), 'sha256': sha(producer_path)},
            'producer_evidence_files_SHA_verified': len(producer_files), 'producer_unique_frames': 185,
            'input_manifest_sha256_verified': sha(manifest_path), 'source_HTML_10_match_approved': True,
            'ffprobe': {'path': (OUT / 'ffprobe.json').as_posix(), 'sha256': sha(OUT / 'ffprobe.json')},
            'ffmpeg_sha256': sha(ffmpeg), 'ffprobe_sha256': sha(ffprobe), 'extract_argv': command,
            'extract_returncode': result.returncode, 'extract_log_sha256': sha(OUT / 'extract.log'),
            'all_actual_PTS_match_expected': True, 'frames': rows, 'contact_sheets': sheet_manifest,
            'actual_listening': False, 'continuous_playback': False}
dump(QA / 'actual_encoded_evidence_v1.json', evidence)
print(json.dumps({'status': evidence['status'], 'frames': len(rows), 'sheets': len(sheet_manifest),
                  'producer_evidence_files_SHA_verified': len(producer_files), 'video_sha256': actual_sha}, ensure_ascii=False))
