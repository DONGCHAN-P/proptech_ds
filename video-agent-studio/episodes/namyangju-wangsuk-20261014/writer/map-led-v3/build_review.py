import hashlib
import json
from pathlib import Path
import re
import shutil

OUT=Path(__file__).resolve().parent
EP=OUT.parents[1]
SCRIPT=OUT/'script_v3.md'

# 수동으로 고른 의미 경계다. 숫자·금액·지구+블록·노선명 안에서는 자르지 않는다.
CUTS={
'M001':[
'왕숙에서 집을 고른다면,','이번에는 이 지도에 그려진 도시가,',
'왕숙1은 진접과 진건, 퇴계원 일대에 걸친 큰 지구이고,',
'같은 왕숙이라도','앞으로 단지를 볼 때는',
'집이 들어설 곳만 보지 말고,','일할 곳, 전철을 탈 곳, 장을 볼 곳,',
'입주할 때 열리는 시설인지, 몇 년을 더 기다려야 하는지에 따라',
'이 순서로 지도를 읽은 뒤,','주변에서 이미 거래되는 아파트와 가격을 비교하고,',
],
'M002':[
'주거만 늘어나는 곳에 비해,','일터와 철도를 함께 연결하려는 자리가 있다는 것이',
'주변 블록에서 그 일터로 출근할 수 있다면,',
'왕숙 도시첨단산업단지는 약 120만 제곱미터 규모이고,',
'우리금융, 카카오, 신한은',
'우리금융 AI 디지털 유니버스는 건축허가를 받았고,',
'남측 A24와 B17의 입주예정은 2028년 12월이어서,',
'이곳의 장점은','그 사업장에 실제 출근할 가구라면',
'계속 서울로 출근한다면,','다음에 볼 철도가 자신의 목적지로 어떻게 이어지는지가',
],
'M003':[
'남양주시는 GTX-B와 9호선, 경춘선이',
'서로 다른 방향의 철도를 함께 선택할 수 있다는 점이',
'경의중앙선의 신설역과 9호선 연장 환승이',
'같은 왕숙2라도 이 교통 중심으로 이어지는 방향이 다르므로,',
'9호선 연장인 강동하남남양주선은',
'왕숙1 A24와 B17은 2028년 12월,','왕숙2 A1은 2029년 2월,',
'미래 환승의 장점을 선택하는 대신,',
'그때 비교할 기존 교통은 별내역의 8호선과 경춘선,',
'내 단지에서 어느 기존 역으로 가는지,',
'미래 노선이 개통한 뒤의 길과 입주 첫해의 길,',
'이 두 경로가 모두 가능한 가구라면',
],
'M004':[
'그 기다림을 감수할 만큼',
'전용 84제곱미터급 표시가격은',
'왕숙1 B17이 약 6억 4천만 원,',
'왕숙2 A1이 약 6억 9천만 원,',
'왕숙이라는 이름 하나로 가격을 묶기보다,',
'다만 46형이나 55형의 가격을 주변 84형과 비교해',
'면적을 줄여 예산을 맞추는 선택과,',
'지금 읽은 84형 금액은 기준층 기본가격이고,',
'새 공고를 검토할 때는',
],
'M005':[
'이제 단지에서 아이를 보내고,',
'왕숙1 북측 A2는 서쪽과 남쪽의 학교 계획,',
'남측 A24는 서쪽의 학교·공원과 연결되고,',
'역을 중심으로 보는 자리와',
'왕숙2에서는 A1 동쪽에',
'A3은 남쪽의 공공복합 기능과 주상복합,',
'아이의 학교 동선을 먼저 볼 가구와,',
'복합 기능이 갖춰진 생활공간을 원하는 가구가',
'왕숙1 북측 A1과 A2 공고의 왕숙1초는',
'반면 남측 A24와 B17은 2028년 12월 입주예정이고,',
'배정과 실제 개교는 별도로 확인해야 하지만,',
'이 달력 차이 자체는 어느 가구가',
'상업과 공원도',
'왕숙의 생활 입지를 고른다면 역 표시 하나보다,',
'이 선이 가족의 하루에 무리가 없는지,',
'첫 입주 시점에 실제 이용할 수 있는지를 맞추면',
],
'M006':[
'이제 주변에 언제 얼마나 많은 집이 들어오는지를',
'이 큰 숫자는 도시 전체의 계획규모이지',
'지금 확인한 여섯 블록을 달력에 올리면,',
'왕숙1 A1과 A2는 2028년 8월,',
'2028년 입주예정 블록을 보는 가구는',
'입주가 모이면 상권을 이용할 사람이 늘 수 있고,',
'같은 때 집을 내놓거나 세입자를 구한다면',
'여기까지 지도를 읽으면',
'왕숙은 한 번에 완성되는 상품이라기보다,',
'주택과 학교의 일정이 먼저 잡히고',
'공간 배치의 장점은 분명히 볼 수 있지만',
],
'M007':[
'그럼 왕숙의 84형은 주변 대안과 비교하면',
'전용면적과 층 조건을 비슷하게 맞추고,',
'2026년 7월부터 9월 계약 중',
'다산롯데캐슬은 약 11억 원,',
'높은 가격의 기존 생활권 대신,',
'왕숙2보다 낮은 예산의 84제곱미터급',
'왕숙1 B17은 기본가격 약 6억 4천만 원이니',
'같은 6억대에서 새집과 미래 환승 입지를 기다릴지,',
'다만 B17에는 확장과 선택비용을 더해야 하고,',
'다산롯데캐슬은 2017년, 별내푸르지오는 2015년,',
'연식과 입지, 단지의 상품, 실제 역으로 가는 길이 서로 다르고,',
'이 비교가 유용한 지점은',
'지금 이사를 해야 하고 이미 운영되는 시설을 쓰고 싶다면',
'반대로 새집을 원하고 입주까지 기다릴 수 있다면,',
'왕숙의 가격에 기다리는 시간과',
'더 높은 가격의 대안을 피하면서 새집을 선택할 수 있는지,',
],
'M008':[
'계획도에서 중심 교통과 생활 기능, 넓은 주택형을 함께 본',
'입지 대장 후보는',
'왜 이 둘을 먼저 보는지,',
'먼저 예정 왕숙역 방향의',
'A24는 전용 55제곱미터급 신혼희망타운이고,',
'작은 집으로 예산을 맞추면서',
'교육·녹지와 미래 교통 중심을 함께 보려는 신혼가구가',
'가족에게 84제곱미터급 공간이 필요하다면,',
'약 6억 4천만 원의 표시가격을 가진 이 블록을',
'다만 동측에 방음벽 설치 계획이 있어',
'두 블록의 입주예정은 2028년 12월이고,',
'전용 46형과 55형 신혼희망타운이고,',
'신혼희망타운 자격과 자금 조건이 맞고,',
'큰 면적보다 초기 예산과 이사 시점이 중요한 가구라면',
'학교와 공원 계획이 여러 방향에 놓여 있어',
'다만 남측 예정 왕숙역의 자리와 같은 교통 입지는 아니며,',
'이 지구 서쪽에 있고,',
'앞서 본 59형과 84형, 2029년 2월 입주예정을 함께 놓으면',
'학교의 3월 목표와 한 달 차이가 있으므로,',
'A3은 A1보다 동쪽으로 들어와,',
'남쪽에는 공공복합 기능과 주상복합,',
'학교 배치와 빠른 입주를 먼저 보던 A1과 달리,',
'대신 84형 기준층 가격은 더 높고',
'그 배치가 내 생활에 더 유리한지 확인한 뒤에',
'이 기준에서는 왕숙1 B17을',
'예정 환승권역과 84형 가격을 함께 보는 입지 대장 후보로,',
'왕숙2 A3을 미래 환승 방향과 복합 기능을 함께 보는',
'B17은 교통 완성 전의 출근과 동측 환경,',
'왕숙2 A1은 학교 배치와 더 이른 입주,',
'작은 면적과 초기 예산이 우선인 신혼가구는 왕숙1 A2,',
'같은 작은 면적이라도 예정 교통 중심과 학교·공원 배치를 함께 보면',
'앞으로 철도와 중심시설이 실제로 준비되지 않거나,',
'좋은 계획 입지가 내 생활에도 좋은 집이 되려면,',
],
'M009':[
'좋은 자리에 계획된 시설이 내 입주 시점에도 쓸 수 있는지,',
'기업 이름이 더해졌는지보다 실제 운영 단계가 바뀌었는지,',
'그렇게 보면 왕숙이라는 큰 이름에서,',
],
}

