from pathlib import Path
import json, hashlib, shutil
EP=Path(__file__).resolve().parents[2]
O=EP/'outputs/readable-video-v2';O.mkdir(parents=True,exist_ok=True)
src=EP/'writer/readable-v2/scenes.json'
d=json.loads(src.read_text('utf-8'))
d['scenes'][2]['paragraphs'][1]['text']='크기를 눈에 그려보려면 실제 평면이 도움이 됩니다. 남양주왕숙 A-1블록의 59A를 보겠습니다. 이 집의 실제 전용면적은 59.92제곱미터, 약 18.1평입니다. 주거공용면적을 더한 공급면적은 약 84.46제곱미터, 약 25.5평입니다. 같은 집도 어느 면적을 쓰느냐에 따라 숫자가 달라집니다. 방과 거실의 배치를 보면 이 공간이 우리 생활에 맞을지도 생각해볼 수 있습니다.'
d['scenes'][2]['paragraphs'][1]['note']='FP59 공식 LH 2025 팸플릿 PDF9쪽(인쇄16·17), 남양주왕숙 A-1 59A, 전용59.92/공급84.4583. 분양 계획도, 발코니 확장형. R2·R3 표본단지 아님. 59.92/3.305785=18.13평,84.4583/3.305785=25.55평(반올림25.5).'
d['scenes'][2]['paragraphs'][1]['source_ids']=['FP59']
heads=[
 ['같은 수도권인데, 왜 다르게 움직일까요?','2006년 이후 실거래에서 출발합니다','가격 차이 뒤의 생활 조건을 봅니다'],
 ['사람은 그대로, 사는 집은 두 곳으로','사람 수 다음에는 어떤 가구인지 봅니다','주거비가 올라서 이동했을 수도 있습니다','전출 숫자 뒤의 사정을 봅니다'],
 ['살지 빌릴지, 필요한 공간은 얼마인지','같은 집의 전용면적과 공급면적','소득과 자산은 다른 조건입니다','누가 어떤 크기의 집을 찾는가'],
 ['새집이 완성되기 전에 살 집이 필요합니다','주민들의 실제 이주 목적지를 추적했습니다','가격과 이동의 방향을 구분한 추정','사업지 밖의 대체 거주도 살펴봅니다'],
 ['똑같이 천 채가 준공돼도 순증은 다릅니다','이사 날짜와 입주 날짜가 맞을까요?','준공 직후와 그 이후는 구분합니다','몇 채, 언제, 어떤 집이 생기는가'],
 ['역까지 같아도 출근길은 다릅니다','사업체 수 다음에 통근 연결을 봅니다','통근 연결과 이동의 편의는 다릅니다','걷기·대기·환승까지 넣어 봅니다','내 직장까지 다닐 수 있는 집인가'],
 ['가구마다 집을 고르는 조건이 있습니다','조건을 겹치면 남는 집이 달라집니다','실제로 고를 수 있는 집은 얼마나 될까요?'],
 ['가격 경로에서 가구의 선택으로','다음에는 이 조건들을 자료로 확인합니다','집값을 데이터로 함께 살펴봅니다']
]
for s,hs in zip(d['scenes'],heads):
    assert len(s['paragraphs'])==len(hs),(s['id'],len(s['paragraphs']))
    for p,h in zip(s['paragraphs'],hs):p['screen_headline']=h
