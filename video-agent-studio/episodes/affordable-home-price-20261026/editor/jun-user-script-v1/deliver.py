"""Write scoped design, alignment contract and handoff from verified local artifacts."""
import ast,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build import HERE,EP,ROOT,OUT,PROJECT,read,sha,dump,write,PLAN,MANIFEST,CAPTIONS,CALC,BASE

def main():
    plan=read(PLAN);manifest=read(MANIFEST);caps=read(CAPTIONS);qa=read(OUT/'qa_receipt.json')
    current=[OUT/'S13_preview_silent_v1.mp4',OUT/'S18_S19_preview_silent_v1.mp4',OUT/'S21_preview_silent_v1.mp4']
    combined=OUT/'representative_preview_silent_v1.mp4';assert combined.is_file() and qa['media'][-1]['decoded_video_frames']==1050
    dup=[]
    for id in ['S18_S19','S21']:
        a=OUT/f'{id}_preview_silent_v1.mp4';b=OUT/f'{id}_preview_silent_v2.mp4';assert sha(a)==sha(b)
        dup.append({'v1':str(a),'v2':str(b),'sha256':sha(a),'byte_identical':True,'preserved':True})
    dump(HERE/'header_false_positive_closed.json',{'status':'closed_false_positive','reason':'Parent corrected earlier visual impression using native pixel bounds. Encoded brand y32..51, preview status y34..53. v2 files are byte-identical duplicates of v1. No defect or further header repair is claimed.','evidence':str(OUT/'header_bounds_receipt.json'),'duplicate_versions':dup})
    # The combined reel already contains identical video bytes; relabel its exact input aliases.
    write(OUT/'concat_current.txt',''.join("file '"+p.as_posix()+"'\n" for p in current))
    for r in qa['media']:
        for d in dup:
            if r['path']==d['v2']:r['path']=d['v1'];r['identical_preserved_alias']=d['v2']
    qa['status']='technical_pass_and_sampled_visual_review_complete_preview_only'
    qa['visual_review']={'actual_encoded_sample_frames':9,'combined_boundary_frames_generated':8,'combined_boundary_visual_review':'see producer_review.json','full_size_representatives_viewed':['S13','S18_S19','S21'],'small_size_contact_viewed':True,'baseline_encoded_frames_viewed':[270,320,400],'continuous_playback':False,'actual_listening':False,'independent_QA':'parent Euler agent; separate findings are not authored by editor'}
    dump(OUT/'qa_receipt.json',qa)
    outputs={'clips':[str(p) for p in current],'combined':str(combined),'duration_s':35,'pngs':[str(OUT/f'{id}_representative_v1.png') for id in ['S13','S18_S19','S21']],'contact_sheet':str(OUT/'contact_sheet.png'),'small_contact':str(OUT/'three_representatives_small.png')}
    dump(HERE/'current_deliverables.json',outputs)
    inputs=read(HERE/'input_versions.json');inputs['local_tools']={'hyperframes':'0.8.181','chrome_source':'existing cached headless shell 152.0.7977.30','ffmpeg':'existing housing-choice media-bin/ffmpeg.exe','ffprobe':'existing video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe','node':'existing installation'}
    inputs['project_files']=[{'path':str(p),'sha256':sha(p)} for p in sorted(PROJECT.rglob('*')) if p.is_file() and '.hyperframes' not in p.parts]
    inputs['baseline_public_Jun_video']={'path':str(BASE.parent/'renders/measured-jun-v1/housing_choice_jun_v1.mp4'),'sha256':sha(BASE.parent/'renders/measured-jun-v1/housing_choice_jun_v1.mp4'),'sampled_seconds':[270,320,400],'use':'style reference only; no old scene graphics or amounts reused'}
    dump(HERE/'input_versions.json',inputs)
    refs={k:{'path':str(p),'sha256':sha(p)} for k,p in [('manifest',MANIFEST),('caption_plan',CAPTIONS),('scene_plan',PLAN)]}
    incoming={'schema_version':'jun-scene-alignment-v1','timing_locked':False,'timing_basis':None,'source_doc_sha256':plan['source_sha256'],**refs,'voice':{'name':'Jun','revision':None},'audio_units':[{'audio_unit_id':f'C{i:02}','path':None,'sha256':None,'duration_s':None} for i in range(1,8)],'scenes':[]}
    paragraphs={p['paragraph_id']:p for p in manifest['paragraphs']}
    for s in plan['scenes']:
        incoming['scenes'].append({'scene_id':s['scene_id'],'paragraph_ids':s['paragraph_ids'],'audio_unit_id':f'C{s["chapter"]:02}','audio_start_s':None,'audio_end_s':None,'characters':[{'paragraph_id':id,'spoken_sha256':paragraphs[id]['spoken_sha256'],'expected_codepoints':len(paragraphs[id]['spoken_text']),'start_s':[],'end_s':[]} for id in s['paragraph_ids']],'beats':[{'beat_id':f'{s["scene_id"]}.b{i+1:02}','anchor_original':b['anchor'],'start_s':None,'end_s':None} for i,b in enumerate(s['beats'])],'captions':[{'cue_id':c['cue_id'],'display_lines':c['display_lines'],'start_s':None,'end_s':None} for c in caps['cues'] if c['scene_id']==s['scene_id']]})
    dump(HERE/'incoming_alignment.template.json',incoming)
    dump(HERE/'issue_TIMING_INPUT_CONTRACT.json',{'issue_id':'JUN-S-TIMING-CONTRACT','scene_ids':[s['scene_id'] for s in plan['scenes']],'problem':'Actual Jun audio and measured timings are not supplied; preview timing remains unlocked.','evidence':{'manifest':refs['manifest'],'caption_plan':refs['caption_plan']},'proposal':'Narration fills incoming_alignment.template.json using actual character alignment and exact caption display_lines. Parent provides scene-level timing lock; editor emits body EDL.','impact':'No full 31-scene expansion or final sync before measured input; this is a production prerequisite, not a new user permission request.','next_owner':'parent / narration','direct_peer_message_tool_available':False})
    write(HERE/'ASSEMBLY_CONTRACT.md','''# Jun 장면 정렬 입력 계약

`incoming_alignment.template.json`은 S01~S31·48문단·101개 원문 앵커·156개 자막을 포함합니다. 초 단위 값은 전부 미확정입니다. `R001` 계열 입력은 받지 않습니다.

1. 실제 Jun 생성본의 7개 장 파일을 `audio_units`에 경로·SHA256·실측 길이로 연결합니다. `voice.revision`, 실제 정렬 근거와 `timing_locked=true`를 채웁니다. 전사/문자 정렬 원본도 narration 담당이 보존합니다.
2. 각 장면의 `audio_start_s` / `audio_end_s`는 해당 장 오디오 내 절대 초입니다. `characters`, `beats`, `captions`의 초는 **장면 시작=0**인 로컬 초입니다. 장 오디오 시각에서 장면 시작 시각을 빼서 변환합니다.
3. 문자 배열은 manifest 각 문단의 `spoken_text`의 **Unicode codepoint** 순서입니다. 문단 사이 구분자는 배열에서 제외하고 원본 정렬에서 별도 추적합니다. 음절·숫자 낭독 변환을 원문 인덱스와 혼동하지 않습니다. `spoken_sha256`을 대조합니다.
4. 앵커는 `scene_plan.json`의 원문 문자열과 beat_id를 그대로 유지합니다. 문자 정렬과 display_mapping으로 최초 발화 위치를 연결하며 불일치는 수동 확인 대상으로 남깁니다. 글자 수 비례로 시각을 추정하지 않습니다.
5. 자막은 `caption_plan.json`의 `cue_id`와 `display_lines`를 그대로 소비합니다. 임의 문자 분할·금액 단위 분리는 하지 않습니다. 원문·낭독·표시문 해시는 별도로 연결합니다.
6. `assembly_contract.py 입력.json --out <editor 내부 경로>`는 해시·31개 장면 순서·48문단/156큐·문자 수·실측 구간 범위를 검사하고 `output_kind=body_edl`, `renders_video=false`인 본문 EDL을 만듭니다. 이 어댑터는 영상을 렌더하거나 TTS를 호출하지 않습니다.

본편 제작/렌더는 기존 사용자 요청으로 승인된 범위입니다. 대표 검수와 정책 확인은 내부 제작 조건이며 새 사용자 승인 지점이 아닙니다. 유료 음성 예산 답변은 총괄이 처리합니다.

현재 S13·S18/S19·S21만 화면 구현됐습니다. 대표 시안의 임의 초를 실제 음성에 재사용하지 않습니다. 나머지 장면은 계약/스토리보드 상태입니다. 장면별 본문 길이를 확정한 뒤 자막·모션·컷·독립 이미지 챕터·브랜드를 조립합니다. S18/S19는 현재 하나의 검토 클립이지만 실제 EDL에서는 두 scene_id를 유지합니다.

마지막 실제 발화 후 3초(기존 꼬리 무음 포함)에 아웃트로를 시작합니다. 원본 음성의 존재·정렬만으로 발음/자연스러움 검수를 통과시키지 않습니다.
''')
    write(HERE/'BRIEF.md','''---
workflow: general-video
flow: automation
storyboard: yes
---

사용자 DOCX 원문과 Jun을 사용하는 매매가격 계산 편. 이번 담당 범위는 대표 세 유형의 실제 무음 HyperFrames 시안과 S01~S31 연결 계약이다. 음성·본편 타이밍은 미확정이며 유료 서비스·전체 본편 렌더·업로드는 실행하지 않는다. 창작 질문을 다시 열지 않고 마스터 가이드와 최신 사용자 지시를 적용한다.

핵심 질문: 통장 현금이 어떤 계산을 거쳐 주택가격 예산이 되는가?
핵심 발견: 준비금을 분리한 자기자금에 대출을 합산하며 개인 한도 4억원 이후에는 대출과 월 상환이 같아진다.
시청자 행동: 잔금 현금·확인한 대출·감당할 월 원리금을 적는다.
''')
    write(HERE/'DESIGN.md','''# 대표 화면 설계 및 스타일 대조

1920×1080, 30fps. 공개 housing-choice Jun 편 ch03의 Pretendard 400/600/700 로컬 파일·GSAP을 복사하고 해시를 기록했다. 실제 MP4 270/320/400초 프레임을 추출해 자금 분리·막대·고정 흰 자막의 기능을 비교했다. 원본 프레임/수치/완성 차트는 새 영상에 사용하지 않았다.

아이보리 #f6f4ef, 네이비 #173348, 자기자금 파랑 #286cda, 대출 골드 #c29a44, 여유/잔여 초록 #3f8f7f. 제목 x80/y142/43px 굵게, 브랜드 x88/y28/22px, 본문 y265~835, 자막 x96/y876/w1728/h124/40px, 출처 x96/y1020/20px. 기준편의 서체·제목·자막 위계를 계승한다. 작은 출처와 조건은 화면의 증명 역할을 설명하는 최소 정보다.

| 유형 | 입력 → 과정 → 결과 | 비례와 모션 | 대표 파일 |
|---|---|---|---|
| S13 | 1억−2000만원 → 8000만원÷30% → 선택 예시2.66억 | 1억=250px, 8000만원=200px, 대출1.86억=465px. 준비금이 분리되고 계산식 후 결과 등장 | S13_preview_silent_v1.mp4 |
| S18/S19 | 자기자금2.6/3.5/4.4억 + 대출4억 → 집값6.6/7.5/8.4억 | 1억=120px. 대출480px에서 정지. 세 월 상환 점을 같은 높이에 연결. 주택가격·월 금액은 별개 영역 | S18_S19_preview_silent_v1.mp4 |
| S21 | 세금1016.4만원 + 복비/VAT290.4만원 → 합계1306.8만원, 잔여2693.2만원 | 4000만원=720px, 비용235.224px/잔여484.776px. 항목 등장→합계→미배분 잔여. 임의 견적 배정 없음 | S21_preview_silent_v1.mp4 |

GSAP의 좌측 기준 scaleX fill·원문 앵커별 순차 등장·결과 유지 패턴을 사용한다. 정지 제목 슬라이드로 계산 과정을 대체하지 않는다. 레지스트리 animated-bar-chart를 로컬 검색했지만 다운로드 EACCES로 설치하지 못했다. 기존 GSAP으로 조건부 계산을 직접 구현했고 전역 의존성을 바꾸지 않았다. 외부 feedback 전송도 하지 않았다.

이미지 챕터는 계산 사실과 분리한다. transaction-costs.png는 거래 비용, bank-limits.png는 대출 장 분위기에만 연결한다. 이 두 파일의 구도 검토는 **총괄이 수행했다고 전달**했으며 이 편집자가 새로 봤다고 기록하지 않는다. 은행 모형은 실제 장소 근거가 아니다. 다른 장은 guide_validation.json 후보를 문맥·구도 검토 후 각각 선택한다. 이 세 계산 화면을 31장면에 반복 배치하지 않는다.

본편에는 독립 이미지 챕터와 주택/생활 맥락이 들어간다. 이미지의 글자/정확한 수치는 별도 레이어이며 AI 배지·반복 부정형 푸터를 넣지 않는다. 상단 ‘무음 시안·타이밍 미확정’ 표기는 검토용이고 본편 조립 시 제거한다.
''')
    lines=['# S01~S31 스토리보드','', '초 단위는 전체 미확정. 세 대표 유형 이외 화면은 아직 구현하지 않았다. 원문/발화 앵커는 scene_templates/*.json에 보존했다.','', '| 장면 | 메시지 | 주자료/동작 | 현재 상태 |','|---|---|---|---|']
    for s in plan['scenes']:
        status='실제 대표 시안' if s['scene_id'] in ['S13','S18','S19','S21'] else '설계/입력 계약'
        lines.append(f'| {s["scene_id"]} | {s["message"]} | {s["material_type"]} · {len(s["beats"])}개 발화 연결 | {status} |')
    write(HERE/'STORYBOARD.md','\n'.join(lines)+'\n')
    write(HERE/'placement_guide.md','''# 실제 검토 파일 배치

모두 무음·1920×1080·30fps. 아래 시간은 **35초 검토 합본 안의 추천 위치**이며 본편 권장 시각은 실제 Jun 정렬 이후 확정한다.

| 실제 파일명 | 합본 추천 시간 | 길이 | 자료 유형 | 레이어/전환 |
|---|---:|---:|---|---|
| S13_preview_silent_v1.mp4 | 00:00 | 10초 | 계산 모션그래픽 | 현금/준비금 분리→계산식→주택가격. 자막·출처 별도 HTML 레이어 |
| S18_S19_preview_silent_v1.mp4 | 00:10 | 13초 | 개인 한도 비교 모션 | 대출4억에서 fill 정지→다른 현금 행→동일 월 원리금. 두 scene_id 보존 |
| S21_preview_silent_v1.mp4 | 00:23 | 12초 | 비용 영수증/비례 막대 | 세금→중개보수→합계→미배분 잔여. 잔여는 항목별 임의 금액 배정 없음 |
| representative_preview_silent_v1.mp4 | 00:00 | 35초 | 위 세 클립 연결본 | 동일 코덱/타임베이스 확인 후 stream copy, 하드컷10/23초 |

클립 사이 트랜지션은 별도 효과 없는 컷이다. 본편 자막은 narration/caption_plan.json display_lines와 실제 큐 시간을 사용하고, 그림·수치·자막·출처가 겹치지 않게 유지한다. 이동/줌이 필요하면 배경에만 적용한다. 본편에서 검토 전용 상단 상태 문구는 제거한다.

v2는 상단 잘림 오탐 조사 중 생성됐으며 두 파일 모두 v1과 SHA256이 같은 중복본이다. 삭제하지 않고 보존하되 현재 기준은 v1이다. 업로드는 실행하지 않았다.
''')
    commands=[]
    for id in ['S13','S18_S19','S21']:
        commands.append({'scene_id':id,'argv':['node',str(Path('C:/Users/e2ken/AppData/Roaming/npm/node_modules/hyperframes/bin/hyperframes.mjs')),'render',str(PROJECT/id),'--output',str(OUT/f'{id}_preview_silent_NEW_VERSION.mp4'),'--fps','30','--quality','looks','--workers','2']})
    dump(HERE/'render_commands.json',{'build':['tools/python311/python.exe','-B','-X','utf8',str(HERE/'build.py')],'render':commands,'environment':{'DO_NOT_TRACK':'1','HYPERFRAMES_NO_UPDATE_CHECK':'1','HYPERFRAMES_NO_AUTO_INSTALL':'1','PATH_prepend':['existing housing-choice private-production-v1/media-bin','existing video/node_modules/@remotion/compositor-win32-x64-msvc']},'no_global_upgrade':True,'concat':{'argv':['existing ffmpeg.exe','-f','concat','-safe','0','-i',str(OUT/'concat_current.txt'),'-c','copy','-movflags','+faststart','NEW_VERSION.mp4']},'warning':'Choose a new output version. Do not overwrite existing MP4s.'})
    for p in [HERE/'build.py',HERE/'assembly_contract.py',HERE/'finish.py',HERE/'deliver.py']:ast.parse(p.read_text(encoding='utf8'))
    # The null timing template must reject before any normalization/render.
    import assembly_contract
    try:assembly_contract.validate(HERE/'incoming_alignment.template.json')
    except AssertionError:contract_test='correctly_rejects_unlocked_template'
    else:raise AssertionError('Unlocked timing incorrectly accepted')
    dump(HERE/'preflight_receipt.json',{'scope':'master guide and episode_preflight adapted to representative-only editor work','voice_selection':'latest Jun request supersedes old free/direct-recording defaults','script':'exact user DOCX wording retained','source_doc_sha256':plan['source_sha256'],'source_paragraphs':48,'scene_contracts':31,'caption_cues':156,'actual_representative_types':3,'source_template_AST':'pass','alignment_template_guard':contract_test,'full_film_authorized_by_existing_user_request':True,'new_permission_gate_added':False,'full_film_not_rendered_because':'actual Jun timing is unavailable; no expansion before representative inspection','maps_newtown_preflight':'not applicable to these calculational visuals','independent_QA':'parent Euler owns separate record','tts_calls':0,'global_installs':0,'uploads':0})
    dump(HERE/'handoff.json',{'task_id':'JUN-USER-SCRIPT-V1-REPRESENTATIVES','status':'representatives_delivered_timing_unlocked','artifacts':{'current':str(HERE/'current_deliverables.json'),'combined':str(combined),'project':str(PROJECT),'storyboard':str(HERE/'STORYBOARD.md'),'assembly_contract':str(HERE/'ASSEMBLY_CONTRACT.md'),'placement':str(HERE/'placement_guide.md')},'input_versions':str(HERE/'input_versions.json'),'verification':{'receipt':str(OUT/'qa_receipt.json'),'header_issue':'closed_false_positive; v2 byte-identical to v1','scope':'35s / 1050frames, 1080p30, audio0, decode/PTS/CLI checks; 9 encoded samples + small contact viewed','continuous_playback':False,'actual_listening':False},'unresolved':['Actual Jun alignment pending; use incoming_alignment.template.json.','Parent Euler independent QA remains separate.'],'affected_scenes':['S13','S18','S19','S21'],'next_owner':'parent / narration / Euler QA','full_film_expanded_or_rendered':False})
    print(json.dumps({'handoff':str(HERE/'handoff.json'),'combined':str(combined),'current':'all three v1 originals; v2 duplicates preserved','status':'ready_for_parent_QA'}))
if __name__=='__main__':main()
