from pathlib import Path
import subprocess,os,json,base64,datetime,hashlib
H=Path(__file__).resolve().parent
context=(H/'context.txt').read_text(encoding='utf8')
e=json.loads((H/'evidence.json').read_text(encoding='utf8'))
task='''사용자가 Claude와 Codex가 실제 현재 영상을 시청자 관점으로 검토하고 개선점을 말해달라고 요청했다. 아래는 최종MP4 실제시간 프레임과 실제자막/타이밍이다. 이미지들을 직접 보며 독립 비평하라. 이는 연속동영상/음성입력이 아니므로 실제 청취·전편 연속시청했다고 주장하지 말라. 나는 이미 코드를 만들었다는 이유로 좋은점에편향되지말라.
출력 한국어1500~2300자: 1)시청자관점한문장총평 2)우선순위5~7개,각각 정확한시간범위/관찰증거/이해·몰입영향/수정안/확신수준. 정지화면으로확인한것과편집통계추론을구분. 기술적으로정상이어도재미/이해측면문제비판. 3)대본·유료음성없이바로바꿀3가지와대본합의필요사항 4)좋은점2개 및Codex가반박할수있는판단1개. 과장된이탈률/조회보장,실제안들린효과음평가,새가격/통근/계획팩트생성금지. 고정지도에서대상/레이어/자료역할을바꾸는방법권장,카메라줌/급전환금지. 10분이상유지,무료음성15:34를최종Jun길이로단정금지. 각시간은제공된초단위를분초로정확변환.'''
content=[{'type':'text','text':task+'\n'+context}]
for row in e['frames']:
 p=H/row['image'];t=row['time_s']
 content.extend([{'type':'text','text':f'실제MP4 {t//60:02d}:{t%60:02d} ({t}초)'},{'type':'image','source':{'type':'base64','media_type':'image/jpeg','data':base64.b64encode(p.read_bytes()).decode()}}])
p=H/'mobile_readability.jpg';content.extend([{'type':'text','text':'아래는 512px 너비 축소 비교. 실제 휴대폰 앱 실행 화면은 아님.'},{'type':'image','source':{'type':'base64','media_type':'image/jpeg','data':base64.b64encode(p.read_bytes()).decode()}}])
payload=json.dumps({'type':'user','message':{'role':'user','content':content}},ensure_ascii=False)+'\n'
(H/'claude_task.txt').write_text(task,encoding='utf8')
env=os.environ.copy()
for k in list(env):
 if k.startswith(('ANTHROPIC_','CLAUDE_CODE_USE_')):env.pop(k,None)
env['CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC']='1'
cmd=['C:/Users/e2ken/.local/bin/claude.exe','-p','--effort','low','--input-format','stream-json','--output-format','stream-json','--verbose','--tools','','--strict-mcp-config','--mcp-config','{"mcpServers":{}}','--no-session-persistence','--disable-slash-commands','--setting-sources','','--settings','{"disableAllHooks":true}']
receipt={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'image_count':15,'actual_mp4_sha256':e['sha256'],'input_mode':'actual image blocks + timestamped subtitles and timeline','continuous_playback':False,'actual_listening':False,'tools_enabled':False}
try:
 with (H/'claude_events.jsonl').open('w',encoding='utf8') as out,(H/'claude_stderr.log').open('w',encoding='utf8') as err:
  p=subprocess.run(cmd,input=payload,encoding='utf8',stdout=out,stderr=err,cwd=H,env=env,timeout=180)
 receipt['exit_code']=p.returncode
 if p.returncode==0:
  events=[json.loads(line) for line in (H/'claude_events.jsonl').read_text(encoding='utf8').splitlines() if line.strip()]
  d=next(x for x in reversed(events) if x.get('type')=='result');(H/'claude_result.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8');result=d.get('result','');(H/'claude_review.md').write_text(result,encoding='utf8');receipt.update(is_error=d.get('is_error'),usage=d.get('usage'),reported_estimated_cost_usd=d.get('total_cost_usd'),billing_note='API equivalent estimate, not verified extra charge',output_chars=len(result))
except subprocess.TimeoutExpired:receipt.update(exit_code=-1,error='timeout_180s_no_automatic_retry')
(H/'claude_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in receipt.items() if k!='usage'},ensure_ascii=False))
