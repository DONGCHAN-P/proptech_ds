"""Record observed frame QA and bounded offline verification in the QA folder."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

QA = Path(__file__).resolve().parent
EP = QA.parents[1]
ROOT = EP.parents[2]
OUT = EP / 'outputs/production-v1-jun'
proof = json.loads((QA / 'input_verification.json').read_text('utf-8'))
assert proof['status'] == 'pass' and not proof['failures']

def rel(p):
    return Path(p).resolve().relative_to(ROOT).as_posix()

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def save(name, value):
    (QA / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

frame_dir = OUT / 'checks/encoded_preview_frames'
revision = {
    'production_revision': 'production-v1-jun',
    'script_sha256': sha(EP / 'outputs/script-review-v3/script_v3.md'),
    'chart_data_sha256': sha(OUT / 'project/assets/chart_data.json'),
    'combined_mp4_sha256': sha(OUT / 'previews/지역별회복_모션시안_v1_무음.mp4'),
    'incheon_mp4_sha256': sha(OUT / 'previews/incheon2008-2016recovery_provisional_v1.mp4'),
    'incheon_7s_png_sha256': sha(frame_dir / 'incheon2008-2016recovery_7s.png'),
    'input_verification_sha256': sha(QA / 'input_verification.json'),
    'input_sha_manifest': rel(QA / 'input_verification.json') + '#inputs',
}
unit_affected = [x for x in proof['authored_coverage'] if x['chart_units'] == ['', '']]
required = {
    'issue_id': 'RPR-P1-REQ-01', 'scene_id': 'S007',
    'timecode': {'combined_preview': ['00:10', '00:12', '00:15'], 'clip': 'incheon2008-2016recovery',
                 'clip_seconds': [2, 4, 7], 'body_provisional_seconds': [402.533333, 418.666667], 'timing_locked': False},
    'severity': 'required',
    '문제': '인천 확대 차트의 위쪽 가격 경로에 지수 기준값이 없다. 212·142·70.8 숫자만 보이며, 만원/㎡ 원가격과 구별하는 2006Q1=100이 빠졌다.',
    'evidence': {'actual_encoded_png': rel(frame_dir / 'incheon2008-2016recovery_7s.png'),
                 'contact_sheet': rel(frame_dir / 'contact_sheet.png'),
                 'screen_region': '상단 인천 가격선, x145~1265 y220~710. 하단 낙폭은 % 표기 존재.',
                 'geometry_source': rel(EP / 'editor/production-v1/build.py') + ':97 episode_chart → chart 호출의 unit 생략',
                 'preview_html': rel(OUT / 'project/preview/incheon2008-2016recovery.html'),
                 'serialized_price_chart_unit': '',
                 'correct_definition': 'chart_data.series.인천은 2006Q1=100, 첫 복귀 2008Q3→2016Q2, 31분기. 하단은 누적 최고 대비 %.',
                 'affected_authored_beats': [x['beat_id'] for x in unit_affected]},
    '수정안': '공통 episode_chart의 상단 가격선에 unit="2006Q1=100"을 표시한다. 지수라는 말도 제목/단위에 명시하고 하단 %축과 분리한다. 공유 컴포넌트가 사용된 비트의 단위/라벨 경계 및 수정 인천 클립과 연결부만 재검수한다.',
    'owner': 'editor/production-v1', 'status': 'open', 'checked_revision': revision,
}
recommendations = [
    {'issue_id': 'RPR-P1-REC-01', 'scene_id': 'S007',
     'timecode': {'combined_preview': ['00:10', '00:12', '00:15'], 'clip_seconds': [2, 4, 7], 'timing_locked': False},
     'severity': 'recommended',
     '문제': '최초 복귀 2016Q2 라벨의 왼쪽 글자 위로 인천 가격 곡선이 지나간다. 내용은 판독 가능하지만 핵심 복귀일과 곡선이 같은 색으로 겹친다.',
     'evidence': {'actual_encoded_png': rel(frame_dir / 'incheon2008-2016recovery_7s.png'),
                  'screen_region': 'x1000~1195 y331~358',
                  'geometry': '복귀 라벨 baseline y355, 23px. 같은 영역으로 저점 이후 상승 곡선 통과.'},
     '수정안': '복귀 라벨을 곡선과 떨어진 고정 레인으로 이동하거나 크림 배경의 짧은 라벨 박스와 리더선을 쓴다. 고점·관측 저점·최초 복귀의 분기는 유지한다.',
     'owner': 'editor/production-v1', 'status': 'open', 'checked_revision': revision},
    {'issue_id': 'RPR-P1-REC-02', 'scene_id': 'S004',
     'timecode': {'combined_preview': ['00:02', '00:04', '00:07'], 'clip_seconds': [2, 4, 7], 'timing_locked': False},
     'severity': 'recommended',
     '문제': '6패널을 480px 폭으로 축소한 접촉시트에서 축·분기·커서 수치가 매우 작다. 제목과 자막은 읽히지만 각 패널의 정확한 숫자 비교는 확대가 필요하다.',
     'evidence': {'actual_encoded_png': rel(frame_dir / 'full2006paths_7s.png'),
                  'contact_sheet': rel(frame_dir / 'contact_sheet.png'),
                  'scale': '접촉시트 1440×870, 한 열 480px. 실제 휴대전화 재생 검사는 아님.',
                  'declared_typography': '축21~22px·커서23px/1920px → 480px 환산 약5.25~5.75px. 자막39px → 약9.75px.'},
     '수정안': '6지역 개요 뒤 발화 대상 1~2개 패널을 순서대로 크게 보여 주거나 핵심 수치만 별도 강조한다. 동일축·전체 기간·관측 종료는 유지한다. 출처를 자막 안으로 옮기지 않는다.',
     'owner': 'editor/production-v1', 'status': 'open', 'checked_revision': revision},
]
technical = json.loads((OUT / 'checks/preview_technical.json').read_text('utf-8'))
coverage = {
    'full_resolution_encoded_pngs_viewed': [rel(frame_dir / f'{name}_7s.png') for name in
        ['full2006paths', 'incheon2008-2016recovery', 'rawmedianvsindex']],
    'nine_frame_contact_sheet_viewed': rel(frame_dir / 'contact_sheet.png'),
    'sample_times': {'full2006paths': [2, 4, 7], 'incheon2008-2016recovery': [2, 4, 7], 'rawmedianvsindex': [2, 4, 7]},
    'combined_preview_sample_seconds': [2, 4, 7, 10, 12, 15, 18, 20, 23],
    'sample_note': '실제 MP4에서 추출된 기존 PNG를 독립 열람. 개별 원해상도는 7초의 3장, 나머지 6장은 접촉시트에서 확인.',
    'baseline_images_viewed': [rel(OUT / f'reusable_assets/baseline_gyosan_{n}s.png') for n in [45, 430, 850]],
    'static_style': '크림 바탕·짙은 남색 굵은 제목·Pretendard·파랑/절제된 지역색·하단 흰 자막 상자와 별도 출처가 기준 프레임과 부합. 자막은 기준 예보다 굵음.',
    'mobile_readability': '480px 폭 접촉시트로 근사. 실제 기기 UI·휴대전화 재생 없음. REC-02 참조.',
    'frame_boundaries': 'unchecked: 0/8/16/24초와 경계 전후 프레임 미제공. 2/4/7초 표본으로 연결·연속성을 통과시키지 않음.',
    'maximum_zoom': '전체 화면 줌 없는 고정 지오메트리 확인. 전용 최대 줌/경계 프레임 검사는 unchecked.',
    'continuous_playback': 'unchecked', 'actual_listening': 'unchecked',
    'stream_checks': '기존 ffprobe/전체 디코드 기술 영수증을 SHA 일치로 재사용. 신규 ffprobe/디코드 없음. 3클립 각8초·1920×1080·30fps·음성0. 코덱명은 해당 영수증에 없어 이번 범위 unchecked.',
    'combined_mp4': {'path': technical['combined_preview']['path'],
                     'sha256': technical['combined_preview']['sha256'], 'bytes': technical['combined_preview']['bytes'],
                     'expected_duration_seconds': 24, 'independently_reprobed_duration': 'unchecked'},
    'full_film': 'not_generated', 'actual_voice': 'not_generated', 'timing_locked': False,
    'authored_coverage': {'scenes': 12, 'beats': 39, 'verification': rel(QA / 'input_verification.json') + '#authored_coverage',
                          'level': '공통/승인 장면표·비트 manifest 순서·HTML 비트와 차트ID 존재를 독립 확인. 전체39비트의 미디어 화질·내용적 충분성 통과가 아님.',
                          'encoded_beat_ids': ['S004-P1', 'S007-P2', 'S003-P3']},
    'typography_bounds': {'source': rel(OUT / 'checks/hyperframes_check.json'),
                         'producer_check': 'layout12시점, contrast5시점217검사; transitionSamples=[]; lint경고6. 현재 샘플 3키프레임에서 제목/자막/출처 잘림 없음.',
                         'limits': '기존 검사에는 전체39비트별 글자 경계 영수증/SHA 연결이 없다. 모든 비트의 타이포 경계 통과로 확대하지 않음.'},
    'new_png_or_video': 0, 'paid_calls': 0, 'network_calls': 0, 'external_messages': 0,
}
report = {
    'task_id': 'RPR-PROD1-PREVIEW-QA', 'role': 'independent_qa',
    'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'status': 'required_fix_open',
    'summary': '자료 변환·기존 산술 근거 재사용·12장면39비트 구성·오프라인22검사 영수증은 확인. 인천 확대 지수축 기준값 누락 1건 필수 수정, 라벨 겹침/축소 가독성 2건 권장. 본편/음성 최종 QA 아님.',
    'counts': {'critical': 0, 'required_open': 1, 'recommended_open': 2},
    'checked_revision': revision, 'findings': [required] + recommendations,
    'verified': [
        {'check': 'frozen_table_conversion', 'result': 'pass', 'evidence': rel(QA / 'input_verification.json'),
         'scope': '538지수행·574원가격행·33하락구간·7요약·147연간거래량·13민감도·7기간요약을 현재 원CSV와 정확 대조. 새 원거래/6백만건 재계산 없음.'},
        {'check': 'prior_math_reuse', 'result': 'pass', 'evidence': rel(QA / 'input_verification.json'),
         'scope': '이전 독립 검산 코드 SHA/통계 정의/허용오차 유지. 현SHA와 재계산 필드 대조. 원가격 독립 검산은 기존 3표본 범위만 재사용.'},
        {'check': 'first_returns', 'result': 'pass',
         'evidence': '인천 2008Q3→2013Q1 관측 저점→2016Q2 최초복귀,31분기=7년9개월,-17.5948495%. 경기24q·서울2010사례21q·서울2008 DD01·부산12q·대구11q는 동일 episodes/이전검산 영수증에 연결.'},
        {'check': 'units_periods_samples_in_opened_frames', 'result': 'pass_with_REQ_01',
         'evidence': '6지역2006Q1=100 동일0~600축,종료2026Q2. 이동 커서7초는2026Q1이며 최종값이라 주장하지 않음. 원가격은만원/㎡·25~75백분위; 별도 매칭지수2006Q1=100;양쪽분기2건/연결30단지 조건 표시. 실제 관측기간·표본을 혼합하지 않음.'},
        {'check': 'sejong_censor_sensitivity_data', 'result': 'pass_data_only',
         'evidence': '세종2015Q1 시작·초기코드경고·미회복first_return=null·최근주기2020Q1~2022Q4의2/3/5건 요약만 보존. 세종/민감도 장면은 이번 인코딩 표본에 없어 표시 가독성 unchecked.'},
        {'check': 'caption_source_title_separation', 'result': 'pass_sampled_only',
         'evidence': '열람 키프레임에서 제목94~147,조건866~898,자막922~1020,출처1042~1067의 별도 레이어. 잘림 없음. 실제 발화 정렬 검수 아님.'},
        {'check': 'narration_readiness', 'result': 'offline_receipt_only',
         'evidence': 'offline_verification.json 22/22 passed·현재4개 코드SHA 일치·외부요청0. 승인 대본/39문단SHA 일치. budget5fe307eed02c pending·5807포함크레딧 상한·추가결제0; 생성/청취/실제타이밍 미실시.'},
    ],
    'coverage': coverage,
    'inherited_issues': [{'issue_id': 'FHQA-R01', 'status': 'open_deferred_metadata_only',
                          'reference': rel(EP / 'qa/full-history-v1/final_recheck_v3.json'), 'new_numeric_defect': False}],
    'delivery_disposition': '필수 수정 전 무조건 통과·최종 완성으로 표현하지 않음. 총괄의 Telegram 초안에는 무음/임시/대표3클립/필수 수정 상태를 명시. 이번 QA는 게시·전송·유료 권한을 부여하지 않음.',
    'next_role': 'editor가REQ-01 수정→qa가변경클립/공유단위/연결부 재검수→director',
}
save('findings.json', report)
save('issue_RPR-P1-REQ-01.json', {'task_id': report['task_id'], **required,
     '영향': '인천 대표8초 및 공통 episode_chart를 쓰는12개 비트. 변경 후 영향 비트의 단위/글자경계, 수정 인천클립과 앞뒤 연결만 재검수.',
     'delivery': '직접 peer 메시지 도구 없음. 이 파일과 handoff 경로를 총괄에게 반환; 다른 채팅/Telegram 발송 없음.'})
save('handoff.json', {
    'task_id': report['task_id'], 'role': 'qa', 'status': 'required_fix_open',
    'input_revisions': {'production': 'production-v1-jun', 'script_sha256': revision['script_sha256'],
                        'chart_data_sha256': revision['chart_data_sha256'],
                        'combined_mp4_sha256': revision['combined_mp4_sha256'], 'all_sha': 'input_verification.json#inputs'},
    'outputs': ['findings.json', 'input_verification.json', 'issue_RPR-P1-REQ-01.json'],
    'affected_scene_ids': ['S001', 'S004', 'S006', 'S007', 'S008', 'S012'],
    'checks': [{'check': 'CSV/동일SHA 산술재사용·12장면39비트·오프라인22영수증', 'result': 'pass', 'evidence': 'input_verification.json'},
               {'check': '실제인코딩PNG3장+9프레임접촉시트+기준3장 열람', 'result': 'required_fix_open', 'evidence': 'findings.json'},
               {'check': '연속재생·청취·전체본편·경계', 'result': 'unchecked', 'evidence': 'findings.json#coverage'}],
    'open_issue_ids': ['RPR-P1-REQ-01', 'RPR-P1-REC-01', 'RPR-P1-REC-02'],
    'required_fix': '인천 확대 상단 지수축에2006Q1=100 명시. 공통episode_chart의같은단위누락12비트도수정. 값/기간/승인음성변경없음.',
    'limits': '무음대표3클립만열람. 본편/음성없음. budget5fe307eed02c pending. 생성·게시·전송0.',
    'next_role': 'editor 수정→qa 영향클립/단위/연결부 재검수→director',
})
print(json.dumps({'status': report['status'], 'counts': report['counts'], 'outputs': ['findings.json', 'handoff.json', 'issue_RPR-P1-REQ-01.json']}, ensure_ascii=False))
