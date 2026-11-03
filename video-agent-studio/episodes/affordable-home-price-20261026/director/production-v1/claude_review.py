"""Review an immutable, approved-scope packet with the logged-in Claude CLI."""
import argparse
import base64
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from claude_transport import parse_result
from financial_review_context import build_packet, script_prompt, revision_prompt

ROOT=Path(__file__).resolve().parents[5]
EP=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser()
parser.add_argument('--script',required=True)
parser.add_argument('--round',required=True)
parser.add_argument('--image',action='append',default=[])
parser.add_argument('--image-list')
parser.add_argument('--media-report')
parser.add_argument('--previous-review')
parser.add_argument('--previous-media-receipt')
args=parser.parse_args()
if args.image_list:
    listing=(ROOT/args.image_list).resolve()
    assert listing.is_relative_to(EP) and listing.suffix.lower()=='.json'
    values=json.loads(listing.read_text(encoding='utf-8'))
    assert isinstance(values,list) and all(isinstance(v,str) for v in values)
    args.image.extend(values)
script_path=(ROOT/args.script).resolve()
assert script_path.is_relative_to(EP)
out=EP/'director/production-v1/claude'/args.round
out.mkdir(parents=True,exist_ok=True)
assert not (out/'receipt.json').exists(), 'Use a new round; retain review receipts.'
script=script_path.read_text(encoding='utf-8')
sha=hashlib.sha256(script_path.read_bytes()).hexdigest()
artifact_sha=sha
media_binding={}
packet=build_packet(script,sha,EP)
if args.media_report:
    report=(ROOT/args.media_report).resolve()
    assert report.is_relative_to(EP)
    packet['media_report']=json.loads(report.read_text(encoding='utf-8'))
    media=packet['media_report']
    video=(ROOT/media['video']).resolve()
    subtitles=(ROOT/media['subtitles']).resolve()
    assert video.is_relative_to(EP) and subtitles.is_relative_to(EP)
    digest=hashlib.sha256()
    with video.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):
            digest.update(block)
    assert digest.hexdigest()==media['video_sha256']
    assert hashlib.sha256(subtitles.read_bytes()).hexdigest()==media['subtitles_sha256']
    artifact_sha=media['video_sha256']
    media_binding={'video_sha256':artifact_sha,'subtitles_sha256':media['subtitles_sha256'],
                   'media_report_sha256':hashlib.sha256(report.read_bytes()).hexdigest()}
    for field in ('metadata','description','thumbnail'):
        file=(ROOT/media[field]).resolve()
        assert file.is_relative_to(EP) and file.is_file()
        expected=media[field+'_sha256']
        assert hashlib.sha256(file.read_bytes()).hexdigest()==expected
        media_binding[field+'_sha256']=expected
    packet['media_binding']=media_binding
    packet['media_status']='첨부된 실제 인코딩 표본 프레임과 검수 보고서에 한해 미디어 검토. 미제공 재생/청취를 했다고 쓰지 않음.'
