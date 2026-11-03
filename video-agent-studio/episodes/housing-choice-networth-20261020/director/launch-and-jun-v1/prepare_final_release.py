"""Bind a private upload job to actual, exact-version Codex and Claude approvals."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[5]
EP=Path(__file__).resolve().parents[2]
HERE=Path(__file__).parent
CHANNEL='UCr_mTC0x_Uobv6MrIsOkrXw'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def sha(path):
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):
            digest.update(block)
    return digest.hexdigest()
def local(value):
    p=(ROOT/value).resolve()
    assert p.is_relative_to(EP) and p.is_file(),f'Missing episode artifact: {value}'
    return p
def relative(path):
    return path.relative_to(ROOT).as_posix()
def save(path,data):
    assert not path.exists(),f'Preserve existing release record; use a new release directory: {path}'
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--video',required=True)
parser.add_argument('--subtitles',required=True)
parser.add_argument('--codex-review',required=True)
parser.add_argument('--claude-receipt',required=True)
parser.add_argument('--release-dir',default='outputs/jun-release-v1')
parser.add_argument('--revision',default='jun-v1')
args=parser.parse_args()
out=(EP/args.release_dir).resolve()
assert out.is_relative_to(EP) and out.is_dir()
assert not (out/'upload_job.json').exists() and not (out/'upload_receipt.json').exists()
video=local(args.video);subtitles=local(args.subtitles)
video_sha=sha(video);subtitle_sha=sha(subtitles)
lock=read(HERE/'locked_script.json')
assert sha(local(lock['script_path']))==lock['script_sha256']
codex_path=local(args.codex_review);codex=read(codex_path)
assert codex['approved'] is True and codex['video_sha256']==video_sha
assert codex['subtitles_sha256']==subtitle_sha and codex['script_sha256']==lock['script_sha256']
assert codex['required_issues']==[] and codex.get('critical_issues',[])==[]
assert codex['burned_in_captions_verified'] is True
claude_path=local(args.claude_receipt);claude=read(claude_path)
claude_review=read(claude_path.with_name('review.json'))
assert claude['approved'] is True and claude['video_sha256']==video_sha
assert claude['subtitles_sha256']==subtitle_sha and claude['script_sha256']==lock['script_sha256']
assert not claude['is_error'] and claude['exit_code']==0
assert claude_review['approved'] and claude_review['artifact_sha256']==video_sha and not claude_review['required_issues']
authorization_path=HERE/'authorization.json'
authorization=read(authorization_path)
assert authorization['youtube_upload_authorized'] and authorization['youtube_visibility']=='private'
assert authorization['paid_voice_generation_authorized'] is True
assert authorization['included_credit_cap']==10739 and authorization['additional_cash_usd_cap']==0
ledger=read(EP/'narration/jun-production-v1/generation_ledger.json')
assert ledger['status']=='all54_generated_measured_alignment_validated_not_listened' and ledger['actual_credits']<=authorization['included_credit_cap']
assert len(ledger['requests'])==54 and all(row['status']=='complete' and row['charge_known'] for row in ledger['requests'])
assert ledger['reserved_pending_credits']==0
technical=read(EP/'narration/jun-production-v1/technical_validation.json')
assert technical['status']=='passed_technical_only_not_listened' and technical['final_timing_sha256']==sha(EP/'narration/jun-production-v1/final_timing.json')
assert ledger['topup_calls']==0 and ledger['overage_calls']==0 and ledger['automatic_retries']==0
metadata=read(out/'metadata_measured.json')
assert metadata['visibility']=='private' and not metadata.get('scheduled') and not metadata.get('published')
description_path=(out/metadata['description']).resolve()
assert description_path.is_relative_to(out) and description_path.is_file()
description=description_path.read_text(encoding='utf-8')
thumbnail=out/'thumbnail.png'
for field,file in [('metadata',out/'metadata_measured.json'),('description',description_path),('thumbnail',thumbnail)]:
    assert codex[field+'_sha256']==claude[field+'_sha256']==sha(file)
assert len(description.encode('utf-8'))<=5000 and thumbnail.stat().st_size<2*1024*1024
assert 0<len(metadata['title'])<=100
now=datetime.now(timezone.utc).isoformat()
dual={'video_sha256':video_sha,'subtitles_sha256':subtitle_sha,'script_sha256':lock['script_sha256'],
    'required_open':[],'critical_open':[],
    'codex':{'approved':True,'video_sha256':video_sha,'receipt':relative(codex_path),'receipt_sha256':sha(codex_path)},
    'claude':{'approved':True,'video_sha256':video_sha,'receipt':relative(claude_path),'receipt_sha256':sha(claude_path)},
    'coverage':codex.get('coverage',{}),'approval_scope':'Actual evidence supplied and checked; unchecked listening/playback remains recorded.',
    'at_utc':now}
save(out/'dual_media_review.json',dual)
qa={'checked_revision':video_sha,'status':'passed_with_limits','required_unresolved':[],'critical_open':[],
    'independent_codex_receipt':relative(codex_path),'independent_claude_receipt':relative(claude_path),
    'coverage':codex.get('coverage',{}),'at_utc':now}
save(out/'release_validation.json',qa)
job={'episode_root':relative(EP),'channel_id':CHANNEL,'privacy':'private',
    'video':relative(video),'sha256':video_sha,'subtitles':relative(subtitles),'subtitles_sha256':subtitle_sha,
    'title':metadata['title'],'description':description,'tags':metadata['tags'],
    'thumbnail':relative(thumbnail),'thumbnail_sha256':sha(thumbnail),
    'qa':relative(out/'release_validation.json'),'dual_review':relative(out/'dual_media_review.json'),
    'approval_file':relative(out/'pre_upload_decision.json'),'authorization':relative(authorization_path),
    'burned_in_captions_verified':True}
save(out/'upload_job.json',job)
basis='Current direct user instruction authorizes private upload after both reviews pass. Exact-version evidence satisfies this condition; no later human viewing is asserted.'
save(out/'completed_decision.json',{'id':f'housing-choice-{args.revision}-completed','gate':'completed','status':'approved',
    'video_sha256':video_sha,'approval_basis':basis,'dual_review':relative(out/'dual_media_review.json'),'at_utc':now})
save(out/'pre_upload_decision.json',{'id':f'housing-choice-{args.revision}-private-pre-upload','gate':'pre_upload','status':'approved',
    'video_sha256':video_sha,'job_sha256':sha(out/'upload_job.json'),'channel_id':CHANNEL,'privacy':'private',
    'completed_decision_file':relative(out/'completed_decision.json'),
    'current_direct_user_authorization':relative(authorization_path),'new_paid_generation_authorized':False,
    'approval_basis':basis,'at_utc':now})
print(json.dumps({'job':relative(out/'upload_job.json'),'privacy':'private','sha256':video_sha,'uploaded':False}))
