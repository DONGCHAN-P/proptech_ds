"""Consolidate completed exact-video visual/package/ASR/DSP evidence."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import shutil

QA = Path(__file__).resolve().parent
EP = QA.parent.parent


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ref(path):
    return {'path': Path(path).as_posix(), 'sha256': sha(path)}


def write(name, data):
    (QA / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


final_path = QA / 'final_review.json'
final = read(final_path)
visual = read(QA / 'encoded_visual_review_v1.json')
package = read(QA / 'packaging_review_v2.json')
caption_state_path = QA / 'encoded_caption_state_check_v1.json'
caption_state = read(caption_state_path)
signal_path = EP / 'qa/audio-v1/final-signal-v1/signal_receipt.json'
signal = read(signal_path)
assert signal['approved_for_technical_signal_scope'] and not signal['required_issues'] and not signal['critical_issues']
assert visual['approved'] and package['approved'] and caption_state['status'] == 'pass'
assert not visual['required_issues'] and not package['required_issues']
assert sha(final['video_path']) == final['video_sha256'] == signal['video_sha256'] == signal['video']['sha256']
assert final['script_sha256'] == signal['script_sha256']
assert final['artifacts']['timing']['sha256'] == signal['timing_sha256']
for frozen in final['artifacts'].values():
    assert sha(frozen['path']) == frozen['sha256'], frozen['path']
for frozen in [signal[key] for key in ('renderer_receipt', 'frozen_audio_gate', 'canonical_carve_receipt',
                                      'EDL', 'source_assembly_filter', 'ffmpeg', 'runner')] + [signal['measurements']['analysis_log']]:
    assert sha(frozen['path']) == frozen['sha256'], frozen['path']
m = signal['measurements']
assert m['audio_full_decode_passes'] == 1 and m['sample_rate'] == 48000 and m['channels'] == 2
assert all(m[key] == 0 for key in ('rail_or_over_full_scale_sample_values', 'NaN_sample_values',
                                  'Inf_sample_values', 'denormal_float32_sample_values'))
edl = read(final['artifacts']['edl']['path'])
joins = signal['measurements']['encoded_EDL_join_signal_samples']
assert len(joins) == len(edl['segments']) - 1 == 12
for row, segment in zip(joins, edl['segments'][1:]):
    assert row['center'] == round(segment['global_start_s'] * 48000)
assert not signal['coverage']['actual_listening'] and not signal['coverage']['continuous_playback']

for old_name, preserved_name in [('final_review.json', 'final_review.pre_signal_v1.json'),
                                 ('final_encoded_QA_handoff.json', 'final_encoded_QA_handoff.pre_signal_v1.json'),
                                 ('handoff.json', 'handoff.source_v4.json'), ('ready.json', 'ready.source_v4.json')]:
    old, preserved = QA / old_name, QA / preserved_name
    if old.exists() and not preserved.exists():
        shutil.copyfile(old, preserved)

stamp = datetime.now(timezone.utc).isoformat()
signal_ref = ref(signal_path)
final['coverage'].update({
    'final_encoded_DSP_receipt': signal_ref, 'final_encoded_DSP_consolidated': True,
    'final_encoded_DSP_scope': 'Kant 동일 MP4 전체 AAC 1회 기술신호 분석 및 12접합부 신호 표본; 청취/주관적 음질/음악 균형 승인 아님',
    'final_encoded_DSP_metrics': {key: m[key] for key in ('integrated_LUFS', 'LRA_LU', 'true_peak_dBTP',
                                                        'rail_or_over_full_scale_sample_values', 'NaN_sample_values',
                                                        'Inf_sample_values', 'denormal_float32_sample_values',
                                                        'sample_rate', 'channels')},
    'caption_state_samples_checked': caption_state['body_samples_checked'],
    'caption_state_check_receipt': ref(caption_state_path),
    'actual_listening': False, 'continuous_playback': False,
    'subjective_naturalness_reviewed': False, 'perceived_music_voice_balance_reviewed': False
})
final.update({
    'status': 'approved_exact_media_with_sampled_visual_ASR_and_technical_signal_scope', 'approved': True,
    'approved_at_utc': stamp, 'pending_gates': [], 'required_issues': [], 'critical_issues': [],
    'burned_in_captions_verified': True, 'signal_receipt': signal_ref,
    'caption_state_check': ref(caption_state_path),
    'issues_note': '실제 인코딩 화면/자막/패키지 및 제공된 최종 ASR·기술신호 범위에서 필수·치명 이슈0.',
    'approval_scope': '독립 Codex 최종 미디어 검수: 정확한 MP4 및 고정 SRT/대본/메타데이터/설명/썸네일. 45장면·150큐·명시된 경계 표본, 기존 소스/내용 승인 및 Kant ASR·최종DSP 통합. 실제 청취·연속 재생·주관적 자연스러움/음악균형 검수 미실시.',
    'other_owner_gates': {'Claude_final_review': '총괄이 별도 실제 결과 확인',
                          'release_and_platform_approval': '총괄 소유; 이 파일이 업로드 명령 또는 플랫폼 승인 영수증은 아님'}
})
write('final_review.json', final)
write('final_findings.json', {'status': 'pass_for_declared_media_scope', 'video_sha256': final['video_sha256'],
                             'required_issues': [], 'critical_issues': [],
                             'recommended_issues': visual['recommended_issues'],
                             'closed_required': read(QA / 'source_issue_encoded_closure_v1.json')['closures'],
                             'final_review': ref(final_path)})
handoff = {'status': 'exact_final_media_review_approved', 'approved': True,
           'video_sha256': final['video_sha256'], 'final_review': ref(final_path),
           'required_issues': [], 'critical_issues': [], 'burned_in_captions_verified': True,
           'coverage': {'scenes': 45, 'caption_midpoints': 150, 'chapter_samples': 10,
                        'scene_start_end_samples': 90, 'EDL_joins': 12, 'manual_unique_frames': 296,
                        'independent_extracted_PTS_checked_frames': 552},
           'signal_receipt': signal_ref, 'actual_listening': False, 'continuous_playback': False,
           'next_owner': 'video_director', 'next': '총괄이 별도 최종Claude 검수·배포 게이트 진행. 현재 정확한6개 입력SHA의 독립 미디어 검수 통과.'}
assert len(json.dumps(handoff, ensure_ascii=False)) <= 1600
write('final_encoded_QA_handoff.json', handoff)
write('handoff.json', handoff)
write('ready.json', {'status': handoff['status'], 'approved': True, 'final_review': ref(final_path),
                     'required': [], 'critical': [], 'actual_listening': False, 'continuous_playback': False})
print(json.dumps({'status': final['status'], 'approved': final['approved'],
                  'video_sha256': final['video_sha256'], 'final_review': ref(final_path),
                  'signal_receipt_sha256': signal_ref['sha256']}, ensure_ascii=False))
