from pathlib import Path
import subprocess,os,json,datetime
H=Path(__file__).resolve().parent/'claude'
task=(H/'recovery_prompt.txt').read_text(encoding='utf-8')
payload=json.dumps({'type':'user','message':{'role':'user','content':[{'type':'text','text':task}]}},ensure_ascii=False)+'\n'
env=os.environ.copy()
for k in list(env):
 if k.startswith(('ANTHROPIC_','CLAUDE_CODE_USE_')):env.pop(k,None)
env['CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC']='1'
cmd=['C:/Users/e2ken/.local/bin/claude.exe','-p','--effort','low','--input-format','stream-json','--output-format','stream-json','--verbose','--tools','','--strict-mcp-config','--mcp-config','{"mcpServers":{}}','--no-session-persistence','--disable-slash-commands','--setting-sources','','--settings','{"disableAllHooks":true}']
receipt={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'image_count':0,'input_mode':'short source-grounded text design/code, stream-json','authorization':'root explicit one recovery after initial180s timeout','execution_permission':'use_default; exact network restriction not diagnosed','continuous_playback':False,'actual_listening':False,'tools_enabled':False}
try:
 with (H/'recovery_events.jsonl').open('w',encoding='utf8') as out,(H/'recovery_stderr.log').open('w',encoding='utf8') as err:
  p=subprocess.run(cmd,input=payload,encoding='utf8',stdout=out,stderr=err,cwd=H,env=env,timeout=180)
 receipt['exit_code']=p.returncode
 if p.returncode==0:
  events=[json.loads(line) for line in (H/'recovery_events.jsonl').read_text(encoding='utf8').splitlines() if line.strip()]
  d=next(x for x in reversed(events) if x.get('type')=='result');(H/'recovery_result.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8');result=d.get('result','');(H/'recovery_response.md').write_text(result,encoding='utf8');receipt.update(is_error=d.get('is_error'),usage=d.get('usage'),reported_estimated_cost_usd=d.get('total_cost_usd'),billing_note='API equivalent estimate, not verified extra charge',output_chars=len(result))
except subprocess.TimeoutExpired:receipt.update(exit_code=-1,error='timeout_180s_no_automatic_retry')
(H/'recovery_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in receipt.items() if k!='usage'},ensure_ascii=False))
