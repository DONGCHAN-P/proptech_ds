"""Offline portrait Shorts. Original Jun PCM, measured type, native motion, no API.

Run from repository root: tools/python311/python.exe -X utf8 <this file>
Only this directory and episode outputs/jun-quality-v2/shorts are written.
"""
from pathlib import Path
from functools import lru_cache
import argparse, hashlib, json, math, subprocess, wave, sys, re, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
EP = HERE.parents[2]
ROOT = EP.parents[2]
OUT = EP / 'outputs/jun-quality-v2/shorts'
N = EP / 'narration/jun-user-script-v1'
FF = ROOT / 'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
PROBE = ROOT / 'video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe'
FPS, W, H = 30, 1080, 1920
INK, BLUE, GOLD, GREEN = '#173348', '#286cda', '#a77725', '#267b69'
CREAM, PALE, MUTED = '#f6f4ef', '#e2e9e5', '#536b78'
load = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
def save(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
def write(p, s):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding='utf-8')

# Actual scene-relative ranges, never the landscape-film clock.
SPECS = [
 dict(id='promo', name='01_promo_jun_v3', title='돈은 모았는데, 어떤 집을 살 수 있을까? | 내 집 예산',
      description='현금 1억부터 5억까지, 모은 돈과 집값을 연결하는 순서를 본편에서 살펴봅니다. 집값에 넣을 돈, 남겨둘 준비금, 매달 갚을 돈을 함께 확인하세요. 기존 Jun 내레이션을 사용한 홍보형 쇼츠입니다.\n#내집마련 #집값예산 #부동산 #Shorts',
      ranges=[('S02',3.52,14.4),('S03',9.72,26.12),('S25',5.12,12.96)], tail=3.0),
 dict(id='summary', name='02_summary_jun_v3', title='현금 1억이면 집값은 얼마? 8천만 원에서 시작하는 계산',
      description='현금 1억 원에서 준비금 2천만 원을 남기면 집값에 넣을 돈은 8천만 원입니다. LTV 70%를 가정하면 내 돈은 집값의 30%이므로 8천만÷30%로 계산합니다. 집값을 2억6,600만 원으로 낮춰 잡으면 대출은 1억8,600만 원, 연 4.5%·30년 원리금균등의 월 원리금은 약 94만 원입니다. 관리비·보유세·생활비는 별도로 준비합니다.\n계산 예시: 집값=담보평가액, 기존 대출 없음, 개인 심사한도 4억 원, 그 밖의 지역·정책 조건이 예시를 추가로 제한하지 않는 가정입니다. 개인별 소득·부채·지역·은행 심사에 따라 결과가 달라집니다.\n#내집마련 #LTV #주택담보대출 #Shorts',
      ranges=[('S13',0,21.92),('S14',0,12.52),('S28',0,14.0)], tail=3.0),
]

# Each split is a complete spoken phrase. Times are mapped through the frozen
# original->spoken-character map rather than estimated from text length.
SPLITS = {
 'P008Q02':['그래서 이 돈으로','무슨 집을 살 수 있는데?'],
 'P008Q03':['부동산 앱을 켜보면','6억, 10억, 15억짜리','아파트가 나오는데,'],
 'P008Q04':['내 통장에 있는 돈하고','저 가격이 바로 연결되지는 않거든요.'],
 'P010Q01':['그래서 오늘은 목표를','조금 구체적으로 잡아보겠습니다.'],
 'P010Q02':['현금이 1억, 2억, 3억,','4억, 5억 있을 때,','어느 가격대의 집부터 찾아보면','좋을지 계산해볼게요.'],
 'P010Q03':['집값에 들어가는 돈,','따로 남겨야 하는 돈,','매달 갚아야 하는 돈까지','같이 보겠습니다.'],
 'P057Q01':['그리고 은행이 빌려줄 수 있는 금액이','곧 내가 편하게 갚을 수 있는','금액은 아닙니다.'],
 'P057Q02':['월 200만 원을 낼 수 있다고 해도,','생활비와 교육비,'],
 'P057Q03':['부모님 지원, 출산이나 이직 계획까지','넣으면 체감이 달라져요.'],
 'P032Q01':['자, 현금 1억 원부터 보겠습니다.'],
 'P032Q02':['준비금 2천만 원을 빼면','집값에 넣을 돈이','8천만 원 남습니다.'],
 'P033Q01':['LTV 70퍼센트라면','내 돈이 집값의 30퍼센트는','있어야 하잖아요.'],
 'P033Q02':['그래서 8천만 원을','30퍼센트로 나누면,','계산상으로는 약','2억 6천6백만 원대가 나옵니다.'],
 'P033Q03':['오늘은 조금 내려서','2억 6천6백만 원짜리 집을','예로 들게요.'],
 'P034Q01':['내 돈 8천만 원에','대출 1억 8천6백만 원을 더하면','집값이 맞습니다.'],
 'P034Q02':['이 대출의 월 원리금은','약 94만 원입니다.'],
 'P034Q03':['물론 이 돈 말고','관리비, 보유세, 생활비도','따로 나가겠죠.'],
 'P062Q01':['이 숫자 자체보다 중요한 건','계산 순서입니다.'],
 'P062Q02':['현금에서 준비금을 빼고,','내게 실제로 가능한 대출을 확인하고,'],
 'P062Q03':['그 대출을 매달 갚을 수 있는지','보는 겁니다.'],
 'P062Q04':['그래야 부동산 앱에 있는 가격들이','내 상황하고 연결됩니다.'],
}

