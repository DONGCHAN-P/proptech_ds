import csv, hashlib, json, subprocess, sys
from pathlib import Path
import numpy as np

video = Path(sys.argv[1])
out = Path(__file__).parent / sys.argv[2]
out.mkdir(exist_ok=True)
ffmpeg = 'C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin/ffmpeg.exe'
# Caption, title, footer excluded. Map-only downsample; metrics are evidence,
# not a semantic cut detector. Every candidate must be visually classified.
cmd = [ffmpeg, '-v', 'error', '-i', str(video), '-vf',
       'crop=1760:650:80:190,scale=352:130,format=gray', '-f', 'rawvideo', '-']
p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
size = 352 * 130
rows = []
previous = None
n = 0
while True:
    raw = p.stdout.read(size)
    if not raw:
        break
    assert len(raw) == size
    current = np.frombuffer(raw, dtype=np.uint8).astype(np.int16)
    if previous is not None:
        delta = np.abs(current - previous)
        rows.append((n, float(delta.mean()), float((delta > 12).mean())))
    previous = current
    n += 1
err = p.stderr.read().decode(errors='replace')
assert p.wait() == 0, err
with (out / 'map_roi_all_frame_deltas.csv').open('w', newline='') as f:
    w = csv.writer(f); w.writerow(['frame','mean_abs_delta','fraction_delta_gt12']); w.writerows(rows)
candidates = [r[0] for r in rows if r[1] > 4 or r[2] > .12]
motion = [r[0] for r in rows if r[1] > .3 and r[2] > .005]
report = {'sha256':hashlib.sha256(video.read_bytes()).hexdigest(),
          'decoded_frames':n,'map_roi_xywh':[80,190,1760,650],
          'all_frame_metrics':'map_roi_all_frame_deltas.csv',
          'cut_candidate_frames':candidates,'motion_candidate_frames':motion,
          'threshold_note':'Candidates require visual classification; not an automatic quality verdict.',
          'actual_listening':False,'continuous_playback':False}
(out / 'motion_audit.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps({'frames':n,'cut_candidates':len(candidates),'motion_candidates':len(motion)}))
