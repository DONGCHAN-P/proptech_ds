from pathlib import Path
import json,math,csv
O=Path(__file__).parent;annual=json.loads((O/'comparison.json').read_text(encoding='utf8'));a=list(csv.DictReader((O/'annual_returns.csv').open(encoding='utf-8-sig')));rows=[]
for n in [3,5,10,20]:
 subset=[r for r in a if int(r['year'])>2025-n];house=None
 if len(subset)==n:house=(math.prod(1+float(r['housing_return']) for r in subset)**(1/n)-1)*100
 etf=None;total=None
 if n in [3,5]:
  data=json.loads((O/f'raw/tiger_{n}y_response.json').read_text(encoding='utf8'))['rtnData'];total=float(data[-1]['nav']);etf=((1+total/100)**(1/n)-1)*100
 rows.append(dict(years=n,start=2025-n,end=2025,housing_cagr_pct=house,tiger_cagr_pct=etf,tiger_cumulative_pct=total,tiger_note='실제 ETF 이력 없음' if n>5 else '공식 NAV·분배금 재투자·세전'))
(O/'tiger_comparison.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
with (O/'tiger_comparison.csv').open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
svg='<svg viewBox="0 0 1100 440" xmlns="http://www.w3.org/2000/svg"><rect width="1100" height="440" fill="white"/>'
for i,r in enumerate(rows):
 y=30+i*100;svg+=f'<text x="20" y="{y+20}" font-size="22">최근 {r["years"]}년</text>'
 for j,(key,color,label) in enumerate([('housing_cagr_pct','#286cda','수도권'),('tiger_cagr_pct','#24816c','TIGER')]):
  v=r[key];yy=y+j*35;svg+=f'<text x="160" y="{yy+19}" font-size="16">{label}</text>'
  if v is None:svg+=f'<text x="250" y="{yy+19}" font-size="16" fill="#677780">'+('2005년 기준 자료 없음' if key.startswith('housing') else '2020년 상장 · 해당 기간 실적 없음')+'</text>'
  else:svg+=f'<rect x="250" y="{yy}" width="{max(v,0)*23}" height="26" rx="4" fill="{color}"/><text x="{260+max(v,0)*23}" y="{yy+20}" font-size="20" fill="{color}">{v:.2f}%</text>'
svg+='</svg>'
html='''<!doctype html><html lang="ko"><meta charset="utf-8"><title>국내상장 ETF와 수도권 집값</title><style>body{max-width:1150px;margin:30px auto;padding:20px;background:#f6f4ef;color:#173348;font-family:Malgun Gothic,sans-serif;line-height:1.8}svg{width:100%}.note{background:white;padding:20px;border-radius:12px}</style><h1>국내 상장 S&P500 ETF와 수도권 집값</h1><p>최근 완료연도인 <b>2025년 말 기준</b> · 연복리(CAGR) · 파랑: 수도권, 초록: TIGER 미국S&P500(360750)</p>'''+svg+'''<div class="note"><b>10년·20년을 실제 ETF 성과로 채우지 않았습니다.</b><p>TIGER 미국S&P500은 2020-08-07 상장. 환헤지 선물 ETF를 연결하지 않습니다. 집값은 2006년부터여서 2025년까지 20년 간격의 상승률도 계산할 수 없습니다. 2006~2025년은 19년입니다.</p><p>ETF는 공식 차트 NAV의 분배금 재투자 세전 누적수익률을 3년·5년으로 연환산했습니다. 3년 2022-12-29~2025-12-30, 5년 2020-12-30~2025-12-30. 순자산가치에 운용비용은 반영되지만 투자자의 세금·거래비용은 제외합니다. 환율 효과를 다시 더하지 않습니다.</p><p>주택은 연평균 거래가격 기준이며 ETF는 연말 기준이므로 매수·매도일이 정확히 일치하는 투자 실험은 아닙니다. 대출·주거편익을 제외한 참고 비교입니다.</p><a href="https://www.tigeretf.com/ko/product/search/detail/index.do?ksdFund=KR7360750004">TIGER 공식 상품·수익률 기준</a> · <a href="tiger_comparison.csv">계산표</a></div></html>'''
(O/'tiger_chart.html').write_text(html,encoding='utf8');print(rows)
