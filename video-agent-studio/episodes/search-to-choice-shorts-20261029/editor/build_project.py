"""Frozen-data portrait composition and original local music. No external calls."""
import hashlib,json,shutil,wave
from pathlib import Path
import numpy as np

EP=Path(__file__).resolve().parents[1]
ROOT=EP.parents[2]
PROJECT=EP/'editor/project'
ASSETS=PROJECT/'assets'
ASSETS.mkdir(parents=True,exist_ok=True)
data=json.loads((EP/'research/chart_data.json').read_text(encoding='utf-8'))
regions=data['facts']['regions']
quarters=sorted(set(r['quarter'] for r in data['observations']))
lookup={(r['region'],r['quarter']):r for r in data['observations']}
frames=[{'q':q,'values':[lookup[r,q]['median_manwon']/10000 for r in regions],'n':sum(lookup[r,q]['n'] for r in regions),'gap':(lookup['서울',q]['median_manwon']-lookup['경기',q]['median_manwon'])/10000} for q in quarters]
assert len(frames)==82 and max(v for f in frames for v in f['values'])<14
assert abs(frames[0]['gap']-1.16)<1e-10 and abs(frames[-1]['gap']-4.90)<1e-10
for weight in ['Regular','Bold']:
 src=ROOT/f'video-agent-studio/episodes/capital-10eok-map-20261017/visual/map-preview-v1/Pretendard-{weight}.ttf'
 shutil.copyfile(src,ASSETS/src.name)
gsap=ROOT/'video-agent-studio/episodes/affordable-home-price-20261026/outputs/rebuild-v2/template-check-v3/scenes/TEST_rate_sensitivity/assets/gsap.min.js'
shutil.copyfile(gsap,ASSETS/'gsap.min.js')
shutil.copyfile(EP/'research/chart_data.json',ASSETS/'chart_data.json')

# Original ambient pulse, no copied reference music, no paid generation.
rate=48000;duration=30;audio=np.zeros((rate*duration,2),dtype=np.float64)
def note(start,length,freq,gain,pan=.0):
 n=min(int(length*rate),len(audio)-int(start*rate));t=np.arange(n)/rate
 env=(1-np.exp(-t/.016))*np.exp(-t/1.1)*np.minimum(1,(length-t)/.15)
 tone=(np.sin(2*np.pi*freq*t)+.19*np.sin(2*np.pi*2*freq*t)+.07*np.sin(2*np.pi*3*freq*t))*env*gain
 offset=int(start*rate);audio[offset:offset+n,0]+=tone*np.sqrt((1-pan)/2);audio[offset:offset+n,1]+=tone*np.sqrt((1+pan)/2)
