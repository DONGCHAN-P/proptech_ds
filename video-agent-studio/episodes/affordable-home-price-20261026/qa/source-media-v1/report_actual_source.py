from pathlib import Path
import datetime
import hashlib
import json
import re

QA = Path(__file__).resolve().parent
EP = QA.parents[1]


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write(name, data):
    (QA/name).write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


metrics = read(QA/'actual_source_metrics_v2.json')
candidate = read(QA/'candidate_source_frames_v2.json')
v2_archive = EP/'outputs/private-production-v1/source-archive/native-v2-complete-review'
edl_path = v2_archive/'assembly_edl.json'
edl = read(edl_path)
cli_path = EP/'editor/checks/native-v2/summary.json'
cli = read(cli_path)
old_ready = read(QA/'ready.json')
chapter_map = {c['chapter']:c for c in metrics['chapters']}
frames = metrics['source_frames']+[f for f in candidate['frames'] if f.get('path')]


def frame(scene, kind='representative'):
    return next(f for f in frames if f['scene_id']==scene and f['kind']==kind)


def clock(ch, local):
    mapping = next(m for m in edl['offset_map'] if m['chapter']==ch and m['local_start_s']<=local<m['local_end_s'])
    return local+mapping['global_offset_s']


def tc(seconds):
    ms=round(seconds*1000)
    h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
    return f'{h:02}:{m:02}:{s:02}.{ms:03}'


def location(ch,local):
    return dict(chapter=ch,chapter_local_s=local,global_s=clock(ch,local),timecode=tc(clock(ch,local)),timing_revision='production-injoon-v2_잠정')


revision = dict(script_sha256=metrics['script_sha256'],timing_sha256=metrics['timing_sha256'],
                source_chapters={f'ch{c["chapter"]:02}':c['html_sha256'] for c in metrics['chapters']},
                timing_status='v2검수용.실제음성v3반영/EDL재잠금전에는최종미디어승인불가')
findings=[]


def issue(identifier, scenes, severity, problem, evidence, correction):
    locations=[location(f['chapter'],f['time_s']) for f in evidence if 'time_s' in f and 'chapter' in f]
    findings.append(dict(issue_id=identifier,scene_id=','.join(scenes),scene_ids=scenes,
                         timecode=locations,severity=severity,**{'문제':problem,'evidence':evidence,'수정안':correction},
                         owner='Carson/editor; main은통합EDL/공통타이밍',status='open',checked_revision=revision))


issue('SOURCE-TAX-001',['S016','S018'],'required',
      '세금 곡선·복비 계단의 열린 축 경로가 기본검정으로 채워져 큰 삼각형을 만듭니다. 파란선 뒤에 의도하지 않은 감소형 면적이 나타나 도표 해석과 가독성을 해칩니다.',
      [frame('S016'),frame('S018'),dict(path='editor/graphics.py',code='<path d="M100 90 V450 H1600" stroke="var(--muted)" stroke-width="2"/>',observation='fill 속성이 없는 열린축을SVG가검정면적으로닫아채움.직접본문확인.')],
      '축경로에fill="none"을명시하고다른열린path/polyline도함께점검합니다.선/축/점의색·좌표·숫자는유지합니다.수정후S016/S018대표및진입·최대강조프레임을재검수합니다.')
issue('SOURCE-CLIP-002',['S040'],'required',
      '진입y=8px모션 시작에서하단조건문이패널하단을넘어획이잘립니다.안정상태는읽히지만진입프레임은불합격입니다.',
      [frame('S040','bbox_candidate'),dict(metrics=metrics['geometry_candidates'][0],observation='실제원본크기프레임에서하단획잘림확인. glyph.bottom819 > panel.bottom815.')],
      '같은폰트크기를유지하고S040_text011의기본y를8~12px위로옮기거나진입이동중에도잉크가패널내에머물도록여유를확보합니다.진입0/.1/.35초와안정상태,앞뒤장면연결만재검수합니다.')
