from pathlib import Path
import json

ROOT=Path(__file__).resolve().parent
def write(name,data):
    p=ROOT/name;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')

scenes=[
 dict(scene_id='S1',start=0,end=4,title='같은 월요일, 달라진 하루',caption='출근 후 찾던 숫자가, 이제 먼저 도착합니다.',assets=['A02','A07','A13'],video='office.mp4',color='purple',message='월요일 Before/After'),
 dict(scene_id='S2',start=4,end=7,title='질문 하나가 걷던 길',caption='질문은 길었고, 답은 늦었습니다.',assets=['A04'],video=None,color='gray',message='이슈 인지 → 요청 부서 찾기 → 검토·재질문'),
 dict(scene_id='S3a',start=7,end=10,title='09:50  요기 시그널룸',caption='② 평소에도 먼저, 지표와 신호가 도착합니다.',assets=['A01','A07'],video=None,color='purple',message='자동 브리핑'),
 dict(scene_id='S3b',start=10,end=13,title='11:00  쿼리지니',caption='① 필요한 순간 바로, 검증된 데이터로 확인합니다.',assets=['A03','A09'],video=None,color='rose',message='자연어 질의와 검증된 데이터'),
 dict(scene_id='S3c',start=13,end=16,title='14:00  또박',caption='애매한 질문이, 분석을 시작할 요건서가 됩니다.',assets=['A05','A12'],video=None,color='rose',message='요건 구체화'),
 dict(scene_id='S3d',start=16,end=19,title='16:00  본부 대시보드',caption='확인에서 판단과 실행까지, 더 가까워집니다.',assets=['A10'],video=None,color='rose',message='대시보드와 짧아진 의사결정 경로'),
 dict(scene_id='S4',start=19,end=23,title='밤과 주말에도',caption='출근하지 않은 시간에도, 같은 기준으로 흐릅니다.',assets=['A04','A08','A01'],video='pantry.mp4',color='purple',message='매시 10분 · 야간·주말 이상 알림'),
 dict(scene_id='S5',start=23,end=27,title='업무의 필요에서, 함께 만든 변화',caption='30명 · 7개 본부가 함께 만든 일상의 변화입니다.',assets=['A11','A06','A08','A10'],video='team.mp4',color='purple',message='30명 · 7개 본부 / Weekly 7회 / 2~3시간 → 5분'),
 dict(scene_id='S6',start=27,end=30,title='목적은 통제보다 안심입니다.',caption='2027, 보고서 플랫폼으로 이어집니다.',assets=['A06'],video=None,color='rose_purple',message='보안·정합성을 걱정하지 않는 환경'),
]
for s in scenes:
 s.update(narration_text='',claim_ids=['user_supplied_synopsis'],asset_ids=s['assets'],script_revision='v1-30s-text-locked',audio_revision='no-narration',timing_basis='30-second editorial lock at 30fps',status='script_locked')
write('brief.json',dict(episode_id=ROOT.name,request_type='new_video',duration=30,fps=30,width=1920,height=1080,format='무대사 · BGM · 한글 별도 합성',purpose='WBR 삽입 및 사내 단독 공유',source='Downloads/영상제작 이미지.zip',all_13_assets_required=True,style=dict(rose='① 필요한 순간 바로',purple='② 평소에도 먼저',before='무채색'),scope='제공된 시놉시스를 30초로 압축; 인물 등장 유료 API 클립; 전 이미지 사용',approvals=dict(topic='direct user request',script='user supplied synopsis with delegated 30s adaptation; prewritten text v1',budget='user explicitly selected maximum USD 3.00, tax excluded',upload=False),source_data_note='팀 규모·성과 수치는 사용자 제공 구성안이며 외부 검증하지 않음; 일정 10/14는 화면에 표시하지 않음',text_policy='한글은 생성 API에 맡기지 않고 로컬 한글 폰트로 합성; 실제 UI는 제공 이미지 원문 사용; 무대사 유지',api_plan=dict(provider='Runway',model='gen4.5',clips=3,seconds_each=5,expected_credits=180,max_credits=300,max_cash_usd=3.0,retry_max=2,reference_assets=['A02','A04','A11'],external_transmission_authorized=True),nonapplicable_defaults=['부동산 채널 브랜드/구독 CTA/지도/가격/Jun TTS; 별도 사내 영상이므로 사용하지 않음']))
write('scenes.json',dict(revision='v1-30s-text-locked',fps=30,total_frames=900,scenes=scenes))
write('state.json',dict(episode_id=ROOT.name,status='script_ready',revision='v1',topic='approved_direct',script='prewritten_v1',budget='approved_usd3',timing_locked=True,paid_generation='not_started',publication='not_authorized'))
write('decisions.json',dict(decisions=[dict(id='DI-TOPIC-v1',type='topic',decision='direct request: Data Insight internal film; all ZIP images'),dict(id='DI-SCRIPT-v1',type='script',decision='latest request:30s; people; premium quality; prewrite all Korean. Caption file locked before API calls'),dict(id='DI-BUDGET-v1',type='budget',decision='approved',max_credits=300,max_usd=3.0,tax_excluded=True,expected_credits=180,source='explicit async question reply: 최대 $3.00로 진행'),dict(id='DI-MEDIA-v1',type='production',decision='Only office photos A02/A04/A11 sent to Runway; UI screenshots preserved locally. AI people are conceptual reenactment, not actual team footage. All Hangul separately composited locally.')]))
pre=json.loads((ROOT.parents[1]/'templates/episode_preflight.json').read_text(encoding='utf8'))
pre.update(episode_id=ROOT.name,status='applied_for_internal_video',baseline=dict(current_video='independent internal Data Insight film; existing real estate final preserved',script_revision='v1-30s-text-locked',audio_revision='no-narration',bgm='original local composition planned'),story=dict(order=[s['scene_id'] for s in scenes]),visual_defaults=dict(hangul_separate_local_compositing=True,rose='needed now',purple='proactive',before='gray'),vertical_video=dict(applicable=False),channel_style_contract=dict(applicable=False,reason='User supplied independent internal corporate film style overrides property-channel defaults'))
pre['approvals']['topic'].update(status='approved_direct',decision_id='DI-TOPIC-v1');pre['approvals']['script'].update(status='user_requested_adaptation_prepared',decision_id='DI-SCRIPT-v1');pre['approvals']['budget'].update(status='approved',decision_id='DI-BUDGET-v1',credits_cap=300,cash_cap=3.0)
write('episode_preflight.json',pre)
lines=['# Data Insight — 30초 화면 문구 확정본 v1','','무대사. 아래 문구는 생성 모델이 그리지 않고 한글 폰트로 별도 합성합니다.','로즈: ① 필요한 순간 바로 / 보라: ② 평소에도 먼저 / Before: 무채색.','']
for s in scenes:
 lines.extend([f"## {s['start']:02}–{s['end']:02}초 | {s['scene_id']}",f"제목: {s['title']}",f"자막: {s['caption']}",f"보조 표시: {s['message']}",f"입력 이미지: {', '.join(s['assets'])}",''])
lines.extend(['## 표기와 근거','인물·사무실 동작은 AI 재현입니다. 실제 UI는 제공 자료를 활용합니다.','30명·7개 본부·Weekly 7회·2~3시간→5분 등은 사용자 제공 구성안의 수치입니다.','모든 원본 13개를 사용합니다. 원본 ZIP과 기존 타 영상은 보존합니다.'])
(ROOT/'script_v1.md').write_text('\n'.join(lines),encoding='utf8')
print('Prepared brief, locked script, scenes, decisions and preflight')