def setup_fonts():
    folder=HERE/'fonts'; folder.mkdir(exist_ok=True)
    source=ROOT/'video-agent-studio/episodes/capital-10eok-map-20261017/visual/map-preview-v1'
    for weight in ['Regular','SemiBold','Bold']:
        dest=folder/(weight+'.ttf')
        if not dest.exists():
            # Frozen local TTF equivalents avoid installing a WOFF2 decoder.
            shutil.copyfile(source/f'Pretendard-{"Bold" if weight=="SemiBold" else weight}.ttf',dest)
@lru_cache(None)
def font(size, weight='Bold'):
    return ImageFont.truetype(str(HERE/'fonts'/f'{weight}.ttf'),size)

def mapped_index(p, index, end=False):
    oi=si=0
    for m in p['display_mapping']:
        no,ns=len(m['original']),len(m['spoken'])
        if index<=oi+no:
            if no==ns:return si+index-oi
            q=(index-oi)*ns/max(1,no)
            return si+(math.ceil(q) if end else math.floor(q))
        oi+=no;si+=ns
    return len(p['spoken_text'])

def wrap(text, size=54, width=680):
    # A whitespace boundary never separates a numeric value from its unit.
    tokens=re.findall(r'\S+(?:\s+(?:원|퍼센트|만|억)(?=\s|[,.?!]|$))?',text)
    if font(size).getlength(text)<=width:return [text]
    candidates=[]
    for k in range(1,len(tokens)):
        a,b=' '.join(tokens[:k]),' '.join(tokens[k:])
        wa,wb=font(size).getlength(a),font(size).getlength(b)
        if max(wa,wb)<=width:candidates.append((abs(wa-wb),[a,b]))
    assert candidates,('Split spoken phrase into smaller complete units',text)
    return min(candidates,key=lambda x:x[0])[1]

