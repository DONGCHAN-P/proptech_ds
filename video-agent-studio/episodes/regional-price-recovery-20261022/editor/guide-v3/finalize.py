from pathlib import Path
import json,hashlib,datetime,shutil,subprocess,os,sys

EP=Path(__file__).resolve().parents[2];ROOT=EP.parents[2]
O=EP/'outputs/guide-v3';P=O/'project';D=EP/'director/guide-v3';D.mkdir(parents=True,exist_ok=True)
def dump(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),'utf-8')
def read(p):return json.loads(p.read_text('utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(ROOT).as_posix()
def ts(s):return f'{int(s)//60:02}:{int(s)%60:02}'

def capture():
    paths=[ROOT/'config/current_video.json',EP/'outputs/readable-video-v2/대본.md',EP/'outputs/readable-video-v2/regional_literature_readable_v2.mp4',EP/'outputs/literature-video-v1/내레이션_초안.md']
    dest=D/'protected_baseline.json'
    if not dest.exists():dump(dest,{rel(p):sha(p) for p in paths})
    if not (D/'state_before.json').exists():shutil.copy2(EP/'state.json',D/'state_before.json')
    print('Protected baseline and episode state recorded; no delivery aliases changed.')

def started():
    paths=[p for p in P.rglob('*') if p.is_file() and '.hyperframes' not in p.relative_to(P).parts]
    dump(D/'render_input_manifest.json',{rel(p):sha(p) for p in paths})
    state=read(EP/'state.json')
    state['pending_production']={'revision':'guide-v3','status':'full_render_in_progress','guide':rel(D/'design.md'),'preview_qa':rel(EP/'qa/guide-v3/preview_review.json'),'current_ready_version_preserved':'readable-video-v2','narration_on_hold':True}
    dump(EP/'state.json',state)
    print(json.dumps({'frozen_inputs':len(paths),'ready_v2_preserved':True,'pending':'guide-v3'}))

def main():
    v=read(O/'checks/verification.json');t=read(P/'timing.json');a=read(O/'assets.json')
    video=O/'regional_guide_v3.mp4';script=O/'대본.md'
    qa=EP/'qa/guide-v3/video_review.json'
    assert read(qa)['required_open_issues']==0
    assert read(EP/'qa/guide-v3/preview_review.json')['required_open_issues']==0
    assert read(O/'checks/check_receipt.json')['ok'] is True
    assert v['full_decode'] and sha(video)==v['sha256']
    protected=read(D/'protected_baseline.json')
    for path,h in protected.items():assert sha(ROOT/path)==h,path
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    sem=read(O/'semantic_units.json')
    (O/'낭독대본.txt').write_text('\n\n'.join(p['text'] for s in sem['scenes'] for p in s['paragraphs'])+'\n','utf-8')
    frameinfo=read(O/'checks/encoded_frames.json')
    planunit=next(u for u in t['units'] if 'FP59' in u['asset_ids'])
    picked=min(frameinfo,key=lambda f:abs(f['pts_seconds']-5-(planunit['start']+planunit['end'])/2))
    shutil.copy2(picked['file'],O/'미리보기.png')
    rows=['# 전체 화면 구성 · 제작 가이드 반영 v3','','시간표는 내레이션 생성 전 임시 길이입니다. 의미 단위는 문장·절·완결구절을 먼저 정했으며 시간 추정과 구분합니다.','','| 구간 | 장면 | 화면 |','|---|---|---|','| 00:00–00:05 | 기존 채널 인트로 | 브랜드·기존 음악 |']
    for s in t['scenes']:
        rows.append(f'| {ts(s["start"]+5)}–{ts(s["start"]+8.5)} | {s["id"]} 챕터 | 독립 이미지 · {s["title"]} |')
        seen=set()
        for u in s['units']:
            if u['paragraph_id'] in seen:continue
            seen.add(u['paragraph_id']);group=[x for x in s['units'] if x['paragraph_id']==u['paragraph_id']]
            modes=list(dict.fromkeys(x['mode'] for x in group))
            rows.append(f'| {ts(u["start"]+5)}–{ts(group[-1]["end"]+5)} | {u["paragraph_id"]} | {u["screen_headline"]} · {", ".join(modes)} |')
    rows+=['','마지막 자막 이후 3초 동안 본문을 유지한 뒤 기존 아웃트로 10초로 이어집니다. 자막 박스는 본문·챕터·큐 사이에 계속 유지하며, 브랜드와 마지막 무음 CTA에서만 숨깁니다.','', '[의미 단위별 상세 표](의미단위_대본과_표기표.md) · [논문 상세 인용](인용자료.md)']
    (O/'화면구성.md').write_text('\n'.join(rows)+'\n','utf-8')
    used=['# 이미지 사용 목록 · v3','','새 이미지 9개는 내장 image_gen으로 생성했습니다. 실제 현장이나 논문 분석 단지의 사진이 아닌 개념 이미지이며 화면에 표시했습니다. 외부 유료 미디어 API와 음성 API는 호출하지 않았습니다. 내장 생성의 계정 청구 상태는 조회하지 않았습니다.','','| 용도 | 이미지 | 파일 |','|---|---|---|']
    for c in a['chapters']:
        path=Path(c['image_file'])
        used.append(f'| {c.get("scene_id",c.get("id",""))} 독립 챕터 | {c.get("asset_id","")} | `{path.name}` |')
    for x in a['generated']:
        used.append(f'| 새 생성 | {x.get("asset_id",x.get("id",""))} | `{Path(x["local_file"]).name}` |')
    used+=['','챕터 8개 이미지 해시가 모두 다릅니다. 본문 사진 5개는 각각 한 주제에서만, 최대 12초 사용했습니다. 집 단면 예시는 가구 분리 장에, 실제 LH 59A 평면은 주거 공간 장에만 사용했습니다.','', '원본 경로·생성 프롬프트·SHA-256·실제 사용 구간: `assets.json`, `image_prompts.json`, `project/timing.json`.']
    (O/'이미지_사용목록.md').write_text('\n'.join(used)+'\n','utf-8')
    report=f'''# 제작 가이드 재적용 · 전체 검토본 v3

[전체 영상](regional_guide_v3.mp4) · [대본](대본.md) · [의미 단위별 표기표](의미단위_대본과_표기표.md) · [논문 상세 인용](인용자료.md)

{ts(v['duration'])} · 1920×1080 · 30fps. 기존 BGM과 브랜드를 연결한 **내레이션 없는 화면 검토본**입니다. ElevenLabs Jun 생성 보류는 유지했습니다. 자막 시간은 음성에 맞춰 확정한 값이 아닙니다.

이전 v2는 일부 집·건물 그림을 다른 주제로 반복했고, 독립 이미지 챕터와 새 이미지 생성이 빠졌습니다. 자막도 의미 단위를 먼저 결정하는 기준을 충분히 적용하지 못했습니다. 이전 기술 검수의 통과를 이 제작 가이드 전체의 충족으로 해석하지 않습니다.

| 사용자 지침 | 이번 반영 | 확인 근거 |
|---|---|---|
| 같은 이미지 반복하지 않기 | 챕터 이미지 8개 모두 다름. 본문 사진 5개를 장 사이에 재사용하지 않음 | 이미지 해시·사용 구간·실제 MP4 표본 |
| 필요한 이미지 생성 | 원룸·가계 재무·이사·공사·환승 본문 5개와 챕터 4개, 총 9개 새 생성 | 로컬 원본·프롬프트·프로젝트 복사·실제 화면 |
| 주제 넘어갈 때 이미지 | 8장 시작마다 3.5초 독립 이미지와 번호·주제 | 각 챕터와 본문 진입 경계 전후 프레임 |
| 의미 단위에 맞는 대본·화면 | 원문 30문단을 162개 문장·절·완결구절로 먼저 나눔. 자막과 강조 대상을 함께 배정 | 30문단 원문 복원·수치/이름 보호·명시적 표기 변환 4개·독립 검수 |

실제 MP4 독립 검수에서 발견한 순증 재고 단위 ‘가구’를 ‘채’로 수정하고 해당 공급 챕터를 재렌더링했습니다. 결과는 ‘순증 200채·1,000채’이며 대본·수치·시간표는 유지했습니다.

작은 월셋집 설명은 작은 임차 칸을, 독립은 집 1→2와 컵 3→2+1을, 철거·준공은 시점에 따른 순증 계산을 강조합니다. 재건축 이주 연구의 OLS와 IV 결과를 구분하고, 통근 연결과 사업체 수의 결과도 별도 화면으로 보여줍니다. 자료에서 확인한 가격 경로와 향후 검증할 지역별 원인 기여율을 구분합니다. AI 이미지는 실제 위치·연구 단지·원인의 증거로 사용하지 않았습니다.

저자 ‘님’ 표기와 논문·보고서 6개 상세 인용은 유지했습니다. LH 남양주왕숙 A-1 59A 실제 계획 평면으로 전용 59.92㎡(약18.1평)와 공급84.46㎡(약25.5평)을 구분합니다. 논문 표본 단지의 평면은 아닙니다. 원천 PDF와 출처는 보존했고 도판 재이용 범위는 게시 준비 때 별도 확인 대상입니다.

검수 범위는 원문·표기·자산 사용 검사, 전체 디코딩, 실제 MP4의 장별 표본과 주요 경계입니다. 전편 연속 재생과 실제 청취는 수행하지 않았습니다. 음성·유료 외부 미디어 API·외부 전송·업로드는 실행하지 않았습니다. 기존 MP4와 대본은 보존했습니다.

음악: Thinking Music by Kevin MacLeod | incompetech.com | CC BY 4.0
'''
    (O/'검토안내.md').write_text(report,'utf-8')
    (O/'가이드_반영내역.md').write_text(report,'utf-8')
    statepath=EP/'state.json'
    if not (D/'state_before.json').exists():shutil.copy2(statepath,D/'state_before.json')
    state=read(statepath)
    state.update(stage='guide_v3_local_full_visual_review_ready_narration_on_hold',updated_at=now,script_revision='guide-v3',script_status='semantic_resegmentation_and_local_visual_production_authorized_by_current_user_instruction',script_file=rel(script),script_sha256=sha(script),script_decision_id='regional-guide-v3-user-instruction-20261025',production_revision='guide-v3',qa_file=rel(qa),audio_status='existing_bgm_only_narration_user_hold',timing_locked=False,pre_upload_status='not_authorized',budget_status='voice_generation_deferred_by_user',full_review_scope='Semantic authoring and independent review, eight image chapters, nine generated assets, encoded samples and full decode. No actual listening or continuous playback.')
    state['production_render']={'mode':'visual-review','status':'complete_for_local_visual_review','video_file':rel(video),'video_sha256':sha(video),'duration':v['duration'],'frames':v['frames'],'resolution':v['resolution'],'fps':30,'narration':False,'actual_listening':False,'continuous_playback':False,'verification':rel(O/'checks/verification.json')}
    state.pop('pending_production',None)
    state.setdefault('qa_history',[]).extend(rel(EP/f'qa/guide-v3/{n}.json') for n in ['semantic_review','preview_review','video_review'])
    dump(statepath,state)
    auth={'id':'regional-guide-v3-user-instruction-20261025','episode':EP.name,'gate':'script','status':'approved_to_do_requested_work','approval_type':'explicit_instruction_to_reapply_guides_and_make_full_video','created_at':now,'video_revision':'guide-v3','user_instruction':'확인해보고 다시 반영해서 만들어줘','scope':'semantic segmentation, topic-specific image generation and full local visual production','artifacts':{rel(script):sha(script),rel(video):sha(video)},'approval_basis':'Current instruction authorizes the requested corrective work. It is not user acceptance of these newly produced artifacts.','old_version_approval_inherited':False,'narration_generation_authorized':False,'external_paid_media_api_authorized':False,'native_image_generation':'requested_and_run_9_images_billing_not_queried','external_send_authorized':False,'upload_authorized':False,'result_acceptance':'not_yet_reviewed_by_user'}
    dump(D/'authorization.json',auth);dump(ROOT/'output/video_decisions/decisions/regional-guide-v3-user-instruction-20261025.json',auth)
    pre=read(ROOT/'video-agent-studio/templates/episode_preflight.json')
    pre.update(status='completed_local_visual_review_voice_on_hold',episode_id=EP.name)
    pre['baseline'].update(previous_video=rel(EP/'outputs/readable-video-v2/regional_literature_readable_v2.mp4'),current_video=rel(video),sha256=sha(video),script_revision='guide-v3',audio_revision='existing_bgm_only_Jun_hold')
    pre['approvals']['script'].update(decision_id=auth['id'],status='current_user_instruction_to_reapply_guide_and_produce',artifact_hashes={'script':sha(script)})
    pre['approvals']['budget'].update(status='voice_hold_no_external_paid_media_api_native_images_requested_billing_unknown')
    pre['approvals']['completed']['status']='local_artifact_delivered_user_acceptance_pending'
    pre['approvals']['pre_upload']['status']='not_authorized'
    pre['story']['order']=['price_difference','households','floorplan_and_tenure','relocation','net_supply','commute','feasible_choices','next_tests']
    pre['visual_defaults'].update(independent_image_chapters=8,chapter_image_unique_hashes=8,new_generated_images=9,body_photo_cross_chapter_reuse=False,semantic_units_authored_before_timing=162)
    pre['change_control'].update(changed_scene_ids=[s['id'] for s in t['scenes']],single_timing_lock=False,package_frozen_before_hash=True,issues=[],superseded_rules=['Topic-specific guide reapplication authorized in current user instruction; no change to narration hold.'])
    pre['qa'].update(actual_encoded_frames='sampled_all_chapters_major_boundaries_and_changed_semantic_cases',all_cut_boundaries_no_flash='sampled_before_at_after_each_chapter_and_body_entry_not_continuous_playback',semantic_caption_original_text_match='162_semantic_units_30_paragraphs_reconstructed',protected_numbers_units_names='independent_semantic_review_passed',caption_display_mapping_and_numeric_value_match='four_explicit_conversions_verified',caption_box_exceptions='body_and_chapters_continuous_brand_and_final_CTA_hidden',last_speech_plus_three_seconds='three_second_provisional_caption_end_hold_voice_absent',full_decode='passed',continuous_playback_performed=False,actual_listening_performed=False,required_open_issues=0,evidence_paths=[rel(qa),rel(O/'checks/verification.json')])
    pre['representative_style_QA']='passed_before_full_render';dump(D/'episode_preflight.json',pre)
    cfgpath=ROOT/'config/video_shelf.json';cfg=read(cfgpath);entry=next(e for e in cfg['entries'] if e['name']=='지역별가격회복');files=entry['files']
    replacements={'대본.md':script,'낭독대본.txt':O/'낭독대본.txt','화면설계.md':O/'화면구성.md','검토영상.mp4':video,'검토자막_임시.srt':O/'의미단위_임시자막.srt','검토안내.md':O/'검토안내.md','논문영상_대본.md':script,'논문영상_구성안.md':O/'화면구성.md','논문영상_장면표.json':O/'화면설계.json','논문영상_인용자료.md':O/'인용자료.md','논문영상_검수.json':qa}
    replacements.update({'논문영상_검토본.mp4':video,'논문영상_자막_임시.srt':O/'의미단위_임시자막.srt','논문영상_검토안내.md':O/'검토안내.md','논문영상_완성검수.json':qa})
    for alias,path in replacements.items():
        if alias in files and files[alias]!=rel(path):files.setdefault(('이전_가독성_v2_' if 'readable-video-v2' in files[alias] else '이전_논문_v1_')+alias,files[alias])
        files[alias]=rel(path)
    files.update({'인용자료.md':rel(O/'인용자료.md'),'의미단위_대본과_표기표.md':rel(O/'의미단위_대본과_표기표.md'),'가이드_반영내역.md':rel(O/'가이드_반영내역.md'),'이미지_사용목록.md':rel(O/'이미지_사용목록.md'),'미리보기_v3.png':rel(O/'미리보기.png'),'논문영상_검수_v3.json':rel(qa)})
    entry['status']=f'제작 가이드 반영 v3 · 전체 {ts(v["duration"])} 화면 검토본 · 새 이미지 9개·이미지 챕터8개·162의미단위 · 음성 보류'
    dump(cfgpath,cfg)
    r=subprocess.run([str(ROOT/'tools/python311/python.exe'),'-X','utf8',str(ROOT/'tools/refresh_video_shelf.py')],cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
    if r.returncode:raise RuntimeError(r.stdout+r.stderr)
    for alias,path in replacements.items():assert os.path.samefile(ROOT/'영상/지역별가격회복'/alias,path)
    for path,h in protected.items():assert sha(ROOT/path)==h,path
    dump(D/'delivery.json',{'at_utc':now,'video':rel(video),'script':rel(script),'sha256':sha(video),'aliases_refreshed':True,'voice_on_hold':True,'new_native_images':9,'external_paid_media_api_calls':0,'billing_not_queried':True,'telegram_sent':False,'uploaded':False})
    print(r.stdout.strip());print(json.dumps({'video':rel(video),'script':rel(script),'duration':v['duration'],'guide':rel(O/'가이드_반영내역.md')},ensure_ascii=False))
if __name__=='__main__':{'capture':capture,'started':started}.get(sys.argv[1] if len(sys.argv)>1 else '',main)()
