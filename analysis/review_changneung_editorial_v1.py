import concurrent.futures
import json
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
ep = root / 'video-agent-studio/episodes/goyang-changneung-20261015'
out = ep / 'qa/editorial-review-v1/root_frames'
out.mkdir(parents=True, exist_ok=True)
ffmpeg = 'C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin/ffmpeg.exe'
video = ep / 'outputs/production-v5/changneung_full_v5r2.mp4'

def extract(seconds):
    target = out / f'{seconds}.png'
    subprocess.run([ffmpeg, '-v', 'error', '-y', '-ss', str(seconds), '-i', str(video), '-frames:v', '1', str(target)], check=True)
    return {'requested_seconds': seconds, 'file': str(target)}

with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    results = list(pool.map(extract, [125, 305, 410, 735]))
(out / 'manifest.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(results, ensure_ascii=False))
