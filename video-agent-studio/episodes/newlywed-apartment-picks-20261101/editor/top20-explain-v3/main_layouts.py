"""승인된 새 본문 전용 도입·비교·회수·마지막 유지 화면입니다."""
from caption_tools import norm,translated_index,local_word_time

def install(g,ctx):
    txt,box,img,tween=[g[k] for k in ['txt','box','img','tween']]
    def block(text,x,y,w,h,size=34,cl='',id=None):
        attr=f' id="{id}"' if id else ''
        return f'<div{attr} class="text fit {cl}" data-min-font="24" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;font-size:{size}px">{g["esc"](text)}</div>'
    def exact(s,key,aliases,sentence_id=None):
        for st in s['sentence_times']:
            if sentence_id and st['sentence_id']!=sentence_id:continue
            for alias in aliases:
                at=st['text'].find(str(alias))
                if at<0:continue
                reading=g['readings'][st['sentence_id']]
                index=translated_index(st['text'],reading,len(norm(st['text'][:at])))
                time=local_word_time(g['word_groups'][st['sentence_id']],index,None)
                if time is None or not 0<=time<s['duration_s']:raise ValueError('실제 발화 앵커 범위 오류: '+s['scene_id']+':'+key)
                ctx['anchor_audit'].append({'scene_id':s['scene_id'],'key':key,'sentence_id':st['sentence_id'],'local_s':time,'basis':'actual_new_v6_original_word_char_boundary'})
                return time
        raise ValueError('실제 새 발화 앵커 누락: '+s['scene_id']+':'+key)
    def reveal(s,key,selector,aliases,sentence_id=None):return tween(selector,{'opacity':0},{'opacity':1},exact(s,key,aliases,sentence_id),.25)

    def opening(s):
        ss=img('../assets/top20_overview.svg',80,220,1080,620)
        ss+=txt('수도권 53개 구 가운데',1220,230,620,33,700)
        ss+=txt('거주 수 TOP20',1220,300,620,57,700,'#286cda')
        ss+=txt('20위 → 1위',1220,395,620,68,700)
        for i,label in enumerate(['거주 규모','주거 특징·실제 랜드마크','동일 면적의 실거래가격']):
            ss+=txt(label,1220,550+i*96,620,31,700)
        return ss,''

    def insight1(s):
        rows=[g['regions']['R18'],g['regions']['R17']];ss='';anim=''
        for label,x in [('2023년',460),('2024년',1030),('전년 변화',1510)]:ss+=txt(label,x,220,320,30,700)
        for i,r in enumerate(rows):
            y=320+i*210;rid=r['region_id'];pid=s['scene_id']+'-'+rid
            ss+=txt(r['region'],80,y+20,340,36,700)
            ss+=txt(f"{r['count2023']:,}쌍",460,y,410,58,700)
            ss+=txt('→',910,y+4,110,55,700,'#536873')
            ss+=f'<div id="{pid}">'+txt(f"{r['count2024']:,}쌍",1030,y,430,58,700,'#286cda')+txt(('+' if r['change_couples']>0 else '−')+f"{abs(r['change_couples']):,}쌍",1510,y+9,330,48,700)+'</div>'
            anim+=reveal(s,'change_'+rid,'#'+pid,[f"{abs(r['change_couples']):,}쌍"],'I001-02')
        ss+=block('새로운 혼인과 혼인 5년 경과에 따른 집계 변화도 포함합니다.',80,760,1760,100,34)
        return ss,anim

    def insight2(s):
        a,b=g['regions']['R12'],g['regions']['R13'];ss='';anim=''
        for i,r in enumerate([a,b]):
            x=80+i*910;ss+=box(x,220,850,560,'#e7e9e4',12)+txt(r['region'],x+35,247,780,39,700)
            ss+=txt('신혼부부 전체',x+35,335,780,26)+txt(f"{r['count2024']:,}쌍",x+35,383,780,65,700)
            pid=s['scene_id']+'-'+r['region_id']+'-first';ss+=txt('초혼 부부',x+35,520,780,26)+txt(f"{r['first_marriage_couples']:,}쌍",x+35,568,780,65,700,'#286cda',id=pid)
            anim+=reveal(s,'first_'+r['region_id'],'#'+pid,[f"{r['first_marriage_couples']:,}쌍"],'I002-02')
        gap=abs(a['count2024']-b['count2024']);ss+=txt(f'전체 수 차이 {gap}쌍',80,812,1760,34,700,id='I002-gap')
        anim+=reveal(s,'total_gap','#I002-gap',[f'{gap}쌍'],'I002-01')
        return ss,anim

    def conclusion(s,hold=False):
        source=next(v for v in g['scenes'] if v['scene_id']=='C001');sid=s['scene_id'];ss='';anim=''
        for i,rid in enumerate(['R10','R06']):
            p=g['panels'][rid];r=g['regions'][rid];x=80+i*910;pid=sid+'-range-'+rid
            ss+=box(x,220,850,240,'#e7e9e4',12)+txt(r['region'],x+30,242,790,32,700)
            ss+=txt(p['display_price'],x+30,300,790,66,700,'#286cda',id=pid)+txt(f"지역 거래 {p['n']:,}건",x+30,398,790,25)
            if not hold:anim+=reveal(source,'range_'+rid,'#'+pid,[p['display_price']],'C001-01')
        ss+=txt('지역 아파트 실거래 중위값 · 2026.05~10 계약 · 전용 83~85㎡',80,484,1760,25,color='#536873')
        criteria=txt('직장 위치 · 필요한 면적 · 예산',80,570,1760,42,700)+block('지역과 단지의 범위 · 같은 계약기간과 면적 · 각각의 거래 건수',80,641,1760,85,31)
        ss+=f'<div id="{sid}-criteria">{criteria}</div>'
        ss+=txt('이어지는 지역 비교도 함께 살펴보겠습니다',80,760,1760,32,700)+txt('구독과 좋아요',80,818,1760,35,700,'#286cda',id=sid+'-cta')
        if not hold:
            anim+=reveal(source,'criteria','#'+sid+'-criteria',['직장 위치'],'C001-03')
            anim+=reveal(source,'cta','#'+sid+'-cta',['구독과 좋아요'],'C001-05')
        return ss,anim

    ctx.update(exact=exact,reveal=reveal)
    g.update(insight1=insight1,insight2=insight2,main_opening=opening,conclusion=conclusion)
    return ctx
