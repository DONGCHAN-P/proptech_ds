import zipfile, xml.etree.ElementTree as ET, json, statistics, hashlib
from pathlib import Path
root=Path(__file__).parent
path=root/'ilsan_official.xlsx'
ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
with zipfile.ZipFile(path) as z:
    strings=[''.join(x.itertext()) for x in ET.fromstring(z.read('xl/sharedStrings.xml'))]
    sheet=ET.fromstring(z.read('xl/worksheets/sheet2.xml'))
    cells={}
    for cell in sheet.findall('.//s:c',ns):
        value=cell.find('s:v',ns)
        if value is not None:
            cells[cell.attrib['r']]=strings[int(value.text)] if cell.attrib.get('t')=='s' else value.text
def seconds(value): return round(float(value)*86400)
def clock(value):
    s=seconds(value)%86400
    return f'{s//3600:02}:{s//60%60:02}:{s%60:02}'
out={'source_url':'https://www.korail.com/file/cubedata/COMMON/jfile/202508/06/202508061987eaed712820.xlsx','list_url':'https://www.korail.com/com/userBoard.do?mode=list&schBcid=ticketTable','board_id':21101,'board_title':'일산선 시각표(2022.8.1.부터)','uploaded_on':'2025-08-06','checked_on':'2026-10-16','sheet':'일산(3호)선 평일_하행','sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'method':'같은 열차번호 열(column)의 원흥 출발(row21)부터 목적지 도착(row40/44/66) 차감; 07:00~08:59 출발 전 열차','results':[]}
for name,row in [('연신내',28),('경복궁',40),('종로3가',44),('교대',66)]:
    samples=[]
    for address,value in cells.items():
        if not address.endswith('21') or not address[:-2].isalpha(): continue
        column=address[:-2]
        try:
            depart=seconds(value)
            if not 7*3600<=depart<9*3600: continue
            arrive=cells[column+str(row)]
            duration=(seconds(arrive)-depart)/60
            samples.append({'train':cells.get(column+'3'),'departure':clock(value),'arrival':clock(arrive),'minutes':duration,'from_cell':address,'to_cell':column+str(row)})
        except (ValueError,KeyError): continue
    vals=[x['minutes'] for x in samples]
    out['results'].append({'destination':name,'n':len(vals),'minimum':min(vals),'maximum':max(vals),'median':statistics.median(vals),'samples':samples})
(root/'ilsan_calculation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
for r in out['results']:
    print(r['destination'],r['n'],r['minimum'],r['maximum'],r['median'],r['samples'][:2])
