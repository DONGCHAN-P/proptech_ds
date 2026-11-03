from pathlib import Path
import sys,json,re,hashlib,datetime,shutil
H=Path(__file__).resolve().parent;EP=H.parents[1];ROOT=EP.parents[2];sys.path.insert(0,str(ROOT))
from notify import video_decisions as gates
OUT=EP/'outputs/script-review-v5';OUT.mkdir(parents=True,exist_ok=True)
for round_name in ['round1','round2']:
 r=json.loads((H/(round_name+'_receipt.json')).read_text(encoding='utf8'));assert r['exit_code']==0 and not r['is_error'] and r['output_chars']>500
draft=(H/'codex_draft_v5.md').read_text(encoding='utf8')
draft=draft.replace('# 창릉 대본 v5 · Codex 협의 초안','# 창릉 대본 v5 · Codex × Claude 구성 합의안')
draft=draft.replace('상태: Claude 1차 검토 전 작성한 제안. 미확정. 기존 영상·음성·대본 보존. 사실은 v4와 script-v4-addendum의 확인 범위만 사용한다.','상태: 사용자 검토 대기·미확정. Claude Code 실제 2회 검토의 조건을 Codex가 수용·반영했다. 이는 구성 합의이며 사용자 승인·팩트 전수 검증·음성 예산·렌더·업로드 승인이 아니다. 기존 영상·음성·대본은 보존한다. 사실은 v4와 script-v4-addendum의 확인 범위만 사용하며 주변 전체 공급량은 미확보다.')
old_opening='7억 후반에서 8억 후반의 창릉 새집을 기다릴까요, 이미 교통과 상권이 있는 원흥·삼송의 기존 아파트를 고를까요?'
new='창릉의 새집을 기다릴까요, 이미 교통과 상권이 있는 원흥·삼송의 기존 아파트를 고를까요?'
assert old_opening in draft;draft=draft.replace(old_opening,new)
draft=draft.replace('기존 가족 달력 자산 재사용.','기존 완성본 10:52~11:24 구간과 교체하며 병렬 삽입하지 않는다. 이 시간은 기존 영상의 위치 식별용이고 새 음성 타임코드로 승계하지 않는다. 기존 가족 달력 자산 재사용.')
draft=draft.replace("공급 장의 범위 표제: '확인된 공고의 입주 달력'.","공급 장에서 시청자가 직접 읽는 표 제목: '확인된 공고 입주달력(주변 전체 아님)'.")
(OUT/'script_v5.md').write_text(draft,encoding='utf8')
chunks=re.findall(r'## (M\d+[^\n]*)\n\n### 낭독\n\n([\s\S]*?)(?=\n### 화면 지시)',draft);assert len(chunks)==10
narration='\n\n'.join(text.strip() for _,text in chunks)
(OUT/'narration_v5.txt').write_text(narration,encoding='utf8')
agreement='''# Claude 협업 합의 기록

실제 Claude Code 2.1.168로 2회 검토했다. 1차에는 기존 완성본 SRT와 v4 낭독, 짧은 시리즈 맥락을 전달했다. Codex의 수정안과 반론을 작성한 뒤 2차에 다시 전달했다. 전체 대화·자격증명·.env는 입력에 넣지 않았고 외부 모델의 파일/셸/MCP 도구는 비활성화했다.

## 논의와 결론

| 쟁점 | Claude 의견 | Codex 답변·최종 반영 |
|---|---|---|
| 큰 구성 | 기존 생활권 대 새집을 전체의 중심으로 유지 | 수용. 9,700만원 독립 훅 삭제, 가격→생활→결론에서만 회수 |
| 가족 달력 | 1차에서 기존 영상에 없는 신규 장으로 판단 | 실제 SRT 10:52~11:24를 제시해 정정. 기존 구간을 보완·대체하고 병렬 추가하지 않음 |
| 오프닝 가격 범위 | 2차에서 7억 후반~8억 후반도 삭제 권고 | 수용. 첫 문장은 생활 선택 질문만 남김 |
| S6 | 공급 장에서 한번 낭독 | 수용. 'S5가 창릉 전체 첫 입주'라는 오해 방지, 교통 장 반복 없음 |
| 공급 범위 | 3후보 부분집계를 주변 전체로 오해할 위험 | 표 제목을 '확인된 공고 입주달력(주변 전체 아님)'으로 명시 |
| 정확 가격 | 음성은 근사값·의미, 표는 정확값 | 수용. 3가격 비교표 및 특정 타입·층·옵션 조건 유지 |
| 전편 연결 | 광교동탄 기준→왕숙 완성 시차→창릉 기존 생활권 | 도입과 결론에 반영, 전편 소개 장문·중복 CTA 줄임 |

Claude 2차 판정은 위 3가지 수정 조건을 충족하면 편집 구성 합의를 권고한다는 내용이다. Codex가 세 조건을 모두 반영했다. 수정 후 Claude가 별도 3차 원고 전체를 승인했다고 표현하지 않는다. 이 합의는 사용자 승인 및 사실 QA를 대신하지 않는다.

## 남은 사실 확인

- 창릉·주변 전체 연도별 공급량 미확보. 세 후보 2,277세대와 S6 보조사례만 확인한 범위로 한정.
- 열차 24/28/49분은 2022.08 시행 공개표 사례. 현재 집-직장 실측값이 아님.
- 입주·개교·철도는 기존 출처의 예정/목표이며 최신 확정일 전수 검증을 새로 수행하지 않음.
- 웹 지도에 새로 연결한 자료는 위치 보조자료다. 기존 창릉 WFS733개의 geometry/properties 일치는 별도 확인했다.

## 보존 기록

writer/claude-consensus-v5/round1_input.txt, round1_review.md, round1_result.json, round1_receipt.json, codex_response_round1.md, codex_draft_v5.md, round2_input.txt, round2_review.md, round2_result.json, round2_receipt.json. CLI의 total_cost_usd는 API 환산 추정치이며 구독 외 실제 청구 증거가 아니다. 실제 사용량은 각 receipt에 보존했다. 추가 결제 0원을 검증한 청구서라고 주장하지 않는다.
'''
(OUT/'consensus_record.md').write_text(agreement,encoding='utf8')
shutil.copy2(H/'scene_reuse_plan.md',OUT/'scene_reuse_plan.md')
changes=f'''# v5 변경 요약

- 시리즈 연결: 광교·동탄의 5기준 → 왕숙의 완성 시차 → 창릉의 기존 생활권 접점.
- 기존 완성본 뼈대를 유지하고 v4의 가격·조건부 결론을 압축 반영.
- 첫 문장에서 가격범위를 빼고 ‘창릉 새집 대 원흥·삼송 기존집’ 질문으로 시작.
- 가족 달력은 기존 구간과 교체. S6는 공급 장에서 한 번만 설명.
- 공급 표는 확인된 공고 부분집계로 명시. 주변 전체 공급분석이 아님.
- 낭독 {len(narration):,}자, 10장. v4 기록 6,566자 대비 약 {(1-len(narration)/6566)*100:.1f}% 감소. 시간은 새 음성 전 미확정.
- 기존 v5r2 영상과 모든 원본 보존. 신규 음성·이미지·렌더·업로드 실행 없음.
- 사용자 대본 검토용이며 사실 보강 공백과 새 음성 비용은 별도 확인.
'''
(OUT/'changes_v5.md').write_text(changes,encoding='utf8')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
artifacts={str(p.relative_to(EP)):sha(p) for p in [OUT/'script_v5.md',OUT/'narration_v5.txt',OUT/'consensus_record.md',OUT/'scene_reuse_plan.md',OUT/'changes_v5.md']}
old=ROOT/'output/video_decisions/decisions/30a358949599.json';prior=json.loads(old.read_text(encoding='utf8'))
existing=OUT/'review_decision.json'
if existing.exists():decision=json.loads(existing.read_text(encoding='utf8'))
else:decision=gates.create(EP.name,'script','창릉 대본 v5: Codex×Claude 실제 2회 구성 검토 후 오프닝·가족달력 교체·공급 범위 표시 조건 반영. 대본/화면 지시만 검토하며 유료 생성·업로드는 포함하지 않음.')
decision.update(script_revision='script-v5',scope='script_and_scene_direction_only',artifact_hashes=artifacts,paid_generation_authorized=False,upload_authorized=False,claude_review_rounds=2)
gates.write(ROOT/'output/video_decisions/decisions'/f"{decision['id']}.json",decision);gates.write(existing,decision)
if prior['status']=='pending':prior.update(status='superseded',superseded_by=decision['id'],reason='사용자 시리즈 연계 재정리 및 Claude 협업 요청으로 v5 검토안 생성');gates.write(old,prior)
statep=EP/'state.json';state=json.loads(statep.read_text(encoding='utf8'));state.update(stage='script_review_pending',draft_script_revision='script-v5',draft_script_status='review_pending',draft_script_path='outputs/script-review-v5/script_v5.md',draft_script_sha256=sha(OUT/'script_v5.md'),pending_gate='script',pending_decision_ids={'script':decision['id']},paid_generation_authorized=False,voice_generation_hold=True,active_tasks=[])
state['claude_collaboration']={'rounds':2,'path':'writer/claude-consensus-v5','status':'conditional_editorial_agreement_conditions_applied','user_approval':False};gates.write(statep,state)
dp=EP/'decisions.json';log=json.loads(dp.read_text(encoding='utf8'))
if not any(d.get('id')==decision['id'] for d in log['decisions']):log['decisions'].append(decision)
for d in log['decisions']:
 if d.get('id')==prior['id']:d.update(prior)
gates.write(dp,log)
check={'chapters':len(chunks),'narration_chars':len(narration),'claude_calls_succeeded':2,'conditions_applied':{'opening_price_removed':old_opening not in draft and new in draft,'replace_household_segment':'기존 완성본 10:52~11:24 구간과 교체' in draft and '병렬 삽입하지 않는다' in draft,'supply_scope_title':'확인된 공고 입주달력(주변 전체 아님)' in draft},'script_sha256':sha(OUT/'script_v5.md'),'decision_id':decision['id'],'fact_reverification':'not performed; existing claim basis inherited','paid_media_generation':False}
assert all(check['conditions_applied'].values());gates.write(OUT/'validation.json',check);print(json.dumps(check,ensure_ascii=False))
