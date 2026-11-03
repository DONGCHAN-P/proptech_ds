"""Bounded, read-only public RTMS pilot. Never log keys or request URLs."""
import sys, json, math
from pathlib import Path
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
from urllib.parse import unquote
import requests

BASE = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(BASE))
from common import load_secrets

OUT = Path(__file__).with_name('data_pilot_results.json')
MAX_REQUESTS = 12
count = 0
result = {'checked_on': '2026-10-20', 'max_requests': MAX_REQUESTS,
 'purpose': 'presence_and_pagination_only_not_price_statistics',
 'units': {'dealAmount': '만원', 'deposit': '만원', 'monthlyRent': '만원/월', 'excluUseAr': '㎡'},
 'queries': [], 'errors': []}

try:
    key = unquote(load_secrets()['data_go_kr_service_key'])
except Exception as e:
    result['errors'].append({'stage':'credentials','error_type':type(e).__name__})
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('credentials unavailable; recorded safe error type')
    raise SystemExit(0)

targets = [('11710', '서울 송파 잠실엘스', ['엘스']),
           ('41117', '수원 광교자연앤힐스테이트', ['자연앤힐스테이트'])]
for code,label,names in targets:
 for ym in ['201601','202609']:
  for kind,svc in [('trade','RTMSDataSvcAptTrade'),('rent','RTMSDataSvcAptRent')]:
   q={'district':code,'candidate':label,'contract_month':ym,'kind':kind,
      'pages':[],'totalCount':None,'received_rows':0,'matched_rows':[],
      'source_endpoint':f'https://apis.data.go.kr/1613000/{svc}/get{svc}'}
   page=1; expected=None
   while count < MAX_REQUESTS:
    count+=1
    try:
     r=requests.get(q['source_endpoint'],params={'serviceKey':key,'LAWD_CD':code,
       'DEAL_YMD':ym,'numOfRows':1000,'pageNo':page},timeout=35)
     if r.status_code!=200:
      q['error']={'http_status':r.status_code}; break
     root=ET.fromstring(r.content)
     rc=root.findtext('.//resultCode')
     if rc not in ('000','00','0'):
      q['error']={'resultCode':rc,'reason':'non_success_response_body_not_logged'}; break
     total=root.findtext('.//totalCount')
     if total is None:
      q['error']={'reason':'missing_totalCount'}; break
     expected=int(total); q['totalCount']=expected
     rows=[{x.tag:(x.text or '').strip() for x in item} for item in root.findall('.//item')]
     q['pages'].append({'pageNo':page,'rows':len(rows)})
     q['received_rows']+=len(rows)
     for row in rows:
      if not any(n in row.get('aptNm','') for n in names): continue
      try: area=float(row.get('excluUseAr',''))
      except ValueError: continue
      if not 84<=area<85: continue
      q['matched_rows'].append({k:row.get(k) for k in
        ['aptNm','aptSeq','umdNm','jibun','excluUseAr','floor','dealYear','dealMonth','dealDay',
         'dealAmount','deposit','monthlyRent','contractType','contractTerm','useRRRight',
         'cdealType','cdealDay','dealingGbn'] if k in row})
     if q['received_rows']>=expected or not rows: break
     page+=1
    except Exception as e:
     q['error']={'error_type':type(e).__name__,'reason':'details_omitted_to_protect_key'}; break
   q['pagination_complete']=expected is not None and q['received_rows']==expected
   q['matched_count']=len(q['matched_rows'])
   q['area_rule']='84 <= exclusive_area_m2 < 85; exact values retained, not assumed identical'
   result['queries'].append(q)
   result['actual_requests']=count
   OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
   if q.get('error'):
    print(json.dumps({'stopped_after_first_error':True,'requests':count,'error':q['error']}))
    raise SystemExit(0)
result['actual_requests']=count
result['limitations']=['September 2026 is a completed calendar month but late reports/cancellations remain possible.',
 'Single-month presence pilot; not long-run statistics or strategy winners.',
 'Exact exclusive area, floor, contract status must be matched before comparison.']
OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'requests':count,'queries':[{'candidate':q['candidate'],'month':q['contract_month'],
 'kind':q['kind'],'total':q['totalCount'],'received':q['received_rows'],
 'complete':q['pagination_complete'],'matches':q['matched_count'],'error':q.get('error')} for q in result['queries']]},ensure_ascii=False))
