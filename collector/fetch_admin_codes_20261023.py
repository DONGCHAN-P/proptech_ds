"""Fetch and inspect the official public code archive; never execute its content."""
from pathlib import Path
import csv
import hashlib
import io
import json
import zipfile
import xml.etree.ElementTree as ET
import requests

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'raw/rtms_trade_expansion/admin_codes_20261023'
OUT.mkdir(parents=True,exist_ok=True)
URL='https://mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_00146280tlU2Y2B&fileSn=0'
path=OUT/'jscode20260701.zip'
if not path.exists():
    response=requests.get(URL,timeout=40)
    response.raise_for_status()
    assert zipfile.is_zipfile(io.BytesIO(response.content)), 'Official attachment is not a readable ZIP'
    path.write_bytes(response.content)
with zipfile.ZipFile(path) as z:
    names=z.namelist()
    chosen=[n for n in names if 'kikcd_b' in n.lower() and not n.lower().endswith(('.xlsx','.xls'))]
    if not chosen:
        print(json.dumps({'members':names},ensure_ascii=False))
        raise SystemExit('Inspect official archive formats before mapping')
    data=z.read(chosen[0])
    for enc in ('utf-8-sig','cp949','utf-16'):
        try:
            text=data.decode(enc)
            break
        except UnicodeError:
            continue
    (OUT/'legal_dong_codes.txt').write_text(text,encoding='utf8')
    workbook_name=next(n for n in names if 'kikcd_b' in n.lower() and n.lower().endswith('.xlsx'))
    with zipfile.ZipFile(io.BytesIO(z.read(workbook_name))) as wb:
        shared=[]
        if 'xl/sharedStrings.xml' in wb.namelist():
            shared=[''.join(t.text or '' for t in si.findall('.//{*}t')) for si in ET.fromstring(wb.read('xl/sharedStrings.xml')).findall('{*}si')]
        rows=[]
        for row in ET.fromstring(wb.read('xl/worksheets/sheet1.xml')).findall('.//{*}sheetData/{*}row'):
            vals=[]
            for c in row.findall('{*}c'):
                col=''.join(ch for ch in c.attrib['r'] if ch.isalpha())
                idx=0
                for ch in col:
                    idx=idx*26+ord(ch)-64
                while len(vals)<idx:
                    vals.append(None)
                v=c.findtext('{*}v')
                vals[idx-1]=shared[int(v)] if c.attrib.get('t')=='s' and v is not None else ''.join(t.text or '' for t in c.findall('.//{*}t')) if c.attrib.get('t')=='inlineStr' else v
            rows.append(vals)
    districts=[]
    for r in rows[1:]:
        if r[0] is None:
            continue
        code=str(int(r[0])) if isinstance(r[0],(int,float)) else str(r[0]).strip()
        if len(code)==10 and code.endswith('00000') and code[2:5]!='000':
            districts.append({'code':code[:5],'fields':r})
    (OUT/'district_codes.json').write_text(json.dumps(districts,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    target_rows=[r for r in districts if any(k in ' '.join(str(v or '') for v in r['fields']) for k in ('광산구','광주동구','광주서구','광주남구','광주북구','울산광역시','충청북도','충청남도'))]
    receipt={'source_page':'https://mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=127039','download_url':URL,'effective_date':'2026-07-01','sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size,'archive_member':workbook_name,'columns':rows[0],'rows':len(rows)-1,'districts':len(districts),'target_district_rows':target_rows}
    (OUT/'source_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    # Exact district-level rows are selected after inspecting the official header.
    print(json.dumps(receipt,ensure_ascii=False,indent=2))