REPLACEMENTS={
'A24와B17':'A24와 B17',
'GTX-B와9호선':'GTX-B와 9호선','경의중앙선의 신설역과9호선':'경의중앙선의 신설역과 9호선',
'개통 목표는2031년':'개통 목표는 2031년','전체는2032년':'전체는 2032년',
'B17은2028년12월':'B17은 2028년 12월','A1은2029년2월':'A1은 2029년 2월',
'A3은2030년5월':'A3은 2030년 5월','별내역의8호선과경춘선':'별내역의 8호선과 경춘선',
'이어지는4호선':'이어지는 4호선','전용84제곱미터급':'전용 84제곱미터급',
'서쪽과남쪽':'서쪽과 남쪽','동쪽과남쪽':'동쪽과 남쪽',
'유치원과초·중학교':'유치원과 초·중학교','기능과주상복합':'기능과 주상복합',
'A1과A2':'A1과 A2','왕숙1초는2028년3월':'왕숙1초는 2028년 3월',
'같은 해8월':'같은 해 8월','A24와B17은2028년12월':'A24와 B17은 2028년 12월',
'개교목표는2029년3월':'개교목표는 2029년 3월','A1도2월':'A1도 2월','입주와3월':'입주와 3월',
'상업과공원':'상업과 공원','개점과개방일':'개점과 개방일','학교와공원·상업':'학교와 공원·상업',
'A2는2028년8월':'A2는 2028년 8월','그해12월':'그해 12월','주거와상권':'주거와 상권',
'주택과학교':'주택과 학교','광역철도와일자리':'광역철도와 일자리',
'왕숙의84형':'왕숙의 84형','전용면적과층':'전용면적과 층','2026년7월부터9월':'2026년 7월부터 9월',
'약11억9천만 원':'약 11억 9천만 원','약11억 원':'약 11억 원','약6억8천만 원':'약 6억 8천만 원',
'예산의84제곱미터급':'예산의 84제곱미터급','약6억4천만 원':'약 6억 4천만 원',
'같은6억대':'같은 6억대','새집과미래':'새집과 미래','확장과선택비용':'확장과 선택비용',
'시점과입주':'시점과 입주','전용55제곱미터급':'전용 55제곱미터급',
'전용46형과55형':'전용 46형과 55형','원과4억':'원과 4억','59형과84형':'59형과 84형',
'환승권역과84형':'환승권역과 84형','방향과복합':'방향과 복합',
}

