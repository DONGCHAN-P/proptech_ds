from pathlib import Path
import hashlib, json, math, sys

e = Path(__file__).resolve().parent
repo = e.parents[2]
sys.path.insert(0, str(repo))
from notify.video_decisions import create, write

out = e / 'outputs/story-review-v6'
out.mkdir(exist_ok=True)
text = '지난 영상에서 예고했던 신도시, 오늘은 왕숙부터 보겠습니다. 지난 영상이 궁금하시다면, 지금 보이는 영상도 함께 확인해보세요. 다음은 창릉, 그다음은 교산입니다. 두 지역도 궁금하시다면 구독해주세요. 꼼꼼한 조사와 알기 쉬운 지도로, 집을 고르는 데 도움이 되는 영상으로 찾아뵙겠습니다. 그럼 7억 안팎의 왕숙 새집은 기다릴 만할까요? 토지계획도와 입주 달력을 겹쳐보고, 대체 지역과 비교해 먼저 볼 블록을 좁혀보겠습니다.'
units = ['지난 영상에서 예고했던 신도시,','오늘은 왕숙부터 보겠습니다.','지난 영상이 궁금하시다면,','지금 보이는 영상도 함께 확인해보세요.','다음은 창릉, 그다음은 교산입니다.','두 지역도 궁금하시다면 구독해주세요.','꼼꼼한 조사와 알기 쉬운 지도로,','집을 고르는 데 도움이 되는 영상으로','찾아뵙겠습니다.','그럼 7억 안팎의 왕숙 새집은','기다릴 만할까요?','토지계획도와 입주 달력을 겹쳐보고,','대체 지역과 비교해','먼저 볼 블록을 좁혀보겠습니다.']
old = (e/'outputs/story-review-v5/script_v5.md').read_text(encoding='utf-8')
old_text = (e/'outputs/story-review-v5/M000_series_hook.txt').read_text(encoding='utf-8')
new = old.replace('대본 v5', '대본 v6').replace('## v5 공통', '## v6 공통').replace(old_text, text)
direction = '''
### v6 전편 확인·후속편 구독 안내 화면

- “지난 영상이 궁금하시다면”부터 전편 실제 파일 `video/out/newtown-v14-release.mp4`의 대표 화면을 영상 카드로 보여준다. ‘지난 영상 · 광교·동탄’ 문구를 함께 표시한다. 실제 업로드 링크·카드 연결이 검증되기 전에는 클릭 가능한 것처럼 보이는 버튼이나 가짜 URL을 넣지 않는다.
- 전편 카드가 충분히 보인 뒤 ‘이번 왕숙 → 다음 창릉 → 그다음 교산’ 시리즈 화면으로 전환한다. 구독 안내는 내레이션과 같은 시점에 단정한 작은 구독 그래픽으로 보여준다.
- 꼼꼼한 조사·이해하기 쉬운 지도라는 제작 약속으로 표현한다. 투자 성과를 약속하지 않는다.
- 전편 화면의 원래 음성은 재생하지 않고 새 Jun 내레이션만 사용한다. 의미 단위 자막과 고정 흰 자막바를 유지한다.
- 새 M000 끝 → 기존 5초 인트로 → 기존 M001 본문 순서 및 기존 10초 아웃트로 복원은 유지한다.

'''
new = new.replace('## M001 —', direction+'## M001 —', 1)
(out/'M000_series_hook.txt').write_text(text,encoding='utf-8')
(out/'script_v6.md').write_text(new, encoding='utf-8')
cursor=0; cues=[]
for i, unit in enumerate(units):
    start=text.index(unit,cursor); cursor=start+len(unit)
    cues.append(dict(cue_id=f'M000-V6-{i+1:02}',text=unit,lines=[unit],char_start=start,char_end=cursor,start_s=None,end_s=None))
assert ''.join(text.split()) == ''.join(''.join(x['text'].split()) for x in cues)
write(out/'M000_semantic_captions.json',dict(scene_id='M000',revision='script-v6-series-cta',cues=cues))
h=hashlib.sha256((out/'script_v6.md').read_bytes()).hexdigest()
th=hashlib.sha256(text.encode()).hexdigest()
n=len(text); reserve=math.ceil(n*.2); cap=n+reserve
manifest=dict(script_revision='script-v6-series-cta',script_sha256=h,new_voice_input_sha256=th,input_characters=n,correction_reserve=reserve,hard_cap_characters_and_credits=cap,additional_cash_usd=0,body_audio_reuse_count=10,new_generation_calls=0,paid_generation_authorized=False)
write(out/'manifest.json',manifest)
receipt=out/'approval_decisions.json'
if not receipt.exists():
    script=create(e.name,'script',f'대본 v6: 전편 실제 화면과 확인 안내, 왕숙→창릉→교산 시리즈·구독 안내 추가. 새 M000 {n}자. 본문10개음성 및 기존5초인트로/10초아웃트로 재사용. Exact script SHA256 {h}.')
    budget=create(e.name,'budget',f'Only new M000 {n} chars SHA256 {th}, script SHA256 {h}. Jun/eleven_v4 initial{n}+reserve{reserve}, hardcap{cap} submitted chars AND actual credits; included credits only, additional cash USD0. No automatic retry/overage/topup/new paid images/cloud render. Prior exact-v5 approval not transferred. Requires matching script approval and fresh balance check.')
    common=json.loads((e/'decisions.json').read_text(encoding='utf-8'))
    for obj in (script,budget):
        obj.update(version='script-v6-series-cta',source_script_sha256=h)
        write(repo/'output/video_decisions/decisions'/f"{obj['id']}.json",obj)
        common['decisions'].append(obj)
    write(e/'decisions.json',common)
    write(receipt,dict(script_sha256=h,script_decision_id=script['id'],budget_decision_id=budget['id']))
d=json.loads(receipt.read_text(encoding='utf-8'))
state=json.loads((e/'state.json').read_text(encoding='utf-8'))
state.update(stage='v8_visual_ready_hook_v6_review',script_revision_target='script-v6-series-cta',pending_gate='script_and_budget',pending_decision_ids=dict(script=d['script_decision_id'],budget=d['budget_decision_id']),new_paid_generation_authorized=False)
write(e/'state.json',state)
print(json.dumps(dict(**manifest,**{k:v for k,v in d.items() if k!='script_sha256'})))
