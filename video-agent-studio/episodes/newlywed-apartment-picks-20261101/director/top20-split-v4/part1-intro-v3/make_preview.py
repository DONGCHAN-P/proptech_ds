"""End the user-facing preview after a complete introductory region sentence."""
from pathlib import Path
import math, json, subprocess, sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from jobs import D, E, FF, sha, probe, read, save, run

t = read(D/'locked_timing.json')
a = read(D/'assembly_v2.json')
video = Path(a['video'])
assert sha(video) == a['video_sha256']
first, second = t['body_scenes'][0]['sentences'][:2]
end = math.ceil((first['end_s'] + .45)*30)/30
assert end < second['start_s']-.15
out = video.parent/'intro_preview_v1.mp4'
assert not out.exists()
fade = .25
run([FF, '-v', 'error', '-y', '-i', video, '-t', f'{end:.9f}',
     '-vf', f'fade=t=out:st={end-fade:.9f}:d={fade}',
     '-af', f'afade=t=out:st={end-fade:.9f}:d={fade}',
     '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p',
     '-c:a', 'aac', '-b:a', '256k', '-movflags', '+faststart', out], D/'evidence/v2/preview.log')
p = probe(out)
assert abs(float(p['format']['duration'])-end) < .04
run([FF, '-v', 'error', '-xerror', '-i', out, '-f', 'null', '-'], D/'evidence/v2/preview_decode.log')
receipt = {'status': 'passed', 'preview': str(out), 'preview_sha256': sha(out),
           'source_video_sha256': a['video_sha256'], 'duration_s': end,
           'last_sentence_end_s': first['end_s'], 'next_sentence_start_s': second['start_s'],
           'fade_start_s': end-fade, 'fade_duration_s': fade,
           'complete_sentence_before_end': True, 'strict_decode_passed': True,
           'actual_listening': False, 'continuous_playback': False}
save(D/'preview_v1.json', receipt)
print(json.dumps(receipt, ensure_ascii=False))
