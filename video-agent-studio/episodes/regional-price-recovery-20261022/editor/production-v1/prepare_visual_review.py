"""Explicit provisional visual-review mode. Never relax the actual-Jun timing guard."""
import hashlib,html,json,math,re
from pathlib import Path
ED=Path(__file__).resolve().parent;EP=ED.parent.parent;REPO=EP.parents[2];OUT=EP/'outputs/production-v1-jun';P=OUT/'project';C=OUT/'checks/visual-review'
SHA='99b40e8730ee0f8fdf74402cffbe04b5b418540344e6d2a7175e6a01c3054664'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
NUM={'육백육십사만 건':'664만건','삼만 천육백 호':'31,600호','이만 구천사백 호':'29,400호','칠 년 구 개월':'7년 9개월','오 년 삼 개월':'5년 3개월','두 해 구 개월':'2년 9개월','삼 점 사 퍼센트':'3.4%','오 점 구 퍼센트':'5.9%','십일 퍼센트':'11%','십 퍼센트':'10%','팔 퍼센트':'8%','일 퍼센트':'1%','오백삼십삼':'533','이백삼':'203','지수를 백으로':'지수를 100으로','기준값 백에서':'기준값 100에서','출발선 백과':'출발선 100과','거리는 영입니다':'거리는 0입니다','네 분기':'4분기','다섯 배':'5배','두 배':'2배','두 건':'2건','세 건':'3건','다섯 건':'5건','일 년':'1년','삼 년':'3년','오 년':'5년','육 년':'6년','십 년':'10년','십일 년':'11년','이십 년':'20년','일분기':'1분기','이분기':'2분기','삼분기':'3분기','사분기':'4분기'}
for word,year in [('이천육',2006),('이천팔',2008),('이천구',2009),('이천십',2010),('이천십사',2014),('이천십오',2015),('이천십육',2016),('이천십칠',2017),('이천십팔',2018),('이천이십',2020),('이천이십일',2021),('이천이십이',2022),('이천이십삼',2023),('이천이십사',2024),('이천이십오',2025),('이천이십육',2026)]:NUM[word+' 년']=str(year)+'년'
pattern=re.compile('|'.join(re.escape(k) for k in sorted(NUM,key=len,reverse=True)))
protected=re.compile(r'\d{4}년\s+\d분기[^\s]*|\d+년\s+\d+개월[^\s]*|\S+')
def normalize(text):
    spans=[]
    def sub(m):spans.append({'source_start':m.start(),'source_end':m.end(),'source':m.group(),'display':NUM[m.group()]});return NUM[m.group()]
    return pattern.sub(sub,text),spans
def chunks(text):
    result=[]
    for sentence in re.split(r'(?<=[.!?])\s+',text):
        current=[]
        for word in protected.findall(sentence):
            if current and len(' '.join(current+[word]))>64:result.append(' '.join(current));current=[]
            current.append(word)
        if current:result.append(' '.join(current))
    i=0
    while i<len(result):
        if len(result[i])<16 and len(result)>1:
            if i and len(result[i-1])+len(result[i])+1<=82:result[i-1]+=' '+result.pop(i);continue
            if i+1<len(result) and len(result[i])+len(result[i+1])+1<=82:result[i]+=' '+result.pop(i+1)
        i+=1
    return result
def stamp(t):
    ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
