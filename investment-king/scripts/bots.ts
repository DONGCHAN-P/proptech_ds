import { writeFileSync, mkdirSync } from 'node:fs';
import { createRun, simulate, scores, draw } from '../src/core/engine.ts';

const count=Number(process.argv[2]??1000);
if(!Number.isInteger(count)||count<1||count>10000)throw new Error('Seed count must be 1..10000');
const results:{seed:string;netWorthKRW:string;lifeScore:number;balanceScore:number;arrearsKRW:string;hash:string}[]=[];
let completed=0,arrearsCount=0;const actionsUsed:Record<string,number>={};
const started=performance.now();
for(let seedIndex=0;seedIndex<count;seedIndex++) {
  const seed=`alpha-balance-${seedIndex.toString().padStart(4,'0')}`;
  let s=createRun(seed);
  for(let t=0;t<80;t++) {
    let actions:string[];
    if(!s.employed) {
      if(s.cashKRW<500_000n)actions=['PART_TIME','PART_TIME','EXERCISE'];
      else if(s.stats.career_skill<30)actions=['PART_TIME','STUDY_CAREER','EXERCISE'];
      else actions=['PART_TIME','APPLY_JOB','EXERCISE'];
    } else actions=['EXERCISE',draw(seed,t,'bot-choice')<0.5?'SOCIALIZE':'STUDY_CAREER','EXERCISE'];
    actions.forEach(a=>actionsUsed[a]=(actionsUsed[a]??0)+1);
    s=simulate(s,{turnIndex:s.turnIndex,stateHash:s.stateHash,actions,orders:[]});
    if(s.cashKRW<0n)throw new Error('Negative cash');
    for(const e of s.lastTurn!.ledger)if(e.debits.reduce((n,p)=>n+p.amountKRW,0n)!==e.credits.reduce((n,p)=>n+p.amountKRW,0n))throw new Error('Unbalanced ledger');
  }
  const score=scores(s);
  if(s.status==='COMPLETED'&&s.turnIndex===80)completed++;
  if(s.arrearsKRW>0n)arrearsCount++;
  results.push({seed,netWorthKRW:score.netWorthKRW.toString(),lifeScore:score.lifeScore,balanceScore:score.balanceScore,arrearsKRW:s.arrearsKRW.toString(),hash:s.stateHash});
}
const percentile=(values:number[],p:number)=>values.sort((a,b)=>a-b)[Math.floor((values.length-1)*p)];
const report={quality:'MOCK',scope:'One balanced career/life policy; not seven-policy production balance validation',seedCount:count,completed,completionRate:completed/count,endingArrearsRate:arrearsCount/count,
  netWorthKRW:{p10:percentile(results.map(r=>Number(r.netWorthKRW)),.1),p50:percentile(results.map(r=>Number(r.netWorthKRW)),.5),p90:percentile(results.map(r=>Number(r.netWorthKRW)),.9)},
  lifeScore:{p10:percentile(results.map(r=>r.lifeScore),.1),p50:percentile(results.map(r=>r.lifeScore),.5),p90:percentile(results.map(r=>r.lifeScore),.9)},
  actionsUsed,elapsedSeconds:(performance.now()-started)/1000};
mkdirSync(new URL('../reports/',import.meta.url),{recursive:true});
writeFileSync(new URL('../reports/balanced-policy-summary.json',import.meta.url),JSON.stringify(report,null,2));
writeFileSync(new URL('../reports/balanced-policy-seeds.json',import.meta.url),JSON.stringify(results,null,2));
console.log(JSON.stringify(report,null,2));