(out/'packet.json').write_text(json.dumps(packet,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
prompt=script_prompt(packet)
if args.previous_review:
    previous_path=(ROOT/args.previous_review).resolve()
    assert previous_path.is_relative_to(EP)
    previous=json.loads(previous_path.read_text(encoding='utf-8'))
    packet['previous_review']=previous
    packet['revision_changes']=json.loads((script_path.parent/'changes.json').read_text(encoding='utf-8'))
    (out/'packet.json').write_text(json.dumps(packet,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    prompt=revision_prompt(packet)
if args.media_report:
    locked=json.loads((EP/'director/production-v1/locked_script.json').read_text(encoding='utf-8'))
    assert locked['script_sha256']==sha
    accepted_receipt=(ROOT/locked['claude_receipt']).resolve()
    assert accepted_receipt.is_relative_to(EP)
    packet['previous_script_review']=json.loads(accepted_receipt.with_name('review.json').read_text(encoding='utf-8'))
    assert packet['previous_script_review']['artifact_sha256']==sha and packet['previous_script_review']['approved']
    packet['approved_content_reference']={
        'script_sha256':sha,'basis_sha256':packet['basis_sha256'],
        'claude_script_receipt':locked['claude_receipt'],
        'claude_script_receipt_sha256':hashlib.sha256(accepted_receipt.read_bytes()).hexdigest(),
        'scope':'Unchanged exact script and policy/case content were already reviewed; current task is rendered media and packaging evidence.'}
    for unchanged in ('verified_policy_and_cases','current_primary_catalog','independent_primary_delta_QA'):
        packet.pop(unchanged,None)
    (out/'packet.json').write_text(json.dumps(packet,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    prompt='''이미 양측 내용 검수를 통과한 잠긴 대본의 최종 미디어 증거 검수입니다. 기존 금융모형·수치·대본 승인은 변경되지 않았으므로 전면 재계산하지 마세요.
첨부된 실제 인코딩 표본 프레임과 기술·자막·로컬ASR 검수 기록을 읽고 글자잘림, 잘못된 수치, 음성과 화면의 연결, 반복, 출처/권리 누락, 프레임/타이밍 문제의 필수 수정이 남았는지 검토하세요. 썸네일과 설명도 제공 범위에서 검사하세요.
실제 동영상 연속재생이나 직접 청취는 제공되지 않습니다. 이 제한을 정직하게 coverage_notes에 기록하고, 하지 않은 관찰을 주장하지 마세요. 프레임/기술/ASR 증거와 대본 검토로 판정 가능한 범위에서 승인합니다. ASR 차이는 오인식과 확정 발음오류를 구분하세요.
필수 이슈가 있으면 정확한 시각·장면·근거와 최소 수정안을 required_issues에 기록하세요. 필수 이슈가 없으면 approved true, required_issues []로 하세요. artifact_sha256는 이번 완성 MP4의 media_binding.video_sha256와 정확히 같아야 합니다.
최종 출력은 간결하게: 권고 최대2개, coverage_notes 최대6개. 청취/연속재생 미확인 범위를 숨기거나 '완벽'이라고 표현하지 마세요.
'''+json.dumps(packet,ensure_ascii=False,indent=2)
    if args.previous_media_receipt:
        prior_path=(ROOT/args.previous_media_receipt).resolve()
        assert prior_path.is_relative_to(EP) and prior_path.is_file()
        prior=json.loads(prior_path.read_text(encoding='utf-8'))
        prior_review=json.loads(prior_path.with_name('review.json').read_text(encoding='utf-8'))
        assert prior['approved'] and prior_review['approved'] and not prior_review['required_issues']
        assert prior['video_sha256']==prior_review['artifact_sha256']
        assert prior['script_sha256']==sha and prior['video_sha256']!=artifact_sha
        packet['prior_media_approval']={'receipt':{k:v for k,v in prior.items() if k not in ['images','model_usage']},
            'receipt_file_sha256':hashlib.sha256(prior_path.read_bytes()).hexdigest(),'review':prior_review}
        (out/'packet.json').write_text(json.dumps(packet,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        prompt='''기존 승인 영상의 자막 분할 수정본에 대한 변경분 검수입니다. 이전 승인과 현재 실제 인코딩 프레임·변경 기록·새 MP4 및 SRT 해시를 제공합니다.
이번 변경은 동일 음성·대본·수치·장면·총길이를 유지하며 고립된 서술어 자막을 의미 단위로 재분할하고 두 줄 표시를 적용한 것입니다. 기존 자료의 전면 재검산은 하지 마세요.
첨부된 새 자막 프레임에서 의미 단위, 숫자와 단위 보존, 두 줄 글자잘림과 영역 침범, 읽을 수 있는 길이·시점, 장면과 자막 연결을 집중 검토하세요. 전체 큐 보존·타이밍·경계 검수 기록도 확인하세요.
변경되지 않은 영역의 이전 승인은 그 제공 범위 안에서만 재사용합니다. 이전 승인에도 실제 청취·연속재생은 포함되지 않았고 이번에도 제공되지 않습니다. 현재 MP4의 해시를 exact artifact_sha256로 출력하고, 현재 제공 범위에 필수 문제가 남으면 승인하지 마세요.
권고 최대2개, coverage_notes 최대5개. 필수 문제가 없으면 approved true와 required_issues []로 판정하세요.
'''+json.dumps(packet,ensure_ascii=False,indent=2)
schema={'type':'object','properties':{
    'artifact_sha256':{'type':'string'},'approved':{'type':'boolean'},
    'required_issues':{'type':'array','items':{'type':'object','properties':{
        'id':{'type':'string'},'section':{'type':'string'},'reason':{'type':'string'},'replacement':{'type':'string'}},
        'required':['id','section','reason','replacement']}},
    'recommended':{'type':'array','items':{'type':'string'}},
    'coverage_notes':{'type':'array','items':{'type':'string'}}},
    'required':['artifact_sha256','approved','required_issues','recommended','coverage_notes']}
env=os.environ.copy()
for key in list(env):
    if key.startswith('ANTHROPIC_') or key.startswith('CLAUDE_CODE_USE_') or key=='CLAUDE_CODE_OAUTH_TOKEN':
        env.pop(key,None)
env.update(CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC='1',DISABLE_TELEMETRY='1',DISABLE_ERROR_REPORTING='1')
cmd=[str(Path.home()/'.local/bin/claude.exe'),'-p','--model','opus','--effort','max',
     '--output-format','json','--json-schema',json.dumps(schema),'--tools','',
     '--permission-mode','dontAsk','--disable-slash-commands','--no-chrome',
     '--strict-mcp-config','--mcp-config','{"mcpServers":{}}','--setting-sources','',
     '--settings','{"disableAllHooks":true}','--no-session-persistence']
stdin=prompt
images=[]
if args.image:
    content=[{'type':'text','text':prompt}]
    for value in args.image:
        path=(ROOT/value).resolve()
        assert path.is_relative_to(EP) and path.suffix.lower()=='.png'
        if args.media_report:
            expected=next(r['sha256'] for r in packet['media_report']['image_manifest'] if r['path']==path.relative_to(ROOT).as_posix())
            assert hashlib.sha256(path.read_bytes()).hexdigest()==expected
        content.append({'type':'image','source':{'type':'base64','media_type':'image/png',
                                                'data':base64.b64encode(path.read_bytes()).decode('ascii')}})
        images.append({'path':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    cmd[cmd.index('--output-format')+1]='stream-json'
    cmd+=['--input-format','stream-json','--verbose']
    stdin=json.dumps({'type':'user','message':{'role':'user','content':content}},ensure_ascii=False)+'\n'
t0=time.monotonic()
proc=subprocess.run(cmd,input=stdin,encoding='utf-8',errors='replace',capture_output=True,
                    cwd=out,env=env,timeout=1200)
(out/('response.stream.jsonl' if args.image else 'response.raw.json')).write_text(proc.stdout,encoding='utf-8')
(out/'stderr.txt').write_text(proc.stderr,encoding='utf-8')
try:
    response=parse_result(proc.stdout)
except ValueError:
    response={}
(out/'response.json').write_text(json.dumps(response,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
review=response.get('structured_output')
if review is None and response.get('result','').lstrip().startswith('{'):
    review=json.loads(response['result'])
receipt={'at_utc':datetime.now(timezone.utc).isoformat(),'exit_code':proc.returncode,
    'elapsed_seconds':round(time.monotonic()-t0,2),'script_sha256':sha,'model_requested':'opus','effort_requested':'max',
    'model_usage':response.get('modelUsage',{}),'cli_cost_estimate_usd':response.get('total_cost_usd'),
    'authentication':'existing_subscription_login; API-key env removed; no paid-provider fallback',
    'is_error':response.get('is_error'),'subtype':response.get('subtype'),
    'images':images,'tools':[],'approved':False,'review_scope':packet['media_status']}
receipt.update(media_binding)
if review:
    assert review['artifact_sha256']==artifact_sha, 'Review did not echo the exact input digest.'
    receipt['approved']=bool(review['approved'] and not review['required_issues'] and proc.returncode==0 and not response.get('is_error'))
    (out/'review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(out/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in receipt.items() if k not in ['images','model_usage']}|{'image_count':len(images),'models':list(receipt['model_usage'])},ensure_ascii=False,indent=2))
if not review or proc.returncode or response.get('is_error'):
    raise SystemExit('Claude review failed; no approval or model/provider fallback applied.')