CLAIMS={
'M001':['DEV-001','DEV-002']+[f'{b}-LOC' for b in ['W1-A1','W1-A2','W1-A24','W1-B17','W2-A1','W2-A3']],
'M002':['MAP-JOBS-W1','MAP-RAIL-W1','DEV-005','DEV-006','DEV-007','W1-A24-LOC','W1-B17-LOC','W1-A24-TIME','W1-B17-TIME'],
'M003':['MAP-RAIL-W1','MAP-RAIL-W2','MAP-GTX-TIME','MAP-NINE-TIME','DEV-008','LIV-010','LIV-011']+[f'{b}-{k}' for b in ['W1-A24','W1-B17','W2-A1','W2-A3'] for k in ['LOC','TIME']],
'M004':['W1-B17-PRICE','W2-A1-PRICE','W2-A3-PRICE','ALT-SALE-A1','ALT-SALE-A3'],
'M005':[f'{b}-{k}' for b in ['W1-A1','W1-A2','W1-A24','W1-B17','W2-A1','W2-A3'] for k in ['LIFE','SCHOOL','TIME']],
'M006':['DEV-001']+[f'{b}-TIME' for b in ['W1-A1','W1-A2','W1-A24','W1-B17','W2-A1','W2-A3']],
'M007':['ALT-001','ALT-002','ALT-003','ALT-SALE-A1','ALT-SALE-A3','W1-B17-PRICE'],
'M008':['MAP-RAIL-W1','MAP-RAIL-W2']+[f'{b}-{k}' for b in ['W1-A2','W1-A24','W1-B17','W2-A1','W2-A3'] for k in ['LOC','TIME','LIFE','PRICE','SCHOOL']],
'M009':[],
}

