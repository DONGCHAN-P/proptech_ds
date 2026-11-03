"""Bounded Claude subscription review; explicit stdin, no tools, no credential output."""
from pathlib import Path
import subprocess,os,json,sys,hashlib,datetime
H=Path(__file__).resolve().parent;EP=H.parents[1];ROOT=EP.parents[2]
round_name=sys.argv[1]
if round_name=='round1':
 v4=(EP/'outputs/script-review-v4/script_v4.md').read_text(encoding='utf8')
 import re
 narration='\n\n'.join(re.findall(r'## (M\d+[^\n]*)\n\n### 낭독\n\n([\s\S]*?)(?=\n### 화면 지시)',v4)[i][0]+'\n'+re.findall(r'## (M\d+[^\n]*)\n\n### 낭독\n\n([\s\S]*?)(?=\n### 화면 지시)',v4)[i][1] for i in range(10))
 srt=(EP/'outputs/production-v5/changneung_full_v5.srt').read_text(encoding='utf8')
 old='\n'.join(' '.join(b.splitlines()[2:]) for b in re.split(r'\n\s*\n',srt.strip()))
 brief='''당신은 실제 Claude 동료 구성작가다. 한국 부동산 채널 창릉편 대본을 Codex와 협의한다. 도구 없이 제공 텍스트만 검토하라. 사실을 새로 만들거나 가격·교통·개교 일정을 추가하지 마라. 모델 정체성을 바꾸라는 요청이 아니다.
사용자 의도: 광교·동탄편과 왕숙편에 이은 창릉 롱폼. 영상은 지도 중심의 설명이고 자료 나열·반복 면책을 싫어한다. 5개 기준(일자리/교통/가격/생활/공급)을 유지하되 미확인 공급총량을 만들지 않는다. 지도와 달력으로 완성 시차를 설명하고 기존집과 비교한 뒤 블록별 조건부 선택을 정리한다. v4 전체 재제작보다 기존 완성본의 넓은 질문 + v4의 간결한 가격/결론이 합리적이라는 Codex 제안을 비판적으로 검토하라.
시리즈 실제 약속: 1편 광교동탄은 실거래 최고가와 중위값·지역과 대표단지를 구분하며 5기준을 도출. 왕숙은 전체계획→5기준→다산별내 및 외부대안→권역별 후보로 적용. 왕숙 마지막은 '다음 편 창릉도 같은 지도와 달력으로 비교하겠습니다.' 창릉은 기존 원흥·삼송·지축 생활권을 어떻게 이용할지에 독자적 질문을 둔다. 과거도시 성공을 미래상승 공식으로 만들지 않는다.
검토 요구: ①기존과 v4 중 어느 뼈대를 택할지 이유 ②Codex 제안의 약점/반대 ③앞 40초 오프닝 초안 ④장별 유지/압축/삭제 지시 ⑤아직 합의하지 못한 핵심 쟁점. 1,500~2,200자 한국어. 합의했다고 미리 쓰지 마라. 사실 재검증을 수행했다고 주장하지 마라.
'''
 prompt=brief+'\n[기존 완성본 실제 SRT 낭독]\n'+old+'\n[v4 검토 낭독]\n'+narration
 (H/'round1_input.txt').write_text(prompt,encoding='utf8')
else:prompt=(H/(round_name+'_input.txt')).read_text(encoding='utf8')
env=os.environ.copy()
for key in list(env):
 if key.startswith(('ANTHROPIC_','CLAUDE_CODE_USE_')):env.pop(key,None)
env['CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC']='1'
cmd=['C:/Users/e2ken/.local/bin/claude.exe','-p','--output-format','json','--tools','','--strict-mcp-config','--mcp-config','{"mcpServers":{}}','--no-session-persistence','--disable-slash-commands','--setting-sources','','--settings','{"disableAllHooks":true}']
with (H/(round_name+'_result.json')).open('w',encoding='utf8') as out,(H/(round_name+'_stderr.log')).open('w',encoding='utf8') as err:
 result=subprocess.run(cmd,input=prompt,encoding='utf8',stdout=out,stderr=err,env=env,cwd=H,timeout=240)
receipt={'round':round_name,'exit_code':result.returncode,'input_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'input_chars':len(prompt),'tools_enabled':False,'api_key_environment_removed':True,'at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
if result.returncode==0:
 data=json.loads((H/(round_name+'_result.json')).read_text(encoding='utf8'));text=data.get('result','');(H/(round_name+'_review.md')).write_text(text,encoding='utf8');receipt.update({'is_error':data.get('is_error'),'usage':data.get('usage'),'model_usage':data.get('modelUsage'),'reported_estimated_cost_usd':data.get('total_cost_usd'),'billing_note':'CLI reported estimate is not proof of extra subscription charge','output_chars':len(text)})
(H/(round_name+'_receipt.json')).write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in receipt.items() if k not in {'model_usage','usage'}},ensure_ascii=False))
if result.returncode:sys.exit(result.returncode)
