"""Read-only local Codex usage audit. Does not read authentication files."""
from pathlib import Path
import json,sqlite3,datetime as dt,collections,csv
BASE=Path('C:/Users/e2ken/.codex'); OUT=Path('output/usage_audit/2026-10-12_to_2026-10-17');OUT.mkdir(parents=True,exist_ok=True)
TZ=dt.timezone(dt.timedelta(hours=9)); START=dt.datetime(2026,10,12,tzinfo=TZ); END=dt.datetime.now(dt.timezone.utc)
conn=sqlite3.connect(f'file:{BASE.as_posix()}/state_5.sqlite?mode=ro',uri=True);conn.row_factory=sqlite3.Row
threads={r['id']:dict(r) for r in conn.execute('select id,title,source,cwd,model,agent_role,agent_path,agent_nickname from threads')};conn.close()
keys=['input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens','reasoning_output_tokens','total_tokens']
records={};turns={};tools=collections.Counter();outliers=[];last_rate=None;files=0;fallback_files=[];seen_calls=set();seen_outputs=set()
for f in list((BASE/'sessions').rglob('*.jsonl'))+list((BASE/'archived_sessions').glob('*.jsonl')):
    if dt.datetime.fromtimestamp(f.stat().st_mtime,dt.timezone.utc)<START:continue
    files+=1;meta={};model='unknown';turn=None;prompt='';pending={};prev_total=None;has_record=False;fallback=[]
    for line in f.open(encoding='utf-8',errors='replace'):
        try:d=json.loads(line)
        except (ValueError,TypeError):continue
        typ=d.get('type');p=d.get('payload',{});ts=d.get('timestamp','')
        if typ=='session_meta':meta=p
        if typ=='turn_context':model=p.get('model',model);turn=p.get('turn_id',turn)
        if typ=='event_msg' and p.get('type')=='user_message' and p.get('message'):prompt=str(p['message'])[-400:]
        if typ=='response_item' and p.get('type')=='message' and p.get('role')=='user':
            text='\n'.join(x.get('text','') for x in p.get('content',[]) if isinstance(x,dict))
            if text and not text.startswith(('# AGENTS.md','<environment_context>')):
                prompt=text.split('## My request:')[-1].strip()[-400:]
        if not ts:continue
        try:when=dt.datetime.fromisoformat(ts.replace('Z','+00:00'))
        except ValueError:continue
        within=START<=when<=END
        if typ=='response_item' and p.get('type') in ('function_call','custom_tool_call'):
            name=p.get('name','?');pending[p.get('call_id')]=name
            if within and p.get('call_id') not in seen_calls:tools[name]+=1;seen_calls.add(p.get('call_id'))
        if typ=='response_item' and p.get('type') in ('function_call_output','custom_tool_call_output') and within and p.get('call_id') not in seen_outputs:
            seen_outputs.add(p.get('call_id'))
            content=p.get('output','');n=len(content) if isinstance(content,str) else len(json.dumps(content))
            if n>100000:outliers.append({'timestamp':ts,'thread_id':meta.get('id'),'tool':pending.get(p.get('call_id'),'unknown'),'output_characters':n})
        if typ=='token_usage_record':
            has_record=True
            if not within:continue
            rid=p.get('response_id')
            if not rid:continue
            sid=p.get('thread_id',meta.get('id','unknown'));tid=p.get('turn_id',turn);info=threads.get(sid,{})
            row={k:int(p.get('usage',{}).get(k,0) or 0) for k in keys}
            row.update(response_id=rid,timestamp=ts,day=when.astimezone(TZ).date().isoformat(),thread_id=sid,turn_id=tid,model=model,source=str(meta.get('source',info.get('source',''))),agent_path=info.get('agent_path') or '',title=info.get('title') or '',prompt=prompt)
            row['uncached_input_tokens']=max(0,row['input_tokens']-row['cached_input_tokens']-row['cache_write_input_tokens'])
            # Prefer record in its own rollout rather than inherited fork history.
            if rid not in records or sid==meta.get('id'):records[rid]=row
        if typ=='event_msg' and p.get('type')=='token_count':
            info=p.get('info') or {};total=info.get('total_token_usage');usage=info.get('last_token_usage')
            if within and p.get('rate_limits'):
                if last_rate is None or ts>last_rate['timestamp']:last_rate={'timestamp':ts,'limits':p['rate_limits']}
            if within and usage and total and total!=prev_total:fallback.append((ts,usage,meta.get('id'),model,prompt,turn))
            if total:prev_total=total
    if not has_record and fallback:
        fallback_files.append(f.name)
        for ts,u,sid,m,pr,tid in fallback:
            rid=f'legacy:{sid}:{ts}';when=dt.datetime.fromisoformat(ts.replace('Z','+00:00'));info=threads.get(sid,{})
            row={k:int(u.get(k,0) or 0) for k in keys};row.update(response_id=rid,timestamp=ts,day=when.astimezone(TZ).date().isoformat(),thread_id=sid,turn_id=tid,model=m,source=str(meta.get('source','')),agent_path=info.get('agent_path') or '',title=info.get('title') or '',prompt=pr);row['uncached_input_tokens']=max(0,row['input_tokens']-row['cached_input_tokens']-row['cache_write_input_tokens']);records[rid]=row
