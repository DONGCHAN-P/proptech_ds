from pathlib import Path
import json,requests,xml.etree.ElementTree as ET,datetime
p=Path(__file__).parent/'price_raw';p.mkdir(exist_ok=True)
secrets=json.loads(Path('config/secrets.json').read_text(encoding='utf-8'))
endpoint='https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev'
for ym in ['202607','202608','202609']:
 try:
  r=requests.get(endpoint+'?serviceKey='+secrets['data_go_kr_service_key']+'&LAWD_CD=41450&DEAL_YMD='+ym+'&numOfRows=1000&pageNo=1',timeout=30)
  t=ET.fromstring(r.text);n=int(t.findtext('.//totalCount') or 0);cnt=len(t.findall('.//item'));code=t.findtext('.//resultCode');ok=r.status_code==200 and code in ('00','000') and n==cnt
  if ok:(p/f'41450_{ym}.xml').write_text(r.text,encoding='utf-8')
  (p/f'41450_{ym}.meta.json').write_text(json.dumps({'fetched_at':datetime.datetime.now().astimezone().isoformat(),'items':cnt,'total':n,'result_code':code,'complete':ok,'endpoint':endpoint}),encoding='utf-8')
  print(ym,ok,cnt)
 except Exception as e:print(ym,type(e).__name__)