def main():
    C.mkdir(exist_ok=True);assert sha(EP/'outputs/script-review-v3/script_v3.md')==SHA
    lock=read(P/'timing_resolved.json');assert lock['timing_locked'] is False,'This mode must stay explicitly provisional'
    scenes=read(EP/'outputs/script-review-v3/scenes_v3.json')['scenes'];texts={b['beat_id']:b['narration_text'] for s in scenes for b in s['beats']};assert len(texts)==39
    source=(P/'index.html').read_text(encoding='utf-8');assert '<audio'not in source
    body_end=lock['beats'][-1]['end'];end=body_end+3;captions=[];ledger=[];markup=[]
    for beat in lock['beats']:
        original=texts[beat['beat_id']];display,spans=normalize(original);parts=chunks(display)
        while len(parts)*2>beat['duration']:parts[-2:]=[' '.join(parts[-2:])]
        total=sum(len(p) for p in parts);t=beat['start'];remaining=beat['duration']-2*len(parts)
        ledger.append({'beat_id':beat['beat_id'],'approved_original':original,'display_paragraph':display,'normalizations':spans})
        for i,text in enumerate(parts):
            endcue=beat['end'] if i==len(parts)-1 else t+2+remaining*len(text)/total
            cue={'beat_id':beat['beat_id'],'start':t,'end':endcue,'global_start':t+5,'global_end':endcue+5,'text':text};captions.append(cue)
            display_html=re.sub(r'(\d{4}년) (\d분기)|(\d+년) (\d+개월)',lambda m:m.group().replace(' ','\u00a0'),text)
            markup.append(f'<div id="vr-cap-{beat["beat_id"]}-{i}" class="rpr-caption clip" data-start="{t:.6f}" data-duration="{endcue-t:.6f}" data-track-index="8">{html.escape(display_html)}</div>');t=endcue
    assert abs(captions[-1]['end']-837.7)<.00001
    for b,term in [('S002-P1','664만건'),('S006-P2','2015년 2분기'),('S011-P2','29,400호')]:assert any(c['beat_id']==b and term in c['text'] for c in captions)
    assert not any(re.fullmatch(r'(건입니다\.|2분기였습니다\.|구천사백 호였습니다\.)',c['text']) for c in captions)
    source=re.sub(r'<div id="cap-[^"]+" class="rpr-caption clip"[\s\S]*?</div>','',source)
    source=source.replace('<div class="rpr-source">',''.join(markup)+'<div class="rpr-source">',1)
    source=source.replace('data-composition-id="main"','data-composition-id="visual-review"',1).replace('window.__timelines["main"]','window.__timelines["visual-review"]')
    source=source.replace(f'data-duration="{body_end:.6f}" data-fps="30"',f'data-duration="{end:.6f}" data-fps="30"',1)
    # Extend only a separate last-scene copy; all actual-Jun scene files stay unchanged.
    last=(P/'compositions/S012.html').read_text(encoding='utf-8');duration=float(re.search(r'data-composition-id="S012"[^>]*data-duration="([^"]+)"',last).group(1))
    last=last.replace('data-composition-id="S012"','data-composition-id="review-S012"',1).replace('window.__timelines["S012"]','window.__timelines["review-S012"]')
    last=last.replace(f'data-duration="{duration:.6f}" data-fps="30"',f'data-duration="{duration+3:.6f}" data-fps="30"',1)
    match=re.search(r'<section id="S012-P6"[^>]*>',last);tag=match.group();old=float(re.search(r'data-duration="([^"]+)"',tag).group(1));newtag=re.sub(r'data-duration="[^"]+"',f'data-duration="{old+3:.6f}"',tag);last=last[:match.start()]+newtag+last[match.end():]
    (P/'compositions/review-S012.html').write_text(last,encoding='utf-8')
    mount=re.search(r'<div id="mount-S012"[^>]*>',source);tag=mount.group().replace('data-composition-id="S012"','data-composition-id="review-S012"').replace('compositions/S012.html','compositions/review-S012.html');tag=re.sub(r'data-duration="[^"]+"',f'data-duration="{duration+3:.6f}"',tag);source=source[:mount.start()]+tag+source[mount.end():]
    source=source.replace('</style>','.rpr-caption{word-break:keep-all;overflow-wrap:normal}</style>',1)
    badge='<div style="position:absolute;right:80px;top:64px;font-size:20px;color:#526872;z-index:35">음성 없는 전체 검토본 · 임시 타이밍</div>'
    source=re.sub(r'(<div id="root"[^>]*>)',lambda m:m.group()+badge,source,count=1)
    (P/'visual-review.html').write_text(source,encoding='utf-8')
    dump(C/'caption_display_mapping.json',{'script_sha256':SHA,'approved_original_unchanged':True,'timing_locked':False,'basis':'provisional display resegmentation only; 39 paragraph start/end unchanged','paragraphs':ledger})
    dump(C/'captions.json',{'timing_locked':False,'body_offset':5,'last_caption_end_body':body_end,'last_caption_end_global':body_end+5,'captions':captions})
    srt='\n\n'.join(f'{i+1}\n{stamp(c["global_start"])} --> {stamp(c["global_end"])}\n{c["text"]}' for i,c in enumerate(captions))+'\n';(OUT/'previews/full_visual_review_v1.srt').write_text(srt,encoding='utf-8')
    plan={'mode':'visual-review','aliases':['silent-review'],'provisional':True,'timing_locked':False,'script_sha256':SHA,'story_duration':body_end,'body_duration_including_CTA_hold':end,'body_frames':round(end*30),'body_offset':5,'last_caption_end':body_end+5,'outro_start':5+end,'outro_frames':300,'intro_frames':150,'expected_total_duration':end+15,'actual_last_spoken_end':None,'hold_basis':'provisional last caption end +3s; no speech exists','voice':0,'TTS_API_calls':0,'audio_body_render':0,'narration_present':False,'caption_count':len(captions),'shortest_caption_seconds':min(c['end']-c['start'] for c in captions),'longest_caption_characters':max(len(c['text']) for c in captions),'body_output':str(OUT/'previews/full_visual_review_body_v1.mp4'),'assembled_output':str(OUT/'previews/full_visual_review_v1.mp4'),'caption_SRT':str(OUT/'previews/full_visual_review_v1.srt'),'render_options':{'fps':30,'resolution':[1920,1080],'quality':'looks','workers':2,'experimental_fast_capture':False},'protected_original_actual_Jun_entry_sha256':sha(P/'index.html'),'protected_actual_Jun_guard':'run_local.ps1 -Mode body still requires real timing_lock +39audio files'}
    dump(P/'visual_review_plan.json',plan);dump(C/'prepare_receipt.json',plan)
    print(json.dumps({k:plan[k] for k in ['mode','story_duration','body_duration_including_CTA_hold','expected_total_duration','caption_count','shortest_caption_seconds','longest_caption_characters']},ensure_ascii=False))
if __name__=='__main__':main()
