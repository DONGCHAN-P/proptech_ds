"""Verify the delivered draft, links, Claude receipt and Telegram archive."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import os
import zipfile

ROOT=Path(__file__).resolve().parents[1]
EP=ROOT/'video-agent-studio/episodes/regional-price-recovery-20261022'
OUT=EP/'outputs/script-review-v2'

def read(p):
    return json.loads(p.read_text(encoding='utf8'))

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def write(p,obj):
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

checks=read(OUT/'package_checks.json')
for rel,meta in checks['files'].items():
    assert sha(ROOT/rel)==meta['sha256'],rel
script_sha=sha(OUT/'script_v2.md')
qa=read(EP/'qa/script-v2/claude_recheck.json')
assert qa['current_script_sha256']==script_sha and qa['required_open_issue_count']==0
claude=read(OUT/'collaboration/claude_execution_receipt.json')
assert claude['exit_code']==0 and not claude['is_error'] and claude['requested_effort']=='max'
assert claude['actual_model_usage']['claude-opus-4-8']['outputTokens']>0
cfg=read(ROOT/'config/video_shelf.json')
entry=next(x for x in cfg['entries'] if x['name']=='지역별가격회복')
links=[]
for name,rel in entry['files'].items():
    alias=ROOT/'영상/지역별가격회복'/name
    assert os.path.samefile(alias,ROOT/rel),name
    links.append(name)
receipt_path=ROOT/'output/telegram_deliveries/regional_script_v2.json'
delivery=read(receipt_path)
archive=OUT/'지역별_영상대본_v2.zip'
assert delivery['ok'] and delivery['private_recipient_verified'] and delivery['message_id']>0
assert delivery['sha256']==sha(archive) and delivery['script_sha256']==script_sha
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    assert z.read('지역별_영상대본_v2.md')==(OUT/'script_v2.md').read_bytes()
    assert z.read('클로드_편집검토.md')==(OUT/'claude_editorial_review_v2.md').read_bytes()
    archive_count=len(z.namelist())
assert (EP/'writer/script_v1.md').is_file()
assert (OUT/'script_v2_codex_before_qa.md').is_file()
assert (OUT/'script_v2_after_qa_before_claude.md').is_file()
final={'checked_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'status':'verified_draft_delivered_not_user_approved','script_sha256':script_sha,'scene_count':checks['scene_count'],'paragraph_count':checks['narration_paragraphs'],'required_script_issues_open':0,'samefile_aliases':links,'zip_entries':archive_count,'telegram_message_id':delivery['message_id'],'claude_model':'claude-opus-4-8','claude_effort_argument':'max','source_files_preserved':True,'official_index_release_crosscheck':'pending','actual_audio_listening':False,'continuous_video_playback':False,'rendered_video':False}
write(OUT/'delivery_verification.json',final)
state=read(EP/'state.json')
state.update(stage='script_v2_delivered_for_review',telegram_delivery_receipt=receipt_path.relative_to(ROOT).as_posix(),delivery_verification=(OUT/'delivery_verification.json').relative_to(ROOT).as_posix())
write(EP/'state.json',state)
pre=read(EP/'episode_preflight_v2.json')
pre['release']['telegram_notice_receipt']=receipt_path.relative_to(ROOT).as_posix()
write(EP/'episode_preflight_v2.json',pre)
print(json.dumps(final,ensure_ascii=False,indent=2))
