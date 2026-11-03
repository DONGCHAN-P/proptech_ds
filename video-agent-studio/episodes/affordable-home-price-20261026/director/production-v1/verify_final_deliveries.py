"""Read-only final verification of both requested private deliveries."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[5]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
rows=[]
for name,folder in [('housing-choice-networth-20261020','outputs/private-release-v3'),
                    ('affordable-home-price-20261026','outputs/private-release-v2')]:
    ep=ROOT/'video-agent-studio/episodes'/name
    out=ep/folder
    completion=read(out/'completion.json')
    receipt=read(out/'upload_receipt.json')
    job=read(out/'upload_job.json')
    dual=read(out/'dual_media_review.json')
    assert completion['status']=='private_uploaded_processed_with_Korean_captions'
    assert receipt['private_verified'] and receipt['caption_serving_verified'] and receipt['caption_status']=='serving'
    assert receipt['verification']['status']['privacyStatus']=='private'
    assert not receipt['verification']['status'].get('publishAt')
    assert receipt['verification']['processingDetails']['processingStatus']=='succeeded'
    assert sha(ROOT/job['video'])==job['sha256']==completion['video_sha256']
    assert sha(ROOT/job['subtitles'])==job['subtitles_sha256']
    assert dual['required_open']==dual['critical_open']==[]
    assert all(dual[k]['approved'] for k in ['codex','claude'])
    assert read(ep/'state.json')['stage']=='private_uploaded_verified'
    rows.append({'episode':name,'url':completion['url'],'private':True,'processing':'succeeded',
        'Korean_captions':'serving','both_reviews':'approved','seconds':completion['film_seconds']})
assert read(ROOT/'config/current_video.json')['version']=='gyosan-v5-jun'
assert read(ROOT/'config/video_production_queue_20261026.json')['status']=='both_private_uploads_verified'
print(json.dumps({'verified':rows,'public_baseline_unchanged':True},ensure_ascii=False))
