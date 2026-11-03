from pathlib import Path
import subprocess,os,json,datetime
H=Path(__file__).resolve().parent
prompt='''사용자가 Claude 모션 코드를 요청했다. 도구없이 React+Remotion4 TSX 코드만 출력, fence금지. 100줄/6500자 이하, 설명없음. 1920x1080 투명 content, x80~1840 y190~820 내. 기본색 ink#173348 blue#286cda green#4f8970 크림#f6f4ef Pretendard. 카메라줌/반복점멸/CSSanimation금지. frame prop 기준 18~30프레임 한번만진입후유지. interpolate import remotion 양끝clamp. 데이터하드코딩금지.
다음6함수를export. 모든props 타입명시. FocusOverlay({x,y,width,height,frame,active=true,label}) SVG대상사각형+라벨강조, RouteReveal({d,frame,color,label,x,y}) SVG경로strokeDasharray/pathLength=1 30f에그리기, CommuteComparison({frame,active='all',rows}) rows:{label:string,values:number[]}[] 열S1/S4/S5 표, PriceComparison({frame,rows,active}) rows:{label:string,value:number,note?:string}[] 3가격막대, CalendarReveal({frame,events,startYear=2027,endYear=2032,active}) events:{label:string,year:number,month?:number,kind?:'move'|'school'|'rail',status?:string}[] 가로연도축 3레인충돌최소화,월미정은year범위bar로표현, DecisionHighlight({frame,active,rows}) rows:{label:string,reason:string}[] 3후보짧은강조. active:string label일치또는all. frame:number. 제목/자막/출처는부모가추가하므로생략. 글자26이상,숫자34,조건20, 안전영역여백유지. JSX스타일절대좌표. 외부이미지/좌표/팩트생성금지. React/remotion만의존. 코드만짧게완결.'''
(H/'compact_prompt.txt').write_text(prompt,encoding='utf8')
env=os.environ.copy()
for k in list(env):
 if k.startswith(('ANTHROPIC_','CLAUDE_CODE_USE_')):env.pop(k,None)
env['CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC']='1'
cmd=['C:/Users/e2ken/.local/bin/claude.exe','-p','--effort','low','--output-format','json','--tools','','--strict-mcp-config','--mcp-config','{"mcpServers":{}}','--no-session-persistence','--disable-slash-commands','--setting-sources','','--settings','{"disableAllHooks":true}']
receipt={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'first_request':'timed_out_300s_no_result','scope':'compact 100-line motion code','tools_enabled':False}
try:
 with (H/'compact_result.json').open('w',encoding='utf8') as out,(H/'compact_stderr.log').open('w',encoding='utf8') as err:
  p=subprocess.run(cmd,input=prompt,encoding='utf8',stdout=out,stderr=err,cwd=H,env=env,timeout=180)
 receipt['exit_code']=p.returncode
 if p.returncode==0:
  d=json.loads((H/'compact_result.json').read_text(encoding='utf8'));code=d.get('result','').strip()
  if code.startswith('```'):code='\n'.join(code.splitlines()[1:-1])
  (H/'MotionKit.tsx').write_text(code,encoding='utf8');receipt.update(is_error=d.get('is_error'),usage=d.get('usage'),reported_estimated_cost_usd=d.get('total_cost_usd'),billing_note='estimate not verified extra charge',code_chars=len(code))
except subprocess.TimeoutExpired:receipt.update(exit_code=-1,error='timeout_180s')
(H/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in receipt.items() if k!='usage'},ensure_ascii=False))
