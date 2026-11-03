import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { MOCK_DATASET, SCALE, quarterDates, lastPrice, executionPrice } from './market.ts';
import type { Dataset, Asset } from './market.ts';

export const CONFIG = JSON.parse(readFileSync(new URL('../../docs/BALANCE_CONFIG_v1.0.json', import.meta.url), 'utf8'));
export const QUARTERS = Array.from({length:80},(_,i)=>quarterDates(i).quarter);
export const RULES_VERSION = 'alpha-0.1.0/balance-1.0.0-draft';
export const EVENT_VERSION = 'personal-fixtures-0.1.0';
export const ACTION_LABELS: Record<string,string> = { PART_TIME:'단기 알바',READ_BOOK:'금융 책 읽기',STUDY_CAREER:'직무 공부',EXERCISE:'운동과 휴식',SOCIALIZE:'친구와 교류',APPLY_JOB:'취업 지원' };
export interface Order { assetId:string; side:'BUY'|'SELL'; quantity:string; maxSpendKRW?:string }
export interface Plan { turnIndex:number; stateHash:string; actions:string[]; orders:Order[] }
interface Posting { account:string; amountKRW:bigint }
interface Entry { sequence:number; month:number; reason:string; debits:Posting[]; credits:Posting[] }
interface Holding { assetId:string; units:bigint; costBasisKRW:bigint }
export interface OrderResult { assetId:string; side:string; quantity:string; status:'FILLED'|'REJECTED'; reason?:string; notionalKRW?:bigint; feeKRW?:bigint; executionPriceKRW?:bigint; executedAt?:string }
interface Summary { turnIndex:number; quarter:string; cashKRW:bigint; netWorthKRW:bigint; lifeScore:number; balanceScore:number; incomeKRW:bigint; expenseKRW:bigint; actions:string[]; events:string[] }
export interface GameState {
  runId:string; seed:string; turnIndex:number; status:'OPEN'|'COMPLETED'; asOfDate:string; endingAt?:string;
  dataVersion:string; rulesVersion:string; eventVersion:string;
  cashKRW:bigint; arrearsKRW:bigint; salaryKRW:bigint; employed:boolean;
  stats:Record<string,number>; wellbeing:Record<string,number>; holdings:Holding[];
  housing:'FAMILY'; family:{partnerStatus:string;childrenCount:number};
  memoryFragments:string[]; history:Summary[]; ledgerSequence:number;
  lastTurn:null | {ledger:Entry[];orders:OrderResult[];events:string[];draws:{id:string;value:number}[]};
  stateHash:string;
}
export class GameError extends Error {
  code:string;
  constructor(code:string) { super(code); this.code=code; }
}
export function fail(code:string): never { throw new GameError(code); }
export const stringify = (value:unknown) => JSON.stringify(value,(_,v)=>typeof v==='bigint'?{$bigint:v.toString()}:v);
export const parse = (value:string) => JSON.parse(value,(_,v)=>v && typeof v==='object' && Object.keys(v).length===1 && typeof v.$bigint==='string' ? BigInt(v.$bigint):v);
function canonical(value:any):string {
  if(typeof value==='bigint') return `"bigint:${value}"`;
  if(value===null || typeof value!=='object') return JSON.stringify(value);
  if(Array.isArray(value)) return `[${value.map(canonical).join(',')}]`;
  return `{${Object.keys(value).filter(k=>value[k]!==undefined).sort().map(k=>`${JSON.stringify(k)}:${canonical(value[k])}`).join(',')}}`;
}
export const digest = (value:unknown) => createHash('sha256').update(canonical(value)).digest('hex');
export function hashState(s:GameState) { const {stateHash,...rest}=s; return digest(rest); }
export function draw(seed:string, turn:number, id:string, counter=0) {
  const hex=digest([seed,turn,id,counter]).slice(0,13);
  return Number.parseInt(hex,16)/0x10000000000000;
}
const clamp=(v:number,min=0,max=100)=>Math.max(min,Math.min(max,v));
const rounded=(a:bigint,b:bigint)=>(a+b/2n)/b;
const memories=[
  '인터넷에서 태어난 낯선 화폐가 언젠가 세상의 주목을 받았던 것 같다.',
  '매일 쌓은 작은 배움이 오래 뒤 삶의 선택지를 바꾸었던 것 같다.',
  '자산이 흔들릴 때 일상을 지탱할 여유가 필요했던 것 같다.',
  '좋은 기회도 건강과 관계를 모두 되돌려 주지는 못했던 것 같다.',
  '긴 시간을 함께한 선택이 뜻밖의 결과를 만들었던 것 같다.',
];
export function createRun(seed:string,runId='headless'):GameState {
  if(typeof seed!=='string'||seed.length<1||seed.length>80) fail('INVALID_SEED');
  const s:GameState={runId,seed,turnIndex:0,status:'OPEN',asOfDate:'2006-09-30',dataVersion:MOCK_DATASET.version,rulesVersion:RULES_VERSION,eventVersion:EVENT_VERSION,
    cashKRW:BigInt(CONFIG.game.starting_cash_krw),arrearsKRW:0n,salaryKRW:0n,employed:false,
    stats:{...CONFIG.starting_stats},wellbeing:{...CONFIG.starting_wellbeing},holdings:[],housing:'FAMILY',family:{partnerStatus:'SINGLE',childrenCount:0},
    memoryFragments:memories.slice(0,CONFIG.memory.fragments_at_start),history:[],ledgerSequence:0,lastTurn:null,stateHash:''};
  s.stateHash=hashState(s);return s;
}
function available(s:GameState,asset:Asset) {
  if(asset.listedDate>s.asOfDate) return 'NOT_LISTED';
  if(!asset.availableFrom) return 'RESEARCH_REQUIRED';
  if(asset.availableFrom>s.asOfDate) return 'NOT_UNLOCKED';
  if(s.stats.financial_knowledge<asset.requiresKnowledge) return 'NOT_UNLOCKED';
  return 'AVAILABLE';
}
function quantityUnits(value:unknown,asset:Asset):bigint {
  if(typeof value!=='string'||value.length>30||!/^\d+(\.\d{1,8})?$/.test(value)) fail('INVALID_LOT');
  const [whole,decimal='']=value.split('.');
  const units=BigInt(whole)*SCALE+BigInt(decimal.padEnd(8,'0'));
  if(units<=0n||units%asset.lotUnits!==0n) fail('INVALID_LOT');
  return units;
}
function money(value:unknown) {
  if(typeof value!=='string'||!/^\d{1,18}$/.test(value)||BigInt(value)<=0n) fail('INVALID_BUDGET');
  return BigInt(value);
}
export function preview(s:GameState,p:Plan,data:Dataset=MOCK_DATASET) {
  if(s.status==='COMPLETED') fail('RUN_COMPLETED');
  if(data.version!==s.dataVersion) fail('DATASET_VERSION');
  if(s.rulesVersion!==RULES_VERSION||s.eventVersion!==EVENT_VERSION) fail('RULES_VERSION');
  if(!p||p.turnIndex!==s.turnIndex) fail('WRONG_TURN');
  if(p.stateHash!==s.stateHash) fail('CONFLICT_STATE_HASH');
  if(!Array.isArray(p.actions)||!Array.isArray(p.orders)||p.orders.length>20) fail('INVALID_PLAN');
  let ap=0,cost=0n;const counts:Record<string,number>={};
  for(const id of p.actions) {
    if(typeof id!=='string'||!Object.hasOwn(CONFIG.actions,id)) fail('INVALID_ACTION');
    const a=CONFIG.actions[id];ap+=a.ap_cost;
    if(ap>CONFIG.game.action_points_per_turn) fail('AP_EXCEEDED');
    counts[id]=(counts[id]??0)+1;
    if(counts[id]>a.max_per_turn) fail('ACTION_LIMIT');
    cost+=BigInt(a.book_purchase_price_krw??a.cost_krw??0);
  }
  // Study actions earlier in the ordered plan can establish job eligibility.
  const tempStats={...s.stats};let stress=s.wellbeing.stress;
  for(const id of p.actions) {
    if(id==='STUDY_CAREER') tempStats.career_skill=growth(tempStats.career_skill,CONFIG.actions[id].career_skill_base_delta,stress);
    if(id==='APPLY_JOB'&&(s.employed||tempStats.career_skill<CONFIG.actions.APPLY_JOB.career_skill_minimum)) fail('JOB_REQUIREMENTS');
    stress=clamp(stress+(CONFIG.actions[id].stress_delta??0));
  }
  let reserved=cost;const reservedUnits:Record<string,bigint>={};
  for(const o of p.orders) {
    if(!o||typeof o!=='object') fail('INVALID_ORDER');
    const a=data.assets.find(a=>a.id===o.assetId);if(!a) fail('INVALID_ASSET');
    const status=available(s,a);if(status!=='AVAILABLE') fail(status);
    const units=quantityUnits(o.quantity,a);
    if(!lastPrice(data,a.id,s.asOfDate)) fail('NO_PRICE');
    if(o.side==='BUY') reserved+=money(o.maxSpendKRW);
    else if(o.side==='SELL') {
      reservedUnits[a.id]=(reservedUnits[a.id]??0n)+units;
      if(reservedUnits[a.id]>(s.holdings.find(h=>h.assetId===a.id)?.units??0n)) fail('INSUFFICIENT_HOLDINGS');
    } else fail('INVALID_ORDER');
  }
  if(reserved>s.cashKRW) fail('INSUFFICIENT_CASH');
  const living=BigInt(CONFIG.starting_household.monthly_essential_living_cost_krw)*3n;
  return {apUsed:ap,actionCostKRW:cost,reservedCashKRW:reserved,unreservedCashKRW:s.cashKRW-reserved,livingCostKRW:living,
    warning:s.cashKRW-reserved<living?'주문 예약 뒤 생활비가 부족할 수 있습니다. 알바·근로소득은 결산 때 반영됩니다.':null,
    quality:'MOCK',priceNotice:'주문은 분기 첫 가상 세션에 체결됩니다. 실제 체결가가 예약 한도를 넘으면 거부됩니다.'};
}
function growth(before:number,base:number,stress:number) {
  return clamp(before+base*(1+0.005*before)*clamp(1-stress/200,0.5,1)*(1-0.005*Math.max(0,before-50)));
}
export function netWorth(s:GameState,data:Dataset=MOCK_DATASET) {
  let total=s.cashKRW-s.arrearsKRW;
  for(const h of s.holdings) {
    const p=lastPrice(data,h.assetId,s.asOfDate);if(!p) fail('VALUATION_UNAVAILABLE');
    total+=rounded(h.units*p.priceKRW,SCALE);
  }
  return total;
}
export function scores(s:GameState,data:Dataset=MOCK_DATASET) {
  const wealth=netWorth(s,data),sc=CONFIG.scoring,w=sc.life_metric_weights;
  const wealthScore=100*clamp(Math.log1p(Number(wealth>0n?wealth:0n)/sc.wealth_score_reference_krw)/Math.log1p(sc.wealth_score_soft_cap_krw/sc.wealth_score_reference_krw),0,1);
  const lifeScore=w.health*s.stats.health+w.relationship*s.stats.relationship+w.autonomy*s.wellbeing.autonomy+w.happiness*s.wellbeing.happiness+w.stability*s.wellbeing.stability;
  const liquid=Number(s.cashKRW)+s.holdings.reduce((sum,h)=>sum+Number(rounded(h.units*lastPrice(data,h.assetId,s.asOfDate)!.priceKRW,SCALE)),0);
  const runway=clamp(liquid/(sc.liquid_runway_full_credit_months*CONFIG.starting_household.monthly_essential_living_cost_krw),0,1);
  // Alpha has no sustainable nonlabor-income product or loan contracts yet.
  const freedom=100*(sc.financial_freedom_metric_weights.liquid_runway*runway+sc.financial_freedom_metric_weights.debt_safety*(s.arrearsKRW===0n?1:0));
  return {netWorthKRW:wealth,wealthScore,lifeScore,balanceScore:sc.wealth_score_share*wealthScore+sc.life_score_share*lifeScore,freedomIndex:freedom};
}
export function simulate(input:GameState,p:Plan,data:Dataset=MOCK_DATASET):GameState {
  preview(input,p,data);
  const s=structuredClone(input),d=quarterDates(s.turnIndex);
  const ledger:Entry[]=[],events:string[]=[],orders:OrderResult[]=[],draws:{id:string;value:number}[]=[];
  let month=0,parttime=0n,offer=false;
  function post(reason:string,debits:Posting[],credits:Posting[]) {
    if(debits.reduce((n,p)=>n+p.amountKRW,0n)!==credits.reduce((n,p)=>n+p.amountKRW,0n)) fail('UNBALANCED_LEDGER');
    ledger.push({sequence:++s.ledgerSequence,month,reason,debits,credits});
  }
  const incoming=(amount:bigint,reason:string,from='INCOME')=>{s.cashKRW+=amount;post(reason,[{account:'CASH',amountKRW:amount}],[{account:from,amountKRW:amount}]);};
  function expense(amount:bigint,reason:string,mandatory=false) {
    const paid=amount>s.cashKRW?s.cashKRW:amount,unpaid=amount-paid;
    if(unpaid&&!mandatory) fail('INSUFFICIENT_CASH');
    s.cashKRW-=paid;s.arrearsKRW+=unpaid;
    post(reason,[{account:'EXPENSE',amountKRW:amount}],[{account:'CASH',amountKRW:paid},...(unpaid?[{account:'ARREARS',amountKRW:unpaid}]:[])]);
  }
  const rng=(id:string,counter=0)=>{const value=draw(s.seed,s.turnIndex,id,counter);draws.push({id:`${id}:${counter}`,value});return value;};
  for(const [i,id] of p.actions.entries()) {
    const a=CONFIG.actions[id];
    if(id==='READ_BOOK') {expense(BigInt(a.book_purchase_price_krw),'금융 도서');s.stats.financial_knowledge=growth(s.stats.financial_knowledge,a.financial_knowledge_base_delta,s.wellbeing.stress);}
    if(id==='STUDY_CAREER') s.stats.career_skill=growth(s.stats.career_skill,a.career_skill_base_delta,s.wellbeing.stress);
    if(id==='PART_TIME') parttime+=BigInt(a.income_krw_per_action);
    if(id==='SOCIALIZE') expense(BigInt(a.cost_krw),'교류 비용');
    if(id==='APPLY_JOB'&&!offer) {
      const chance=clamp(1/(1+Math.exp(-(-2.2+0.045*s.stats.career_skill+0.015*s.stats.execution+0.30))),0.05,0.85);
      if(rng('job',i)<chance) {offer=true;events.push('취업 합격 · 두 번째 달부터 급여가 발생합니다.');}
      else events.push('이번 지원은 불합격했습니다. 공부와 재지원으로 다시 도전할 수 있습니다.');
    }
    for(const [stat,key] of [['health','health_delta'],['execution','execution_delta'],['relationship','relationship_delta']]) if(a[key]) s.stats[stat]=clamp(s.stats[stat]+a[key]);
    s.wellbeing.stress=clamp(s.wellbeing.stress+(a.stress_delta??0));
    s.wellbeing.happiness=clamp(s.wellbeing.happiness+(a.happiness_delta??0));
  }
  // All buy budgets already fit starting cash after action costs. Unspent reservations are released on settlement.
  for(const o of p.orders) {
    const a=data.assets.find(a=>a.id===o.assetId)!;
    const units=quantityUnits(o.quantity,a),quote=executionPrice(data,a.id,s.turnIndex);
    const reject=(reason:string)=>orders.push({...o,status:'REJECTED',reason});
    if(!quote) {reject('NO_PRICE');continue;}
    if(quote.priceKRW<=0n) {reject('NO_PRICE');continue;}
    if(quote.volumeUnits===null||quote.volumeUnits<=0n||units>quote.volumeUnits/100n) {reject('ILLIQUID');continue;}
    const notional=rounded(units*quote.priceKRW,SCALE),fee=rounded(notional*a.feeBps,10000n);
    if(notional<=0n) {reject('INVALID_LOT');continue;}
    if(o.side==='BUY') {
      const total=notional+fee;
      if(total>money(o.maxSpendKRW)||total>s.cashKRW) {reject('BUDGET_EXCEEDED');continue;}
      s.cashKRW-=total;
      post(`매수 ${a.id}`,[{account:'INVESTMENTS',amountKRW:notional},{account:'EXPENSE',amountKRW:fee}],[{account:'CASH',amountKRW:total}]);
      let h=s.holdings.find(h=>h.assetId===a.id);
      if(!h) {h={assetId:a.id,units:0n,costBasisKRW:0n};s.holdings.push(h);}
      h.units+=units;h.costBasisKRW+=notional;
    } else {
      const h=s.holdings.find(h=>h.assetId===a.id)!;
      const basis=h.costBasisKRW*units/h.units,proceeds=notional-fee;
      s.cashKRW+=proceeds;h.units-=units;h.costBasisKRW-=basis;
      const gain=notional-basis;
      post(`매도 ${a.id}`,[{account:'CASH',amountKRW:proceeds},{account:'EXPENSE',amountKRW:fee},...(gain<0n?[{account:'LOSS',amountKRW:-gain}]:[])],
        [{account:'INVESTMENTS',amountKRW:basis},...(gain>=0n?[{account:'GAIN',amountKRW:gain}]:[])]);
    }
    orders.push({assetId:o.assetId,side:o.side,quantity:o.quantity,status:'FILLED',notionalKRW:notional,feeKRW:fee,executionPriceKRW:quote.priceKRW,executedAt:quote.date});
  }
  s.holdings=s.holdings.filter(h=>h.units>0n);
  for(month=1;month<=3;month++) {
    if(month===1&&parttime) incoming(parttime,'단기 알바');
    if(offer&&month===2) {s.employed=true;s.salaryKRW=1_200_000n+BigInt(Math.round(s.stats.career_skill))*10_000n;}
    if(s.employed) incoming(s.salaryKRW,'급여');
    expense(BigInt(CONFIG.starting_household.monthly_essential_living_cost_krw),'생활비',true);
    if(s.arrearsKRW>0n&&s.cashKRW>0n) {
      const paid=s.cashKRW<s.arrearsKRW?s.cashKRW:s.arrearsKRW;
      s.cashKRW-=paid;s.arrearsKRW-=paid;
      post('기존 미납 상환',[{account:'ARREARS',amountKRW:paid}],[{account:'CASH',amountKRW:paid}]);
    }
  }
  month=3;
  const personal=rng('personal-event');
  if(personal<0.10) {incoming(50_000n,'가상 사건: 뜻밖의 선물');events.push('개인 사건 · 지인에게 작은 선물을 받았습니다. +50,000원');}
  else if(personal<0.18) {expense(30_000n,'가상 사건: 생활용품 수리',true);events.push('개인 사건 · 생활용품 수리가 필요했습니다. 30,000원');}
  else if(personal<0.28) {s.wellbeing.happiness=clamp(s.wellbeing.happiness+3);events.push('개인 사건 · 오랜 친구에게 반가운 연락이 왔습니다. 행복 +3');}
  if(s.employed) s.wellbeing.stress=clamp(s.wellbeing.stress+5);
  s.stats.health=clamp(s.stats.health-Math.max(0,s.wellbeing.stress-50)/30);
  s.wellbeing.autonomy=clamp(40+Math.min(Number(s.cashKRW/150_000n),40)-Number(s.arrearsKRW/150_000n));
  s.wellbeing.stability=clamp(45+(s.employed?20:0)+Math.min(Number(s.cashKRW/150_000n),25)-(s.arrearsKRW>0n?30:0));
  if(s.arrearsKRW>0n) events.push('생활비 미납이 있습니다. 알바·취업·자산 매도로 복구할 수 있습니다.');
  for(const [i,condition] of [[2,s.stats.financial_knowledge>=40],[3,s.turnIndex>=20],[4,s.turnIndex>=50]] as [number,boolean][]) if(condition&&!s.memoryFragments.includes(memories[i])) {s.memoryFragments.push(memories[i]);events.push('새로운 기억의 파편을 떠올렸습니다.');}
  s.asOfDate=d.end;
  s.lastTurn={ledger,orders,events,draws};
  const sc=scores(s,data);
  const income=ledger.flatMap(e=>e.credits).filter(p=>p.account==='INCOME').reduce((n,p)=>n+p.amountKRW,0n);
  const expenses=ledger.flatMap(e=>e.debits).filter(p=>p.account==='EXPENSE').reduce((n,p)=>n+p.amountKRW,0n);
  s.history.push({turnIndex:s.turnIndex,quarter:d.quarter,cashKRW:s.cashKRW,netWorthKRW:sc.netWorthKRW,lifeScore:sc.lifeScore,balanceScore:sc.balanceScore,incomeKRW:income,expenseKRW:expenses,actions:[...p.actions],events:[...events]});
  s.turnIndex++;
  if(s.turnIndex===80) {s.status='COMPLETED';s.endingAt='2026-10-01';}
  if(s.cashKRW<0n||s.arrearsKRW<0n||s.holdings.some(h=>h.units<=0n)) fail('INVARIANT_FAILED');
  s.stateHash=hashState(s);return s;
}
export function project(s:GameState,data:Dataset=MOCK_DATASET) {
  return {
    runId:s.runId,turnIndex:s.turnIndex,quarter:s.status==='COMPLETED'?'2026Q4':QUARTERS[s.turnIndex],asOfDate:s.asOfDate,status:s.status,endingAt:s.endingAt,
    ageYears:20+s.turnIndex/4,ap:3,stateHash:s.stateHash,cashKRW:s.cashKRW,arrearsKRW:s.arrearsKRW,salaryKRW:s.salaryKRW,employed:s.employed,
    stats:s.stats,wellbeing:s.wellbeing,housing:s.housing,family:s.family,memoryFragments:s.memoryFragments,history:s.history,lastTurn:s.lastTurn,
    holdings:s.holdings.map(h=>({...h,quantity:formatUnits(h.units),valueKRW:rounded(h.units*lastPrice(data,h.assetId,s.asOfDate)!.priceKRW,SCALE)})),
    scores:scores(s,data),dataVersion:s.dataVersion,rulesVersion:s.rulesVersion,eventVersion:s.eventVersion,quality:'MOCK',
    market:data.assets.filter(a=>a.listedDate<=s.asOfDate).map(a=>{
      const status=available(s,a),price=status==='AVAILABLE'?lastPrice(data,a.id,s.asOfDate):undefined;
      return {id:a.id,name:a.name,class:a.class,status,priceKRW:price?.priceKRW??null,priceDate:price?.date??null,quality:'MOCK',feeBps:a.feeBps.toString(),
        lot:a.class==='STOCK'?'1':'0.01',series:status==='AVAILABLE'?data.prices.filter(p=>p.assetId===a.id&&p.date<=s.asOfDate&&p.kind!=='EXECUTION').map(p=>({date:p.date,priceKRW:p.priceKRW})):[]};
    }),
    actions:Object.entries(CONFIG.actions).map(([id,a]:[string,any])=>({id,label:ACTION_LABELS[id],ap:a.ap_cost,maxPerTurn:a.max_per_turn,costKRW:BigInt(a.book_purchase_price_krw??a.cost_krw??0),
      description:actionDescription(id),disabled:id==='APPLY_JOB'&&s.employed})),
  };
}
function formatUnits(units:bigint) {return `${units/SCALE}.${(units%SCALE).toString().padStart(8,'0')}`.replace(/\.?0+$/,'');}
function actionDescription(id:string) {return ({PART_TIME:'수입 40만 원 · 스트레스 +4',READ_BOOK:'지식 성장 · 도서 2.5만 원',STUDY_CAREER:'직무능력 성장 · 스트레스 +2',EXERCISE:'건강 +6 · 스트레스 −7',SOCIALIZE:'관계 +5 · 행복 +3 · 2만 원',APPLY_JOB:'직무능력 30 이상 · 합격 시 다음 달 근무'} as Record<string,string>)[id];}
