import test from 'node:test';
import assert from 'node:assert/strict';
import { createRun, simulate, project, hashState, QUARTERS, preview } from '../src/core/engine.ts';
import { MOCK_DATASET } from '../src/core/market.ts';

const plan = (s, actions = [], orders = []) => ({ turnIndex: s.turnIndex, stateHash: s.stateHash, actions, orders });
const step = (s, actions = [], orders = [], data = MOCK_DATASET) => simulate(s, plan(s, actions, orders), data);

test('80 settlements end on 2026-10-01 and reject an 81st', () => {
  let s = createRun('calendar');
  assert.equal(QUARTERS.length, 80);
  assert.equal(project(s).quarter, '2006Q4');
  for (let i=0; i<80; i++) s = step(s, ['PART_TIME','PART_TIME','EXERCISE']);
  assert.equal(s.turnIndex, 80);
  assert.equal(s.status, 'COMPLETED');
  assert.equal(s.asOfDate, '2026-09-30');
  assert.equal(s.endingAt, '2026-10-01');
  assert.equal(s.history.at(-1).quarter, '2026Q3');
  assert.throws(() => step(s), /RUN_COMPLETED/);
});

test('same seed, versions and actions produce identical state hashes, without mutating input', () => {
  let a = createRun('repeat'), b = createRun('repeat');
  const initial = structuredClone(a);
  for(let i=0;i<12;i++) { a=step(a,['PART_TIME','READ_BOOK','EXERCISE']); b=step(b,['PART_TIME','READ_BOOK','EXERCISE']); assert.equal(a.stateHash,b.stateHash); }
  assert.deepEqual(createRun('repeat'), initial);
  assert.notEqual(createRun('other').stateHash, initial.stateHash);
});

test('starting config, AP and repeat limits are enforced atomically', () => {
  const s = createRun('ap');
  assert.equal(s.cashKRW, 1_000_000n);
  assert.equal(s.stats.financial_knowledge,20);
  assert.equal(s.stats.career_skill,25);
  assert.throws(()=>step(s,['EXERCISE','PART_TIME','READ_BOOK','SOCIALIZE']),/AP_EXCEEDED/);
  assert.throws(()=>step(s,['PART_TIME','PART_TIME','PART_TIME']),/ACTION_LIMIT/);
  assert.throws(()=>step(s,['UNKNOWN']),/INVALID_ACTION/);
  assert.equal(s.turnIndex,0);
  assert.equal(s.cashKRW,1_000_000n);
});

test('book cost and three monthly living costs occur once with a balanced cash ledger', () => {
  const a=step(createRun('ledger'),['PART_TIME','READ_BOOK','EXERCISE']);
  const entries=a.lastTurn.ledger;
  assert.equal(entries.filter(e=>e.reason==='생활비').length,3);
  assert.equal(entries.filter(e=>e.reason==='금융 도서').length,1);
  assert.equal(entries.filter(e=>e.reason==='단기 알바').length,1);
  for(const entry of entries) assert.equal(entry.debits.reduce((n,e)=>n+e.amountKRW,0n),entry.credits.reduce((n,e)=>n+e.amountKRW,0n));
  const delta=entries.reduce((n,e)=>n+e.debits.filter(x=>x.account==='CASH').reduce((a,x)=>a+x.amountKRW,0n)-e.credits.filter(x=>x.account==='CASH').reduce((a,x)=>a+x.amountKRW,0n),0n);
  assert.equal(a.cashKRW,1_000_000n+delta);
  assert.equal(a.stateHash,hashState(a));
});

test('unpaid living costs become arrears, no negative cash, no forced sale', () => {
  let s=createRun('shortfall');
  for(let i=0;i<5;i++) s=step(s);
  assert.equal(s.cashKRW,0n);
  assert.ok(s.arrearsKRW>0n);
  assert.equal(s.turnIndex,5);
  const recovered=step(s,['PART_TIME','PART_TIME']);
  assert.ok(recovered.arrearsKRW < s.arrearsKRW);
});

test('availability cannot be bypassed for BTC, ETH or pre-market KRX gold', () => {
  const s=createRun('locked');
  for(const assetId of ['BTC','ETH','KRX_GOLD']) assert.throws(()=>step(s,[],[{assetId,side:'BUY',quantity:'1',maxSpendKRW:'100000'}]),/NOT_LISTED|RESEARCH_REQUIRED|NOT_UNLOCKED/);
});