GOALS={
'M001':'전체 토지계획도에서 왕숙1·2와 기능 배치, 분석 범위를 먼저 파악한다.',
'M002':'남측 산업·환승 기능의 공간 장점과 2028 입주/2029 개별준공/2032 단계추진의 시차를 이해한다.',
'M003':'두 예정 환승 중심의 편의와 입주 첫해 기존 교통 연결을 함께 판단한다.',
'M004':'84형 기준층 약6.4/6.9/7.3억과 작은 면적 상품을 분리해 예산을 읽는다.',
'M005':'학교·공원·복합 기능 배치와 2028/2029 학교 목표를 가족 동선에 대입한다.',
'M006':'여섯 블록의 입주예정 군집을 보고 초기생활과 공급중첩의 의미를 이해한다.',
'M007':'같은84㎡급 대안에서 새집·기다림·현재 생활권을 교환하는 조건부 메리트를 판단한다.',
'M008':'B17/A3 입지대장 후보와 A1/A2/A24 실생활·예산 대안을 조건별로 좁힌다.',
'M009':'좋은 배치·이용시점·감수할 가격을 동시에 맞춰 다음 자료를 읽는다.',
}

LINE_BREAKS={
'같은 왕숙 안에서도 일자리 공간과 관계가 가까운 쪽을 구별해 읽을 수 있습니다.':['같은 왕숙 안에서도','일자리 공간과 관계가 가까운 쪽을 구별해 읽을 수 있습니다.'],
'왕숙 안에서 일하고 생활할 가능성을 함께 볼 수 있는 자리라는 데 있습니다.':['왕숙 안에서 일하고 생활할 가능성을','함께 볼 수 있는 자리라는 데 있습니다.'],
'이 출발 가격을 기억하고, 잠시 뒤 주변의 기존 아파트와 비교해보죠.':['이 출발 가격을 기억하고,','잠시 뒤 주변의 기존 아파트와 비교해보죠.'],
'개점과 개방일이 확인되지 않은 곳은 지도에서 계획 상태로 남겨두겠습니다.':['개점과 개방일이 확인되지 않은 곳은','지도에서 계획 상태로 남겨두겠습니다.'],
'단지에서 학교와 공원·상업으로 이어지는 배치를 먼저 보는 것이 좋겠습니다.':['단지에서 학교와 공원·상업으로 이어지는 배치를','먼저 보는 것이 좋겠습니다.'],
'왕숙2 A1은 2029년 2월, A3은 2030년 5월 입주예정입니다.':['왕숙2 A1은 2029년 2월,','A3은 2030년 5월 입주예정입니다.'],
'먼저 들어가는 권역과 뒤에 들어가는 권역이 나뉘는 것을 볼 수 있습니다.':['먼저 들어가는 권역과 뒤에 들어가는 권역이','나뉘는 것을 볼 수 있습니다.'],
'더 이른 이사 선택지를 갖지만, 후속 주거와 상권이 함께 완성되는 과정도 살펴야 합니다.':['더 이른 이사 선택지를 갖지만,','후속 주거와 상권이 함께 완성되는 과정도 살펴야 합니다.'],
'그리고 그 대가로 감수할 조건이 내 생활에서 가능한지가 핵심입니다.':['그리고 그 대가로 감수할 조건이','내 생활에서 가능한지가 핵심입니다.'],
'그리고 예산과 가족 조건에 따라 더 실용적인 대안은 무엇인지 살펴보죠.':['그리고 예산과 가족 조건에 따라','더 실용적인 대안은 무엇인지 살펴보죠.'],
'웹 주택형 평균 표시값은 각각 약 3억 5천만 원과 4억 2천만 원입니다.':['웹 주택형 평균 표시값은 각각','약 3억 5천만 원과 4억 2천만 원입니다.'],
'가족의 면적·예산·학교 달력을 구체적으로 비교하기 좋은 후보입니다.':['가족의 면적·예산·학교 달력을','구체적으로 비교하기 좋은 후보입니다.'],
'미래 환승과 복합 기능이 만들어진 뒤의 생활을 함께 검토할 후보입니다.':['미래 환승과 복합 기능이 만들어진 뒤의 생활을','함께 검토할 후보입니다.'],
'A3은 더 높은 가격과 늦은 입주를 감수할 수 있을 때의 후보입니다.':['A3은 더 높은 가격과 늦은 입주를','감수할 수 있을 때의 후보입니다.'],
'더 낮은 기준층 가격을 중시하면 A3보다 먼저 볼 실생활 경쟁후보입니다.':['더 낮은 기준층 가격을 중시하면','A3보다 먼저 볼 실생활 경쟁후보입니다.'],
'같은 작은 면적이라도 예정 교통 중심과 학교·공원 배치를 함께 보면':['같은 작은 면적이라도','예정 교통 중심과 학교·공원 배치를 함께 보면'],
'내 가족의 첫 출근·등교 조건이 맞지 않으면 이 우선순위는 내려놓아야 합니다.':['내 가족의 첫 출근·등교 조건이 맞지 않으면','이 우선순위는 내려놓아야 합니다.'],
'철도 선이 늘었는지보다 내 첫 출근길이 달라지는지 확인하면 됩니다.':['철도 선이 늘었는지보다','내 첫 출근길이 달라지는지 확인하면 됩니다.'],
}

