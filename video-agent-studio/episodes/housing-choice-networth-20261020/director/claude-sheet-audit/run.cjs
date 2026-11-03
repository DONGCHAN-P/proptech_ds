const fs=require('fs'),path=require('path'),cp=require('child_process'),crypto=require('crypto');
const dir=__dirname;
const prompt='한국어로 주거 선택 순자산 비교 모형을 독립 감사하세요. 허용된 packet.json만 Read로 읽으세요. 사용자 실제 재산 정보는 없고 익명 구조입니다. 계산의 채택할 부분, 확정 오류와 조건부 의심의 구별, 이중계상 방지, 공정 비교 보완, 대본에서 피할 단정 5개를 최대 900단어로 제시하세요. 외부 검색이나 다른 파일 읽기 없이 제공 구조만 검토하세요. 전체 시트 검증을 했다고 주장하지 마세요. 파일: '+path.join(dir,'packet.json');
fs.writeFileSync(path.join(dir,'input.txt'),prompt);
const env={...process.env};for(const k of Object.keys(env))if(/^(ANTHROPIC_|CLAUDE_CODE_USE_)/.test(k))delete env[k];env.CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC='1';
const args=['-p','--effort','low','--output-format','json','--tools','Read','--allowedTools','Read('+dir.replaceAll('\\','/')+'/packet.json)','--strict-mcp-config','--mcp-config','{"mcpServers":{}}','--no-session-persistence','--disable-slash-commands','--setting-sources','','--settings','{"disableAllHooks":true}','--max-turns','5'];
const r=cp.spawnSync('C:/Users/e2ken/.local/bin/claude.exe',args,{input:prompt,encoding:'utf8',env,cwd:dir,timeout:240000,maxBuffer:2000000});
fs.writeFileSync(path.join(dir,'stdout.json'),r.stdout||'');fs.writeFileSync(path.join(dir,'stderr.log'),r.stderr||'');
let result;try{result=JSON.parse(r.stdout);}catch{}
if(result?.result)fs.writeFileSync(path.join(dir,'review.md'),result.result);
const receipt={at:new Date().toISOString(),exit_status:r.status,signal:r.signal,error:r.error?.message,scope:'Anonymized method only; subscription CLI; no API keys; Read packet only; no sheet access',input_sha256:crypto.createHash('sha256').update(prompt).digest('hex'),is_error:result?.is_error,cli_cost_estimate:result?.total_cost_usd};
fs.writeFileSync(path.join(dir,'receipt.json'),JSON.stringify(receipt,null,2));console.log(JSON.stringify(receipt));
