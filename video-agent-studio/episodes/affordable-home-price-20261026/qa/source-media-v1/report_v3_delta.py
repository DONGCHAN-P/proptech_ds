from pathlib import Path
import copy
import datetime
import hashlib
import json
import re

QA=Path(__file__).resolve().parent
EP=QA.parents[1]


def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,d):(QA/name).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


metrics=read(QA/'source_delta_metrics_v3.json')
old=read(QA/'source_findings_v2.json')
timing=EP/'narration/production-injoon-v3/final_timing.json'
edl_file=EP/'outputs/private-production-v1/assembly_edl.json'
edl=read(edl_file)
assert sha(timing)==metrics['timing_sha256']
assert sha(edl_file)==metrics['edl_sha256']
chapters={c['chapter']:c for c in metrics['chapters']}
source_files=[EP/f'outputs/private-production-v1/ch{c:02}/index.html' for c in range(1,11)]
assert all(sha(p)==chapters[i+1]['html_sha256'] for i,p in enumerate(source_files))
cli_path=EP/'editor/checks/native-v3/summary.json'
cli=read(cli_path)
cli_matches=cli['status']=='pass' and all(c['html_sha256']==chapters[c['chapter']]['html_sha256'] for c in cli['chapters'])
edl_review=EP/'director/production-v1/edl_review_v3.json'
er=read(edl_review)
assert er['edl_sha256']==metrics['edl_sha256'] and er['timing_sha256']==metrics['timing_sha256']
assert er['subtitles_sha256']==sha(EP/'outputs/private-production-v1/captions_measured.srt')
assert not metrics['anchor_failures'] and not metrics['caption_failures'] and not metrics['focus_presence_failures'] and not metrics['geometry_candidates']


def frame(sid,kind='changed_or_fix'):
    return next(f for f in metrics['frames'] if f['scene_id']==sid and f['kind']==kind)


def location(ch,t):
    m=next(m for m in edl['offset_map'] if m['chapter']==ch and m['local_start_s']<=t<m['local_end_s'])
    g=t+m['global_offset_s'];ms=round(g*1000);h,ms=divmod(ms,3600000);mi,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
    return dict(chapter=ch,chapter_local_s=t,global_s=g,timecode=f'{h:02}:{mi:02}:{s:02}.{ms:03}',timing_revision='production-injoon-v3')


revision=dict(script_sha256=metrics['script_sha256'],timing_sha256=metrics['timing_sha256'],edl_sha256=metrics['edl_sha256'],source_chapters={f'ch{c:02}':chapters[c]['html_sha256'] for c in chapters})
findings=copy.deepcopy(old['findings'])
for finding in findings:
    finding['before_checked_revision']=finding['checked_revision']
    finding['checked_revision']=revision
    issue=finding['issue_id']
    if issue=='SOURCE-TAX-001':
        finding['status']='closed_verified_source_v3'
        finding['closure_evidence']=[frame('S016'),frame('S018')]
        finding['closure']='원본크기v3소스프레임직접열람:축의검정삼각형없음,세율곡선/복비계단숫자와색유지.실제MP4검수는별도.'
    elif issue=='SOURCE-CLIP-002':
        finding['status']='closed_verified_source_v3'
        finding['closure_evidence']=[f for f in metrics['frames'] if f['scene_id']=='S040']
        finding['closure']='S040_text011 baseline580→568·폰트유지.진입0/.1/.35초및안정상태수치검사0초과.진입첫프레임원본크기직접열람하여하단획이안잘림확인.'
    elif issue=='SOURCE-FOCUS-003':
        selected=[b for c in metrics['chapters'] for b in c['focus_checks'] if b['cue_id'] in ['C07_S031Q002','C07_S031Q003','C09_S040Q003']]
        finding['status']='open_confirmed_source_v3'
        finding['current_evidence']=selected
        finding['timecode']=[location(c['chapter'],b['time_s']) for c in metrics['chapters'] for b in selected if b in c['focus_checks']]
    elif issue=='SOURCE-BRAND-004':
        finding['status']='open_confirmed_source_v3'
        finding['current_evidence']=[metrics['brand_resume'],frame('brand_resume','source_at_cut')]
        finding['timecode']=[dict(chapter=1,chapter_local_s=metrics['brand_resume']['chapter_local_s'],global_s=metrics['brand_resume']['global_s'],timecode='00:28.033',timing_revision='production-injoon-v3')]
    elif issue=='SOURCE-LABEL-006':
        finding['status']='closed_verified_source_v3'
        finding['closure_evidence']=[frame('S032'),next(b for b in chapters[8]['focus_checks'] if b['cue_id']=='C08_S032Q003')]
        finding['closure']='소스실제라벨에서AND→가운뎃점으로변경됨.합산2억이하·각1인1.3억이하동시조건보존.'
    else:
        finding['status']='open_recommended'
