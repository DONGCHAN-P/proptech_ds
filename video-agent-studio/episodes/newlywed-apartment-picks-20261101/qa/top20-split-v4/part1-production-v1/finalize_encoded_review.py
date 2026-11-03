"""실제 view_image로 본 범위를 기록하는 PART1 v4 독립 QA 핸드오프."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
from PIL import Image

Q=Path(__file__).resolve().parent;E=Q.parents[2];ROOT=E.parents[2]
D=E/'director/top20-split-v4/part1-production-v1'
V=E/'outputs/top20-split-v4/part1/part1_free_v4.mp4'
EXPECTED='9de0ac10a1d177b49da95b720d863f913fbf8ecc8cdb972a461eb02524b180b2'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def save(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf-8')
assert sha(V)==EXPECTED
base=read(Q/'v4/encoded_frame_manifest.json')
additional=read(Q/'v4/additional_encoded_manifest.json')
packet=read(Q/'encoded_packet_v4/packet_checks.json')
supp=read(Q/'encoded_packet_v4/supplemental_manifest.json')
assert base['video_sha256']==additional['video_sha256']==packet['technical']['video_sha256']==EXPECTED
assert len(base['frames'])==104 and len(additional['frames'])==12 and len(supp)==5
assert not packet['technical_problems']
for f in additional['frames']+supp:
    p=Path(f['file']);assert p.exists() and sha(p)==f['sha256']
    with Image.open(p) as im:assert im.size==(1920,1080)

# 이미 실행한 view_image 호출 목록을 기록하며 자동 시각 판정을 뜻하지 않는다.
full_base=[92,93,94,95,96,97,98,99,57,3,102]
full_extra=[10,11,4,5,3]
views=[]
for collection,indices in [(base['frames'],full_base),(additional['frames'],full_extra)]:
    for i in indices:
        f=collection[i]
        views.append(dict(file=f['file'],sha256=f['sha256'],time_s=f['time_s'],inspection='view_image individual1920x1080 frame',visually_viewed=True))
for f in supp:
    views.append(dict(file=f['file'],sha256=f['sha256'],requested_time_s=f['requested_time_s'],inspection='view_image individual1920x1080 frame; independently extracted from actual MP4',visually_viewed=True))
assert len(views)==21
contacts=[Q/f'v4/contact_{i:02d}.jpg' for i in range(1,10)]+[Q/'v4/price_final_contact.jpg']
contact_evidence=[dict(file=str(p),sha256=sha(p),visually_viewed=True,scope='overview only; reduced-size frame cells') for p in contacts]
save(Q/'encoded_packet_v4/manual_visual_coverage.json',dict(contact_sheets=contact_evidence,overview_base_frame_files=104,overview_additional_frame_files=12,individual_full_resolution_views=views,individual_full_resolution_count=21,additional_independently_extracted_frames=5,actual_listening=False,continuous_playback=False))

now=datetime.now(timezone.utc).isoformat()
issue3=dict(issue_id='QA-PART1-ENCODED-REC-003',scene_id='P01-R20',timecode='00:46.534 requested seek (actual encoded frame near00:46.567)',severity='recommended',문제='장면 첫 부제의 페이드인 동안 기존 지도 이미지의 상세 제목이 짧게 겹쳐 보입니다.',evidence=dict(file=supp[0]['file'],sha256=supp[0]['sha256'],observed='구 전체·생활권 상세 아래에 기존 미리내마을 상세 제목 잔상이 비침.47.034초 표본부터 부제 배경이 완전히 불투명해지고 겹침이 사라짐.',comparison_file=supp[1]['file']),수정안='다음 수정 때 부제 배경은 처음부터 불투명하게 유지하고 글자만 페이드인하면 첫 약0.2초의 제목 겹침을 줄일 수 있습니다.',owner='director/editor',status='open_recommended',checked_revision=dict(revision='part1_free_v4',video_sha256=EXPECTED),created_at=now,delivery_impact='로컬 검토본 통과를 막지 않는 짧은 제목 전환 권장 개선. 하단 의미 단위 자막 잘림은 발견하지 않음.')
save(Q/'issue_QA-PART1-ENCODED-REC-003.json',issue3)
findings=read(Q/'findings.json')
for i in findings:
    if i['issue_id']=='QA-PART1-SOURCE-001':
        i['status']='resolved_verified'
        i['checked_revision']=dict(revision='part1_free_v4',video_sha256=EXPECTED)
        i['encoded_verification']=[additional['frames'][10],additional['frames'][11]]
        i['resolution']='실제 MP4의 두 브랜드 중간 프레임과 종료 프레임에서 승인 브랜드 영상·제목·CTA가 확인됨. WAV 오연결 해결.'
    elif i['issue_id']=='QA-PART1-SOURCE-002':
        i['status']='resolved_verified'
        i['checked_revision']=dict(revision='part1_free_v4',video_sha256=EXPECTED)
        i['encoded_verification']=supp[3]
        i['resolution']='93.191초 요청 시점 실제 MP4 표본에서 신중동역 강조만 보이고 별개 중동역 추가 ring 없음. 학교2곳 위치도 원본 지도와 정렬.'
    save(Q/('issue_'+i['issue_id']+'.json'),i)
findings=[i for i in findings if i['issue_id']!=issue3['issue_id']]+[issue3]
save(Q/'findings.json',findings)

signal=read(D/'evidence/v4/encoded_audio_signal.json')
assert signal['video_sha256']==EXPECTED and signal['source_voice_sha256']=='6d6123f988e8f2aacfd2ac7ed7b2fd45aaf5c804ac53a6f71598eca37b0edd72'
assert len(signal['checked_scene_windows'])==12
assert signal['actual_listening_performed'] is False
minimum=min(s['pearson_source_voice_to_encoded_mix'] for s in signal['checked_scene_windows'])
assert minimum>.9997 and signal['peak_pcm']<32767
lock=read(D/'locked_timing.json')
outro=next(b for b in lock['brand_inserts'] if b['kind']=='outro')
gap=outro['start_s']-lock['last_spoken_end_s']
assert gap>=3 and gap<3.0001
before_after=[]
for s in lock['scenes'][1:]:
    fs=[f for f in base['frames'] if f['scene_id']==s['scene_id'] and f['phase'] in ['cut_before','cut_after']]
    assert len(fs)==2
    assert any(f['phase']=='cut_before' and 0<s['start_s']-f['time_s']<.041 for f in fs)
    assert any(f['phase']=='cut_after' and 0<f['time_s']-s['start_s']<.041 for f in fs)
    before_after.append(dict(scene_id=s['scene_id'],boundary_s=s['start_s'],samples=fs,view_scope='both viewed as contact-sheet cells; nominal±.040s, not exact boundary-frame or continuous playback verification'))

for p in [D/'evidence/v4/decode.log',D/'evidence/v4/decode.log.stderr.log']:assert p.exists() and p.stat().st_size==0
assets=read(Q/'source_review_evidence.json')
scene_coverage=[]
for s in lock['scenes']:
    rows=[f for f in base['frames'] if f['scene_id']==s['scene_id']]
    phases=sorted({f['phase'] for f in rows if f['phase'] not in ['cut_before','cut_after']})
    scene_coverage.append(dict(scene_id=s['scene_id'],overview_frames=[f['file'] for f in rows],phases=phases,visually_viewed_at='contact sheet overview; individual full-resolution subset listed separately',result='no required/critical pixel defect observed in sampled scope'))
price_values=assets['price_display_evidence']
assert len(price_values)==20
reused=[]
for p in [Q/'audio_script_review.json',Q/'ASR_support_review.json',Q/'brand_binding_patch_review.json',Q/'provisional_source_review.json',E/'qa/top20-split-v4/script_review.json',E/'qa/top20-split-v4/map_data_review.json',E/'qa/top20-split-v4/map_revision_v3_review.json']:
    reused.append(dict(path=str(p),sha256=sha(p)))

report=dict(task_id='PART1-v4-independent-final-media-review',generated_at=now,status='passed_for_local_review',video=str(V),video_sha256=EXPECTED,required_open_count=0,critical_open_count=0,recommended_open_count=1,reviewer='independent_QA_role',checked_revision=dict(render='part1_free_v4',project='final-v3 with corrected visual brand binding',script_sha256='b20616e6c8b5e128f41bc505ba79875ad90735bee38ecd16d1099739c0c1f951',locked_timing_sha256=sha(D/'locked_timing.json'),source_audio_sha256=signal['source_voice_sha256']),technical=packet['technical'],counts=dict(scenes=12,sentences=85,provider_words=1277,semantic_caption_cues=176,parent_base_encoded_frame_files=104,parent_additional_encoded_frame_files=12,independently_extracted_encoded_frame_files=5,overview_sample_entries=116,contact_sheets_viewed=10,individual_full_resolution_frames_viewed=21,all_viewed_frame_file_entries=121,scene_cut_pairs=11,scene_cut_frame_samples=22,intro_outro_sentence_samples=8,long_caption_samples_full_resolution=8,distinct_region_photo_files=10,final_price_comparison_states=10,price_display_rows=20,brand_midpoints=2),coverage=dict(scene_by_scene=scene_coverage,all_scene_phases='62 primary scene/phase frame entries checked in overview, plus8 intro/outro sentence frames',boundaries=before_after,maximum_zoom='fixed full-screen source plates; no map or photo zoom transform in current source. Fixed maximum-scale layouts covered in all10 regions overview, with full-resolution subset; no continuous motion review.',photos='10 region photos visibly distinct in contact sheets and10 frozen source hashes unique; actual-place/source attribution matched prior source QA. R20/R11 credit panels directly read at full resolution. No new site visit or rights re-research.',prices='all10 final-state comparison frames read in contact sheet;3 additional full-resolution final price views R16/R15/R17. All20 source row values/labels/transaction_n/complex_n or distribution denominator/period/83–85㎡ matched in source QA. Mid-reveal empty values not treated as omissions.',price_display_rows=price_values,semantic_captions='all176 text/timing tuples matched lock;8 long-caption actual encoded frames individually viewed, no clipping found. Other cues not individually visually read through playback.',point_legend='6 fixed price-bin colors and school/station/commerce symbols visible; regional source point quantities and bounds inherited by matching source SHA. Sampled actual map markers align with underlying map. R20 wrong additional station ring absence verified at93.191s requested seek.',source_clipping='OSM/licensing/date/area lines visible above captions in full-resolution map samples. Two photo credits fully viewed including long R11 credit. Remaining photo credit placements checked at overview only.',brand='intro/outro each one source-timed muted clip; actual middle frames individually viewed at8.317s/595.168s; no body captions overlay brand. Final encoded frame also directly viewed.',ending_hold=dict(last_provider_word_end_s=lock['last_spoken_end_s'],outro_start_s=outro['start_s'],metadata_gap_s=gap,hold_frame_s=base['frames'][102]['time_s'],hold_visual='CTA retained, caption absent; full-resolution frame viewed',acoustic_end='not listened; native provider boundary scaled by1.35'),context_to_price_fade='3 additional actual encoded R20 frames before/mid/after fade directly viewed; point field fades in with fixed map geometry and legend',last_frame=dict(requested_seek_s=600.16,video_frame_count=18006,expected_last_frame_index_0based=18005,expected_timestamp_s=18005/30,file=supp[4]['file'],viewed=True,observed='outro brand/next/recommended/subscribe composition remains visible, no blank tail',timestamp_scope='accurate seek600.160s selects the next final30fps frame; frame index inferred from stream count/fps'),continuous_playback=False,actual_listening=False,full_film_watched=False,Claude_review='not_called_no_external_transfer'),audio_evidence=dict(signal_report=str(D/'evidence/v4/encoded_audio_signal.json'),signal_report_sha256=sha(D/'evidence/v4/encoded_audio_signal.json'),scene_windows=12,min_source_to_encoded_mix_Pearson=minimum,peak_dbfs=signal['peak_dbfs'],no_integer_clipping=signal['peak_pcm']<32767,measurement_owner='director; saved artifact read and video/source SHA binding independently checked',pronunciation='source/display/read all85 and numeric86 checked; native metadata exact; local ASR small12/medium5 reused across visual-only binding patch; actual listening and naturalness unchecked'),strict_decode=dict(performed_by='director',reported_passed=True,logs=[dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size) for p in [D/'evidence/v4/decode.log',D/'evidence/v4/decode.log.stderr.log']],independently_rerun=False,scope='parent completion reports strict decode pass; retained error logs inspected empty. QA independently read actual streams/hashed MP4/extracted5frames rather than repeating full decode.'),findings=findings,reused_QA=reused,manifests=[dict(path=str(p),sha256=sha(p)) for p in [Q/'v4/encoded_frame_manifest.json',Q/'v4/additional_encoded_manifest.json',Q/'encoded_packet_v4/supplemental_manifest.json']],manual_visual_evidence=dict(path=str(Q/'encoded_packet_v4/manual_visual_coverage.json'),sha256=sha(Q/'encoded_packet_v4/manual_visual_coverage.json')),source_watchlist_retained='Source review nonblocking station-word timing candidates R19/R14 retained; phonetic synchronization not certified by sampled stills or ASR.',scope_limit='PART1 local review only. PART2, thumbnail, guide/ZIP/package integrity and upload are outside this MP4 QA packet. Source/technical checks do not certify continuous audiovisual quality.',next_owner='director local completed pack/finalizer; user local review; separate pre_upload gate preserved',paid_calls=0,network_calls=0,external_messages_sent=0,actual_listening=False,continuous_playback=False)
save(Q/'final_review.json',report)
h=read(Q/'handoff.json');h.update(status=report['status'],video=str(V),video_sha256=EXPECTED,required_open_count=0,critical_open_count=0,recommended_open_count=1,open_issue_ids=[issue3['issue_id']],affected_scenes=[s['scene_id'] for s in lock['scenes']],validation=report['counts'],unresolved=['actual listening/naturalness unchecked','continuous playback unchecked',issue3['issue_id']],next_owner=report['next_owner'])
h['outputs']=list(dict.fromkeys(h['outputs']+[str(Q/'final_review.json'),str(Q/'encoded_packet_v4/manual_visual_coverage.json')]))
h['output_hashes']={Path(p).name:sha(Path(p)) for p in h['outputs']}
save(Q/'handoff.json',h)
assert read(Q/'final_review.json')['status']=='passed_for_local_review'
assert read(Q/'final_review.json')['video_sha256']==EXPECTED
print(json.dumps(dict(status=report['status'],video_sha256=EXPECTED,required=0,critical=0,recommended=1,overview=116,full_resolution=21,final_review_sha256=sha(Q/'final_review.json')),ensure_ascii=False))

