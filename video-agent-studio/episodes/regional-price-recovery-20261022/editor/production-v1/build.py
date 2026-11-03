"""Approved v3 -> deterministic HyperFrames. No API calls or paid generation.
Run from repository root; paths are resolved from this file, never cwd.
"""
import argparse, hashlib, html, json, math, re, shutil, subprocess
from pathlib import Path

ED = Path(__file__).resolve().parent
EP = ED.parent.parent
REPO = EP.parents[2]
PROJECT = EP / 'outputs/production-v1-jun/project'
CHECKS = PROJECT.parent / 'checks'
PREVIEWS = PROJECT.parent / 'previews'
SHA = '99b40e8730ee0f8fdf74402cffbe04b5b418540344e6d2a7175e6a01c3054664'
DATA_SHA = '3731da4b839424f7c12a948c6316a0b0ac29cec99aa42c6d6855b832fe7c1899'
COLORS = dict(zip(['서울','경기','인천','부산','대구','대전','세종'], ['#286cda','#1c7386','#ae6027','#6855a2','#ad475e','#45733d','#8a652a']))
def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,s):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(s,encoding='utf-8')
def js(p,d): write(p,json.dumps(d,ensure_ascii=False,indent=2))
def esc(x): return html.escape(str(x),quote=True)
def qi(q): return int(q[:4])*4+int(q[-1])-1
def qstr(i): return f'{i//4}Q{i%4+1}'
def fmt(v): return f'{v:,.0f}' if abs(v)>=100 else f'{v:.1f}'

CSS = '''@font-face{font-family:Pretendard;src:url(assets/fonts/Pretendard-Regular.woff2);font-weight:400}@font-face{font-family:Pretendard;src:url(assets/fonts/Pretendard-Bold.woff2);font-weight:700}
*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;background:#f6f4ef;color:#173348;font-family:Pretendard,sans-serif;overflow:hidden}#root{position:relative;width:100%;height:100%;overflow:hidden}.rpr-scene{position:absolute;inset:0}.rpr-beat{position:absolute;inset:0;background:#f6f4ef}.rpr-head{position:absolute;left:80px;right:80px;top:30px;display:flex;justify-content:space-between;font-size:23px;color:#526872}.rpr-title{position:absolute;left:80px;top:94px;right:80px;font-size:43px;font-weight:700;line-height:1.22;margin:0}.rpr-sub{position:absolute;left:80px;right:80px;top:156px;font-size:23px;color:#526872}.rpr-plot{position:absolute;left:0;top:0;width:1920px;height:1080px}.rpr-plot text{font-family:Pretendard,sans-serif;fill:#173348;font-variant-numeric:tabular-nums}.rpr-note{position:absolute;left:96px;right:96px;top:866px;font-size:21px;color:#526872;line-height:1.25}.rpr-caption-box{position:absolute;left:96px;top:916px;width:1728px;height:110px;background:#fff;border-radius:13px;z-index:20}.rpr-caption{position:absolute;left:126px;top:922px;width:1668px;height:98px;display:flex;align-items:center;justify-content:center;text-align:center;font-size:39px;font-weight:700;line-height:1.25;z-index:21}.rpr-source{position:absolute;left:96px;top:1042px;width:1728px;height:25px;font-size:18px;color:#526872;z-index:22;white-space:nowrap}.clip{position:absolute;inset:0}.rpr-caption.clip{left:126px;top:922px;right:auto;bottom:auto}.rpr-readout{font-variant-numeric:tabular-nums}.rpr-axis{fill:#526872!important;font-size:22px}.rpr-panel-title{font-size:29px;font-weight:700}.rpr-big{font-size:43px;font-weight:700}.rpr-value{font-size:30px;font-weight:700}.rpr-key{font-size:23px}.rpr-micro{font-size:20px;fill:#526872!important}
'''

