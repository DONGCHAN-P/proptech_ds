from pathlib import Path
import re,json,hashlib
E=Path('video-agent-studio/episodes/goyang-changneung-20261015');Q=E/'qa/revision-v7'
s=(E/'outputs/script-review-v7/script_v7.md').read_text(encoding='utf-8')
p=json.loads((E/'writer/revision-v7/narration_packet.json').read_text(encoding='utf-8'))
v=json.loads((E/'writer/revision-v7/validation.json').read_text(encoding='utf-8'))
pr=json.loads((E/'writer/revision-v7/scene_proposals.json').read_text(encoding='utf-8'))
narr=[{'scene_id':m.group(1),'text':m.group(2).strip()} for m in re.finditer(r'## (M\d{3}).*?\n### 낭독\n(.*?)\n### 화면 지시',s,re.S)]
norm=lambda t:re.sub(r'\s+','',t)
packet={x['scene_id']:x['text'] for x in p['scenes']}
tot=sum(len(x['text']) for x in narr);school=next(x['text'] for x in narr if x['scene_id']=='M005')
sha=hashlib.sha256((E/'outputs/script-review-v7/script_v7.md').read_bytes()).hexdigest()
r={'revision':'script-v7','status':'passed_for_user_script_review','script_path':'outputs/script-review-v7/script_v7.md','checked_revision':sha,'required_unresolved':[],'approved_for_generation':False,'scene_count':len(narr),'sequence':[x['scene_id'] for x in narr],
'checks':{
'price_growth_and_candidate_focus':'pass: 진입가격·현재 대체재·접근·공급과 조건부 수요, S4 가격수준 후보와 상승률 구분',
'facts_vs_hypotheses':'pass: 현재 관측·공식 계획일과 향후 수요·후보 판단 구분; 목표가격/수익률 없음',
'regulatory_start_events':'pass_inherited_evidence: S4 전매3년=당첨자발표일, 거주의무3년=거주의무개시일; 입주+3년 매도일 산정 없음; S3 LH환매 구분',
'spoken_style':'pass: 자연스러운 구어체; 필수 문체 재작성 없음',
'school_weight':'pass: M005 보조 정착수요, 후보 이유는 진입가격·접근·기존수요 중심',
'personal_move_calendar':'removed: M008 장면·낭독 삭제',
'caveats':'pass: 필요한 비교조건을 해당 위치에 설명, 반복 면책 독립장 없음',
'price_comparisons':'pass: 776598000/790380000/873329000원, 약9700/8300만원 차액, 공고연도/타입/확장 구분',
'resale_order_and_samples':'pass: 11.275/9.2/8.5/8.45/8.375/7.45억 내림차순, 거래6/11/3/17/20/11건, 3건 참고표본 명시',
'source_placement':'S01 수정확인: 하단 의미자막 아래 별도 고정 출처영역',
'chapter_transition':'S01 수정확인: 읽기시간 있는 독립 번호챕터카드, 우상단 상시라벨과 별개',
'current_commute':'pass: 숫자 전 계산법·대표점·08:00/조회일·대기/환승·현재교통 설명; 15값 기존근거 범위',
'packet_text_sync':all(norm(x['text'])==norm(packet[x['scene_id']]) for x in narr),
'script_hash_sync':sha==v['script_sha256']==pr['script_sha256']},
'duration':{'narration_characters':6456,'prior_Jun_characters':6372,'prior_pcm_duration_s':786.48,'estimated_narration_s':796.8,'estimated_final_s':814.8,'chapter_card_dwell_extra_not_counted':True,'over10min_estimate':True,'actual_v7_duration':'음성 미생성·실측 미검증'},
'school_character_share':round(len(school)/tot,4),
'resolved':[{'issue_id':'QAV7-S01','status':'closed_verified_script_and_scene_proposals','change':'출처 자막아래/독립 번호챕터카드 명시'}, {'issue_id':'QAV7-S02','status':'not_a_factual_defect_editorial_omission','evidence':'CN7-S4-PRECOMP의 LH2022 단지회고27:1은 qualified 검증값; 분모/유형 확대불가. 최신가이드도 단일보조 허용','disposition':'총괄 최신 결정대로 최종ceb9a4e 초안에서 낭독/화면 보류 유지; 연구출처팩 보존'}],
'limits':['사용자 대본 승인 아님; 유료/음성/게시 승인 없음','불변 가격·좌표·규제 원문 재조사 없이 기존 검수와 연구패킷 근거 범위 승계','보존 공식PDF 재취득 실패: 최신 정정본 일치 새 검증으로 승격하지 않음','MP4·실제음성·청취·연속재생 검수 아님; visual-review-v7 대기','원문이미지 상업영상 재사용 권리 미확인 상태는 연구패킷 한계로 유지'],
'next_owner':'director/user_script_gate; editor visual review pending'}
(Q/'script_review.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'sha':sha,'scene_count':len(narr),'packet_sync':r['checks']['packet_text_sync'],'hash_sync':r['checks']['script_hash_sync'],'school_share':r['school_character_share'],'estimate_s':814.8,'required_open':0},ensure_ascii=False))
