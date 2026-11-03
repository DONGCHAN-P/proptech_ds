from pathlib import Path
import pandas as pd,json
O=Path(__file__).parent/'exploration';a=pd.read_csv(O/'quarterly_matched_index.csv');v=pd.read_csv(O/'quarterly_volume_distribution.csv');s=pd.read_csv(O/'sensitivity.csv'); colors={'서울':'#286cda','경기':'#d17b16','인천':'#24816c'}
def chart(data,col,title):
 dates=sorted(data.q.unique());lo=min(0,float(data[col].min()));hi=float(data[col].max());hi=hi if hi>lo else lo+1
 X=lambda q:70+dates.index(q)/(len(dates)-1)*1040;Y=lambda val:290-(val-lo)/(hi-lo)*235
 svg=f'<h2>{title}</h2><svg viewBox="0 0 1160 335">'
 for i in range(6):
  val=lo+(hi-lo)*i/5;y=Y(val);svg+=f'<line x1="70" x2="1110" y1="{y}" y2="{y}" stroke="#ddd"/><text x="60" y="{y+4}" text-anchor="end">{val:,.1f}</text>'
 for q in dates:
  if q.endswith('Q1') and int(q[:4])%2==0:svg+=f'<text x="{X(q)}" y="320" text-anchor="middle">{q[:4]}</text>'
 for reg,c in colors.items():
  z=data[data.region==reg].sort_values('q');pts=' '.join(f'{X(r.q)},{Y(getattr(r,col))}' for r in z.itertuples());svg+=f'<polyline points="{pts}" stroke="{c}" fill="none" stroke-width="2.5"/>'
  for r in z.itertuples():svg+=f'<circle cx="{X(r.q)}" cy="{Y(getattr(r,col))}" r="3" fill="{c}"><title>{reg} {r.q}: {getattr(r,col):,.2f}</title></circle>'
 return svg+'</svg>'
a['drawdown']=a.groupby('region')['index'].transform(lambda z:(z/z.cummax()-1)*100)
v['price_ratio']=v.p90/v['median']
html='''<!doctype html><html lang="ko"><meta charset="utf-8"><title>실거래 탐색 · 고점과 회복</title><style>body{background:#f6f4ef;color:#173348;font-family:Malgun Gothic,sans-serif;max-width:1250px;margin:auto;padding:25px}section{background:white;border-radius:12px;padding:20px;margin:20px 0}svg{width:100%;font-size:12px}p{line-height:1.8}table{border-collapse:collapse;width:100%;font-size:14px}td,th{padding:10px;border-bottom:1px solid #ddd}</style><h1>실거래 데이터 탐색: 흐름·분포·거래량·고점과 회복</h1><p>서울 <span style="color:#286cda">●</span> · 경기 <span style="color:#d17b16">●</span> · 인천 <span style="color:#24816c">●</span><br>2006Q1~2026Q3 · 점에 마우스를 올리면 값 표시</p><p><b>탐색용 자체 지수입니다.</b> 같은 단지·면적에서 전분기와 현재 분기 각각 2건 이상 거래된 가격의 중위값을 비교하고, 단지에 같은 가중치를 부여해 연결했습니다. 개별 주택의 회복이나 공식 지수를 뜻하지 않습니다. 2026Q3는 신고 지연으로 잠정치입니다.</p>'''
for df,col,title in [(a,'index','1. 가격 흐름 · 2006Q1=100'),(v,'transactions','2. 분기 거래량 · 건'),(v,'price_ratio','3. 거래가격 분포 · ㎡당 가격 상위 10% 경계 ÷ 중위가격'),(a,'drawdown','4. 과거 최고 지수 대비 하락률 · %')]:html+='<section>'+chart(df,col,title)+'</section>'
s=s.rename(columns={'region':'지역','min_trades':'분기별 최소 거래','peak_quarter':'2020~2022 고점','trough_quarter':'이후 저점','drawdown_pct':'고점→저점 %','recovery_quarter':'저점 이후 첫 회복','latest_quarter':'최신 분기','latest_vs_peak_pct':'최신/고점 %','min_matched':'최소 매칭 단지'})
html+='<section><h2>표본 기준에 따른 고점·회복 민감도</h2>'+s.round(2).fillna('미회복').to_html(index=False,border=0)+'</section><p>분포 차트는 실제 거래 구성의 변화도 포함합니다. 가격 변화만으로 인과관계를 주장하지 않습니다. 회복은 2020~2022 최고 분기 이후 저점을 지난 뒤 그 고점 이상이 된 첫 분기이며 지속 회복은 별도 검증이 필요합니다. 분기 연결 표본은 계속 달라지고 층·수리·거래시점은 미조정입니다. 부산·대구·대전은 수집 중이므로 제외했습니다.</p></html>'
(O/'dashboard.html').write_text(html,encoding='utf8');print('dashboard created')