changes=[]
for ch,p in enumerate(source_files,1):
    before=(QA/f'source-v2-preserved-inputs/ch{ch:02}.html').read_text(encoding='utf-8')
    after=p.read_text(encoding='utf-8')
    sections=lambda raw:dict(re.findall(r'<section id="(S[0-9]+R?)"[^>]*>(.*?)</section>',raw,re.S))
    a,b=sections(before),sections(after)
    nofill=lambda s:re.sub(r'(<path\b[^>]*?) fill="none"',r'\1',s)
    for sid in a:
        changes.append(dict(scene_id=sid,chapter=ch,before_static_sha256=hashlib.sha256(a[sid].encode()).hexdigest(),after_static_sha256=hashlib.sha256(b[sid].encode()).hexdigest(),exact=a[sid]==b[sid],equal_except_explicit_open_path_fill=nofill(a[sid])==nofill(b[sid])))
open_required=[f['issue_id'] for f in findings if f['severity']=='required' and f['status'].startswith('open')]
closed_required=[f['issue_id'] for f in findings if f['severity']=='required' and f['status'].startswith('closed')]
assert open_required==['SOURCE-FOCUS-003','SOURCE-BRAND-004']
result=dict(status='required_changes_open',source_approved=False,media_approved=False,critical=0,required=len(open_required),recommended=sum(f['severity']=='recommended' and f['status'].startswith('open') for f in findings),closed_required=closed_required,open_required=open_required,findings=findings)
write('source_findings_v3.json',result)
write('findings.json',result)
report=dict(status='required_changes_open',source_approved=False,media_approved=False,checked_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),checked_revision=revision,
            coverage=dict(previous_source_review='source_review_v2.json:실제45장면/150큐/723시각/8957텍스트검사와45대표/9전환시트',
                          current_metadata=dict(scenes=45,native_cues=150,anchor_failures=0,caption_failures=0,focus_presence_failures=0,scope='실제v3HTML의45장면start/end·150큐표시문/원어시각/BEAT시각·현재큐실행선택검사.강조의미통과와구분.'),
                          current_graphic_comparison=dict(scenes=45,unchanged_except_explicit_path_fill=sum(c['equal_except_explicit_open_path_fill'] for c in changes),other_changes=[c['scene_id'] for c in changes if not c['equal_except_explicit_open_path_fill']],details=changes),
                          current_frame_capture_count=len(metrics['frames']),current_fullres_actually_viewed=['S016','S018','S040진입0','브랜드재개첫소스프레임'],
                          voice_delta_scenes=['S014','S019','S024','S030'],voice_delta_frame_paths=[f for f in metrics['frames'] if f['scene_id'] in ['S014','S019','S024','S030']],
                          edl_srt_reused=dict(path=edl_review.as_posix(),sha256=sha(edl_review),checked_cues=150,reran_math=False,planned_total_seconds=edl['total_seconds']),
                          CLI_reused=dict(path=cli_path.as_posix(),sha256=sha(cli_path),status='pass_reused_exact_sha' if cli_matches else 'current_source_hash_recheck_pending',all10HTML_SHA_match=cli_matches),
                          finance_or_primary_reaudit=False,actual_listening='unchecked',continuous_playback='unchecked',actual_encoded_frames=0),
            closed_required=closed_required,open_required=open_required,
            next_action='Carson: S031/S040 의미라벨매핑과CH01브랜드뒤S002선택수정후소스SHA/해당프레임을전달.영향3장면+경계만재검수.',
            final_media_gate='아직실제MP4검수/전량decode/양측최종미디어승인없음.이문서는렌더승인이아님.')
write('source_review_v3.json',report)
for ident in open_required:
    write('issue_'+ident+'.json',next(f for f in findings if f['issue_id']==ident))
write('ready.json',dict(status='required_changes_open',source_approved=False,media_approved=False,current_review='source_review_v3.json',current_findings='source_findings_v3.json',open_required=open_required,closed_required=closed_required,checked_revision=revision))
write('handoff.json',dict(status='required_changes_open',source_approved=False,media_approved=False,
      outputs=['qa/source-media-v1/source_review_v3.json','qa/source-media-v1/source_findings_v3.json','qa/source-media-v1/issue_SOURCE-FOCUS-003.json','qa/source-media-v1/issue_SOURCE-BRAND-004.json'],
      input_versions=revision,validation='v2의45장면시각검수재사용+실제v3전체45앵커/150큐실행검사0실패.축삼각형·S040진입잘림수정확인.EDL/SRT현재해시일치receipt재사용.현재HTML의CLI SHA일치는source_review_v3.json확인.',
      unresolved=['SOURCE-FOCUS-003 S0311개월/6개월·S040월액/저축강조분리','SOURCE-BRAND-004 인트로끝후S0011.41초재등장','이후실제MP4검수'],
      affected_scenes=['S001','S002','S031','S040'],next_owner='Carson대상수정→QA부분재검수;main렌더게이트는아직대기',actual_listening=False,continuous_playback=False))
print(json.dumps(dict(required_open=open_required,required_closed=closed_required,anchor_checks='45/150 pass',unchanged_graphics_except_fill=sum(c['equal_except_explicit_open_path_fill'] for c in changes),other_changed=[c['scene_id'] for c in changes if not c['equal_except_explicit_open_path_fill']]),ensure_ascii=False))
