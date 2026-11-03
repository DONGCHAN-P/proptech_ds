"""Known-input opening context and human-readable source footer. No render runner."""
from graphics import Drawing

# Opening context is separate from the unchanged writer beats. No result is
# pre-revealed; these are known inputs or the subject/definition being spoken.
OPENINGS={
 'R001':['보유자금','2억5천만원','집값의 범위'],
 'R002':['가구의 현금','매달 쓸 예산','대출 조건'],
 'R003':['보유현금 2억5천만원','예비자금 분리','구입자금'],
 'R004':['취득세','중개보수','등기·기타 비용'],
 'R005':['구입자금 2억2천만원','거래비용 1,074만원','집값 6억원'],
 'R006':['6억원 주택','담보평가액 = 매매가','LTV 비율 적용'],
 'R007':['인정소득','연간 상환예산','기존 대출 원리금'],
 'R008':['실제 납부금리','스트레스 가산금리','심사에 쓰는 금리'],
 'R009':['집값 → 담보 한도','소득 → 상환 한도','여러 한도를 비교'],
 'R010':['공제 전 담보 한도','4억2천만원','서울 담보대출 공제'],
 'R011':['6억원 주택','보증 승인으로 공제 보완','매달 갚는 금액'],
 'R029':['보유현금 2억5천만원','인정소득 연1억원','약정금리 4% · 30년'],
 'R030':['매달 예산 300만원','소유비 30만원','남길 저축 100만원'],
 'R031':['매달 예산 300만원','대출 상환액','남길 저축'],
 'R032':['A의 같은 최초 대출원금','약정금리 4% / 6%','각각 360개월'],
 'R033':['현금과 은행 조건','매달의 상환 목표','두 기준의 집값'],
 'R012':['주택가격','6억원 → 9억원','취득세율 구간'],
 'R013':['주택가격','구간별 중개보수','총 거래비용'],
 'R014':['생애최초 주택 구입','취득세 감면 조건','감면 한도 비교'],
 'R015':['A · 생애최초','9억원 주택','필요대출과 은행 한도'],
 'R016':['A · 생애최초','12억원 주택','필요대출과 은행 한도'],
 'R017':['주택가격 구간','총 대출금액 상한','가격별 상한 비교'],
 'R018':['A 가구의 조건','B 가구의 조건','정책대출 검토'],
 'R019':['B · 6억원 주택','디딤돌대출','필요대출과 상품상한'],
 'R020':['B · 6억원 주택','보금자리론 자체 기준','필요대출과 상품상한'],
 'R021':['B의 같은 필요대출','디딤돌 · 보금자리론','신생아 특례'],
 'R022':['대출 실행일','전입 기한','실거주 기간'],
 'R023':['B 출산가구','접수일 기준 출산 시점','소득 · 순자산 조건'],
 'R024':['B · 현재 주택 6억원','신생아 특례 자격','필요한 대출금액'],
 'R025':['B · 신생아 특례','초기 기본금리','처음 5년의 상환'],
 'R026':['B · 초기 기본금리 2.9%','60회 상환','이후 금리와 잔액'],
 'R027':['B · 9억원 주택','신생아 특례','상품 대출상한'],
 'R028':['주택가격 9억원','대출상한 4억원','남은 집값과 비용'],
 'R034':['자기자금','대출 가능 범위','월 상환 목표'],
}


def attach_opening_context(g,sid,first):
    if first<1.5:return
    d=Drawing();body=''
    for i,label in enumerate(OPENINGS[sid]):
        x=55+i*555
        body+=d.label('opening-node-'+str(i),label,x,150,525,32,'var(--ink)')
        if i<2:body+=d.label('opening-arrow-'+str(i),'→',x+465,260,60,48,'var(--muted)')
    # Neutral input paths, never a finished chart or a conclusion.
    for i in range(3):
        body+=f'<div id="opening-rule-{i}" data-object="shape" style="position:absolute;left:{55+i*555}px;top:330px;width:440px;height:5px;background:#a8b5b6"></div>'
    g['html']='<div id="opening-context" class="opening-context">'+body+'</div>'+g['html']
    g['objects']=d.objects+g['objects']
    g['opening_context']={'id':'opening-context','start_s':0,'end_s':max(0,first-1/30),'basis':'fixed known inputs / spoken topic; separate from writer anchors','labels':OPENINGS[sid]}
    g['source_recipe']['opening_context']=g['opening_context']


def source_footer(sid):
    if sid in ['R004','R012','R013','R014']:
        return '자료: 서울특별시 · 국가법령정보센터 | 기준 2026.10.26 · 사례 계산'
    if sid in ['R025','R026']:
        return '자료: 주택도시기금 금리표 2026.10.19 | 사례 계산 · 우대금리 0'
    if sid in ['R019','R023','R024','R027','R028']:
        return '자료: 주택도시기금 | 기준 2026.10.26 · 사례 계산'
    if sid=='R020':return '자료: 한국주택금융공사 | 기준 2026.10.26 · 사례 계산'
    if sid in ['R018','R021','R022']:
        return '자료: 주택도시기금 · 한국주택금융공사 | 기준 2026.10.26 · 사례 계산'
    if sid in ['R006','R007','R008','R009','R010','R017']:
        return '자료: 금융위원회 · 한국주택금융공사 | 기준 2026.10.26 · 사례 계산'
    return '자료: 공개 제도 기준 · 사례 계산 | 기준 2026.10.26'

