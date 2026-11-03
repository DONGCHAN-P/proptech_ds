from pathlib import Path
import copy,datetime,hashlib,json

Q=Path(__file__).resolve().parent;EP=Q.parents[1]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def write(n,d):(Q/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


static=read(Q/'targeted_static_v4.json');targeted=read(Q/'targeted_focus_brand_v4.json');cli=read(Q/'targeted_cli_v4.json')
previous=read(Q/'source_findings_v3.json');base_cli_path=EP/'editor/checks/native-v3/summary.json';base_cli=read(base_cli_path)
assert static['status']==targeted['status']==cli['status']=='pass'
assert all(x['passed'] for x in static['checks']) and all(x['passed'] for x in targeted['checks'])
assert len(static['scene_geometry'])==45 and all(x['unchanged_geometry_and_labels'] for x in static['scene_geometry'])
for f in targeted['frames']:assert sha(Path(f['path']))==f['sha256']
rows=[]
for c in static['chapters']:
    p=Path(c['path']);assert sha(p)==c['postcarve_html_sha256']
    clirow=next(x for x in (cli['chapters'] if c['chapter'] in [1,7,9] else base_cli['chapters']) if x['chapter']==c['chapter'])
    assert clirow['ok'] and clirow['html_sha256']==sha(p)
    rows.append(dict(chapter=c['chapter'],path=p.as_posix(),postcarve_html_sha256=sha(p),bytes=p.stat().st_size,
                     CLI_receipt=(Q/'targeted_cli_v4.json').as_posix() if c['chapter'] in [1,7,9] else base_cli_path.as_posix(),
                     CLI_scope='현재변경장소스전체lint·해당경계/큐runtime·layout샘플' if c['chapter'] in [1,7,9] else '동일HTML_SHA의기존통과재사용'))
assert len(rows)==10
lock=read(EP/'director/production-v1/locked_script.json')
workspace=EP.parents[2]
assert sha(workspace/lock['script_path'])==static['script_sha256']==lock['script_sha256']
assert sha(EP/'research/facts_v2.json')==lock['facts_sha256']
assert sha(EP/'research/newborn_policy_addendum_v2.json')==lock['newborn_addendum_sha256']
revision=dict(script_sha256=static['script_sha256'],timing_sha256=static['timing_sha256'],edl_sha256=static['edl_sha256'],
              source_chapters={f'ch{x["chapter"]:02}':x['postcarve_html_sha256'] for x in rows},visual_revision='visual-v4')
findings=copy.deepcopy(previous['findings'])
for f in findings:
    f['before_closure_revision']=f['checked_revision'];f['checked_revision']=revision
    if f['issue_id']=='SOURCE-FOCUS-003':
        f['status']='closed_verified_visual_v4'
        f['closure_evidence']=[x for x in targeted['frames'] if x.get('cue_id') in ['C07_S031Q002','C07_S031Q003','C09_S040Q003','C09_S040Q004']]
        f['closure']='실제수정HTML의원본크기프레임4장직접열람.디딤돌1개월/2년과보금자리6개월강조분리,월액4개와저축2개강조분리.앞뒤원어큐경계에서불필요한이전강조/자막유지없음.'
    elif f['issue_id']=='SOURCE-BRAND-004':
        f['status']='closed_verified_visual_v4'
        f['closure_evidence']=[x for x in targeted['frames'] if x['kind']=='brand_boundary']
        f['closure']='실측local23.033333초부터S002선택확인.해당소스원본크기프레임직접열람.이전프레임S001/당프레임S002/다음프레임S002이며native24.547333초전글자비움·본문흰박스유지.음성/자막/EDL시간불변.'
    elif f['status'].startswith('closed'):
        f['closure_retained_by']='이전실제프레임수정확인+45SVG좌표/라벨·CSS·폰트불변SHA.해당장면재렌더반복없음.'
open_required=[f['issue_id'] for f in findings if f['severity'] in ['critical','required'] and not f['status'].startswith('closed')]
assert not open_required
summary=dict(status='source_pass_exact_postcarve_HTML',source_approved=True,media_approved=False,critical=0,required=0,
             open_required=[],recommended=sum(f['severity']=='recommended' and f['status'].startswith('open') for f in findings),findings=findings,checked_revision=revision)
write('source_findings_v4.json',summary);write('findings.json',summary)
for issue in findings:
    if issue['issue_id'] in ['SOURCE-FOCUS-003','SOURCE-BRAND-004']:
        write('issue_'+issue['issue_id']+'.json',issue)
artifacts=[Q/p for p in ['targeted_static_v4.json','targeted_focus_brand_v4.json','targeted_cli_v4.json','source_findings_v4.json']]
approval=dict(status='source_pass_exact_postcarve_HTML',approved=True,source_approved=True,media_approved=False,
              approved_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),revision='visual-v4 / production-injoon-v3 / exact postcarve HTML',
              checked_revision=revision,postcarve_HTML=rows,critical=[],required=[],closed_required=['SOURCE-TAX-001','SOURCE-CLIP-002','SOURCE-FOCUS-003','SOURCE-BRAND-004'],
              recommended=[f['issue_id'] for f in findings if f['severity']=='recommended' and f['status'].startswith('open')],
              coverage=dict(initial_actual_source='source_review_v2.json:45장면대표/9전환프레임시트와150원어큐·723시각·8957텍스트기하검수',
                            voice_v3_delta='source_review_v3.json:현재45장면앵커/150큐실행연결·변경4문단타이밍검수.불변수치원문재검수없음.',
                            this_delta=dict(changed_chapters=[1,7,9],static_checks=len(static['checks']),actual_runtime_checks=len(targeted['checks']),captured_source_frames=len(targeted['frames']),
                                            actually_viewed_fullres=['brand_23.033333.png','C07_S031Q002.png','C07_S031Q003.png','C09_S040Q003.png','C09_S040Q004.png'],
                                            static_geometry_and_labels_unchanged=45,caption_display_and_native_time_unchanged=150,whole45_frame_repeat=False,
                                            audio_tags_and_voice_carved_bed_sha='10장원본postcarve와동일태그·voice/bed WAV SHA 확인.음질·발음승인이아님.'),
                            CLI=dict(version='0.8.181',new_checks=[1,7,9],same_HTML_SHA_receipt_reused=[2,3,4,5,6,8,10],new_check_storage='QA소유shadow에동일HTML복사,자산읽기전용junction,로그/캐시QA내저장',telemetry_opt_out='DO_NOT_TRACK=1;설치/업그레이드/유료생성없음'),
                            actual_encoded_film_frames=0,full_MP4_decode='unchecked',actual_listening=False,continuous_playback=False),
              immutable_inputs=[dict(path=p.as_posix(),sha256=sha(p)) for p in [EP/'director/production-v1/locked_script.json',EP/'narration/production-injoon-v3/final_timing.json',EP/'outputs/private-production-v1/assembly_edl.json',EP/'outputs/private-production-v1/captions_measured.srt',EP/'editor/mix_receipt.json']],
              artifacts=[dict(path=p.as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in artifacts],
              independent_voice_QA='Kant의ASR명료성진단/최종음성게이트별도.이문서로음성통과를추정하지않음.',
              full_render_authorized=False,final_media_approval=False,
              next_gate='main의음성/믹스/렌더승인후실제MP4해시·45장면/장/브랜드경계·최대글자프레임·전체decode검수.최종Claude/release는main소유.')
write('source_approval_v4.json',approval)
write('ready.json',dict(status=approval['status'],source_approved=True,media_approved=False,source_approval='qa/source-media-v1/source_approval_v4.json',required=[],next_owner='main렌더게이트/이후실제MP4독립QA',actual_listening=False,continuous_playback=False))
write('handoff.json',dict(status=approval['status'],source_approved=True,media_approved=False,
      outputs=['qa/source-media-v1/source_approval_v4.json','qa/source-media-v1/source_findings_v4.json','qa/source-media-v1/targeted_focus_brand_v4.json'],
      input_versions=dict(script_sha256=static['script_sha256'],timing_sha256=static['timing_sha256'],edl_sha256=static['edl_sha256'],postcarve_10_HTML_SHA='source_approval_v4.json postcarve_HTML'),
      validation='필수4건모두실제증거로닫음.변경CH01/07/09 경계/강조101검사통과·원본크기5프레임직접열람.45도형/150표시큐·원어시각/10음성·bed파일불변확인.현재3장CLI통과+동일SHA7장receipt재사용.',
      required=[],recommended=['SOURCE-REPEAT-005 비차단'],unresolved=['Kant음성독립게이트','이후실제MP4검수/전체decode/최종양측미디어게이트'],
      affected_scenes=['S001','S002','S031','S040'],next_owner='main음성/carve/렌더게이트;실제MP4제공후QA검수',actual_listening=False,continuous_playback=False,full_render_authorized=False))
print(json.dumps(dict(status=approval['status'],required=approval['required'],HTMLs=len(rows),new_CLI_chapters=[1,7,9],checks=len(static['checks'])+len(targeted['checks']),approval_sha256=sha(Q/'source_approval_v4.json')),ensure_ascii=False))
