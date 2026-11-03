"""Offline, copy-only editor sidecar. Builds projects and plans; NEVER renders or calls TTS.

python -X utf8 build.py [--require-measured]
Candidate script -> clearly estimated preview; locked SHA + final_timing -> measured projects.
"""
import argparse
import hashlib
import html
import importlib.util
import json
import math
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from alignment import Alignment, norm, parse_script
from additions import additions

HERE = Path(__file__).resolve().parent
EP = HERE.parents[1]
WORKSPACE = EP.parents[2]
OUT = EP / 'outputs/private-production-v2'
DIRECTOR = EP / 'director/two-episode-production-v1'
BASE = HERE / 'baseline'
INPUTS = {}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tracked(path):
    path = Path(path).resolve()
    INPUTS[str(path.relative_to(WORKSPACE)).replace('\\','/')] = digest(path)
    return path


def read_json(path):
    return json.loads(tracked(path).read_text(encoding='utf-8-sig'))


def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf8')


def module(name, path):
    spec=importlib.util.spec_from_file_location(name, tracked(path))
    mod=importlib.util.module_from_spec(spec)
    sys.modules[name]=mod
    spec.loader.exec_module(mod)
    return mod


def resolve_path(value):
    p=Path(value)
    if p.is_absolute():
        result=p.resolve()
    elif (WORKSPACE/p).is_file():
        result=(WORKSPACE/p).resolve()
    else:
        result=(EP/p).resolve()
    if not result.is_relative_to(WORKSPACE):
        raise ValueError('Input must stay inside the workspace')
    return result


def script_and_timing(require_measured, timing_path=None, narration_handoff=None):
    lockpath=DIRECTOR/'locked_script.json'
    lock=read_json(lockpath) if lockpath.exists() else None
    if lock:
        script=resolve_path(lock.get('script_path') or lock.get('path') or lock.get('script', ''))
        expected=lock.get('script_sha256') or lock.get('sha256')
        if not expected or digest(script)!=expected:
            raise ValueError('locked_script.json must contain the current script SHA256')
        if not lock.get('codex_content_pass') or not lock.get('claude_content_pass'):
            raise ValueError('Both content review passes are required in the current lock')
        for name,expected_sha in lock.get('review_receipt_sha256',{}).items():
            if digest(tracked(resolve_path(name)))!=expected_sha:
                raise ValueError('Locked content review receipt SHA mismatch: '+name)
    else:
        script=EP/'outputs/script-final-v5/script_v5.md'
    script=tracked(script)
    chapters=parse_script(script.read_text(encoding='utf8'))
    fp=resolve_path(timing_path) if timing_path else EP/'narration/free-tts-v1/final_timing.json'
    if timing_path:
        if not narration_handoff:raise ValueError('Formal narration handoff path is required before measured integration')
        delivery=read_json(resolve_path(narration_handoff))
        if delivery.get('status') in ['in_progress','technical_validation_pending','failed']:
            raise ValueError('Narration formal handoff is not ready')
    timing=read_json(fp) if fp.exists() else None
    if timing:
        if not lock or timing.get('script_sha256')!=digest(script):
            raise ValueError('final_timing is not bound to the current locked script')
        if resolve_path(timing['script_path'])!=script:
            raise ValueError('final_timing script_path mismatch')
        for key in ['voice','audio_revision','chapters']:
            if key not in timing:
                raise ValueError('Missing timing contract field: '+key)
    if require_measured and not timing:
        raise ValueError('Measured final_timing.json and matching locked script are required')
    return script, chapters, lock, timing