class Art:
    def __init__(self, prefix): self.prefix=prefix; self.svg=[]; self.drivers=[]; self.counter=0
    def add(self,s): self.svg.append(s)
    def text(self,x,y,s,size=24,color='#173348',weight=400,anchor='start',cls=''):
        self.add(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" style="fill:{color}" class="{cls}">{esc(s)}</text>')
    def line(self,x,y,xx,yy,color='#d4dcd9',width=1,dash=''):
        self.add(f'<line x1="{x}" y1="{y}" x2="{xx}" y2="{yy}" stroke="{color}" stroke-width="{width}" stroke-dasharray="{dash}"/>')
    def rect(self,x,y,w,h,color,opacity=1): self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}" opacity="{opacity}"/>')
    def path(self,pts,color,width=4,fill='none',attrs=''):
        d=' '.join(('M' if i==0 else 'L')+f'{x:.2f},{y:.2f}' for i,(x,y) in enumerate(pts))
        self.add(f'<path d="{d}" stroke="{color}" stroke-width="{width}" fill="{fill}" stroke-linejoin="round" {attrs}/>')
    def chart(self, rows, box, title, color='#286cda', key='index', domain=None, yrange=None, band=None, markers=None, running=False, unit='', percent=False):
        """Straight observed quarter segments only; a missing quarter breaks the path."""
        self.counter+=1; ident=f'{self.prefix}-c{self.counter}'; x,y,w,h=box
        lo,hi=domain or (qi(rows[0]['quarter']),qi(rows[-1]['quarter']))
        rows=[r for r in rows if lo<=qi(r['quarter'])<=hi and r.get(key) is not None]
        assert rows, f'No data {title}'
        vals=[r[key] for r in rows]
        if band: vals += [r[k] for r in rows for k in band if r.get(k) is not None]
        low,high=yrange or (min(0,min(vals)), max(vals)*1.12)
        if high==low: high=low+1
        X=lambda q: x+(qi(q)-lo)/(hi-lo)*w
        Y=lambda v: y+h-(v-low)/(high-low)*h
        self.text(x,y-53 if markers else y-23,title,28,weight=700)
        for i in range(4):
            v=low+(high-low)*i/3; yy=Y(v)
            self.line(x,yy,x+w,yy)
            self.text(x-12,yy+7,fmt(v)+('%' if percent else ''),21,anchor='end',color='#526872')
        ticks=[lo,(lo+hi)//2,hi]
        for i,t in enumerate(ticks):
            xx=x+(t-lo)/(hi-lo)*w
            self.text(xx,y+h+32,qstr(t),22,anchor=['start','middle','end'][i],color='#526872')
        if unit: self.text(x+w,y-53 if markers else y-23,unit,21,anchor='end',color='#526872')
        if markers:
            a,b=markers[0][0],markers[-1][0]
            self.rect(X(a),y,max(0,X(b)-X(a)),h,color,.07)
        groups=[]; group=[]
        for r in rows:
            if group and qi(r['quarter'])-qi(group[-1]['quarter'])!=1: groups.append(group);group=[]
            group.append(r)
        if group: groups.append(group)
        if band:
            for g in groups:
                pts=[(X(r['quarter']),Y(r[band[0]])) for r in g]+[(X(r['quarter']),Y(r[band[1]])) for r in reversed(g)]
                self.path(pts,'none',0,color,attrs='opacity="0.12"')
        if running:
            peak=-math.inf; pts=[]
            for r in rows: peak=max(peak,r[key]);pts.append((X(r['quarter']),Y(peak)))
            self.path(pts,'#526872',2,attrs='stroke-dasharray="8 7"')
        for g in groups: self.path([(X(r['quarter']),Y(r[key])) for r in g],color,4)
        if markers:
            for j,(q,label) in enumerate(markers):
                match=next((r for r in rows if r['quarter']==q),None)
                if not match: continue
                xx,yy=X(q),Y(match[key]); self.line(xx,y,xx,y+h,color,1,'5 6')
                self.add(f'<circle cx="{xx}" cy="{yy}" r="7" fill="#f6f4ef" stroke="{color}" stroke-width="4"/>')
                # Reserve an annotation row ABOVE the data, keeping text off price lines.
                labelx=[x+10,x+w*.5,x+w-10][min(j,2)]
                self.text(labelx,y-20,label,23,color,700,['start','middle','end'][min(j,2)])
        self.add(f'<line id="{ident}-line" x1="{x}" y1="{y}" x2="{x}" y2="{y+h}" stroke="{color}" stroke-width="2" stroke-dasharray="5 6"/><circle id="{ident}-dot" r="7" fill="{color}"/><text id="{ident}-read" x="{x+w}" y="{y+h+65}" text-anchor="end" font-size="23" font-weight="700"/>')
        self.drivers.append(dict(id=ident,hideRead=h<100,points=[dict(x=round(X(r['quarter']),3),y=round(Y(r[key]),3),q=r['quarter'],v=r[key],extra=(f" · 면적 {r['median_area_m2']:.1f}㎡ · {r['n']:,}건" if 'median_area_m2' in r else '')) for r in rows],unit=unit,percent=percent))
    def finish(self): return '<svg class="rpr-plot" viewBox="0 0 1920 1080">'+''.join(self.svg)+'</svg>'

def index_rows(d,r,common=False):
    rows=d['series'][r]
    if not common: return rows
    base=next(x['index'] for x in rows if x['quarter']=='2015Q1')
    return [dict(x,index=x['index']/base*100) for x in rows if x['quarter']>='2015Q1']

def episode_chart(a,d,r,peak,box=(145,265,1120,380)):
    e=next(e for e in d['episodes'] if e['region']==r and e['peak_quarter']==peak)
    end=e['first_return_quarter'] or '2026Q2'; trough=e['trough_quarter']
    marks=[(peak,'고점 '+peak),(trough,'관측 저점 '+trough),(end,('최초 복귀 ' if e['first_return_quarter'] else '미회복 · ')+end)]
    domain=(max(qi(d['series'][r][0]['quarter']),qi(peak)-2),min(qi('2026Q2'),qi(end)+2))
    # Zooming into an episode does not rebase its original supported-history index.
    unit=f"{d['series'][r][0]['quarter']}=100"
    a.chart(d['series'][r],box,r+' · 자체 지수 · 고점에서 최초 복귀까지',COLORS[r],domain=domain,markers=marks,unit=unit)
    a.text(1380,310,r,42,COLORS[r],700)
    if e['first_return_quarter']:
        quarters=int(e['peak_to_first_return_quarters']); yrs=quarters//4; months=(quarters%4)*3
        a.text(1380,382,f'{quarters}분기',55,COLORS[r],700)
        a.text(1380,429,f'{yrs}년'+(f' {months}개월' if months else ''),35,weight=700)
    else:
        a.text(1380,382,'관측 종료 시 미회복',31,COLORS[r],700)
        a.text(1380,429,'미래 복귀일 미표시',26)
    a.text(1380,508,'고점 → 관측 저점',25)
    a.text(1380,551,f"{e['max_drawdown_pct']:.2f}%",43,weight=700)
    a.text(1380,602,'실제 보유 수익률 아님',23,color='#526872')
    dd=[dict(x,index=x['drawdown']) for x in d['series'][r]]
    a.chart(dd,(145,745,1120,75),'누적 최고 대비 낙폭',COLORS[r],domain=domain,yrange=(-max(20,abs(e['max_drawdown_pct'])*1.15),0),percent=True)
    return e

def layout(d,s,b):
    a=Art(b['beat_id']); sn=int(s['scene_id'][1:]); pn=int(b['beat_id'].split('P')[1]); note='수집 실거래 자체 비교 지수 · 실제 보유 수익률 아님 · 2026Q2 관측 종료'
    if sn==4 or (sn==1 and pn==2) or (sn==12 and pn in (1,2,4,5,6)):
        for i,r in enumerate(d['regions'][:6]):
            col=i%3;row=i//3
            a.chart(index_rows(d,r),(135+col*600,260+row*300,480,190),r,COLORS[r],yrange=(0,600),unit='2006Q1=100')
            if sn==4 and pn==2 and r in ('서울','대구'):
                a.text(135+col*600,282+row*300,f"2026Q2  {d['summary'][r]['latest_index']:.2f}",28,COLORS[r],700)
        if sn==4 and pn==3:
            note='CAGR: '+ ' / '.join(f"{r} {d['summary'][r]['full_period_cagr_pct']:.2f}%" for r in d['regions'][:6])+' · 전체 기간 경로와 함께 비교'
        if sn==12 and pn>=5: note='다음 분석: 공급·준공 후 미분양 · 날짜 헤더·행정경계 확인 전 시계열 값 미표시'
    elif sn==2 and pn==1:
        years=sorted(set(int(v['year']) for v in d['annual_volume'])); totals=[sum(v['valid_transactions'] for v in d['annual_volume'] if int(v['year'])==yy) for yy in years]
        a.text(110,250,'보유 7개 지역 유효거래',30,weight=700);a.text(110,326,f"{sum(totals):,}건",70,'#286cda',700)
        mx=max(totals)
        for i,(yy,v) in enumerate(zip(years,totals)):
            x=120+i*82;h=v/mx*350
            a.rect(x,780-h,50,h,'#286cda' if yy!=2026 else '#ae6027')
            if yy%2==0: a.text(x+25,815,str(yy),22,anchor='middle')
        note='2026년은 상반기 · 세종 2006~2014 9,776건: 현행 코드 조회 이력, 과거 행정경계 포괄성 미검증'
    elif sn in (2,3):
        r='서울'; raw=d['all_transactions'][r]
        a.chart(raw,(150,280,755,365),'전체 거래 · ㎡당 가격 중위값','#286cda',key='median_price_per_m2_manwon',band=('p25_price_per_m2_manwon','p75_price_per_m2_manwon'),unit='만원/㎡')
        a.chart(d['series'][r],(1090,280,675,365),'동일 단지·면적 매칭지수','#1c7386',unit='2006Q1=100')
        a.text(150,775,'음영 = ㎡당 가격 25~75백분위',25)
        a.text(1090,775,'양쪽 분기 2건 이상 · 연결 30단지 이상',24)
        a.text(150,822,'서울 · 같은 분기의 거래 면적·건수를 커서에 연결',24)
        if pn==2:
            a.line(145,845,1765,845,'#286cda',3)
            note='거래 구성도 달라짐 · 면적 보정만으로 입지·연식이 같아지지는 않음 · 신뢰구간 아님'
        else: note='원가격 통계(모든 유효거래)와 매칭지수는 단위·표본이 다름 · 중위값 변화를 동일 품질 수익률로 해석하지 않음'
    elif sn in (1,6,7,8) or (sn==12 and pn==3):
        if sn==1: r,peak=('인천','2008Q3') if pn==1 else ('서울','2010Q1')
        elif sn==6: r,peak='서울','2008Q3' if pn==1 else '2010Q1'
        elif sn==7: r,peak=('경기','2008Q3') if pn==1 else ('인천','2008Q3')
        elif sn==8: r,peak=('부산','2017Q3') if pn==1 else ('대구','2015Q3') if pn==2 else ('부산','2022Q2')
        else: r,peak='인천','2008Q3'
        episode_chart(a,d,r,peak)
        if sn==1 and pn==1: a.text(1380,680,'서울 2010Q1 → 2015Q2',25);a.text(1380,725,'21분기 · 5년 3개월',28,'#286cda',700)
        if sn==6 and pn==3: a.text(1380,685,'2008년 사례: -11.48% / 4분기',22);a.text(1380,725,'2010년 사례: -10.74% / 21분기',22)
        if sn==7 and pn==3: note='시간의 출발점: 고점(보유 경험) / 관측 저점(사후 확인) · 저점을 사전에 안 매수기회로 표시하지 않음'
        if sn==8: note='대구 전 기간 군위 제외 · 미회복은 2026Q2에서 검열 · 미래 저점·복귀선 미표시'
    elif sn==5:
        r='서울' if pn<3 else '경기'
        a.chart(d['series'][r],(145,275,1130,290),r+' · 실제 지수와 누적 최고',COLORS[r],running=True,unit='2006Q1=100')
        a.chart([dict(x,index=x['drawdown']) for x in d['series'][r]],(145,720,1130,90),'누적 최고 대비 낙폭',COLORS[r],yrange=(-25,0),percent=True)
        if pn==2:
            for i,(q,v) in enumerate([('2008Q3',-11.48),('2010Q1',-10.74),('2021Q4',-12.79)]): a.text(1385,340+i*105,f'{q}  {v:.2f}%',28,weight=700)
            a.text(1385,700,'서울 최신 낙폭 0%',31,'#286cda',700)
        else:
            for i,r in enumerate(d['regions']): a.text(1385,285+i*67,f"{r}  {d['summary'][r]['all_time_high_first_quarter']}",27,weight=700)
        note='누적 최고는 해당 분기까지의 값만 사용 · 세종 2015Q1 이후 · 경기 기본표본 민감도는 S010에서 별도 비교'
    elif sn==9:
        common=pn==3
        for i,r in enumerate(['대전','세종']):
            a.chart(index_rows(d,r,common),(150+i*880,290,740,400),r,COLORS[r],domain=(qi('2006Q1'),qi('2026Q2')) if not common else None,unit='2015Q1=100' if common else ('2006Q1=100' if r=='대전' else '2015Q1=100'))
        a.text(1030,815,'세종 2006~2014 매칭지수: 공백',26,'#8a652a',700)
        note='세종 과거 유효거래 9,776건 ≠ 2006년 세종시 전체 시장 · 서로 다른 관측 기간의 배수 순위 미표시'
    elif sn==10 and pn==3:
        a.chart(d['series']['경기'],(145,300,1000,400),'경기 · 기본 2건 매칭지수',COLORS['경기'],unit='2006Q1=100')
        a.text(1270,255,'최근 주기 기준 고점 대비',30,weight=700)
        a.text(1270,294,'고점 탐색: 2020Q1~2022Q4',24)
        for i,row in enumerate(x for x in d['sensitivity'] if x['region']=='경기'):
            y=385+i*140; a.text(1270,y,f"{row['min_trades']}건 이상  ·  고점 {row['peak_quarter']}",26)
            a.text(1270,y+50,f"{row['latest_vs_peak_pct']:+.2f}%",43,'#286cda',700)
        note='요약값 · 3/5건 시계열 미연결 · +5.24%는 전체 관측 최고점 대비가 아님'
    elif sn==10:
        r='서울' if pn==1 else '세종'; rows=d['series'][r]
        a.chart(rows,(145,280,1430,430),r+' · 전체 경로',COLORS[r],unit='시작점=100')
        if pn==1:
            # Endpoints only: visibly labelled explanatory chord, not an observed series.
            a.line(145,710-(rows[0]['index']/(max(x['index'] for x in rows)*1.12))*430,1575,710-(rows[-1]['index']/(max(x['index'] for x in rows)*1.12))*430,'#526872',2,'10 9')
            a.text(160,824,'점선: 시작·끝 복리 설명용 보조선',25)
        else:
            for i,(q,v) in enumerate([('2023Q2',.96),('2021Q2',-3.41),('2016Q2',5.88)]): a.text(250+i*500,820,f'{q} → 2026Q2  {v:+.2f}%',26,weight=700)
        note='기간별 연환산 변화율과 실제 분기 경로를 구분 · 미래 경로 추정 아님'
    elif sn==11:
        a.chart(d['series']['대구'],(145,280,1030,310),'대구 · 가격 경로 (군위 제외)',COLORS['대구'],unit='2006Q1=100')
        for i,t in enumerate(['공급·준공 후 미분양','가구·연령 이동','일자리·금융 여건']):
            a.line(145,730+i*48,1175,730+i*48,'#c6d0cc',2,'6 6'); a.text(155,719+i*48,t+' — 검증 전 값 미표시',24)
        a.text(1300,280,'원인 기여율·인과 화살표 없음',26,weight=700)
        if pn==2:
            a.text(1300,395,'대구 준공 · 전체 주택',29,weight=700)
            for i,(yr,v) in enumerate([(2023,31630),(2024,29441)]):
                a.text(1300,465+i*130,f'{yr}년',27);a.rect(1300,482+i*130,v/31630*420,34,'#286cda');a.text(1730,510+i*130,f'{v:,}호',30,weight=700,anchor='end')
        note='국토교통부 원표 · 전체 주택·시점별 공표 경계 / 가격은 군위 제외 · 검증된 기술통계 예시, 인과 검증 아님'
    else: raise ValueError(b['beat_id'])
    return a.finish(),a.drivers,note

def timeline_script(cid,drivers):
    return '''<script>(()=>{const tl=gsap.timeline({paused:true});const jobs=JOBS;
for(const job of jobs){const state={p:0};const line=document.getElementById(job.id+'-line'),dot=document.getElementById(job.id+'-dot'),read=document.getElementById(job.id+'-read');
const update=()=>{const ps=job.points;const p=Math.max(0,Math.min(1,state.p));const i=Math.min(ps.length-1,Math.round(p*(ps.length-1)));const d=ps[i];
line.setAttribute('x1',d.x);line.setAttribute('x2',d.x);dot.setAttribute('cx',d.x);dot.setAttribute('cy',d.y);
read.textContent=job.hideRead?'':d.q+'  '+d.v.toLocaleString('ko-KR',{maximumFractionDigits:2})+(job.percent?'%':'')+(job.unit?' · '+job.unit:'')+d.extra;};
tl.fromTo(state,{p:0},{p:1,duration:Math.max(.1,job.duration-1.2),ease:'none',onUpdate:update,immediateRender:false},job.start+.3);update();}
window.__timelines[CID]=tl;})();</script>'''.replace('JOBS',json.dumps(drivers,ensure_ascii=False)).replace('CID',json.dumps(cid))

def shell(cid,duration,body,script,template=False):
    root=f'<div id="root" data-composition-id="{cid}" data-width="1920" data-height="1080" data-duration="{duration:.6f}" data-fps="30">{body}</div>'
    if template:
        # Shared CSS/font/GSAP live on the assembled host. Template transport retains local script.
        return '<!doctype html><html lang="ko"><head><meta charset="utf-8"></head><body><template><style>#root{position:absolute;inset:0;width:100%;height:100%}</style>'+root+script+'</template></body></html>'
    return '<!doctype html><html lang="ko"><head><meta charset="utf-8"><script src="assets/gsap.min.js"></script><style>'+CSS+'</style></head><body>'+root+script+'</body></html>'

def caption_parts(text):
    # Punctuation/phrase-first, with original spans, provisional duration only.
    parts=[]
    for sentence in re.findall(r'[^.!?]+[.!?]?',text):
        words=sentence.strip().split(); chunk=[]
        for w in words:
            if chunk and len(' '.join(chunk+[w]))>57: parts.append(' '.join(chunk));chunk=[]
            chunk.append(w)
        if chunk: parts.append(' '.join(chunk))
    return parts

def make_timing(scenes,lockpath=None):
    if not lockpath:
        t=0;beats=[]
        for s in scenes:
            for b in s['beats']:
                dur=max(8,len(b['narration_text'])/6.0+.8)
                parts=caption_parts(b['narration_text']); cursor=t; caps=[]
                total=sum(len(p) for p in parts)
                for text in parts:
                    end=cursor+dur*len(text)/total;caps.append(dict(start=cursor,end=end,text=text));cursor=end
                beats.append(dict(beat_id=b['beat_id'],scene_id=s['scene_id'],start=t,end=t+dur,duration=dur,captions=caps,audio_path=None));t+=dur
        return dict(script_sha256=SHA,timing_locked=False,timing_basis='provisional_6chars_per_second_not_audio',beats=beats,last_spoken_end=None)
    lock=read(lockpath);assert lock['script_sha256']==SHA and lock['timing_locked'] is True,'Actual approved v3 timing lock required'
    ids=[b['beat_id'] for s in scenes for b in s['beats']];assert [b['beat_id'] for b in lock['beats']]==ids,'39 exact ordered beats required'
    previous=0
    for b in lock['beats']:
        assert b['scene_id']==b['beat_id'].split('-')[0]
        assert b['start']>=previous-.00001 and b['end']>b['start']
        assert abs(b['duration']-(b['end']-b['start']))<.035
        p=Path(b['audio_path']);p=p if p.is_absolute() else EP/p
        assert p.is_file(),f'Missing audio {p}'
        b['resolved_audio_path']=str(p)
        assert b['captions'],'Measured semantic captions required'
        for c in b['captions']: assert b['start']-.035<=c['start']<c['end']<=b['end']+.035,'Caption times must be BODY-relative'
        previous=b['end']
    # Contract defines caption end as speech end. Optional explicit alignment is stronger.
    lock['last_spoken_end']=lock.get('last_spoken_end',max(c['end'] for b in lock['beats'] for c in b['captions']))
    assert lock['last_spoken_end']<=lock['beats'][-1]['end']+.035
    lock['timing_basis']='actual_jun_timing_lock_caption_end_or_explicit_last_spoken_end'
    return lock

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--timing-lock');args=ap.parse_args()
    script=EP/'outputs/script-review-v3/script_v3.md'; scene_path=EP/'outputs/script-review-v3/scenes_v3.json'; data_path=EP/'visual/production-v1/chart_data.json'
    assert digest(script)==SHA,'Approved script changed'
    assert digest(data_path)==DATA_SHA,'Chart revision changed; director must authorize new input'
    scenes=read(scene_path)['scenes'];d=read(data_path)
    assert len(scenes)==12 and sum(len(s['beats']) for s in scenes)==39
    for p in (PROJECT,CHECKS,PREVIEWS,PROJECT/'assets/fonts',PROJECT/'compositions',PROJECT/'preview'):p.mkdir(parents=True,exist_ok=True)
    old=EP.parent/'housing-choice-networth-20261020/outputs/regional-motion-v1/assets'
    shutil.copy2(old/'gsap.min.js',PROJECT/'assets/gsap.min.js')
    for f in ('Pretendard-Regular.woff2','Pretendard-Bold.woff2'):shutil.copy2(old/'fonts'/f,PROJECT/'assets/fonts'/f)
    icons=PROJECT/'assets/emoji';icons.mkdir(exist_ok=True)
    for f in ('집.png','달력.png','돋보기.png','emoji_LICENSE.md'):
        source=PROJECT.parent/'reusable_assets'/f
        if source.is_file(): shutil.copy2(source,icons/f)
    shutil.copy2(data_path,PROJECT/'assets/chart_data.json')
    timing=make_timing(scenes,args.timing_lock);js(PROJECT/'timing_resolved.json',timing)
    write(PROJECT/'BRIEF.md','''---
workflow: general-video
flow: automation
storyboard: no
message: "긴 기간에 오른 가격과 고점 뒤 기다린 시간은 다른 경험이다"
aspect: 1920x1080
language: ko
length: actual-Jun-audio-pending
---

## Intent

승인 대본 v3의 12장면·39문단을 실제 전체 분기 경로로 설명한다. 이번 산출은 무음 8초 프리뷰 3개와 재현 가능한 편집 준비본이다. 본편은 실제 Jun 음성의 timing lock 이후 조립한다.

## Assets

- assets/chart_data.json — visual/production-v1 동결 데이터의 로컬 사본
- assets/fonts/ — 기존 regional-motion-v1의 Pretendard
- ../reusable_assets/manifest.json — 총괄이 고정한 브랜드·음악·기준 프레임 (읽기 전용)

## Customizations

전 기간 실제 꺾은선, 동기화된 분기 커서, 고점·관측 저점·최초 복귀 표식, 누적 최고 낙폭, 원가격의 사분위 범위·거래 면적·건수. 3/5건 민감도는 요약값만 표시.

## Notes

새 유료 생성·클라우드 렌더·업로드 없음. 브랜드는 150/300프레임 원본만 나중 조립. 마지막 실제 발화+3초 후 아웃트로. 추정 타이밍으로 전체 렌더 금지. 기존 승인 대본의 내용·순서를 바꾸지 않음.
''')
    write(PROJECT/'frame.md','''# 채널 화면 규격

크림 #f6f4ef, 잉크 #173348, 파랑 #286cda, Pretendard 400/700. 제목 43px, 본문 자막 39px, 주요 수치 43~70px, 축 21~23px. 출처 18px은 채널 규격의 보조 레이어다.

이 영상의 비유는 가격의 선을 따라 긴 기다림을 읽는 분기 달력이다. 커서는 실제 관측 분기로만 이동한다. 실제 데이터의 선형 연결은 관측 사이 안내선이며 추가 관측값을 만들지 않는다. 결측 분기는 선을 끊는다.

레이어: 제목 y94~147 / 자료 x80~1840,y210~852 / 조건 y866~898 / 흰 자막박스 x96,y916,w1728,h110 / 자막 y922~1020 / 출처 y1042~1067. 출처는 자막 아래. 전체 화면 줌 없음. 그래프·자막·출처는 서로 다른 레이어.

6개 패널은 동일한 0~600 지수축, 2006Q1~2026Q2를 유지한다. 세종은 별도 패널과 2015Q1 출발. 원가격(만원/㎡)과 매칭지수(시작점=100)는 같은 세로축을 공유하지 않는다. IQR은 ㎡당 가격 25~75백분위이며 신뢰구간 아님.

미회복은 2026Q2에서 끝난다. 빈 시계열·미래 경로·인과 화살표·3/5건 곡선은 생성하지 않는다. AI 장소 이미지 없음. 브랜드의 기존 AI 개념 도시 자료는 실제 분석 지역 자료로 소개하지 않는다.
''')
    caption_limit=timing['last_spoken_end'] if timing['timing_locked'] else timing['beats'][-1]['end']
    mounts=[];caphtml=[f'<div class="rpr-caption-box clip" style="inset:auto;left:96px;top:916px" data-start="0" data-duration="{caption_limit:.6f}" data-track-index="7"></div>']; audio=[];board=['---\nformat: 1920x1080\nmessage: "가격의 상승과 회복의 시간은 다른 경험이다"\nmode: autonomous\n---\n']; source='출처: 보유 아파트 매매 실거래 · 자체 집계/동일 단지·면적 매칭 · 2026Q2 관측 종료'
    allcaps=[c for b in timing['beats'] for c in b['captions']]
    display_ends={id(c):(allcaps[i+1]['start'] if i+1<len(allcaps) else c['end']) for i,c in enumerate(allcaps)}
    plans=[]
    for n,s in enumerate(scenes):
        sb=[b for b in timing['beats'] if b['scene_id']==s['scene_id']];start=sb[0]['start'];end=sb[-1]['end'];dur=end-start; content=[];drivers=[]
        board.append(f"\n## Frame {n+1} — {s['message']}\n\n- status: animated\n- src: compositions/{s['scene_id']}.html\n- duration: {dur:.3f}s\n- timing: {'actual' if timing['timing_locked'] else 'provisional'}\n- transition_in: cut\n- rules: chart-scrub-readout, svg-path-draw\n")
        for original,b in zip(s['beats'],sb):
            graphic, jobs,note=layout(d,s,original);local=b['start']-start
            for job in jobs:job.update(start=local,duration=b['duration'])
            drivers.extend(jobs)
            icon={3:'집.png',7:'달력.png',10:'돋보기.png'}.get(n+1)
            iconhtml=f'<img src="assets/emoji/{icon}" alt="" style="position:absolute;left:1748px;top:166px;width:64px;height:64px">' if icon else ''
            body=f'<div class="rpr-head"><span>부동산 데이터 해설</span><span>{s["scene_id"]} · {original["beat_id"].split("-")[1]}'+(' · 타이밍 시안' if not timing['timing_locked'] else '')+f'</span></div><h1 class="rpr-title">{n+1:02d}  {esc(s["message"])}</h1><div class="rpr-sub">{esc(original["beat_id"])} · '+('실제 분기 데이터 · 음성 대기' if not timing['timing_locked'] else '실제 분기 데이터')+f'</div>{iconhtml}{graphic}<div class="rpr-note">{esc(note)}</div>'
            content.append(f'<section id="{original["beat_id"]}" class="rpr-beat clip" data-start="{local:.6f}" data-duration="{b["duration"]:.6f}" data-track-index="1">{body}</section>')
            board.append(f"\n{original['beat_id']}: {original['visual']}\n")
            plans.append(dict(beat_id=original['beat_id'],scene_id=s['scene_id'],start=b['start'],end=b['end'],visual=original['visual'],source=original['source'],chart_ids=[j['id'] for j in jobs]))
            for i,c in enumerate(b['captions']):
                caphtml.append(f'<div id="cap-{original["beat_id"]}-{i}" class="rpr-caption clip" data-start="{c["start"]:.6f}" data-duration="{display_ends[id(c)]-c["start"]:.6f}" data-track-index="8">{esc(c["text"])}</div>')
            if timing['timing_locked']:
                dest=PROJECT/'assets/audio'/f'{b["beat_id"]}{Path(b["resolved_audio_path"]).suffix}';dest.parent.mkdir(exist_ok=True);shutil.copy2(b['resolved_audio_path'],dest)
                audio.append(f'<audio id="audio-{b["beat_id"]}" class="clip" src="{dest.relative_to(PROJECT).as_posix()}" data-start="{b["start"]:.6f}" data-duration="{b["duration"]:.6f}" data-track-index="9" data-volume="1"></audio>')
        write(PROJECT/f'compositions/{s["scene_id"]}.html',shell(s['scene_id'],dur,''.join(content),timeline_script(s['scene_id'],drivers),True))
        js(PROJECT/f'compositions/{s["scene_id"]}.motion.json',{'duration':dur,'assertions':[{'kind':'appearsBy','selector':f'#{b["beat_id"]} .rpr-title','bySec':b['start']-start+.2} for b in sb]})
        mounts.append(f'<div id="mount-{s["scene_id"]}" class="clip" data-composition-id="{s["scene_id"]}" data-composition-src="compositions/{s["scene_id"]}.html" data-start="{start:.6f}" data-duration="{dur:.6f}" data-track-index="1" data-width="1920" data-height="1080"></div>')
    total=timing['beats'][-1]['end'];body=''.join(mounts+caphtml+audio)+f'<div class="rpr-source">{source}</div>'
    write(PROJECT/'index.html',shell('main',total,body,'<script>const tl=gsap.timeline({paused:true});window.__timelines["main"]=tl;</script>'))
    js(PROJECT/'index.motion.json',{'duration':total,'assertions':[{'kind':'staysInFrame','selector':'#cap-S001-P1-0'},{'kind':'staysInFrame','selector':'.rpr-source'}]})
    write(PROJECT/'STORYBOARD.md','\n'.join(board));js(PROJECT/'beat_manifest.json',{'timing_locked':timing['timing_locked'],'duration':total,'beats':plans})
    for name,si,pi in [('full2006paths',3,0),('incheon2008-2016recovery',6,1),('rawmedianvsindex',2,2)]:
        s=scenes[si];b=s['beats'][pi];graphic,jobs,note=layout(d,s,b)
        for job in jobs:job.update(start=0,duration=8)
        previewcaption={'full2006paths':'2006년을 100으로 맞춘 여섯 지역의 실제 분기 경로입니다.','incheon2008-2016recovery':'인천은 2008년 고점에서 처음 돌아오기까지 31분기가 걸렸습니다.','rawmedianvsindex':'전체 거래의 중위값과 같은 단지·면적의 지수는 따로 읽습니다.'}[name]
        icon={3:'집.png',7:'달력.png'}.get(si+1)
        iconhtml=f'<img src="assets/emoji/{icon}" alt="" style="position:absolute;left:1748px;top:166px;width:64px;height:64px">' if icon else ''
        content=f'<div class="rpr-head"><span>부동산 데이터 해설</span><span>무음 모션 시안 · 임시 타이밍 · {b["beat_id"]}</span></div><h1 class="rpr-title">{si+1:02d}  {esc(s["message"])}</h1><div class="rpr-sub">실제 분기 데이터 · 대표 8초 발췌 · 음성 확정 후 재동기화</div>{iconhtml}{graphic}<div class="rpr-note">{esc(note)}</div><div class="rpr-caption-box"></div><div class="rpr-caption">{esc(previewcaption)}</div><div class="rpr-source">{source}</div>'
        page=shell(name,8,content,timeline_script(name,jobs)).replace('src="assets/','src="../assets/').replace('url(assets/','url(../assets/')
        write(PROJECT/f'preview/{name}.html',page)
        js(PROJECT/f'preview/{name}.motion.json',{'duration':8,'maxStaticSec':2,'assertions':[{'kind':'staysInFrame','selector':'.rpr-caption'},{'kind':'keepsMoving','withinSelector':'#root'}]})
    deps={str(p.relative_to(REPO)):digest(p) for p in [script,scene_path,data_path,EP/'outputs/production-v1-jun/data_contract.md',REPO/'config/channel_style_tokens.json']}
    js(CHECKS/'input_versions.json',{'task_id':'RPR-PROD1-EDITOR','inputs':deps,'scene_count':12,'beat_count':39,'index_rows':sum(len(x) for x in d['series'].values()),'raw_quarters':sum(len(x) for x in d['all_transactions'].values()),'episode_count':len(d['episodes']),'timing_locked':timing['timing_locked'],'body_duration':total,'brand_not_assembled':True})
    js(PROJECT/'assembly_plan.json',{'status':'not_assembled','requires_actual_timing_lock':True,'reusable_assets_manifest':'../reusable_assets/manifest.json','intro_video_frames':150,'outro_video_frames':300,'fps':30,'container_duration_not_video_frame_count':True,'intro_body_offset_seconds':5,'last_spoken_end':timing.get('last_spoken_end'),'outro_body_start':timing['last_spoken_end']+3 if timing['timing_locked'] else None,'outro_final_start':5+timing['last_spoken_end']+3 if timing['timing_locked'] else None,'audio_tail_policy':'preserve_PCM_tail_inside_3s_gap; do_not_use_container_duration_as_speech_end','bgm':'director manifest only; no new sourcing; mix and listen in later assembly'})
    write(PROJECT/'package.json',json.dumps({'name':'rpr-production-v1','private':True,'type':'module','scripts':{'check':'npx.cmd --no-install hyperframes check','rebuild':'python ../../../editor/production-v1/build.py'}},indent=2))
    print(json.dumps({'scene_count':12,'beat_count':39,'timing_locked':timing['timing_locked'],'body_duration':round(total,3),'previews':3,'project':str(PROJECT)},ensure_ascii=False))

if __name__=='__main__':main()