def make_plan():
    a=load(N/'scene_alignment.json'); assert a['timing_locked']
    scenes={s['scene_id']:s for s in a['scenes']}
    manifest=load(ROOT/a['manifest']['path'])
    paragraphs={p['paragraph_id']:p for p in manifest['paragraphs']}
    cp=load(N/'caption_plan.json'); cueplan={c['cue_id']:c for c in cp['cues']}
    units={x['audio_unit_id']:x for x in a['audio_units']}
    result=[]
    for spec in SPECS:
        p={k:v for k,v in spec.items() if k!='ranges'};p['ranges']=[];p['captions']=[];pos=0
        for sid, lo, hi in spec['ranges']:
            s=scenes[sid];uid=s['audio_unit_id'];u=units[uid]
            count=math.ceil((hi-lo)*FPS-1e-8); duration=count/FPS
            p['ranges'].append(dict(scene_id=sid,audio_unit_id=uid,path=str(ROOT/u['path']),sha256=u['sha256'],
                                    scene_in_s=lo,scene_out_s=hi,source_in_s=s['audio_start_s']+lo,
                                    source_out_s=s['audio_start_s']+hi,output_start_s=pos,output_duration_s=duration))
            for c in s['captions']:
                if c['start_s']<lo-1e-6 or c['end_s']>hi+1e-6:continue
                pieces=SPLITS[c['cue_id']];assert ' '.join(pieces)==c['text'],c['cue_id']
                para=paragraphs[c['paragraph_id']];chars=next(x for x in s['characters'] if x['paragraph_id']==c['paragraph_id'])
                begin=cueplan[c['cue_id']]['source_start'];seek=begin
                for n,piece in enumerate(pieces):
                    at=para['text'].index(piece,seek);seek=at+len(piece)
                    first=mapped_index(para,at);last=mapped_index(para,seek,True)-1
                    start=chars['start_s'][first];end=chars['end_s'][last]
                    start=max(c['start_s'],start);end=min(c['end_s'],end)
                    assert start<end,(piece,start,end)
                    p['captions'].append(dict(id=f'{c["cue_id"]}.{n+1}',source_cue_id=c['cue_id'],scene_id=sid,text=piece,
                          lines=wrap(piece),start_s=round(pos+start-lo,6),end_s=round(pos+end-lo,6),
                          source_character_range=[at,seek],timing_basis='original_to_spoken_map_and_provider_character_alignment'))
            pos+=duration
        p['speech_cut_end_s']=pos;p['frames']=math.ceil((pos+spec['tail'])*FPS-1e-8);p['duration_s']=p['frames']/FPS
        assert 35<=p['duration_s']<=60
        for x,y in zip(p['captions'],p['captions'][1:]): assert x['end_s']<=y['start_s']+1e-6
        result.append(p)
    save(HERE/'edit_plan.json',dict(revision='portrait-shorts-v3-final',audio_revision='jun-user-script-v1',fps=FPS,width=W,height=H,
         renderer='Pillow native scene layers + local FFmpeg',safe_profile='youtube_portrait_full_frame_v2',shorts=result))
    return result

BOUNDS={}; TEXT_CACHE={}
def label(im, text, x, y, size=56, color=INK, weight='Bold', kind='key_value', key='', centered=False):
    f=font(size,weight); d=ImageDraw.Draw(im)
    if centered:x-=d.textlength(text,font=f)/2
    box=d.textbbox((x,y),text,font=f,anchor='lt')
    if key:BOUNDS[key]=dict(id=key,kind=kind,text=text,font_px=size,bbox=[round(z,3) for z in box])
    d.text((x,y),text,font=f,fill=color,anchor='lt')
def rr(im,box,fill,r=22,outline=None,width=2):
    ImageDraw.Draw(im).rounded_rectangle(box,radius=r,fill=fill,outline=outline,width=width)
def line(im,xy,fill,width=4):ImageDraw.Draw(im).line(xy,fill=fill,width=width)
def ease(v):v=max(0,min(1,v));return 1-(1-v)**3

def cue_at(p,id):return next(x['start_s'] for x in p['captions'] if x['id']==id)
def reveal(im,box,at,t,fill='#ffffff'):
    """Reveal an individual semantic layer; fixed captions and credits never move."""
    progress=ease((t-at)/.42)
    if progress>=1:return
    box=tuple(int(v) for v in box);crop=im.crop(box).convert('RGBA')
    rr(im,box,fill,0)
    if progress<=0:return
    crop.putalpha(int(progress*255));im.paste(crop,(box[0],box[1]+round(10*(1-progress))),crop)

def house(im,x,y,w=300,color=BLUE):
    d=ImageDraw.Draw(im);h=w*.77
    d.polygon([(x,y+w*.36),(x+w*.5,y),(x+w,y+w*.36)],fill=color)
    rr(im,[x+w*.12,y+w*.34,x+w*.88,y+h], '#e1e9ef',12)
    rr(im,[x+w*.41,y+w*.52,x+w*.59,y+h], INK,6)
    for xx in [.23,.64]:rr(im,[x+w*xx,y+w*.44,x+w*(xx+.13),y+w*.56],'#ffffff',4)

@lru_cache(None)
def backdrop(dark=False):
    im=Image.new('RGB',(W,H),INK if dark else CREAM);d=ImageDraw.Draw(im)
    d.ellipse([550,-180,1600,860],fill='#213f55' if dark else '#e7ede9')
    d.ellipse([-600,1290,750,2520],fill='#20455c' if dark else '#e7ece6')
    # Full canvas residential silhouettes are decorative; evidence stays in safe rect.
    for x,y,w,h in [(-40,1380,215,540),(195,1490,180,430),(740,1420,170,500),(930,1320,220,600)]:
        rr(im,[x,y,x+w,y+h],'#24465b' if dark else '#d8e0dd',18)
        for yy in range(y+35,1900,54):
            for xx in range(x+25,x+w-20,48):rr(im,[xx,yy,xx+18,yy+25],'#31576c' if dark else '#f1f3ef',3)
    return im

