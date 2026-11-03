"""Send only the explicitly authorized twelve-image Shorts packet to logged-in Claude."""
import base64,hashlib,json,os,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
HERE=Path(__file__).resolve().parent;EP=HERE.parents[1];ROOT=EP.parents[2]
sys.path.insert(0,str(HERE));from claude_transport import parse_result
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
folder=HERE/'shorts_media_input_v2';packet=read(folder/'report.json');listing=read(folder/'image_paths.json')
auth=read(HERE/'shorts_claude_payload_authorization.json')
assert auth['authorized'] is True and auth['report_sha256']==sha(folder/'report.json') and auth['image_list_sha256']==sha(folder/'image_paths.json')
assert len(listing)==12
for item in packet['items']:
    assert sha(ROOT/item['video'])==item['video_sha256'] and sha(ROOT/item['subtitles'])==item['subtitles_sha256']
prompt='''독립 한국어 부동산 영상 검수자입니다. 확정 본편의 기존 Jun 음성 문장을 재배치한 두 세로 쇼츠의 최종 미디어 증거를 검토하세요.
각 영상에 실제 인코딩 장면모음2장·긴자막2장·전환 전후2장을 제공하며 전체 SRT·실측 타이밍·신호·조건을 제공합니다. 대본은 확정 본편의 완전한 문장을 원속도로 발췌했고 새 음성생성은0입니다.
입력에 있는 사실만 사용하세요. 핵심은 동일조건 비교가정을 유지하면서 집값 가정에 따른 순위변화와 초기/월투자금·대출의 차이를 설명하는 것입니다. 연2%를 실제 시장평균/미래예측으로 읽게 하지 마세요. 평가 순자산과 매각현금, 첫해 집평가이익/자기자금5%와 비용후최종수익을 구분합니다. 원금상환은 남은대출을 줄이며 비용으로 중복차감하지 않습니다.
화면·숫자·의미단위자막·읽기속도·현재발화강조·조건·논리·반복·전환에서 실제 미해결 필수를 잡으세요. 불필요한 부정형 면책이나 AI제작배지를 요구하지 마세요. 샘플과 SRT가 제공된 범위를 넘어 연속재생·직접청취를 했다고 쓰지 마세요. 소형글자 OCR 혼동은 source 문자열과 비교해 의심과 확정오류를 구분합니다.
각 id와 video_sha256를 정확히 echo하고 필수0일때만 approvedtrue. 권고는 두편합쳐최대3개. 내부 코드·TTS·외부도구 실행 없이 이 입력만 검토합니다. 최종응답은 짧은 JSON. metadata/description 본문·음성파일은 제공하지 않습니다.
'''+json.dumps(packet,ensure_ascii=False,indent=2)
schema={'type':'object','properties':{'shorts':{'type':'array','items':{'type':'object','properties':{'id':{'type':'string'},'video_sha256':{'type':'string'},'approved':{'type':'boolean'},'required_issues':{'type':'array','items':{'type':'string'}},'recommended':{'type':'array','items':{'type':'string'}},'coverage_notes':{'type':'array','items':{'type':'string'}}},'required':['id','video_sha256','approved','required_issues','recommended','coverage_notes']}}},'required':['shorts']}
content=[{'type':'text','text':prompt}]
for value in listing:
    path=(ROOT/value).resolve();assert path.is_relative_to(EP) and path.suffix=='.png'
    manifest=next(x for x in packet['image_manifest'] if x['path']==value);assert sha(path)==manifest['sha256']
    content.append({'type':'image','source':{'type':'base64','media_type':'image/png','data':base64.b64encode(path.read_bytes()).decode('ascii')}})
env=os.environ.copy()
for key in list(env):
    if key.startswith('ANTHROPIC_') or key.startswith('CLAUDE_CODE_USE_') or key=='CLAUDE_CODE_OAUTH_TOKEN':env.pop(key,None)
env.update(CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC='1',DISABLE_TELEMETRY='1',DISABLE_ERROR_REPORTING='1')
out=HERE/'claude/shorts-final-v2';out.mkdir(parents=True,exist_ok=True);assert not (out/'receipt.json').exists()
cmd=[str(Path.home()/'.local/bin/claude.exe'),'-p','--model','opus','--effort','max','--input-format','stream-json','--output-format','stream-json','--verbose','--json-schema',json.dumps(schema),'--tools','','--permission-mode','dontAsk','--disable-slash-commands','--no-chrome','--strict-mcp-config','--mcp-config','{"mcpServers":{}}','--setting-sources','','--settings','{"disableAllHooks":true}','--no-session-persistence']
stdin=json.dumps({'type':'user','message':{'role':'user','content':content}},ensure_ascii=False)+'\n'
t=time.monotonic();p=subprocess.run(cmd,input=stdin,capture_output=True,text=True,encoding='utf8',errors='replace',cwd=out,env=env,timeout=1200)
(out/'response.stream.jsonl').write_text(p.stdout,encoding='utf8');(out/'stderr.log').write_text(p.stderr,encoding='utf8')
response=parse_result(p.stdout);review=response.get('structured_output')
if review is None and response.get('result','').lstrip().startswith('{'):review=json.loads(response['result'])
receipt={'approved':False,'exit_code':p.returncode,'is_error':response.get('is_error'),'authentication':'existing subscription login; API-key env removed; no API-provider fallback','model_requested':'opus','effort_requested':'max','elapsed_s':time.monotonic()-t,'report_sha256':sha(folder/'report.json'),'image_list_sha256':sha(folder/'image_paths.json'),'image_count':12,'items':[],'actual_listening':False,'continuous_playback':False,'at_utc':datetime.now(timezone.utc).isoformat()}
if review:
    assert {r['id'] for r in review['shorts']}=={'funnel','analysis'}
    for r in review['shorts']:
        item=next(x for x in packet['items'] if x['id']==r['id']);assert r['video_sha256']==item['video_sha256']
        receipt['items'].append({'id':r['id'],'video_sha256':r['video_sha256'],'subtitles_sha256':item['subtitles_sha256'],'approved':bool(r['approved'] and not r['required_issues'])})
    receipt['approved']=all(r['approved'] for r in receipt['items']) and p.returncode==0 and not response.get('is_error')
    (out/'review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(out/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(receipt,ensure_ascii=False))
if not review or p.returncode or response.get('is_error'):raise SystemExit('Claude review failed; no approval inferred.')
