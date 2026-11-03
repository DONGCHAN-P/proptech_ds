"""Additive local-only representative build. Does not synthesize or assemble a film."""
import argparse, hashlib, html, json, shutil
from pathlib import Path

HERE=Path(__file__).resolve().parent
EP=HERE.parents[1]
ROOT=EP.parents[2]
OUT=EP/'outputs/jun-user-script-v1/representatives'
PROJECT=HERE/'project'
PLAN=EP/'director/user-recording-v1/scene_plan.json'
CALC=EP/'director/user-recording-v1/calculation_check.json'
MANIFEST=EP/'narration/jun-user-script-v1/narration_manifest.json'
CAPTIONS=EP/'narration/jun-user-script-v1/caption_plan.json'
BASE=ROOT/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/jun-production-v1/ch03'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,s):
    p=p.resolve()
    assert any(p.is_relative_to(r.resolve()) for r in [HERE,OUT]),str(p)
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf8')
def dump(p,v):write(p,json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def text(id,s,x,y,w,size=32,color='var(--ink)',weight=400,cls=''):
    return f'<div id="{id}" data-text="true" class="txt {cls}" style="left:{x}px;top:{y}px;width:{w}px;font-size:{size}px;color:{color};font-weight:{weight}">{html.escape(s)}</div>'
def shape(id,x,y,w,h,color,cls='',value=None,scale=None):
    attrs='' if value is None else f' data-money-won="{value}" data-px-per-won="{scale}"'
    return f'<div id="{id}" class="shape {cls}"{attrs} style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;background:{color}"></div>'
def group(id,body,cls='reveal'):return f'<div id="{id}" class="group {cls}">{body}</div>'

CSS='''@font-face{font-family:Pretendard;font-weight:400;src:url(assets/fonts/Pretendard-Regular.woff2)}
@font-face{font-family:Pretendard;font-weight:600;src:url(assets/fonts/Pretendard-SemiBold.woff2)}
@font-face{font-family:Pretendard;font-weight:700;src:url(assets/fonts/Pretendard-Bold.woff2)}
:root{--canvas:#f6f4ef;--ink:#173348;--muted:#546973;--blue:#286cda;--gold:#c29a44;--green:#3f8f7f;--gray:#c8cdcc}
*{box-sizing:border-box;margin:0;padding:0}html,body{position:fixed;inset:0;width:100%;height:100%;overflow:hidden;background:var(--canvas)}
#root{width:100%;height:100%;position:fixed;inset:0;overflow:hidden;color:var(--ink);font-family:Pretendard,sans-serif;background:var(--canvas)}
.txt{position:absolute;line-height:1.32;white-space:nowrap;letter-spacing:-.015em;font-variant-numeric:tabular-nums}
.group{position:absolute;inset:0}.shape{position:absolute;transform-origin:left center;border-radius:3px}
.reveal{opacity:0}.fill{transform-origin:left center}.brand{font-size:22px!important}.cap{position:absolute;inset:0;opacity:0}
#capbox{position:absolute;left:96px;top:876px;width:1728px;height:124px;border-radius:16px;background:#fff}
.caption{position:absolute;left:140px;top:876px;width:1640px;height:124px;display:flex;align-items:center;justify-content:center;text-align:center;white-space:pre;font-size:40px;line-height:50px;letter-spacing:0}
.caption span{display:block;white-space:pre}.source{font-size:20px!important}.hair{border-top:2px solid #cbd0cd;position:absolute}
'''

def s13():
    b=text('cash-k','보유현금',110,280,500,30,'var(--muted)')+text('cash-v','1억원',110,325,500,82,weight=700)
    b+=shape('cash-track',110,470,250,50,'#e0e4df')
    b+=group('cash-equity',shape('equity',110,470,200,50,'var(--blue)','fill',80000000,2.5e-6))
    b+=group('reserve',shape('reserve-bar',310,470,50,50,'var(--gray)',value=20000000,scale=2.5e-6)+text('reserve-k','별도 준비금',110,560,400,30,'var(--muted)')+text('reserve-v','2000만원',110,602,400,42,weight=600))
    b+=group('eq-value',text('eq-k','집값에 넣을 자기자금',420,325,440,30,'var(--muted)')+text('eq-v','8000만원',420,373,440,62,'var(--blue)',700))
    b+=group('formula',text('formula-label','8000만원 ÷ 30%',420,550,450,38,weight=600)+text('formula-ceiling','계산상 약 2억6667만원',420,607,480,29,'var(--muted)'))
    b+=shape('divider',935,280,2,480,'#d5d8d1')
    b+=text('house-topic','자기자금 + 대출 → 주택가격',1010,280,800,30,'var(--muted)')
    b+=group('house-result',text('house-k','이번 예시의 집값',1010,344,750,30,'var(--muted)')+text('house-v','2억6600만원',1010,395,780,72,weight=700)+shape('house-eq',1010,520,200,64,'var(--blue)','fill',80000000,2.5e-6)+shape('house-loan',1210,520,465,64,'var(--gold)','fill',186000000,2.5e-6)+text('house-eq-k','자기자금',1010,610,220,30,'var(--blue)',600)+text('house-eq-v','8000만원',1010,651,235,36,weight=600)+text('house-loan-k','대출',1325,610,300,30,'var(--muted)',600)+text('house-loan-v','1억8600만원',1325,651,430,36,weight=600))
    return dict(id='S13',duration=10,title='4. 현금 1억원을 집값으로 바꾸면',condition='사례 가정  LTV 70% · 개인 대출한도 4억원 · 준비금 2000만원',body=b,
      events=[{'at':.15,'show':['cash-equity'],'fills':['equity']},{'at':1.1,'show':['reserve'],'move':[{'id':'reserve-bar','y':70}]},{'at':2.4,'show':['eq-value']},{'at':4.0,'show':['formula']},{'at':6.2,'show':['house-result'],'fills':['house-eq','house-loan']}],
      cues=[(0,'자, 현금 1억원부터 보겠습니다.'),(1.1,'준비금 2000만원을 빼면\n집값에 넣을 돈이 8000만원 남습니다.'),(4.0,'내 돈이 집값의 30%는 있어야 하잖아요.'),(6.2,'오늘은 조금 내려서\n2억6600만원짜리 집을 예로 들게요.')],
      anchor_events={'S13.b01':1.1,'S13.b02':2.4,'S13.b03':4.0,'S13.b04':6.2},source='계산: 사용자 원고의 가상 사례 · 현금과 주택가격은 준비금을 분리해 표시',samples=[0,1.6,2.9,4.6,6.7,9.5])

def capscene():
    b=text('eq-head','집값 투입 자기자금',315,260,500,30,'var(--blue)',600)+text('loan-head','사용 대출',905,260,420,30,'var(--muted)',600)+text('total-head','주택가격',1480,260,330,30,'var(--muted)',600)
    b+=group('limit',shape('cap-rule',1384,310,4,414,'var(--gold)')+text('cap-label','개인 한도 4억원',1035,305,330,31,'var(--ink)',700))
    vals=[(3,2.6,6.6),(4,3.5,7.5),(5,4.4,8.4)]
    for i,(cash,eq,total) in enumerate(vals):
        y=380+i*145
        content=text(f'cash-{i}',f'현금 {cash}억',100,y-44,200,32,weight=600)+text(f'eq-label-{i}',f'{eq:g}억원',315,y-48,350,36,'var(--blue)',700)+shape(f'eq-{i}',315,y,eq*120,44,'var(--blue)','fill',round(eq*1e8),1.2e-6)+shape(f'loan-track-{i}',905,y,480,44,'#e6e1d5')
        if i==0:b+=content
        else:b+=group(f'row-{i}',content)
        b+=group(f'loan-row-{i}',shape(f'loan-{i}',905,y,480,44,'var(--gold)','fill',400000000,1.2e-6)+text(f'loan-label-{i}','4억원',1060,y+51,300,31,weight=600))
        b+=group(f'price-{i}',text(f'price-label-{i}',f'{total:g}억원',1480,y-17,350,54,weight=700))
    b+=group('monthly',shape('month-line',915,794,400,2,'var(--green)')+''.join(shape(f'dot-{i}',925+i*185,787,16,16,'var(--green)') for i in range(3))+text('monthly-value','세 사례 모두 월 원리금 약 203만원',100,763,780,35,'var(--green)',700))
    return dict(id='S18_S19',scene_ids=['S18','S19'],duration=13,title='5. 현금이 늘어도, 대출은 4억원에서 멈춥니다',condition='사례 가정  LTV 70% · 개인 대출한도 4억원 · 연 4.5% · 30년 원리금균등',body=b,
      events=[{'at':.15,'fills':['eq-0']},{'at':1.8,'show':['limit']},{'at':2.8,'show':['loan-row-0'],'fills':['loan-0'],'duration':1.1},{'at':4.1,'show':['price-0']},{'at':6.0,'show':['row-1','loan-row-1','price-1'],'fills':['eq-1','loan-1']},{'at':8.0,'show':['row-2','loan-row-2','price-2'],'fills':['eq-2','loan-2']},{'at':10,'show':['monthly']}],
      cues=[(0,'집값에 넣을 돈은 2억6000만원입니다.'),(1.8,'오늘 이 사람은 대출한도가 4억원이죠.'),(4.1,'2억6000만원에 4억원을 더한\n6억6000만원이 예시 집값이 됩니다.'),(6,'현금 4억원이면 집값 7억5000만원,'),(8,'현금 5억원이면 집값 8억4000만원이고요.'),(10,'세 경우 모두 대출을 4억원으로 잡았으니까\n월 원리금은 약 203만원으로 같습니다.')],
      anchor_events={'S18.b01':.15,'S18.b02':1.8,'S18.b03':4.1,'S18.b04':4.8,'S19.b01':6,'S19.b02':8,'S19.b03':10},source='계산: 사용자 원고의 가상 사례 · 대출한도는 개인별 사례 조건 · 모든 금액 막대 동일 축척',samples=[0,2.2,3.3,4.7,6.7,8.7,10.7,12.5])

def receipt():
    b=shape('paper',100,290,900,530,'#ffffff')+text('receipt-head','6억6000만원 주택의 비용',135,310,830,34,weight=700)
    rows=[('tax','취득세','924만원',380),('edu','지방교육세','92만4000원',439),('taxsum','세금 소계','1016만4000원',510),('broker','중개보수·부가세','290만4000원',582),('sum','세금·중개보수 합계','1306만8000원',720)]
    for id,k,v,y in rows:
        b+=group(id,text(id+'-k',k,135,y,500,32,weight=600 if id in ['sum','taxsum'] else 400)+text(id+'-v',v,650,y,350,36,weight=700))
    b+=group('broker-basis',text('broker-note','상한요율 0.4% · 부가세 10% 가정',135,640,810,28,'var(--muted)'))
    b+=text('reserve-title','먼저 떼어둔 준비금',1070,300,750,30,'var(--muted)')+text('reserve-total','4000만원',1070,343,750,68,weight=700)
    b+=group('remaining',text('remaining-k','다른 항목에 배분할 잔여',1070,458,750,30,'var(--green)',600)+text('remaining-v','2693만2000원',1070,502,750,60,'var(--green)',700))
    b+=shape('reserve-track',1070,617,720,50,'#e2e6df')
    b+=group('cost-bar-group',shape('cost-bar',1070,617,235.224,50,'var(--gold)','fill',13068000,1.8e-5))
    b+=group('remaining-bar-group',shape('remaining-bar',1305.224,617,484.776,50,'var(--green)','fill',26932000,1.8e-5)+text('allocate-1','등기 · 이사 · 수리',1070,703,750,33,weight=600)+text('allocate-2','가전 · 가구 · 비상금',1070,751,750,33,weight=600))
    return dict(id='S21',duration=12,title='5. 준비금 4000만원, 어디에 얼마나 쓸까',condition='6억6000만원 · 일반적인 1주택 취득 · 전용 85㎡ 이하 · 감면 없음 · 일반과세 중개사',body=b,
      events=[{'at':1,'show':['tax','edu','taxsum']},{'at':3.5,'show':['broker','broker-basis']},{'at':5.5,'show':['sum','cost-bar-group'],'fills':['cost-bar']},{'at':7.5,'show':['remaining','remaining-bar-group'],'fills':['remaining-bar']}],
      cues=[(0,'아까 빼놓은 준비금도 한번 확인해볼게요.'),(1,'취득세와 지방교육세가 합쳐서\n약 1016만원입니다.'),(3.5,'일반과세 중개사의 부가세까지 가정하면\n중개보수는 약 290만원이고요.'),(5.5,'두 항목만 약 1307만원입니다.'),(7.5,'남은 약 2693만원 안에서\n등기 관련 비용, 이사, 가전과 가구, 비상금 등을 배분하는 거예요.')],
      anchor_events={'S21.b01':1,'S21.b02':3.5,'S21.b03':5.5,'S21.b04':7.5},source='자료: 지방세법 제11·151조 · 서울시 중개보수 요율표 | 원고의 6.6억 사례 조건',samples=[0,1.7,4.2,6.2,8.2,11.5])

RUNTIME='''document.fonts.ready.then(()=>{
const tl=gsap.timeline({paused:true});
const el=id=>{const n=document.getElementById(id);if(!n)throw Error('Missing '+id);return n;};
tl.set('.fill',{scaleX:0},0);
for(const e of MODEL.events){const d=e.duration||.45;
 for(const id of e.show||[])tl.fromTo(el(id),{opacity:0,y:8},{opacity:1,y:0,duration:.18,ease:'power2.out',immediateRender:false},e.at);
 for(const id of e.fills||[])tl.fromTo(el(id),{scaleX:0},{scaleX:1,duration:d,ease:'power2.out',immediateRender:false},e.at);
 for(const m of e.move||[])tl.fromTo(el(m.id),{y:0},{y:m.y,duration:.45,ease:'power2.out',immediateRender:false},e.at);
}
MODEL.cues.forEach((c,i)=>{const n=el('caption-'+i),end=MODEL.cues[i+1]?.[0]||MODEL.duration;
tl.fromTo(n,{opacity:0},{opacity:1,duration:.001,immediateRender:false},c[0]);
tl.to(n,{opacity:0,duration:.001},end-.001);});
window.__timelines=window.__timelines||{};window.__timelines[MODEL.id]=tl;
window.__sourceSeek=t=>tl.pause().totalTime(t,false);window.__sourceSeek(0);window.__ready=true;
});'''

def emit(m,folder):
    assets=folder/'assets';assets.mkdir(parents=True,exist_ok=True)
    for name in ['gsap.min.js','fonts/Pretendard-Regular.woff2','fonts/Pretendard-SemiBold.woff2','fonts/Pretendard-Bold.woff2']:
        target=assets/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(BASE/'assets'/name,target)
    shell=text('brand','부동산 데이터 | 내 집 예산',88,28,1000,22,cls='brand')+text('preview','무음 시안 · 타이밍 미확정',1410,30,430,22,'var(--muted)')+text('message',m['title'],80,142,1760,43,weight=700)+text('condition',m['condition'],96,218,1728,28,'var(--muted)')
    captions='<div id="capbox"></div>'+''.join(f'<div id="caption-{i}" class="cap"><div data-text="true" class="caption"><span>{html.escape(c)}</span></div></div>' for i,(t,c) in enumerate(m['cues']))
    shell+=m['body']+captions+text('source',m['source'],96,1020,1728,20,'var(--muted)',cls='source')
    data={k:v for k,v in m.items() if k!='body'}
    write(folder/'index.html',f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{html.escape(m["title"])}</title><script src="assets/gsap.min.js"></script><style>{CSS}</style></head><body><div id="root" data-composition-id="{m["id"]}" data-start="0" data-duration="{m["duration"]}" data-width="1920" data-height="1080">{shell}</div><script>const MODEL={json.dumps(data,ensure_ascii=False)};{RUNTIME}</script></body></html>')
    dump(folder/'preview_model.json',dict(data,timing_basis='preview_only_unlocked',audio=None))
    dump(folder/'hyperframes.json',{'name':'jun-user-script-'+m['id'].lower(),'width':1920,'height':1080,'fps':30,'entry':'index.html'})

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--scene',action='append');args=parser.parse_args()
    plan=read(PLAN);models=[s13(),capscene(),receipt()]
    caption_plan=read(CAPTIONS);by_cue={c['cue_id']:c for c in caption_plan['cues']}
    selections={
      'S13':[(0,'P032Q01'),(1.1,'P032Q02'),(3.1,'P033Q01'),(4,'P033Q02'),(6.2,'P033Q03')],
      'S18_S19':[(0,'P042Q02'),(1.8,'P043Q01'),(4.1,'P043Q02'),(6,'P044Q02'),(10,'P045Q01')],
      'S21':[(0,'P047Q01'),(1,'P047Q03'),(3.5,'P048Q02'),(5.5,'P048Q03'),(7.5,'P048Q05')]}
    for m in models:
        m['cues']=[(t,'\n'.join(by_cue[c]['display_lines'])) for t,c in selections[m['id']]]
        m['cue_ids']=[c for t,c in selections[m['id']]]
        m['caption_policy']='Exact supplied display_lines, selected cues only. Preview seconds are NOT narration synchronization.'
    for m in models:
        if not args.scene or m['id'] in args.scene:emit(m,PROJECT/m['id'])
    scenes=[]
    for s in plan['scenes']:
        s=dict(s);s['timing_basis']='UNLOCKED: awaiting actual Jun alignment'
        s['template_status']='representative_authored' if s['scene_id'] in ['S13','S18','S19','S21'] else 'contract_only_not_authored'
        s['template']='S18_S19' if s['scene_id'] in ['S18','S19'] else s['scene_id']
        s['beat_ids']=[f'{s["scene_id"]}.b{i+1:02}' for i in range(len(s['beats']))]
        s['preview_seconds']=None
        scenes.append(s)
        dump(HERE/'scene_templates'/f'{s["scene_id"]}.json',s)
    dump(HERE/'scene_registry.json',{'schema_version':'jun-assembly-v1','scene_count':31,'full_render_enabled':False,'timing_locked':False,'scenes':scenes})
    inputs=[PLAN,CALC,MANIFEST,CAPTIONS,BASE/'index.html',ROOT/'config/channel_style_tokens.json',EP/'director/user-recording-v1/guide_validation.json']
    for n in ['gsap.min.js','fonts/Pretendard-Regular.woff2','fonts/Pretendard-SemiBold.woff2','fonts/Pretendard-Bold.woff2']:inputs.append(BASE/'assets'/n)
    dump(HERE/'input_versions.json',{'inputs':[{'path':str(p),'sha256':sha(p)} for p in inputs],'source_doc_sha256':plan['source_sha256'],'no_tts':True,'no_global_dependency_changes':True})
    dump(HERE/'preview_plan.json',{'timing_basis':'preview_only_unlocked','projects':[{'id':m['id'],'project':str(PROJECT/m['id']),'duration_s':m['duration'],'samples':m['samples']} for m in models]})
    print(json.dumps({'representatives':[m['id'] for m in models],'scene_contracts':len(scenes),'timing_locked':False}))

if __name__=='__main__':main()
