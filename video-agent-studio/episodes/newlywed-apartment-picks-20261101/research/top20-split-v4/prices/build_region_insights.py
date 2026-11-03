from pathlib import Path
import json,sys
import pandas as pd
D=Path(__file__).resolve().parent;E=D.parents[2]
sys.path.insert(0,str(D));from price_domain import BANDS
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def main():
    frame=pd.read_parquet(E/'research/top20-explain-v3/prices/final-api-20261103-v2/api_rows_valid83_85.parquet')
    points=read(D/'complex_prices.json')['rows'];coverage=read(D/'coverage.json')['regions']
    out=[]
    for r in coverage:
        rid=r['region_id'];t=frame[frame.region_id==rid];p=[x for x in points if x['region_id']==rid and x['coordinate_verified']]
        dongs=[]
        for name,g in t.groupby('umdNm'):
            dongs.append({'dong':name,'transaction_n':len(g),'complex_n':int(g.api_complex_id.nunique()),'median_manwon':float(g.deal_amount_manwon.median())})
        dongs.sort(key=lambda x:(-x['transaction_n'],x['dong']))
        cohort=[]
        for lo,hi,label in [(0,2000,'2000년 이전 준공'),(2001,2010,'2001~2010년 준공'),(2011,9999,'2011년 이후 준공')]:
            g=t[pd.to_numeric(t.buildYear,errors='coerce').between(lo,hi)]
            if len(g):cohort.append({'label':label,'transaction_n':len(g),'complex_n':int(g.api_complex_id.nunique()),'median_manwon':float(g.deal_amount_manwon.median())})
        bands=[{'label':b['label'],'color':b['color'],'complex_n':sum(x['band']==i for x in p),'denominator':len(p)} for i,b in enumerate(BANDS)]
        vals=sorted(x['median_manwon'] for x in p)
        out.append({**r,'mapped_bands':bands,'mapped_complex_price_quantiles':{str(q):float(pd.Series(vals).quantile(q)) for q in [.1,.25,.5,.75,.9]},'dong_prices_by_transaction_count':dongs,'build_cohorts':cohort,'interpretation_limit':'거래구성·세부입지·연식·층·단지상품 차이가 함께 섞인 관측 비교. 인과효과나 개별 단지 가치평가로 해석하지 않음.'})
    (D/'region_insights.json').write_text(json.dumps({'regions':out,'method':'dong/cohort are transaction medians; mapped quantiles/bands are one median per location-verified complex. Denominators are separate.'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps([{'rid':r['region_id'],'region':r['region'],'n':r['mapped_complexes'],'top_dongs':r['dong_prices_by_transaction_count'][:2]} for r in out],ensure_ascii=False))
if __name__=='__main__':main()
