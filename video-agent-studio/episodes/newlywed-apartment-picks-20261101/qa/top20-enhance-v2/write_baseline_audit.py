import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('C:/projects/realestate_reco')
EP = ROOT / 'video-agent-studio/episodes/newlywed-apartment-picks-20261101'
OUT = EP / 'qa/top20-enhance-v2'
OLD = EP / 'outputs/top20-production-v1/main/top20_main_free_v5.mp4'
FRAME_INDEX = EP / 'editor/top20-production-v1/evidence/encoded-main-v5/frames.json'
TIMING = EP / 'director/top20-production-v1/locked_timing.json'

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for part in iter(lambda: f.read(1024 * 1024), b''):
            h.update(part)
    return h.hexdigest()

def save(name, obj):
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

frames = json.loads(FRAME_INDEX.read_text(encoding='utf-8-sig'))
selected = [
    ('O001', '003-11.736s.jpg'), ('S003', '014-56.130s.jpg'),
    ('S011', '050-181.849s.jpg'), ('S022', '102-415.799s.jpg'),
    ('I001', '034-124.880s.jpg'), ('I002', '058-222.413s.jpg'),
    ('C001', '106-444.038s.jpg'), ('E001', '110-459.771s.jpg'),
]
evidence = []
for scene, filename in selected:
    row = next(f for f in frames if Path(f['file']).name == filename)
    actual = sha(row['file'])
    if actual != row['sha256']:
        raise RuntimeError('프레임 SHA 불일치: ' + filename)
    evidence.append(dict(scene_id=scene, timecode=round(row['time_s'], 6),
                         path=row['file'], sha256=actual,
                         inspection='view_image로 실제 이미지 시각 확인'))

probe = subprocess.run([
    str(ROOT / 'video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe'),
    '-v', 'error', '-show_entries',
    'format=duration,size:stream=index,codec_name,codec_type,width,height,r_frame_rate,sample_rate,channels,duration',
    '-of', 'json', str(OLD)
], capture_output=True, text=True, check=True)
metadata = json.loads(probe.stdout)
old_hash = sha(OLD)
if old_hash != '1cea67518687e604af5d89fd2aad4e9df1826d5460abaead780912be5f97f304':
    raise RuntimeError('기준 MP4가 전달 버전과 다릅니다.')

def item(issue, scene, time, severity, problem, ev, fix, owner='editor'):
    return dict(issue_id=issue, scene_id=scene, timecode=time, severity=severity,
                문제=problem, evidence=ev, 수정안=fix, owner=owner,
                status='new_revision_review_pending', checked_revision='main-v5')

