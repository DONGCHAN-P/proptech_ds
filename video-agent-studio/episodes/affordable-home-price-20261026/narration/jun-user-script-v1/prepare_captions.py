"""Prepare meaning-based display cues without inventing audio timestamps."""
from pathlib import Path
import json
import re
import hashlib

OWN=Path(__file__).resolve().parent
manifest=json.loads((OWN/'narration_manifest.json').read_text(encoding='utf-8'))
money=re.compile(r'\d[\d,]*(?:\.\d+)?(?:\s*[억천백십만](?:\s*\d[\d,]*(?:\.\d+)?)?)+\s*(?:원)?|\d+(?:\.\d+)?\s*(?:퍼센트|제곱미터|개월|년)|(?:LTV|DSR)\s*\d+퍼센트')

def protected(text):
    return [(m.start(),m.end()) for m in money.finditer(text)]

def boundary_ok(pos,spans):
    return all(not a<pos<b for a,b in spans)

def split_span(text,start,end,maximum=58):
    if end-start<=maximum:
        return [(start,end)]
    sub=text[start:end]
    spans=protected(text)
    # Commas and complete Korean clauses are preferred over arbitrary words.
    candidates=[]
    for m in re.finditer(r',\s+|(?:고요|지만|하면|때문에|때|뒤에|보다|따라|반면에|보면|빼고|확인하고)\s+',sub):
        q=start+m.end()
        if 12<=q-start<=maximum and end-q>=9 and boundary_ok(q,spans):
            candidates.append(q)
    if not candidates:
        candidates=[start+m.end() for m in re.finditer(r'\s+',sub) if 18<=m.end()<=maximum and end-start-m.end()>=9 and boundary_ok(start+m.end(),spans)]
    assert candidates, f'Manual semantic split required: {sub}'
    goal=min(46,(end-start)/2) if end-start<=100 else 46
    cut=min(candidates,key=lambda x:abs(x-start-goal))
    return split_span(text,start,cut,maximum)+split_span(text,cut,end,maximum)

def lines(text):
    if len(text)<=31:
        return [text]
    spans=protected(text)
    candidates=[m.end() for m in re.finditer(r'\s+',text) if boundary_ok(m.end(),spans)]
    assert candidates, f'Manual line break required: {text}'
    def penalty(q):
        left,right=text[:q].strip(),text[q:].strip()
        return max(len(left),len(right))+abs(len(left)-len(right))*.15+(12 if max(len(left),len(right))>33 else 0)
    q=min(candidates,key=penalty)
    result=[text[:q].strip(),text[q:].strip()]
    assert all(result)
    return result

cues=[]
for p in manifest['paragraphs']:
    text=p['text']
    # Sentence punctuation only when followed by whitespace/end; decimal dots stay intact.
    ends=[m.end() for m in re.finditer(r'[.!?](?=\s|$)',text)]
    if not ends or ends[-1]!=len(text):ends.append(len(text))
    cursor=0
    for end in ends:
        if not text[cursor:end].strip():
            cursor=end
            continue
        for a,b in split_span(text,cursor,end):
            while a<b and text[a].isspace():a+=1
            while b>a and text[b-1].isspace():b-=1
            value=text[a:b]
            if not value:continue
            display=lines(value)
            assert re.sub(r'\s+','',''.join(display))==re.sub(r'\s+','',value)
            if len(display)==2:
                split_at=value.index(display[1])
                assert boundary_ok(split_at,protected(value)),(value,display)
            cues.append({'cue_id':p['paragraph_id']+f'Q{sum(x["paragraph_id"]==p["paragraph_id"] for x in cues)+1:02}','scene_id':p['scene_id'],'chapter':p['chapter'],'paragraph_id':p['paragraph_id'],'source_start':a,'source_end':b,'text':value,'display_lines':display,'start_s':None,'end_s':None,'timing_basis':'pending_actual_Jun_character_alignment'})
        cursor=end
    restored=''.join(c['text'] for c in cues if c['paragraph_id']==p['paragraph_id'])
    assert re.sub(r'\s+','',restored)==re.sub(r'\s+','',text),p['paragraph_id']
overrides={
    'P008Q04':{'display_lines':['내 통장에 있는 돈하고','저 가격이 바로 연결되지는 않거든요.']},
    'P009Q02':{'display_lines':['대출을 더 받았다고','그만큼 내 재산이 생기는 것도 아닙니다.']},
    'P038Q01':{'display_lines':['현금 1억 원을 더 모으니까','볼 수 있는 집값이 많이 올라갔죠.']},
    'P039Q01':{'text':'그리고 현금 2억 원이 있어도 내 소득으로 대출이 2억 원까지만 가능하다면,','display_lines':['그리고 현금 2억 원이 있어도','내 소득으로 대출이 2억 원까지만 가능하다면,']},
    'P039Q02':{'text':'같은 준비금을 남겼을 때 집값 예산은 3억 7천만 원입니다.','display_lines':['같은 준비금을 남겼을 때 집값 예산은','3억 7천만 원입니다.']},
}
by_id={p['paragraph_id']:p['text'] for p in manifest['paragraphs']}
for c in cues:
    if c['cue_id'] in overrides:
        fix=overrides[c['cue_id']]
        c.update(fix)
        if 'text' in fix:
            c['source_start']=by_id[c['paragraph_id']].index(c['text'])
            c['source_end']=c['source_start']+len(c['text'])
        c['meaning_boundary_basis']='independent_QA_JUN-CAP-003'
    assert by_id[c['paragraph_id']][c['source_start']:c['source_end']]==c['text']
    assert re.sub(r'\s+','',''.join(c['display_lines']))==re.sub(r'\s+','',c['text'])
    if len(c['display_lines'])==2:
        assert boundary_ok(c['text'].index(c['display_lines'][1]),protected(c['text']))
for pid,text in by_id.items():
    restored=''.join(c['text'] for c in cues if c['paragraph_id']==pid)
    assert re.sub(r'\s+','',restored)==re.sub(r'\s+','',text),pid
assert len({c['cue_id'] for c in cues})==len(cues)==156
result={'status':'semantic_display_prepared_audio_timing_unlocked','source_doc_sha256':manifest['source_doc_sha256'],'source_manifest_sha256':hashlib.sha256((OWN/'narration_manifest.json').read_bytes()).hexdigest(),'paragraphs':48,'scenes':31,'cue_count':len(cues),'max_line_characters':max(len(line) for c in cues for line in c['display_lines']),'audio_timing_measured':False,'cues':cues,'scope':'Text-only original coverage, protected numeric boundaries and proposed lines verified. Actual rendered width/readability and sound sync remain to check.'}
result['qa_meaning_overrides']=list(overrides)
(OWN/'caption_plan.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:result[k] for k in ['status','cue_count','max_line_characters','audio_timing_measured']},ensure_ascii=False))
