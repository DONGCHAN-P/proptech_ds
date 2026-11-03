"""Isolated, resumable RTMS history collector. Never prints URLs or credentials."""
import argparse,json,sys,time,os,math
from pathlib import Path
from datetime import datetime,timezone,timedelta
from urllib.parse import unquote
import xml.etree.ElementTree as ET
import requests
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from common import load_secrets
BASE='https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev'
CODES={'busan':'26110 26140 26170 26200 26230 26260 26290 26320 26350 26380 26410 26440 26470 26500 26530 26710'.split(),'daegu':'27110 27140 27170 27200 27230 27260 27290 27710 27720 47720'.split(),'daejeon':'30110 30140 30170 30200 30230'.split()}
OUT=ROOT/'raw/rtms_trade_expansion/three_cities'; KST=timezone(timedelta(hours=9))
LEDGER=OUT

def stamp(): return datetime.now(KST).isoformat()
def save(p,d):
 p.parent.mkdir(parents=True,exist_ok=True); t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
 for attempt in range(10):
  try:
   os.replace(t,p);return
  except PermissionError:
   if attempt==9:raise
   time.sleep(.1*(attempt+1))
def parse_page(text):
 root=ET.fromstring(text); code=root.findtext('.//resultCode')
 if code not in ('000','00','0'): raise ValueError('API_RESULT_'+str(code))
 total=root.findtext('.//totalCount')
 if total is None: raise ValueError('MISSING_TOTAL')
 return int(total),root.findall('.//items/item')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--max-calls',type=int,default=9000);ap.add_argument('--limit-months',type=int);a=ap.parse_args()
 OUT.mkdir(parents=True,exist_ok=True); lock=OUT/'running.lock'
 try: fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.write(fd,str(os.getpid()).encode());os.close(fd)
 except FileExistsError: raise SystemExit('Existing collection lock; check process before restarting')
 status={'state':'running','started':stamp(),'complete_months':0,'rows':0,'errors':[]}; key=unquote(load_secrets()['data_go_kr_service_key']);session=requests.Session();done=0
 def report(): status['updated']=stamp();save(OUT/'status.json',status)
 try:
  for year in range(2026,2005,-1):
   for month in range(12,0,-1):
    ym=f'{year}{month:02}'
    if ym>'202609':continue
    for city,codes in CODES.items():
     for code in codes:
      folder=OUT/city/ym;meta=folder/f'{code}.meta.json'
      if meta.exists() and json.loads(meta.read_text(encoding='utf8')).get('complete'): continue
      folder.mkdir(parents=True,exist_ok=True);status.update(city=city,code=code,month=ym);report();allitems=[];expected=None;page=1
      while True:
       dest=folder/f'{code}.page{page}.xml'
       if dest.exists(): text=dest.read_text(encoding='utf8')
       else:
        for attempt in range(3):
         day=datetime.now(KST).strftime('%Y-%m-%d'); ledger=LEDGER/f'calls-{day}.json'; used=json.loads(ledger.read_text()).get('calls',0) if ledger.exists() else 0
         if used>=a.max_calls: status['state']='local_call_cap_reached';report();return
         save(ledger,{'calls':used+1,'updated':stamp(),'note':'This collector only; external API use unknown'})
         try:
          response=session.get(BASE,params={'serviceKey':key,'LAWD_CD':code,'DEAL_YMD':ym,'numOfRows':1000,'pageNo':page},timeout=40)
          if response.status_code in (401,403,429): raise ValueError('HTTP_STOP_'+str(response.status_code))
          response.raise_for_status();text=response.text;parse_page(text);dest.write_text(text,encoding='utf8');time.sleep(.35);break
         except ValueError: raise
         except requests.RequestException:
          if attempt==2:raise RuntimeError('NETWORK_RETRY_EXHAUSTED') from None
          time.sleep(2**attempt)
       total,items=parse_page(text)
       if expected is None:expected=total
       if total!=expected:raise ValueError('TOTAL_CHANGED_RETRY_MONTH')
       allitems.extend(items)
       if len(allitems)==expected:break
       if len(allitems)>expected or not items:raise ValueError('PAGE_COUNT_MISMATCH')
       page+=1
      save(meta,{'city':city,'code':code,'ym':ym,'totalCount':expected,'stored_rows':len(allitems),'pages':page,'complete':True,'collected_at':stamp(),'gunwi_note':'27720 and 47720 kept separate; do not aggregate without deduplication'})
      status['complete_months']+=1;status['rows']+=len(allitems);done+=1;report()
      if done%25==0:print(json.dumps(status,ensure_ascii=False),flush=True)
      if a.limit_months and done>=a.limit_months:status['state']='pilot_complete';report();return
  status['state']='completed';report()
 except Exception as e:
  status['state']='stopped_error';status['errors'].append({'type':type(e).__name__,'reason':str(e) if isinstance(e,(ValueError,RuntimeError)) else 'See error type; URL suppressed'});report();print(json.dumps(status,ensure_ascii=False),flush=True)
 finally:lock.unlink(missing_ok=True)
if __name__=='__main__':main()
