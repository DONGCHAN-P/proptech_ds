import json
import pathlib
import subprocess
import sys

version = sys.argv[1] if len(sys.argv) > 1 else 'v2'
root = pathlib.Path('video/out/channel-brand-' + version + '-qa')
root.mkdir(exist_ok=True)
ffmpeg = 'video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe'
ffprobe = ffmpeg.replace('ffmpeg.exe', 'ffprobe.exe')
results = {}
for kind, times in [('intro', [0.5, 2, 4.8]), ('outro', [2, 4.9667, 5, 9])]:
    video = 'video/out/channel-' + kind + '-' + version + '.mp4'
    results[kind] = json.loads(subprocess.check_output([
        ffprobe, '-v', 'error', '-show_entries',
        'format=duration:stream=codec_type,width,height,r_frame_rate', '-of', 'json', video
    ]))
    subprocess.run([ffmpeg, '-v', 'error', '-i', video, '-c:v', 'libx264', '-preset', 'ultrafast', '-c:a', 'aac', '-f', 'null', '-'], check=True)
    for time in times:
        subprocess.run([ffmpeg, '-y', '-ss', str(time), '-i', video, '-frames:v', '1',
                        str(root / (kind + str(time) + '.png'))], capture_output=True, check=True)
(root / 'technical.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
print(json.dumps(results))
