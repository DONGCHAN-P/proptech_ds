"""Package a script draft and sentence-linked visual plan; never render or send."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import re
import os

ROOT = Path(__file__).resolve().parents[1]
EP = ROOT / 'video-agent-studio/episodes/regional-price-recovery-20261022'
OUT = EP / 'outputs/script-review-v2'
DATA = ROOT / 'analysis/housing_growth_2006/regional_expansion_v1'
NOW = dt.datetime.now(dt.timezone.utc).isoformat()

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

text = (OUT / 'script_v2.md').read_text(encoding='utf-8')
pattern = r'### (S\d+)\. ([^\n]+)\n\n\*\*낭독\*\*\n\n(.*?)\n\n\*\*화면\*\*\n\n(.*?)(?=\n\n###|\n\n---)'
sections = re.findall(pattern, text, re.S)
assert [s[0] for s in sections] == [f'S{i:03}' for i in range(1, 13)]

# One visual state for each exact narration paragraph, not a generic chapter slide.
beats = {
'S001': ['서울·대구 선과 기준100, 두 종점 라벨을 발화 순서로 밝힘', '7개 지역선과 2026Q2 종점 커서 등장; 자체 지수 각주 유지', '고점·저점·현재 세 위치에 표식을 차례로 붙임'],
'S002': ['2020~2022 구간만 음영; 각 지역 기준 고점 표식', '원리 예시 100→80→96→100; 같은 축에서 +20%와 +25% 구분', '원리 예시를 닫고 실제 회복 차트의 100선으로 연결'],
'S003': ['지역별 고점을 100에 맞추는 정규화 동작; 가격 금액 비교와 구별', '7개 패널의 종점·100선 간격; 경기의 표본 민감도 표시', '실제 지역선은 유지하고 서로 다른 높이·간격을 동시에 읽을 시간 확보'],
'S004': ['서울·인천 두 선과 공통 고점 분기 표식', '서울 하락·반등을 순서대로 그리고 2024Q3 첫 교차 강조', '인천 하락·반등 뒤 100까지 남은 간격 강조', '지역 집계선 아래 지역 집계와 개별 단지의 범위 도식; 미계산 단지별 가격선·분포·수치 금지'],
'S005': ['경기 기본 선의 고점→저점→종점, -4.08% 표시', '단지·면적 집단의 양쪽 분기 거래 수 필터 2→3→5', '세 기준별 독립 요약 패널에 각 기준 고점과 종점 거리 표시; 요약점들을 꺾은선으로 잇지 않음', '거래 많은 표본이라는 선택 조건을 남김; 특정 기준을 정답 체크로 표시 금지'],
'S006': ['부산·대구 선을 같은 달력에서 밝힘', '각 지역 기준 고점 이후~2026Q2의 관측 저점을 가로 달력에 옮겨 2022Q4·2023Q1·2025Q2 구분', '부산·대구 각 선의 낙폭·누적 반등·고점 거리 순차 강조', '같은 최근 구간 음영 안에 서로 다른 경로; 고점 이후 관측 최저와 미래 바닥 구별'],
'S007': ['대전의 고점·관측 저점·종점 구간', '세종의 더 깊은 낙폭과 현재 위치', '저점 대비 반등의 순서에서 고점까지 거리 순서로 강조 대상 교체', '기사형 숫자 카드의 출발점 항목을 확대 없이 고정해 표시; 가상 기사로 명시'],
'S008': ['같은 2026Q2 종점과 3·5·10년 시작점 눈금', '세종 선에서 세 구간을 순서대로 강조하고 CAGR 교체', '세종 실제 경로는 유지하며 시작점이 상승 전·상승 중·저점 근처임을 연결', '대구 선으로 교체해 동일 기간 3개 결과 표시', '실제 변동선 위에 시작·끝만 연결하는 복리 설명용 보조선; 실측과 구별'],
'S009': ['2006 시작 여섯 지역 패널; 세종은 공백을 유지', '7개 공통2015Q1=100 보기로 교체; 세종 미확보 과거를 잇지 않음', '2016Q2→2026Q2만 음영 처리하고 서울·대전·대구10년 값 표시', '지수→실제 비용 관계를 짧은 도식으로 설명; 가격 지수와 보유수익 합성 금지'],
'S010': ['실제 가격선 옆에 공급·이동·일자리·금융 시간축 자리 배치', '전체 주택 준공→기존 주택 대비→준공 후 미분양의 서로 다른 분모·단계', '대구 준공 원문 2023년31,630호·2024년29,441호 행 강조. 전체 주택·공표 경계, 가격은 군위 제외라는 조건을 병기', '총인구·가구·연령 이동·직장과 거주의 다른 범위를 도식화', '2025서울-26,769명·인천+32,264명 순이동 원문과 두 지역 가격선; 서로 다른 기간을 명시하고 인과 화살표 금지', '동일 시간축 금융 여건과 지역 수요·공급을 점선 질문으로 연결; 검증한 원인 화살표 금지'],
'S011': ['같은 단지·면적의 두 분기 집계 구조와 평균 금액과의 차이', '실제 매칭 단지 수 보조 그래프에 서울43·세종35 최소 구간 표시', '광주 자료 확인 중 배지, 값0이나 가격선 없이 제외', '지역→생활권→단지의 범위를 좁히는 표식; 매수 추천 문구 금지'],
'S012': ['앞서 사용한 세 차트의 작은 예고 위치만 배치', '인천·세종 반등과 고점 거리 장면 회수', '저점 시계 달력 장면 회수', '3·5·10년과 경기 표본 비교 장면 회수', '가격 가정2%는 별도 시나리오 카드로 연결하고 관측선과 구분', '다음 편 공급·미분양 검증 시간축, 미계산 결과는 빈칸', '채널 CTA, 마지막 발화+3초 뒤 기존 아웃트로; 시간은 실제 음성 후 확정'],
}
assets = {
'price': ('analysis/housing_growth_2006/regional_expansion_v1/quarterly_index.csv', '확보(지수·표본수); 발화 연동 모션 제작 예정', '이미 확보된 regional_peak_recovery.png를 같은 정보 범위로 사용'),
'sensitivity': ('analysis/housing_growth_2006/regional_expansion_v1/sensitivity.csv', '확보(표본별 요약); 기준별 독립 요약 패널 제작 예정. 다른 문턱의 시계열은 미확보', '각 기준의 고점·종점 거리 표와 확보된 2건 기준 실측선만 사용'),
'long': ('analysis/housing_growth_2006/regional_expansion_v1/quarterly_index.csv', '확보; 2006 여섯 지역/2015 공통 보기 모션 예정', '확보된 regional_long_run.png와 시작점 각주'),
'factors': ('video-agent-studio/episodes/regional-price-recovery-20261022/research/script-v2-factors/verified_examples.json', '가격·전체 주택 준공·순이동 예시 확보 및 검증 / 인과·가구·연령·일자리 패널 미완', '기존 가격선에 검증 질문만 연결; 미검증 수치 그래프 생략'),
'example': ('수학 예시 100×0.8×1.2=96; 100/80-1=25%', '직접 제작 예정·관측자료 아님', '고정 예시 도식과 원리 설명'),
}
scenes = []
story = ['# 지역별 가격 회복 v2 자료화면 설계', '', '대본의 각 낭독 문단을 P1, P2…로 연결한다. 초 단위 시간은 실제 음성 정렬 후 확정한다. 차트는 자체 집계와 공식 통계를 구별한다. 크림 바탕·Pretendard 일반/굵게·작은 브랜드 행·굵은 제목·얇은 연도축·고정 흰 본문 자막 박스를 계승한다. 외부 사진·유료 생성 없이 우선 제작 가능한 설계다. 집·가구·직장 조각 아이콘은 의미 안내에만 쓰며 실제 지역 증거를 대신하지 않는다.', '']
spoken = []
for sid, title, narration, visual in sections:
    paragraphs = narration.split('\n\n')
    assert len(paragraphs) == len(beats[sid]), (sid, len(paragraphs), len(beats[sid]))
    typ = 'sensitivity' if sid == 'S005' else 'long' if sid == 'S009' else 'factors' if sid == 'S010' else 'example' if sid == 'S002' else 'price'
    source, status, alternative = assets[typ]
    claim_ids = ['RPR-'+sid, 'METHOD-V2']
    scene = {'scene_id': sid, 'message': title, 'narration_text': narration, 'claim_ids': claim_ids, 'material_type': 'chart_and_data_motion' if typ != 'factors' else 'chart_and_testable_hypothesis', 'asset_ids': [typ], 'script_revision': 'v2', 'audio_revision': None, 'start': None, 'end': None, 'timing_basis': 'narration_paragraphs_not_audio_locked', 'status': 'script_review_draft', 'visual_instruction': visual.strip(), 'beats': []}
    story += [f'## {sid}. {title}', '', f'**根拠 / 근거:** `{source}`. 자체 제작 차트는 원자료 출처를 병기한다. 기존 채널 자산의 권리 기록을 계승하며 신규 외부 사진·음악 이용허락을 가정하지 않는다.', '', f'**준비 상태:** {status}. **대안:** {alternative}.', '', '| 연결 | 낭독 시작 | 화면에서 보여줄 것·강조 동작 |', '|---|---|---|']
    for n, (paragraph, motion) in enumerate(zip(paragraphs, beats[sid]), 1):
        scene['beats'].append({'beat_id': f'{sid}-P{n}', 'narration_text': paragraph, 'purpose': title, 'visual': motion, 'source': source, 'readiness': status, 'alternative': alternative, 'start': None, 'end': None})
        story.append(f'| {sid}-P{n} | {paragraph[:48]}… | {motion} |')
    story.append('')
    scenes.append(scene)
    spoken.append(narration)

(OUT / 'visual_storyboard.md').write_text('\n'.join(story).replace('根拠 / ', '') + '\n', encoding='utf-8')
(OUT / 'narration_v2.txt').write_text('\n\n'.join(spoken) + '\n', encoding='utf-8')
write(EP / 'scenes.json', {'episode_id': EP.name, 'script_revision': 'v2', 'timing_locked': False, 'scenes': scenes})
write(OUT / 'scenes_v2.json', {'episode_id': EP.name, 'script_revision': 'v2', 'timing_locked': False, 'scenes': scenes})

hangul = len(re.findall('[가-힣]', '\n'.join(spoken)))
manifest = {'script_revision': 'v2', 'checked_at_utc': NOW, 'scene_count': len(scenes), 'narration_paragraphs': sum(len(s['beats']) for s in scenes), 'spoken_hangul_syllables': hangul, 'duration_basis': 'Target11-14minutes; no actual audio. Count alone is not a measured runtime.', 'files': {}, 'immutable_inputs': {}, 'checks': {'scene_ids_unique': True, 'each_paragraph_has_visual_state': True, 'narration_has_no_screen_instructions': '**화면**' not in '\n'.join(spoken), 'all_timing_unlocked': all(s['start'] is None and s['end'] is None for s in scenes)}, 'actual_listening': False, 'continuous_playback': False, 'rendered': False}
for p in [OUT/'script_v2.md', OUT/'visual_storyboard.md', OUT/'수치와_자료근거.md', OUT/'클로드_협업상태.md', OUT/'claude_editorial_review_v2.md', OUT/'수정내역.md', OUT/'narration_v2.txt', OUT/'scenes_v2.json']:
    manifest['files'][p.relative_to(ROOT).as_posix()] = {'bytes': p.stat().st_size, 'sha256': sha(p)}
for p in [DATA/'results.json', DATA/'regional_summary.csv', DATA/'sensitivity.csv', DATA/'quarterly_index.csv']:
    manifest['immutable_inputs'][p.relative_to(ROOT).as_posix()] = sha(p)
write(OUT / 'package_checks.json', manifest)
print(json.dumps({k: manifest[k] for k in ('scene_count', 'narration_paragraphs', 'spoken_hangul_syllables', 'checks')}, ensure_ascii=False))