test('buys use hidden execution prices and fees, sells preserve fixed-point quantities', () => {
  const s=createRun('trade');
  const view=project(s);
  assert.ok(view.market.find(a=>a.id==='MOCK_A').priceKRW>0n);
  const order={assetId:'MOCK_A',side:'BUY',quantity:'2',maxSpendKRW:'300000'};
  const p=preview(s,plan(s,[],[order]));
  assert.equal(JSON.stringify(p,(_,v)=>typeof v==='bigint'?v.toString():v).includes('executionPrice'),false);
  const bought=step(s,[],[order]);
  assert.equal(bought.holdings[0].units,200000000n);
  const fill=bought.lastTurn.orders[0];
  assert.equal(fill.status,'FILLED');
  assert.ok(fill.feeKRW>0n);
  assert.equal(bought.lastTurn.ledger.find(e=>e.reason==='매수 MOCK_A').credits[0].amountKRW,fill.notionalKRW+fill.feeKRW);
  const sold=step(bought,[],[{assetId:'MOCK_A',side:'SELL',quantity:'1'}]);
  assert.equal(sold.holdings[0].units,100000000n);
});

test('shared reservations, action costs, lots and short sales cannot overspend', () => {
  const s=createRun('invalid');
  const buy={assetId:'MOCK_A',side:'BUY',quantity:'1',maxSpendKRW:'600000'};
  assert.throws(()=>step(s,[],[buy,buy]),/INSUFFICIENT_CASH/);
  assert.throws(()=>step(s,['READ_BOOK'],[{...buy,maxSpendKRW:'1000000'}]),/INSUFFICIENT_CASH/);
  for(const quantity of ['0','-1','NaN','1.1','1e8','Infinity']) assert.throws(()=>step(s,[],[{...buy,quantity}]),/INVALID_LOT/);
  assert.throws(()=>step(s,[],[{assetId:'MOCK_A',side:'SELL',quantity:'1'}]),/INSUFFICIENT_HOLDINGS/);
});

test('fill above reserved budget is rejected without debiting an order', () => {
  const s=createRun('budget');
  const n=step(s,[],[{assetId:'MOCK_A',side:'BUY',quantity:'1',maxSpendKRW:'1'}]);
  assert.equal(n.lastTurn.orders[0].status,'REJECTED');
  assert.equal(n.holdings.length,0);
});

test('missing execution prices and liquidity are never substituted', () => {
  const s=createRun('missing');
  const data=structuredClone(MOCK_DATASET);
  data.prices=data.prices.filter(p=>!(p.assetId==='MOCK_A' && p.date>='2006-10-01' && p.date<='2006-12-31'));
  const o={assetId:'MOCK_A',side:'BUY',quantity:'1',maxSpendKRW:'300000'};
  assert.equal(step(s,[],[o],data).lastTurn.orders[0].reason,'NO_PRICE');
  const illiquid=structuredClone(MOCK_DATASET);
  illiquid.prices.filter(p=>p.assetId==='MOCK_A'&&p.date>='2006-10-01').forEach(p=>p.volumeUnits=null);
  assert.equal(step(s,[],[o],illiquid).lastTurn.orders[0].reason,'ILLIQUID');
});

test('public prices and history exclude future records and fixed future outcomes', () => {
  const s=createRun('asof');
  const v=project(s);
  for(const a of v.market) for(const p of a.series ?? []) assert.ok(p.date<='2006-09-30');
  assert.equal(v.history.length,0);
  assert.equal(v.seed,undefined);
  assert.equal(v.dataset,undefined);
  assert.equal(v.memoryFragments.length,2);
  assert.equal(v.market.some(a=>['BTC','ETH','KRX_GOLD'].includes(a.id)),false);
});

test('stale turn/hash and dataset version fail before mutation', () => {
  const s=createRun('stale');
  assert.throws(()=>simulate(s,{...plan(s),turnIndex:1}),/WRONG_TURN/);
  assert.throws(()=>simulate(s,{...plan(s),stateHash:'fake'}),/CONFLICT_STATE_HASH/);
  assert.throws(()=>step(s,[],[],{...MOCK_DATASET,version:'other'}),/DATASET_VERSION/);
});
