import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[4]
OLD = PROJECT / 'video-agent-studio/episodes/namyangju-wangsuk-20261014/research/map-led-v5'
CHECKED = '2026-10-25'
URL = 'https://apply.lh.or.kr/lhapply/lhFile.do?fileid=62796613'
NOTICE_URL = 'https://apply.lh.or.kr/lhapply/lhFile.do?fileid=62796608'
PAGE_URL = 'https://apply.lh.or.kr/lhapply/apply/wt/wrtanc/selectWrtancInfo.do?ccrCnntSysDsCd=02&mi=1027&panId=0000060920'
PAPER_URL = 'https://www.kpaj.or.kr/_PR/view/?aidx=50743&bidx=4543'
PDF = ROOT / 'LH_남양주왕숙_A1_팸플릿_20250724.pdf'
NOTICE = ROOT / 'LH_남양주왕숙_A1_모집공고_20250724.pdf'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, data):
    (ROOT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


assert PDF.is_file() and NOTICE.is_file()
assert sha(PDF) == sha(OLD / 'w1_a1_pamphlet.pdf')
assert sha(NOTICE) == sha(OLD / 'w1_a1_notice.pdf')
assert '전' in (ROOT / 'FP59_pamphlet_page9.txt').read_text(encoding='utf-8')
assert '59.9200㎡' in (ROOT / 'FP59_pamphlet_page9.txt').read_text(encoding='utf-8')
assert '59B' in (ROOT / 'FP59_notice_page4.txt').read_text(encoding='utf-8')
supply = float(Decimal('59.9200') + Decimal('24.5383'))
assert supply == 84.4583

example = {
    'id': 'FP59',
    'complex': '남양주왕숙지구 A-1블록 공공분양',
    'block': 'A-1',
    'unit_type': '59A',
    'exclusive_area_m2': 59.9200,
    'exclusive_area_source_text': '59.9200㎡',
    'supply_area_m2': supply,
    'supply_area_method': '모집공고 PDF 4쪽 공급면적 하위 열의 주거전용 59.92 + 주거공용 24.5383을 합산. 84.4583㎡는 합산값이며 별도의 84타입을 뜻하지 않음.',
    'residential_common_area_m2': 24.5383,
    'contract_area_m2': 134.4820,
    'source_url': URL,
    'source_page_url': PAGE_URL,
    'source_file': str(PDF),
    'page': 9,
    'page_number_basis': 'PDF 파일의 1부터 시작하는 페이지 번호. 펼침면의 인쇄 쪽수는 16·17.',
    'printed_pages': '16·17',
    'source_publisher': '한국토지주택공사(LH)',
    'source_publication_year': 2025,
    'source_publication_date': '2025-07-24',
    'source_date_basis': '보존된 공식 다운로드 원파일명 (250724), 모집공고 PDF 1쪽의 입주자모집공고일 2025.07.24 대조. 팸플릿 자체에 별도 인쇄 발행일은 확인하지 못함.',
    'supporting_source_url': NOTICE_URL,
    'supporting_source_file': str(NOTICE),
    'supporting_page': 4,
    'figure_description': 'UNIT PLAN / 단위세대, 59A 펼침면의 왼쪽 2D 단위세대 평면도와 상단 주택면적표. 침실1·2·3, 거실, 주방/식당, 욕실1·2 등 원본 문자 포함. 오른쪽 3D 아이소와 침실2+3 통합 옵션 도판은 본 크롭에서 제외.',
    'figure_condition': '모집공고는 전 세대 발코니 확장형 시공을 명시. 팸플릿 도판은 분양 당시 계획·이해용 개략도이며 실제 시공이나 준공 실측을 확인한 자료는 아님.',
    'image_file': str(ROOT / 'source59.png'),
    'additional_image_file': str(ROOT / 'source59_plan.png'),
    'full_page_preview': str(ROOT / 'FP59_page9_preview.png'),
    'caption': '공간감 보조 예시 · 논문 표본단지 아님 | 남양주왕숙 A-1블록 59A, 전용 59.9200㎡ | 출처: LH 2025 팸플릿 PDF 9쪽(인쇄 16·17쪽). 분양 계획도, 실제 시공과 다를 수 있음.',
    'rights': '확인: 보존된 LH 공식 공고 HTML 하단에 Copyright 2023 korea land & housing corporation all rights reserved. 표시. 해당 HTML에서 공공누리/KOGL 표시는 검색되지 않음. 미확인: 이 팸플릿 평면도에 대한 별도 재이용·상업영상·크롭 허락 범위. 공개 다운로드가 재사용 허락이라는 뜻으로 기록하지 않음.',
    'rights_status': 'reuse_permission_unverified',
    'reference_date': '2025-07-24',
    'checked_date': CHECKED,
    'verification_scope': '원PDF 해당 페이지 텍스트 확인, 전체 펼침면과 최종 source59.png 직접 이미지 열람, 모집공고 PDF 4쪽 표 이미지 대조, 재사용 원본 SHA256 일치, LH URL HTTP 200/PDF 서명 확인. URL 검사는 첫 8바이트만 확인했으며 전체 온라인 PDF와 로컬 원본 해시 비교는 하지 않음.',
    'crop': {'pdf_page': 9, 'rect_pdf_points': [0, 95, 680, 775], 'render_scale': 4, 'expected_pixels': [2720, 2720], 'method': '기존 PyMuPDF 의존성으로 PDF 영역을 직접 래스터화; AI 생성·재작성·문자 수정 없음'},
    'source_sha256': sha(PDF),
    'image_sha256': sha(ROOT / 'source59.png'),
}

save('floorplan_facts.json', {
    'status': 'verified',
    'examples': [example],
    'status_scope': '공식자료 출처·단지·타입·면적·도판 내용의 검증 상태. 저작물 재사용 허락 검증 상태는 rights_status를 따름.',
    'same_complex_84': {'status': 'not_available_in_reviewed_official_release', 'evidence': '모집공고 PDF 1쪽 전용면적59㎡ 629세대 및 4쪽 공급대상표 59A 484세대/59B 145세대. 같은 블록 84타입은 해당 공급자료에 없음. 다른 단지의 84타입 추가조사 없음.'},
    'checked_date': CHECKED,
})

claims = [
    ('FP59-AREA', '남양주왕숙 A-1블록 59A의 공식 팸플릿상 전용면적은 59.9200㎡다.', URL, str(PDF), 'PDF 9쪽(인쇄16·17쪽), 59A 주택면적표 전용면적', 'verified'),
    ('FP59-SUPPLY', '59A 공급면적은 주거전용 59.92㎡와 주거공용 24.5383㎡의 합계 84.4583㎡로 계산된다.', NOTICE_URL, str(NOTICE), 'PDF 4쪽, 2. 공급대상 표 공급면적의 주거전용/주거공용 열. Decimal로 합산.', 'verified'),
    ('FP59-FIGURE', '확보한 도판은 실제 분양단지의 59A 확장형 계획 평면도이며, 논문 표본단지의 실측도는 아니다.', URL, str(PDF), 'PDF 9쪽 59A UNIT PLAN 및 도판 주의문; 모집공고 PDF4쪽 확장형 안내', 'verified'),
    ('FP59-NO84', '검토한 A-1블록 공급자료에는 59A·59B만 있고 84타입은 없다.', NOTICE_URL, str(NOTICE), 'PDF1쪽 공급대상 및 PDF4쪽 공급대상표 전체', 'verified'),
    ('P2-59-EXCLUSIVE', '이주논문 III.2 본문은 59㎡ 아파트라고 적고 있으며, 열람한 HTML 본문에는 전용이라는 면적 정의가 명시되지 않아 전용59㎡라는 논문 표현은 추가 확인이 필요하다.', PAPER_URL, None, 'III.2 시간적·공간적 범위 첫 문단. HTML 본문 전용 검색 결과 없음. 표 이미지·부록 데이터 코드의 면적 정의는 이번에 확인하지 않음.', 'qualified'),
]
save('facts.json', {'revision': 'floorplan-readable-v2-20261025', 'claims': [dict(claim_id=cid, sentence=sentence, source_url=url, source_file=file, evidence_location=location, reference_date=('2026-08-31' if cid.startswith('P2') else '2025-07-24'), checked_date=CHECKED, status=status) for cid, sentence, url, file, location, status in claims]})

save('paper59_check.json', {
    'status': 'qualified', 'claim_id': 'P2-59-EXCLUSIVE', 'source_url': PAPER_URL,
    'title': '재건축사업으로 인한 이주가 주택가격에 미치는 영향: 서울 가락시영아파트 사례',
    'location': 'III.2 시간적·공간적 범위, 첫 문단',
    'short_excerpt': '종속변수는 도착지 행정동별 59m² 아파트의 월세 및 매매 실거래가격',
    'result': '59㎡ 표기는 확인. 전용 명시는 열람한 HTML 본문에서 확인되지 않음. 팸플릿의 전용59.9200㎡와 논문의 59㎡는 서로 다른 자료·시점·대상임.',
    'writer_recommendation': '논문 설명은 “59㎡ 아파트를 대상으로”로 유지하고, 평면도에는 “전용59.9200㎡ 공간감 보조 예시·논문 표본단지 아님”을 별도 표기.',
    'checked_date': CHECKED, 'other_papers_researched': False,
})

save('issue_FP59_USAGE.json', {
    'issue_id': 'FP59-USAGE', 'affected_scene_ids': ['L004'],
    'affected_claim_ids': ['FP59-FIGURE', 'P2-59-EXCLUSIVE'],
    'problem': '공간감 예시가 가락시영 원형 또는 논문 표본단지 평면도로 오해될 가능성, 논문 59㎡의 전용 정의 미확인.',
    'evidence': [str(ROOT / 'floorplan_facts.json'), str(ROOT / 'paper59_check.json')],
    'proposal': 'caption의 보조 예시·논문 표본단지 아님 표시를 필수 유지. 논문 문장에는 전용을 덧붙이지 않음. 공급84.4583㎡를 전용84타입으로 표시하지 않음.',
    'impact': 'writer 문구 및 visual 평면도 캡션에만 반영. 같은 단지84 추가 없음. 재이용 권한 범위는 rights 필드의 미확인 상태를 승계.',
    'recipients': ['director', 'writer', 'visual'], 'delivery': '직접 에이전트 메시지 도구 없음; 담당 폴더 이슈 파일로 전달',
})

save('source_manifest.json', {
    'checked_date': CHECKED,
    'sources': [
        {'source_url': URL, 'preserved_file': str(PDF), 'reused_from': str(OLD / 'w1_a1_pamphlet.pdf'), 'sha256': sha(PDF), 'bytes': PDF.stat().st_size},
        {'source_url': NOTICE_URL, 'preserved_file': str(NOTICE), 'reused_from': str(OLD / 'w1_a1_notice.pdf'), 'sha256': sha(NOTICE), 'bytes': NOTICE.stat().st_size},
    ],
    'prior_url_mapping': str(OLD / 'pdf_downloads.json'),
    'rights_marker_file': str(OLD / 'w1_a1.html'),
    'rights_marker_location': 'HTML footer p.copyright, line4901',
    'official_url_check': str(ROOT / 'official_url_check.json'),
})

save('handoff.json', {
    'task_id': 'FP59-readable-v2-20261025', 'role': 'research', 'status': 'verified',
    'base_folder': str(ROOT),
    'input_revisions': {'source_packet': 'namyangju-wangsuk-20261014/research/map-led-v5', 'pamphlet_sha256': sha(PDF), 'notice_sha256': sha(NOTICE), 'latest_user_request': '평형을 보여줄 거면 대표적인 건축 예시 활용'},
    'outputs': ['floorplan_facts.json', 'source59.png', 'source59_plan.png', PDF.name, NOTICE.name, 'facts.json', 'paper59_check.json', 'source_manifest.json', 'issue_FP59_USAGE.json', 'verification.json'],
    'affected_scene_ids': ['L004'],
    'checks': [
        {'check': 'PDF9쪽·최종PNG·공고4쪽열람', 'result': 'passed', 'evidence': 'verification.json'},
        {'check': '원본해시·59A면적', 'result': 'passed', 'evidence': 'source_manifest.json'},
        {'check': '논문59㎡의전용명시', 'result': 'unconfirmed', 'evidence': 'paper59_check.json'},
        {'check': '상업영상재이용허락', 'result': 'unconfirmed', 'evidence': 'rights_status=reuse_permission_unverified'},
    ],
    'open_issue_ids': ['FP59-USAGE'], 'next_role': 'director → writer/visual',
    'limitations': ['같은블록84없음', '독립QA미실행', '신규시세·유료생성·외부전송없음'],
})
print(json.dumps({'status': 'written', 'facts': str(ROOT / 'floorplan_facts.json'), 'image': str(ROOT / 'source59.png'), 'exclusive_area_m2': 59.92, 'supply_area_m2': supply}, ensure_ascii=False))
