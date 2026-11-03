from pathlib import Path
import re,json,hashlib,difflib
ep=Path(__file__).resolve().parents[2]
own=ep/'writer/revision-v8'; out=ep/'outputs/script-review-v8'
source=ep/'outputs/script-review-v7/script_v7.md'
old=source.read_text(encoding='utf-8')
expected='ceb9a4e443dc2d7b36cdf84f5c515fa726d501a85e04d82ca81a4439c894bbbc'
assert hashlib.sha256(source.read_bytes()).hexdigest()==expected
replacements={
'경쟁할 수 있겠죠.':'경쟁할 수 있습니다.',
'가격을 어떻게 갈라놓는지 봤고요.':'가격을 어떻게 갈라놓는지 살펴봤습니다.',
'차례로 볼게요.':'차례로 살펴보겠습니다.',
'출발점이 다르죠.':'출발점이 다릅니다.',
'함께 살펴볼 후보이고요.':'함께 살펴볼 후보입니다.',
'중요한 건 지구 이름 하나로 가격을 묶지 않는 겁니다.':'중요한 점은 지구 이름 하나로 가격을 묶지 않는 것입니다.',
'다를 수 있거든요.':'다를 수 있기 때문입니다.',
'일자리부터 볼게요.':'일자리부터 살펴보겠습니다.',
'더 구체적이겠죠.':'더 구체적입니다.',
'시간을 비교했어요.':'시간을 비교했습니다.',
'80분이었고요.':'80분이었습니다.',
'여기서 상암을 조금 더 볼까요.':'상암의 결과를 조금 더 살펴보겠습니다.',
'빠른 건 아니었어요.':'빠른 것은 아니었습니다.',
'부담스러운 시간이죠.':'부담스러운 시간입니다.',
'구간이 먼저 있죠.':'구간이 먼저 있습니다.',
'2030년 3월이고요.':'2030년 3월입니다.',
'똑같이 좋아지는 건 아니겠죠.':'똑같이 좋아지는 것은 아닙니다.',
'다시 쓰게 될 수 있으니까요.':'다시 쓰게 될 수 있기 때문입니다.',
'사는 건 다른 선택이에요.':'사는 것은 다른 선택입니다.',
'가격표를 볼게요.':'가격표를 살펴보겠습니다.',
'세금은 별도이고요.':'세금은 별도입니다.',
'약 8,300만 원이고요.':'약 8,300만 원입니다.',
'다시 확인해야 하니까요.':'다시 확인해야 하기 때문입니다.',
'여력은 작을 수 있죠.':'여력은 작을 수 있습니다.',
'중위값을 계산했어요.':'중위값을 계산했습니다.',
'9억 2,000만 원이고요.':'9억 2,000만 원입니다.',
'서로 다르기 때문이죠.':'서로 다르기 때문입니다.',
'중요하다는 걸 이 표에서도 볼 수 있죠.':'중요하다는 점을 이 표에서도 확인할 수 있습니다.',
'다른 아파트예요.':'다른 아파트입니다.',
'생활권 대안도 있죠.':'생활권 대안도 있습니다.',
'거래가 있다는 건,':'거래가 있다는 것은,',
'그럼 집이 늘어나는 건 가격에 유리할까요, 불리할까요?':'집이 늘어나는 것은 가격에 유리할까요, 불리할까요?',
'2,277세대예요.':'2,277세대입니다.',
'이건 오늘 비교한':'이는 오늘 비교한',
'부를 수는 없고요.':'부를 수는 없습니다.',
'기반이 생기는 거죠.':'기반이 생기는 것입니다.',
'꼭 같지는 않아요.':'꼭 같지는 않습니다.',
'함께 봐야 하는 이유죠.':'함께 봐야 하는 이유입니다.',
'지금 확보한 건':'지금 확보한 자료는',
'짧게 구분할게요.':'짧게 구분하겠습니다.',
'선택할 이유가 생기겠죠.':'선택할 이유가 생길 수 있습니다.',
'그해 3월 목표이고요.':'그해 3월 목표입니다.',
'2030년 3월 목표이고요.':'2030년 3월 목표입니다.',
'완성도가 달라지니까요.':'완성도가 달라지기 때문입니다.',
'이제 세 후보를 좁혀볼게요.':'이제 세 후보를 좁혀보겠습니다.',
'가능성을 보는 겁니다.':'가능성을 보는 것입니다.',
'잘 이뤄지는지도 봐야겠죠.':'잘 이뤄지는지도 확인해야 합니다.',
'빠르지는 않았죠.':'빠르지는 않았습니다.',
'시간을 거쳐야 해요.':'시간을 거쳐야 합니다.',
'볼 요소이고요.':'살펴볼 요소입니다.',
'정해 놓은 건 아닙니다.':'정해 놓은 것은 아닙니다.'
}
def parse(s):
    ch=re.split(r'\n## (M\d+) ',s)[1:]; result=[]
    for i in range(0,len(ch),2):
        sid,b=ch[i:i+2]; sec=b.split('### ')
        result.append((sid,sec[1].split('\n\n',1)[1].strip(),sec[2].split('\n\n',1)[1].strip()))
    return result
