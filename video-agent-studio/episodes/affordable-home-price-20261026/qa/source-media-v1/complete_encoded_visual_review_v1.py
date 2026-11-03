"""Record actually viewed encoded samples and packaging; keep DSP as a separate gate."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import shutil

QA = Path(__file__).resolve().parent
EP = QA.parent.parent
PROD = EP / 'outputs/private-production-v1'
RELEASE = EP / 'outputs/private-release-v2'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ref(path):
    return {'path': Path(path).as_posix(), 'sha256': sha(path)}


def write(name, value):
    (QA / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


stamp = datetime.now(timezone.utc).isoformat()
plan = read(QA / 'encoded_sampling_plan_v4.json')
evidence_path = QA / 'actual_encoded_evidence_v1.json'
evidence = read(evidence_path)
producer_path = PROD / 'encoded_frame_plan.json'
producer = read(producer_path)
receipt_path = EP / 'editor/render_receipt.json'
receipt = read(receipt_path)
video = Path(receipt['final_file'])
video_sha = sha(video)
assert video_sha == evidence['video']['sha256'] == producer['final_sha256'] == 'ad9df5989c019395e9ea9eb7877c81300cf78e9ab611536ebcc7431c8fc3609a'
for value in plan['artifacts'].values():
    assert sha(value['path']) == value['sha256']
source = read(QA / 'source_approval_v4.json')
assert source['approved'] and not source['required'] and not source['critical']
audio = read(QA / 'audio_gate_consolidation_v3.json')
assert audio['approved'] and not audio['actual_listening']
technical = read(QA / 'encoded_provenance_and_package_checks_v1.json')
assert technical['status'] == 'pass' and technical['overlapping_encoded_frames_pixel_identical'] == 90

viewed = []
manual_frames = set()
for sheet in producer['contact_sheets']:
    viewed.append({**ref(PROD / sheet['file']), 'scope': '45장면 대표 화면의 의미/그래픽/가독성/수치/출처 배치'})
manual_frames.update(item['global_frame'] for item in producer['samples'] if item['role'] == 'representative')
for sheet in evidence['contact_sheets']:
    viewed.append({**ref(sheet['path']), 'scope': sheet['group'], 'crop': sheet['crop'],
                   'frame_indices': sheet['frame_indices']})
    manual_frames.update(sheet['frame_indices'])
full_resolution_files = ['00065.png', '00071.png', '00117.png', '00118.png', '00136.png',
                         '00160.png', '00161.png', '00007.png', '00143.png']
evidence_dir = video.parent / 'encoded-evidence'
full_resolution = []
for name in full_resolution_files:
    sample = next(item for item in producer['samples'] if Path(item['file']).name == name)
    row = {**ref(evidence_dir / name), 'frame_index': sample['global_frame'],
           'time_s': sample['global_time_s'], 'scene_id': sample['scene_id'],
           'cue_id': sample.get('cue_id'), 'scope': '실제 1920x1080 전체 프레임 열람'}
    full_resolution.append(row)
    viewed.append(row)
    manual_frames.add(row['frame_index'])

closure_specs = [
    ('SOURCE-TAX-001', ['00065.png', '00071.png'], ['S016', 'S018'], '열린 축 경로의 의도하지 않은 검정 삼각형 없음. 세율 곡선과 계단 선이 정상.'),
    ('SOURCE-CLIP-002', ['00160.png', '00161.png'], ['S040'], '동일 폰트의 마지막 설명 글리프가 패널 하단 안에서 온전히 보임.'),
    ('SOURCE-FOCUS-003', ['00117.png', '00118.png', '00160.png', '00161.png'], ['S031', 'S040'], 'S031은 발화 상품별 시계만 강조. S040은 월액과 저축여유의 강조가 해당 자막 큐로 분리됨.'),
    ('SOURCE-BRAND-004', ['00007.png'], ['S002'], '브랜드 뒤 첫 본문 프레임 f841/28.033333초에 S002를 표시. S001 재등장 없음; 첫 실제 자막 시각 유지.')
]
closures = []
for issue_id, names, scenes, result in closure_specs:
    proofs = [row for row in full_resolution if Path(row['path']).name in names]
    closures.append({'issue_id': issue_id, 'scene_id': scenes, 'timecode': [row['time_s'] for row in proofs],
                     'severity': 'required', '문제': '기존 필수 소스 이슈의 실제 인코딩 반영 확인',
                     'evidence': proofs, '수정안': '추가 수정 불필요', 'owner': 'video_editor / Carson',
                     'status': 'closed_actual_encoded', 'result': result,
                     'checked_revision': {'video_sha256': video_sha, 'source_approval': ref(QA / 'source_approval_v4.json')}})
write('source_issue_encoded_closure_v1.json', {'status': 'pass', 'required_issues': [], 'critical_issues': [], 'closures': closures})

coverage = {
    'method': '실제 MP4에서 추출한 정지 프레임 표본을 contact sheet/자막 ROI 및 중요 전체 프레임으로 열람',
    'encoded_video_opened_for_independent_decode': True, 'encoded_scenes_reviewed': 45,
    'scene_representative_frames_reviewed': 45, 'scene_start_and_end_samples_reviewed': 90,
    'chapter_samples_reviewed': 10, 'assembly_joins_reviewed': 12, 'assembly_join_frames_reviewed': 36,
    'burned_caption_midpoints_reviewed': 150, 'max_text_top10_cues_included': plan['max_text_cue_ids'],
    'critical_full_resolution_frames_reviewed': len(full_resolution), 'manually_viewed_unique_encoded_frames': len(manual_frames),
    'manually_viewed_frame_indices': sorted(manual_frames), 'independent_extracted_frames': 552,
    'all_552_actual_PTS_validated': True, 'all_552_frames_manually_viewed': False,
    'producer_extracted_unique_frames_SHA_verified': 185, 'producer_and_independent_pixel_identical_frames': 90,
    'actual_listening': False, 'continuous_playback': False, 'sampled_review_only': True,
    'full_AV_decode': {'scope': 'Carson 실제 렌더 영수증 및 동일 MP4 SHA로 재사용; 사람이 연속 재생한 뜻 아님',
                       'returncode': receipt['decode_returncode'], 'receipt': ref(receipt_path)},
    'inherited_source_approval': ref(QA / 'source_approval_v4.json'),
    'audio_ASR_gate': audio['receipt'], 'audio_ASR_scope': audio['approval_scope'],
    'final_encoded_DSP_receipt': None, 'subjective_naturalness_reviewed': False,
    'limitations': ['150큐는 각 실제 native 중간 프레임을 확인함. 모든 자막의 매 순간 연속 확인은 아님.',
                    '본문 native 큐 공백에는 승인된 흰 자막 rail이 유지됨. clean intro/outro 및 최종 무음 CTA만 EDL의 숨김 구간이며 그 구간은 정상.',
                    '준비 계획의 S002 첫 자막 전 빈 rail 없음이라는 문구는 승인된 소스 정책과 불일치한 검수 가정이었다. 실제 결함으로 분류하지 않음.',
                    '정책56항목/18사례와 B 재설정 산술은 불변 SHA 기준 기존 승인 근거 재사용. 재산술/재수집 미실시.']}
recommended = [{'issue_id': 'SOURCE-REPEAT-005', 'severity': 'recommended', 'scene_id': 'chapter_title_cards',
                'timecode': [item['frame'] / 30 for item in plan['chapters'][1:]],
                '문제': '일부 장 구분 카드에서 집/문서/봉투 도형이 반복됨.', '수정안': '후속 편에서 구분 카드 시각적 변주 확대.',
                'owner': 'video_editor', 'status': 'accepted_nonblocking_inherited',
                'evidence': [row for row in viewed if row.get('scope') == 'chapter10'],
                'checked_revision': {'video_sha256': video_sha}}]
visual = {'status': 'actual_encoded_visual_pass', 'approved': True, 'approval_scope': '인코딩 화면·번인 자막의 명시된 표본 범위',
          'at_utc': stamp, 'video': ref(video), 'required_issues': [], 'critical_issues': [], 'recommended_issues': recommended,
          'burned_in_captions_verified': True, 'coverage': coverage, 'viewed_evidence': viewed,
          'machine_evidence': ref(evidence_path), 'closure_receipt': ref(QA / 'source_issue_encoded_closure_v1.json'),
          'final_media_approved': False, 'remaining_gate': 'Kant final encoded DSP evidence'}
write('encoded_visual_review_v1.json', visual)
write('encoded_visual_findings_v1.json', {'video_sha256': video_sha, 'required_issues': [], 'critical_issues': [],
                                        'recommended_issues': recommended, 'closed_required': closures})

package = {'status': 'pass', 'approved': True, 'at_utc': stamp, 'revision': 'private-release-v2',
           'artifacts': {key: plan['artifacts'][key] for key in ('metadata', 'description', 'thumbnail')},
           'required_issues': [], 'critical_issues': [], 'recommended_issues': [],
           'checks': ['제목46자·내용과 6/9/12억 사례 일치·단정적 승인/수익 보장 문구 없음',
                      '비공개 설정·정책 기준일·가구A/B 조건·보증/공제·감면 전 세금/부가세/계획비 조건이 실제 본문과 일치',
                      '첫 영상 실제 링크 exEGpjcqdF0·주요 출처 링크·음악 저작자/CC BY4.0 표시 확인',
                      '10개 chapter 표시는 현재 EDL 글로벌 초의 내림값 및 설명 timeline과 일치',
                      '썸네일1280x720 전체와320x180 축소에서 한글·제목 여백·질문형 주장·일반 주거 이미지 의미 적합'],
           'source_links_scope': '제공된 고정 연구 승인/소스팩과 링크 문자열 대조. 외부 링크 재방문 없음.',
           'normalized_description_utf8_bytes': technical['description_utf8_bytes_normalized'],
           'thumbnail_viewed': [ref(RELEASE / 'thumbnail.png'), ref(QA / 'thumbnail_release_v2_320.png')]}
write('packaging_review_v2.json', package)

final_path = QA / 'final_review.json'
preserved = QA / 'final_review.pre_encoded.json'
if not preserved.exists():
    shutil.copyfile(final_path, preserved)
final = read(final_path)
final.update({'status': 'actual_encoded_visual_and_package_pass_pending_final_DSP', 'approved': False,
              'video_sha256': video_sha, 'video_path': video.as_posix(), 'video_bytes': video.stat().st_size,
              'required_issues': [], 'critical_issues': [], 'burned_in_captions_verified': True,
              'reviewed_at_utc': stamp, 'coverage': coverage,
              'pending_gates': ['consolidate_Kant_final_encoded_DSP_for_exact_MP4'],
              'issues_note': '화면/자막/패키지 필수 이슈0. 최종DSP 통합 전 최종 미디어 승인은 대기.',
              'encoded_visual_receipt': ref(QA / 'encoded_visual_review_v1.json'),
              'packaging_receipt': ref(QA / 'packaging_review_v2.json'),
              'approval_scope': '최종DSP 대기. 실제 청취·연속 재생은 미실시. 게시/업로드 승인은 총괄 별도.'})
write('final_review.json', final)
write('final_encoded_QA_handoff.json', {'status': final['status'], 'approved': False,
                                      'final_review': ref(final_path), 'visual_review': ref(QA / 'encoded_visual_review_v1.json'),
                                      'packaging_review': ref(QA / 'packaging_review_v2.json'),
                                      'required_issues': [], 'critical_issues': [], 'pending': final['pending_gates'],
                                      'actual_listening': False, 'continuous_playback': False,
                                      'next': 'Kant 실제 최종DSP 영수증을 동일 MP4 SHA로 연결한 후 최종 판정. 총괄이 최종Claude/배포 게이트 진행.'})
print(json.dumps({'status': final['status'], 'manual_unique_frames': len(manual_frames),
                  'burned_caption_midpoints': 150, 'required_issues': [], 'video_sha256': video_sha}, ensure_ascii=False))
