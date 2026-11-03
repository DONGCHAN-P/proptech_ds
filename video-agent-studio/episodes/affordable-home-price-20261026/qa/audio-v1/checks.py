"""Text evidence only: KRW/units/acronyms, never a listening verdict."""
import difflib, re
from decimal import Decimal

DIGITS=dict(zip('영일이삼사오육칠팔구',range(10)));DIGITS['공']=0
SMALL={'십':10,'백':100,'천':1000};LARGE={'만':10000,'억':100000000,'조':1000000000000}
K=r'0-9영공일이삼사오육칠팔구십백천만억조'
PAT=re.compile(r'(?<![가-힣0-9])([0-9영공일이삼사오육칠팔구십백천]['+K+r'., \t]*?)\s*(퍼센트\s*포인트|%\s*포인트|%p|퍼센트|프로|%|제곱미터|㎡|개월|회|세|원|년|월|일)')
ALIASES={'디에스알':'dsr','디에스아르':'dsr','엘티브이':'ltv','엘티비':'ltv','디티아이':'dti'}
TERMS=['dsr','ltv','dti','원리금균등','디딤돌','보금자리론','신생아특례','방공제','보증']
def value(text):
    total=section=number=Decimal(0)
    for t in re.findall(r'\d+(?:\.\d+)?|[영공일이삼사오육칠팔구십백천만억조]',text.replace(',','')):
        if t in DIGITS:number=Decimal(DIGITS[t])
        elif t in SMALL:section+=(number or 1)*SMALL[t];number=Decimal(0)
        elif t in LARGE:total+=(section+number or 1)*LARGE[t];section=number=Decimal(0)
        else:number=Decimal(t)
    return total+section+number
def decimalize(text):
    def repl(m):
        fraction=''.join(str(DIGITS.get(c,c)) for c in re.sub(r'\s','',m[2]))
        return str(value(m[1]))+'.'+fraction
    return re.sub(r'(?<![가-힣0-9])([0-9영공일이삼사오육칠팔구십백천]['+K+r', \t]*?)\s*(?:소수점|쩜|점)\s*([영공일이삼사오육칠팔구0-9]+)',repl,text)
def numbers(text):
    text=decimalize(text).replace('시월','십월').replace('유월','육월');rows=[]
    for m in PAT.finditer(text):
        raw=m[0];unit=re.sub(r'\s','',m[2])
        if raw.strip()=='조건' or (unit=='원' and text[m.end():m.end()+1]=='화'):continue
        unit={'퍼센트포인트':'percentage_point','%포인트':'percentage_point','%p':'percentage_point','퍼센트':'percent','프로':'percent','%':'percent','제곱미터':'m2','㎡':'m2','원':'KRW'}.get(unit,unit)
        rows.append({'raw':raw,'value':format(value(m[1]).normalize(),'f'),'unit':unit})
    return rows
def norm(text):
    text=decimalize(text).lower()
    for a,b in ALIASES.items():text=re.sub(r'\s*'.join(a),b,text)
    return re.sub(r'[^0-9a-z가-힣]','',text)
def compare(reference,transcript):
    a,b=numbers(reference),numbers(transcript);aa=[(x['value'],x['unit']) for x in a];bb=[(x['value'],x['unit']) for x in b]
    differences=[{'operation':op,'expected':a[i:j],'recognized':b[k:l]} for op,i,j,k,l in difflib.SequenceMatcher(a=aa,b=bb,autojunk=False).get_opcodes() if op!='equal']
    na,nb=norm(reference),norm(transcript)
    terms=[{'term':t,'expected_count':na.count(t),'recognized_count':nb.count(t)} for t in TERMS if na.count(t)!=nb.count(t)]
    return {'reference_numbers':a,'recognized_numbers':b,'numeric_differences':differences,'coreterm_differences':terms,'text_similarity':round(difflib.SequenceMatcher(a=na,b=nb,autojunk=False).ratio(),4),'actual_pronunciation_verified':False}
