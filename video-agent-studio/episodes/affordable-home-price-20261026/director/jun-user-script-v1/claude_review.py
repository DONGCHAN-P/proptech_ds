"""Sanitized visual/script review through the user's logged-in Claude subscription.

No audio, keys, account data, individual transactions, repo tools or API-key path.
Preparation is default. --send makes exactly one bounded print-mode review.
"""
from pathlib import Path
import json,hashlib,subprocess,base64,tempfile,os,sys,re
OWN=Path(__file__).resolve().parent;EP=OWN.parents[1];ROOT=EP.parents[2]
PACKET=OWN/'claude-review-v1';PACKET.mkdir(exist_ok=True)
EDIT=EP/'editor/jun-user-script-v1/full-film-v1'
VIDEO=EP/'outputs/jun-user-script-v1/full-film-v1/affordable_price_jun_user_script_v2.mp4'
FF=ROOT/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
sch=load(EDIT/'schedule.json');manifest=load(EP/'narration/jun-user-script-v1/narration_manifest.json')
images=[]
for sid in ['S01','S16','S21','S24','S26','S31']:
    p=next(p for p in sch['placements'] if p['id']==sid);at=p['start']+p['scene']['duration_s']-.3
    dst=PACKET/(sid+'.png')
    if not dst.exists():
        r=subprocess.run([str(FF),'-v','error','-ss',str(at),'-i',str(VIDEO),'-frames:v','1','-update','1',str(dst)],capture_output=True);assert r.returncode==0,r.stderr.decode('utf-8','replace')[-1000:]
    images.append({'path':str(dst),'sha256':sha(dst),'basis':'actual_encoded_v2_frame','scene_id':sid,'time_s':at,'mime':'image/png'})
for p in sorted((EP/'qa/jun-user-script-v1/full-film-v1').glob('scenes_contact_*.jpg')):
    images.append({'path':str(p),'sha256':sha(p),'basis':'compiled_source_scene_contact_not_encoded_video','mime':'image/jpeg'})
