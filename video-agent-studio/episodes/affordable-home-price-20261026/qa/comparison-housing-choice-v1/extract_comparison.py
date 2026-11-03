"""Read-only media comparison; write only separate QA frame evidence."""
import concurrent.futures
import hashlib
import json
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
EPS = ROOT / 'video-agent-studio/episodes'
FFMPEG = ROOT / 'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
FFPROBE = ROOT / 'video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe'
INPUTS = [
    ('baseline', 'housing-choice-networth-20261020', 'jun-production-v1',
     'renders/measured-jun-v1/housing_choice_jun_v1.mp4',
     '136a20c43ba3a99a138ba7282c1fb1a8532fc3aa92695c57ca2f904d011b1079'),
    ('next', 'affordable-home-price-20261026', 'private-production-v1',
     'renders/measured-v3-visual-v4-r1/affordable_home_price_private_voice_v3_visual_v4.mp4',
     'ad9df5989c019395e9ea9eb7877c81300cf78e9ab611536ebcc7431c8fc3609a'),
]

def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()

def globtime(edl, chapter, t):
    for seg in edl['segments']:
        if seg.get('chapter') == chapter and seg['source_start_s'] <= t < seg['source_end_s']:
            return seg['global_start_s'] + t - seg['source_start_s']
    raise ValueError((chapter, t))

def extract(job):
    result = subprocess.run([str(FFMPEG), '-hide_banner', '-loglevel', 'error', '-ss', str(job['time_s']),
                             '-i', job['video'], '-frames:v', '1', '-vf', 'scale=960:540', '-y', job['image']],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert Path(job['image']).is_file()

def main():
    jobs, records = [], {}
    for label, epn, prod, video_rel, expected in INPUTS:
        p = EPS / epn / 'outputs' / prod
        video = p / video_rel
        assert sha(video) == expected
        probe = json.loads(subprocess.check_output([str(FFPROBE), '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(video)], text=True))
        edl = read(p / 'assembly_edl.json')
        scenes = []
        for chapter in range(1, 11):
            timing = read(p / f'ch{chapter:02d}/timing.json')
            for s in timing['scenes']:
                start = s.get('clip_start_s', s['start_s'])
                end = s.get('clip_end_s', s['end_s'])
                mid = (start + end) / 2
                time_s = globtime(edl, chapter, mid)
                image = OUT / 'frames' / label / f'C{chapter:02d}_{s["scene_id"]}_{time_s:.3f}.png'
                image.parent.mkdir(parents=True, exist_ok=True)
                row = {'chapter': chapter, 'scene_id': s['scene_id'], 'title': s.get('title', s.get('message', '')),
                       'local_start_s': start, 'local_end_s': end, 'duration_s': end-start,
                       'time_s': time_s, 'image': str(image), 'video': str(video)}
                scenes.append(row)
                jobs.append(row)
        records[label] = {'video': str(video), 'sha256': expected, 'probe': probe, 'scenes': scenes}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(extract, jobs))
    font = ImageFont.truetype('C:/Windows/Fonts/malgun.ttf', 19)
    for label, record in records.items():
        rows = record['scenes']
        for page in range((len(rows)+11)//12):
            part = rows[page*12:page*12+12]
            sheet = Image.new('RGB', (1920, 4*408), '#e3e5e7')
            draw = ImageDraw.Draw(sheet)
            for i, row in enumerate(part):
                x, y = (i%3)*640, (i//3)*408
                frame = Image.open(row['image']).resize((640,360))
                sheet.paste(frame, (x,y))
                t = row['time_s']
                label_text = f'{int(t//60):02d}:{t%60:04.1f} C{row["chapter"]:02d}/{row["scene_id"]} {row["title"]}'
                draw.text((x+8,y+363),label_text[:46],font=font,fill='black')
            sheet.save(OUT/f'{label}_sheet_{page+1}.jpg',quality=93)
    (OUT/'evidence.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({label:{'scenes':len(r['scenes']),'seconds':r['probe']['format']['duration']} for label,r in records.items()}))

if __name__ == '__main__':
    main()