s031 = frame('S031','one_month_focus')
b031 = next(b for b in chapter_map[7]['beats'] if b['cue_id']=='C07_S031Q002')
b040 = next(b for b in chapter_map[9]['beats'] if b['cue_id']=='C09_S040Q003')
issue('SOURCE-FOCUS-003',['S031','S040'],'required',
      '원어큐연결은있지만자동부분문자일치로발화와다른수치가함께강조됩니다. S031의디딤돌1개월전입큐에서다른상품의6개월전입도강조되고, S040월상환액비교큐에서저축여유수치가우선강조됩니다.',
      [s031,dict(chapter=7,time_s=b031['time_s'],cue_id=b031['cue_id'],spoken=b031['spoken_display_text'],screen_labels=b031['text_labels'],element_ids=b031['text_ids']),frame('S040'),dict(chapter=9,time_s=b040['time_s'],cue_id=b040['cue_id'],spoken=b040['spoken_display_text'],screen_labels=b040['text_labels'],element_ids=b040['text_ids']),dict(path='editor/build_measured.py',location='native_focus lines64~71',observation='SequenceMatcher가공통두글자이상인라벨을점수순최대3개선택하며다른상품/측정값을구분하지않음.')],
      'C07_S031Q002는디딤돌1개월/2년만,다음Q003은보금자리6개월만강조합니다. C09_S040Q003는227.3→285.5및170.0→213.5월액, Q004는저축여유를강조하도록명시적의미라벨매핑을사용합니다.동일부분일치규칙이선택한나머지큐도잘못된다른상품/수치를강조하지않는지매핑표로확인합니다.숫자재계산은필요없습니다.')
resume = frame('S001','brand_resume_source')
resume_after = frame('S001','brand_resume_plus1')
s1 = next(s for s in chapter_map[1]['scenes'] if s['scene_id']=='S001')
brand_end = next(s['global_end_s'] for s in edl['segments'] if s['id']=='clean_brand_intro')
issue('SOURCE-BRAND-004',['S001','S002'],'required',
      '인트로종료후재개되는로컬23.033333초에서이전훅S001이계속선택됩니다.현v2 EDL대로합성하면브랜드뒤약1.412667초동안이전훅화면이되살아납니다.자막글자는비어있어도이전화면fallback금지에어긋납니다.',
      [resume,resume_after,dict(path=edl_path.as_posix(),edl_sha256=sha(edl_path),chapter=1,time_s=edl['hook_cut_s'],global_brand_end_s=brand_end,source_scene=s1,remaining_old_scene_s=s1['clip_end_s']-edl['hook_cut_s'],scope='실제HTML선택과EDL를대조한소스결함.아직MP4를봤다는뜻아님.')],
      '브랜드종료첫프레임부터S002화면을선택하도록현재실측EDL의훅분할점에서장면선택경계를바꿉니다.다음실제원어큐전까지글자만비우고본문흰박스는유지합니다.임의70ms연장이나이전큐hold를추가하지않습니다. v3소스와EDL에서인트로종료전/당프레임/다음프레임을대조합니다.')
issue('SOURCE-REPEAT-005',['CH03','CH04','CH05','CH06','CH07','CH10'],'recommended',
      '주제전환에서CH03/06/10은동일집3개+막대, CH04/05/07은동일문서3개배경을제목만바꿔반복합니다.본문45개도표는역할이대체로다르지만챕터전환의독립성은약합니다.',
      [dict(path=(QA/'actual-source-v2-frames/chapter_titles.png').as_posix(),sha256=sha(QA/'actual-source-v2-frames/chapter_titles.png'),observation='9개챕터진입소스프레임직접열람.'),dict(path='editor/build_measured.py',location='chapter_art lines20~28',observation='번호그룹마다같은모양·같은좌표를재사용')],
      '추가유료생성없이담보는집/비율,소득은연상환예산,비용은영수증,가격별계산은세가격,정책은자격필터,다음선택은단지비교처럼각장의자료역할이구분되도록전환벡터를다르게구성합니다.')