chords=[[146.832,174.614,220.0],[130.813,164.814,196.0],[116.541,146.832,174.614],[130.813,164.814,220.0]]
beat=60/100
for b in range(48):
 start=b*beat;chord=chords[(b//8)%4]
 note(start,1.2,chord[b%3]*2,.08,(-.2 if b%2 else .2))
 if b%4==0:note(start,2.3,chord[0]/2,.16)
 if b%8==0:
  for freq in chord:note(start,2.5,freq,.05)
for f in [146.832,174.614,220,293.665]:note(28.0,2.0,f,.075)
fade=np.minimum(1,np.arange(len(audio))/int(.35*rate))*np.minimum(1,(len(audio)-np.arange(len(audio)))/int(.9*rate))
audio*=fade[:,None];audio*=.36/max(np.max(np.abs(audio)),1e-9)
pcm=(audio*32767).astype('<i2')
with wave.open(str(ASSETS/'original_data_pulse.wav'),'wb') as f:f.setnchannels(2);f.setsampwidth(2);f.setframerate(rate);f.writeframes(pcm.tobytes())

colors=['#168A91','#C37835','#6685A8','#8A74A8','#889364','#9B7B72']
rows='\n'.join(f'''<div class="row" id="row-{i}" style="top:{588+i*72}px;--color:{color}"><span class="city measure">{region}</span><div class="track"><div class="bar" id="bar-{i}"></div></div><span class="price measure" id="price-{i}"></span></div>''' for i,(region,color) in enumerate(zip(regions,colors)))
doc='''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=1080,height=1920"><title>84㎡대, 지역별 가격 격차의 20년</title><script src="assets/gsap.min.js"></script><style>
@font-face{font-family:Pretendard;src:url('assets/Pretendard-Regular.ttf');font-weight:400}@font-face{font-family:Pretendard;src:url('assets/Pretendard-Bold.ttf');font-weight:700}
*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;background:#F4F1E9;font-family:Pretendard,sans-serif;color:#17313F}#root{position:relative;width:100%;height:100%;overflow:hidden}.clip{position:absolute;inset:0}.ground{position:absolute;inset:0;background:#F4F1E9}.stripe{position:absolute;top:0;left:0;width:100%;height:18px;background:#168A91}.cityscape{position:absolute;bottom:0;width:1080px;height:390px;opacity:.24}.rail{position:absolute;left:140px;right:240px;top:225px;height:4px;background:#CAD8D7}.rail i{display:block;height:100%;width:100%;background:#168A91;transform-origin:left}.eyebrow{position:absolute;left:145px;top:270px;font-size:28px;font-weight:700;letter-spacing:3px;color:#386574}.title{position:absolute;left:140px;top:322px;width:700px;font-size:68px;line-height:1.18;letter-spacing:-2px;font-weight:700}.title div{white-space:nowrap}.title .accent{color:#168A91}.subtitle{position:absolute;left:145px;top:494px;font-size:30px;color:#496371}.date{position:absolute;right:240px;top:482px;font-size:42px;font-weight:700;letter-spacing:-1px}.chart-surface{position:absolute;left:116px;top:563px;width:752px;height:490px;border:1px solid #D7DFDC;border-radius:28px;background:#FFFEFA;box-shadow:0 18px 40px #17313F08}.row{position:absolute;left:0;right:0;height:58px;display:flex;align-items:center}.city{position:absolute;left:148px;font-size:52px;line-height:60px;font-weight:700;letter-spacing:-1px;width:110px}.track{position:absolute;left:277px;width:370px;height:37px;border-radius:4px;background:#EDF0EB;overflow:hidden}.bar{width:100%;height:100%;background:var(--color);transform-origin:left center;transform:scaleX(1);border-radius:4px}.bar:after{content:'';position:absolute;inset:0;background:linear-gradient(90deg,#FFFFFF00,#FFFFFF33)}.price{position:absolute;left:663px;width:177px;text-align:right;font-size:49px;font-weight:700;font-variant-numeric:tabular-nums;letter-spacing:-1.5px;white-space:nowrap}.axis{position:absolute;left:277px;top:1020px;width:370px;height:24px;font-size:24px;color:#536976}.axis span{white-space:nowrap;position:absolute;transform:translateX(-50%)}.samples{position:absolute;left:145px;top:1064px;font-size:28px;color:#496371}.gap-panel{position:absolute;left:140px;top:1120px;width:700px;height:126px;border-radius:20px;background:#17313F;color:#FFFEFA;display:flex;align-items:center;padding:24px}.gap-label{font-size:31px;line-height:1.3;max-width:300px}.gap-value{position:absolute;right:27px;font-size:71px;font-weight:700;font-variant-numeric:tabular-nums;letter-spacing:-2px}.gap-label b{display:block;color:#A9DBD8;font-size:25px}.source{position:absolute;left:145px;top:1274px;width:690px;font-size:26px;line-height:1.55;color:#496371;white-space:nowrap}.source .definition{font-size:25px}.period{display:none;position:absolute;top:173px;left:144px;color:#496371;font-size:27px;font-weight:700}.end-title{position:absolute;left:140px;top:320px;width:700px;font-size:62px;line-height:1.2;font-weight:700;letter-spacing:-2px}.end-title .accent{color:#168A91}.end-label{position:absolute;left:145px;top:515px;font-size:34px;color:#496371}.end-card{position:absolute;left:140px;width:700px;border-radius:26px;background:#FFFEFA;border:1px solid #D7DFDC;padding:24px 30px;display:flex;align-items:center;justify-content:space-between}.end-card.old{top:580px;height:150px}.end-card.new{top:820px;height:188px;background:#17313F;color:#FFFEFA}.end-card .quarter{font-size:37px;font-weight:700}.end-card .amount{font-size:83px;font-weight:700;letter-spacing:-2px;font-variant-numeric:tabular-nums}.new .amount{color:#A9DBD8}.connector{position:absolute;left:452px;top:752px;width:76px;height:49px}.same-area{position:absolute;left:145px;top:1057px;font-size:32px;color:#496371;line-height:1.45}.cta{position:absolute;left:140px;top:1156px;width:700px;height:88px;border-radius:16px;border:2px solid #168A91;background:#168A9110;color:#175F69;display:flex;align-items:center;justify-content:center;gap:16px;font-size:32px;font-weight:700}.cta svg{flex:none}.end-source{top:1272px}.focusline{position:absolute;left:140px;top:1102px;width:700px;height:1px;background:#CAD8D7}
</style></head><body><div id="root" data-composition-id="regional-gap" data-start="0" data-duration="30" data-width="1080" data-height="1920">
<div id="ground" class="clip" data-start="0" data-duration="30" data-track-index="0"><div class="ground"></div><div class="stripe"></div><svg class="cityscape" viewBox="0 0 1080 390" aria-hidden="true"><g fill="#BCCDC9"><path d="M0 390V170H100V110H220V390Z"/><path d="M235 390V230H370V60H475V390Z"/><path d="M495 390V155H640V250H742V390Z"/><path d="M770 390V95H895V175H1010V390H1080V390Z"/></g><g stroke="#F4F1E9" stroke-width="9"><path d="M30 205H195M30 250H195M30 295H195M400 95H445M400 145H445M400 195H445M525 190H610M525 240H610M800 135H865M800 185H865M800 235H865"/></g></svg></div>
<section id="history" class="clip" data-start="0" data-duration="23" data-track-index="1"><div id="history-inner"><div class="period measure">2006Q1 → 2026Q2</div><div class="rail"><i id="progress"></i></div><div class="eyebrow measure">데이터로보는부동산</div><div class="title"><div class="measure">같은 84㎡대,</div><div class="accent measure">지역별 가격은?</div></div><div class="subtitle measure">실거래 중위가격 · 명목</div><div id="date" class="date measure"></div><div class="chart-surface"></div>
__ROWS__
<div class="axis"><span class="measure" style="left:0">0</span><span class="measure" style="left:185px">7</span><span class="measure" style="left:370px">14억</span></div><div class="samples measure" id="samples"></div><div class="gap-panel"><div class="gap-label measure">서울−경기 차이<b>두 지역 중위값의 차이</b></div><div class="gap-value measure" id="gap"></div></div><div class="source"><div class="measure">국토교통부 실거래가 · 수집 6개 지역</div><div class="definition measure">84㎡ 이상·85㎡ 미만 · 분기별 거래</div></div></div></section>
<section id="closing" class="clip" data-start="23" data-duration="7" data-track-index="2"><div id="closing-inner"><div class="period measure">2006Q1 → 2026Q2</div><div class="rail"><i></i></div><div class="eyebrow measure">데이터로보는부동산</div><div class="end-title"><div class="measure">20년이 흐른 뒤,</div><div class="accent measure">가격 차이는?</div></div><div class="end-label measure">서울−경기 84㎡대 중위가격 차이</div><div class="end-card old"><span class="quarter measure">2006Q1</span><span class="amount measure">1.16억</span></div><svg class="connector" viewBox="0 0 76 49" aria-hidden="true"><path d="M38 1V40M13 22L38 47L63 22" stroke="#168A91" stroke-width="6" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg><div class="end-card new"><span class="quarter measure">2026Q2</span><span class="amount measure">4.90억</span></div><div class="same-area"><div class="measure">같은 면적대에서 확인한 지역 격차</div></div><div class="focusline"></div><div class="cta" id="cta"><svg width="36" height="36" viewBox="0 0 36 36" aria-hidden="true"><path fill="#168A91" d="M4 5h28v20H19l-9 7v-7H4z"/></svg><span class="measure">다음 비교 지역은? 댓글로 남겨주세요</span></div><div class="source end-source"><div class="measure">국토교통부 실거래가 · 수집 6개 지역</div><div class="definition measure">분기 중위값 · 자료 종점 2026-06-30</div></div></div></section>
<audio id="music" class="clip" src="assets/original_data_pulse.wav" data-start="0" data-duration="30" data-track-index="3" data-volume="0.70"></audio>
</div><script>
const DATA=__DATA__;const REGIONS=__REGIONS__;const TOTAL=30;const driver={t:0};
function stateAt(time){let u=Math.max(0,Math.min(1,(time-2.4)/16.6)),p=u*(DATA.length-1),i=Math.floor(p),j=Math.min(i+1,DATA.length-1),mix=p-i;const a=DATA[i],b=DATA[j];return {q:a.q,next_q:b.q,between:time>2.4&&time<19,values:a.values.map((v,k)=>v+(b.values[k]-v)*mix),gap:a.gap+(b.gap-a.gap)*mix,n:a.n,position:p,complete:u===1};}
function render(time){const s=stateAt(time);document.getElementById('history').style.opacity=time<23?1:0;document.getElementById('closing').style.opacity=time>=23?1:0;document.getElementById('date').textContent=s.between?s.q+' → '+s.next_q:s.q;document.getElementById('date').style.fontSize=s.between?'28px':'42px';document.getElementById('samples').textContent=s.between?'분기 관측값을 연결한 흐름':'이 분기 표본 '+s.n.toLocaleString('ko-KR')+'건';document.getElementById('gap').textContent=(Math.round((s.gap+1e-9)*100)/100).toFixed(2)+'억';document.getElementById('progress').style.transform='scaleX('+Math.max(.01,Math.min(1,time/19))+')';for(let i=0;i<6;i++){document.getElementById('bar-'+i).style.transform='scaleX('+(s.values[i]/14)+')';document.getElementById('price-'+i).textContent=(Math.round((s.values[i]+1e-9)*100)/100).toFixed(2)+'억';}document.getElementById('cta').style.opacity=time>=26?1:0;window.__frameState={time,...s};}
const tl=gsap.timeline({paused:true});tl.to(driver,{t:30,duration:30,ease:'none',onUpdate:()=>render(driver.t)},0);window.__timelines=window.__timelines||{};window.__timelines['regional-gap']=tl;window.__sourceSeek=(t)=>{tl.seek(t,false);render(t);};render(0);
</script></body></html>'''
doc=doc.replace('__ROWS__',rows).replace('__DATA__',json.dumps(frames,ensure_ascii=False)).replace('__REGIONS__',json.dumps(regions,ensure_ascii=False))
(PROJECT/'index.html').write_text(doc,encoding='utf-8')
shutil.copyfile(EP/'BRIEF.md',PROJECT/'BRIEF.md')
frame_spec={'canvas':[1080,1920],'fps':30,'duration':30,'font':'Pretendard','colors':colors,'safe_profile':'youtube_portrait_full_frame_v2','fixed_chart_axis_eok':[0,14],'bar_origin_x':277,'bar_width_px':370,'row_y':[588+i*72 for i in range(6)],'quarter_interpolation':'linear visual interpolation between observed quarters; fractions are not additional transactions or daily observations','start_hold_s':2.4,'timeline_end_s':19,'endpoint_hold_s':4,'closing_start_s':23,'CTA_start_s':26,'critical_text_rect':[140,260,840,1360],'source_observations':82,'component_adopted':'animated-bar-chart: card, numeric callout and proportionate fills adapted to fixed horizontal rows; original source retained'}
(EP/'editor/frame_spec.json').write_text(json.dumps(frame_spec,ensure_ascii=False,indent=2),encoding='utf-8')
ledger={'assets':[{'file':str(p.relative_to(EP)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in ASSETS.iterdir() if p.is_file()], 'music':{'type':'original deterministic local synthesis','copyright':'original for this production','paid_cost':0,'duration_s':30},'reference_media_reused':False,'voice_generated':False}
(EP/'editor/asset_ledger.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'project':str(PROJECT),'quarters':len(frames),'latest_n':frames[-1]['n'],'max_price':max(v for f in frames for v in f['values']),'duration':30},ensure_ascii=False))
