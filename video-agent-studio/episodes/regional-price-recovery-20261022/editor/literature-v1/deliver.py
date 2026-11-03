"""Finalize local review delivery only after independent encoded-media QA."""
from pathlib import Path
import json,hashlib,zipfile,os
from datetime import datetime,timezone
EP=Path(__file__).resolve().parents[2];ROOT=EP.parents[2];OUT=EP/'outputs/literature-visual-v1';P=OUT/'project';D=EP/'director/literature-visual-v1';Q=EP/'qa/literature-visual-v1'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def dump(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
    return h.hexdigest()
T=read(P/'timing.json');R=read(OUT/'checks/assembly_receipt.json');E=read(OUT/'checks/encoded/evidence.json');qa_path=Q/'final_findings.json';qa=read(qa_path)
assert E['decoded_successfully'] and E['video_sha256']==R['sha256']
assert qa['summary']['critical_open']==0 and qa['summary']['required_open']==0
qa_video_sha=qa.get('video_sha256') or qa.get('checked_revision',{}).get('video_sha256')
assert qa_video_sha==R['sha256'],'QA must bind the exact encoded MP4'
assert sha(ROOT/R['path'])==R['sha256']
assert abs(T['body_duration']-T['last_caption_end']-3)<.001
script=EP/'outputs/literature-video-v1/내레이션_초안.md';assert sha(script)==T['script_sha256']
for path,digest in read(D/'protected.json').items():assert sha(ROOT/path)==digest,path
now=datetime.now(timezone.utc).isoformat()
guide=OUT/'검토안내.md'
guide.write_text(f'''# 논문 인용형 화면 검토본 v1

제작일 2026-10-23. 사용자 승인 대본 SHA256 `{T['script_sha256']}`.

- 영상: **9분 28.27초 · 1920×1080 · 30fps · 8장면**
- 전체 대본에 해당하는 41문단·97개 임시 자막을 배치했습니다.
- **내레이션 없음.** 기존 브랜드 영상과 기존 BGM만 재사용했습니다. Jun 음성 생성 보류를 유지했습니다.
- 자막·화면의 길이는 텍스트 기반 임시 배분입니다. 실제 음성·발음·자막 정렬은 확정하지 않았습니다.
- 마지막 임시 자막이 끝난 뒤 3초 동안 그림을 유지하고 기존 아웃트로로 연결합니다. 실제 마지막 발화 기준 검수는 아닙니다.

## 이번에 만든 화면

1. 2006년 이후 서울·경기 자체 가격 경로와 2021Q4 고점 이후 비교
2. 같은 인구와 달라지는 가구 수, 주거비와 이동의 관찰된 관련성
3. 소득·자산·면적·자가와 임차의 선택 분기
4. 가락시영 주요 이주 구간과 대체 거주의 시간 공백
5. 가상 준공·멸실·순증 계산과 입주 시점
6. 통근 연결 지수·직장 접근성의 차이와 대기·환승 구조
7. 면적·비용·날짜·직장 조건을 통과하는 선택지의 개념도
8. 현재 관측과 후속 검증 과제의 구분

자체 집계·연구 결과·가상 계산·개념도·종합 해석·후속 과제는 서로 구분했습니다. 가상의 아이콘 수와 경로를 실제 지역 수치로 읽지 않도록 표시했습니다. 실제 이동 목적지 지도·개별 매수자 자산·집값 원인별 기여율은 이번에 계산하지 않았습니다.

## 검수 범위

HyperFrames의 41문단 표본 실행·배치·대비 검사에서 오류 0건을 확인했습니다. 편집 트랙 밀도 관련 정보성 경고는 기록에 보존했습니다. 실제 MP4는 전체 영상 프레임 디코드를 통과했으며 {E['evidence_frame_count']}개 표본 프레임으로 문단과 장면 경계를 검토했습니다. 독립 QA의 critical·required 미해결 항목은 0건입니다.

위 범위는 **연속 재생·실제 청취·음성 정렬 검수와 구분**합니다. 이번 작업에서 연속 재생과 실제 청취를 수행했다고 주장하지 않습니다.

후속 편집 권고 2건을 남겼습니다. 도입 8–12.5초의 가격 곡선 되그리기, 일부 중간 장 전환 직전의 빈 자막 배경입니다. 필수 수정과 구분한 연출 정돈 항목이며 세부 프레임은 완성검수 JSON에 있습니다.

## 로컬 파일과 재현

- `논문영상_검토본.mp4`: 이번 화면 검토본
- `논문영상_자막_임시.srt`: 텍스트 배분에 맞춘 자막
- `논문영상_프로젝트.zip`: HyperFrames 본문 프로젝트·대본·인용 근거
- `작업폴더/outputs/literature-visual-v1/project`: 실제 프로젝트 원본
- Studio: http://localhost:3027/#project/project — 현재 PC에서 서버가 실행되는 동안 접근 가능

본문 프로젝트는 HyperFrames CLI **0.8.181**, 로컬 GSAP와 Pretendard를 사용했습니다. 실제 제작 명령·입력 해시·타이밍·합성 명세는 `editor/literature-v1` 및 이번 outputs의 checks에 남겼습니다. 전체 브랜드 합성 입력은 `reused_assets.json`에 원본 경로와 SHA를 보존했습니다.

## 출처와 자산

논문·보고서 6개의 정확한 링크·대상 기간·표본·해석 범위는 승인 대본의 각주와 `인용근거.json`에 있습니다. 원문 도판을 복제하지 않고 자체 도형과 문장으로 설명했습니다. 기존 챕터 배경은 AI 개념 자산으로 실제 지역·공식 계획의 증거가 아닙니다. 새 이미지·음성·음악 유료 생성은 하지 않았습니다.

Thinking Music by Kevin MacLeod | incompetech.com | Licensed under Creative Commons: By Attribution 4.0
https://creativecommons.org/licenses/by/4.0/

기존 v3 대본·가격 그래프 검토 영상·원천 자료는 보존했습니다. 이번 결과는 로컬 검토용이며 외부 전송·업로드를 수행하지 않았습니다.
''',encoding='utf8')
clean='\n\n'.join(b['narration_text'] for s in T['scenes'] for b in s['beats'])+'\n';(OUT/'낭독대본.txt').write_text(clean,encoding='utf8')
package=OUT/'논문영상_프로젝트_v1.zip'
with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for f in P.rglob('*'):
        if f.is_file() and not any(part in ('.hyperframes','node_modules','renders') for part in f.relative_to(P).parts):z.write(f,'project/'+f.relative_to(P).as_posix())
    for f in (EP/'outputs/literature-video-v1').glob('*'):
        if f.is_file() and f.suffix in ('.md','.json'):z.write(f,'script-and-evidence/'+f.name)
    z.write(guide,'검토안내.md');z.write(qa_path,'QA/final_findings.json');z.write(OUT/'reused_assets.json','reused_assets.json');z.write(OUT/'asset_provenance.json','asset_provenance.json');z.write(D/'script_approval.json','verification/script_approval.json');z.write(OUT/'checks/render_inputs.json','verification/render_inputs.json');z.write(OUT/'checks/caption_integrity.json','verification/caption_integrity.json')
with zipfile.ZipFile(package) as z:assert z.testzip() is None
artifacts=[ROOT/R['path'],OUT/'previews/literature_visual_v1.srt',guide,package,script,qa_path]
manifest={'revision':'literature-visual-v1','status':'local_visual_review_complete_narration_on_hold','at_utc':now,'video_sha256':R['sha256'],'script_sha256':T['script_sha256'],'duration':R['video_duration'],'scenes':8,'paragraphs':41,'captions':97,'provisional':True,'narration_present':False,'voice_generation_calls':0,'paid_calls':0,'external_delivery_sent':False,'youtube_upload':False,'continuous_playback':False,'actual_listening':False,'technical':R,'qa':qa_path.relative_to(ROOT).as_posix(),'encoded_evidence':(OUT/'checks/encoded/evidence.json').relative_to(ROOT).as_posix(),'artifacts':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in artifacts]}
dump(OUT/'delivery_manifest.json',manifest)
state=read(EP/'state.json')
if state.get('script_revision')=='v3':state['previous_script_v3']={k:state.get(k) for k in ('script_revision','script_file','script_sha256','script_status','script_decision_id')}
if state.get('production_revision')=='production-v1-jun':state['previous_production_v1_jun']={k:state.get(k) for k in ('production_revision','production_review_video','production_render','production_review_qa','production_delivery_manifest')}
state.update(stage='literature_visual_v1_local_review_ready_narration_on_hold',script_revision='literature-video-v1',script_file=script.relative_to(ROOT).as_posix(),script_sha256=T['script_sha256'],script_status='approved_for_visual_production_by_explicit_reply',script_decision_id='regional-literature-script-v1-20261023',production_revision='literature-visual-v1',production_review_video=R['path'],production_render={'mode':'visual-review','status':'complete_for_local_visual_review','video_sha256':R['sha256'],'duration':R['video_duration'],'expected_duration_seconds':R['video_duration'],'paid_calls':0,'timing_locked':False,'narration_present':False},production_review_qa=qa_path.relative_to(ROOT).as_posix(),production_delivery_manifest=(OUT/'delivery_manifest.json').relative_to(ROOT).as_posix(),next_script_status='approved_for_visual_production',literature_visual_revision='literature-visual-v1',literature_visual_review=R['path'],literature_visual_delivery_manifest=(OUT/'delivery_manifest.json').relative_to(ROOT).as_posix(),literature_visual_qa=qa_path.relative_to(ROOT).as_posix(),literature_visual_timing_locked=False,updated_at=now)
state.setdefault('qa_history',[]).append(qa_path.relative_to(EP).as_posix())
assert state['budget_status']=='voice_generation_deferred_by_user';dump(EP/'state.json',state)
dec=read(EP/'decisions.json');completion={'id':'regional-literature-visual-v1-completed-20261023','status':'review_ready_not_upload_approval','basis':'User authorized visuals for approved literature script; local completion receipt','video_sha256':R['sha256'],'script_sha256':T['script_sha256'],'duration':R['video_duration'],'narration_present':False,'qa_required_open':0,'at_utc':now};dec['decisions']=[d for d in dec['decisions'] if d['id']!=completion['id']]+[completion];dump(EP/'decisions.json',dec)
pre=read(EP/'episode_preflight_literature_visual_v1.json');pre['status']='local_visual_review_complete_narration_pending';pre['baseline'].update(current_video=R['path'],sha256=R['sha256'],script_revision='literature-video-v1',audio_revision='existing_BGM_only_no_narration');pre['approvals']['completed'].update(status='review_ready_not_user_acceptance',decision_id=completion['id'],artifact_hashes={'video':R['sha256']});pre['qa'].update(actual_encoded_frames=f'{E["evidence_frame_count"]} sampled frames',full_decode='pass_video_frames',continuous_playback_performed=False,actual_listening_performed=False,required_open_issues=0,semantic_caption_original_text_match='pass_with_explicit_display_mapping',actual_speech_alignment='not_performed_no_narration',last_caption_plus_three_seconds='verified',evidence_paths=[(OUT/'checks/encoded/evidence.json').relative_to(ROOT).as_posix(),qa_path.relative_to(ROOT).as_posix(),(OUT/'checks/caption_integrity.json').relative_to(ROOT).as_posix()]);pre['representative_style_QA']='pass_text_and_sampled_encoded_frames_not_continuous_playback';pre['release']['longform']={'path':R['path'],'status':'local_visual_review_not_uploaded'};dump(EP/'episode_preflight_literature_visual_v1.json',pre)
shelf=read(ROOT/'config/video_shelf.json');entry=next(e for e in shelf['entries'] if e['workspace']==EP.relative_to(ROOT).as_posix());files=entry['files']
old_review='video-agent-studio/episodes/regional-price-recovery-20261022/outputs/production-v1-jun/previews/full_visual_review_v1.mp4'
files['이전검토영상_가격그래프.mp4']=old_review
files['이전대본_v3.md']='video-agent-studio/episodes/regional-price-recovery-20261022/outputs/script-review-v3/script_v3.md'
for alias,path in [('논문영상_검토본.mp4',ROOT/R['path']),('검토영상.mp4',ROOT/R['path']),('논문영상_자막_임시.srt',OUT/'previews/literature_visual_v1.srt'),('논문영상_검토안내.md',guide),('검토안내.md',guide),('논문영상_프로젝트.zip',package),('대본.md',script),('낭독대본.txt',OUT/'낭독대본.txt'),('논문영상_완성검수.json',qa_path)]:files[alias]=path.relative_to(ROOT).as_posix()
entry['status']='논문 인용형 화면 검토본 v1 · 9분28초 · 8장면 · 음성 없이 기존 BGM · 임시 타이밍 · 독립 화면 QA 필수0 · 새 대본 화면 제작 승인 · 기존 v3·MP4 보존'
dump(ROOT/'config/video_shelf.json',shelf)
plan=ROOT/'docs/superpowers/plans/2026-10-23-literature-video-visuals.md';plan.write_text(plan.read_text(encoding='utf8').replace('- [ ]','- [x]'),encoding='utf8')
print(json.dumps({'status':state['stage'],'video':R['path'],'duration':R['video_duration'],'qa_required_open':0,'artifacts':len(artifacts),'zip_verified':True,'external_send':False},ensure_ascii=False))