issue('SOURCE-LABEL-006',['S032'],'recommended',
      '맞벌이조건의영문AND는한국어조건을읽는흐름을끊습니다.조건과숫자자체는정확합니다.',
      [frame('S032')],
      '같은조건을유지하면서AND를그리고/이며로바꾸면읽기쉽습니다.폰트를축소하지않고해당라벨만경계재검수합니다.')

before_inputs=[]
archive=QA/'source-v2-preserved-inputs';archive.mkdir(exist_ok=True)
fingerprints=[]
for ch,row in chapter_map.items():
    source=v2_archive/f'ch{ch:02}/index.html'
    current_sha=sha(source)
    before_inputs.append(dict(chapter=ch,reviewed_sha256=row['html_sha256'],current_sha256=current_sha,same_as_reviewed=current_sha==row['html_sha256']))
    if current_sha==row['html_sha256']:
        destination=archive/f'ch{ch:02}.html';destination.write_bytes(source.read_bytes())
        raw=source.read_text(encoding='utf-8')
        style=re.search(r'<style>(.*?)</style>',raw,re.S)[1]
        for sid,markup in re.findall(r'<section id="(S[0-9]+R?)"[^>]*>(.*?)</section>',raw,re.S):
            fingerprints.append(dict(scene_id=sid,chapter=ch,static_graphic_sha256=hashlib.sha256(markup.encode('utf-8')).hexdigest(),css_sha256=hashlib.sha256(style.encode('utf-8')).hexdigest(),timing_excluded=True))
write('source_visual_fingerprints_v2.json',dict(scene_fingerprints=fingerprints,input_versions=before_inputs))
cli_valid = all(next(c for c in cli['chapters'] if c['chapter']==row['chapter'])['html_sha256']==row['html_sha256'] for row in metrics['chapters'])
assert cli_valid
fullres=['S016','S018','S040','S034R','S024','S032','S031']
coverage=dict(source_scenes=45,chapters=10,native_focus_cues=metrics['total_native_focus_cues'],
              actual_source_time_samples=sum(len(c['samples']) for c in metrics['chapters']),actual_source_text_checks=metrics['total_text_checks'],
              actual_caption_failures=metrics['caption_failures'],runtime_errors=metrics['runtime_errors'],
              focus_existence_missing=metrics['focus_failures'],focus_semantic_verdict='150큐매핑표직접검토;SOURCE-FOCUS-003의반례확인.존재검사통과를의미강조통과로확대하지않음.',
              source_glyph_geometry='실제45소스전량/150큐40px·50px행높이검사.현재확인된SVG진입잘림1건,캡션잘림0건.',
              visual_sheet_review=dict(scene_count=45,contact_sheets=5,chapter_title_frames=9,scope='45장면대표및9개챕터전환시트를직접열람.일반구성·반복·숫자/대상일치검토.'),
              full_resolution_review_scenes=fullres,additional_fullres_frames=['S001브랜드재개2프레임','S0311개월강조프레임','S040진입잘림프레임'],
              zoom='현재소스는scale줌없음.진입y8px/.35s경계와고정도표전체정보검사.',
              source_CLI=dict(status='pass_reused_exact_source_hashes',version=cli['version'],receipt_path=cli_path.as_posix(),receipt_sha256=sha(cli_path),chapters=10,independent_rerun=False),
              backward_seek='10챕터중간프레임순/역seek픽셀SHA동일검사',backward_seek_all_pass=all(c['backward_seek_pixel_identical'] for c in metrics['chapters']),
              finance_primary='56사실·18사례·B전환승인입력재사용.157산술/신생아원문재검수없음.',
              audio='v2 ASR 명료성 4문단 보완은Kant/Gibbs범위.발음오류라고독립확정하지않음.',
              actual_listening='unchecked',continuous_playback='unchecked',actual_MP4='unchecked / 미렌더',final_media_approved=False)
