from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
SOURCES = {
    'P1_park2023': 'https://www.ejrea.org/archive/view_article?pid=jrea-9-3-1',
    'P2_seomun2026': 'https://www.kpaj.or.kr/_PR/view/?aidx=50743&bidx=4543',
    'P5_son2025': 'https://www.kpaj.or.kr/_PR/view/?aidx=47897&bidx=4316',
    'P3_hfr2025_issue': 'https://researcher.hf.go.kr/researcher/sub04/sub05_3.do?articleNo=592609&attachNo=91197&mode=download',
}

def fetch(item):
    key, url = item
    try:
        response = requests.get(url, timeout=50)
        response.raise_for_status()
        if response.content.startswith(b'%PDF'):
            path = ROOT / (key + '.pdf')
            path.write_bytes(response.content)
            return {'id':key,'url':url,'file':path.name,'bytes':len(response.content)}
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        for tag in soup(['script','style','nav','header','footer']):
            tag.decompose()
        path = ROOT / (key + '.txt')
        path.write_text(soup.get_text('\n', strip=True), encoding='utf-8')
        return {'id':key,'url':url,'file':path.name,'bytes':path.stat().st_size}
    except Exception as error:
        return {'id':key,'url':url,'error':str(error)}

with ThreadPoolExecutor(max_workers=4) as pool:
    results = list(pool.map(fetch, SOURCES.items()))
(ROOT / 'fetch_receipt.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(results,ensure_ascii=False,indent=2))
