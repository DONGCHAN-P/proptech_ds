from pathlib import Path
import json,hashlib,datetime,shutil,subprocess
EP=Path(__file__).resolve().parents[2];ROOT=EP.parents[2];O=EP/'outputs/readable-video-v2';P=O/'project';D=EP/'director/readable-video-v2';D.mkdir(parents=True,exist_ok=True)
def dump(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),'utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(ROOT).as_posix()
def main():
    v=json.loads((O/'checks/verification.json').read_text('utf-8'))
    qa=EP/'qa/readable-video-v2/video_review.json'
    assert qa.exists(),'Encoded video QA must precede delivery'
    q=json.loads(qa.read_text('utf-8'));assert q.get('required_open_issues')==0,q
    scriptqa=json.loads((EP/'qa/readable-video-v2/script_review.json').read_text('utf-8'))
    assert scriptqa['status']=='production_text_reviewed_no_open_script_findings'
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    t=json.loads((P/'timing.json').read_text('utf-8'))
    scenes=json.loads((O/'scene_script.json').read_text('utf-8'))['scenes']
    (O/'낭독대본.txt').write_text('\n\n'.join(p['text'] for s in scenes for p in s['paragraphs'])+'\n','utf-8')
    def ts(secs):return f'{int(secs)//60:02}:{int(secs)%60:02}'
    rows=['# 전체 화면 구성 · 가독성 수정본 v2','','대본의 서술 순서에 따라 전체 8장을 제작했습니다. 시간표는 음성 생성 전의 임시 길이입니다.','','| 구간 | 장면 | 설명과 화면 |','|---|---|---|','| 00:00–00:05 | 기존 채널 인트로 | 기존 브랜드·음악 재사용 |']
    for s in t['scenes']:
        for b in s['beats']:
            si=next(x for x in scenes if x['id']==s['id']);idx=int(b['id'].split('-P')[1])-1
            rows.append(f'| {ts(s["start"]+b["start"]+5)}–{ts(s["start"]+b["start"]+b["duration"]+5)} | {b["id"]} | {si["paragraphs"][idx]["screen_headline"]} |')
    rows+=['', '끝말 이후 본문 화면 3초를 유지한 뒤 기존 아웃트로 10초를 연결합니다. Jun 음성을 새로 생성하거나 기존 낭독을 새 대본처럼 재사용하지 않았습니다.']
    (O/'화면구성.md').write_text('\n'.join(rows)+'\n','utf-8')
    report=f'''# 전체 검토본 v2

[전체 영상](regional_literature_readable_v2.mp4) · [대본](대본.md) · [상세 인용자료](인용자료.md) · [화면 구성](화면구성.md)

1920×1080, 30fps, {ts(v['duration'])}입니다. 기존 채널 인트로 5초·아웃트로 10초와 보유 BGM을 재사용했습니다. **내레이션 없는 화면 검토본**이며, Jun 음성 생성 보류는 유지했습니다. 자막 시간은 실제 음성에 맞춘 확정값이 아닙니다.

대본은 가격 차이 → 가구의 분리 → 공간과 거주 방식 → 재건축 이주 → 순증 공급 → 직장 접근성 → 실제 선택지 순서로 정리했습니다. 개인 저자에게는 ‘님’을 붙였고, 논문·보고서 6개의 전체 제목, 저자, 연도, 학술지, 권호·쪽수, DOI, 분석 대상과 해석 범위를 별첨에 적었습니다.

면적 설명에는 LH의 남양주왕숙 A-1블록 59A 공식 평면을 사용했습니다. 전용 59.92㎡·약 18.1평과 공급 84.46㎡·약 25.5평을 구분합니다. 발코니 확장형 분양 계획도이며 논문 분석 단지의 평면이 아닙니다. 원PDF·면적표·크롭의 출처와 검증 기록은 유지했습니다. 별도 도판 재이용 허락 범위는 확인되지 않아 게시 준비 때 확인할 항목으로 남겼습니다.

영상은 8장 전체를 집과 공간 중심 화면으로 구성했습니다. 가격 곡선, 이주 시간 순서, 가상 순증 계산, 통근 연결, 조건에 따라 줄어드는 후보를 서로 다른 화면으로 보여줍니다. 가상 예시·문헌 결과·자체 관측·후속 질문을 구분했습니다.

검수는 30단락 대본·장면표·108개 자막의 텍스트 일치, 전체 디코딩, 해상도·길이·프레임 수, 실제 MP4의 장별 표본과 주요 경계를 포함합니다. 실제 청취와 전편 연속 재생은 수행하지 않았습니다. 새 유료 생성, 텔레그램 전송, 업로드는 실행하지 않았습니다. 기존 대본과 MP4는 해시로 보존을 확인했습니다.

음악: Thinking Music by Kevin MacLeod | incompetech.com | Licensed under Creative Commons: By Attribution 4.0
'''
    (O/'검토안내.md').write_text(report,'utf-8')
    script=O/'대본.md';video=O/'regional_literature_readable_v2.mp4'
    original_state=EP/'state.json'
    if not (D/'state_before.json').exists():shutil.copy2(original_state,D/'state_before.json')
    state=json.loads(original_state.read_text('utf-8'))
    state.update(stage='literature_readable_v2_local_full_review_ready_narration_on_hold',updated_at=now,script_status='revised_and_produced_under_current_user_instruction',script_revision='readable-video-v2',script_file=rel(script),script_sha256=sha(script),script_decision_id='regional-readable-v2-user-instruction-20261025',production_revision='readable-video-v2',qa_file=rel(qa),audio_status='existing_bgm_only_narration_user_hold',timing_locked=False,pre_upload_status='not_authorized',budget_status='voice_generation_deferred_by_user',full_review_scope='All eight chapters rebuilt from revised narration; BGM only, provisional captions. Encoded frame sampling and full decode; no continuous viewing or actual listening.')
    state['production_render']={'mode':'visual-review','status':'complete_for_local_visual_review','video_file':rel(video),'video_sha256':sha(video),'duration':v['duration'],'frames':v['frames'],'resolution':v['resolution'],'fps':30,'narration':False,'actual_listening':False,'continuous_playback':False,'verification':rel(O/'checks/verification.json')}
    state.pop('pending_production',None)
    state.setdefault('qa_history',[]).extend([rel(EP/'qa/readable-video-v2/script_review.json'),rel(qa)])
    dump(original_state,state)
    dump(D/'authorization.json',{'client_date':'2026-10-25','user_instruction':'대본을 좀 가독성 좋게 바꾸고, 저자 OOO님, 논문 상세 인용, 대표적인 건축 예시로 평형 설명, 대본 서술 순서 정리 후 영상제작 진행','scope':'rewrite and full local visual production for this episode','version':'readable-video-v2','basis':'explicit_current_user_instruction_not_inherited_old_version_approval','voice_generation':'still_on_hold','external_send':False,'upload':False,'new_paid_calls':0,'script_sha256':sha(script),'video_sha256':sha(video)})
    decision_dir=ROOT/'output/video_decisions/decisions';decision_dir.mkdir(parents=True,exist_ok=True)
    dump(decision_dir/'regional-readable-v2-user-instruction-20261025.json',{'id':'regional-readable-v2-user-instruction-20261025','episode':'regional-price-recovery-20261022','gate':'script','status':'approved','approval_type':'explicit_instruction_to_rewrite_then_produce','created_at':now,'video_revision':'readable-video-v2','artifacts':{rel(script):sha(script),rel(O/'인용자료.md'):sha(O/'인용자료.md')},'approval_basis':'Current user explicitly requested a readability rewrite with named author honorifics, detailed paper citations and a representative real apartment plan, followed by video production. This records permission to do that work; it does not assert that the user has reviewed or accepted the resulting script or MP4.','old_version_approval_inherited':False,'narration_generation_authorized':False,'new_paid_generation_authorized':False,'cash_cap_krw':0,'external_send_authorized':False,'upload_authorized':False,'result_acceptance':'not_yet_reviewed_by_user'})
    pre=json.loads((ROOT/'video-agent-studio/templates/episode_preflight.json').read_text('utf-8'))
    pre.update(status='completed_local_visual_review_voice_on_hold',episode_id='regional-price-recovery-20261022')
    pre['baseline'].update(current_video=rel(video),sha256=sha(video),script_revision='readable-video-v2',audio_revision='existing_bgm_only_Jun_hold')
    pre['approvals']['script'].update(decision_id='regional-readable-v2-user-instruction-20261025',status='current_user_instruction_to_rewrite_then_produce',artifact_hashes={'script':sha(script)})
    pre['approvals']['budget'].update(status='new_generation_not_run_voice_hold',cash_cap=0,credits_cap=0)
    pre['approvals']['pre_upload']['status']='not_authorized'
    pre['story']['order']=['price_difference','households','floorplan_and_tenure','relocation','net_supply','commute','feasible_choices','next_tests']
    pre['change_control'].update(changed_scene_ids=[s['id'] for s in scenes],single_timing_lock=False,package_frozen_before_hash=True,issues=[],superseded_rules=['Current request for natural narrative order supersedes site-tour order; current user instruction authorizes rewrite and production.'])
    pre['qa'].update(actual_encoded_frames='sampled_all_chapters_and_major_cuts',all_cut_boundaries_no_flash='sampled_chapter_boundaries_not_continuous_playback',semantic_caption_original_text_match='verified_108_cues_30_paragraphs',full_decode='passed',continuous_playback_performed=False,actual_listening_performed=False,required_open_issues=0,last_speech_plus_three_seconds='three_second_provisional_caption_end_hold_voice_absent',evidence_paths=[rel(qa),rel(O/'checks/verification.json')])
    dump(D/'episode_preflight.json',pre)
    cfgfile=ROOT/'config/video_shelf.json';cfg=json.loads(cfgfile.read_text('utf-8'));entry=next(e for e in cfg['entries'] if e['name']=='지역별가격회복');f=entry['files']
    for alias,new in [('대본.md',script),('검토영상.mp4',video),('검토자막_임시.srt',O/'검토용_임시자막.srt'),('검토안내.md',O/'검토안내.md'),('낭독대본.txt',O/'낭독대본.txt'),('화면설계.md',O/'화면구성.md'),('논문영상_대본.md',script),('논문영상_구성안.md',O/'화면구성.md'),('논문영상_장면표.json',O/'scene_script.json')]:
        if alias in f and f[alias]!=rel(new):
            oldname='이전_논문_v1_'+alias
            f.setdefault(oldname,f[alias])
        f[alias]=rel(new)
    f['논문영상_인용자료.md']=rel(O/'인용자료.md');f['논문영상_검수_v2.json']=rel(qa)
    f['논문영상_수정내역_v2.md']=rel(O/'수정내역.md')
    f['평면_59A.png']=rel(P/'assets/floorplan59.png');f['미리보기_v2.png']=rel(O/'미리보기.png')
    entry['status']='가독성 대본 v2 · 전체 12분17초 화면 검토본 · 논문 상세 인용·실제 59A 평면 · 음성 보류'
    dump(cfgfile,cfg)
    proc=subprocess.run([str(ROOT/'tools/python311/python.exe'),'-X','utf8',str(ROOT/'tools/refresh_video_shelf.py')],cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
    if proc.returncode:raise RuntimeError(proc.stdout+proc.stderr)
    print(proc.stdout.strip())
    dump(D/'delivery.json',{'at_utc':now,'video':rel(video),'script':rel(script),'citations':rel(O/'인용자료.md'),'sha256':sha(video),'aliases_refreshed':True,'voice_on_hold':True,'new_paid_calls':0,'telegram_sent':False,'uploaded':False})
    print(json.dumps({'video':rel(video),'script':rel(script),'citations':rel(O/'인용자료.md'),'duration':v['duration']},ensure_ascii=False))
if __name__=='__main__':main()
