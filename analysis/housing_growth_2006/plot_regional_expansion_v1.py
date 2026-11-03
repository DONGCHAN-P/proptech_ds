from pathlib import Path
import json
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'analysis/housing_growth_2006/regional_expansion_v1'
data=json.loads((OUT/'results.json').read_text(encoding='utf8'))
frame=pd.read_csv(OUT/'quarterly_index.csv')
font_manager.fontManager.addfont('C:/Windows/Fonts/malgun.ttf')
plt.rcParams.update({'font.family':'Malgun Gothic','axes.unicode_minus':False,'font.size':14})
BG,INK,BLUE,RED,GRAY='#f6f4ef','#173348','#286cda','#b54c46','#546973'
order=['서울','경기','인천','부산','대구','대전','광주','세종']
summary={r['region']:r for r in data['summaries']}
quarter=pd.period_range('2020Q1',data['endpoint'],freq='Q')
for mode in ('start','peak','long'):
    quarter=pd.period_range('2006Q1' if mode=='long' else '2020Q1',data['endpoint'],freq='Q')
    curves={}
    for region in data['included_regions']:
        s=frame[frame.region==region].set_index('quarter')['index']
        ref=s.loc['2015Q1'] if mode=='long' else (s.loc['2020Q1'] if mode=='start' else s.loc[summary[region]['peak_quarter']])
        curves[region]=s.reindex([str(q) for q in quarter])/ref*100
    values=[float(v) for curve in curves.values() for v in curve if pd.notna(v)]
    low=math.floor(min(min(values),100)/20)*20
    high=math.ceil(max(max(values),100)/20)*20
    if mode=='long':
        low=0
        high=math.ceil(max(values)/100)*100
    fig,axes=plt.subplots(4,2,figsize=(18,16),facecolor=BG)
    fig.subplots_adjust(left=.07,right=.965,top=.84,bottom=.12,hspace=.54,wspace=.23)
    heading='2006년 이후 지역별 장기 가격 경로' if mode=='long' else ('같은 출발점에서도, 지역별 가격 경로는 달랐습니다' if mode=='start' else '이전 고점까지 얼마나 회복했을까?')
    fig.text(.07,.958,heading,fontsize=25,weight='bold',color=INK)
    basis='2015년 1분기 = 100 · 세종의 2015년 이전 선은 표시하지 않음' if mode=='long' else ('2020년 1분기 = 100' if mode=='start' else '지역별 2020~2022년 최고 분기 = 100')
    fig.text(.07,.924,f'{basis}  ·  같은 세로축 {low}~{high}  ·  2026년 2분기까지',fontsize=15,color=GRAY)
    for ax,region in zip(axes.flat,order):
        ax.set_facecolor(BG)
        for spine in ax.spines.values():spine.set_visible(False)
        if region not in curves:
            ax.axis('off')
            ax.text(0,.89,region,transform=ax.transAxes,fontsize=20,weight='bold',color=INK)
            ax.text(0,.55,'요청 완료 표시와 실제 자료 확보는 다릅니다',transform=ax.transAxes,fontsize=15,color=GRAY)
            count=data['normalization']['api_rows'].get(region,0)
            ax.text(0,.29,f'이번 수집 원본 {count:,}행 · 가격 비교 제외',transform=ax.transAxes,fontsize=16,weight='bold',color=RED)
            continue
        curve=curves[region]
        y=curve.to_numpy()
        ax.axhline(100,color=GRAY,linewidth=1,linestyle=(0,(4,4)),alpha=.65)
        ax.plot(range(len(y)),y,color=BLUE,linewidth=3)
        ax.scatter([len(y)-1],[y[-1]],color=BLUE,s=32,zorder=3)
        ax.set_ylim(low,high)
        ax.set_xlim(-.2,len(y)+1)
        ticks=[i for i,q in enumerate(quarter) if q.quarter==1 and (mode!='long' or q.year%4==2)]
        ax.set_xticks(ticks,[str(quarter[i].year) for i in ticks])
        ax.set_yticks(range(low,high+1,100 if mode=='long' else 20))
        ax.tick_params(length=0,labelcolor=GRAY,labelsize=12,pad=7)
        ax.grid(axis='y',color='#d9dedf',linewidth=.8)
        r=summary[region]
        title=region+' (군위 제외)' if region=='대구' else region
        ax.set_title(title,loc='left',fontsize=20,weight='bold',color=INK,pad=29)
        measure=(y[-1]/100-1)*100
        label=f'2015Q1 대비 {measure:+.1f}%' if mode=='long' else (f'2020Q1 대비 {measure:+.1f}%' if mode=='start' else f'이전 고점 대비 {measure:+.1f}%')
        ax.text(0,1.055,label,transform=ax.transAxes,fontsize=14,color=BLUE if measure>=0 else RED,weight='bold')
        ax.text(len(y)-.25,y[-1],f'  {y[-1]:.1f}',fontsize=13,color=INK,va='center')
    notes=['보유 실거래 자료의 자체 매칭 지표 · 공식 가격지수가 아니며 투자수익률과 다릅니다.',
           '동일 단지·면적의 분기 중위가격 연결 / 양 분기 각각 2건 이상 / 연결마다 단지 30개 이상 / 지역 내 단지 동일 가중.',
           '분기마다 매칭 표본이 달라지고 동·층·수리 상태는 미조정. 표본 기준에 따라 회복 판정이 달라질 수 있음. 대구는 군위 제외.',
           '2026Q3은 신고가 더 들어올 수 있어 제외. 광주는 현재 원본 응답에서 거래가 확보되지 않아 비교에서 제외.']
    for i,text in enumerate(notes):fig.text(.07,.081-i*.019,text,fontsize=11,color=GRAY)
    name='regional_long_run.png' if mode=='long' else ('regional_price_paths.png' if mode=='start' else 'regional_peak_recovery.png')
    fig.savefig(OUT/name,dpi=130,facecolor=BG)
    plt.close(fig)
print('Saved three regional charts')
