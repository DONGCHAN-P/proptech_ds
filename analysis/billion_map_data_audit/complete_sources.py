from pathlib import Path
import json,hashlib,time,math,datetime,xml.etree.ElementTree as E,sys
from collections import Counter
import requests
from urllib.parse import unquote
ROOT=Path(__file__).resolve().parents[3] if False else Path.cwd()
OUT=ROOT/'video-agent-studio/episodes/capital-10eok-map-20261017/research/source-completion-v1';OUT.mkdir(parents=True,exist_ok=True)
API='https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev'
def sha(b):return hashlib.sha256(b).hexdigest()
def parse(b):
 r=E.fromstring(b);rc=(r.findtext('.//resultCode') or '').strip()
 if rc not in ['000','00','0']:raise RuntimeError('API response failure code '+rc[:8])
 rows=[{x.tag:(x.text or '').strip() for x in i} for i in r.findall('.//item')]
 return {'total':int(r.findtext('.//totalCount') or 0),'page':int(r.findtext('.//pageNo') or 1),'rows':rows}
def fp(r):return sha(json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())
def run(mode,cap):
 key=json.loads((ROOT/'config/secrets.json').read_text(encoding='utf8')).get('data_go_kr_service_key'); assert key; key=unquote(key)
 import pandas as pd
 table=pd.read_csv(ROOT/'analysis/billion_map_data_audit/truncated_raw_files.csv',dtype={'code':str,'ym':str}); pairs=[('11350','200603'),('11350','200609')] if mode=='pilot' else list(zip(table.code,table.ym))
 journal=OUT/'requests.jsonl'; used=sum(1 for _ in journal.open(encoding='utf8')) if journal.exists() else 0; executed=0
 receipts=[]
 def fetch(code,ym,page,path):
  nonlocal executed,used
  if executed>=cap or used>=850:raise RuntimeError('approved call cap reached')
  time.sleep(.38);executed+=1;used+=1
  begin=datetime.datetime.now(datetime.timezone.utc).isoformat();record={'request_index':used,'code':code,'ym':ym,'page':page,'fetched_at':begin}
  try:
   resp=requests.get(API,params={'serviceKey':key,'LAWD_CD':code,'DEAL_YMD':ym,'numOfRows':1000,'pageNo':page},timeout=45)
   record['http_status']=resp.status_code
   if resp.status_code!=200:
    try:
     er=E.fromstring(resp.content); record['api_result_code']=er.findtext('.//resultCode') or er.findtext('.//returnReasonCode'); msg=er.findtext('.//resultMsg') or er.findtext('.//returnAuthMsg') or er.findtext('.//errMsg') or ''; record['api_general_message']=msg.replace(key,'[REDACTED]')[:160]
    except Exception: record['api_general_message']='non-XML HTTP error; body omitted'
    raise RuntimeError('HTTP status '+str(resp.status_code))
   b=resp.content;path.write_bytes(b);d=parse(b);record.update({'file':str(path.relative_to(ROOT)),'sha256':sha(b),'total':d['total'],'items':len(d['rows']),'status':'ok'})
   if d['page']!=page:raise RuntimeError('response page number mismatch')
  except Exception as e:
   record['status']='failed';record['error_type']=type(e).__name__
   with journal.open('a',encoding='utf8') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
   raise RuntimeError('Safe collection stop: '+type(e).__name__) from None
  with journal.open('a',encoding='utf8') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
  return d,record
 for code,ym in pairs:
  folder=OUT/'raw'/ym[:4]/ym[4:]/code;folder.mkdir(parents=True,exist_ok=True);receipt=folder/'receipt.json'
  if receipt.exists():
   old=json.loads(receipt.read_text(encoding='utf8'))
   if old.get('complete'):receipts.append(old);continue
  first,fr=fetch(code,ym,1,folder/'page-0001.xml');total=first['total'];pages=math.ceil(total/1000) or 1;allrows=list(first['rows']);prs=[fr];seen=set(map(fp,allrows));cross=0
  for page in range(2,pages+1):
   d,pr=fetch(code,ym,page,folder/f'page-{page:04d}.xml');prs.append(pr)
   if d['total']!=total:raise RuntimeError('totalCount changed within pagination')
   fs=list(map(fp,d['rows']));cross+=sum(f in seen for f in fs);seen.update(fs);allrows.extend(d['rows'])
  check,cr=fetch(code,ym,1,folder/'verify-page-0001.xml');prs.append(cr)
  if check['total']!=total or list(map(fp,check['rows']))!=list(map(fp,first['rows'])):raise RuntimeError('snapshot changed at final page1 recheck')
  if len(allrows)!=total:raise RuntimeError('all-pages row count does not equal totalCount')
  # Full payload equality is not an official transaction ID: preserve multiplicity, flag only.
  if cross: pass
  legacy=ROOT/f'raw/rtms_trade/{ym[:4]}/{ym[4:]}/{code}_{ym}.xml';prior=parse(legacy.read_bytes());ps=set(map(fp,prior['rows']));ns=set(map(fp,allrows));fields=sorted(set().union(*(r.keys() for r in allrows))); pc=Counter(map(fp,prior['rows']));nc=Counter(map(fp,allrows))
  rec={'code':code,'ym':ym,'complete':True,'pages':pages,'validation_calls':1,'totalCount':total,'actual_rows':len(allrows),'unique_full_payloads':len(ns),'identical_payload_extra_occurrences':len(allrows)-len(ns),'cross_page_shared_payload_patterns':cross,'multiplicity_preserved':True,'new_payload_occurrences':sum((nc-pc).values()),'old_payload_occurrences_not_in_new':sum((pc-nc).values()),'legacy_cached_rows':len(prior['rows']),'new_payload_fingerprints':len(ns-ps),'old_payloads_not_in_new':len(ps-ns),'source_fields':fields,'legacy_source_fields':sorted(set().union(*(r.keys() for r in prior['rows']))),'page_receipts':prs}
  receipt.write_text(json.dumps(rec,ensure_ascii=False,indent=2),encoding='utf8');receipts.append(rec);print(json.dumps({k:rec[k] for k in ['code','ym','pages','totalCount','new_payload_fingerprints','old_payloads_not_in_new']},ensure_ascii=False),flush=True)
 summary={'mode':mode,'completed_pairs':len(receipts),'new_requests':executed,'all_journal_requests':used,'cash_cost':0,'external_generation':0,'complete':len(receipts)==len(pairs),'receipts':[str((OUT/'raw'/r['ym'][:4]/r['ym'][4:]/r['code']/'receipt.json').relative_to(ROOT)) for r in receipts]};(OUT/f'{mode}_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(summary,ensure_ascii=False),flush=True)
if __name__=='__main__':
 try:run(sys.argv[1],int(sys.argv[2]))
 except Exception as e: print(json.dumps({'safe_failure':type(e).__name__,'reason':str(e) if isinstance(e,RuntimeError) else 'details omitted to protect credentials'}),flush=True);sys.exit(1)
