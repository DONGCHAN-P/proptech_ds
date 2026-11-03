from pathlib import Path
import subprocess,os,json,datetime,hashlib
H=Path(__file__).resolve().parent
prompt='''사용자가 실제 Claude에게 모션그래픽 코드를 요청했다. 당신은 React/Remotion4 모션 담당이다. 아래 계약의 단일 TSX 모듈을 작성하라. 도구/네트워크/파일 접근 없이 코드만 출력한다. markdown fence 없이 TypeScript만, 220줄 이내. 새 사실/이미지/지도좌표/노선 생성 금지.
출력 exports: FocusOverlay({x,y,width,height,frame,active=true,label}) 절대좌표 SVG/HTML 강조(최종 1회 부드러운 18프레임 진입,불투명도 최소0.65,반복점멸 금지), RouteReveal({d,frame,color,label,x,y}) SVGpath를 strokeDasharray/pathLength=1로 30프레임에 그리기, CommuteComparison({frame,active='all',rows}) 전체 화면 1920x1080 content영역 x80~1840 y190~820 내 지도와 결합가능한 투명 표(좌표/배경지도는부모), PriceComparison({frame,rows,active}) 3개 가격 비교 표시, CalendarReveal({frame,events,startYear=2027,endYear=2032,active}) 가로 날짜축, DecisionHighlight({frame,active,rows}) 후보3행. 각각 독립export 함수, 모든 props명시적 TypeScript type. 반환JSX는 래퍼내 content만, 채널쉘/자막/브랜드는부모. frame은부모에서주므로 useCurrentFrame없어도됨. 데이터는props에서만. props rows: Commute {label:string,values:number[]}[], Price {label:string,value:number,note?:string}[], Decision {label:string,reason:string}[]; active는 label일치 강조 아니면all. Calendar events:{label:string,year:number,month?:number,kind?:'move'|'school'|'rail',status?:string}[]; 같은 날짜 라벨끼리 충돌방지: event index별 y레인 최대3, 각label한줄최대22글자; text label은연도/월과한묶음. 미정월은임의1월X year만이면가로year범위표시. 2030.03과2030.??목표같은지점확정처럼그리면안됨.
톤: #f6f4ef 크림,ink#173348,blue#286cda,green#4f8970,muted#637580 Pretendard 700/400. 제목은부모,표글자최소26숫자34,작은조건20. 지나친카드PPT보다는자료위에서 현재 말하는항목을짧게강조. 기존영상이 고정지도,상세토지이용도+좌측locator,얇은연도축,지속흰하단자막인점준수. 카메라줌,스프링,흔들림,반복펄스,1초미만컷,CSSanimation/transition,Math.random,Date.now 금지. interpolate는import from remotion하고extrapolate양끝clamp. 컴포넌트가없어도타입체크가능React/remotion만의존.
실데이터 예시(코드기본값에 하드코딩말고설계참고): Commute 광화문[66,68,67],상암MBC[46,62,56],여의도[63,78,72],LG사이언스파크[72,80,68],강남[87,94,94]. 열헤더 S1/S4/S5. 숫자는현재교통길찾기예상,08:00부터도착. Price S5 7.76598억/S1 7.9038억/S4 8.73329억이지만 데이터는부모정확값을써야함. 작은source는부모가추가.
필요한 모든코드를1회완결제공,외부에보냈다고/테스트완료했다고주장하지말것.'''
(H/'prompt.txt').write_text(prompt,encoding='utf8')
env=os.environ.copy()
for k in list(env):
 if k.startswith(('ANTHROPIC_','CLAUDE_CODE_USE_')):env.pop(k,None)
env['CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC']='1'
cmd=['C:/Users/e2ken/.local/bin/claude.exe','-p','--output-format','json','--tools','','--strict-mcp-config','--mcp-config','{"mcpServers":{}}','--no-session-persistence','--disable-slash-commands','--setting-sources','','--settings','{"disableAllHooks":true}']
with (H/'result.json').open('w',encoding='utf8') as out,(H/'stderr.log').open('w',encoding='utf8') as err:
 p=subprocess.run(cmd,input=prompt,encoding='utf8',stdout=out,stderr=err,cwd=H,env=env,timeout=300)
receipt={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':p.returncode,'tools_enabled':False,'input_sha256':hashlib.sha256(prompt.encode()).hexdigest()}
if p.returncode==0:
 d=json.loads((H/'result.json').read_text(encoding='utf8'));code=d.get('result','').strip()
 if code.startswith('```'):code='\n'.join(code.splitlines()[1:-1])
 (H/'MotionKit.tsx').write_text(code,encoding='utf8')
 receipt.update(is_error=d.get('is_error'),usage=d.get('usage'),reported_estimated_cost_usd=d.get('total_cost_usd'),billing_note='CLI equivalent estimate, not verified extra charge',code_chars=len(code))
(H/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in receipt.items() if k!='usage'},ensure_ascii=False))
raise SystemExit(p.returncode)
