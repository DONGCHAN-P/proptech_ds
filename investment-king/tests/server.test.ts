import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, rmSync, readdirSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createApp } from '../src/server.ts';

async function listen(dir) {
  const app=createApp(dir);await new Promise(resolve=>app.listen(0,'127.0.0.1',resolve));
  const base=`http://127.0.0.1:${app.address().port}`;
  return {app,base,close:()=>new Promise(resolve=>app.close(resolve))};
}
async function request(base,path,body,headers={}) {
  const r=await fetch(base+path,{method:body===undefined?'GET':'POST',headers:{'Content-Type':'application/json',...headers},body:body===undefined?undefined:JSON.stringify(body)});
  return {status:r.status,data:await r.json()};
}
const commit=(s,key='test-key',actions=['PART_TIME','EXERCISE'])=>({turnIndex:s.turnIndex,stateHash:s.stateHash,idempotencyKey:key,actions,orders:[]});

test('HTTP round trip persists once across retries, restart and concurrency',async()=>{
  const dir=mkdtempSync(join(tmpdir(),'investment-king-'));
  let srv=await listen(dir);
  try {
    const created=await request(srv.base,'/api/v1/runs',{seed:'api-seed'});
    assert.equal(created.status,201);
    const s=created.data,path=`/api/v1/runs/${s.runId}`;
    assert.equal(s.cashKRW,'1000000');
    const payload=commit(s);
    const before=await request(srv.base,path+'/preview',payload);
    assert.equal(before.status,200);
    const [a,b]=await Promise.all([request(srv.base,path+'/commit',payload),request(srv.base,path+'/commit',payload)]);
    assert.equal(a.status,200);assert.deepEqual(a,b);
    assert.equal((await request(srv.base,path)).data.turnIndex,1);
    assert.equal((await request(srv.base,path+'/commit',{...payload,actions:[]})).data.error,'IDEMPOTENCY_CONFLICT');
    await srv.close();srv=await listen(dir);
    assert.deepEqual((await request(srv.base,path+'/commit',payload)).data,a.data);
    const current=(await request(srv.base,path)).data;
    const results=await Promise.all([request(srv.base,path+'/commit',commit(current,'parallel-a')),request(srv.base,path+'/commit',commit(current,'parallel-b'))]);
    assert.deepEqual(results.map(r=>r.status).sort(),[200,409]);
    assert.equal((await request(srv.base,path)).data.turnIndex,2);
    const disk=readFileSync(join(dir,readdirSync(dir).find(f=>f.endsWith('.json'))),'utf8');
    assert.ok(disk.includes('ledger'));
  } finally {await srv.close();rmSync(dir,{recursive:true,force:true});}
});

test('invalid and cross-origin HTTP requests cannot mutate a run',async()=>{
  const dir=mkdtempSync(join(tmpdir(),'investment-king-'));
  const srv=await listen(dir);
  try {
    const s=(await request(srv.base,'/api/v1/runs',{seed:'safe'})).data,path=`/api/v1/runs/${s.runId}`;
    assert.equal((await request(srv.base,path+'/commit',{...commit(s),orders:[{assetId:'BTC',side:'BUY',quantity:'1',maxSpendKRW:'1'}]})).status,400);
    assert.equal((await request(srv.base,path)).data.turnIndex,0);
    assert.equal((await request(srv.base,path+'/commit',commit(s),{Origin:'https://example.com'})).status,403);
    assert.equal((await request(srv.base,'/api/v1/runs',{seed:{bad:1}})).status,400);
    assert.equal((await request(srv.base,path+'/commit',{...commit(s),stateHash:'bad'})).status,409);
    const invalid=await fetch(srv.base+path+'/commit',{method:'POST',headers:{'Content-Type':'application/json'},body:'{broken'});
    assert.equal(invalid.status,400);
    const projection=(await request(srv.base,path)).data;
    assert.equal(projection.seed,undefined);assert.equal(projection.history.length,0);
    assert.equal((await request(srv.base,path+'/ending')).status,409);
  } finally {await srv.close();rmSync(dir,{recursive:true,force:true});}
});

test('accepted prototype-like idempotency keys survive restart and replay',async()=>{
  const dir=mkdtempSync(join(tmpdir(),'investment-king-'));
  let srv=await listen(dir);
  try {
    const s=(await request(srv.base,'/api/v1/runs',{seed:'special-keys'})).data,path=`/api/v1/runs/${s.runId}`;
    const payload=commit(s,'__proto__');
    const first=await request(srv.base,path+'/commit',payload);
    assert.equal(first.status,200);
    await srv.close();srv=await listen(dir);
    const replay=await request(srv.base,path+'/commit',payload);
    assert.deepEqual(replay,first);
    assert.equal((await request(srv.base,path)).data.turnIndex,1);
  } finally {await srv.close();rmSync(dir,{recursive:true,force:true});}
});
