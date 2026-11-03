import { mkdirSync, readFileSync, writeFileSync, renameSync, existsSync, openSync, fsyncSync, closeSync } from 'node:fs';
import { join } from 'node:path';
import { randomUUID } from 'node:crypto';
import { createRun, simulate, project, preview, stringify, parse, digest, hashState, fail } from './core/engine.ts';
import type { GameState, Plan } from './core/engine.ts';

interface CommitPlan extends Plan { idempotencyKey:string }
interface Receipt { fingerprint:string; result:unknown }
interface SavedRun { state:GameState; receipts:Record<string,Receipt>; turns:unknown[] }

// A single local Node process is the writer. Each mutation and rename is synchronous:
// no await between reading the latest version and persisting its successor.
// For multiple workers use a transactional database with unique turn/key constraints.
export class RunStore {
  directory:string;
  constructor(directory:string) {this.directory=directory;mkdirSync(directory,{recursive:true});}
  path(id:string) {
    if(!/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(id)) fail('RUN_NOT_FOUND');
    return join(this.directory,`${id}.json`);
  }
  load(id:string):SavedRun {
    const path=this.path(id);if(!existsSync(path)) fail('RUN_NOT_FOUND');
    const saved=parse(readFileSync(path,'utf8')) as SavedRun;
    if(saved.state.runId!==id||saved.state.stateHash!==hashState(saved.state)) fail('SAVE_CORRUPTED');
    return saved;
  }
  save(saved:SavedRun) {
    const path=this.path(saved.state.runId),temp=`${path}.${randomUUID()}.tmp`;
    writeFileSync(temp,stringify(saved),{encoding:'utf8',flag:'wx'});
    const fd=openSync(temp,'r+');try {fsyncSync(fd);} finally {closeSync(fd);}
    renameSync(temp,path);
  }
  create(seed:string) {
    const s=createRun(seed,randomUUID());this.save({state:s,receipts:{},turns:[]});return project(s);
  }
  get(id:string) {return project(this.load(id).state);}
  preview(id:string,p:Plan) {return preview(this.load(id).state,p);}
  history(id:string) {return this.load(id).state.history;}
  ending(id:string) {const s=this.load(id).state;if(s.status!=='COMPLETED') fail('RUN_NOT_COMPLETED');return project(s);}
  commit(id:string,p:CommitPlan) {
    if(!p||typeof p.idempotencyKey!=='string'||!/^[a-zA-Z0-9_-]{1,100}$/.test(p.idempotencyKey)) fail('INVALID_IDEMPOTENCY_KEY');
    const saved=this.load(id),fingerprint=digest(p);
    if(Object.hasOwn(saved.receipts,p.idempotencyKey)) {
      const receipt=saved.receipts[p.idempotencyKey];
      if(receipt.fingerprint!==fingerprint) fail('IDEMPOTENCY_CONFLICT');
      return receipt.result;
    }
    const next=simulate(saved.state,p);
    const result={settledTurn:p.turnIndex,nextTurn:next.turnIndex,stateHash:next.stateHash,status:next.status,summary:next.history.at(-1)};
    saved.turns.push({plan:p,beforeHash:saved.state.stateHash,afterHash:next.stateHash,...next.lastTurn});
    saved.state=next;
    Object.defineProperty(saved.receipts,p.idempotencyKey,{value:{fingerprint,result},enumerable:true,writable:true,configurable:true});
    this.save(saved);
    return result;
  }
}
