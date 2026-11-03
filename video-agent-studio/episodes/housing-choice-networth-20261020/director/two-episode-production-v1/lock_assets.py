import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[5]
HERE=Path(__file__).parent
source=ROOT/'video-agent-studio/episodes/regional-price-recovery-20261022/outputs/literature-visual-v1/reused_assets.json'
items=json.loads(source.read_text(encoding='utf-8'))['assets'][:3]
locked=[]
for item in items:
    p=(ROOT/item['actual_file']).resolve()
    assert p.is_relative_to(ROOT) and p.is_file()
    sha=hashlib.sha256(p.read_bytes()).hexdigest()
    assert sha==item['sha256'], item['asset_id']
    locked.append(dict(asset_id=item['asset_id'],path=p.relative_to(ROOT).as_posix(),sha256=sha,
                       license=item.get('license','existing approved clean channel brand asset'),
                       new_generation=False))
result={'revision':'housing-private-media-assets-v1','assets':locked,
        'ffmpeg':'video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe',
        'ffprobe':'video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe',
        'new_paid_calls':0,'music_credit_required':True,
        'housing_stability_image':'video-agent-studio/episodes/housing-choice-networth-20261020/visual/private-production-v1/housing-stability-v1.json'}
(HERE/'media_assets.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'verified_assets':len(locked),'new_paid_calls':0,'output':'media_assets.json'}))
