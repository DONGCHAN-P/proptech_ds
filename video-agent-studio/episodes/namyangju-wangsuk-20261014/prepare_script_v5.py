from pathlib import Path
import hashlib,json
e=Path(__file__).resolve().parent
out=e/'outputs/story-review-v5';out.mkdir(parents=True,exist_ok=True)
old=(e/'writer/map-led-v4/script_v4.md').read_text(encoding='utf-8')
text=(out/'M000_series_hook.txt').read_text(encoding='utf-8')
assert len(text)==234
before,rest=old.split('## M001 —',1)
intro='''# 왕숙 토지계획도 읽기 — 전편 연결·시리즈 예고·기존 브랜드 복원 대본 v5

상태: 사용자 검토 대기. 변경은 M000 내레이션과 인트로·아웃트로 연출이다. M001 이후 내레이션은 승인된 v4 원문과 동일하며 기존 Jun 음성을 재사용한다. 새 유료 음성은 별도 승인 전 생성하지 않는다.

## M000 — 전편에서 이번 왕숙, 다음 창릉·교산으로

### 내레이션

'''+text+'''

### 화면 지시

첫 문장은 전편 「광교·동탄」의 실제 제목·대표 화면을 함께 보여준다. 전편에 예고했던 신도시 중 왕숙을 이번에 먼저 다룬다는 연결이며, 전편이 투자 추천을 보증한 것으로 표현하지 않는다. `이번 왕숙 → 다음 창릉 → 이어서 교산`은 이번에 안내하는 시리즈 순서다. 전편의 열거 순서를 그대로 인용하는 표현이 아니다.

가격 질문으로 넘어갈 때 왕숙 지도·입주 달력으로 관심을 연결한다. 음성 길이 확정 후 도입 훅 끝에 전편에서 사용한 `channel-intro-v2.mp4` 5초를 원본으로 넣고 M001로 이어간다. 새 인트로 영상·음악을 생성하지 않는다. 브랜드 배경 도시는 기존 AI 개념 컷이며 왕숙 현장 영상으로 소개하지 않는다. 흰 자막 박스는 인트로 구간에도 유지하되 내레이션이 없으면 글자만 비운다.

'''
new=intro+'## M001 —'+rest
new+='''

## v5 공통 편집 변경 — 실제 채널 인트로·아웃트로 복원

- 도입: 새 M000 훅 → 전편 5초 채널 인트로 → 기존 M001 이후 본문.
- 마무리: 기존 M009 음성 뒤에 전편 10초 `channel-outro-v2.mp4`를 붙인다. 기존 9초 음악 꼬리와 중복하지 않는다. 다음 편 창릉·이어질 교산의 명칭을 종료 화면에서 다시 안내할 수 있다.
- 브랜드 클립의 기존 음원을 사용한다. 본문 음악과 겹쳐 음량이 커지지 않도록 구간을 나누고 경계를 페이드한다.
- 50초·1분10초·2분32초·4분20초 지도 수정 요청은 기존 영상의 내용 기준 위치다. 도입 길이가 바뀌면 해당 장면의 상대 타이밍을 유지한 채 최종 시간표를 다시 제공한다.
- 본문·분양가·조건부 후보의 결론은 변경하지 않는다. 지도 용도 사전과 후반 편집은 v8 수정 범위로 계속 진행한다.
'''
(out/'script_v5.md').write_text(new,encoding='utf-8')
units=[
'지난 영상에서 예고했던 신도시 가운데,','오늘은 왕숙부터 보겠습니다.',
'다음은 창릉, 그다음은 교산을','같은 기준으로 살펴볼 예정입니다.',
'7억 안팎으로 집을 알아본다면,','이미 만들어진 동네와','앞으로 들어설 왕숙의 새집 중','무엇을 고르시겠습니까?',
'가격만큼 중요한 건,','그 돈으로 언제 어떤 생활을','할 수 있느냐겠죠.',
'오늘은 왕숙의 지도와 입주 달력을 겹쳐보고,','대체 지역과 비교해','기다릴 조건과 먼저 볼 블록을','좁혀보겠습니다.']
cursor=0;cues=[]
for i,u in enumerate(units):
 start=text.index(u,cursor);end=start+len(u);cursor=end
 cues.append({'cue_id':f'M000-V5-{i+1:02}','text':u,'lines':[u],'char_start':start,'char_end':end,'start_s':None,'end_s':None})
assert ''.join(''.join(c['text'].split()) for c in cues)==''.join(text.split())
(out/'M000_semantic_captions.json').write_text(json.dumps({'scene_id':'M000','revision':'script-v5-series-brand','cues':cues},ensure_ascii=False,indent=2),encoding='utf-8')
h=hashlib.sha256((out/'script_v5.md').read_bytes()).hexdigest()
manifest={'script_revision':'script-v5-series-brand','script_sha256':h,
 'parent_script_sha256':hashlib.sha256((e/'writer/map-led-v4/script_v4.md').read_bytes()).hexdigest(),
 'new_voice_input':'outputs/story-review-v5/M000_series_hook.txt','input_characters':234,
 'new_voice_input_sha256':hashlib.sha256(text.encode()).hexdigest(),'new_voice_chapters':['M000'],
 'unchanged_body':'M001 through M009 including M007B, 10 existing audio-v2 chapters',
 'semantic_cues_new_M000':len(cues),'body_text_exact_unchanged':True,
 'reuse_brand_intro':'video/out/channel-intro-v2.mp4','reuse_brand_outro':'video/out/channel-outro-v2.mp4',
 'paid_generation_authorized':False,'publication_authorized':False}
(out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(manifest,ensure_ascii=True))
