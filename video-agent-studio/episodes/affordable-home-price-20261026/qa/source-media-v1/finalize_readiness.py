from pathlib import Path
import datetime
import hashlib
import json
import struct

QA = Path(__file__).resolve().parent
EP = QA.parents[1]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def write(name, data):
    (QA/name).write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


edl_path = EP/'outputs/private-production-v1/assembly_edl.json'
srt_path = EP/'outputs/private-production-v1/captions_measured.srt'
receipt_path = EP/'director/production-v1/edl_review.json'
edl, receipt = read(edl_path), read(receipt_path)
packet = read(QA/'caption_packet.json')
text = read(QA/'caption_text_review.json')
glyph = read(QA/'caption_glyph_review.json')
assert receipt['edl_sha256'] == sha(edl_path)
assert receipt['subtitles_sha256'] == sha(srt_path)
assert receipt['script_sha256'] == packet['script_sha256']
assert receipt['timing_sha256'] == packet['timing_sha256']
assert receipt['checked_cues'] == 150
assert text['failed'] == 0 and glyph['status'] == 'pass'
assert glyph['cues'] == 150 and glyph['css_unchanged']


def global_time(chapter, local):
    offsets = [m for m in edl['offset_map'] if m['chapter'] == chapter and m['local_start_s'] <= local < m['local_end_s']]
    assert len(offsets) == 1, (chapter, local)
    return local + offsets[0]['global_offset_s']


fps = edl['fps']
samples = []
for scene in packet['scene_plan']:
    cues = [c for c in packet['cues'] if c['scene_id'] == scene['scene_id']]
    rows = [r for r in glyph['rows'] if r['scene_id'] == scene['scene_id']]
    largest = max(rows, key=lambda r:max(l['width'] for l in r['lines']))
    by_id = {c['id']:c for c in cues}
    chosen = by_id[largest['cue_id']]
    local = (chosen['start_s']+chosen['end_s'])/2
    candidates = [dict(reason='대표/최대자막폭', local_s=local, cue_id=chosen['id'])]
    for reason, at in [('첫큐시작',cues[0]['start_s']),('마지막큐종료',cues[-1]['end_s'])]:
        candidates.append(dict(reason=reason, local_s=at))
    samples.append(dict(scene_id=scene['scene_id'], chapter=scene['chapter'], graphic_id=scene['graphic_id'],
                        samples=[dict(**x,global_s=global_time(scene['chapter'],x['local_s']),nearest_frame=round(global_time(scene['chapter'],x['local_s'])*fps)) for x in candidates],
                        narrative_time_basis='native큐와실측EDL.실제소스화면전환경계는완성소스수신후대조',
                        additional_required='소스T앵커/최대줌/모든정보표시상태/강조대상/제목·출처글자경계'))
boundaries = []
for segment in edl['segments'][1:]:
    frame = round(segment['global_start_s']*fps)
    boundaries.append(dict(id=segment['id'],time_s=segment['global_start_s'],frames=[frame-1,frame,frame+1],
                           check='입출경계연결·이전장면fallback·브랜드자막hold·본문빈박스'))
for interval in edl['caption_hidden_intervals']:
    for side in ['start_s','end_s']:
        frame = round(interval[side]*fps)
        valid_frames = sorted({min(round(edl['total_seconds']*fps)-1,max(0,n)) for n in [frame-1,frame,frame+1]})
        boundaries.append(dict(id=interval['reason']+'/'+side,time_s=interval[side],frames=valid_frames,check='브랜드/마지막CTA무음에서글자와흰박스숨김'))
write('encoded_sampling_plan.json',dict(status='prepared_not_executed',fps=fps,edl_sha256=sha(edl_path),script_sha256=packet['script_sha256'],timing_sha256=packet['timing_sha256'],scenes=samples,boundaries=boundaries,
      frame_index_rule='EDL PTS기준30fps.실제MP4 timebase확인후글로벌PTS/연속decode순번과교차.파일이름만으로원본프레임판정금지.',
      actual_encoded_frames_inspected=0, continuous_playback='unchecked',actual_listening='unchecked'))
package = []
for name in ['metadata_measured.json','description_measured.md','thumbnail.png']:
    p = EP/'outputs/private-release-v1'/name
    row = dict(path=p.as_posix(),sha256=sha(p),bytes=p.stat().st_size,review='파일/해시만기록;최종내용·작은화면검수대기')
    if name.endswith('.png'):
        raw=p.read_bytes()
        assert raw[:8] == b'\x89PNG\r\n\x1a\n'
        row['width'],row['height']=struct.unpack('>II',raw[16:24])
    package.append(row)
