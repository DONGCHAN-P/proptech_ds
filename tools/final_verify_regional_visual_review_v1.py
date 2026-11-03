"""Fresh local handoff verification, read-only; UTF-8 file avoids shell pipe loss."""
from pathlib import Path
import hashlib,json,os,zipfile
ROOT=Path(__file__).resolve().parents[1]
EP=ROOT/'video-agent-studio/episodes/regional-price-recovery-20261022'
DEST=EP/'director/production-v1/delivery'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb')as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()
m=read(DEST/'delivery_manifest.json');archive=read(DEST/'archive_manifest.json')
assert all(sha(ROOT/p)==meta['sha256']for p,meta in m['files'].items())
assert sha(ROOT/m['video']['path'])==m['video']['sha256']
assert sha(ROOT/archive['path'])==archive['sha256']
with zipfile.ZipFile(ROOT/archive['path'])as z:assert z.testzip()is None
assert os.path.samefile(ROOT/'영상/지역별가격회복/검토영상.mp4',ROOT/m['video']['path'])
assert os.path.samefile(ROOT/'영상/지역별가격회복/검토자막_임시.srt',ROOT/m['subtitle'])
s=read(EP/'state.json');assert s['budget_status']=='voice_generation_deferred_by_user'and not s['timing_locked']
assert read(ROOT/'output/video_decisions/decisions/5fe307eed02c.json')['resolution']=='deferred_by_user'
assert not(EP/'narration/production-v1/authorization.json').exists()
assert sha(ROOT/'config/current_video.json')=='2cfbd606ce61a3b547e7a441c0f15d5270b1e7837c6ed4363dba813382ebfa4c'
receipt=ROOT/'output/telegram_deliveries/regional_full_visual_review_v1_parts.json'
t=read(receipt)if receipt.exists()else{}
if t.get('ok'):
    split=read(DEST/'telegram_parts_v1/manifest.json')
    expected=[archive]+split['parts']
    assert t['master_sha256']==m['video']['sha256']
    assert len(t['items'])==len(expected)==5
    assert all(item['ok']and item['message_id']and item['sha256']==meta['sha256']for item,meta in zip(t['items'],expected))
    assert split['all_video_frames_preserved']and split['video_frames']==25671
print(json.dumps({'local_delivery_integrity':'pass','archive_integrity':'pass','hardlinks_verified':2,
    'required_open':m['required_open'],'voice_generation':'deferred','published_baseline':'unchanged',
    'telegram_status':t.get('status'),'telegram_ok':t.get('ok')},ensure_ascii=False))
