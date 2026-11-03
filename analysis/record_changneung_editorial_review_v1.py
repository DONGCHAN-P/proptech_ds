import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

root = Path(__file__).resolve().parents[1]
ep = root / 'video-agent-studio/episodes/goyang-changneung-20261015'
out = ep / 'qa/editorial-review-v1'
out.mkdir(parents=True, exist_ok=True)
video = ep / 'outputs/production-v5/changneung_full_v5r2.mp4'
sha = hashlib.sha256(video.read_bytes()).hexdigest()
assert sha == '7979a8071e4c07d4047a46b37b4abf6fa89c1a8aa9f4fb0c90dd0d99bec9f0b0'
review = {
    'source_event': '718066299',
    'reviewed_at': datetime.now(timezone.utc).isoformat(),
    'status': 'recommendations_only_not_script_or_budget_approval',
    'video': str(video), 'video_sha256': sha,
    'scope': '전체 낭독문·183개 자막·전장 표본 검토 및 실제 MP4 추가 대표 프레임. 실제 청취·전체 연속 재생 미실시.',
    'main_finding': '집·철도·학교의 시간차는 전달되지만, 지금 가능한 선택과 블록별 통근·가격 대가·공급 비교가 부족해 최초 선택 질문에 충분히 답하지 못한다.',
    'priorities': [
        {'priority': 1, 'scene': 'M000/M004/M008/M009', 'problem': '이미 발표된 본청약 사례와 지금 기다려 취득할 선택이 혼재', 'proposal': '초반부터 분석 대상과 시청자 유형을 밝히고 결말에서 같은 취득 전제 회수. 추가모집·전매 가능 날짜 임의 생성 금지.', 'requires': '낭독 수정안 검토'},
        {'priority': 2, 'scene': 'M002/M003', 'problem': '원흥역 24/28/49분이 블록별 현관 출발 통근 비교로 연결되지 않음', 'proposal': 'S1/S4/S5의 기존 역 접근을 동일 출발 조건으로 조사하고 도심·DMC·여의도 등 대표 목적지의 접근/대기/철도/마지막 이동을 분해. 미확인 시간을 임의 배분하지 않음.', 'requires': '추가 경로 근거 조사'},
        {'priority': 3, 'scene': 'M004/M007/M009', 'problem': '정확 금액 나열에 비해 S4 추가 공고가격 부담과 장점의 비교가 약함', 'proposal': 'S4-S5 96,731,000원, S4-S1 82,949,000원을 기존 공고가 기준 차이로 제시하고 생활 접점·학교 목표와 함께 결론에 회수. 현재 매입가격·미래 프리미엄으로 해석하지 않음.', 'requires': '기존 승인 수치 재배치; 낭독 변경 시 별도 수정안'},
        {'priority': 4, 'scene': 'M006', 'problem': '공급 장이 주변 공급량 없이 거래 규제로 전환됨', 'proposal': '주변 사업지의 연도별 예정 입주 가구 수와 창릉 합산 여부를 조사하거나 제목·오프닝의 약속을 입주/거래 조건으로 좁힘.', 'requires': '추가 공급 조사 또는 범위 정정'},
        {'priority': 5, 'scene': 'M008/M009', 'problem': '최종 후보가 앞선 상세 지도 반복에 머물고 S1 차별화 근거가 약함', 'proposal': 'S4/S5/S1의 동일 항목 3열 최종 비교판으로 회수. S1의 확인되지 않은 강점은 만들지 않고 관찰 조건을 분명히 함.', 'requires': '편집 구성/낭독 수정 제안'}
    ],
    'root_visual_observations': [
        {'seconds': 125, 'evidence': 'root_frames/125.png', 'problem': '업무지 지도 우측 편집 안내 문구가 넓은 면적을 차지', 'proposal': '지도 확대 및 해당 업무지 접근 구조/시청자가 얻는 결론만 짧게 표기'},
        {'seconds': 305, 'evidence': 'root_frames/305.png', 'problem': '0~9억 축의 큰 가격판이 작은 확장비 차이를 설명하며 의사결정 비교는 뒤로 밀림', 'proposal': '정확 기본가·확장비는 작은 보조표, 3후보 합계와 가격 차이를 주요 비교로 사용'},
        {'seconds': 410, 'evidence': 'root_frames/410.png', 'problem': '여러 윤곽선 동시 파랑 강조와 학교·하천 라벨 근접으로 시각 위계 약함', 'proposal': '현재 발화 대상만 1차 강조, 주변은 저채도. 학교·공원·하천 라벨 순차 노출/인접 배치. 우측 카드 축소로 지도 여유 확보'},
        {'seconds': 735, 'evidence': 'root_frames/735.png', 'problem': '최종 후보 설명이 앞선 학교 상세판을 반복해 최종 판단의 새 정보가 약함', 'proposal': '입주/가격/기존 생활 접점/학교 목표/철도 공백을 한 판에서 비교하고 해당 후보 열만 강조'}
    ],
    'production_sequence_if_later_authorized': ['추가 조사 공백 정리', '질문-근거-생활 의미-선택으로 낭독 수정안', '같은 결론을 담는 대표 3장 내부 검토', '변경분 음성 예산·대본 범위 확인', '변경 구간 편집 및 검수'],
    'unchanged': ['원본 MP4/SRT/음성', '다섯 승인 게이트', '기존 예산', 'YouTube 비공개 게시 상태'],
    'external_paid_calls': 0, 'new_render': False,
    'writer_report': 'writer/editorial-review-v1/viewer_message_review.md',
    'independent_visual_report': 'qa/editorial-review-v1/편집품질_독립검토.md',
    'additional_visual_recommendations': [
        '09:15~10:05 대안 지도 대상 옆에 단지명/중위값/n 지속 표시',
        '10:53~11:24 가족 달력에 실제 날짜와 구분한 입력 방법 및 기다릴 개월 수×자기 월 주거비 구조 제시',
        '08:15 전매제한/거주의무는 같은 시작점 공통축 대신 각기 다른 시작 사건으로 시각 분리',
        '05:51~06:25 추상 조건 카드 반복을 입주·개통·개교 공백의 구체 비교로 압축'
    ],
}
(out / 'director_synthesis.json').write_text(json.dumps(review, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
event_path = root / 'output/telegram_conversation/inbox/718066299.json'
event = json.loads(event_path.read_text(encoding='utf-8-sig'))
event.update(
    application_status='applied',
    applied_at=datetime.now(timezone.utc).isoformat(),
    application_result='Whole-script and final-video sampled editorial review completed; recommendations recorded; no script/media changes, generation, gate approval, or upload.',
    review_paths=[str(out / 'director_synthesis.json'), str(out / '편집품질_독립검토.md'), str(ep / review['writer_report'])],
)
event_path.write_text(json.dumps(event, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'review': str(out / 'director_synthesis.json'), 'video_unchanged': True}, ensure_ascii=False))
