"""Static research charts and a machine-readable trial ledger."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT=Path(__file__).resolve().parent
R=ROOT/'results';T=ROOT/'results_timeliness'
font=Path('C:/Windows/Fonts/malgun.ttf')
if font.exists():
    font_manager.fontManager.addfont(str(font))
    plt.rcParams['font.family']=font_manager.FontProperties(fname=str(font)).get_name()
plt.rcParams.update({'axes.unicode_minus':False,'font.size':10,'figure.facecolor':'#f8fafc',
                      'axes.facecolor':'#f8fafc','axes.spines.top':False,'axes.spines.right':False})
main=pd.read_csv(R/'scorecard.csv')
timing=pd.read_csv(T/'scorecard.csv')
selected=['v3_hgb','hgb_full_120m','fixed_blend','hgb_t2_120m']
labels=['기존 HGB','최근 10년 HGB','고정 50:50 결합','입력 한 달 갱신\n조건부 실험']
allmetrics=pd.concat([main[main.model.isin(selected[:-1])],timing[timing.model.eq(selected[-1])]],ignore_index=True)
fig,axes=plt.subplots(2,2,figsize=(13,8),layout='constrained')
for i,window in enumerate(['all_regimes','recent']):
    for j,level in enumerate(['province','district']):
        ax=axes[i,j]
        s=allmetrics[allmetrics.window.eq(window)&allmetrics.level.eq(level)].set_index('model').reindex(selected)
        bars=ax.bar(range(4),s.mae_pp,color=['#64748b','#a5b4fc','#60a5fa','#2563eb'])
        ax.bar_label(bars,fmt='%.2f',padding=4)
        ax.set_xticks(range(4),labels,fontsize=9)
        ax.set_ylim(0,s.mae_pp.max()*1.2)
        ax.set_ylabel('평균 절대 오차 (%p)')
        ax.set_title(('전체 국면 2017~2026' if i==0 else '최근 2024~2026')+' · '+('시도' if j==0 else '세부 지역'),loc='left',fontweight='bold')
        ax.grid(axis='y',alpha=.15)
fig.suptitle('반복 실험: 개선 폭과 평가 기간을 함께 본다',fontsize=17,fontweight='bold')
fig.get_layout_engine().set(rect=(0,.05,1,.95))
fig.text(.02,.01,'동일 원점·지역·6개월 목표 비교 · 마지막 후보는 과거 공개본을 복원하지 않은 입력 시점 민감도 실험',fontsize=9,color='#526070')
fig.savefig(R/'scores_overview.png',dpi=160,bbox_inches='tight');plt.close(fig)

bytime=pd.read_csv(R/'by_origin.csv',parse_dates=['origin'])
tp=pd.read_parquet(T/'predictions.parquet')
tp['ae']=(tp.prediction_pct-tp.actual_pct).abs()
ts=tp[tp.model.eq('hgb_t2_120m')].groupby(['origin','level']).ae.mean().reset_index(name='mae_pp')
ts['model']='hgb_t2_120m'
fig,axes=plt.subplots(2,1,figsize=(13,8),layout='constrained')
for ax,level in zip(axes,['province','district']):
    for name,color,label in [('v3_hgb','#64748b','기존 HGB'),('hgb_full_120m','#a78bfa','최근 10년 HGB'),('hgb_t2_120m','#2563eb','입력 한 달 갱신 조건부')]:
        data=ts[ts.level.eq(level)] if name=='hgb_t2_120m' else bytime[bytime.level.eq(level)&bytime.model.eq(name)]
        ax.plot(pd.to_datetime(data.origin),data.mae_pp,label=label,color=color,marker='o',ms=3,lw=1.8)
    ax.axvspan(pd.Timestamp('2020-01-01'),pd.Timestamp('2021-12-31'),color='#fee2e2',alpha=.45)
    ax.axvspan(pd.Timestamp('2022-01-01'),pd.Timestamp('2023-12-31'),color='#dbeafe',alpha=.55)
    ax.set_title('시도' if level=='province' else '세부 지역',loc='left')
    ax.set_ylabel('평균 절대 오차 (%p)');ax.grid(alpha=.15);ax.legend(frameon=False,ncols=3,fontsize=9)
fig.suptitle('안정기 평균으로 급등·급락기 오차를 가리지 않는다',fontsize=16,fontweight='bold')
fig.savefig(R/'regime_errors.png',dpi=160);plt.close(fig)

fig,axes=plt.subplots(1,2,figsize=(12,5),layout='constrained')
for ax,level in zip(axes,['province','district']):
    windows=['boom','turn','recent'];x=np.arange(3)
    for shift,name,color,label in [(-.18,'v3_hgb','#94a3b8','기존'),(.18,'hgb_t2_120m','#2563eb','입력 갱신 조건부')]:
        s=timing[timing.level.eq(level)&timing.model.eq(name)].set_index('window').reindex(windows)
        bars=ax.bar(x+shift,s.interval_coverage_80*100,.36,color=color,label=label)
        ax.bar_label(bars,fmt='%.0f%%',padding=3,fontsize=9)
    ax.axhline(80,color='#dc2626',ls='--',lw=1,label='명목 80%')
    ax.set_xticks(x,['상승기\n2020~2021','전환기\n2022~2023','최근\n2024~2026'])
    ax.set_ylim(0,112);ax.set_ylabel('실제 범위 포함 비율 (%)')
    ax.set_title('시도' if level=='province' else '세부 지역',loc='left');ax.legend(frameon=False,fontsize=8)
fig.suptitle('예측 범위도 검증: 급변기 포함 비율이 낮다',fontsize=16,fontweight='bold')
fig.get_layout_engine().set(rect=(0,.07,1,.93))
fig.text(.02,.015,'각 시점에 공개된 과거 예측 오차만으로 범위 생성 · 독립 표본의 확률 보장을 뜻하지 않음',fontsize=9,color='#526070')
fig.savefig(R/'interval_calibration.png',dpi=160,bbox_inches='tight');plt.close(fig)

rows=[]
for round_id,path,kind in [('round1',ROOT/'round1/scorecard.csv','18개 후보·4개 결합 규칙'),
                           ('round2',R/'scorecard.csv','26개 후보·4개 결합 규칙')]:
    table=pd.read_csv(path)
    values=table[table.window.eq('all_regimes')].pivot(index='model',columns='level',values='balanced_mae_pp')
    base=values.loc['v3_hgb'];ratio=(values/base).mean(axis=1)
    best=ratio.idxmin()
    rows.append({'round':round_id,'scope':kind,'best_exploratory_model':best,
                 'mean_balanced_mae_ratio':float(ratio.min()),'promotion_gate_passed':False,
                 'new_blind_data':False})
values=timing[timing.window.eq('all_regimes')].pivot(index='model',columns='level',values='balanced_mae_pp')
ratio=(values/values.loc['v3_hgb']).mean(axis=1)
rows.append({'round':'round3','scope':'2개 입력 시점 민감도 대안','best_exploratory_model':ratio.idxmin(),
             'mean_balanced_mae_ratio':float(ratio.min()),'promotion_gate_passed':bool(ratio.min()<=.95),
             'new_blind_data':False,'historical_input_availability_assumed':True})
pd.DataFrame(rows).to_csv(R/'trial_history.csv',index=False,encoding='utf-8-sig')
allmetrics.to_csv(R/'key_metrics.csv',index=False,encoding='utf-8-sig')
print(json.dumps({'charts':3,'trial_rounds':3,'last_ratio':float(ratio.min())}))
