"""Resume approved extra history in isolation; account for every API request."""
from pathlib import Path
from datetime import datetime
from urllib.parse import unquote
import argparse
import json
import os
import sys
import requests

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from common import load_secrets
import collector.collect_three_cities as worker

OUT=ROOT/'raw/rtms_trade_expansion/additional_20261023'
ADMIN=ROOT/'raw/rtms_trade_expansion/admin_codes_20261023/district_codes.json'
LEDGER=ROOT/'raw/rtms_trade_expansion/three_cities'
OLD_GWANGJU={'동구':'29110','서구':'29140','남구':'29155','북구':'29170','광산구':'29200'}

def groups():
    rows=json.loads(ADMIN.read_text(encoding='utf8'))
    gj={r['fields'][2]:r['code'] for r in rows if r['code'].startswith('12') and r['fields'][2] in OLD_GWANGJU}
    assert set(gj)==set(OLD_GWANGJU) and len(set(gj.values()))==5
    def leaf(prefix):
        selected=[r for r in rows if r['code'].startswith(prefix)]
        return [r['code'] for r in selected if not any(x['code']!=r['code'] and str(x['fields'][2]).startswith(str(r['fields'][2])+' ') for x in selected)]
    # Historical aliases are preserved separately by code; no direct regional sum.
    return {'gwangju':[gj[n] for n in OLD_GWANGJU], 'ulsan':leaf('31'),
            'chungbuk':leaf('43')+['43710'],
            'chungnam':leaf('44')+['44130','44730','44830']}

def stamp():
    return datetime.now(worker.KST).isoformat()

def reserve_call(cap):
    path=LEDGER/f'calls-{datetime.now(worker.KST):%Y-%m-%d}.json'
    ledger=json.loads(path.read_text(encoding='utf8')) if path.exists() else {'calls':0}
    if ledger['calls']>=cap:
        raise RuntimeError('LOCAL_CALL_CAP_REACHED')
    worker.save(path,{'calls':ledger['calls']+1,'updated':stamp(),'note':'Known expansion collectors only; other account API use unknown'})

def pilot(cap):
    g=groups(); gj=g['gwangju'][list(OLD_GWANGJU).index('광산구')]
    key=unquote(load_secrets()['data_go_kr_service_key'])
    cases=[('gwangju_old','29200','202112'),('gwangju_current',gj,'202112'),
           ('gwangju_current_2006',gj,'200601'),('ulsan','31140','200601'),
           ('chungbuk','43111','200601')]
    report={'started':stamp(),'groups':g,'cases':[],'state':'running'}
    for label,code,ym in cases:
        reserve_call(cap)
        try:
            response=requests.get(worker.BASE,params={'serviceKey':key,'LAWD_CD':code,'DEAL_YMD':ym,'numOfRows':1000,'pageNo':1},timeout=35)
            if response.status_code in (401,403,429):
                raise ValueError('HTTP_STOP_'+str(response.status_code))
            response.raise_for_status()
            total,items=worker.parse_page(response.text)
            dest=OUT/'probes'/f'{label}_{code}_{ym}.xml'
            dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_text(response.text,encoding='utf8')
            report['cases'].append({'label':label,'code':code,'ym':ym,'totalCount':total,'stored_page1':len(items),'path':dest.relative_to(ROOT).as_posix()})
        except requests.RequestException:
            report.update(state='stopped_error',reason='NETWORK_ERROR_URL_SUPPRESSED')
            worker.save(OUT/'probe_report.json',report)
            raise RuntimeError('NETWORK_ERROR_URL_SUPPRESSED') from None
        except (ValueError,RuntimeError) as exc:
            report.update(state='stopped_error',reason=str(exc))
            worker.save(OUT/'probe_report.json',report)
            raise
    report['gwangju_current_nonzero']=all(x['totalCount']>0 for x in report['cases'] if x['label'].startswith('gwangju_current'))
    report['state']='pilot_complete'
    report['completed']=stamp()
    worker.save(OUT/'probe_report.json',report)
    print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
    return report

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--mode',choices=('plan','pilot','run'),default='plan')
    ap.add_argument('--max-calls',type=int,default=8000)
    a=ap.parse_args()
    assert 0<a.max_calls<=8000
    OUT.mkdir(parents=True,exist_ok=True)
    g=groups()
    if a.mode=='plan':
        plan={'groups':g,'months':249,'from':'200601','to':'202609','maximum_known_daily_calls':a.max_calls,'code_source':str(ADMIN.relative_to(ROOT)),'legacy_aliases':{'43710':'Former Cheongwon, needs historical-boundary/dedup review','44130':'Cheonan parent historical candidate','44730':'Former Yeongi; not automatically current Chungnam geography','44830':'Former Dangjin county'},'credentials_logged':False}
        worker.save(OUT/'plan.json',plan)
        print(json.dumps(plan,ensure_ascii=False,indent=2))
        return
    lock=OUT/'batch_running.lock'
    try:
        fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
        os.write(fd,str(os.getpid()).encode());os.close(fd)
    except FileExistsError:
        raise SystemExit('Existing batch lock; verify its process before restarting')
    try:
        for old in (LEDGER/'running.lock',ROOT/'raw/rtms_trade_expansion/gwangju_sejong/running.lock'):
            if old.exists():
                raise RuntimeError('OTHER_KNOWN_COLLECTOR_LOCK_ACTIVE')
        if a.mode=='pilot':
            pilot(a.max_calls)
            return
        report=json.loads((OUT/'probe_report.json').read_text(encoding='utf8'))
        if report.get('state')!='pilot_complete' or not report.get('gwangju_current_nonzero'):
            raise RuntimeError('PASS_CURRENT_CODE_PILOT_BEFORE_BULK')
        status={'state':'running','started':stamp(),'priority':list(g),'finished_groups':[], 'full_period_target':'200601-202609','call_cap':a.max_calls}
        worker.save(OUT/'batch_status.json',status)
        worker.OUT=OUT
        worker.LEDGER=LEDGER
        for city,codes in g.items():
            status.update(current_group=city,updated=stamp())
            worker.save(OUT/'batch_status.json',status)
            worker.CODES={city:codes}
            sys.argv=[sys.argv[0],'--max-calls',str(a.max_calls)]
            worker.main()
            result=json.loads((OUT/'status.json').read_text(encoding='utf8'))
            if result['state']!='completed':
                status.update(state=result['state'],updated=stamp(),last_worker=result)
                worker.save(OUT/'batch_status.json',status)
                return
            status['finished_groups'].append(city)
            worker.save(OUT/'batch_status.json',status)
        status.update(state='completed',updated=stamp())
        worker.save(OUT/'batch_status.json',status)
    finally:
        lock.unlink(missing_ok=True)

if __name__=='__main__':
    try:
        main()
    except (ValueError,RuntimeError) as exc:
        print(json.dumps({'state':'stopped_error','reason':str(exc)},ensure_ascii=False))
        raise SystemExit(1)
