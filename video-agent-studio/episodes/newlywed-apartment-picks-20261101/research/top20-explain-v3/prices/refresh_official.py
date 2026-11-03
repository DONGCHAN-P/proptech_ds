"""승인된 무료 국토부 GET만 호출합니다. 재시도·전역 캐시 변경은 없습니다."""
import argparse
import hashlib
import json
import math
import sys
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
ENDPOINT = 'https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev'
LOG = HERE/'api_request_log.json'
LIMIT = 200
EXECUTION_SCOPE = 'default'


def stamp():
    return datetime.now(ZoneInfo('Asia/Seoul')).isoformat()


def save(path,data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def fetch(code,ym,page=1,manual_network_probe=False,request_reason='승인된 20지역 2026년5~10월 수집'):
    ledger=json.loads(LOG.read_text(encoding='utf-8')) if LOG.exists() else {'authorization':'parent bounded FREE 20regions May-Oct <=200 HTTP, no retry', 'limit':LIMIT,'requests':[]}
    if len(ledger['requests'])>=LIMIT:
        return {'status':'stopped_request_limit','count':len(ledger['requests'])}
    resolved=ledger.get('connection_error_resolved_at_sequence',0)
    unresolved=[r for r in ledger['requests'] if r.get('fatal') and r['sequence']>resolved]
    if unresolved and not (manual_network_probe and all(r['status']=='network_error' for r in unresolved)):
        return {'status':'stopped_previous_error','count':len(ledger['requests'])}
    if not manual_network_probe and any(r['lawd_cd']==code and r['contract_month']==ym and r['page']==page and r['status']=='ok' for r in ledger['requests']):
        return {'status':'existing_response_reused','lawd_cd':code,'contract_month':ym,'page':page}
    secrets=json.loads((ROOT/'config/secrets.json').read_text(encoding='utf-8-sig'))
    key=urllib.parse.unquote(secrets.get('data_go_kr_service_key',''))
    if not key:return {'status':'missing_existing_key','fatal':True}
    entry={'sequence':len(ledger['requests'])+1,'started_at':stamp(),'lawd_cd':code,'contract_month':ym,'page':page,'status':'attempt_started','automatic_retry':False,
           'manual_network_probe':manual_network_probe,'execution_scope':'require_escalated' if manual_network_probe else EXECUTION_SCOPE,'request_reason':request_reason}
    ledger['requests'].append(entry)
    save(LOG,ledger)
    try:
        # requests의 기본 재시도 횟수는 0입니다. 기존 전역 수집기를 실행하지 않습니다.
        response=requests.get(ENDPOINT,params={'serviceKey':key,'LAWD_CD':code,'DEAL_YMD':ym,'numOfRows':1000,'pageNo':page},timeout=(12,35),allow_redirects=False)
    except Exception as exc:
        # Exception URLs can contain a credential; do not stringify exceptions.
        chain=[];current=exc;seen=set()
        while current is not None and id(current) not in seen and len(chain)<8:
            seen.add(id(current))
            chain.append({'type':type(current).__name__,'errno':getattr(current,'errno',None),'winerror':getattr(current,'winerror',None)})
            current=getattr(current,'reason',None) or current.__cause__ or current.__context__
        entry.update(status='network_error',error_type=type(exc).__name__,error_chain=chain,fatal=True,finished_at=stamp())
        save(LOG,ledger)
        return entry
    entry.update(http_status=response.status_code,finished_at=stamp())
    body=response.content
    if key.encode() in body or urllib.parse.quote(key,safe='').encode() in body:
        entry.update(status='credential_echo_response_not_saved',fatal=True)
        save(LOG,ledger)
        return entry
    raw=HERE/'raw'
    raw.mkdir(exist_ok=True)
    filename=f'{entry["sequence"]:03d}_{code}_{ym}_p{page}_{datetime.now().strftime("%Y%m%dT%H%M%S")}.xml'
    path=raw/filename
    with path.open('xb') as f:f.write(body)
    entry.update(response_file=str(path.relative_to(HERE)),response_sha256=hashlib.sha256(body).hexdigest(),response_bytes=len(body))
    try:
        xml=ET.fromstring(body)
        result_code=xml.findtext('.//resultCode') or xml.findtext('.//returnReasonCode')
        msg=xml.findtext('.//resultMsg') or xml.findtext('.//returnAuthMsg') or ''
        # Only protocol codes and short messages; keys/URLs are never logged.
        msg=msg.replace(key,'[REDACTED]')
        if 'http' in msg.lower() or 'servicekey' in msg.lower():msg='protocol_error_message_omitted'
        entry.update(result_code=result_code,result_message=msg[:100],total_count=int(xml.findtext('.//totalCount') or 0),rows=len(xml.findall('.//item')))
        entry['field_names']=sorted({ch.tag for item in xml.findall('.//item') for ch in item})
        entry['contract_years']=sorted({item.findtext('dealYear') for item in xml.findall('.//item') if item.findtext('dealYear')})
        entry['status']='ok' if response.status_code==200 and result_code in ['000','00','0'] else 'api_or_http_error'
    except (ET.ParseError,ValueError):
        entry.update(status='unparseable_response')
    entry['fatal']=entry['status']!='ok'
    if manual_network_probe and entry['status']=='ok':
        ledger['connection_error_resolved_at_sequence']=entry['sequence']
    save(LOG,ledger)
    return entry


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--collect',action='store_true')
    parser.add_argument('--manual-network-probe',action='store_true')
    parser.add_argument('--escalated-network',action='store_true')
    parser.add_argument('--probe-current-r01',action='store_true')
    args=parser.parse_args()
    EXECUTION_SCOPE='require_escalated' if args.escalated_network else 'default'
    if args.probe_current_r01:
        results=[]
        for code in ['28275','28290']:
            result=fetch(code,'202605',request_reason='총괄 수동 지시: 구28260 5월0건에 대해 현행코드 과거계약 재매핑 비교 조회')
            results.append(result)
            if result.get('fatal'):break
        positive=len(results)==2 and all(r.get('status')=='ok' and r.get('rows',0)>0 and r.get('contract_years')==['2026'] for r in results)
        save(HERE/'api_geography_feasibility.json',{'checked_at':stamp(),'old_code_28260_may_rows':0,'probes':results,'current_codes_all_months_confirmed_by_may_response':positive,
            'authorized_inference':'총괄이 현행 두 코드의 과거 계약 응답을 확인하면 R01 전기간 현행코드 합산을 허용했습니다. 과거 법적 명칭 변경일 자체를 앞당긴다는 뜻은 아닙니다.'})
        print(json.dumps({'current_code_retroactive_response':positive,'probes':[{k:v for k,v in r.items() if k in ['sequence','lawd_cd','rows','status','total_count','result_code']} for r in results]},ensure_ascii=False))
    elif args.manual_network_probe:
        r=fetch('11710','202610',manual_network_probe=True)
        save(HERE/'api_manual_network_feasibility.json',{'checked_at':stamp(),'execution_scope':'require_escalated','result':r})
        print(json.dumps({k:v for k,v in r.items() if k in ['sequence','status','http_status','result_code','result_message','rows','total_count','error_type','error_chain','contract_years']},ensure_ascii=False))
    elif not args.collect:
        results=[]
        for ym in ['202610','202605']:
            r=fetch('11710',ym)
            results.append(r)
            if r.get('fatal'):break
        save(HERE/'api_feasibility.json',{'checked_at':stamp(),'probe_results':results,
             'existing_daily_usage_ledger':'기존 수집기의 전역 일별 호출 집계는 확인되지 않습니다. 이 작업의 호출은 별도 로그로 전수 기록합니다.',
             'global_collector_executed':False,'paid_api':False})
        print(json.dumps({'probe':[{k:v for k,v in r.items() if k in ['sequence','status','http_status','result_code','result_message','rows','total_count','error_type','contract_years']} for r in results]},ensure_ascii=False))
    else:
        ranking=json.loads((HERE.parents[2]/'research/top20-8min-v2/price_context.json').read_text(encoding='utf-8'))['geography_crosswalk']
        targets=[]
        geography_path=HERE/'api_geography_feasibility.json'
        current_all_months=geography_path.exists() and json.loads(geography_path.read_text(encoding='utf-8')).get('current_codes_all_months_confirmed_by_may_response')
        for r in ranking:
            for ym in ['202605','202606','202607','202608','202609','202610']:
                lawds=(['28275','28290'] if current_all_months else (['28260'] if ym<'202607' else ['28275','28290'])) if r['region_id']=='R01' else r['current_cache_codes']
                targets.extend((code,ym) for code in lawds)
        failed=None
        for code,ym in targets:
            first=fetch(code,ym)
            if first.get('fatal') or first['status'].startswith('stopped'):
                failed=first;break
            if first['status']=='existing_response_reused':
                first=next(r for r in json.loads(LOG.read_text(encoding='utf-8'))['requests'] if r['lawd_cd']==code and r['contract_month']==ym and r['page']==1 and r['status']=='ok')
            if first.get('total_count',0)==0:
                failed={'status':'empty_target_month','lawd_cd':code,'contract_month':ym};break
            for page in range(2,math.ceil(first['total_count']/1000)+1):
                result=fetch(code,ym,page)
                if result.get('fatal') or result['status'].startswith('stopped'):
                    failed=result;break
            if failed:break
        ledger=json.loads(LOG.read_text(encoding='utf-8'))
        receipt={'finished_at':stamp(),'target_code_months':len(targets),'request_count':len(ledger['requests']),'complete':failed is None,'failure':failed}
        save(HERE/'api_collection_receipt.json',receipt)
        print(json.dumps({k:v for k,v in receipt.items() if k!='failure'}|{'failure_status':failed.get('status') if failed else None},ensure_ascii=False))
