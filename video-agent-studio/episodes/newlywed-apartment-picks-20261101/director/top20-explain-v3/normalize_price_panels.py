"""Connect the verified API price pack to editor/map inputs without rounding."""
from pathlib import Path
from decimal import Decimal
import hashlib,json

D=Path(__file__).resolve().parent; E=D.parents[1]
P=E/'research/top20-explain-v3/prices/final-api-20261103-v2'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def display(value):
    amount=Decimal(str(value)); high=int(amount//10000); rest=amount-high*10000
    low=f'{rest:,.1f}'.removesuffix('.0')
    return (f'{high}억원' if not rest else f'{high}억{low}만원') if high else f'{low}만원'

def main():
    source=P/'map_price_inputs.json'; pack=read(source); values=read(P/'writer_price_values.json')
    byid={r['region_id']:r for r in values['regions']}; rows=[]
    assert len(pack['layers'])==len(byid)==20
    for row in pack['layers']:
        rid=row['region_id']; rep=row['marker']; v=byid[rid]
        assert v['median_manwon']==row['regional_fill_value_manwon'] and v['n']==row['regional_n']
        assert v['representative']['median_manwon']==rep['median_manwon'] and rep['n']>=5
        assert rep['coordinate_verified'] and rep['point_in_2024_target_geometry'] and rep['point_in_official_polygon']
        rows.append({'region_id':rid,'scene_id':row['scene_id'],'rank':row['rank'],'region':row['region'],'province':row['province'],
                     'median_manwon':row['regional_fill_value_manwon'],'display_price':display(row['regional_fill_value_manwon']),
                     'n':row['regional_n'],'contract_window':{'start':row['contract_period_start'],'end':row['contract_period_end']},
                     'as_of_date':row['as_of_date'],'area_range_m2':{'minimum':83,'maximum':85,'endpoints_inclusive':True},
                     'statistic':'아파트 매매 실거래 중위값','reporting_complete':False,'october_reporting_ongoing':True,
                     'rounding':'none; exact aggregated median in ten-thousand KRW',
                     'claim_id':v['regional_claim_id'],
                     'representative':{'apt_id':rep['local_apt_id'],'api_apt_seq':rep['api_apt_seq'],'official_id':rep['official_id'],
                                       'apt_name':rep['name'],'legal_dong_name':v['representative']['legal_dong_name'],
                                       'median_manwon':rep['median_manwon'],'display_price':display(rep['median_manwon']),'n':rep['n'],
                                       'lat':rep['latitude'],'lng':rep['longitude'],'coordinate_status':'verified',
                                       'coordinate_source':rep['coordinate_source'],'verified_address':rep['verified_address'],
                                       'claim_id':v['representative']['claim_id'],'label':'단지 사례'}})
    data={'revision':'top20-explain-v3','status':'verified_price_data_for_script_review_not_video_approval',
          'source_file':str(source.relative_to(E)).replace('\\','/'),'source_sha256':sha(source),
          'methodology_file':str((P/'methodology.json').relative_to(E)).replace('\\','/'),
          'regions':rows}
    (D/'price_panel_data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'regions':len(rows),'n':sum(r['n']for r in rows),'rounding':'none','source':data['source_file']},ensure_ascii=False))

if __name__=='__main__':main()
