"""Export static research figures; inputs are preserved experiment outputs."""
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT=Path(__file__).resolve().parent
font=Path('C:/Windows/Fonts/malgun.ttf')
if font.exists():
    font_manager.fontManager.addfont(str(font))
    plt.rcParams['font.family']=font_manager.FontProperties(fname=str(font)).get_name()
plt.rcParams.update({'axes.unicode_minus':False,'font.size':10,'figure.facecolor':'#ffffff',
    'axes.spines.top':False,'axes.spines.right':False,'axes.labelcolor':'#354a60','text.color':'#172a3a'})
blue='#2659d9';gray='#8a9bb1';teal='#128475';amber='#e8b75f'

def finish(fig,name,footer=None):
    if footer:
        fig.get_layout_engine().set(rect=(0,.065,1,.96))
        fig.text(.025,.012,footer,fontsize=8,color='#65758a')
    fig.savefig(ROOT/name,dpi=170,bbox_inches='tight');plt.close(fig)

regime=pd.read_csv(ROOT/'regime_diagnostics.csv')
fig,ax=plt.subplots(figsize=(9.5,3.5),layout='constrained')
left=np.zeros(2)
for key,label,color in [('early','2017~2019','#c6d1e2'),('boom','상승기 2020~2021',amber),
                        ('turn','전환기 2022~2023',blue),('recent','최근 2024~2026',teal)]:
    values=np.array([regime[regime.level.eq(level)&regime.regime.eq(key)].error_share.iloc[0]*100
                     for level in ['province','district']])
    ax.barh([1,0],values,left=left,color=color,label=label,height=.52)
    for y,x,v in zip([1,0],left,values):ax.text(x+v/2,y,f'{v:.1f}%',ha='center',va='center',fontsize=10,color='white' if key in ['turn','recent'] else '#203449')
    left+=values
ax.set_yticks([1,0],['시도','시군구']);ax.set_xlim(0,100);ax.set_xlabel('전체 균형 MAE의 오차 기여 비중 (%)')
ax.legend(loc='upper center',bbox_to_anchor=(.5,-.23),ncols=4,frameon=False,fontsize=8)
ax.set_title('2020~2023년이 전체 균형 오차의 약 62~66%를 차지',loc='left',fontweight='bold',pad=16)
finish(fig,'error_concentration.png','같은 19개 반기 원점 · 시도·원점 균등 가중 · 시군구는 시도 내부에서 먼저 평균')

factors=pd.read_csv(ROOT/'factor_decomposition.csv')
fig,axes=plt.subplots(1,2,figsize=(10,3.9),layout='constrained')
for ax,window,title in zip(axes,['all_regimes','recent'],['전체 2017~2026','최근 2024~2026']):
    s=factors[factors.window.eq(window)].set_index('level').reindex(['province','district'])
    x=np.arange(2)
    for shift,key,label,color in [(-.18,'lag_shapley_pp','입력 시차',blue),(.18,'training_shapley_pp','학습 규칙',teal)]:
        bars=ax.bar(x+shift,s[key],.34,label=label,color=color)
        ax.bar_label(bars,fmt='%.4f',padding=4,fontsize=9)
    ax.set_xticks(x,['시도','시군구']);ax.set_ylim(0,max(s.lag_shapley_pp.max(),s.training_shapley_pp.max())*1.28)
    ax.set_ylabel('균형 MAE 감소 기여 (%p)');ax.set_title(title,loc='left',fontweight='bold');ax.legend(frameon=False,fontsize=9)
finish(fig,'factor_effects.png','네 고정 조합의 대칭 기여 분해 · 학습 규칙은 시작 연도·120개월 창 차이 포함 · 입력 시차는 최신 수정본 가정')

outcome=pd.read_csv(ROOT/'outcome_band_diagnostics.csv')
fig,axes=plt.subplots(1,2,figsize=(9.5,4),layout='constrained')
for ax,level,title in zip(axes,['province','district'],['시도','시군구']):
    s=outcome[outcome.level.eq(level)].set_index('realized_move_band').reindex(['rise_above10','fall_below_minus10'])
    x=np.arange(2)
    for shift,key,label,color in [(-.18,'actual_mean_pct','실제 평균',blue),(.18,'predicted_mean_pct','예측 평균',gray)]:
        bars=ax.bar(x+shift,s[key],.34,label=label,color=color);ax.bar_label(bars,fmt='%.1f',padding=3,fontsize=9)
    ax.axhline(0,color='#8492a6',lw=.8);ax.set_xticks(x,[f'실제 +10% 초과\n{s.scored_n.iloc[0]:.0f}건',f'실제 -10% 미만\n{s.scored_n.iloc[1]:.0f}건'])
    ax.set_title(title,loc='left',fontweight='bold');ax.set_ylabel('6개월 누적 변화율 (%)');ax.legend(frameon=False,fontsize=9)
    ax.set_ylim(-19,21)
finish(fig,'extreme_moves.png','실제 결과를 본 뒤 분류한 진단 집단 · 모델 입력으로 사용하지 않음 · 하락 사례는 표본이 작음')

interval=pd.read_csv(ROOT/'interval_scorecard.csv')
fig,axes=plt.subplots(1,2,figsize=(10,4),layout='constrained')
for ax,level,title in zip(axes,['province','district'],['시도','시군구']):
    s=interval[interval.window.eq('all_regimes')&interval.level.eq(level)].set_index('calibration_rule').reindex(['baseline','symmetric','volatility_scaled'])
    bars=ax.bar(range(3),s.interval_coverage_80*100,color=[gray,blue,teal])
    ax.bar_label(bars,fmt='%.1f%%',padding=4)
    ax.axhline(80,color='#bd8326',ls='--',lw=1,label='명목 80%')
    ax.set_xticks(range(3),['기준','대칭 잔차','변동성 스케일']);ax.set_ylim(0,95)
    ax.set_title(title,loc='left',fontweight='bold');ax.set_ylabel('실제 포함률 (%)');ax.legend(frameon=False,fontsize=8)
finish(fig,'interval_comparison.png','포함률만으로 채택하지 않음 · 대칭 방식은 시도 구간점수 개선, 시군구 포함률 부족 · 점예측은 동일')

rental=pd.read_csv(ROOT/'rental_scorecard.csv');residual=pd.read_csv(ROOT/'residual_scorecard.csv')
scores=pd.concat([rental,residual[residual.model.ne('v3_hgb')]],ignore_index=True)
fig,axes=plt.subplots(1,2,figsize=(10,4),layout='constrained')
for ax,level,title in zip(axes,['province','district'],['시도','시군구']):
    s=scores[scores.window.eq('all_regimes')&scores.level.eq(level)].set_index('model').reindex(['v3_hgb','v3_hgb_rental','hgb_momentum_residual'])
    bars=ax.bar(range(3),s.balanced_mae_pp,color=[gray,blue,teal]);ax.bar_label(bars,fmt='%.3f',padding=4)
    ax.set_xticks(range(3),['기존 HGB','전세 변수 추가','모멘텀 + 보정']);ax.set_ylim(0,s.balanced_mae_pp.max()*1.2)
    ax.set_title(title,loc='left',fontweight='bold');ax.set_ylabel('전체 균형 MAE (%p)')
finish(fig,'model_trials.png','같은 19개 채점 원점·지역·목표·기존 HGB 설정 · 두 대안은 별도 실험 · 모두 사후 연구 성적')
print('5 research figures exported')
