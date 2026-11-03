"""Additional primary-source conditions and an independently checked five-year reset case."""
import hashlib
import html
import json
import re
from decimal import Decimal, getcontext
from html.parser import HTMLParser
from pathlib import Path

HERE=Path(__file__).resolve().parent
EVIDENCE=HERE/'evidence/director-newborn-v1'
class Text(HTMLParser):
    def __init__(self):super().__init__(convert_charrefs=True);self.parts=[];self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in ['script','style']:self.skip+=1
    def handle_endtag(self,tag):
        if tag in ['script','style']:self.skip=max(0,self.skip-1)
    def handle_data(self,data):
        if not self.skip:self.parts.append(data)

sources=[]
for name in ['KB','NHUF']:
    p=EVIDENCE/(name+'.html');parser=Text();parser.feed(p.read_text(encoding='utf-8',errors='replace'))
    text=re.sub(r'\s+',' ',' '.join(parser.parts))
    fragments=[]
    for term in ['입양아','0.75','특례금리 적용 종료','특례금리 종료 후','8.5천만원']:
        i=text.find(term)
        if i>=0:fragments.append({'term':term,'context':text[max(0,i-90):i+480]})
    sources.append({'source_id':name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'fragments':fragments})
kb=next(r for r in sources if r['source_id']=='KB')
assert any(r['term']=='0.75' for r in kb['fragments'])

getcontext().prec=40
D=Decimal
principal=D(390740000);r=D('.029')/12
initial=principal*r/(1-(1+r)**-360)
balance=principal
for _ in range(60):balance=balance*(1+r)-initial
closed=principal*(1+r)**60-initial*((1+r)**60-1)/r
assert abs(balance-closed)<D('.000001')
rate2=D('.0365')/12
later=balance*rate2/(1-(1+rate2)**-300)
pv=sum(later/(1+rate2)**m for m in range(1,301))
assert abs(pv-balance)<D('.000001')
final=balance
for _ in range(300):final=final*(1+rate2)-later
assert abs(final)<D('.000001')
assert abs(initial-D('1626377.024396469120911861925820032915688'))<D('.000001')

packet={'status':'director_primary_source_addendum_and_illustration_pending_independent_script_review',
    'as_of_kst':'2026-10-26','sources':sources,
    'primary_urls':{
      'KB':'https://obank.kbstar.com/quics?cc=b032425:b033525&page=C020709&prcode=LN40001049',
      'NHUF':'https://nhuf.molit.go.kr/FP/FP05/FP0503/FP05030801.jsp'},
    'new_claims':[
      {'claim_id':'N01A','statement':'입양가구의 기본요건은 대출접수일 현재 입양아가 만2세 미만이라는 나이 조건을 포함합니다.',
       'source':'KB current product features and application eligibility; fresh local cache plus web primary page opened.'},
      {'claim_id':'N05A','statement':'기본 특례5년 종료 후 금리는 신규취급시 부부합산소득 구간과 대출접수일 기준 산식으로 정합니다.',
       'exact_conditions':'신규시 합산소득8500만원 이하: 특례금리에 [접수일 기준 생애최초 신혼 내집마련디딤돌 최저기본금리−신생아 최저특례금리]를 가산. KB 현행 표의2026.08.11기준 가산폭0.75%p. 기본 특례기간5년; 추가출산 연장·금리우대·자산초과가산·중도상환은 아래 예시에서0.',
       'source':'KB basic interest section A1, current NHUF reset formula. No future market-rate estimate.'}],
    'case':{'case_id':'B_newborn_6eok_reset_after60_current_schedule',
       'base_case':'B_newborn_P600000000_C0','principal_krw':str(principal),
       'initial_annual_rate':'0.029','initial_months':60,'original_months':360,
       'initial_monthly_krw':str(initial),'balance_after60_krw':str(balance),
       'current_schedule_reset_spread_pp':'0.75','current_schedule_reset_rate':'0.0365',
       'remaining_months':300,'reset_monthly_krw':str(later),'monthly_increase_krw':str(later-initial),
       'meaning':'A의 최초원금·신규360개월 금리 비교와 별개로, B의60회 상환 후 잔액·남은300개월을 계산했습니다.',
       'scope':'Current application-rate schedule illustration, base rates before preferences, no additional birth/prepayment; future policy or personal execution changes require corresponding input update.'},
    'verification':{'independent_discounted300_payments_match_balance':True,'recursive60_and_closed_form_match':True,
                    'recursive300_final_balance_zero':True,'initial_payment_matches_preverified_ledger':True}}
out=HERE/'newborn_reset_addendum_v1.json'
assert not out.exists(),'Retain the old addendum; version corrections.'
out.write_text(json.dumps(packet,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'case':packet['case'],'source_fragment_counts':[len(r['fragments']) for r in sources]},ensure_ascii=False))