findings = [
    item('EV2-B01', ['S003', 'S011', 'S022'], ['00:56.130', '03:01.849', '06:55.799'], 'required',
         '세 지역 모두 왼쪽 사진·오른쪽 큰 수도권 지도·하단 단일 막대가 같은 배치다. 사진 비율 차이로 원미구는 좌우, 옛 서구는 상하 여백이 크다. 이번 시각 개선 요청의 우선 수정 대상으로 지정한다.',
         [evidence[i] for i in [1, 2, 3]],
         '사진 중심·인접 규모 비교·상위권 강조의 세 구도를 적용한다. 사진 원비율에 맞춰 패널을 조정하고 고정 척도 순위 사다리로 전체 맥락을 연결한다. 실제 장소명·촬영시점·권리는 유지한다.'),
    item('EV2-B02', ['S003', 'S011', 'S022'], ['00:56.130', '03:01.849', '06:55.799'], 'recommended',
         '수도권 지도에서 현재 구 하나가 작은 색면으로만 강조되며 주변 기준 지명은 없다. 지도 면적에 비해 위치 설명 정보가 적다.',
         [evidence[i] for i in [1, 2, 3]],
         '검증된 경계를 작은 고정 위치 안내로 사용하고 현재 지역과 필요한 주변 기준 지명만 붙인다. 2024 옛 서구와 현 서구+검단구 범위 설명을 보존한다.'),
    item('EV2-B03', 'I001', '02:04.880', 'recommended',
         '중간 표본에서 두 방향 변화선·두 사진·19곳 요약이 동시에 보인다. 요약 발화의 초점을 차트와 별도로 강화할 여지가 있다. 정지 이미지로 기존 모션 순서는 판정하지 않는다.',
         [evidence[4]],
         '7,797쌍 공통 시작점 → 기흥 -111·연수 +78의 분기 → 비교 가능 19곳 중 증가6/감소13 순서로 실제 발화 앵커를 연결한다. 확대 세로축 7,600~7,900·연도·단위를 유지한다.'),
    item('EV2-B04', 'I002', '03:42.413', 'recommended',
         '중간 표본은 초혼·재혼 네 막대와 두 결론을 한꺼번에 보여준다. 두 비교의 방향 반전을 더 명확히 드러낼 수 있다.',
         [evidence[5]],
         '전체 차이59 → 초혼 영통+888 → 재혼 권선+830 순으로 활성 비교를 이동한다. 같은 0~8,000쌍 척도와 실제 값·기간을 유지하고 활성 행 외 요소는 낮춰 표시한다.'),
    item('EV2-B05', ['O001', 'C001', 'E001'], ['00:11.736', '07:24.038', '07:39.771'], 'recommended',
         '훅은 사진 세 장·지도·20위→1위가 병렬이고, 결말은 큰 개요지도와 규모/변화/구성 텍스트다. 처음 질문과 최종 활용의 연결을 더 구체화할 수 있다.',
         [evidence[i] for i in [0, 6, 7]],
         '훅에서 이번 편의 대표 발견 하나를 발화에 맞춰 우선 제시한다. 결말은 왼쪽 의미 있는 아이콘과 오른쪽 세 가지 짧은 비교 질문으로 묶고 실제 생활권·예산·집 크기 선택으로 연결한다. 무음 CTA의 자막 박스 숨김을 유지한다.'),
    item('EV2-B06', 'new_analysis', None, 'required',
         '실측 기준본은 470.966667초로 최신 요청의 480초 초과를 충족하지 않는다. 새로운 분석과 그 근거가 필요한 변경이다.',
         [{'path': str(OLD), 'sha256': old_hash, 'ffprobe_duration_s': float(metadata['format']['duration'])}],
         '리서치 담당의 검증된 추가 분석을 채택하고 실제 음성으로 시간을 확장한다. 최종 MP4가 480초를 엄격히 초과하며 계획 목표 510초 이상인지 확인한다. 무음·기존 음성 지연으로 길이를 채우지 않는다.', owner='director'),
]
audit = dict(
    task_id='top20-enhance-QA-v2', stage='baseline_audit',
    created_at=datetime.now(timezone.utc).isoformat(),
    checked_revision='main-v5',
    baseline=dict(path=str(OLD), sha256=old_hash, probe=metadata,
                  timing_path=str(TIMING), timing_sha256=sha(TIMING),
                  frame_index=str(FRAME_INDEX), frame_index_sha256=sha(FRAME_INDEX)),
    coverage=dict(sampled_decoded_frames=8, scene_ids=[x[0] for x in selected],
                  all_scene_review=False, all_boundaries_review=False,
                  maximum_zoom_review=False, continuous_playback='unchecked',
                  actual_listening='unchecked', speech_pronunciation='unchecked',
                  full_decode='not_run_for_baseline', numerical_research='리서치 담당 별도 배정; QA 수치 재조사 미실시',
                  confirmed_clipped_text_in_selected_frames=False),
    evidence=evidence, findings=findings,
    next_gates=[
        '편집 대표3의 실제 MP4·프레임 색인·입력 SHA 수신 후 검수',
        '추가 분석은 리서치 검증 기록과 화면·낭독문을 대조하며 원자료 재조사는 하지 않음',
        '총괄 handoff 후 최종 MP4 정확한 SHA·480초 초과·모든 장면/경계/긴 자막/최대 줌 검수',
        '최종 MP4 전체 디코드·기존 음성 PCM 불변성·추가 음성 provider words 매핑·자막/브랜드 경계 검수',
        '실제 청취·연속 재생 미수행이면 unchecked 유지',
    ],
)
save('baseline_audit.json', audit)
save('findings.json', dict(task_id='top20-enhance-QA-v2', revision='main-v5', findings=findings))
save('issue_BASELINE_HANDOFF.json', dict(
    issue_id='EV2-BASELINE-HANDOFF',
    recipients=[dict(role='editor', agent_id='01a19bab-9d3b-7ed1-9e83-49c83b4661e9'), dict(role='director')],
    delivery_method='공유 QA 파일; 현재 도구 목록에 에이전트 직접 메시지 도구 없음',
    delivery_status='written_for_director_relay; direct_message_not_sent',
    scene_id=['O001', 'S003', 'S011', 'S022', 'I001', 'I002', 'C001', 'E001', 'new_analysis'],
    문제='시각 개선 기준과 대표3·최종 검수 입력 전달',
    evidence=str(OUT / 'baseline_audit.json'),
    제안='B01 세 구도와 사진 여백, B02 위치 안내, B03/B04 비교 초점, B05 훅/결말을 대표3에 반영. 최종 검수용 실제 파일과 입력 매핑을 전달.',
    영향='기존 수치/음성/출처 보존; 전체 편집 확대 전 대표3 검수 필요',
    requested_handoff=['대표3 실제 MP4와 프레임 색인', '새 장면/자막/발화 앵커 시간표', '리서치 추가분 검증 기록', '최종 MP4·SRT·입력SHA', '기존 음성 재사용 매핑과 추가 provider word 대응'],
))
save('handoff.json', dict(
    task_id='top20-enhance-QA-v2', status='baseline_complete_waiting_for_representative3',
    artifacts=[str(OUT / n) for n in ['baseline_audit.json', 'findings.json', 'issue_BASELINE_HANDOFF.json']],
    input_revision=dict(video='main-v5', video_sha256=old_hash, timing_sha256=sha(TIMING)),
    verified=['실제 기존 MP4 해시·ffprobe', '인코딩 프레임8장 직접 확인·프레임SHA 대조'],
    unresolved=['대표3 미수신', '최종 인코딩/총괄 handoff 미수신', '실제 청취·연속 재생 미수행'],
    affected_scenes=[x[0] for x in selected] + ['new_analysis'],
    next_owner=['editor', 'director'],
    direct_message_sent=False,
))
for name in ['baseline_audit.json', 'findings.json', 'issue_BASELINE_HANDOFF.json', 'handoff.json']:
    json.loads((OUT / name).read_text(encoding='utf-8'))
print(json.dumps(dict(status='baseline_written_and_reloaded', frame_count=8,
                      main_sha256=old_hash, duration_s=metadata['format']['duration'],
                      paths=[str(OUT / n) for n in ['baseline_audit.json', 'issue_BASELINE_HANDOFF.json', 'handoff.json']]),
                 ensure_ascii=False))