source_handoff = EP/'editor/handoff.json'
source_stage = read(source_handoff)
coverage = dict(
    script_sha256=packet['script_sha256'],timing_sha256=packet['timing_sha256'],
    approved_data_reuse='사실56개·검증사례18개·B금리전환 입력해시 고정.157산술/신생아원문검수 재실행없음.',
    caption_source_text=dict(cues=150,scenes=45,checks=text['checks'],failures=0,scope='원문span·표시/읽기변환·보호숫자·단위·원어경계대조'),
    isolated_font_geometry=dict(cues=150,failures=0,max_line_width_px=glyph['max_line_width_px'],limit_px=1600,font='실제Pretendard400/40px·50px행높이·WOFF2 SHA고정',source_or_encoded=False),
    harness_visual_inspection=dict(count=2,cue_ids=['C08_S036Q003','C08_S033Q003'],scope='격리폰트harness 이미지 직접열람;실제45소스/MP4아님'),
    edl_srt_reuse=dict(receipt=receipt_path.as_posix(),receipt_sha256=sha(receipt_path),edl_sha256=sha(edl_path),srt_sha256=sha(srt_path),checked_cues=receipt['checked_cues'],max_rounding_error_s=receipt['max_caption_rounding_error_s'],math_reexecuted=False),
    source_media=dict(status='waiting_actual_measured_source_handoff',producer_handoff_status=source_stage['status'],producer_handoff_sha256=sha(source_handoff),source_frames_45='unchecked',source_CLI='현재3개임시템플릿receipt는완성45소스통과로승계하지않음',title_footer_choreography_semantics='unchecked_until_actual_sources'),
    encoded_media=dict(status='waiting_actual_MP4',sample_plan='encoded_sampling_plan.json',actual_frames_inspected=0,stream_probe='unchecked',full_decode='unchecked'),
    playback='unchecked',actual_listening='unchecked',audio_owner='Kant qa/audio-v1',package_inventory=package,
    network='HTTP차단로컬headless측정만.외부전송/유료호출없음')
write('findings.json',dict(status='readiness_only_not_media_approval',critical=0,required=0,recommended=0,findings=[],unchecked=['실제45소스프레임/CLI/앵커·모션·의미·제목·출처','실제MP4전량decode/프레임','최종썸네일·패키지내용'],checked_revision=dict(script_sha256=packet['script_sha256'],timing_sha256=packet['timing_sha256'],css_sha256=packet['css_sha256'])))
write('ready.json',dict(status='ready_for_measured_source_review',media_approved=False,source_approved=False,checked_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),coverage=coverage,
      next_input='Carson의현재45장면완성source HTML/EDL/T앵커/CLI/BBox/프레임핸드오프.이후실제MP4를별도로전달.',
      reviewer_policy='필수이슈는실제scene/time/SHA/증거프레임에귀속.다른소유파일수정하지않음.'))
write('issue_READINESS.json',dict(issue_id='SOURCE-QA-READY',scene_id='ALL45/CUES150',problem='준비검수통과.완성45소스/MP4검수대기.',evidence='ready.json/caption_text_review.json/caption_glyph_review.json',proposal='현재실측45소스가준비되면HTML·EDL·T앵커·CLI/BBox·대표/경계프레임경로와SHA전달.',impact='측정자막통과는본문/최종미디어승인으로확대하지않음.',owner='main / Carson',status='ready',direct_message='직접agent메시지도구없음.로컬issue/최종경로로인계.'))
write('handoff.json',dict(status='ready_for_measured_source_review',source_approved=False,media_approved=False,
      outputs=['qa/source-media-v1/ready.json','qa/source-media-v1/findings.json','qa/source-media-v1/caption_text_review.json','qa/source-media-v1/caption_glyph_review.json','qa/source-media-v1/scene_review_plan.json','qa/source-media-v1/encoded_sampling_plan.json'],
      input_versions=dict(script_sha256=packet['script_sha256'],timing_sha256=packet['timing_sha256'],edl_sha256=sha(edl_path),srt_sha256=sha(srt_path)),
      validation='150큐원문/숫자/단위592검사0실패·실제CSS/WOFF2전량기하0실패·최대줄1116.48/1600px.격리harness2프레임실제열람.EDL/SRT기존통과해시재사용.',
      unresolved=['실제45소스프레임/앵커/모션/CLI','실제MP445장면+경계/최대정보프레임·decode','최종패키지시각/내용'],affected_scenes='ALL45/CUES150',next_owner='Carson:현재완성source핸드오프;main:후속검수호출/최종Claude·release',
      listening_playback='둘다unchecked;audio-v1범위와분리',external_calls=0))
print(json.dumps(dict(status='ready_for_measured_source_review',source_approved=False,media_approved=False,captions=150,scenes=45,total_seconds=edl['total_seconds'],hook_cut_s=edl['hook_cut_s'],outro_start_s=next(s['global_start_s'] for s in edl['segments'] if s['id']=='clean_brand_outro')),ensure_ascii=False))