rows=list(records.values());sumkeys=keys+['uncached_input_tokens']
def grouped(fn):
    groups={}
    for r in rows:
        k=fn(r);g=groups.setdefault(k,{'group':k,'calls':0,**{x:0 for x in sumkeys}});g['calls']+=1
        for x in sumkeys:g[x]+=r[x]
    return sorted(groups.values(),key=lambda g:g['total_tokens'],reverse=True)
bythread=grouped(lambda r:r['thread_id'])
for g in bythread:
    info=threads.get(g['group'],{});g.update({k:info.get(k) for k in ['title','cwd','agent_path','agent_role']})
byturn=grouped(lambda r:(r['thread_id'],r['turn_id']))
for g in byturn:
    rr=[r for r in rows if (r['thread_id'],r['turn_id'])==g['group']];g['prompt']=rr[-1]['prompt'];g['timestamp']=rr[0]['timestamp'];g['thread_title']=threads.get(g['group'][0],{}).get('title');g['group']=list(g['group'])
report={'period_start_kst':START.isoformat(),'snapshot_utc':END.isoformat(),'scope':'Local Codex rollouts on this PC only; response_id deduplicated; usage not invoice','files_scanned':files,'response_count':len(rows),'legacy_fallback_files':fallback_files,'totals':{k:sum(r[k] for r in rows) for k in sumkeys},'by_day':grouped(lambda r:r['day']),'by_model':grouped(lambda r:r['model']),'by_role':grouped(lambda r:'subagent' if r['agent_path'] and r['agent_path']!='/root' else 'root_or_standalone'),'by_thread':bythread,'top_turns':byturn[:35],'largest_tool_outputs':sorted(outliers,key=lambda x:x['output_characters'],reverse=True)[:15],'tool_calls':tools.most_common(20),'latest_rate_limits':last_rate,'unclassified_reported_total_tokens':sum(r['total_tokens'] for r in rows if r['input_tokens']==0 and r['output_tokens']==0)}
(OUT/'summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
with (OUT/'responses.csv').open('w',encoding='utf-8-sig',newline='') as fh:
    writer=csv.DictWriter(fh,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
print(json.dumps({k:report[k] for k in ['period_start_kst','snapshot_utc','files_scanned','response_count','totals','by_day','by_model','by_role']},ensure_ascii=False,indent=2))
print('TOP_THREADS',json.dumps(bythread[:9],ensure_ascii=False));print('TOP_TURNS',json.dumps(byturn[:7],ensure_ascii=False));print('OUTPUT',str(OUT))
