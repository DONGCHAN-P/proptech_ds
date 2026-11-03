from pathlib import Path
import subprocess,json,os,hashlib,datetime,sys
H=Path(__file__).resolve().parent;EP=H.parent
prompt=(H/'claude_input.txt').read_text(encoding='utf8')
env=os.environ.copy()
for k in list(env):
 if k.startswith(('ANTHROPIC_','CLAUDE_CODE_USE_')):env.pop(k,None)
env['CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC']='1'
cmd=['C:/Users/e2ken/.local/bin/claude.exe','-p','--effort','low','--output-format','json','--tools','','--strict-mcp-config','--mcp-config','{"mcpServers":{}}','--no-session-persistence','--disable-slash-commands','--setting-sources','','--settings','{"disableAllHooks":true}']
with (H/'claude_result.json').open('w',encoding='utf8') as out,(H/'claude_stderr.log').open('w',encoding='utf8') as err:
 p=subprocess.run(cmd,input=prompt,encoding='utf8',stdout=out,stderr=err,env=env,cwd=H,timeout=240)
receipt=dict(exit_code=p.returncode,input_sha256=hashlib.sha256(prompt.encode()).hexdigest(),tools_enabled=False,api_key_environment_removed=True,at=datetime.datetime.now(datetime.timezone.utc).isoformat())
if p.returncode==0:
 d=json.loads((H/'claude_result.json').read_text(encoding='utf8'));(H/'claude_review.md').write_text(d.get('result',''),encoding='utf8');receipt.update(is_error=d.get('is_error'),usage=d.get('usage'),reported_cost_estimate=d.get('total_cost_usd'),billing_note='CLI estimate is not evidence of an added API charge')
(H/'claude_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in receipt.items() if k!='usage'}));sys.exit(p.returncode)