dest=O/'approved_working_scenes.json';dest.write_text(json.dumps(d,ensure_ascii=False,indent=2),'utf-8')
# Preserve writer's handoff unchanged. Main's exact production text is versioned separately.
refs=json.loads((Path(__file__).parent/'references.json').read_text('utf-8'))
fp=json.loads((EP/'research/readable-v2/floorplan_facts.json').read_text('utf-8'))['examples'][0]
md=['# 인용자료와 화면 예시','', '가독성 수정본 v2 · 2026-10-25','', '영상에서는 저자를 처음 소개할 때 각 개인에게 ‘님’을 붙입니다. 아래는 원문의 서지와 이번 영상에서 실제로 사용하는 범위를 함께 적은 목록입니다. 문헌의 결과를 서울·경기 집값 차이의 원인별 기여율로 계산한 것은 아닙니다.','']
for key,r in refs.items():
    md +=[f'<a id="{key.lower()}"></a>',f'## {key} · {r["title"]}','',f'**{r["display_authors"]} ({r["year"]})** · {r["publication"]}','']
    if 'doi' in r:md +=[f'DOI: [{r["doi"]}](https://doi.org/{r["doi"]})','']
    if key=='D1':md+=['[자체 분석 보고서](C:/projects/realestate_reco/'+r['url']+')','']
    else:md +=[f'[발행기관 원문]({r["url"]})','']
    md +=['분석 대상과 영상에서 쓰는 내용: '+r['scope'],'', '해석할 때의 범위: '+r['limits'],'']
md +=['## FP59 · 실제 건축 평면 예시','',f'**{fp["complex"]} · {fp["unit_type"]}**. 한국토지주택공사(LH)의 2025년 공식 분양 자료입니다.','',f'[LH 공고]({fp["source_page_url"]}) · [공식 팸플릿]({fp["source_url"]}) · [면적 확인용 모집공고]({fp["supporting_source_url"]})','', '팸플릿 PDF 9쪽(인쇄 16·17쪽)의 평면. 면적은 모집공고 PDF 4쪽과 대조했습니다. 전용 59.9200㎡, 주거공용 24.5383㎡, 공급 84.4583㎡(두 면적의 합)입니다. 전용은 약 18.1평, 공급은 약 25.5평이며 계약면적 134.4820㎡와도 구분합니다.','', '59타입이라는 이름을 정확히 59.00㎡로 환산하지 않았습니다. 도면은 발코니 확장형 분양 계획도로 실제 시공·실측 자료가 아니고, 논문 R2·R3의 분석 단지 평면도 아닙니다. 화면에서 출처와 용도를 표시합니다. 공개 다운로드를 별도 재이용 허가로 간주하지 않았고, 현재 결과는 로컬 검토용입니다.','', '원PDF와 크롭·해시는 [평면 검증 기록](C:/projects/realestate_reco/'+str((EP/'research/readable-v2/floorplan_facts.json').relative_to(EP.parents[2])).replace('\\','/')+')에 보존했습니다.','', '## 영상의 설명 순서','', '1. 2006년 이후 실거래로 서울·경기의 회복 차이를 확인합니다.','2. 같은 인구도 가구가 나뉘면 필요한 집이 달라지는 예를 듭니다. R1로 주거비와 이동의 관계를 소개합니다.','3. 실제 59A 평면으로 면적을 이해하고, R2로 소득·자산·거주방식의 차이를 설명합니다.','4. R3로 재건축 이주와 당장 필요한 거처를, R4로 준공 시점별 전세가격 관계를 연결합니다.','5. R5의 통근 상호작용과 R6의 교통 접근성을 구분합니다.','6. 가격 차이를 설명할 후속 자료 수집과 비교 조건을 정리합니다.','', '## 재사용 음악 출처','', 'Thinking Music by Kevin MacLeod | incompetech.com | Licensed under Creative Commons: By Attribution 4.0','', '[음원 원출처](https://incompetech.com/music/royalty-free/mp3-royaltyfree/Thinking%20Music.mp3) · [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)','']
(O/'인용자료.md').write_text('\n'.join(md),'utf-8')
record={'revision':'readable-video-v2','user_instruction':'대본 가독성 개선, 개인저자 님 표기, 상세 논문 인용, 실제 대표 평면 사용, 대본 정리 후 영상제작 진행','authorization':'explicit_current_user_instruction','voice_generation':'on_hold','paid_media_calls':0,'external_transmission':False,'publication':False,'script_input':str(dest),'sources_verified_on':'2026-10-25','floorplan_example':fp,'original_script_preserved':True,'original_videos_preserved':True}
(O/'production_record.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps({'scenes':len(d['scenes']),'narration_characters':sum(len(p['text']) for s in d['scenes'] for p in s['paragraphs']),'production_text':str(dest)},ensure_ascii=False))
