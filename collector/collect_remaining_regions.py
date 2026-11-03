"""Resume Chungnam, then collect missing provincial RTMS history using the existing worker."""
from pathlib import Path
from datetime import datetime
from urllib.parse import unquote
import argparse,contextlib,hashlib,json,os,sys,time
import requests

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from common import load_secrets
from collector import collect_three_cities as worker
from collector import collect_more_regions as previous

OUT=ROOT/'raw/rtms_trade_expansion/additional_20261026'
OLD=previous.OUT;LEDGER=worker.LEDGER;ADMIN=previous.ADMIN
PROVINCES={'gyeongnam':'경상남도','gyeongbuk':'경상북도','jeonbuk':'전북특별자치도','jeonnam':'전남광주통합특별시','gangwon':'강원특별자치도','jeju':'제주특별자치도'}
REPRESENTATIVES={'gyeongnam':'48121','gyeongbuk':'47111','jeonbuk':'52111','jeonnam':'12110','gangwon':'51110','jeju':'50110'}
MONTHS=[f'{y}{m:02}' for y in range(2006,2027) for m in range(1,13) if f'{y}{m:02}'<='202609']
def read(p):return json.loads(p.read_text('utf-8'))
def stamp():return datetime.now(worker.KST).isoformat()
def groups():
    rows=read(ADMIN);g={'chungnam':read(OLD/'plan.json')['groups']['chungnam']}
    for name,province in PROVINCES.items():
        selected=[r for r in rows if r['fields'][1]==province and (name!='jeonnam' or r['code'] not in previous.groups()['gwangju'])]
        g[name]=[r['code'] for r in selected if not any(x['code']!=r['code'] and str(x['fields'][2]).startswith(str(r['fields'][2])+' ') for x in selected)]
    # Potential old municipality codes are kept separate from current districts, for later boundary/dedup review.
    g['gyeongnam']+=['48110','48160','48190']
    assert len(MONTHS)==249 and len(set(c for codes in g.values() for c in codes))==sum(map(len,g.values()))
    return g
def grid(name,codes):
    base=OLD if name=='chungnam' else OUT;done=rows=0
    for ym in MONTHS:
        for code in codes:
            p=base/name/ym/f'{code}.meta.json'
            if p.exists():
                m=read(p)
                if m.get('complete') and m['stored_rows']==m['totalCount']:done+=1;rows+=m['stored_rows']
    return {'target_code_months':len(codes)*len(MONTHS),'complete_code_months':done,'remaining_code_months':len(codes)*len(MONTHS)-done,'stored_api_rows':rows,'source':str(base/name)}
def plan(cap):
    g=groups();obj={'created_at':stamp(),'priority':list(g),'from':'200601','to':'202609','groups':g,'grid':{n:grid(n,c) for n,c in g.items()},'daily_known_call_cap':cap,'code_source':str(ADMIN),'historical_alias_candidates':['48110','48160','48190'],'historical_boundary_and_dedup_review':'before_analysis_integration','auto_wait_for_next_day':False}
    worker.save(OUT/'plan.json',obj);return obj
@contextlib.contextmanager
def exclusive():
    paths=[LEDGER/'running.lock',ROOT/'raw/rtms_trade_expansion/gwangju_sejong/running.lock',OLD/'batch_running.lock',OUT/'batch_running.lock'];held=[]
    try:
        for p in paths:
            p.parent.mkdir(parents=True,exist_ok=True)
            try:fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
            except FileExistsError:raise RuntimeError('EXISTING_COLLECTOR_LOCK_VERIFY_OWNER_BEFORE_RESUME') from None
            with os.fdopen(fd,'w') as f:f.write(str(os.getpid()))
            held.append(p)
        yield
    finally:
        for p in reversed(held):p.unlink(missing_ok=True)