facts=load(EP/'director/user-recording-v1/calculation_check.json')
text='''당신은 한국 부동산 데이터 설명 영상의 독립 검수자입니다. Claude Opus의 최대 추론으로 아래 원고·가상 계산과 화면을 검토하세요. 실제 청취나 연속 재생을 수행했다고 쓰지 마세요. 제공한 PNG6장은 실제 최종v2 MP4의 프레임이고, JPG는 소스 화면 모음입니다. 이 범위만 판단하세요.
사용자 기준: 쉽고 자연스럽게 설명, 의미 단위 자막, 금액·단위 보존, 글자 잘림 방지, 다른 주제에 같은 완성 차트/사진 반복 금지, 필요 주제 전환에 독립 이미지, 같은 주택은 같은 크기로 표시. 막대 비례와 핵심 인사이트를 확인합니다. 화면의 불필요한 'AI 개념 이미지'나 '~아님' 같은 부정형 푸터를 추가하지 마세요. 사용자가 작성한 원문의 말투와 순서를 보존합니다.
계산 조건: 현금1~5억, 각 준비금2000~6000만원, 가상 LTV70%, 개인 대출한도4억원, 연4.5%·30년 원리금균등. 4억원은 개인별 사례 조건입니다. 현재 법률을 새로 추정하지 마세요. 6.6억원 비용 예시는 일반적1주택·전용85㎡이하·감면없음·일반과세 중개사 조건입니다. 2.666.../5.666...억 한도에서2.66/5.66억으로 내려 정한 표시값을 씁니다.
이 영상은 집값 예산과 대출·월 생활비의 연결을 설명합니다. 수익·대출승인을 보장하지 않습니다. 가격 자체만 읽는 대신 추가 자기자금과 빚, 대출한도가 걸리는 지점, 월 부담 차이를 설명해야 합니다.
정량 검사 결과: 원문48문단·31장면·156자막·101발화앵커 정렬, 전체679.2초 MEDIUM ASR 숫자119개 일치. 실제 청취는 미실시. 714.8초 영상의 마지막 발화 뒤3.0067초에 기존10초 아웃트로를 시작합니다. 마지막 자막 종료는 수정했습니다.
필수 수정은 제공 자료에서 확인되는 계산/값/논리 오류·명백한 잘림·중요한 시청자 혼동만 제시하세요. 취향 제안은 recommended에 분리하세요. 화면 모음만으로 움직임·음성·전체 재생 합격을 주장하지 마세요.
JSON만 반환하세요: {"verdict":"pass 또는 revise","required":[{"scene_id":"...","problem":"...","evidence":"...","fix":"..."}],"recommended":[],"scope":{"actual_listening":false,"continuous_playback":false,"sampled_frames":true},"reason":"..."}.
'''
text+='\n원고(원문 보존):\n'+'\n\n'.join(f'{p["paragraph_id"]} {p["text"]}' for p in manifest['paragraphs'])
text+='\n검증된 계산:\n'+json.dumps(facts,ensure_ascii=False)
text+='\n이미지 순서/근거:\n'+json.dumps([{k:v for k,v in i.items() if k!='path'} for i in images],ensure_ascii=False)
save(PACKET/'review_materials.json',{'video':str(VIDEO),'video_sha256':sha(VIDEO),'source_doc_sha256':manifest['source_doc_sha256'],'text':text,'images':images,'excluded':['audio','API keys','account identifiers','individual transactions','environment files'],'authority_basis':['ongoing user instruction to discuss/review this affordable-price episode with Claude','current user-authored script film creation instruction; latest Jun budget approval affects voice only'],'paid_API_key_path':False,'tools_enabled':False})
print(json.dumps({'status':'sanitized_review_packet_prepared','images':len(images),'video_sha256':sha(VIDEO),'audio_included':False}),flush=True)
if '--send' not in sys.argv and '--diagnose' not in sys.argv:raise SystemExit(0)
env={k:v for k,v in os.environ.items() if not k.startswith('ANTHROPIC_') and k not in ['CLAUDE_CODE_USE_BEDROCK','CLAUDE_CODE_USE_VERTEX','CLAUDE_CODE_OAUTH_TOKEN']}
auth=subprocess.run(['C:/Users/e2ken/.local/bin/claude.exe','auth','status','--json'],capture_output=True,text=True,encoding='utf-8',env=env)
status=json.loads(auth.stdout);assert status.get('loggedIn') and status.get('authMethod')=='claude.ai' and not status.get('apiKeySource'),'Subscription auth required; no API fallback'
content=[{'type':'text','text':text}]
for i in images:content.append({'type':'image','source':{'type':'base64','media_type':i['mime'],'data':base64.b64encode(Path(i['path']).read_bytes()).decode()}})
message={'type':'user','session_id':'','parent_tool_use_id':None,'message':{'role':'user','content':content}}
args=['C:/Users/e2ken/.local/bin/claude.exe','--print','--model','opus','--effort','max','--max-turns','1','--tools','','--strict-mcp-config','--mcp-config','{"mcpServers":{}}','--setting-sources','','--no-session-persistence','--input-format','stream-json','--output-format','stream-json','--verbose']
with tempfile.TemporaryDirectory(prefix='realestate-claude-review-') as cwd:
    payload=b'' if '--diagnose' in sys.argv else (json.dumps(message,ensure_ascii=False)+'\n').encode()
    r=subprocess.run(args,input=payload,capture_output=True,cwd=cwd,env=env,timeout=600)
if '--diagnose' in sys.argv:
    error=re.sub(r'[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}','[EMAIL]',r.stderr.decode('utf-8','replace'),flags=re.I)
    error=re.sub(r'sk-ant-\S+','[REDACTED]',error)
    print(json.dumps({'diagnostic':'empty user input, no review submitted','exit':r.returncode,'nested_marker':'CLAUDECODE' in env,'error':error[:2000]},ensure_ascii=False))
    raise SystemExit(0)
try:
    events=[json.loads(line) for line in r.stdout.decode('utf-8-sig').splitlines() if line.strip().startswith('{')]
    result=next(x for x in reversed(events) if x.get('type')=='result')
except Exception:
    save(PACKET/'call_receipt.json',{'status':'non_json_response_no_retry','exit_code':r.returncode,'subscription_auth':True,'model_requested':'opus','effort_requested':'max','stderr_type':'not_saved_to_avoid_account_identifiers','API_key_used':False});print('Claude review returned no JSON; no retry/fallback.');raise SystemExit(r.returncode or 1)
safe={k:result.get(k) for k in ['type','subtype','is_error','result','num_turns','modelUsage','usage']}
save(PACKET/'response.json',safe)
save(PACKET/'call_receipt.json',{'status':'response_received','exit_code':r.returncode,'subscription_auth_method':'claude.ai','model_requested':'opus','effort_requested':'max','API_key_used':False,'tools_enabled':False,'session_persistence':False,'voice_uploaded':False,'input_material_sha256':sha(PACKET/'review_materials.json'),'video_sha256':sha(VIDEO),'single_print_invocation':True,'automatic_fallback':False,'new_payment_or_topup_calls':0})
print(json.dumps({'status':'response_received','exit_code':r.returncode,'is_error':result.get('is_error'),'review':result.get('result')},ensure_ascii=False))
