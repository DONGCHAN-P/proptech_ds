import { createServer } from 'node:http';
import type { IncomingMessage, ServerResponse } from 'node:http';
import { readFileSync } from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { RunStore } from './store.ts';
import { GameError, fail } from './core/engine.ts';

const PUBLIC=new URL('../public/',import.meta.url);
const errors:Record<string,string>={
  INSUFFICIENT_CASH:'현재 현금이 행동 비용과 매수 예약액보다 부족합니다. 주문을 줄이거나 다음 분기에 거래해 보세요.',
  INSUFFICIENT_HOLDINGS:'매도할 보유 수량이 부족합니다.',INVALID_LOT:'거래 단위와 수량을 확인해 주세요. 주식은 정수 주만 가능합니다.',
  JOB_REQUIREMENTS:'이미 취업했거나 직무능력이 30 미만입니다. 직무 공부를 먼저 예약해 보세요.',
  AP_EXCEEDED:'행동은 한 분기에 3개까지 가능합니다.',ACTION_LIMIT:'같은 행동은 분기당 2회까지 가능합니다.',
  NOT_LISTED:'현재 시점에는 등장하지 않은 자산입니다.',RESEARCH_REQUIRED:'거래 접근 시점과 데이터가 검증되지 않아 잠겨 있습니다.',
  CONFLICT_STATE_HASH:'다른 화면에서 진행한 기록이 있습니다. 새로 불러와 주세요.',WRONG_TURN:'이미 진행되었거나 다른 분기의 요청입니다. 새로 불러와 주세요.',
  IDEMPOTENCY_CONFLICT:'같은 요청 번호에 다른 계획을 보낼 수 없습니다. 현재 기록을 다시 확인해 주세요.',
};
function json(res:ServerResponse,status:number,body:unknown) {
  res.writeHead(status,{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','X-Content-Type-Options':'nosniff'});
  res.end(JSON.stringify(body,(_,v)=>typeof v==='bigint'?v.toString():v));
}
async function body(req:IncomingMessage) {
  if(!req.headers['content-type']?.startsWith('application/json')) fail('JSON_REQUIRED');
  let size=0;const chunks:Buffer[]=[];
  for await(const chunk of req) {size+=chunk.length;if(size>65536) fail('BODY_TOO_LARGE');chunks.push(chunk);}
  try {const parsed=JSON.parse(Buffer.concat(chunks).toString('utf8'));if(!parsed||Array.isArray(parsed)||typeof parsed!=='object') fail('INVALID_JSON');return parsed;}
  catch {fail('INVALID_JSON');}
}
export function createApp(saveDirectory=fileURLToPath(new URL('../runtime/saves/',import.meta.url))) {
  const store=new RunStore(saveDirectory);
  return createServer(async(req,res)=>{
    try {
      const localPort=(req.socket.address() as {port:number}).port;
      const hosts=[`127.0.0.1:${localPort}`,`localhost:${localPort}`];
      if(!hosts.includes(req.headers.host??'')) {json(res,403,{error:'INVALID_HOST'});return;}
      if(req.headers.origin&&!hosts.some(h=>req.headers.origin===`http://${h}`)||req.headers['sec-fetch-site']==='cross-site') {json(res,403,{error:'ORIGIN_REJECTED'});return;}
      const path=new URL(req.url??'/','http://localhost').pathname;
      if(req.method==='GET'&&path==='/health') {json(res,200,{status:'ok',quality:'MOCK'});return;}
      if(req.method==='POST'&&path==='/api/v1/runs') {const p=await body(req);json(res,201,store.create(p.seed));return;}
      const match=path.match(/^\/api\/v1\/runs\/([^/]+)(?:\/(market|actions|preview|commit|history|ending))?$/);
      if(match) {
        const [,id,action]=match;
        if(req.method==='GET') {
          if(!action) json(res,200,store.get(id));
          else if(action==='market') json(res,200,store.get(id).market);
          else if(action==='actions') json(res,200,store.get(id).actions);
          else if(action==='history') json(res,200,store.history(id));
          else if(action==='ending') json(res,200,store.ending(id));
          else json(res,405,{error:'METHOD_NOT_ALLOWED'});
          return;
        }
        if(req.method==='POST'&&(action==='preview'||action==='commit')) {
          const p=await body(req);json(res,200,action==='preview'?store.preview(id,p):store.commit(id,p));return;
        }
      }
      const files:Record<string,[string,string]>={'/':['index.html','text/html'],'/style.css':['style.css','text/css'],'/app.js':['app.js','text/javascript']};
      if(req.method==='GET'&&Object.hasOwn(files,path)) {
        const [name,mime]=files[path];
        res.writeHead(200,{'Content-Type':`${mime}; charset=utf-8`,'Cache-Control':'no-cache','X-Content-Type-Options':'nosniff',
          'Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data: blob:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"});
        res.end(readFileSync(new URL(name,PUBLIC)));return;
      }
      json(res,404,{error:'NOT_FOUND'});
    } catch(error) {
      if(error instanceof GameError) {
        const code=error.code,status=['WRONG_TURN','CONFLICT_STATE_HASH','IDEMPOTENCY_CONFLICT','RUN_COMPLETED','RUN_NOT_COMPLETED'].includes(code)?409:code==='RUN_NOT_FOUND'?404:400;
        json(res,status,{error:code,message:errors[code]??`요청을 처리할 수 없습니다: ${code}`});
      } else {console.error(error);json(res,500,{error:'INTERNAL_ERROR',message:'저장 또는 처리에 실패했습니다. 같은 요청으로 다시 시도해 주세요.'});}
    }
  });
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href) {
  const port=Number(process.env.INVESTMENT_KING_PORT??3210);
  createApp().listen(port,'127.0.0.1',()=>console.log(`나는야 투자왕 · MOCK 로컬 알파 http://127.0.0.1:${port}`));
}
