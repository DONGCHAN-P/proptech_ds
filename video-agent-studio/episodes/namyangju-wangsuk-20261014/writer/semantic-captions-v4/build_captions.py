"""Approved narration -> editorial semantic cues; no text rewriting or TTS."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SCRIPT = ROOT / 'writer/script_v2.md'

# These boundaries are individually selected from the approved Korean narration.
# Sentence punctuation supplies natural sentence endings; this list supplies the
# additional semantic clause boundaries, never a character-count slice.
CUTS = {
'S001': [
'광교와 동탄을 살펴본 지난 영상의 마지막에,',
'별내와 다산, 진접 같은 기존 지역부터 지도에서 찾고,',
'이미 살고 있는 도시의 거래를 되짚었던 전편에서,',
'오늘은 먼저 왕숙 전체의 위치를 이해하고,',
'입주와 가격은 이번에 공고를 확인한',
'지구가 다르면',
'광교나 동탄의 가격 흐름을',
'내 직장과 학교, 입주 시기를 떠올리며,',
'다섯 질문 가운데 어느 항목이 준비됐고',
],
'S002': [
'남양주에는 별내와 다산, 진접과 오남,',
'이 이름들을 모든 사람에게 통하는',
'실제 생활은 내 집과 역, 직장, 학교를',
'별내별가람역은 4호선 진접선의 역이고,',
'별내역과 별내별가람역은 이름에 별내가 들어가지만',
"부동산 설명에서 '별내 쪽 지하철'이라는 말을 들었다면,",
'집에서 그 역까지 걸어가는지, 버스를 타는지에 따라',
'운영사의 다산역 안내에는',
'주변 주거와 상권, 공원과 쇼핑시설로 나가는',
'기존 지역을 살펴볼 때는 이런 실제 시설을 지도에서 찾고',
'역이 있다는 사실과',
'내가 알아보는 모든 단지가 역에 가깝다는 것은',
'출근할 목적지를 정하고, 실제 이용할 역을 고른 다음,',
'역에서 회사까지의 시간뿐 아니라',
'전편에서도 역 주변 대표 단지의 가격이',
'남양주에서도 같은 기준으로',
'조건이 같은 통근시간 실측은 없어',
],
'S003': [
'왕숙은 기존 남양주의 여러 지역에 더해지는',
'남양주시 사업개요에서 왕숙1은',
'진접읍, 진건읍, 퇴계원읍 일원에',
'약 1천29만 제곱미터에',
'왕숙2는 일패동과 이패동 일원,',
'지금 8만 세대가 분양을 마쳤다거나',
'큰 숫자를 보실 때는',
'그래서 왕숙이라는 같은 이름을 쓰더라도',
'개별 블록에서 역과 학교, 상업시설로 가는 길을',
'왕숙1 안에서도 어디에 있는 블록인지 확인해야 하고,',
'예정 역의 출입구와 실제 보행길이 확정되지 않으면',
],
'S004': [
'전편에서는 광교와 동탄의 철도를',
'왕숙에서도 노선 이름을 확인한 다음,',
'LH 안내에서 A1은 812세대,',
'같은 왕숙2라도',
'이 날짜는 현재 공고의 예정일이며',
'국토교통부의 2026년 업무계획은',
'GTX-B의 2025년 8월 착공과',
'이 자료 하나가 왕숙 관련 개별 역의 공정과 출입구,',
'9호선 연장으로 불리는 강동하남남양주선은',
'하지만 2026년 9월 경기도의회 자료에는',
'2공구와 5공구의 추진방향을 조속히 확정하고',
'이번 편에서는 9호선의 최신 개통 연도를',
'왕숙2 A1의 2029년 2월,',
'A3의 2030년 5월 입주예정과',
'GTX-B의 2031년 목표를 나란히 놓으면,',
'물론 주택과 철도 일정은 모두 바뀔 수 있으니,',
'예를 들어 서울로 매일 출근하는 가구라면,',
'앞으로 철도가 연결된다는 설명 다음에',
'아직 이용할 수 없다면',
'여기까지 다섯 질문 중 철도는',
'현재 운영 노선은 기존 생활권에서 확인하고,',
'미래 노선의 출입구와 실제 보행길이 확정되지 않았는데',
'지도에 원을 그려 모두 역세권이라고 표시하면',
],
'S005': [
'전편에서 동탄의 일자리는 기업 이름 하나로 설명하지 않고,',
'가까운 곳에서 일할 수 있다면',
'다만 이미 운영하는 일터를 봤던 전편과 달리,',
'남양주시 자료에서 진관, 금곡, 광릉테크노밸리는',
'지도에서 이 기존 단지와 왕숙의 미래 산업단지를 따로 보면,',
'남양주시는 2026년 10월 8일',
'왕숙 도시첨단산업단지의',
'발표에서 설명한 규모는 왕숙지구 남측',
'약 120만 제곱미터,',
'이 금액은 발표된 사업비이며',
'산업단지 계획이 승인됐다는 것은',
'하지만 산업단지 전체가 완성됐고',
'시 소개에는 우리금융, 카카오, 신한이',
'실제 상주 인력과 운영 완료는',
'그중 우리금융 AI 디지털 유니버스는',
'남양주시의 2026년 6월 발표는',
'건축허가라는 단계와',
'허가를 받았다는 사실만으로',
'시설을 조성하는 데 쓰는 자금이 크더라도,',
'지금 봐야 할 것은 어떤 시설인지, 어느 부지에 들어오는지,',
'지역에서 일하는 가구라면',
'서울로 통근하는 가구라면',
'다른 가구의 직주근접 가능성이',
],
'S006': [
'광교와 동탄에서는 역과 일자리뿐 아니라',
"왕숙에서는 그 질문이",
'특히 자녀가 있는 가구라면',
'어느 학교가 심사를 통과했는지, 언제 문을 열려고 하는지,',
'교육지원청의 2025년 10월 발표에는',
'왕숙11초, 왕숙1고, 왕숙2-1초, 왕숙2-1중,',
'같은 해 11월에는 왕숙7유와 왕숙2-1유,',
'두 유치원의 재정투자심사 통과가 발표됐고,',
'이것은 학교와 유치원 설립 절차가 진행됐다는',
'이 자료만으로 내가 알아보는 단지가 어느 학교에 배정되는지,',
'교육시설의 2029년 3월 목표와',
'하지만 그 숫자만으로 A1에 입주하면',
'A3은 2030년 5월 입주예정이므로,',
'남양주시는 왕숙2의 WE 드림파크가',
'발표 당시 총사업비 669억 원 가운데',
'이 소식은 시설 준비의 진행 단계로 볼 수 있지만,',
'아침에는 아이를 학교나 유치원에 보내고,',
'저녁에는 장을 보고,',
'토지이용계획도에 시설이 표시된 것과',
'반대로 아직 준비 중인 시설이 있다는 이유만으로',
'기존 시설을 이용하는 경로와',
],
'S007': [
'숫자를 비교하기 전에',
'LH의 왕숙2 A1 페이지에서',
'59A는 4억 9천304만 원,',
'A3 페이지에서 59A는 5억 2천634만 원,',
'두 페이지에는',
'이후 정정공고와 최종 계약 조건을 모두 대조해',
'왕숙2 전체의 평균 집값이나',
'59A끼리, 84A끼리 먼저 구분하고,',
'같은 이름의 타입이라도',
'여기에 발코니 확장과 유상선택품목을 모두 포함한',
'실제 계약을 검토할 때는',
'A3 페이지는 확장면적 표기와 특별공급 소득기준에',
'정정사항을 안내하고 있으니,',
'다만 이미 사람이 살고 있는 단지의 거래가격과',
'아직 입주 전인 공공분양 가격에는',
'같은 전용면적, 비슷한 거래 시점,',
'서로 다른 조건의 숫자를 빼서',
'전편에서 최고가와 중위가격을 나눠 읽었던 이유도,',
'주변 대비 저렴한지는 동일 조건의 비교가 더 필요하고,',
'앞서 본 8만 114세대는',
'구체적인 공고에서는 왕숙2 A1과 A3처럼',
'같은 생활권에서 어느 해에 얼마나 겹치는지는',
'이번에는 그 전체 물량을 검증하지 못했으므로',
'공급이 많아 가격이 내려간다거나',
],
'S008': [
'광교와 동탄에서 남긴 다섯 질문에,',
'일자리는 기존 산업 기반과 새 산단 승인,',
'철도는 현재 운영과 미래 계획을 구분하고',
'분양가는 왕숙2 A1과 A3의',
'공급도 전체 계획규모와 블록별 입주예정을 구분했지만,',
'서울로 통근하는 가구는 철도의 첫해 이용 조건을,',
'지역에서 일하는 가구는 실제 사업장과 운영 시점을,',
'전편이 이미 만들어진 도시를',
'이번 편은 앞으로 만들어질 도시를',
'이 기준을 이어가며 남양주라는 이름에서',
'다음에 새 발표를 보더라도',
'기업이나 철도 이름에서 멈추지 않고,',
],
}

LINE_BREAKS = {
'계획, 실제 공급, 실제 입주 가운데 무엇을 세었는지 확인해주세요.':
 ['계획, 실제 공급, 실제 입주 가운데','무엇을 세었는지 확인해주세요.'],
'새로운 일자리 계획과 별도로 자신의 서울 출근 경로를 살펴야 합니다.':
 ['새로운 일자리 계획과 별도로','자신의 서울 출근 경로를 살펴야 합니다.'],
"'우리 가족이 들어가는 해에 무엇을 이용할 수 있을까'로 바뀝니다.":
 ["'우리 가족이 들어가는 해에","무엇을 이용할 수 있을까'로 바뀝니다."],
'최신 정정 모집공고의 층별 공급가격과 추가 비용을 확인해야 합니다.':
 ['최신 정정 모집공고의 층별 공급가격과','추가 비용을 확인해야 합니다.'],
'청약 자격과 전매·거주 조건, 대출까지 확인해야 내 예산표가 됩니다.':
 ['청약 자격과 전매·거주 조건, 대출까지 확인해야','내 예산표가 됩니다.'],
}

NAMED_PHRASES = [
 '별내역', '별내별가람역', '오남역', '진접역', '다산역',
 '4호선 진접선', '8호선 별내선', '경춘선', '강동하남남양주선', 'GTX-B',
 '왕숙2 A1', '왕숙2 A3', '왕숙 A1', '왕숙11초', '왕숙1고',
 '왕숙2-1초', '왕숙2-1중', '왕숙2-1유', '왕숙7유', '59A', '84A',
 '우리금융 AI 디지털 유니버스', 'WE 드림파크', '광릉테크노밸리',
 '6만 4천159세대', '1만 5천955세대', '8만 114세대',
 '4억 9천304만 원', '6억 9천363만 원', '5억 2천634만 원', '7억 3천245만 원',
 '1조 8천993억 원', '8천500억 원',
]

# Short dependent introductory clauses stay on screen with their complement.
# These are explicit editorial choices, not a minimum-length heuristic.
MERGE_NEXT = {
'지구가 다르면', '역이 있다는 사실과', '큰 숫자를 보실 때는',
'같은 왕숙2라도', '아직 이용할 수 없다면', '왕숙 도시첨단산업단지의',
'건축허가라는 단계와', '왕숙에서는 그 질문이', '저녁에는 장을 보고,',
'숫자를 비교하기 전에', '두 페이지에는', '같은 이름의 타입이라도',
}

LINE_BREAKS["왕숙에서는 그 질문이 '우리 가족이 들어가는 해에 무엇을 이용할 수 있을까'로 바뀝니다."] = [
 "왕숙에서는 그 질문이 '우리 가족이 들어가는 해에",
 "무엇을 이용할 수 있을까'로 바뀝니다."]
LINE_BREAKS['큰 숫자를 보실 때는 계획, 실제 공급, 실제 입주 가운데 무엇을 세었는지 확인해주세요.'] = [
 '큰 숫자를 보실 때는 계획, 실제 공급, 실제 입주 가운데',
 '무엇을 세었는지 확인해주세요.']

def protected(text):
    values = set(p for p in NAMED_PHRASES if p in text)
    values.update(m.group().strip() for m in re.finditer(
        r'\d[\d만천억조 ]*(?:세대|제곱미터|원|년(?:\s*\d+월(?:\s*\d+일)?)?|호선|공구|층)', text))
    return sorted(values, key=lambda p: (-len(p),p))

def normalized(t):
    return re.sub(r'\s+', '', t)

def make_cues(text, scene):
    text = re.sub(r'\s+', ' ', text).strip()
    for cut in CUTS[scene]:
        assert text.count(cut) == 1, (scene, cut, text.count(cut))
        text = text.replace(cut, cut + '¦')
    # All periods in narration are sentence endings (decimal prices are spoken
    # Korean and do not contain decimal dots). No word/line length split.
    text = re.sub(r'([.!?])(?:\s+|$)', r'\1¦', text)
    chunks = [part.strip() for part in text.split('¦') if part.strip()]
    merged=[]
    n=0
    while n<len(chunks):
        part=chunks[n]
        if part in MERGE_NEXT:
            following=chunks[n+1]
            joined=part+' '+following
            if joined not in LINE_BREAKS and len(joined)>36:
                LINE_BREAKS[joined]=[part,following]
            merged.append(joined)
            n+=2
        else:
            merged.append(part)
            n+=1
    return merged

def main():
    raw = SCRIPT.read_text(encoding='utf-8')
    texts = dict(re.findall(r'## (S00[1-8])[^\n]*\n+### 내레이션\n+(.*?)\n+### 화면 지시', raw, re.S))
    assert len(texts) == 8
    timings = json.loads((ROOT/'editor/render_v1/timing_actual.json').read_text(encoding='utf-8'))
    result = {'revision':'semantic-captions-v4','source_script':'writer/script_v2.md',
      'source_sha256': hashlib.sha256(SCRIPT.read_bytes()).hexdigest(),
      'timing_status':'provisional_character_weight_within_measured_chapter_NOT_word_alignment',
      'word_alignment_performed':False,'actual_listening_performed':False,'chapters':{}}
    review = {'revision':'semantic-captions-v4','chapters':{},'long_cues':[],
       'protected_phrase_checks':[], 'sentence_or_manual_clause_boundaries_only': True,
       'word_alignment_performed': False, 'actual_listening_performed': False}
    for timing in timings:
        scene = timing['scene_id']
        duration = timing['encoded_frames']/30
        parts = make_cues(texts[scene],scene)
        assert normalized(' '.join(parts)) == normalized(texts[scene])
        weights=[len(normalized(part)) for part in parts]
        total=sum(weights)
        cursor=0
        cues=[]
        for n,(part,weight) in enumerate(zip(parts,weights)):
            end = duration if n == len(parts)-1 else cursor + duration*weight/total
            cues.append({'id':f'{scene}-C{n+1:03}','start_s':round(cursor,6),
              'end_s':round(end,6),'text':part,'lines':LINE_BREAKS.get(part,[part]),
              'protected_phrases':protected(part),
              'basis':'editorial_semantic_boundary_character_weight_estimate_NOT_forced_alignment'})
            assert normalized(' '.join(cues[-1]['lines'])) == normalized(part)
            assert len(cues[-1]['lines'])<=2
            assert all(len(line)<=36 for line in cues[-1]['lines']), (scene, part, cues[-1]['lines'])
            if len(part)>36:
                review['long_cues'].append({'scene_id':scene,'id':cues[-1]['id'],'length':len(part),'text':part})
            cursor=end
        result['chapters'][scene]=cues
        for phrase in protected(re.sub(r'\s+', ' ', texts[scene])):
            expected = re.sub(r'\s+', ' ',texts[scene]).count(phrase)
            actual = sum(cue['text'].count(phrase) for cue in cues)
            line_actual = sum(line.count(phrase) for cue in cues for line in cue['lines'])
            assert expected == actual == line_actual, (scene,phrase,expected,actual,line_actual)
            review['protected_phrase_checks'].append({'scene_id':scene,'phrase':phrase,
               'occurrences':expected,'whole_in_one_cue_and_one_line':True})
        review['chapters'][scene]={'cue_count':len(cues),'duration_s':duration,
          'exact_whitespace_normalized_coverage':True,
          'normalized_text_sha256':hashlib.sha256(normalized(texts[scene]).encode()).hexdigest()}
    (OUT/'captions.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    old_path=ROOT.parents[2]/'video/src/namyangju-v2/project.json'
    old=json.loads(old_path.read_text(encoding='utf-8'))['captions']
    examples=[]
    for scene,old_cues in old.items():
        for phrase in protected(re.sub(r'\s+', ' ',texts[scene])):
            if not any(phrase in c['text'] for c in old_cues):
                joined=''.join(normalized(c['text']) for c in old_cues)
                if normalized(phrase) in joined:
                    examples.append({'scene_id':scene,'protected_phrase':phrase,
                       'old_status':'broken_across_cues',
                       'new_cue':[c['text'] for c in result['chapters'][scene] if phrase in c['text']]})
    review['confirmed_old_numeric_or_name_breaks_fixed']=examples
    review['total_cues']=sum(len(c) for c in result['chapters'].values())
    review['maximum_line_chars']=max(len(line) for cs in result['chapters'].values() for c in cs for line in c['lines'])
    review['total_protected_occurrences']=sum(c['occurrences'] for c in review['protected_phrase_checks'])
    (OUT/'semantic_qa.json').write_text(json.dumps(review,ensure_ascii=False,indent=2),encoding='utf-8')
    editorial=['# 의미 단위 자막 v4 전체 검토본', '',
      '승인 대본 v2의 낭독문을 그대로 보존했다. 아래 시각은 장면 상대 추정값이며 음성 단어 정렬이 아니다.', '']
    for scene,cues in result['chapters'].items():
        editorial += [f'## {scene}', '']
        for c in cues:
            editorial += [f"- {c['id']} ({c['start_s']:.3f}–{c['end_s']:.3f}초): "+' / '.join(c['lines'])]
        editorial += ['']
    (OUT/'editorial_review.md').write_text('\n'.join(editorial)+'\n',encoding='utf-8')
    print(json.dumps({k:review[k] for k in ['total_cues','maximum_line_chars','total_protected_occurrences','confirmed_old_numeric_or_name_breaks_fixed']},ensure_ascii=False,indent=2))

if __name__ == '__main__':
    main()
