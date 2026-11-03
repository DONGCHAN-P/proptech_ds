const fs=require('fs'),path=require('path'),cp=require('child_process'),crypto=require('crypto');
const dir=__dirname;
const prompt='한국어 비평입니다. 단순 요약 금지. 허용 packet.json의 revised_script와 key_questions만 검토하고 각 질문에 동의/수정필요/판단불가 및 이유를 답하세요. 1차 Claude가 비평 대신 요약하고 독립QA 미수행이라는 낡은 내용을 반복했습니다. 이를 교정하세요. 핵심 오류 없으면 없다고 하되 시장임대료 적합성/세금/대출가능성 미검증의 제한적 합의인지 밝히세요. 원금/보증금/기회비용/환율중복과 편향을 실제로 비판하세요. 700단어 이내, 다른파일/검색금지. 파일: '+path.join(dir,'packet.json');
fs.writeFileSync(path.join(dir,'input.txt'),prompt);
const env={...process.env};for(const k of Object.keys(env))if(/^(ANTHROPIC_|CLAUDE_CODE_USE_)/.test(k))delete env[k];env.CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC='1';
const args=['-p','--effort','low','--output-format','json','--tools','Read','--allowedTools','Read('+dir.replaceAll('\\','/')+'/packet.json)','--strict-mcp-config','--mcp-config','{"mcpServers":{}}','--no-session-persistence','--disable-slash-commands','--setting-sources','','--settings','{"disableAllHooks":true}','--max-turns','5'];
const r=cp.spawnSync('C:/Users/e2ken/.local/bin/claude.exe',args,{input:prompt,encoding:'utf8',env,cwd:dir,timeout:240000,maxBuffer:2000000});
fs.writeFileSync(path.join(dir,'stdout.json'),r.stdout||'');fs.writeFileSync(path.join(dir,'stderr.log'),r.stderr||'');
let result;try{result=JSON.parse(r.stdout);}catch{}
if(result?.result)fs.writeFileSync(path.join(dir,'review.md'),result.result);
const receipt={at:new Date().toISOString(),exit_status:r.status,signal:r.signal,error:r.error?.message,scope:'Anonymized method only; subscription CLI; no API keys; Read packet only; no sheet access',input_sha256:crypto.createHash('sha256').update(prompt).digest('hex'),is_error:result?.is_error,cli_cost_estimate:result?.total_cost_usd};
fs.writeFileSync(path.join(dir,'receipt.json'),JSON.stringify(receipt,null,2));console.log(JSON.stringify(receipt));
