"""Main visual families. Data and timing are injected by build.py; no IO here."""
import re
from caption_tools import norm,translated_index,local_word_time

BLUE='#286cda';INK='#173348';MUTED='#536873';TEAL='#167f86';GOLD='#88631b'

def number_aliases(v):
    v=abs(v);out=[f'{v:,}',str(v)]
    if v>=10000:out += [f'{int(v)//10000}만 {int(v)%10000:,}',f'{int(v)//10000}만{int(v)%10000:,}']
    if v==10:out += ['열 쌍']
    return out

def install_visuals(g):
    ctx=dict(g);ctx['anchor_audit']=[];ctx['layout_families']={}
    txt,box,img,tween=[ctx[k] for k in ['txt','box','img','tween']]
    regions,photos=ctx['regions'],ctx['photos']

    def exact(s,key,aliases):
        # Explicit director anchors take precedence. They are local scene seconds.
        if key in s['anchors']:
            at=float(s['anchors'][key]);basis='director_explicit_anchor'
        else:
            at=None;basis='static_no_exact_word_anchor'
            for st in s['sentence_times']:
                words=ctx['word_groups'].get(st['sentence_id'],[])
                reading=ctx['readings'].get(st['sentence_id'],st.get('reading_text') or st['text'])
                for a in aliases:
                    k=st['text'].find(str(a))
                    if k<0:continue
                    idx=translated_index(st['text'],reading,len(norm(st['text'][:k])))
                    # Refuse metadata from an unrelated sentence/old version.
                    if words:
                        at=local_word_time(words,idx,float(st['start_s']));basis='provider_word_char_display_reading_map';break
                if at is not None:break
        ctx['anchor_audit'].append({'scene_id':s['scene_id'],'key':key,'aliases':list(aliases),'local_s':at,'basis':basis})
        if at is not None:
            assert 0<=at<s['duration_s'],f'Anchor outside scene {s["scene_id"]}:{key}:{at}'
        return at

    def reveal(s,key,selector,aliases):
        at=exact(s,key,aliases)
        return tween(selector,{'opacity':0},{'opacity':1},at,.25) if at is not None else ''

    def fullname(r):return r['province']+' '+r['region']
    def shortname(r):return r['region'].split()[-1]
    def credit(rid,x,y,w):
        p=photos[rid];year=p.get('photo_capture_year') or '연도 미상'
        author=re.sub('<[^>]+>','',p['source_or_prompt'].get('author',''))
        # Compact on-screen credit; exact author/license/full URL remain in credits.json.
        author=re.sub(r'\s+',' ',author).strip()
        if len(author)>54:author=author[:51]+'…'
        return txt(p['actual_place'],x,y,w,27,700)+txt(f'실제 장소 자료사진 · 촬영 {year}',x,y+41,w,21,color=MUTED)+txt('사진: '+author+' · '+p['license']['name'],x,y+77,w,17,color=MUTED)

    def focus(rid,x,y,w=300,h=160,locator=True):
        # Static actual district path. Same-path same-map locator; no invented pins or zoom.
        part=img(f'../assets/{rid}_focus.svg',x,y,w*.56,h)
        if locator:part+=img(f'../assets/{rid}_locator.svg',x+w*.59,y+8,w*.41,h-16)
        return part

    def ladder(s,x,y,w=560,row_h=40):
        r=regions[s['region_id']];rank=r['rank'];lo=max(1,min(rank-2,16));ss=''
        ss+=txt('앞뒤 순위 · 같은 0–16,000쌍 척도',x,y,w,20,color=MUTED)
        for i,rank0 in enumerate(range(lo,lo+5)):
            q=next(v for v in regions.values() if v['rank']==rank0);yy=y+33+i*row_h;active=q['region_id']==r['region_id']
            unseen=rank0<rank
            col=BLUE if active else MUTED
            if active:ss+=box(x-12,yy-4,w+12,row_h-1,'#e2e7e7',4)
            ss+=txt(f'{rank0:02d}',x,yy,43,23,700,col)+txt('???' if unseen else shortname(q),x+49,yy,w*.39,23,700 if active else 400,col)
            ss+=txt('???' if unseen else f'{q["count2024"]:,}',x+w-115,yy,115,23,700,col)
            ss+=box(x+49,yy+31,w-170,3,'#dfe4e5',0)
            if not unseen:ss+=box(x+49,yy+31,(w-170)*q['count2024']/16000,3,BLUE if active else '#a4b4bd',0)
        return ss

    def current_value(s,x,y,w,size=82):
        r=regions[s['region_id']];pid=s['scene_id']+'-hero-value'
        ss=txt('거주 신혼부부',x,y,w,24,color=MUTED)+txt(f'{r["count2024"]:,}쌍',x,y+36,w,size,700,BLUE,id=pid)
        return ss,reveal(s,'count','#'+pid,number_aliases(r['count2024']))

    def comparison(s):
        r=regions[s['region_id']];rank=r['rank'];prev=next((v for v in regions.values() if v['rank']==rank+1),None)
        if not prev:return hero(s)
        rid=r['region_id'];P=s['scene_id'];n=r['count2024'];diff=n-prev['count2024'];ss='';an=''
        ss+=box(80,220,690,405,'#e7e9e4')+img(f'../assets/{rid}.jpg',80,220,690,405)+credit(rid,80,645,690)
        ss+=focus(rid,80,766,340,102)+txt(shortname(r)+' 경계',457,782,315,21,700)+txt('2024 통계구역 · 수도권 내 위치',457,822,315,19,color=MUTED)
        ss+=txt('옆 순위와 함께 읽는 거주 규모',850,220,990,29,700)
        for j,q in enumerate([r,prev]):
            yy=282+j*127;active=j==0;cid=f'{P}-pair-{j}';bid=cid+'-bar';v=q['count2024'];col=BLUE if active else MUTED
            ss+=txt(f'{q["rank"]}위  {fullname(q)}',850,yy,650,31,700,col)+txt(f'{v:,}쌍',1510,yy-4,330,39,700,col,id=cid)
            ss+=box(850,yy+64,990,20,'#dfe4e5',4)+box(850,yy+64,990*v/16000,20,col,4,'bar',bid)
            at=exact(s,'count' if active else 'comparison_value',number_aliases(v))
            if at is not None:an+=tween('#'+cid,{'opacity':0},{'opacity':1},at,.25)+tween('#'+bid,{'scaleX':0},{'scaleX':1},at,.6)
        ss+=txt('0',850,511,100,18,color=MUTED)+txt('8,000',1310,511,120,18,color=MUTED)+txt('16,000쌍',1720,511,150,18,color=MUTED)
        did=P+'-gap';ss+=txt(f'{shortname(prev)}보다 {diff:,}쌍 많음',850,555,990,43,700,BLUE,id=did)
        an+=reveal(s,'gap','#'+did,number_aliases(diff))
        ss+=ladder(s,1280,644,560,38)
        d=r.get('change_couples');mentioned=any(('전년' in t['text'] or '2023년' in t['text']) for t in s['sentence_times'])
        if d is not None and mentioned:
            ss+=txt('2023 → 2024',850,653,380,23,700)
            change=P+'-change';pc=r['change_percent_display'];sign='+' if d>=0 else '−'
            ss+=txt(f'{sign}{abs(d):,}쌍',850,700,380,51,700,TEAL if d>=0 else GOLD,id=change)
            ss+=txt(f'{abs(pc):.1f}% '+('증가' if d>=0 else '감소'),850,769,380,29,700,TEAL if d>=0 else GOLD)
            if prev.get('change_percent_display') is not None and shortname(prev) in ' '.join(t['text'] for t in s['sentence_times']):
                ppc=prev['change_percent_display'];ss+=txt(f'{shortname(prev)} {ppc:+.1f}%',850,819,380,23,color=MUTED)
            an+=reveal(s,'change','#'+change,number_aliases(abs(d)))
        else:
            ss+=txt(f'{rank}위 / 수도권 53개 구',850,653,380,29,700)
            ss+=txt(fullname(r),850,712,380,37,700,BLUE)
            ss+=txt('순위 옆에 규모 차이를 함께',850,813,400,23,color=MUTED)
        return ss,an

    def hero(s):
        rid=s['region_id']
        if rid in ['R20','R18','R14','R11']:
            # A 4:3/3:2 source receives a tall editorial slot, not a wide letterbox.
            ss=box(80,220,850,637,'#e7e9e4')+img(f'../assets/{rid}.jpg',80,220,850,637)
            val,an=current_value(s,1000,220,840,86);ss+=val
            ss+=focus(rid,1000,412,330,157)+credit(rid,1370,405,470)
            ss+=txt(shortname(regions[rid])+' 경계 · 수도권 내 위치 · 2024 통계구역',1000,588,840,21,color=MUTED)
            ss+=ladder(s,1000,646,840,37)
            return ss,an
        ss=box(80,220,1130,505,'#e7e9e4')+img(f'../assets/{rid}.jpg',80,220,1130,505)+credit(rid,80,746,1130)
        val,an=current_value(s,1280,220,560,81);ss+=val
        ss+=focus(rid,1280,396,560,166)+txt(shortname(regions[rid])+' 경계',1280,574,310,22,700)+txt('수도권 내 위치',1625,574,215,20,color=MUTED)
        ss+=ladder(s,1280,639,560,38)
        return ss,an

    def top5(s):
        rid=s['region_id'];r=regions[rid];P=s['scene_id'];ss=box(80,220,1120,465,'#e7e9e4')+img(f'../assets/{rid}.jpg',80,220,1120,465);an=''
        ss+=focus(rid,80,727,335,132)+credit(rid,455,717,745)
        ss+=txt('1만 쌍을 넘는 상위 5개 구',1260,220,580,28,700)
        for i in range(5):
            q=next(v for v in regions.values() if v['rank']==i+1);yy=278+i*91;active=q['region_id']==rid;col=BLUE if active else MUTED
            unseen=q['rank']<r['rank']
            if active:ss+=box(1244,yy-8,612,84,'#e2e7e7',10)
            ss+=txt(f'{i+1:02d}',1260,yy+1,75,42,700,col)+txt('???' if unseen else shortname(q),1348,yy,250,32,700,col)
            ss+=txt('???' if unseen else f'{q["count2024"]:,}',1615,yy,225,34,700,col)
            ss+=box(1348,yy+54,492,6,'#dfe4e5',0)
            if not unseen:ss+=box(1348,yy+54,492*q['count2024']/16000,6,col,0)
            if active:
                at=exact(s,'count',number_aliases(q['count2024']))
                if at is not None:an+=tween(f'#{P}-current-mark',{'opacity':0},{'opacity':1},at,.25)
        ss+=txt(f'현재 소개  {r["rank"]}위 · {fullname(r)}',1260,753,580,25,700,BLUE,id=P+'-current-mark')
        prev=next((v for v in regions.values() if v['rank']==r['rank']+1),None)
        if prev:
            diff=r['count2024']-prev['count2024'];pid=P+'-gap'
            ss+=txt(f'{shortname(prev)}보다 {diff:,}쌍 많음',1260,801,580,31,700,id=pid);an+=reveal(s,'gap','#'+pid,number_aliases(diff))
        if rid=='R01':ss+=txt('옛 서구 = 현재 서해구 + 검단구',1260,849,580,22,700)
        return ss,an

    def region_scene(s):
        rank=regions[s['region_id']]['rank'];family=s.get('layout_family')
        if not family:family='top5' if rank<=5 else 'hero' if rank in [20,18,17,14,11,9,7] else 'comparison'
        ctx['layout_families'][s['scene_id']]=family
        return {'hero':hero,'comparison':comparison,'top5':top5}[family](s)

    ctx.update(exact=exact,reveal=reveal,number_aliases=number_aliases,fullname=fullname,credit=credit,focus=focus)
    # Existing analysis scenes keep their data geometry, but focus follows exact spoken values.
    original_insight1=g['insight1'];original_insight2=g['insight2'];original_opening=g['opening'];original_overview=g['overview']
    def insight1(s):
        body,_=original_insight1(s);an='';P=s['scene_id']
        for rid,value in [('R18',111),('R17',78)]:
            at=exact(s,'branch_'+rid,number_aliases(value))
            an+=f'document.getElementById("{P}-{rid}-line").style.strokeDasharray="1";'
            if at is not None:an+=tween(f'#{P}-{rid}-line',{'strokeDashoffset':1},{'strokeDashoffset':0},at,.65)
        at=exact(s,'summary',['여섯 곳'])
        if at is not None:an+=tween(f'#{P}-summary',{'opacity':0},{'opacity':1},at,.3)
        return body,an

    def insight2(s):
        body,_=original_insight2(s);an='';P=s['scene_id']
        for category,key in [('초혼','first_marriage_couples'),('재혼','remarried_couples')]:
            for rid in ['R12','R13']:
                v=regions[rid][key];bid=f'{P}-{rid}-{category}';nid=bid+'-value';at=exact(s,'value_'+rid+'_'+category,number_aliases(v))
                an+=f'document.getElementById("{nid}").textContent="{v:,}";'
                if at is not None:an+=tween('#'+bid,{'scaleX':0},{'scaleX':1},at,.55)+tween('#'+nid,{'opacity':0},{'opacity':1},at,.25)
        for key,label,val in [('first','초혼: 영통구가 888쌍 더 많음',888),('remarried','재혼: 권선구가 830쌍 더 많음',830)]:
            pid=P+'-conclusion-'+key;body=body.replace(label,f'<span id="{pid}">{label}</span>')
            an+=reveal(s,'conclusion_'+key,'#'+pid,number_aliases(val))
        return body,an

    def conclusion(s):
        P=s['scene_id'];ss=box(80,220,830,398,'#e7e9e4')+img('../assets/R17.jpg',80,220,830,398)+credit('R17',80,638,830)
        ss+=txt('크기 · 변화 · 구성을 나란히',80,787,830,36,700,BLUE)
        rows=[('규모','기준일에 얼마나 많이 사는가','옆 순위와 몇 쌍 차이일까?'),('변화','강남구 +9.4%  /  옛 서구 −1.3%','1년 동안 어느 방향으로 달라졌을까?'),('구성','전체 기준 · 초혼 기준','어떤 부부를 세고 있을까?')]
        for i,(label,evidence,question) in enumerate(rows):
            y=230+i*173;ss+=txt(label,1000,y,820,34,700,BLUE)+txt(question,1000,y+51,820,33,700)+txt(evidence,1000,y+103,820,24,color=MUTED)
        ss+=txt('두 사람의 직장 · 예산 · 필요한 집 크기',1000,772,840,29,700)
        ss+=txt('다음 편: 지역별 아파트 후보 비교',1000,823,840,26,700,BLUE)
        return ss,''

    def overview(s,close=False):return conclusion(s) if close else original_overview(s,close)

    def opening(s):
        if s['scene_id']!='O001':return original_opening(s)
        ss=box(80,220,1040,480,'#e7e9e4')+img('../assets/R10.jpg',80,220,1040,480)+credit('R10',80,719,1040)
        ss+=txt('순위 한 칸의 차이',1210,232,630,32,700)
        ss+=txt('미추홀구 8,483쌍',1210,302,630,37,700,BLUE)+txt('노원구 8,473쌍',1210,365,630,37,700)
        ss+=txt('10쌍',1210,463,630,112,700,BLUE,id='O001-hook-value')
        ss+=txt('거주 규모는 이렇게 가깝습니다',1210,617,630,28,700)
        ss+=txt('20위 → 1위',1210,734,630,60,700)+txt('수도권 53개 구 가운데 스무 곳',1210,818,630,28)
        an=reveal(s,'hook_value','#O001-hook-value',['열 쌍'])
        return ss,an

    g.update(region_scene=region_scene,insight1=insight1,insight2=insight2,overview=overview,opening=opening)
    return ctx
