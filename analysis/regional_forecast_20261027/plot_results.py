"""Create standalone figures from experiment artifacts; no web dependencies."""
from pathlib import Path
import argparse
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

OUT=Path(__file__).resolve().parent
ap=argparse.ArgumentParser()
ap.add_argument('--results',default='results_v3')
args=ap.parse_args()
R=OUT/args.results
if not R.resolve().is_relative_to(OUT.resolve()): raise ValueError('Outside experiment')
font=Path('C:/Windows/Fonts/malgun.ttf')
if font.exists():
    font_manager.fontManager.addfont(str(font))
    plt.rcParams['font.family']=font_manager.FontProperties(fname=str(font)).get_name()
plt.rcParams.update({'axes.unicode_minus':False,'font.size':11,'figure.facecolor':'#f7f8fb',
                     'axes.facecolor':'#f7f8fb','axes.spines.top':False,'axes.spines.right':False})
summary=json.loads((R/'run_summary.json').read_text('utf-8'))
winner=summary['winner']
m=pd.read_csv(R/'backtest_metrics.csv')
b=pd.read_csv(R/'backtest_predictions.csv')
f=pd.read_csv(R/'forecast_next_6_months.csv')
labels={'price_unchanged':'가격 유지','damped_momentum':'과거 추세 절반 반영','ridge_price':'가격·거래량',
        'ridge_macro':'가격 + 금리','ridge_supply':'가격 + 공급','ridge_demand':'가격 + 인구·가구·이동',
        'ridge_economy':'가격 + 경제·수급','ridge_full':'선형 전체 변수','boosting_full':'트리 전체 변수'}
order=m[m.stage.eq('development')&m.level.eq('province')].sort_values('mae_pp').model.tolist()
fig,ax=plt.subplots(figsize=(12,6),layout='constrained')
x=np.arange(len(order))
for i,(stage,label,color) in enumerate([('development','모델 선택: 2017~2023','#a0b8df'),('holdout','별도 평가: 2024~2026','#2563eb')]):
    s=m[m.stage.eq(stage)&m.level.eq('province')&m.horizon.eq(6)].set_index('model').reindex(order)
    bars=ax.bar(x+(i-.5)*.36,s.mae_pp,.36,label=label,color=color)
    ax.bar_label(bars,fmt='%.2f',fontsize=8,padding=3)
ax.set_xticks(x,[labels.get(o,o) for o in order],rotation=18,ha='right')
ax.set_ylabel('6개월 변화율의 평균 절대 오차 (%p)')
ax.set_title('복잡한 변수가 실제로 예측 오차를 줄였을까?',loc='left',fontweight='bold',pad=18)
ax.legend(frameon=False)
ax.grid(axis='y',alpha=.15)
fig.savefig(R/'model_comparison.png',dpi=170)
plt.close(fig)

s=f[f.horizon.eq(6)&f.level.eq('province')].sort_values('prediction_pct')
fig,ax=plt.subplots(figsize=(11,7),layout='constrained')
y=np.arange(len(s))
for j,(_,row) in enumerate(s.iterrows()):
    ax.plot([row.range_low_pct,row.range_high_pct],[j,j],lw=6,alpha=.25,color='#2563eb')
ax.scatter(s.prediction_pct,y,s=65,color='#2563eb',zorder=3)
ax.set_yticks(y,s['name'])
ax.axvline(0,color='#526070',lw=1)
for j,v in enumerate(s.prediction_pct):
    ax.annotate(f'{v:+.1f}%',(v,j),xytext=(7,7),textcoords='offset points',fontsize=10)
ax.set_xlabel('2026년 10월 대비 2027년 4월 예상 변화율 (%)')
ax.set_title('6개월 전망: 지역별 예측과 과거 검증 오차 범위',loc='left',fontweight='bold',pad=18)
fig.get_layout_engine().set(rect=(0,.07,1,.93))
fig.text(.02,.015,'2026-10-27 기준 · 가격 입력: 2026년 7월까지 · 막대: 2024~2026 평가 잔차의 10~90분위',fontsize=9,color='#566170')
fig.savefig(R/'six_month_forecast.png',dpi=170,bbox_inches='tight')
plt.close(fig)

fig,ax=plt.subplots(figsize=(12,6),layout='constrained')
colors=['#2563eb','#c08c2f','#df4759','#159b8e','#8155b9','#527270']
for name,color in zip(['서울','경기','인천','부산','대구','대전'],colors):
    g=f[f['name'].eq(name)&f.level.eq('province')].sort_values('horizon')
    if g.empty: continue
    ax.plot(np.r_[0,g.horizon],np.r_[100,g.forecast_index],marker='o',ms=4,lw=2,label=name,color=color)
ax.axhline(100,color='#8b97a5',lw=.8)
ax.set_xticks(range(7),['2026.10','11','12','2027.01','02','03','04'])
ax.set_ylabel('기준월 100으로 환산한 예측 변화')
ax.set_title('앞으로 6개월의 지역별 예상 흐름',loc='left',fontweight='bold',pad=18)
ax.legend(ncols=3,frameon=False)
ax.grid(alpha=.12)
fig.get_layout_engine().set(rect=(0,.07,1,.93))
fig.text(.02,.015,'2026년 10월을 100으로 놓은 변화율 전망 · 기준월 실제 가격은 아직 관측 전',fontsize=9,color='#566170')
fig.savefig(R/'forecast_paths.png',dpi=170,bbox_inches='tight')
plt.close(fig)

g=b[b.stage.eq('holdout')&b.level.eq('province')&b.model.eq(winner)&b.horizon.eq(6)]
fig,ax=plt.subplots(figsize=(8,7),layout='constrained')
for name,rows in g.groupby('name'):
    ax.scatter(rows.actual_pct,rows.prediction_pct,s=36,label=name,alpha=.75)
lim=max(abs(g.actual_pct).max(),abs(g.prediction_pct).max())+1
ax.plot([-lim,lim],[-lim,lim],color='#8893a5',lw=1,ls='--')
ax.axhline(0,color='#bdc4cf',lw=.6)
ax.axvline(0,color='#bdc4cf',lw=.6)
ax.set(xlabel='실제 6개월 변화율 (%)',ylabel='예측 변화율 (%)',title='2024년 이후 별도 평가: 예측과 실제')
ax.legend(frameon=False,fontsize=8,ncols=2)
fig.savefig(R/'holdout_actual_vs_prediction.png',dpi=170)
plt.close(fig)

# Past performance can be regime-specific. Save dated errors for inspection.
e=b[b.level.eq('province')&b.horizon.eq(6)].copy()
e['absolute_error']=(e.prediction_pct-e.actual_pct).abs()
t=e[e.model.isin(['price_unchanged','ridge_price',winner])].groupby(['origin','model']).absolute_error.mean().unstack()
fig,ax=plt.subplots(figsize=(12,5),layout='constrained')
for col in t:
    ax.plot(pd.to_datetime(t.index),t[col],marker='o',ms=3,label=labels.get(col,col))
ax.axvspan(pd.Timestamp('2024-01-01'),pd.Timestamp('2026-02-01'),color='#dbeafe',alpha=.5,label='별도 평가 구간')
ax.set(ylabel='평균 절대 오차 (%p)',title='어느 시기에 예측이 어려웠나?')
ax.legend(frameon=False)
ax.grid(alpha=.15)
fig.savefig(R/'errors_by_origin.png',dpi=170)
plt.close(fig)
print(json.dumps({'pngs':[p.name for p in R.glob('*.png')]},ensure_ascii=False))
