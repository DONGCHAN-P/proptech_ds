from pathlib import Path
import os,subprocess,json,hashlib,datetime
HERE=Path(__file__).resolve().parent
prompt='''한국 부동산 해설영상 시청자 QA를 한국어로 수행하세요. 실제 MP4에서 추출한 아래 이미지들을 Read로 열어 비교하세요. 다른 파일은 읽지 마세요. G=교산 검토본, C=최종 창릉 기준본. 전체 연속재생/음성청취는 하지 않았음을 명시하세요.
사용자 요구: 가격/향후수요 중심, 학교는 보조; 합니다체; 실제지도/계획도/원문/가격지도로 의미설명; 상세도엔한개 locator와범위표시; 자료출처는자막아래; 숫자영문자막 의미단위; 지속흰자막 브랜드예외; 독립챕터AI배경 재사용; 텍스트카드만반복금지; 빠른줌/1프레임전환금지; 내용에맞는강조모션; 예정/현재구분; CTA뒤3초outro.
검토이미지:
'''+ '\n'.join(str(HERE/f) for f in ['G_sheet_1.jpg','G_sheet_2.jpg','G_sheet_3.jpg','G_sheet_4.jpg','C_sheet_1.jpg','C_sheet_2.jpg'])+'''
중점: 교산각구간 시청자의메시지이해/기준창릉과차이/필수수정3~6개/권장3개. 이미지만으로좌표·가격의사실오류단정하지마세요. 근거시간코드제시. 수정안은 기존대본/무료음성/기존실제지도재사용, 유료이미지추가금지. 주거36,669호 공원녹지34.0% 자족8.8% 낭독하는데M001수치가화면누락돼보임; 우측과도한여백; 생활A2에서한글자줄바꿈; 공급동일지도연표반복 확인요망. 최대1000한국어단어. 새사실발명금지. 프레임검토만으로연속영상완료주장금지.'''
env=os.environ.copy()
for key in list(env):
 if key.startswith(('ANTHROPIC_','CLAUDE_CODE_USE_')):env.pop(key,None)
env['CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC']='1'
cmd=['C:/Users/e2ken/.local/bin/claude.exe','-p','--effort','low','--output-format','json','--tools','Read','--allowedTools',f'Read({HERE.as_posix()}/**)',
     '--strict-mcp-config','--mcp-config','{"mcpServers":{}}','--no-session-persistence','--disable-slash-commands','--setting-sources','','--settings','{"disableAllHooks":true}','--max-turns','9']
with (HERE/'claude_result.json').open('w',encoding='utf8') as out,(HERE/'claude_stderr.log').open('w',encoding='utf8') as err:
 result=subprocess.run(cmd,input=prompt,encoding='utf8',env=env,stdout=out,stderr=err,cwd=HERE,timeout=300)
receipt={'exit_code':result.returncode,'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'scope':'sampled encoded frames only; no audio listening; no paid generation','tools':'Read only'}
if result.returncode==0:
 data=json.loads((HERE/'claude_result.json').read_text(encoding='utf8'));(HERE/'claude_review.md').write_text(data.get('result',''),encoding='utf8');receipt.update(is_error=data.get('is_error'),usage=data.get('usage'),cli_cost_estimate=data.get('total_cost_usd'))
(HERE/'claude_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in receipt.items() if k!='usage'}))