NAMES=['왕숙1 A1','왕숙1 A2','왕숙1 A24','왕숙1 B17','왕숙2 A1','왕숙2 A3',
'별내별가람역','별내역','오남역','진접역','4호선 진접선','경의중앙선','강동하남남양주선',
'우리금융 AI 디지털 유니버스','다산롯데캐슬','별내푸르지오','별내자이더스타','GTX-B',
'왕숙1초','왕숙11초','55 A1타입','8만 114세대']

def protected(text):
    phrases=set(p for p in NAMES if p in text)
    phrases.update(m.group().strip() for m in re.finditer(r'\d[\d만천억조 ]*(?:세대|제곱미터급|제곱미터|원|년(?:\s*\d+월(?:\s*\d+일)?)?|호선|형|대)',text))
    return sorted(phrases,key=lambda p:(-len(p),p))

def compact(s): return re.sub(r'\s+','',s)
def dump(path,data): path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    raw=SCRIPT.read_text(encoding='utf-8')
    for old,new in REPLACEMENTS.items(): raw=raw.replace(old,new)
    SCRIPT.write_text(raw,encoding='utf-8')
    scenes=re.findall(r'## (M00[1-9]) — ([^\n]+)\n+### 내레이션\n+(.*?)\n+### 화면 지시\n+(.*?)(?=\n## |\Z)',raw,re.S)
    assert len(scenes)==9
    caption_output={'revision':'captions-semantic-script-v3','timing_status':'untimed_pending_approved_new_narration','chapters':{}}
    plan={'revision':'script-v3-map-led','status':'user_review_required','source_script':'writer/map-led-v3/script_v3.md',
       'audio_revision':None,'new_tts_generated':False,'new_images_generated':False,'scenes':[]}
    validation={'source_script_sha256':hashlib.sha256(SCRIPT.read_bytes()).hexdigest(),
       'timing_status':'untimed_pending_new_voice','new_voice_generated':False,
       'chapters':{},'protected_checks':[]}
    all_claims=[]
    for name in ['research/facts.json','research/map-led-v5/facts.json']:
        data=json.loads((EP/name).read_text(encoding='utf-8'))
        all_claims+=data['facts'] if isinstance(data,dict) else data
    alt=json.loads((EP/'research/alternatives-v5/comparison.json').read_text(encoding='utf-8'))
    all_claims+=alt['facts']+alt['wangsuk_sale']
    ids={x['claim_id'] for x in all_claims}
    long=[]
    for scene,title,body,visual in scenes:
        text=re.sub(r'\s+',' ',body).strip()
        marked=text
        for cut in CUTS[scene]:
            assert marked.count(cut)==1,(scene,cut,marked.count(cut))
            marked=marked.replace(cut,cut+'¦')
        marked=re.sub(r'([.!?])(?:\s+|$)',r'\1¦',marked)
        parts=[p.strip() for p in marked.split('¦') if p.strip()]
        assert compact(' '.join(parts))==compact(text)
        cues=[]
        for i,part in enumerate(parts):
            lines=LINE_BREAKS.get(part,[part])
            assert compact(' '.join(lines))==compact(part)
            assert len(lines)<=2 and all(len(line)<=36 for line in lines),(scene,part,lines)
            cues.append({'id':f'{scene}-C{i+1:03}','text':part,'lines':lines,'start_s':None,'end_s':None,
               'protected_phrases':protected(part),'basis':'writer_selected_sentence_or_clause_NOT_character_limit'})
            if len(part)>36: long.append({'scene':scene,'id':cues[-1]['id'],'text':part,'len':len(part)})
        caption_output['chapters'][scene]=cues
        assert all(claim in ids for claim in CLAIMS[scene]),(scene,[c for c in CLAIMS[scene] if c not in ids])
        validation['chapters'][scene]={'exact_whitespace_normalized_coverage':True,
           'normalized_text_sha256':hashlib.sha256(compact(text).encode()).hexdigest(),
           'cue_count':len(cues),'all_claim_ids_resolved':True}
        for phrase in protected(text):
            count=text.count(phrase)
            assert count==sum(c['text'].count(phrase) for c in cues)
            assert count==sum(line.count(phrase) for c in cues for line in c['lines']), (scene,phrase)
            validation['protected_checks'].append({'scene_id':scene,'phrase':phrase,'occurrences':count,'unbroken':True})
        plan['scenes'].append({'scene_id':scene,'title':title,'message':GOALS[scene],
          'narration_text':text,'claim_ids':CLAIMS[scene],'material_types':['map']+(['data_chart'] if scene in ['M003','M004','M006','M007','M008'] else []),
          'visual_instruction':visual.strip(),'asset_ids':[],'script_revision':'script-v3-map-led','audio_revision':None,
          'start_s':None,'end_s':None,'duration_estimate_s':{'min':round(len(text)/10),'max':round(len(text)/7)},
          'timing_basis':'estimate_from_script_length_NOT_actual_narration','status':'story_review',
          'caption_units':len(cues)})
    dump(OUT/'scene_plan.json',plan)
    dump(OUT/'captions_semantic_v3.json',caption_output)
    validation['total_cues']=sum(len(cs) for cs in caption_output['chapters'].values())
    validation['all_times_null']=all(c['start_s'] is None and c['end_s'] is None for cs in caption_output['chapters'].values() for c in cs)
    validation['protected_occurrences']=sum(p['occurrences'] for p in validation['protected_checks'])
    dump(OUT/'validation.json',validation)
    dump(OUT/'source_claims.json',{'revision':'map-led-v3-source-links','claims':all_claims,
       'inferences':[{'id':'ED-LEADER-B17','statement':'예정환승권역+84형기준가격을근거로입지대장후보로검토','status':'조건부편집해석','claim_ids':['MAP-RAIL-W1','W1-B17-LOC','W1-B17-PRICE','W1-B17-LIFE']},
         {'id':'ED-LEADER-A3','statement':'예정환승방향+복합기능배치를근거로입지대장후보로검토','status':'조건부편집해석','claim_ids':['MAP-RAIL-W2','W2-A3-LOC','W2-A3-LIFE','W2-A3-PRICE']} ]})
    print(json.dumps({'scene_count':len(scenes),'cue_count':validation['total_cues'],
       'protected_occurrences':validation['protected_occurrences'],'all_times_null':True,
       'text_preserved_all_chapters':True,'all_claim_ids_resolved':True},ensure_ascii=False))

if __name__=='__main__': main()
