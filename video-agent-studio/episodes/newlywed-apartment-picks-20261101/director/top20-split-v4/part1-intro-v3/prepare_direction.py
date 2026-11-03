"""Freeze the user's revised series intent and a reviewable intro draft only."""
from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,json,sys
D=Path(__file__).resolve().parent;E=D.parents[2];R=E.parents[2]
sys.path.insert(0,str(R))
from notify.video_decisions import create,write
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(R).as_posix()

TEXTS=[
 '우리 예산으로 집을 산다면, 어느 동네부터 찾아봐야 할까요?',
 '앞으로 이 채널에서는 신혼부부가 실제로 매매를 검토할 만한 지역과 아파트를 가격대별로 찾아드리려고 합니다.',
 '어느 지역부터 소개할지, 그 기준도 데이터에서 찾고 싶었습니다.',
 '그래서 먼저 신혼부부 통계를 통해, 신혼부부가 실제로 많이 살고 있는 지역들을 골라봤습니다.',
 '이번 편에서는 수도권 53개 구 가운데 20위부터 11위까지, 지역별 아파트 가격과 생활권을 함께 살펴보겠습니다.',
 '이 지역들을 한 차례 둘러본 뒤에는, 지역마다 더 깊이 들어가 예산별로 비교할 만한 아파트를 찾아보겠습니다.',
 '지도의 점 하나는 아파트 한 단지이고, 색은 그 단지의 거래 중위가격 구간입니다.',
 '그럼 20위 부천 원미구부터 시작하겠습니다.',
]
VISUALS=[
 {'purpose':'시청자 자신의 집 찾기 질문','motion':'큰 집 기호와 내 예산 타이포가 하나의 시선 흐름으로 연결되고, 여러 주거 후보가 정돈된다. 사진 세 칸 도입을 새 데이터 모션으로 교체한다.','anchors':['우리 예산','어느 동네'],'material':'기존 채널 서체·팔레트 + 새 코드 기반 주거 아이콘·타이포'},
 {'purpose':'채널이 앞으로 제공할 도움','motion':'지역 → 가격대 → 단지라는 세 단계가 같은 주거 오브젝트를 중심으로 이어진다. 무작위 가격·임의 매수 가능 금액은 만들지 않는다.','anchors':['신혼부부','가격대별'],'material':'새 데이터 흐름 모션'},
 {'purpose':'데이터로 지역을 선정하는 이유','motion':'한 장의 데이터 레코드가 여러 지역의 집계 열로 펼쳐지고, 카메라가 통계의 선택 기준에 집중한다.','anchors':['기준','데이터'],'material':'통계 레코드·집계 도형'},
 {'purpose':'신혼부부가 실제로 사는 지역이라는 출발점','motion':'거주 통계의 지역 레코드들이 연결되며 실제 지역명과 부부 수가 자리 잡는다. 거주 수를 매수 가능 여부로 바꾸어 표시하지 않는다.','anchors':['신혼부부 통계','많이 살고'],'material':'확정 top20.json과 수도권 구별 집계'},
 {'purpose':'이번 편에서 얻을 지역 후보','motion':'수도권 53개 구를 뜻하는 데이터 배열에서 실제 20~11위 10개 지역이 선택되고, 순위와 지역명이 연속적으로 정렬된다. 마지막에 원미구 지도 진입을 준비한다.','anchors':['53개 구','20위부터 11위','가격과 생활권'],'material':'확정 순위 + 기존 검증 지도'},
 {'purpose':'이후 시리즈로 이어지는 약속','motion':'전체 경로가 지역 후보 → 지역별 생활권 → 예산별 아파트 비교로 확장된다. 1편20~11위, 2편10~1위 이후의 개별 지역 편이라는 순서를 유지한다.','anchors':['한 차례 둘러본 뒤','예산별','아파트'],'material':'시리즈 로드맵 모션'},
 {'purpose':'시청에 필요한 지도 읽기','motion':'한 아파트 기호가 하나의 가격 점으로 바뀌고, 기존 6색 범례가 순서대로 붙는다. 학교·역·상업시설 기호를 짧게 연결한다.','anchors':['점 하나','거래 중위가격'],'material':'기존 6개 가격 구간·지도 범례'},
 {'purpose':'데이터 설명에서 실제 지역으로 자연스럽게 진입','motion':'20위 원미구 레코드가 기존 전체도·생활권 상세도의 제목과 위치로 이어진다. 실제 지도 기하·단지 점 위치는 검증 자료를 그대로 사용한다.','anchors':['20위','부천 원미구'],'material':'기존 R20 지도판'},
]

