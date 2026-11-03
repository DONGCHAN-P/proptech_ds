"""Bounded subscription-authenticated Claude discussion, explicit packet only."""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
EXE=Path('C:/Users/e2ken/.local/bin/claude.exe')
ap=argparse.ArgumentParser();ap.add_argument('packet');ap.add_argument('name');args=ap.parse_args()
packet=Path(args.packet).resolve();prompt=packet.read_text(encoding='utf-8')
env=os.environ.copy()
for key in ['ANTHROPIC_API_KEY','ANTHROPIC_AUTH_TOKEN','ANTHROPIC_BASE_URL','CLAUDE_CODE_USE_BEDROCK','CLAUDE_CODE_USE_VERTEX','CLAUDE_CODE_USE_FOUNDRY']:
 env.pop(key,None)
status=subprocess.run([str(EXE),'auth','status','--json'],capture_output=True,encoding='utf-8',env=env,cwd=HERE,timeout=30)
auth=json.loads(status.stdout)
assert auth.get('loggedIn') and auth.get('authMethod')=='claude.ai','Subscription login required; no API fallback'
cmd=[str(EXE),'-p','--model','opus','--effort','max','--tools','','--disable-slash-commands','--setting-sources','','--strict-mcp-config','--mcp-config','{"mcpServers":{}}','--settings','{"disableAllHooks":true}','--no-session-persistence','--no-chrome','--output-format','json','--system-prompt','You are a critical Korean data-video editorial collaborator. Only use the explicit user packet; no tools, no hidden files, no account data. Reply in Korean.']
result=subprocess.run(cmd,input=prompt,capture_output=True,encoding='utf-8',env=env,cwd=HERE,timeout=240)
receipt={'packet_file':str(packet),'packet_sha256':hashlib.sha256(packet.read_bytes()).hexdigest(),'packet_characters':len(prompt),'auth_method':'claude.ai','subscription_type':auth.get('subscriptionType'),'requested_model':'opus','effort':'max','tools_enabled':False,'exit_code':result.returncode,'new_paid_api_fallback':False}
(HERE/(args.name+'_receipt.json')).write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
try:
 response=json.loads(result.stdout); (HERE/(args.name+'_response.json')).write_text(json.dumps(response,ensure_ascii=False,indent=2),encoding='utf-8');text=response.get('result','');(HERE/(args.name+'_response.md')).write_text(text,encoding='utf-8');print(json.dumps({'receipt':receipt,'is_error':response.get('is_error'),'response':text[:12500]},ensure_ascii=False))
except ValueError:
 (HERE/(args.name+'_error.txt')).write_text(result.stderr[:3000],encoding='utf-8'); print(json.dumps({'receipt':receipt,'error':'Claude returned no JSON response','stderr':result.stderr[:500]},ensure_ascii=False))
