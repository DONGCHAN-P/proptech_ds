import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5];EP=ROOT/'video-agent-studio/episodes/namyangju-wangsuk-20261014'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
facts={f['claim_id']:f for f in read(EP/'research/map-led-v5/facts.json')}
blocks={b['candidate_id']:b for b in read(EP/'research/map-led-v5/analysis.json')['blocks']}
public=[]
for bid,name,area,pattern in [('W1-B17','왕숙1 B17',84.91,r'주택가격은(\d+)원'),('W2-A1','왕숙2 A1',84.67,r'84A(\d+)원'),('W2-A3','왕숙2 A3',84.75,r'84A(\d+)원')]:
    fact=facts[bid+'-PRICE'];amount=int(re.search(pattern,fact['sentence']).group(1));public.append({'id':bid,'name':name,'area':area,'type':'84A','price_krw':amount,'statistic':'공고 기준층 기본형','floor':'5층 이상','date':blocks[bid]['publication_date'],'kind':'public_sale','claim_id':fact['claim_id'],'source_url':fact['source_url'],'basis':fact['evidence_location'],'qualification':'확장·선택품목·세금 별도; 실거래·수익 아님'})
local=[]
for f in read(EP/'research/alternatives-v5/comparison.json')['facts']:
    if f.get('claim_id') not in ['ALT-001','ALT-002','ALT-003']:continue
    local.append({'id':f['claim_id'],'name':f['name'],'area':'83≤전용<85㎡','price_krw':round(f['median_manwon']*10000),'statistic':'수집 실거래 중위','floor':'5층 이상','date':'2026.7~9 계약','n':f['n'],'build_year':f['build_year'],'kind':'resale','source_url':f['source_url'],'qualification':'해제표시 제외; 면적·층·동·향·연식 차이 미보정','range_krw':[round(x*10000) for x in f['range_manwon']]})
out=read(EP/'research/outside-comparisons-v6/comparison.json');cnfact=next(f for f in read(EP/'research/outside-comparisons-v6/facts.json')['facts'] if f['claim_id']=='OUT-CN-S5-PRICE');cp=cnfact['price']
outside=public+[{'id':'changneung-s5','name':'창릉 S5','area':cp['exclusive_area_sqm'],'type':'84A','price_krw':cp['amount_krw'],'statistic':'공고 기준층 기본형','floor':cp['floor'],'date':cnfact['as_of'],'kind':'public_sale','claim_id':cnfact['claim_id'],'source_url':cnfact['source_url'],'qualification':'확장·선택품목·세금 별도; 원공고일 다름'}]
data={'public_rows':public,'local_rows':local,'outside_rows':outside,'outside':out,'source_rule':'B17 uses verified representative floor price644110000, not web average640068000; Gyosan51~59 excluded from84chart','readiness':'facts-bound, final caption/voice timing pending'}
(ROOT/'video/public/namyangju-map-led-v6/comparison_assets.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
print('prepared',len(public),'public',len(local),'resale',len(outside),'outside rows; no API')