def common(p,title,subtitle='',dark=False,condition=None):
    im=backdrop(dark).copy(); col='#ffffff' if dark else INK
    for j,t in enumerate(title):label(im,t,148,276+j*76,64,col,kind='title',key=p['id']+':title:'+t)
    if subtitle:label(im,subtitle,148,448,28,'#b4cbd7' if dark else MUTED,'Regular','condition_source',p['id']+':sub:'+subtitle)
    rr(im,[118,1090,872,1254],'#ffffff',24)
    if condition:
        for j,t in enumerate(condition):label(im,t,148,1273+j*31,26,'#c6d5de' if dark else MUTED,'Regular','condition_source',p['id']+':condition:'+t)
    return im

def steps(im, rows, t=10, active=2):
    for j,(heading,detail) in enumerate(rows):
        yy=554+j*160;rr(im,[142,yy,840,yy+138],'#ffffff',20)
        rr(im,[162,yy+22,225,yy+85],BLUE if j<=active else PALE,18)
        label(im,str(j+1),194,yy+35,38,'#ffffff',centered=True)
        label(im,heading,250,yy+25,52,INK,key='step:'+heading)
        label(im,detail,250,yy+88,28,MUTED,'Regular','condition_source',key='stepdetail:'+detail)

def visual(p,t):
    if p['id']=='promo':
        a,b,c=p['ranges'];cut1=b['output_start_s'];cut2=c['output_start_s'];tail=p['speech_cut_end_s']
        if t<cut1:
            im=common(p,['모은 돈으로','어떤 집을 살까?'],'현금과 집값을 연결하는 첫 계산')
            rr(im,[142,540,840,1018],'#ffffff',28)
            house(im,325,536,290)
            label(im,'내 통장',170,861,32,MUTED,kind='condition_source',key='promo:bank')
            label(im,'살 수 있는 집?',170,914,66,BLUE,key='promo:question')
            # App prices appear only while spoken, with separate positions.
            for j,price in enumerate(['6억','10억','15억']):
                x=170+j*216;rr(im,[x,770,x+186,837],PALE,16)
                label(im,price,x+93,782,52,INK,centered=True,key='promo:app:'+price)
                reveal(im,[x,769,x+187,839],cue_at(p,'P008Q03.2')+j*.40,t)
        elif t<cut2:
            lt=t-cut1
            im=common(p,['현금 1억~5억','집 예산의 출발점'],'본편에서 내 조건에 맞춰 계산합니다')
            if lt<10.7:
                house(im,326,553,280)
                for j,n in enumerate(['1억','2억','3억','4억','5억']):
                    on=t>=cue_at(p,'P010Q02.1')+j*.55
                    x=148+j*138;rr(im,[x,834,x+123,927],BLUE if on else '#e1e7e8',18)
                    label(im,n,x+61,854,52,'#ffffff' if on else INK,centered=True,key='promo:cash:'+n)
                label(im,'어느 가격대부터 볼까요?',148,965,52,INK,key='promo:range')
            else:
                steps(im,[('집값에 넣을 돈','잔금일에 쓸 자기자금'),('따로 남겨둘 돈','비용 · 비상금'),('매달 갚을 돈','생활 · 저축과 함께 확인')])
                for j,anchor in enumerate(['P010Q03.1','P010Q03.2','P010Q03.3']):
                    reveal(im,[146,556+j*160,838,691+j*160],cue_at(p,anchor),t)
        elif t<tail:
            lt=t-cut2
            im=common(p,['대출 한도 다음은','내 생활의 예산'],'내 집을 오래 유지할 수 있는가')
            rr(im,[142,541,840,1016],'#ffffff',28)
            label(im,'월 상환',176,574,34,MUTED,kind='condition_source',key='promo:monthly_label')
            label(im,'200만 원',176,632,84,BLUE,key='promo:200')
            line(im,[(176,755),(806,755)],'#dce3e3',3)
            for j,txt in enumerate(['생활비 · 교육비','부모님 지원','출산 · 이직 계획']):
                yy=790+j*69
                rr(im,[176,yy+7,192,yy+23],GREEN,6)
                label(im,txt,218,yy,52,INK,key='promo:life:'+txt)
                reveal(im,[170,yy-1,825,yy+58],cut2+[1.6,3.6,4.65][j],t)
        else:
            im=common(p,['집을 보기 전에','내 예산부터'],'현금 1억부터 5억까지 · 본편에서 확인',True)
            house(im,295,554,350,'#67a7ee')
            label(im,'집값 · 준비금 · 월 상환',148,913,52,'#ffffff',key='promo:CTA')
            label(im,'본편에서 예산 계산하기',490,1141,54,BLUE,kind='caption',key='promo:CTArail',centered=True)
        cond=['본편: 현금 1억~5억 내 집 예산','소득 · 기존 대출 · 지역 조건을 함께 확인']
        for j,x in enumerate(cond):label(im,x,148,1274+j*33,26,MUTED if t<tail else '#c6d5de','Regular','condition_source',key='promo:credit:'+x)
    else:
        cond=['계산 예시 · 집값=담보평가액 · LTV 70%', '기존 대출 0 · 개인 심사한도 4억 원 가정','지역 · 정책 조건은 예시를 추가 제한하지 않는 가정']
        if t<6.88:
            im=common(p,['현금 1억으로','집값을 계산하면?'],'먼저, 남겨둘 돈부터 빼세요',condition=cond)
            rr(im,[142,543,840,1030],'#ffffff',28)
            for j,(a,b,col) in enumerate([('보유 현금','1억 원',INK),('준비금','− 2천만 원',GOLD),('집값에 쓸 돈','8천만 원',BLUE)]):
                yy=575+j*151;label(im,a,172,yy,30,MUTED,kind='condition_source',key='sum:'+a)
                label(im,b,172,yy+49,68,col,key='sum:'+b)
                if j>0:reveal(im,[165,yy-2,828,yy+126],[0,2.6,5.15][j],t)
            if t>2.6:rr(im,[173,1007,173+int(632*ease((t-2.6)/.7)),1015],BLUE,4)
        elif t<11.48:
            im=common(p,['LTV 70%라면','내 돈은 30%'],'집값 중 내가 마련할 몫을 확인합니다',condition=cond)
            house(im,330,530,280)
            x,y,ww=148,810,680
            rr(im,[x,y,x+ww,y+86],GOLD,14)
            rr(im,[x,y,x+ww*.3,y+86],BLUE,14)
            label(im,'내 돈 30%',148,927,52,BLUE,key='summary:30')
            label(im,'대출 70%',535,927,52,GOLD,key='summary:70')
            reveal(im,[144,924,826,996],8.8,t,CREAM)
        elif t<21.92:
            im=common(p,['8천만 원 ÷ 30%','집값의 기준이 됩니다'],'자기자금 ÷ 내가 마련할 비율',condition=cond)
            rr(im,[142,549,840,1030],'#ffffff',28)
            label(im,'8천만 ÷ 0.3',173,598,72,BLUE,key='summary:formula')
            label(im,'약 2억6,667만 원',173,738,60,MUTED,key='summary:raw')
            line(im,[(174,842),(805,842)],PALE,3)
            label(im,'예시 집값',173,876,30,MUTED,kind='condition_source',key='summary:exlabel')
            label(im,'2억6,600만 원',173,928,68,INK,key='summary:price')
            reveal(im,[166,734,825,821],15.12,t)
            reveal(im,[166,869,825,1012],17.84,t)
        elif t<26.88:
            im=common(p,['내 돈 + 대출','집값 2억6,600만'],'집값을 조금 낮춰 잡은 계산 예시',condition=cond)
            house(im,332,535,270)
            rr(im,[148,790,828,864],GOLD,12);rr(im,[148,790,148+680*.8/2.66,864],BLUE,12)
            label(im,'내 돈 8천만',148,916,52,BLUE,key='summary:equity')
            label(im,'대출 1억8,600만',148,987,52,GOLD,key='summary:loan')
            reveal(im,[145,985,830,1052],23.35,t,CREAM)
        elif t<34.45334:
            cc=['계산 예시 · 대출 1억8,600만 원','연 4.5% · 30년 · 원리금균등','관리비 · 보유세 · 생활비는 별도']
            im=common(p,['매달 갚을 돈','약 94만 원'],'대출 원금과 이자를 함께 갚는 금액',condition=cc)
            rr(im,[142,549,840,1030],'#ffffff',28)
            label(im,'월 원리금',174,591,34,MUTED,kind='condition_source',key='summary:month')
            label(im,'94만 원',174,680,114,BLUE,key='summary:94')
            line(im,[(174,842),(805,842)],PALE,3)
            label(im,'관리비 · 보유세',174,894,52,INK,key='summary:expenses1')
            label(im,'생활비도 남겨두세요',174,966,52,INK,key='summary:expenses2')
            reveal(im,[166,885,825,1030],30.08,t)
        else:
            im=common(p,['집값보다 먼저','이 순서를 기억하세요'],'내 소득과 생활에 맞춰 정하는 내 집 예산',condition=['원문: 사용자 대본 · Jun 기존 음성','숫자는 위 조건에 따른 계산 예시'])
            lt=t-34.45334
            steps(im,[('현금 − 준비금','실제로 집값에 넣을 돈'),('가능한 대출','소득 · 부채 · 담보 조건 확인'),('월 상환 점검','매달 생활과 저축을 유지할 금액')],active=min(2,int(lt/4)))
            for j,anchor in enumerate(['P062Q02.1','P062Q02.2','P062Q03.1']):
                reveal(im,[146,556+j*160,838,691+j*160],cue_at(p,anchor),t)
            if t>=p['speech_cut_end_s']:
                label(im,'내 예산을 먼저 적어보세요',490,1141,54,BLUE,kind='caption',key='summary:CTArail',centered=True)
    return im