def main():
    receipt=D/'direction_receipt.json'
    if receipt.exists():print(receipt.read_text(encoding='utf-8'));return
    source=E/'director/top20-split-v4/part1-production-v1/approved_part1_scene_proposals.json'
    base=read(source);assert sha(source)=='b20616e6c8b5e128f41bc505ba79875ad90735bee38ecd16d1099739c0c1f951'
    W=E/'writer/top20-split-v4/intro-rationale-v3';W.mkdir(parents=True,exist_ok=True)
    O=R/'영상/신혼부부_지역별아파트/2부작_수정안'
    sentences=[]
    for i,(text,visual)in enumerate(zip(TEXTS,VISUALS),1):
        sentences.append({'sentence_id':f'P01-INTRO-V3-{i:02d}','text':text,'narration_text':text,
          'screen_role':'explanation','visual':visual,'statement_type':'verified_scope_or_method'if i in [4,5,7,8]else'channel_intent_or_editorial_question',
          'timing_status':'unlocked_pending_script_approval_and_actual_free_voice'})
    proposal={'revision':'intro-rationale-v3','status':'draft_for_user_direction_review','part':1,
      'source_scene_json':rel(source),'source_scene_json_sha256':sha(source),'changed_scene_ids':['P01-INTRO'],
      'unchanged_scene_ids':[s['scene_id']for s in base['scenes'][1:]],
      'scene_id':'P01-INTRO','title':'왜 신혼부부 통계로 지역을 고를까','sentences':sentences,
      'user_intent':{'channel_purpose':'신혼부부가 실제로 매매를 검토할 만한 지역과 아파트를 데이터로 찾아 소개한다.',
        'selection_basis':'신혼부부 거주 수로 소개할 지역의 출발점과 순서를 정한다.',
        'episode_role':'20~11위 지역의 실거래 가격대와 생활권을 보여주고 비교 후보를 좁힌다.',
        'series_sequence':['1편 20~11위','2편 10~1위','지역별·예산별 아파트 비교'],
        'future_affordability_check':'단지 후보 선정 시 실거래 가격, 보유자금·대출·월 부담 등 실제 예산 조건으로 구체화한다.'},
      'evidence_scope':{'ranking':'research/top20-8min-v2/top20.json','price_and_map':'research/top20-split-v4/prices/legend.json',
        'on_screen_stat_reference':'국가데이터처 · 2024.11.01 거주 기준 · 수도권 53개 구',
        'on_screen_price_reference':'전용83~85㎡ · 2026.05~10 계약 · 2026.11.03 조회 · 10월 조회일까지 신고분',
        'interpretation_rule':'거주 통계는 지역 선정에, 실거래·생활권은 이번 비교에, 실제 예산 조건은 후속 단지 선택에 각각 연결한다.'},
      'voice':'existing_free_InJoon_choice_if_script_approved','cash_cap_krw':0,'paid_generation_authorized':False,
      'new_audio_generated':False,'upload_authorized':False,'part2_production_authorized':False}
    draft=W/'intro_proposal_v3.json';write(draft,proposal)
    guide=O/'도입_방향과모션_v3.md'
    lines=['# 신혼부부 지역 소개 시리즈 · 도입 방향 v3','','## 중심 약속','',
      '**신혼부부가 자기 예산으로 집을 찾을 때, 어느 지역부터 살펴볼지와 어떤 아파트를 비교할지를 데이터로 안내한다.**','',
      '지역 선정은 신혼부부 거주 통계에서 시작하고, 이번 편은 실거래 가격대와 생활권을 연결해 후보를 좁힙니다. 이어지는 개별 지역 편에서 예산별 단지 비교로 구체화합니다.','',
      '## 시리즈 연결','','1. 1편: 20~11위 지역의 가격과 생활권.','2. 2편: 10~1위 지역을 같은 기준으로 비교.','3. 이후: 지역별로 들어가 예산별 아파트 후보와 실제 예산 조건을 세밀하게 비교.','',
      '## 새 도입 원고','','브랜드 인트로는 첫 질문 뒤에 배치하는 안입니다. 낭독·브랜드·모션의 실제 길이는 새 원고 확정 뒤 측정합니다. 현재 시간은 미확정입니다.','']
    for i,(text,visual)in enumerate(zip(TEXTS,VISUALS),1):lines.extend([f'### {i}. {visual["purpose"]}','',text,'',f'화면: {visual["motion"]}',''])
    lines+=['## 화면에서 함께 제시할 기준','',
      '- 거주 통계: 국가데이터처, 2024년 11월 1일 거주 기준, 수도권 53개 구.',
      '- 가격: 전용83~85㎡, 2026년5~10월 계약, 11월3일 조회. 10월은 조회일까지 신고된 거래.',
      '- 점 하나는 위치가 확인된 한 단지. 색은 거래 중위가격의 기존6구간.',
      '- 학교·역·상업시설 기호는 기존 검증 지도와 연결.',
      '', '## 제작 적용 범위','',
      '교체 범위는 P01-INTRO입니다. 지역 본문10장면과 기존 결말3문장은 원문을 보존했습니다. 새 도입의 낭독과 화면 시점은 대본 확인 뒤 정합니다. 이번 단계에서는 새 음성·MP4를 생성하지 않았습니다. 유료 생성·외부 파일 전송·업로드·2편 제작 권한은 추가하지 않습니다.','']
    guide.write_text('\n'.join(lines),encoding='utf-8')
    full=O/'1편_20-11위_대본_v3_도입수정안.md'
    full_lines=['# 신혼부부 거주 TOP20 · 1편20~11위 · 대본v3 도입 수정안','',
      '검토용 초안입니다. 도입을 채널의 집 찾기 취지와 후속 지역·예산별 단지 소개에 맞춰 고쳤습니다. 지역 본문과 결말은 승인된 v2 원문입니다.','',
      '## 왜 신혼부부 통계로 지역을 고를까','']
    for text in TEXTS:full_lines.extend([text,''])
    for s in base['scenes'][1:]:
        full_lines.extend(['## '+s['title'],''])
        for v in s['sentences']:full_lines.extend([v['text'],''])
    full.write_text('\n'.join(full_lines)+'\n',encoding='utf-8')
    protected=[{'scene_id':s['scene_id'],'sentences':[v['text']for v in s['sentences']]}for s in base['scenes'][1:]]
    body_digest=hashlib.sha256(json.dumps(protected,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    cursor=0;reader=full.read_text(encoding='utf-8')
    for s in protected:
        for text in s['sentences']:
            pos=reader.find(text,cursor);assert pos>=cursor;cursor=pos+len(text)
    gate=create(E.name,'script','1편 도입v3: 신혼부부가 실제로 매매를 검토할 지역·아파트를 데이터로 소개한다는 취지 → 신혼부부 거주 통계로 지역 선정 → 이번20~11위 생활권·가격 비교 → 후속 지역별·예산별 단지 소개. 새 도입8문장과 모션 방향 검토. 본문·결말80문장 보존, 무료InJoon/현금0원 유지. 새 음성·업로드·2편 제작은 미진행.')
    gate.update(artifact_revision='top20-split-v4/intro-rationale-v3',part=1,changed_scene_ids=['P01-INTRO'],
      artifacts=[{'path':rel(p),'sha256':sha(p)}for p in [draft,full,guide]],scope='new part1 intro spoken text and screen direction only',
      cash_cap_krw=0,paid_generation_authorized=False,upload_authorized=False,external_file_export_authorized=False)
    write(R/'output/video_decisions/decisions'/f"{gate['id']}.json",gate);write(D/'script_decision.json',gate)
    for p in [R/'output/video_decisions/decisions/697b13162078.json',E/'director/top20-split-v4/part1-production-v1/completed_decision_v4.json']:
        old=read(p);old.update(status='revision_requested',revision_scope='P01-INTRO',
          user_feedback='0~5초,10~18초 모션 개선 및 채널의 신혼부부·현실 예산·데이터 기반 지역 선정 취지를 도입에 반영',
          replaced_by_script_decision_id=gate['id']);write(p,old)
    state=read(E/'state.json')
    state['review_baseline_part1_v4']={k:state.get(k)for k in ['active_video','active_video_sha256','active_audio','active_audio_sha256','active_timing','active_source_project','active_qa']}
    state.update(phase='awaiting_part1_intro_v3_script_review',active_intro_revision='intro-rationale-v3',
      active_script_proposal=rel(draft),active_intro_review_file=rel(full),active_intro_direction=rel(guide),
      pending_decision_id=gate['id'],active_timing_status='v4_baseline_retained_new_intro_unlocked',active_new_intro_audio_generated=False,
      active_upload_authorized=False,updated_at=datetime.now(timezone.utc).isoformat())
    state['active_approval_status'].update(script='body_v2_approved_intro_v3_pending:'+gate['id'],completed='intro_revision_requested_on_697b13162078',pre_upload='not_reached_part1')
    state['active_parts'][0].update(status='intro_script_revision_pending',intro_script_decision_id=gate['id'])
    write(E/'state.json',state)
    result={'status':'direction_and_intro_draft_ready_for_user_review','script_decision_id':gate['id'],
      'new_intro_sentences':8,'unchanged_body_outro_sentences':sum(len(s['sentences'])for s in base['scenes'][1:]),
      'unchanged_body_sha256':body_digest,'reader':rel(full),'direction':rel(guide),'new_audio':False,'new_video':False,
      'paid_calls':0,'cash_cap_krw':0,'part2_production':False}
    write(receipt,result);print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