status='required_changes_open_v3_timing_pending'
doc=dict(status=status,critical=0,required=sum(f['severity']=='required' for f in findings),recommended=sum(f['severity']=='recommended' for f in findings),findings=findings)
write('source_findings_v2.json',doc)
write('findings.json',doc)
write('source_review_v2.json',dict(status=status,source_approved=False,media_approved=False,checked_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),checked_revision=revision,coverage=coverage,source_input_versions=before_inputs,findings_path='source_findings_v2.json'))
write('delta_recheck_plan.json',dict(status='waiting_Carson_v3_source_receipt',
      immutable_reuse=['동일표시150큐/45장면','동일정책/사례/입금리표의기존검수','정적그래픽fingerprint동일장면의구성검수'],
      check_all_new_anchor_metadata=['현재잠금script SHA','실제v3 timing/10WAV SHA','45 scene start/end/paragraph ID','150 CUES/BEATS/native time 및보호표시문','새EDL분할/브랜드/CTA/길이와SRT의총괄receipt SHA'],
      source_frames_recheck=['S016/S018 fillnone수정/열린축회귀','S040 하단조건문진입0/.1/.35s/안정상태','S031 Q002/Q003 다른상품숫자강조제거','S040 Q003/Q004 월액/저축강조분리','CH01실제훅분할/브랜드재개전후프레임S002선택','v3변경읽기4문단S014/S019/S024/S030의실측앵커및앞뒤연결'],
      source_wide_retest_trigger='공통CSS/런타임/폰트/도형컴포넌트변경시해당영향장면만추가.소스전체해시변경만으로금융157검사재실행하지않음.',
      after_receipts='수정후원본HTML/의존자산/EDL/timing SHA와프레임SHA를추가.확인안한문제는담당주장만으로닫지않음.',
      actual_full_MP4='이후실제MP4전량decode/모든45대표+장/브랜드/최대글자프레임을별도검수.최종청취/연속재생미확인상태유지.'))
write('issue_SOURCE-VISUAL-v2.json',dict(issue_id='SOURCE-VISUAL-v2',scene_id='S016,S018,S040,S031,S001/S002',
      problem='필수4건:검정축채움/하단획잘림/다른상품강조/브랜드뒤이전화면fallback',
      evidence='source_findings_v2.json + actual-source-v2-frames/ + actual_source_metrics_v2.json',
      proposal='Carson은v3재바인딩과함께수정.핵심대상/영향장면만재검수.금융값·대본표시문변경불필요.',
      impact='source gate 미통과. full render/미디어승인없음.',owner='Carson / main',status='open',
      direct_message='현재직접agent메시지도구없음.이issue파일과최종응답으로인계.'))
write('handoff.json',dict(status=status,source_approved=False,media_approved=False,
      outputs=['qa/source-media-v1/source_review_v2.json','qa/source-media-v1/source_findings_v2.json','qa/source-media-v1/issue_SOURCE-VISUAL-v2.json','qa/source-media-v1/delta_recheck_plan.json'],
      revision=dict(script_sha256=metrics['script_sha256'],timing_sha256=metrics['timing_sha256']),
      validation='실제45소스/10장·150큐/723시각·8957글자검사.45대표+9전환시트,핵심원본크기프레임직접열람.기존sourceCLI는동일10HTML SHA로재사용.',
      unresolved=['SOURCE-TAX-001 S016/S018','SOURCE-CLIP-002 S040','SOURCE-FOCUS-003 S031/S040','SOURCE-BRAND-004 S001→S002','실제v3소스/EDL타이밍delta','이후실제MP4검수'],
      affected_scenes='S001/S002/S016/S018/S031/S040; v3앵커S014/S019/S024/S030',next_owner='Carson수정+v3소스receipt→QA영향장면재검수;main통합EDL/audio/carve게이트',
      actual_listening=False,continuous_playback=False,paid_external_calls=0))
print(json.dumps(dict(status=status,required=doc['required'],recommended=doc['recommended'],reviewed_source_scenes=45,source_frames=len(frames),visual_fingerprints=len(fingerprints),current_html_changed=[x['chapter'] for x in before_inputs if not x['same_as_reviewed']]),ensure_ascii=False))