def caption_layer(p,c):
    key=(p['id'],c['id'])
    if key in TEXT_CACHE:return TEXT_CACHE[key]
    im=Image.new('RGBA',(W,166),(0,0,0,0))
    n=len(c['lines']);y=(164-n*66)/2
    for j,l in enumerate(c['lines']):
        label(im,l,490,y+j*66,54,INK,kind='caption',centered=True)
        box=ImageDraw.Draw(im).textbbox((490-font(54).getlength(l)/2,y+j*66),l,font=font(54),anchor='lt')
        BOUNDS[p['id']+':caption:'+c['id']+':'+str(j)]=dict(kind='caption',text=l,font_px=54,bbox=[box[0],box[1]+1090,box[2],box[3]+1090],start_s=c['start_s'],end_s=c['end_s'])
    TEXT_CACHE[key]=im
    return im

def audio(p):
    rate=44100; arr=np.zeros(round(p['duration_s']*rate),dtype='<i2');receipts=[]
    for r in p['ranges']:
        src=Path(r['path']);assert sha(src)==r['sha256']
        with wave.open(str(src),'rb') as w:
            assert (w.getnchannels(),w.getsampwidth(),w.getframerate())==(1,2,rate)
            first=round(r['source_in_s']*rate);n=round(r['source_out_s']*rate)-first;w.setpos(first)
            original=w.readframes(n);x=np.frombuffer(original,dtype='<i2').copy()
        # 3ms boundary ramps affect only join edges; no rate/pitch/timbre change.
        fade=min(round(.003*rate),len(x)//2)
        x[:fade]=(x[:fade]*np.linspace(0,1,fade)).astype('<i2');x[-fade:]=(x[-fade:]*np.linspace(1,0,fade)).astype('<i2')
        at=round(r['output_start_s']*rate);arr[at:at+len(x)]=x
        receipts.append(dict(scene_id=r['scene_id'],source_pcm_sha256=hashlib.sha256(original).hexdigest(),sample_count=len(x),boundary_ramp_ms=3))
    dest=HERE/(p['name']+'_audio.wav')
    with wave.open(str(dest),'wb') as w:w.setparams((1,2,rate,0,'NONE','not compressed'));w.writeframes(arr.tobytes())
    save(HERE/(p['id']+'_audio_receipt.json'),dict(source_pcm_preserved_except_3ms_edge_ramps=True,speed=1,pitch_shift=0,no_new_TTS=True,sources=receipts,
        peak_dbfs=float(20*np.log10(max(1,abs(arr.astype(float)).max())/32768)),rms_dbfs=float(20*np.log10(max(1,np.sqrt(np.mean(arr.astype(float)**2)))/32768)),actual_listening=False))
    return dest

def timestamp(t):
    ms=round(t*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'
def subtitles(p):
    write(OUT/(p['name']+'.srt'),'\n\n'.join(f'{i+1}\n{timestamp(c["start_s"])} --> {timestamp(c["end_s"])}\n'+ '\n'.join(c['lines']) for i,c in enumerate(p['captions']))+'\n')
    save(OUT/(p['name']+'_captions.json'),p['captions'])

def render(p):
    dest=OUT/(p['name']+'.mp4');assert not dest.exists(),f'Preserve existing version: {dest}'
    wav=audio(p);subtitles(p)
    argv=[str(FF),'-hide_banner','-loglevel','warning','-n','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{W}x{H}','-framerate',str(FPS),'-i','pipe:0',
          '-i',str(wav),'-map','0:v:0','-map','1:a:0','-vf','setsar=1','-c:v','libx264','-preset','fast','-crf','18','-threads','4','-pix_fmt','yuv420p','-r','30','-c:a','aac','-b:a','192k','-ar','48000',
          '-af','alimiter=level_in=1:level_out=1:limit=0.944:level=false','-movflags','+faststart','-t',str(p['duration_s']),'-metadata:s:v','rotate=0',str(dest)]
    save(HERE/(p['id']+'_render_command.json'),dict(argv=argv,rawvideo_producer=str(Path(__file__).resolve()),sha256=sha(Path(__file__).resolve())))
    with (HERE/(p['id']+'_render.log')).open('wb') as log:
        proc=subprocess.Popen(argv,stdin=subprocess.PIPE,stderr=log)
        try:
            for i in range(p['frames']):
                t=i/FPS;im=visual(p,t)
                c=next((c for c in p['captions'] if c['start_s']<=t<c['end_s']),None)
                if c:im.paste(caption_layer(p,c),(0,1090),caption_layer(p,c))
                # Continuous progress is ornamental and cannot obscure essential content.
                rr(im,[0,1887,int(W*(i+1)/p['frames']),1895],BLUE,3)
                proc.stdin.write(im.tobytes())
            proc.stdin.close();rc=proc.wait()
        except BaseException:
            proc.kill();proc.wait();raise
    assert rc==0,(p['id'],rc)
    print(json.dumps(dict(status='rendered',id=p['id'],path=str(dest),duration=p['duration_s'])),flush=True)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--prepare-only',action='store_true');parser.add_argument('--stills-only',action='store_true');args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True);setup_fonts();plans=make_plan()
    for p in plans:
        # Populate every measured text and check composition before any expensive encode.
        times=([0,3.2,7,11,15,23,29,35,40.5] if p['id']=='promo' else [0,4,9,14,20,24,28,33,37,43,48])
        for t in times:
            im=visual(p,t)
            c=next((c for c in p['captions'] if c['start_s']<=t<c['end_s']),None)
            if c:im.paste(caption_layer(p,c),(0,1090),caption_layer(p,c))
            if args.stills_only or args.prepare_only:im.save(HERE/f'{p["id"]}_sketch_{t:05.1f}.jpg')
        for c in p['captions']:caption_layer(p,c)
        subtitles(p)
    cfg=load(ROOT/'config/vertical_video_safe_area.json');r=cfg['profiles']['youtube_portrait_full_frame_v2']['critical_rect'];rect=[r[x] for x in ['left','top','right','bottom']]
    save(HERE/'layout_bounds.json',dict(safe_rect=rect,profile='youtube_portrait_full_frame_v2',elements=list(BOUNDS.values())))
    errors=[x for x in BOUNDS.values() if x['bbox'][0]<rect[0] or x['bbox'][1]<rect[1] or x['bbox'][2]>rect[2] or x['bbox'][3]>rect[3]]
    assert not errors,errors
    save(OUT/'publishing_metadata.json',dict(visibility='private',upload_owner='parent director',uploaded=False,shorts=[dict(id=p['id'],video=p['name']+'.mp4',srt=p['name']+'.srt',title=p['title'],description=p['description'],duration_s=p['duration_s']) for p in plans]))
    print(json.dumps(dict(status='prepared',shorts=[dict(id=p['id'],duration_s=p['duration_s'],captions=len(p['captions'])) for p in plans],bounds=len(BOUNDS))),flush=True)
    if not args.prepare_only and not args.stills_only:
        for p in plans:render(p)
        save(HERE/'layout_bounds.json',dict(safe_rect=rect,profile='youtube_portrait_full_frame_v2',elements=list(BOUNDS.values())))

if __name__=='__main__':main()