s=old
for sid,narration,screen in parse(old):
    new=narration
    for a,b in replacements.items(): new=new.replace(a,b)
    s=s.replace(narration,new,1)
s=s.replace('# 창릉 대본 v7','# 창릉 대본 v8',1)
s=s.replace('상태: 사용자 검토용 신규 초안. v6 승인을 승계하지 않는다.','상태: 사용자 검토용 v8 문체 수정 초안. v7 검토를 바탕으로 어미·호흡만 교정하며 기존 승인을 새 버전에 자동 적용하지 않는다.',1)
s=s.replace('각 챕터 시작에는 번호와 제목만 담은 독립 챕터 카드를 넣고 제목을 충분히 읽을 시간을 준다.','각 챕터 시작에는 번호와 제목을 담은 독립 챕터 카드를 넣고 제목을 충분히 읽을 시간을 준다. GPT로 만든 분위기 배경의 챕터 화면과 텍스트만 나오는 슬라이드는 사용하지 않는다. 해당 장에서 설명할 실제 지역 지도·계획도·가격 원문 자료를 챕터 배경에 활용하고, 일자리·교통·가격·생활시설·공급의 각 영역에 맞는 자료와 지도 강조를 사용한다.',1)
s=s.replace('화면 챕터 번호는 위에서 아래 설명 순서대로 01~09를 사용한다.','01~09는 장면 순서 메타데이터이며 화면 분석 챕터 번호가 아니다. 도입과 결론은 무번호로 두고 화면 분석 번호는 1 일자리(M002), 2 교통(M003), 3 가격(M004), 4 주변 거래(M007), 5 공급(M006), 6 생활시설(M005)로 표시한다.',1)
s=s.replace('GPT로 만든 분위기 배경의 챕터 화면과 텍스트만 나오는 슬라이드는 사용하지 않는다. 해당 장에서 설명할 실제 지역 지도·계획도·가격 원문 자료를 챕터 배경에 활용하고, 일자리·교통·가격·생활시설·공급의 각 영역에 맞는 자료와 지도 강조를 사용한다.','독립 챕터에는 assets/chapter-backgrounds/v1의 재사용 GPT 개념 배경과 별도 제목을 사용한다. 개념 배경을 실제 창릉의 장소·건축물이나 확정 계획의 증거처럼 표현하지 않는다. 텍스트만 있는 본문 화면은 각 메시지에 맞는 실제 지역 지도·원문 표·이미지·도식으로 바꾼다. 일자리·교통·가격·주변 거래·공급·생활시설의 각 영역에 맞는 자료와 지도 강조를 사용한다.',1)
target=out/'script_v8.md';target.write_text(s,encoding='utf-8')
sha=hashlib.sha256(target.read_bytes()).hexdigest()
scenes=parse(s); oldscenes=parse(old)
assert [x[0] for x in scenes]==[x[0] for x in oldscenes]
evidence=[]
for (sid,a,_),(_,b,_) in zip(oldscenes,scenes):
    nums=lambda t:re.findall(r'\d[\d,.]*(?:·\d+)*',t)
    assert nums(a)==nums(b),(sid,nums(a),nums(b))
    evidence.append({'scene_id':sid,'numeric_tokens_unchanged':True,'before_characters':len(a),'after_characters':len(b),'narration_changed':a!=b})
def write(name,j,folder=own): (folder/name).write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
proposal=json.loads((ep/'writer/revision-v7/scene_proposals.json').read_text(encoding='utf-8'))
proposal['revision']='script-v8';proposal['script_sha256']=sha
analysis_chapters={'M002':1,'M003':2,'M004':3,'M007':4,'M006':5,'M005':6}
proposal['chapter_card_policy']='reusable GPT concept backgrounds from assets/chapter-backgrounds/v1 plus separate titles; do not represent actual Changneung evidence; intro and conclusion unnumbered'
proposal['shared_visual_direction']=s.split('## 공통 화면 지침',1)[1].split('## M000',1)[0].strip()
for sc,(sid,narration,screen) in zip(proposal['scenes'],scenes):
    sc['scene_sequence_index']=sc.get('chapter_index')
    sc['chapter_index']=analysis_chapters.get(sid)
    sc['narration_text']=narration;sc['screen_direction']=screen;sc['script_revision']='script-v8'
    sc['estimated_narration_seconds']=round(len(narration)*786.48/6372,1)
    sc['semantic_caption_plan']=[{'text':x.strip(),'timing_status':'untimed','split_required_if_long':len(x.strip())>42} for x in re.split(r'(?<=[.!?])\s+|\n',narration) if x.strip()]
