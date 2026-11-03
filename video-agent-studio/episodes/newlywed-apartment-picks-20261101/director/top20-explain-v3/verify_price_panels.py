"""Require exact agreement with an independently parsed XML rollup."""
from pathlib import Path
import hashlib,json
D=Path(__file__).resolve().parent; E=D.parents[1]; Q=E/'qa/top20-explain-v3'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    path=D/'price_panel_data.json'; data=read(path); independent=read(Q/'independent_price_rollup.json')
    regional={r['region_id']:r for r in independent['regions']}
    apt={(r['region_id'],r['apt_seq']):r for r in independent['complexes']}; checks=[]
    for r in data['regions']:
        expected=regional[r['region_id']]
        assert (r['n'],r['median_manwon'])==(expected['n'],expected['median_manwon']),r['region_id']
        rep=r['representative']; expected=apt[r['region_id'],rep['api_apt_seq']]
        assert (rep['n'],rep['median_manwon'])==(expected['n'],expected['median_manwon']),rep['apt_name']
        assert rep['apt_name']==expected['apt_name'] and rep['legal_dong_name']==expected['legal_dong']
        checks.append({'region_id':r['region_id'],'region_n_and_median':'exact_match','complex_n_name_and_median':'exact_match'})
    report={'status':'passed','region_count':20,'total_n':sum(r['n']for r in data['regions']),
            'independent_basis':'separate XML parser; no research calculation imported',
            'price_panel_sha256':sha(path),'rollup_sha256':sha(Q/'independent_price_rollup.json'),
            'checks':checks,'actual_listening_performed':False,'continuous_playback_performed':False}
    (Q/'price_panel_verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ['checks']},ensure_ascii=False))
if __name__=='__main__':main()
