"""Exactly three free RTMS GETs; never print credentials, URLs with keys, or exceptions."""
from pathlib import Path
import datetime,json,requests,xml.etree.ElementTree as ET
out=Path(__file__).resolve().parent/'raw'
root=out.parents[5]
secrets=json.loads((root/'config/secrets.json').read_text(encoding='utf-8'))
endpoint='https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev'
for ym in ('202607','202608','202609'):
    try:
        r=requests.get(endpoint+'?serviceKey='+secrets['data_go_kr_service_key']+'&LAWD_CD=41281&DEAL_YMD='+ym+'&numOfRows=1000&pageNo=1',timeout=25)
        xml=ET.fromstring(r.text);code=xml.findtext('.//resultCode');n=int(xml.findtext('.//totalCount') or 0);items=len(xml.findall('.//item'))
        ok=r.status_code==200 and code in ('00','000') and n==items
        meta={'ym':ym,'http_status':r.status_code,'result_code':code,'total_count':n,'items':items,'complete_page':ok,'fetched_at':datetime.datetime.now().astimezone().isoformat(),'endpoint':endpoint,'lawd_cd':'41281'}
        if ok:(out/f'41281_{ym}.xml').write_text(r.text,encoding='utf-8')
        (out/f'41281_{ym}.meta.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
        print(ym,'complete' if ok else 'incomplete',n,items)
    except Exception as e:
        print(ym,'request failed',type(e).__name__)
        (out/f'41281_{ym}.failure.json').write_text(json.dumps({'error_type':type(e).__name__,'ym':ym}),encoding='utf-8')