write('scene_proposals.json',proposal)
packet=json.loads((ep/'writer/revision-v7/narration_packet.json').read_text(encoding='utf-8'))
chars=sum(len(x[1]) for x in scenes)
packet.update({'revision':'script-v8','script_sha256':sha,'characters_including_spaces':chars,'estimated_narration_seconds':round(chars*786.48/6372,1),'estimated_final_seconds':round(chars*786.48/6372+18,1),'direction':'정보 제공에 맞는 설명형 격식체. 합니다·하겠습니다·입니다 중심. 보십시오·마십시오 같은 명령형 억양 금지. 숫자와 단위를 붙여 낭독. 독립 챕터 카드 체류시간은 예상 본편 길이와 별도.','scenes':[{'scene_id':x[0],'text':x[1]} for x in scenes]})
packet['estimate_limit']='Prior Jun character/duration ratio only; pace/numerals differ. No v8 voice generated, listened to, or timing locked. Chapter-card dwell is separate.'
write('narration_packet.json',packet)
plain='\n'.join(x[1] for x in scenes)
bad=['할게요','볼게요','보죠','였고요','거든요','겠죠','예요','이고요','했어요','니까요','아니었어요','않아요','해요','있죠','이죠','다르죠','보십시오','마십시오']
validation={'source_v7_sha256':expected,'source_v7_unchanged':hashlib.sha256(source.read_bytes()).hexdigest()==expected,'script_v8_sha256':sha,'narration_characters':chars,'scene_count':len(scenes),'numeric_tokens_match_every_scene':True,'M008_absent':all(x[0]!='M008' for x in scenes),'speech_endings_scan':{x:plain.count(x) for x in bad},'independent_review':'pending','voice_generated':False,'listening':False,'rendered':False}
write('evidence_comparison.json',{'scope':'same claim_ids/evidence references and numeric tokens; speech endings only. Visual shared instructions add requested background policy.','scenes':evidence})
write('validation.json',validation)
write('handoff.json',{'task_id':'writer-v8','role':'writer','status':'draft_needs_review','input_revisions':{'script':'script-v7','script_sha256':expected,'packets':'writer/revision-v7'},'outputs':['outputs/script-review-v8/script_v8.md','outputs/script-review-v8/changes_v8.md','writer/revision-v8/narration_packet.json','writer/revision-v8/scene_proposals.json','writer/revision-v8/evidence_comparison.json','writer/revision-v8/validation.json','writer/revision-v8/script_v7_to_v8.diff'],'affected_scene_ids':[x[0] for x in scenes],'checks':[{'check':'same numeric tokens and existing claims','result':'pass','evidence':'writer/revision-v8/evidence_comparison.json'},{'check':'independent review','result':'pending','evidence':None}],'open_issue_ids':[],'next_role':'director_then_independent_qa','limits':['v7 unchanged','no new facts','no voice/render','no approval/state changes']})
(own/'script_v7_to_v8.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile='script_v7.md',tofile='script_v8.md')),encoding='utf-8')
(out/'changes_v8.md').write_text(f'''# v8 문체 수정 안내

v7의 사실·수치·장면 순서·가격 중심 대장 후보 논리·학교 보조 비중을 유지하고, 낭독 어미와 호흡을 정보 제공에 맞는 설명형 격식체로 다듬었습니다. “볼게요·했어요·이고요·겠죠·거든요” 등을 “살펴보겠습니다·했습니다·입니다·있습니다” 중심으로 교정했습니다. 보십시오·마십시오 같은 훈계형 문장은 넣지 않았습니다. 새 내용과 경쟁률을 추가하지 않았고 M008 삭제 상태도 유지했습니다.

공통 화면 지침은 독립 챕터에 assets/chapter-backgrounds/v1의 GPT 개념 배경과 별도 제목을 사용하도록 교정했습니다. 개념 배경은 실제 창릉 장소·계획의 근거로 표현하지 않습니다. 텍스트 전용 본문은 지도·원문·이미지·도식으로 대체합니다. 화면 분석 번호는 1 일자리, 2 교통, 3 가격, 4 주변 거래, 5 공급, 6 생활시설이며 도입·결론은 무번호입니다. 01~09는 장면 순서 메타데이터입니다. 우상단 라벨과 하단 의미 자막 아래 출처 영역을 유지합니다.

낭독 {chars:,}자, 9장면입니다. 기존 Jun 6,372자/786.48초의 비율로 낭독 {packet['estimated_narration_seconds']}초, 브랜드와 마감 홀드18초를 더하면 {packet['estimated_final_seconds']}초의 estimate입니다. 독립 챕터 카드 체류시간은 별도이며 새 음성의 실측이나 타임락이 아닙니다.

숫자 토큰을 장면별로 대조했고 기존 claim_ids와 근거 경로를 유지했습니다. v7 원본 해시 {expected}는 변하지 않았습니다. v8 SHA256은 {sha}입니다. 독립 검수와 사용자 승인은 대기 중이며 음성 생성·청취·렌더는 수행하지 않았습니다.
''',encoding='utf-8')
print(json.dumps(validation,ensure_ascii=False))