def cue_times(num, chapter, timing, F):
    if timing:
        rows=timing['chapters']
        if isinstance(rows,dict):
            rows=list(rows.values())
        match=[c for c in rows if int(c['chapter'])==num]
        if len(match)!=1:
            raise ValueError(f'Exactly one measured chapter {num} required')
        row=match[0]
        para_ids={int(c['paragraph']) for c in row['cues']}
        count=len(chapter['paragraphs'])
        source_order=[int(p['paragraph']) for p in row.get('paragraphs',[])] or sorted(para_ids)
        if len(source_order)!=count or set(source_order)!=para_ids or source_order!=sorted(para_ids):
            raise ValueError('Cannot infer complete paragraph order from measured cues and paragraph metadata')
        para_map={pid:i for i,pid in enumerate(source_order)}
        for pid,index in para_map.items():
            body=''.join(norm(c['text']) for c in row['cues'] if int(c['paragraph'])==pid)
            if body!=norm(chapter['paragraphs'][index]):raise ValueError('Measured paragraph content differs from locked script')
        cues=[{**c,'paragraph':para_map[int(c['paragraph'])],'paragraph_source':c['paragraph'],
               'paragraph_mapping':'global narration paragraph id to chapter-local 0-based editor index; exact paragraph text checked'} for c in row['cues']]
        ids=set()
        end=0
        for c in cues:
            for k in ['id','paragraph','text','spoken_text','start_s','end_s','timing_basis']:
                if k not in c: raise ValueError(f'Cue missing {k}: ch{num}')
            if c['id'] in ids or not end<=c['start_s']<c['end_s']<=row['total_seconds']:
                raise ValueError(f'Invalid/overlapping cue: {c["id"]}')
            if not 0<=c['paragraph']<len(chapter['paragraphs']):
                raise ValueError('paragraph must be zero-based per contract')
            ids.add(c['id']); end=c['end_s']
        minimum=.6 if num==1 else 3.5
        if cues[0]['start_s']<minimum-1/30:
            raise ValueError('Leading silence / chapter-card contract mismatch')
        if abs(row['total_seconds']*30-round(row['total_seconds']*30))>1e-4:
            raise ValueError('Measured total must end on a 30fps frame boundary')
        audio=tracked(resolve_path(row['audio_file']))
        probe=tracked(WORKSPACE/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe')
        check=subprocess.run([str(probe),'-v','error','-show_entries','format=duration:stream=codec_type,sample_rate,channels','-of','json',str(audio)],capture_output=True,check=True)
        actual=json.loads(check.stdout)
        if not any(s.get('codec_type')=='audio' for s in actual['streams']) or abs(float(actual['format']['duration'])-float(row['total_seconds']))>1/30:
            raise ValueError('Measured audio stream/duration differs from final_timing: '+str(audio))
        last=float(row['last_speech_end_s'])
        if not end-1/30<=last<=row['total_seconds']:
            raise ValueError('last_speech_end_s is outside cue/audio bounds')
        if num==10 and row['total_seconds']-last<3-1/30:
            raise ValueError('Final chapter requires >=3s after last speech')
        return cues,float(row['total_seconds']),last,audio,'measured_audio_units'
    cues=[]
    t=.6 if num==1 else 3.5
    for pi,p in enumerate(chapter['paragraphs']):
        # Existing local semantic splitter, with numbers and units kept as one lexical token.
        pieces=F.make_cues([p])
        for c in pieces:
            dur=max(.7,F.spoken_len(c['text'])/6.19)
            cues.append(dict(id=f'ch{num:02d}-p{pi:02d}-c{len(cues):03d}',paragraph=pi,text=c['text'],
                             spoken_text=c['text'],start_s=round(t,6),end_s=round(t+dur,6),
                             timing_basis='estimated_placeholder; legacy 6.19 chars/s; new TTS voice unmeasured'))
            t+=dur+.15
        t+=.35
    last=cues[-1]['end_s']
    total=math.ceil((last+(3 if num==10 else 1.2))*30)/30
    return cues,total,last,None,'estimated_placeholder'


# Explicit semantic changes: deleted caution text now triggers the positive explanation of the same fact.
ALIASES={
 '쓸 수 있는 돈이':'쓸 수 있는 돈이', '화면의 숫자는':'투자계좌는 배당과',
 '집값은 연 2%':'투자계좌는 배당과', '투자계좌는 배당':'투자계좌는 배당과',
 '세금과 운용비용':'실제 상품별 세금과 운용비용',
 '출발 자금이 많은':'같은 집과 같은 예산', '더 싼 집에':'같은 집과 같은 예산', '다른 조건의 차이가':'주거 방식에 따른 차이',
 '거래를 시작하는':'설명용 가정 금액', '계약비용을 100만원':'이 비용 묶음에 설명용 가정 약 100만원',
 '처음부터 돈이':'월세 가구가 더 큰 투자계좌로', '같은 돈이 아니라':'월세 가구가 더 큰 투자계좌로',
 '유지·보유 비용을':'보유세와 수선비', '한 가지 흐름만':'초기 투자금과 월 적립금',
 '월세가 나간다는':'초기 투자금과 월 적립금',
 '두 가구의 차이는':'매매와 임차의 비용 가정 차이는',
 '보유세와 수선':'현실에서는 보유세와 수선', '월세와 보증금도':'월세와 보증금은', '여기서 투자하지 않은':'여기서는 투자하지 않은',
 '같은 효과를 두 번':'원금 상환의 효과는', '새 수익으로 더하지':'보증금 반환은 자산의 형태가',
 '포기한 투자수익을':'작은 계좌에서 실제로', '같은 차이가 두 번':'작은 계좌에서 실제로',
 '배당을 다시 더하면':'이 총수익으로 배당 효과까지', '한 번 더 붙이면':'이 원화 수익률로',
 '이번 계산은 이 복잡한':'이번 계산은 배당과',
 '앞으로의 수익 예측이나':'10년간 주거 방식에 따른 차이를', '배당이나 환율을 추가':'배당과 환율 효과를 포함한',
 '실제 상품으로 계산할 때는':'실제 상품별 계산에서는',
 '한 달 수익을':'다음 달부터 수익을', '매달 0.5%를':'월 0.5%의 단순 배분과',
 '가상의 임대료까지':'주거 혜택은 이 지출표에서', '같은 주거 혜택이':'주거 혜택은 이 지출표에서',
 '월세만 따로 누적한':'주거비를 낸 뒤 남은 금융자산까지',
 '고정된 순위를':'조건에 따라 가장 크게', '팔거나 추가로':'그 경로를 멈추도록',
}


TEXT_REPLACEMENTS={
 '돈이 움직이는 구조를 설명하는 가정 · 실제 단지의 지난 10년 성과가 아닙니다':'돈이 움직이는 구조를 비교하는 동일 조건의 가정 모형',
 '계산 안 함':'추가 반영 전',
 '한 가지 흐름만 보면 놓침':'초기 투자금과 월 적립금을 함께 계산',
 '돌려받은 원금 = 새 수익 아님':'보증금 반환 = 자산 형태 전환',
 "포기한 투자수익을":"처음 묶인 자금", '다시 비용으로 빼기':'작아진 투자계좌에 반영', '같은 차이가 두 번':'작은 계좌에서 실제 수익 계산',
 '배당이 들어 있는 수익률에 배당을 다시 더하면 실제보다 높아짐':'총수익 = 가격 변화 + 배당 재투자',
 '원화 ETF 수익률에 환율 상승을 한 번 더 붙이면 중복':'원화 ETF 수익률에 환율 효과 포함',
 '예측 아님':'10년 비교 조건', '지난 10년 실제 성과 아님':'세 가구 동일 적용', '배당·환율 추가 적용 안 함':'배당·환율 포함',
 '월말에 넣은 돈이 한 달 수익을 미리 얻기':'월말 적립 → 다음 달부터 수익', '월 0.5% 단순 적용':'월 약 0.487% 복리 적용',
 '가상의 임대료를 현금수익으로 추가':'주거 혜택은 매달 지출표에 반영', '같은 주거 혜택이 겹침':'주거 혜택을 한 번 반영',
 '기존 ETF 매도 없음':'월예산 안에서 경로 유지', '추가 대출 없음':'예산 초과 시 경로 계산 종료',
 '과거 실적·전망 아님':'비교를 위한 가정', '실제 사례 계산은 이번 편에서 하지 않음':'실제 사례는 계약 조건을 연결해 별도 계산',
 '손익분기선은 계산하지 않음':'추가 조합으로 경계 확인', '계산하지 않음':'추가 계산 대상',
 '수익 없음':'수익률 0% 현금',
}


def positive_text(text):
    for a,b in TEXT_REPLACEMENTS.items(): text=text.replace(a,b)
    return text.replace('class="mark no"','class="mark explain"').replace('<b>✕</b>','<b>→</b>').replace('<br>',' ')


def modify_scenes(num, scenes, new, F):
    if num==2:
        scenes[1]['at']='투자계좌는 배당과'
        # First tile refers to the 2% planning scene that directly preceded it.
        scenes[1]['js']=scenes[1]['js'].replace('T("집값은 연 2%")','S0("s2b",.3)')
        scenes[2]['html']=F.panel('s2c-p', F.box('s2c-a',60,80,700,150,'집값 변화',size=40)+F.box('s2c-b',940,80,700,150,'매달 저축한 돈',size=40)+F.box('s2c-same',260,350,1200,100,'같은 집 · 같은 예산 → 주거 방식에 따른 차이',size=34),wide=True)
        scenes[2]['js']='enter("#s2c-a",T("집값이 얼마나"));enter("#s2c-b",T("매달 얼마를 저축"));enter("#s2c-same",T("같은 집과 같은"));'
        same=scenes[3]
        same['html']=same['html'][:same['html'].index('<div id="s2d-wl"')]+F.box('s2d-result',230,370,1450,105,'세 가구 모두 120개월 시점의 자산과 남은 빚 확인',size=31,border=F.BUY)+'</div>'
        same['js']='[0,1,2].forEach(k=>{fade("#s2d-n"+k,T("비교 기간도"));growX("#s2d-b"+k,T("비교 기간도",.2+k*.2),1.4);});fade("#s2d-mk, #s2d-ml",T("비교 기간도",1.6));stagger(["#s2d-c0","#s2d-c1","#s2d-c2","#s2d-c3"],T("120개월이 지난",.3),.25);enter("#s2d-result",T("120개월이 지난"));'
        scenes=[scenes[0],new['regional'],new['planning'],*scenes[1:]]
    if num==5:
        end=next(s for s in scenes if s['id']=='s5b')
        end['html']=re.sub(r'(<div id="s5b-bt"[^>]*style=")([^"]*)(")',lambda m:m[1]+m[2]+'font-size:28px;width:200px;font-weight:700;color:'+F.BUY+';'+m[3],end['html'])
        end['html']=re.sub(r'(<div id="s5b-br"[^>]*style=")([^"]*)(")',lambda m:m[1]+m[2]+'border-color:'+F.BUY+';border-width:3px 3px 3px 0;'+m[3],end['html'])
        end['js']=end['js'].replace('enter("#s5b-d1, #s5b-t2", T("남은 대출은"))','enter("#s5b-t2", T("남은 대출은"))')
        end['js']+='\nenter("#s5b-d1",T("10년 동안 갚은 원금"));dim("#s5b-d0, #s5b-t0",T("10년 동안 갚은 원금"),.35);tl.to("#s5b-d1",{scale:1.4,duration:.3,yoyo:true,repeat:1},T("10년 동안 갚은 원금",.4));'
        target=next(s for s in scenes if s['id']=='s5c')
        target.update(at='처음 빌린 3억6천만원에서',title='상환한 원금은 줄어든 대출잔액에 반영')
        target['html']=F.panel('s5c-p',F.box('s5c-r0',60,70,480,180,'처음 대출 3억6천만원',size=31)+F.arrow('s5c-a0',560,160,170)+F.box('s5c-r1',750,70,850,180,'매달 갚은 원금 차감 → 남은 대출잔액',size=31)+F.box('s5c-r2',320,345,1100,130,'마지막 순자산에서 남은 대출잔액을 한 번 차감',border=F.BUY,size=31),wide=True)
        target['js']='enter("#s5c-r0",S0("s5c",.3));growX("#s5c-a0",T("매달 갚은 원금을"),.6);enter("#s5c-r1",T("대출잔액을 계산"));enter("#s5c-r2",T("그 잔액을 한 번"));'
    if num==6:
        next(s for s in scenes if s['id']=='s6c')['at']='이번 계산은 배당과'
    if num==8:
        scenes[0]['at']='이어서 집값과 투자수익을'
        scenes=[new['sensitivity'],new['leverage'],*scenes]
    if num==9:
        risk=next(s for s in scenes if s['id']=='s9d')
        extra=F.box('s9d-deposit',120,35,1100,80,'계약 종료 시 보증금 반환 가능성 확인',size=28,border=F.JEONSE)
        risk['html']=risk['html'][:-6]+extra+'</div>'
        risk['js']+='\nenter("#s9d-deposit",T("보증금을 돌려받을 수 있는지"));'
    if num==10:
        scenes=new['closing']
    for s in scenes:
        s['html']=positive_text(s['html']); s['src']=positive_text(s['src'])
        s.setdefault('material_type','editorial_diagram')
        s.setdefault('origin','frozen_motion_v1_graphics_and_motion')
    return scenes


CSS_EXTRA='''
.source{width:1728px;max-height:46px;white-space:normal;line-height:1.2;font-size:18px;}
.title{max-width:1760px;white-space:normal;line-height:1.2;}
.mark.explain b{background:var(--primary)} .mark.explain .ml{color:var(--ink)}
.mark{max-width:calc(100% - 48px);height:auto;min-height:44px;white-space:normal;font-size:22px;line-height:1.25;}
.card-art{position:absolute;left:800px;top:180px;width:1740px;height:650px;transform:scale(.58);transform-origin:0 0;opacity:.5;}
.cardtitle{left:105px;top:420px;max-width:1700px;font-size:64px;white-space:normal;line-height:1.25;}
.cardfill{position:absolute;inset:0;background:#102333;}
.card-art .pnl{background:#e6e7e0;}
.cardshade{position:absolute;inset:0;background:linear-gradient(90deg,#102333 8%,rgba(16,35,51,.92) 38%,rgba(16,35,51,.0) 85%);}
#s5a-c .sub,#s9a-c .sub{color:#425a68!important;}
#s5b-lg span:first-child{color:#225ec3!important;}#s5b-lg span:last-child{color:#54636b!important;}
'''


def captions(cues, total):
    return '\n'.join(f'<p id="cue{i:03d}" class="clip cue" data-start="{c["start_s"]}" data-duration="{min(c["end_s"]+.08,cues[i+1]["start_s"] if i+1<len(cues) else total)-c["start_s"]:.6f}" data-track-index="9">{html.escape(c["text"])}</p>' for i,c in enumerate(cues))


def dependencies(chdir):
    assets=chdir/'assets'
    (assets/'fonts').mkdir(parents=True,exist_ok=True)
    for weight in ['Regular','SemiBold','Bold','ExtraBold']:
        f=tracked(EP/f'outputs/intro-motion-v1/assets/fonts/Pretendard-{weight}.woff2')
        shutil.copy2(f,assets/'fonts'/f.name)
    gsap=tracked(EP/'outputs/regional-motion-v1/assets/gsap.min.js')
    shutil.copy2(gsap,assets/'gsap.min.js')


def build_chapter(num, chapter, cues, total, last, audio, basis, old, scenes, F):
    align=Alignment(old['paragraphs'],chapter['paragraphs'],cues,ALIASES)
    first=0 if num==1 else 3
    starts=[first]
    for s in scenes[1:]: starts.append(max(first,align.locate(s['at'])-.15))
    if any(b<=a for a,b in zip(starts,starts[1:])):
        raise ValueError(f'Non-monotonic scene anchors ch{num}: {list(zip([s["id"] for s in scenes],starts))}')
    spans={s['id']:[a,(starts[i+1] if i+1<len(starts) else total)-a] for i,(s,a) in enumerate(zip(scenes,starts))}
    anchors={}
    for s in scenes:
        for literal in re.findall(r'''\bT\(\s*["']([^"']+)["']''',s['js']):
            anchors[literal]=align.locate(literal)
    capend=last if num==10 else total
    chdir=OUT/f'ch{num:02d}'
    dependencies(chdir)
    for s in scenes:
        for asset in s['assets']:
            asset=tracked(asset)
            shutil.copy2(asset,chdir/'assets'/asset.name)
    card=''
    if num!=1:
        art=re.sub(r'id="([^"]+)"',r'id="card-art-\1"',scenes[0]['html'])
        card=f'<section id="card" class="clip" data-start="0" data-duration="3" data-track-index="1"><div id="card-w" class="wrap"><div class="cardfill"></div><div class="card-art" aria-hidden="true">{art}</div><div class="cardshade"></div><div id="card-t" class="cardtitle">{num}. {html.escape(chapter["title"])}</div></div></section>'
    body=[card, f'<div id="brand" class="clip" data-start="{first}" data-duration="{total-first}" data-track-index="0"><i>|</i><span>데이터로 보는 부동산</span></div>',f'<div id="tag" class="clip" data-start="{first}" data-duration="{total-first}" data-track-index="0">주거 방식 비교</div>']
    for s in scenes:
        a,d=spans[s['id']]
        body.extend([f'<h2 id="title-{s["id"]}" class="clip title" data-start="{a}" data-duration="{d}" data-track-index="2">{html.escape(s["title"])}</h2>',f'<section id="{s["id"]}" class="scene clip" data-start="{a}" data-duration="{d}" data-track-index="3"><div class="wrap" id="{s["id"]}-w">{s["html"]}</div></section>',f'<p id="src-{s["id"]}" class="clip source" data-start="{a}" data-duration="{d}" data-track-index="8">{html.escape(s["src"])}</p>'])
    body += [f'<div id="capbox" class="clip" data-start="{first}" data-duration="{capend-first}" data-track-index="7"></div>',captions(cues,total)]
    if audio:
        audio_name='narration'+audio.suffix
        shutil.copy2(audio,chdir/'assets'/audio_name)
        body.append(f'<audio id="narration" class="clip" src="assets/{audio_name}" data-start="0" data-duration="{total}" data-track-index="10"></audio>')
    helpers=tracked(BASE/'src/helpers.js').read_text(encoding='utf8')
    helpers=re.sub(r'const T = .*?\n      };', '''const T = (sub, off=0) => {if(!Object.hasOwn(ANCHORS,sub)) throw new Error('Unmapped anchor: '+sub); return ANCHORS[sub]+off;};''',helpers,count=1,flags=re.S)
    # The old wrappers faded out onto an empty canvas. Let the framework hard-cut lifecycle own the seam.
    helpers=re.sub(r'\s*tl.to\(`#\$\{id\}-w`,.*?s \+ d - 0.3\);','',helpers)
    if num==1:
        helpers=helpers[:helpers.index('      // 챕터 화면')]
    js='\n'.join('{\n'+s['js']+'\n}' for s in scenes)
    page=f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{num}. {html.escape(chapter['title'])}</title><script src="assets/gsap.min.js"></script><style>{tracked(BASE/'src/shell.css').read_text(encoding='utf8')}{CSS_EXTRA}</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{total}" data-width="1920" data-height="1080">{''.join(body)}</div>
<script>document.fonts.ready.then(()=>{{
window.__timelines=window.__timelines||{{}};
const ANCHORS={json.dumps(anchors,ensure_ascii=False)};
const SPANS={json.dumps(spans)};const CARD=3;
{helpers}
{js}
window.__timelines['main']=tl;
}});</script></body></html>'''
    (chdir/'index.html').write_text(page,encoding='utf8')
    config(chdir,num)
    manifest=[dict(scene_id=s['id'],title=s['title'],start_s=spans[s['id']][0],end_s=sum(spans[s['id']]),source=s['src'],material_type=s['material_type'],origin=s['origin'],narration_anchor=s['at']) for s in scenes]
    dump(chdir/'timing.json',dict(chapter=num,timing_basis=basis,total_seconds=total,last_speech_end_s=last,cues=cues,scenes=manifest))
    dump(chdir/'anchor_audit.json',dict(chapter=num,paragraph_alignment=align.paragraph_audit,anchors=align.audit,zero_second_fallback=False))
    return dict(chapter=num,total_seconds=total,last_speech_end_s=last,timing_basis=basis,project=f'ch{num:02d}',scenes=manifest)


def config(chdir,num):
    dump(chdir/'hyperframes.json',{'paths':{'blocks':'compositions','components':'compositions/components','assets':'assets'},'authoringSkill':'general-video'})
    dump(chdir/'meta.json',{'id':f'housing-private-ch{num:02d}','name':f'housing-private-ch{num:02d}'})
    dump(chdir/'package.json',{'name':f'housing-private-ch{num:02d}','private':True,'type':'module','devDependencies':{'hyperframes':'0.8.181'}})


def assembly_plan(results,media_by_id,basis):
    """One frame-aligned edit map for chapter picture, voice and all caption cues."""
    probe=read_json(HERE/'checks/brand_frame_probe.json')
    intro_frames=int(probe['channel_brand_intro_clean_v7']['streams'][0]['nb_frames'])
    outro_frames=int(probe['channel_brand_outro_clean_v7']['streams'][0]['nb_frames'])
    if any(probe[k]['streams'][0]['r_frame_rate']!='30/1' for k in probe):
        raise ValueError('Brand assets must match locked 30fps canvas')
    intro_s,outro_s=intro_frames/30,outro_frames/30
    ch1=read_json(OUT/'ch01/timing.json')
    hook=math.ceil(max(c['end_s'] for c in ch1['cues'] if c['paragraph']==0)*30)/30
    segments=[{'id':'opening_hook','type':'chapter','chapter':1,'file':'ch01/chapter_versioned.mp4','source_start_s':0,'source_end_s':hook,'global_start_s':0,'global_end_s':hook},
              {'id':'clean_brand_intro','type':'brand','asset':media_by_id['channel_brand_intro_clean_v7'],'source_start_s':0,'source_end_s':intro_s,'global_start_s':hook,'global_end_s':hook+intro_s},
              {'id':'chapter_1_after_hook','type':'chapter','chapter':1,'file':'ch01/chapter_versioned.mp4','source_start_s':hook,'source_end_s':results[0]['total_seconds'],'global_start_s':hook+intro_s,'global_end_s':results[0]['total_seconds']+intro_s}]
    offsets=[{'chapter':1,'local_start_s':0,'local_end_s':hook,'global_offset_s':0},
             {'chapter':1,'local_start_s':hook,'local_end_s':results[0]['total_seconds'],'global_offset_s':intro_s}]
    cursor=results[0]['total_seconds']+intro_s
    for ch in results[1:]:
        duration=ch['total_seconds']
        segments.append({'id':f'chapter_{ch["chapter"]}','type':'chapter','chapter':ch['chapter'],'file':f'ch{ch["chapter"]:02d}/chapter_versioned.mp4','source_start_s':0,'source_end_s':duration,'global_start_s':cursor,'global_end_s':cursor+duration})
        offsets.append({'chapter':ch['chapter'],'local_start_s':0,'local_end_s':duration,'global_offset_s':cursor})
        cursor+=duration
    segments.append({'id':'clean_brand_outro','type':'brand','asset':media_by_id['channel_brand_outro_clean_v7'],'source_start_s':0,'source_end_s':outro_s,'global_start_s':cursor,'global_end_s':cursor+outro_s})
    def stamp(t):
        ms=round(t*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
        return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'
    lines=[]
    for ch in results:
        for cue in read_json(OUT/f'ch{ch["chapter"]:02d}/timing.json')['cues']:
            found=[o for o in offsets if o['chapter']==ch['chapter'] and o['local_start_s']<=cue['start_s']<o['local_end_s']]
            if len(found)!=1:raise ValueError('Global cue offset is ambiguous')
            delta=found[0]['global_offset_s']
            lines.append(f'{len(lines)+1}\n{stamp(cue["start_s"]+delta)} --> {stamp(cue["end_s"]+delta)}\n{cue["text"]}\n')
    name='captions_measured.srt' if basis=='measured_audio_units' else 'captions_estimated.srt'
    (OUT/name).write_text('\n'.join(lines),encoding='utf8')
    edl={'status':basis,'fps':30,'hook_cut_s':hook,'intro_video_frames':intro_frames,'outro_video_frames':outro_frames,
         'segments':segments,'offset_map':offsets,'total_seconds':cursor+outro_s,'captions':name,'execute':False,
         'caption_hidden_intervals':[{'start_s':hook,'end_s':hook+intro_s,'reason':'clean_brand_intro'},
                                      {'start_s':cursor-3,'end_s':cursor,'reason':'final_silent_CTA_hold'},
                                      {'start_s':cursor,'end_s':cursor+outro_s,'reason':'clean_brand_outro'}],
         'voice_and_picture_use_identical_splits':True,'note':'Source-level edit plan; no rendered final file exists. 5s/10s use actual video-frame duration, not AAC container tails.'}
    dump(OUT/'assembly_edl.json',edl)
    return edl


def build_intro(chapter,cues,total,last,audio,basis,old,IB):
    align=Alignment(old['paragraphs'],chapter['paragraphs'],cues)
    times=[align.locate(text) for text,spoken,end in IB.CUES]
    scenes=[]
    for i,(sid,title,a,b) in enumerate(IB.SCENES):
        start=0 if i==0 else times[a]-.15
        end=total if i+1==len(IB.SCENES) else times[IB.SCENES[i+1][2]]-.15
        scenes.append(dict(scene_id=sid,title=title,start_s=start,end_s=end,source=positive_text(IB.SOURCES[sid]),material_type='editorial_diagram' if sid!='s5' else 'official_plan_reconstruction',origin='frozen_intro_template',narration_anchor=IB.CUES[a][0]))
    chdir=OUT/'ch01';dependencies(chdir)
    image=tracked(EP/'outputs/intro-motion-v1/assets/gyosan_landuse_panel.png')
    shutil.copy2(image,chdir/'assets'/image.name)
    template=tracked(BASE/'intro-src/template.html').read_text(encoding='utf8')
    # Equivalent chart-only display units; caption text stays verbatim to the chosen script.
    display_map={text:f'약 {value}억원' for text,value in [('약 6억1천만원','6.1'),('약 6억6천만원','6.6'),('약 6억9천만원','6.9'),('약 7억4천만원','7.4'),('약 5억6천만원','5.6'),('약 5억4천만원','5.4'),('약 4억5천만원','4.5')]}
    for a,b in display_map.items(): template=template.replace(a,b)
    titles='\n'.join(f'<h2 id="title-{s["scene_id"]}" class="clip title" data-start="{s["start_s"]}" data-duration="{s["end_s"]-s["start_s"]}" data-track-index="2">{s["title"]}</h2>' for s in scenes)
    sources='\n'.join(f'<p id="src-{s["scene_id"]}" class="clip source" data-start="{s["start_s"]}" data-duration="{s["end_s"]-s["start_s"]}" data-track-index="8">{html.escape(s["source"])}</p>' for s in scenes)
    replacements={'{{TOTAL}}':str(total),'{{TITLES}}':titles,'{{SOURCES}}':sources,'{{CUES}}':captions(cues,total),
                  '{{CUE_JSON}}':json.dumps(times),'{{SCENE_JSON}}':json.dumps({s['scene_id']:[s['start_s'],s['end_s']-s['start_s']] for s in scenes})}
    for a,b in replacements.items(): template=template.replace(a,b)
    for s in scenes:
        template=template.replace('{{'+s['scene_id']+'_START}}',str(s['start_s'])).replace('{{'+s['scene_id']+'_DUR}}',str(s['end_s']-s['start_s']))
    template=template.replace('https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js','assets/gsap.min.js')
    template=template.replace('</style>',CSS_EXTRA+'.chart .val{left:0;width:110px;}</style>')
    template=template.replace('const C =','document.fonts.ready.then(()=>{\n window.__timelines=window.__timelines||{};\n const C =')
    template=template.replace('window.__timelines["main"] = tl;','window.__timelines["main"] = tl;\n });')
    if audio:
        audio_name='narration'+audio.suffix
        shutil.copy2(audio,chdir/'assets'/audio_name)
        template=template.replace('</body>',f'<audio id="narration" class="clip" src="assets/{audio_name}" data-start="0" data-duration="{total}" data-track-index="10"></audio></body>')
    (chdir/'index.html').write_text(positive_text(template),encoding='utf8')
    config(chdir,1)
    dump(chdir/'timing.json',dict(chapter=1,timing_basis=basis,total_seconds=total,last_speech_end_s=last,cues=cues,scenes=scenes))
    dump(chdir/'anchor_audit.json',dict(chapter=1,anchors=align.audit,paragraph_alignment=align.paragraph_audit,zero_second_fallback=False))
    dump(chdir/'display_mapping.json',{'scope':'chart labels only; captions verbatim','equivalent_krw_units':display_map})
    return dict(chapter=1,total_seconds=total,last_speech_end_s=last,timing_basis=basis,project='ch01',scenes=scenes)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--require-measured',action='store_true')
    parser.add_argument('--timing',help='Explicit final_timing.json from the formally delivered narration version')
    parser.add_argument('--narration-handoff',help='Formal narration handoff JSON; required with --timing')
    parser.add_argument('--chapters',help='Comma-separated chapters to rebuild; retain exact other project files')
    args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    selected=set(map(int,args.chapters.split(','))) if args.chapters else set(range(1,11))
    previous=json.loads((OUT/'render_plan.json').read_text(encoding='utf-8-sig')) if args.chapters else None
    for f in ['authorization.json','plan.md','media_contract.json','episode_preflight.json','media_assets.json']:
        tracked(DIRECTOR/f)
    media=read_json(DIRECTOR/'media_assets.json')
    media_by_id={}
    for asset in media['assets']:
        file=tracked(resolve_path(asset['path']))
        if digest(file)!=asset['sha256']:raise ValueError('Media asset lock hash mismatch: '+asset['asset_id'])
        media_by_id[asset['asset_id']]=asset
    script,chapters,lock,timing=script_and_timing(args.require_measured,args.timing,args.narration_handoff)
    facts=read_json(EP/'outputs/growth-explanation-v1/facts.json')
    csvpath=tracked(WORKSPACE/'analysis/housing_growth_2006/regional_expansion_v1/quarterly_index.csv')
    expected=next(v for k,v in facts['input_sha256'].items() if k.endswith('quarterly_index.csv'))
    if digest(csvpath)!=expected:raise ValueError('Regional data hash differs from facts.json')
    ledger=read_json(EP/'research/illustrative_results.json')
    oldscript=tracked(EP/'outputs/script-review-v1/script_v1.md')
    old=parse_script(oldscript.read_text(encoding='utf8'))
    F=module('framework',BASE/'framework.py')
    C=module('private_chapters',BASE/'chapters.py')
    IB=module('private_intro',BASE/'intro_build.py')
    image_meta=read_json(EP/'visual/private-production-v1/housing-stability-v1.json')
    housing=tracked(resolve_path(image_meta['path']))
    if digest(housing)!=image_meta['sha256'] or image_meta['mode']!='RGBA':
        raise ValueError('Housing illustration SHA/mode mismatch')
    period_check=read_json(EP/'qa/private-production-v1/regional_period_crosscheck.json')
    new=additions(F,facts,csvpath,housing,period_check)
    debt=[m['debt'] for m in ledger['cases']['기본']['paths']['매매']['monthly_ledger']]
    definitions={2:C.ch2,3:C.ch3,4:C.ch4,5:lambda:C.ch5(debt),6:C.ch6,7:C.ch7,8:C.ch8,9:C.ch9,10:C.ch10}
    results=[]
    failures=[]
    for num,ch in chapters.items():
        try:
            cues,total,last,audio,basis=cue_times(num,ch,timing,F)
            if num not in selected:
                prior_timing=json.loads((OUT/f'ch{num:02d}/timing.json').read_text(encoding='utf-8-sig'))
                if previous['status']!=basis or prior_timing['cues']!=cues or prior_timing['total_seconds']!=total or prior_timing['last_speech_end_s']!=last or digest(audio)!=digest(OUT/f'ch{num:02d}/assets/narration.wav'):raise ValueError('Cannot retain chapter with changed cues/timing/voice')
                result=next(c for c in previous['chapters'] if c['chapter']==num)
                results.append(result)
                continue
            if num==1:
                result=build_intro(ch,cues,total,last,audio,basis,old[num],IB)
            else:
                scenes=modify_scenes(num,definitions[num](),new,F)
                result=build_chapter(num,ch,cues,total,last,audio,basis,old[num],scenes,F)
            results.append(result)
        except (ValueError,KeyError) as e:
            failures.append(dict(chapter=num,error=str(e)))
    if failures:
        dump(HERE/'build_failures.json',failures)
        print(json.dumps({'status':'blocked_build_mapping','failures':failures},ensure_ascii=False))
        return 1
    mode='measured_audio_units' if timing else 'estimated_placeholder'
    edl=assembly_plan(results,media_by_id,mode)
    snapshots=[]
    for ch in results:
        for s in ch['scenes']:
            # Settle frame plus boundary pair; every message receives a distinct sample.
            dur=s['end_s']-s['start_s']
            snapshots.append(dict(chapter=ch['chapter'],scene_id=s['scene_id'],project=ch['project'],
                                 representative_s=round(s['start_s']+max(.1,dur*.7),6),
                                 before_end_s=round(s['end_s']-1/30,6),after_start_s=round(s['start_s']+1/30,6),
                                 timing_basis=mode))
    # Longest labels/captions and every T cue are additionally inspected by the browser checker.
    dump(OUT/'snapshot_times.json',{'status':mode,'samples':snapshots})
    offset=0; offset_map=[]
    for ch in results:
        offset_map.append(dict(chapter=ch['chapter'],local_start_s=0,assembly_start_s=offset,total_seconds=ch['total_seconds']))
        offset+=ch['total_seconds']
    plan={'revision':'private-production-v2','status':mode,'script_path':str(script.relative_to(EP)).replace('\\','/'),'script_sha256':digest(script),
          'locked_script_present':bool(lock),'measured_timing_present':bool(timing),'canvas':{'width':1920,'height':1080,'fps':30},
          'full_render_allowed':False,'render_authorization':'user already authorized; proceed without reconfirmation after measured validation, independent preview QA and canonical carve pass',
          'tts_external_upload_allowed_in_this_sidecar':False,'chapters':results,'estimated_total_seconds_without_brand':round(offset,6),
          'offset_map':edl['offset_map'],'assembly_edl':'assembly_edl.json','total_seconds_with_brand':edl['total_seconds'],'brand_assembly':{'status':'assets_locked_measured_cue_pending' if not timing else 'measured_cues_and_locked_brand_frames','clean_intro':media_by_id['channel_brand_intro_clean_v7'],'clean_outro':media_by_id['channel_brand_outro_clean_v7'],'existing_music':media_by_id['existing_channel_bgm'],
          'insert_intro_at':'chapter 1 hook end cue boundary; add actual intro duration to every downstream media/caption entry',
          'outro_start':'chapter 10 measured last_speech_end_s + 3s plus global offset','caption_exceptions':['clean_brand_intro','clean_brand_outro','final_3s_silent_CTA_hold']},
          'render_command_template':['hyperframes.cmd','render','--output','chapter_versioned.mp4'],
          'render_command_status':'execute immediately after formal measured handoff, source/timing validation, independent preview QA and canonical carve pass; no user reconfirmation',
          'pending':['script dual-review/locked SHA' if not lock else 'locked script content QA receipts to be verified by director','actual voice + final_timing' if not timing else 'actual listening and continuous playback','representative independent QA','measured brand global offset map and canonical voiceover carve','actual MP4 metadata/decode/frame checks after authorized render'],
          'workflow_notes':{'update_failure':'general-video Unknown skill reported by director; not rerun because external calls forbidden','skills':'installed general-video/core/animation/registry and local frozen project','catalog':'director reports 448-item words search: data-chart/mk-line-graph; existing chart geometry and channel primitives reused; no external add'},
          'image_requests':[]}
    dump(OUT/'render_plan.json',plan)
    dump(OUT/'assets_manifest.json',{'housing-stability-v1':{**image_meta,'placement_scene_id':'s10life','use_count':1,
          'role':'illustration of long-term living plans','edited_by_editor':False,
          'source_record':'visual/private-production-v1/housing-stability-v1.json'},
          'chapter_cards':{'material_type':'reused_editorial_diagram_fragments','unique_graphic_per_chapter':True,'photo_substitution':False},
          'gyosan_landuse_panel':{'source':'outputs/intro-motion-v1/assets/gyosan_landuse_panel.png','type':'official_plan_reconstruction','scene':'ch01/s5','sha256':digest(EP/'outputs/intro-motion-v1/assets/gyosan_landuse_panel.png')}})
    dump(HERE/'build_failures.json',{'status':'resolved','current_failures':[]})
    # A local review entry point, not an assembled film or render target.
    links=''.join(f'<li><a href="{c["project"]}/index.html">{c["chapter"]}. {html.escape(chapters[c["chapter"]]["title"])} · {c["total_seconds"]:.1f}초</a></li>' for c in results)
    (OUT/'index.html').write_text(f'<!doctype html><html lang="ko"><meta charset="utf-8"><title>편집 준비 프리뷰</title><body style="font-family:sans-serif;max-width:1000px;margin:50px"><h1>기존 영상 재편집 · 검증용 프로젝트</h1><p>시간 기준: {mode}. 전체 렌더·음성 청취·연속 재생 전입니다.</p><ol>{links}</ol><p>각 프로젝트는 로컬 검사 도구로 seek하여 확인합니다. 이 페이지는 장별 검토 진입점입니다.</p></body></html>',encoding='utf8')
    for p in HERE.glob('*.py'): tracked(p)
    for p in HERE.glob('*.cjs'): tracked(p)
    # Dependency installation/cache trees belong to director/tooling and are not our deliverables.
    outputs={}
    for directory,dirs,names in os.walk(OUT):
        dirs[:]=[d for d in dirs if d not in ['preview','audio-deps','ffmpeg-deps','media-bin','node_modules','.hyperframes','renders']]
        for name in names:
            p=Path(directory)/name
            if name not in ['input_manifest.json','output_manifest.json']:outputs[str(p.relative_to(OUT)).replace('\\','/')]=digest(p)
    dump(OUT/'input_manifest.json',{'inputs_sha256':INPUTS,'script_sha256':digest(script),'timing_basis':mode,'gsap_version':'3.14.2','cli_pin':'0.8.181','external_calls':0})
    dump(OUT/'output_manifest.json',outputs)
    print(json.dumps({'status':mode,'chapters':len(results),'scenes':len(snapshots),'seconds_without_brand':round(offset,2),'script_sha256':digest(script),'rendered':False},ensure_ascii=False))
    return 0


if __name__=='__main__':
    try:sys.exit(main())
    except (ValueError,KeyError,FileNotFoundError) as e:
        dump(HERE/'issue_BUILD_CONTRACT.json',{'scene_id':'all','problem':str(e),'evidence':'build input validation','proposal':'director/narration resolve contract; no fallback or full render','impact':'preview or measured build blocked','next_owner':'video_director'})
        print(json.dumps({'status':'blocked_contract','error':str(e)},ensure_ascii=False));sys.exit(1)