def pilot(cap):
    report={'started':stamp(),'state':'running','cases':[],'group_fingerprint':hashlib.sha256(json.dumps(groups(),sort_keys=True).encode()).hexdigest()}
    key=unquote(load_secrets()['data_go_kr_service_key']);session=requests.Session()
    cases=[(n,c,ym) for n,c in REPRESENTATIVES.items() for ym in ['200601','202112']]+[('gyeongnam_legacy',c,'200601') for c in ['48110','48160','48190']]
    try:
        for name,code,ym in cases:
            dest=OUT/'probes'/f'{name}_{code}_{ym}.xml'
            if dest.exists():raw=dest.read_text('utf-8')
            else:
                previous.reserve_call(cap)
                try:r=session.get(worker.BASE,params={'serviceKey':key,'LAWD_CD':code,'DEAL_YMD':ym,'numOfRows':1000,'pageNo':1},timeout=40)
                except requests.RequestException:raise RuntimeError('NETWORK_ERROR_URL_SUPPRESSED') from None
                if r.status_code in (401,403,429):raise RuntimeError('HTTP_STOP_'+str(r.status_code))
                if r.status_code!=200:raise RuntimeError('HTTP_ERROR_'+str(r.status_code))
                raw=r.text;worker.parse_page(raw);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(raw,'utf-8');time.sleep(.35)
            total,items=worker.parse_page(raw)
            if name!='gyeongnam_legacy' and not total:raise RuntimeError('CURRENT_CODE_REPRESENTATIVE_EMPTY_'+name+'_'+ym)
            report['cases'].append({'region':name,'code':code,'month':ym,'totalCount':total,'stored_page1':len(items),'file':str(dest)})
        report.update(state='pilot_complete',completed=stamp());worker.save(OUT/'probe_report.json',report)
    except Exception as exc:
        report.update(state='stopped_error',reason=str(exc) if isinstance(exc,(ValueError,RuntimeError)) else type(exc).__name__);worker.save(OUT/'probe_report.json',report);raise
    return report
def run(cap):
    p=plan(cap);probe=read(OUT/'probe_report.json')
    assert probe['state']=='pilot_complete' and probe['group_fingerprint']==hashlib.sha256(json.dumps(p['groups'],sort_keys=True).encode()).hexdigest()
    worker.save(OUT/'previous_chungnam_batch_status.json',read(OLD/'batch_status.json'))
    state={'state':'running','pid':os.getpid(),'started':stamp(),'priority':p['priority'],'finished_groups':[],'target_period':'200601-202609','daily_known_call_cap':cap,'new_script':str(Path(__file__).resolve())}
    worker.save(OUT/'batch_status.json',state)
    try:
        for name,codes in p['groups'].items():
            base=OLD if name=='chungnam' else OUT;state.update(current_group=name,worker_status_file=str(base/'status.json'),updated=stamp());worker.save(OUT/'batch_status.json',state)
            worker.OUT=base;worker.LEDGER=LEDGER;worker.CODES={name:codes};sys.argv=[str(Path(__file__)),'--max-calls',str(cap)];worker.main()
            result=read(base/'status.json');state.update(last_worker=result,updated=stamp())
            if result['state']!='completed':state['state']=result['state'];worker.save(OUT/'batch_status.json',state);return
            state['finished_groups'].append(name);worker.save(OUT/'batch_status.json',state)
            if name=='chungnam':
                old=read(OLD/'batch_status.json');old.update(state='completed',finished_groups=list(read(OLD/'plan.json')['groups']),resumed_by=str(OUT/'batch_status.json'),updated=stamp());worker.save(OLD/'batch_status.json',old)
        state.update(state='completed',updated=stamp());worker.save(OUT/'batch_status.json',state)
    except Exception as exc:
        state.update(state='stopped_error',reason=str(exc) if isinstance(exc,(ValueError,RuntimeError)) else type(exc).__name__,updated=stamp());worker.save(OUT/'batch_status.json',state);raise
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=['plan','pilot','run'],default='plan');ap.add_argument('--max-calls',type=int,default=8000);a=ap.parse_args();assert 0<a.max_calls<=8000;OUT.mkdir(parents=True,exist_ok=True)
    if a.mode=='plan':print(json.dumps(plan(a.max_calls),ensure_ascii=False,indent=2));return
    with exclusive():
        result=pilot(a.max_calls) if a.mode=='pilot' else run(a.max_calls)
    if result:print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':
    try:main()
    except Exception as exc:
        print(json.dumps({'state':'stopped_error','reason':str(exc) if isinstance(exc,(ValueError,RuntimeError,AssertionError)) else type(exc).__name__},ensure_ascii=False),flush=True);raise SystemExit(1)
