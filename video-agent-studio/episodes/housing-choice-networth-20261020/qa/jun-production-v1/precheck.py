import hashlib,json,re,sys
from pathlib import Path
from decimal import Decimal
from datetime import datetime,timezone
sys.dont_write_bytecode=True
Q=Path(__file__).resolve().parent; E=Q.parent.parent; R=E.parents[2]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pin(p):return dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size)
def dump(n,d):(Q/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
D=dict(zip('영일이삼사오육칠팔구',range(10)))
def integer(t):
    t=t.replace('두','이').replace('서른','삼십'); total=section=number=0
    for x in re.findall(r'\d+|[영일이삼사오육칠팔구십백천만억조]',t):
        if x in D:number=D[x]
        elif x in '십백천':section+=(number or 1)*{'십':10,'백':100,'천':1000}[x];number=0
        elif x in '만억조':total+=(section+number or 1)*{'만':10000,'억':100000000,'조':1000000000000}[x];section=number=0
        else:number=int(x)
    return total+section+number
def amount(t):
    t=t.replace(' ','').replace(',','')
    if '점' in t:
        a,b=t.split('점',1); b=''.join(str(D[x]) if x in D else x for x in b)
        return Decimal(str(integer(a))+'.'+re.match(r'\d+',b)[0])
    if re.search(r'\d+\.\d+',t):return Decimal(re.search(r'\d+\.\d+',t)[0])
    return Decimal(integer(t))
def main():
    Q.mkdir(exist_ok=True)
    script=E/'outputs/script-final-v6/script_v6.md'; text=script.read_text(encoding='utf-8-sig')
    rawp=E/'narration/jun-replacement-v1/narration_manifest.json'; phop=E/'narration/jun-replacement-v1/pronunciation_proposal.json'
    raw=read(rawp);pho=read(phop); oldp=E/'narration/free-tts-v1/caption-v7/final_timing.json';old=read(oldp)
    prep=read(E/'narration/free-tts-v1/prepare-v6/prepared.json'); prepflat=[p for c in prep['chapters'] for p in c['paragraphs']]
    checks=[]
    def ck(name,ok,**e):checks.append(dict(check=name,pass_=bool(ok),**e))
    ck('approved_script_SHA',sha(script)=='0368c9e08b8a2447ed429d9e78ab9a8238b2d823c27467362174600876a797b7')
    ck('approved_phonetic_SHA',sha(phop)=='ea636bf3e07e4fa73fd7dbb25f04e89c38aec191cad02abf3de309af6fbd72a7')
    parsed=[]
    for chap,body in re.findall(r'^## (\d+)\.[^\n]*\n(.*?)(?=^## |\Z)',text,re.M|re.S):
        parsed.extend((int(chap),p.strip()) for p in re.split(r'\n\s*\n',body.strip()) if p.strip())
    ck('independent_54_body_parse',len(parsed)==54 and len(raw['paragraphs'])==54 and len(pho['paragraphs'])==54)
    substitutions=[]; cues=[]; semantic={}
    for n,(a,b,c,(chapter,body)) in enumerate(zip(raw['paragraphs'],pho['paragraphs'],prepflat,parsed)):
        pid=a['paragraph_id']; original=a['text']; spoken=b['proposed_spoken_text']
        ck(pid+' body',original==body and a['chapter']==chapter and text[a['source_start']:a['source_end']]==body)
        ck(pid+' raw_hash',hashlib.sha256(original.encode()).hexdigest()==a['sha256']==b['source_text_sha256'])
        ck(pid+' spoken_hash',hashlib.sha256(spoken.encode()).hexdigest()==b['proposed_spoken_text_sha256'])
        ck(pid+' prior_spoken_conservation',c['paragraph_id']==pid and c['spoken_text']==spoken)
        maps=c['display_mapping']; ck(pid+' full_mapping', ''.join(x['original'] for x in maps)==original and ''.join(x['spoken'] for x in maps)==spoken)
        for x in b['substitutions']:
            ck(pid+' substitution_slice',original[x['source_start']:x['source_end']]==x['original'] and spoken[x['spoken_start']:x['spoken_end']]==x['spoken'])
            if re.search(r'\d',x['original']):
                v1,v2=amount(x['original']),amount(x['spoken']);ok=v1==v2
            else:
                v1=v2=None;ok=(x['original'],x['spoken']) in [('S&P500','에스 앤 피 오백'),('S&P','에스 앤 피'),('S&P','에스 앤드 피'),('ETF','이 티 에프')]
            ck(pid+' semantic_substitution',ok,original=x['original'],spoken=x['spoken'])
            row=dict(paragraph_id=pid,original=x['original'],spoken=x['spoken'],source_value=str(v1),spoken_value=str(v2),equal=ok)
            substitutions.append(row);semantic[x['original']]=row
        ch=old['chapters'][chapter-1];pc=[q for q in ch['cues'] if q['paragraph']==a['paragraph']]
        ck(pid+' cue_body_conservation',re.sub(r'\s','', ''.join(q['text'] for q in pc))==re.sub(r'\s','',body))
        ck(pid+' cue_spoken_conservation',re.sub(r'\s','', ''.join(q['spoken_text'] for q in pc))==re.sub(r'\s','',spoken))
        for q in pc:
            ck(q['id']+' display_lines',re.sub(r'\s','', ''.join(q['display_lines']))==re.sub(r'\s','',q['text']) and len(q['display_lines'])<=2)
            cues.append(dict(id=q['id'],paragraph_id=pid,text=q['text'],spoken_text=q['spoken_text'],display_lines=q['display_lines'],source_start=q['source_start'],source_end=q['source_end']))
    ck('206_unique_cues',len(cues)==206 and len({q['id'] for q in cues})==206)
    numericp=E/'qa/private-production-v1/numeric_audit.json';numeric=read(numericp);reuse=[]
    for rel,v in numeric['input_manifest'].items():
        p=R/rel;expected=v if isinstance(v,str) else v.get('sha256')
        reuse.append(dict(path=str(p),expected=expected,actual=sha(p),matches=sha(p)==expected))
    ck('numeric_audit_inputs_unchanged',all(x['matches'] for x in reuse))
    assets=read(E/'outputs/launch-proposal-v2/assets.json');thumbs=[]
    from PIL import Image
    for a in assets['assets']:
        p=E/'outputs/launch-proposal-v2'/a['upload_size'];im=Image.open(p)
        ck(a['asset_id']+' hash_and_size',sha(p)==a['upload_size_receipt']['sha256'] and im.size==(1280,720))
        dest=Q/(a['asset_id']+'_mobile_320x180.png');im.resize((320,180),Image.Resampling.LANCZOS).save(dest)
        thumbs.append(dict(id=a['asset_id'],file=pin(p),mobile=pin(dest)))
    dump('cue_text_lock.json',dict(script=pin(script),phonetics=pin(phop),prior_timing=pin(oldp),cues=cues))
    dump('text_precheck.json',dict(checked_at=datetime.now(timezone.utc).isoformat(),status='pass' if all(c['pass_'] for c in checks) else 'review_required',checks_count=len(checks),failures=[c for c in checks if not c['pass_']],paragraph_count=len(parsed),cue_count=len(cues),substitution_count=len(substitutions),unique_substitutions=list(semantic.values()),checks=checks,numeric_audit=pin(numericp),unchanged_model_inputs=reuse,financial_model_recalculated=False,script=pin(script),phonetics=pin(phop),raw_manifest=pin(rawp),thumbnails=thumbs,actual_listening=False,continuous_playback=False))
    print(json.dumps(dict(status='pass' if all(c['pass_'] for c in checks) else 'review_required',checks=len(checks),failures=[c for c in checks if not c['pass_']],substitution_count=len(substitutions),unique_substitutions=len(semantic)),ensure_ascii=False))
if __name__=='__main__':main()
