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
out=EP/'director/two-episode-production-v1/claude'/args.round
out.mkdir(parents=True,exist_ok=True)
assert not (out/'receipt.json').exists(), 'Use a new round; retain review receipts.'
script=script_path.read_text(encoding='utf-8')
sha=hashlib.sha256(script_path.read_bytes()).hexdigest()
artifact_sha=sha
media_binding={}
facts=json.loads((EP/'outputs/growth-explanation-v1/facts.json').read_text(encoding='utf-8'))
packet={'script_revision_sha256':sha,'script':script,'verified_aggregate':{
    k:facts[k] for k in ('data_cutoff','regional','sensitivity','constant_model_inputs','leverage_example')},
    'scope':'자체 설명 모형. 비용600/100/100만원 및 월30/5만원은 비용항목 묶음의 설명용 가정. 실거래연결집계는 단지·면적별각분기2건,연결30단지기준이며표본교체됨. 최근10년서울연결단지43~1976개; 경기10년CAGR2/3/5건기준6.59/7.39/8.78%. 강화문턱서울장기경로단절. 과거숫자로미래예측·공식시장평균을주장하지않음.',
    'user_direction':'기존영상최대보존. 상황별매매/전세/월세선택. 집값2%보수적인계획조건·투자원화총수익6%가정. 감당가능대출매매의레버리지·주거안정성은화자관점. 다음편감당가능매매가격. 사진/차트반복금지,글자잘림금지,불필요한~아님/AI개념배지제거,의미자막,숫자발음검수.',
    'authority':'사용자2026-10-26직접지시:Claude검수및무료TTS후YouTube비공개업로드. 개인거래/자격증명전달금지.',
    'media_status':'대본 검수 단계. 실제 음성·완성 영상의 승인과 구분.'}
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
prompt='''독립적인 한국어 부동산 데이터 영상 검수자입니다. 첨부 입력만으로 정확성·설명·제작가이드를 검토하세요.
승인을 목표로 흠을 숨기지 말고, 중대한 수치·표본·범위·논리·주거비/부채·계산·시청자가 오해할 표현을 required_issues로 제시하세요. 각 required는 정확한 장과 근거, 짧은 교체문이 필요합니다.
표본 기준과 민감도를 짧은 긍정형 문장으로 전달하면 충분하며 '공식지수 아님' 등 경고화면 반복을 요구하지 마세요. 미래집값상승보장/6%넘으면임차무조건승리/2%는실증평균 같은 단정은 잡으세요.
비용 묶음의 설명용 가정과 실제 항목별 견적을 구분하고, 현행 대출규정을 설명한 영상으로 확대하지 마세요. 사용자 자신의 조건부 매매 관점과 모형의 순자산 순위를 구분하세요.
권고는 상위3개까지만. 반복 자료나 클리핑은 실제 이미지가 있을 때 확인한 범위만 말하고, 첨부되지 않은 영상 재생이나 음성 청취를 했다고 주장하지 마세요.
approved는 이 입력 버전과 현재 검수 범위에서 필수 이슈가 0개일 때만 true로 하세요. artifact_sha256는 script_revision_sha256와 같아야 합니다.
'''+json.dumps(packet,ensure_ascii=False,indent=2)
if args.previous_review:
    previous_path=(ROOT/args.previous_review).resolve()
    assert previous_path.is_relative_to(EP)
    previous=json.loads(previous_path.read_text(encoding='utf-8'))
    packet['previous_review']=previous
    packet['revision_changes']=json.loads((script_path.parent/'changes.json').read_text(encoding='utf-8'))
    (out/'packet.json').write_text(json.dumps(packet,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    prompt='''이전 독립 검수에 대한 변경분 재검수입니다. 이전 판정과 정확한 수정목록을 함께 제공합니다.
revision_changes에 기록된 변경문과 인접 문맥에 집중해 이전 필수 문제 또는 발음·용어 명료성이 해결됐는지, 새로운 모순이 생겼는지 검사하세요.
이전 검수에서 이미 독립 재계산한 상환·민감도·지역CAGR 숫자는 변경되지 않았으므로 다시 전면 재계산하거나 재검증하지 마세요. 해당 변경분과 인접문맥, 새로운 모순 발생 여부만 검사하세요. 기존 무변경 부분의 검수는 이전 판정 범위로 유지합니다.
수정으로 필수 문제가 해결되고 새 필수 문제가 없으면 approved true와 required_issues []로 정확한 현재 artifact_sha256를 승인하세요. 해결되지 않았으면 정확한 필수 교체문을 쓰세요. 새로운 시장 수치·규정·상품·법정 비용을 추정해 추가하지 마세요.
최종 출력은 짧게: 권고 최대1개, coverage_notes 최대4개. 이 단계는 대본 검수이며 실제 영상·음성 승인으로 확대하지 않습니다.
'''+json.dumps(packet,ensure_ascii=False,indent=2)
if args.media_report:
    locked=json.loads((EP/'director/two-episode-production-v1/locked_script.json').read_text(encoding='utf-8'))
    assert locked['script_sha256']==sha
    accepted_receipt=(ROOT/locked['claude_receipt']).resolve()
    assert accepted_receipt.is_relative_to(EP)
    packet['previous_script_review']=json.loads(accepted_receipt.with_name('review.json').read_text(encoding='utf-8'))
    assert packet['previous_script_review']['artifact_sha256']==sha and packet['previous_script_review']['approved']
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
