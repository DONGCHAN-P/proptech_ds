"""V3-only parser adapter: 일백삼 is a numeral, not a day unit.

Original v2 checker and results remain byte-for-byte preserved.
"""
import re,difflib
import checks as base
PAT=re.compile(base.PAT.pattern.replace('|일)', '|일(?![0-9영공일이삼사오육칠팔구십백천만억조]))'))

def numbers(text):
    text=base.decimalize(text).replace('시월','십월').replace('유월','육월');rows=[]
    for m in PAT.finditer(text):
        raw=m[0];unit=re.sub(r'\s','',m[2])
        if raw.strip()=='조건' or (unit=='원' and text[m.end():m.end()+1]=='화'):continue
        unit={'퍼센트포인트':'percentage_point','%포인트':'percentage_point','%p':'percentage_point','퍼센트':'percent','프로':'percent','%':'percent','제곱미터':'m2','㎡':'m2','원':'KRW'}.get(unit,unit)
        rows.append({'raw':raw,'value':format(base.value(m[1]).normalize(),'f'),'unit':unit})
    return rows

def compare(reference,transcript):
    a,b=numbers(reference),numbers(transcript)
    aa=[(v['value'],v['unit']) for v in a];bb=[(v['value'],v['unit']) for v in b]
    diffs=[{'operation':op,'expected':a[i:j],'recognized':b[k:l]} for op,i,j,k,l in difflib.SequenceMatcher(a=aa,b=bb,autojunk=False).get_opcodes() if op!='equal']
    na,nb=base.norm(reference),base.norm(transcript)
    terms=[{'term':t,'expected_count':na.count(t),'recognized_count':nb.count(t)} for t in base.TERMS if na.count(t)!=nb.count(t)]
    return {'reference_numbers':a,'recognized_numbers':b,'numeric_differences':diffs,'coreterm_differences':terms,'text_similarity':round(difflib.SequenceMatcher(a=na,b=nb,autojunk=False).ratio(),4),'actual_pronunciation_verified':False}
