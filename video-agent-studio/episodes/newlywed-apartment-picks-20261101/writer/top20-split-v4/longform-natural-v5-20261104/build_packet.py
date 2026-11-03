"""승인 v4의 문장 ID를 유지하는 v5 문구 제안. 로컬 파일만 읽고 쓴다."""
import hashlib
import json
import re
import shutil
from pathlib import Path

ROOT = Path('C:/projects/realestate_reco')
EP = ROOT / 'video-agent-studio/episodes/newlywed-apartment-picks-20261101'
OUT = Path(__file__).resolve().parent
TASK = 'longform-natural-v5-20261104'
MANIFEST = EP / 'narration/top20-split-v4/jun-and-shorts-v1/narration_manifest.json'
TIMING = MANIFEST.with_name('timing_proposals.json')

# 요청한 부분만 교체한다. 여기 없는 ID의 표시문·낭독문은 바꾸지 않는다.
EDITS = {
    'P01-INTRO-V3-02': '‘데이터로보는부동산’에서는 신혼부부가 매매를 검토할 만한 지역과 아파트를 데이터로 살펴봅니다.',
    'P01-INTRO-V3-03': '먼저 신혼부부가 실제로 많이 사는 곳을 찾아, 앞으로 소개할 지역을 골라봤습니다.',
    'P01-INTRO-V3-04': '2024년 신혼부부 통계를 보고, 지역마다 신혼부부가 몇 쌍씩 살고 있는지 비교한 거죠.',
    'P01-R20-V2-02': '중동과 상동에 걸친 중동신도시에서는 아파트 단지와 마을, 주변 거리를 함께 살펴보겠습니다.',
    'P01-R20-V2-04': '상동의 거리 사진에서는 아파트와 주변 거리를 보며, 단지 안팎에서의 생활을 함께 떠올릴 수 있습니다.',
    'P01-R20-V2-05': '준공 시기로 나눠 보면 거래 중위값은 2000년까지 지어진 아파트가 6억원, 2011년 이후 지어진 아파트가 8억9,900만원입니다.',
    'P01-R20-V2-07': '중동의 미리내마을(롯데2) 주변에는 계남초등학교·계남중학교가 표시되고, 신중동역의 위치도 같은 상세 지도에서 확인할 수 있습니다.',
    'P01-R19-V2-03': '공식 주거정보에는 주변 서울의료원과 청남공원도 나와 있어, 지하철과 병원, 공원의 위치를 함께 살펴볼 수 있습니다.',
    'P01-R19-V2-04': '신내역 일대의 자료사진에서는 지하철과 버스를 갈아타는 역 주변 모습을 살펴보겠습니다.',
    'P01-R19-V2-05': '면목동 현대 단지 주변으로 옮기면 서울면남초등학교·용마중학교와 7호선 용마산(용마폭포공원)역의 위치를 상세 지도에서 살펴보겠습니다.',
    'P01-R19-V2-06': '신내동의 경춘선·6호선과 면목동의 7호선 중 직장 방향에 맞는 노선을 먼저 고르면, 같은 중랑구 안에서도 비교할 동네를 추릴 수 있습니다.',
    'P01-R19-V2-07': '두 생활권의 거래 중위값은 신내동 7억4,000만원, 면목동 8억4,000만원으로, 예산과 이용할 지하철 노선을 함께 비교할 수 있습니다.',
    'P01-R19-V2-08': '장보러 가는 길과 공원 가는 길도 단지에서 출발해 살펴보면, 출퇴근과 주말 생활에 맞는 동네를 골라볼 수 있습니다.',
    'P01-R18-V2-03': '직장이 어디에 있는지부터 지도에서 찾으면, 넓은 기흥구에서 집과 직장을 오갈 길부터 비교해 볼 수 있습니다.',
    'P01-R18-V2-04': '구성역에서는 GTX-A와 수인분당선을 이용할 수 있고, 사진 속 5번출구에는 버스 이용 안내가 있습니다.',
    'P01-R18-V2-05': '영덕동 용인기흥효성해링턴플레이스 주변 상세도에서는 청곡초등학교와 상갈역을 기준으로 단지의 위치를 살펴보겠습니다.',
    'P01-R18-V2-06': '구성역의 GTX-A·수인분당선 이용을 우선할지, 영덕동의 단지와 학교 주변을 볼지에 따라 확인할 이동 경로도 달라집니다.',
    'P01-R18-V2-07': '거래 중위값은 동백동 5억2,000만원, 영덕동 7억1,500만원으로, 원하는 동네와 예산을 함께 좁혀볼 수 있습니다.',
    'P01-R18-V2-08': '학교와 장보러 가는 길에 실제 출근길을 더해, 두 사람이 매일 오갈 길을 함께 살펴보겠습니다.',
    'P01-R17-V2-02': '연수구에는 연수2동의 아파트와 중심상가, 송도의 국제업무·바이오산업 지역이 함께 있습니다.',
    'P01-R17-V2-03': '평소 이용할 상가와 직장이 같은 동네에 있는지, 서로 떨어져 있어 오가야 하는지 살펴보면 집을 비교하기가 수월합니다.',
    'P01-R17-V2-04': '송도 센트럴파크는 해수 수로와 산책정원을 갖춘 공간으로, 사진에서는 산책하며 여가를 보낼 곳을 살펴보겠습니다.',
    'P01-R17-V2-06': '직장 위치와 원하는 집의 상태를 먼저 정하면, 연수동 일대를 먼저 볼지 송도를 먼저 볼지 정하기가 수월합니다.',
    'P01-R17-V2-07': 'e편한세상송도 상세도에서는 인천송담초등학교·인천미송중학교와 송도달빛축제공원역을 놓고 학교와 지하철역의 위치를 함께 살펴보겠습니다.',
    'P01-R17-V2-08': '공원 이용과 매일의 출근길, 장보러 가는 길을 단지에서 출발해 살펴보면, 같은 연수구 안에서도 동네별 생활을 비교하기 좋습니다.',
    'P01-R16-V2-03': '소래습지생태공원은 갯벌·습지와 탐방데크가 있는 공간이며, 사진에서는 해안의 생태환경을 즐기는 모습을 살펴볼 수 있습니다.',
    'P01-R16-V2-06': '이 상세 지도에서는 학교와 단지 사이의 길을 살펴보고, 장보러 가는 곳과 직장 위치를 더해 평일에 오갈 길을 그려볼 수 있습니다.',
    'P01-R15-V2-02': '구로구에서는 신도림의 아파트와 지하철 환승, 구로동의 산업·업무시설을 함께 살펴볼 수 있습니다.',
    'P01-R15-V2-03': '신도림로·경인로 주변에 여러 아파트 단지가 있고, 사진의 신도림역은 1호선과 2호선의 환승역입니다.',
    'P01-R15-V2-04': 'G밸리는 구로동과 금천구 가산동에 걸쳐 있어, 직장의 실제 주소를 지도에서 찾으면 집에서 오갈 길을 살펴볼 수 있습니다.',
    'P01-R15-V2-05': '구로동 현대연예인 단지 주변에는 서울구일초등학교·구일중학교·구일고등학교를 표시해 단지와 학교가 어디에 있는지 살펴보겠습니다.',
    'P01-R15-V2-06': '지하철 환승을 우선할지, 학교 주변 동네에서 직장까지 가는 길을 우선할지에 따라 후보를 고르는 기준이 달라집니다.',
    'P01-R15-V2-07': '거래 중위값은 구로동 7억8,000만원, 신도림동 13억2,000만원으로, 직장까지 가는 길과 예산을 함께 놓고 비교할 수 있습니다.',
    'P01-R15-V2-08': '장보러 가는 길과 퇴근 뒤 생활도 실제 후보 단지에서 출발해 살펴보면, 신도림과 구로동 중 두 사람의 일상에 맞는 동네를 비교할 수 있습니다.',
    'P01-R14-V2-03': '우물골 단지 옆의 진관동 주민센터처럼, 공동주택과 공공시설이 어디에 있는지 마을 이름과 함께 살펴볼 수 있습니다.',
    'P01-R14-V2-06': '그 예산에 맞는 단지를 추린 다음, 뉴타운의 마을 구성을 선호하는지 실제 이용할 지하철역 주변을 우선하는지 살펴보겠습니다.',
    'P01-R14-V2-07': '응암동 녹번역센트레빌 주변에는 영락중학교·서울녹번초등학교와 녹번역이 표시돼, 학교와 지하철역의 위치를 함께 확인할 수 있습니다.',
    'P01-R14-V2-08': '진관동의 마을과 응암동의 대표 단지에서 출근길과 학교·장보러 가는 길을 살펴보면, 실제로 비교할 동네를 추려볼 수 있습니다.',
    'P01-R13-V2-04': '금곡동 Y CITY(와이시티) 상세도는 수원중촌초등학교·상촌초등학교·칠보중학교와 단지의 배치를 중심으로 살펴보겠습니다.',
    'P01-R13-V2-05': '권선동 터미널 주변을 볼 때와 금곡동의 학교 주변을 볼 때는, 필요한 교통수단과 자주 가는 곳을 각각 놓고 비교할 수 있습니다.',
    'P01-R13-V2-07': '직장으로 가는 실제 경로와 단지 출입구에서 학교·상점으로 이어지는 길을 더하면, 기존 도심과 택지개발지 중 어디를 볼지 정해볼 수 있습니다.',
    'P01-R12-V2-03': '광교는 공동주택과 업무·상업 용지를 나눠 계획한 곳으로, 집과 직장, 장보러 갈 곳의 위치를 지도에서 함께 살펴볼 수 있습니다.',
    'P01-R12-V2-05': '망포마을쌍용1차 주변으로 옮기면 태장초등학교·잠원중학교와 망포역을 기준으로 학교와 지하철역의 위치를 확인할 수 있습니다.',
    'P01-R11-V2-04': '상계2차 중앙하이츠 상세도에는 상계중학교·서울상계초등학교와 노원역이 표시돼, 단지에서 학교와 지하철역을 향하는 방향을 살펴볼 수 있습니다.',
    'P01-R11-V2-05': '학교와 지하철역, 장보러 갈 곳을 지도에 표시하면, 가족이 자주 오갈 길을 실제 후보 단지별로 비교할 수 있습니다.',
    'P01-R11-V2-07': '택지개발로 조성된 동네의 주변 시설과 집의 수리 범위, 관리 상태를 함께 살펴보면, 같은 예산에서 어떤 집을 비교할지 정해볼 수 있습니다.',
    'P01-OUTRO-V2-01': '같은 구 안에서도 예산과 이용할 노선, 학교와 장보러 가는 길에 따라 비교할 동네는 달라집니다.',
}

# 표기와 낭독을 분리한다. 차수·호선·출구 숫자를 누락하거나 새 차수를 만들지 않는다.
PHONETICS = [
    ('상계2차중앙하이츠', '상계2차 중앙하이츠', '상계 이차 중앙 하이츠', '2차를 유지하고 단어 사이를 띄워 낭독'),
    ('용인기흥효성해링턴플레이스', '용인기흥효성해링턴플레이스', '용인 기흥 효성 해링턴 플레이스', '긴 단지명은 단어 단위로 분리'),
    ('e편한세상송도', 'e편한세상송도', '이편한세상 송도', '브랜드 e를 이로 읽고 송도를 분리'),
    ('미리내마을(롯데2)', '미리내마을(롯데2)', '미리내마을 롯데 이', '원문 롯데2 유지; 근거 없는 차를 덧붙이지 않음'),
    ('망포마을쌍용1차', '망포마을쌍용1차', '망포마을 쌍용 일차', '1차를 일차로 읽음'),
    ('Y CITY(와이시티)', 'Y CITY(와이시티)', '와이시티', '영문 표기와 괄호 설명을 중복 낭독하지 않음'),
    ('GTX-A', 'GTX-A', '지티엑스 에이', '수도권광역급행철도 고유 노선명 유지; 지하철로 일괄 치환하지 않음'),
    ('G밸리', 'G밸리', '지밸리', '영문 G 낭독'),
    ('연수2동', '연수2동', '연수 이 동', '행정동 숫자 유지'),
    ('용마산(용마폭포공원)역', '용마산(용마폭포공원)역', '용마산 용마폭포공원 역', '괄호 부역명 유지; 슬래시를 읽지 않음'),
    ('녹번역센트레빌', '녹번역센트레빌', '녹번역 센트레빌', '역명과 브랜드 사이 분리'),
    ('현대연예인', '현대연예인', '현대 연예인', '단지명 단어 분리'),
    ('논현 웰카운티', '논현 웰카운티', '논현 웰카운티', '원문 띄어쓰기 유지'),
    ('논현 파크 포레', '논현 파크 포레', '논현 파크 포레', '원문 띄어쓰기 유지'),
    ('송도달빛축제공원역', '송도달빛축제공원역', '송도달빛축제공원역', '역 고유명 유지'),
    ('수인분당선', '수인분당선', '수인분당선', '노선명 유지'),
    ('경춘선', '경춘선', '경춘선', '노선명 유지'),
    ('경춘선숲길', '경춘선숲길', '경춘선숲길', '폐선 철길을 바꾼 공원 이름; 지하철로 바꾸지 않음'),
]
NUMBER_READINGS = {
    '2024년': '이천이십사 년', '1호선': '일 호선', '2호선': '이 호선',
    '2000년': '이천 년', '2011년': '이천십일 년', '6억원': '육 억 원',
    '8억9,900만원': '팔 억 구천구백 만 원',
    '6호선': '육 호선', '7호선': '칠 호선', '5번출구': '오 번 출구',
    '7억4,000만원': '칠 억 사천 만 원', '8억4,000만원': '팔 억 사천 만 원',
    '5억2,000만원': '오 억 이천 만 원', '7억1,500만원': '칠 억 천오백 만 원',
    '7억8,000만원': '칠 억 팔천 만 원', '13억2,000만원': '십삼 억 이천 만 원',
}
READING_OVERRIDES = {
    'P01-INTRO-V3-02': '데이터로 보는 부동산에서는 신혼부부가 매매를 검토할 만한 지역과 아파트를 데이터로 살펴봅니다.',
    'P01-INTRO-V3-04': '이천이십사 년 신혼부부 통계를 보고, 지역마다 신혼부부가 몇 쌍씩 살고 있는지 비교한 거죠.',
    'P01-R20-V2-05': '준공 시기로 나눠 보면 거래 중윗값은 이천 년까지 지어진 아파트가 육 억 원, 이천십일 년 이후 지어진 아파트가 팔 억 구천구백 만 원입니다.',
    'P01-R11-V2-04': '상계 이차 중앙 하이츠 상세도에는 상계중학교, 서울상계초등학교와 노원역이 표시돼, 단지에서 학교와 지하철역을 향하는 방향을 살펴볼 수 있습니다.',
}

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def rel(path):
    return path.relative_to(ROOT).as_posix()

def write(name, data):
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def reading(text):
    # 고유명사 전체를 먼저 낭독문으로 고정한 뒤 나머지 숫자를 변환한다.
    # 표시 띄어쓰기만으로 발음이 고쳐졌다고 취급하지 않는다.
    protected = {display: spoken for _, display, spoken, _ in PHONETICS}
    for display in sorted(protected, key=len, reverse=True):
        text = text.replace(display, protected[display])
    for display in sorted(NUMBER_READINGS, key=len, reverse=True):
        text = text.replace(display, NUMBER_READINGS[display])
    text = text.replace('중위값', '중윗값').replace('·', ', ')
    return text.replace('‘', '').replace('’', '').replace('데이터로보는부동산에서는', '데이터로 보는 부동산에서는')

def reason(sid, old):
    if sid == 'P01-R20-V2-05':
        return '부모 검토 반영: 준공 집단을 지어진 아파트로 풀어 말함; 2000년까지·2011년 이후 구간과 두 중위가격, 기존 숫자 낭독을 유지'
    if sid == 'P01-INTRO-V3-04':
        return '부모 검토 반영: 2024년 통계 근거를 유지하며 몇 쌍씩 사는지 비교했다는 구어체로 설명'
    if 'INTRO-V3' in sid:
        return '기존 02~04 안에서 채널명·목표, 실제 거주 수로 지역을 고르는 이유, 2024년 통계 기준을 순서대로 설명; 05~06의 이번 편 범위와 후속 예산별 비교는 유지'
    if sid == 'P01-R11-V2-04':
        return '실제 단지의 2차를 유지하고 표시 띄어쓰기와 낭독 단어 경계를 분리; 철도역 문맥은 지하철역으로 구체화'
    tags = []
    if '철도' in old:
        tags.append('출퇴근 문맥의 철도 표현을 지하철·실제 노선명으로 구체화')
    if any(x in old for x in ('읽', '기준점', '가로', '기능', '권역', '권을', '거점', '구체화', '연결', '방식')):
        tags.append('추상적인 공간·기능 설명을 위치·거리·오가는 길 등 말로 설명하기 쉬운 표현으로 수정')
    if sid in ('P01-R18-V2-04', 'P01-R18-V2-06'):
        tags.append('GTX-A와 수인분당선의 고유 노선명을 유지')
    return '; '.join(tags) or '문장의 기존 설명과 비교 제안은 유지하며 어색한 문어체만 구어체로 정리'

def numeric_tokens(text):
    return re.findall(r'\d[\d,]*(?:\.\d+)?', text)

def main():
    assert not (OUT / 'freeze_manifest.json').exists(), '동결본은 덮어쓰지 않음. 추가 요청은 별도 버전으로 처리.'
    snapshot = OUT / 'parent_review_before_tweaks'
    if not snapshot.exists():
        snapshot.mkdir()
        for name in ('script_v5.md', 'sentence_patches.json', 'sentence_mapping.json', 'before_after.md', 'phonetics.json', 'validation.json', 'handoff.json', 'verification.json'):
            shutil.copyfile(OUT / name, snapshot / name)
    reviewed_mapping = read(snapshot / 'sentence_mapping.json')['sentences']
    manifest, timing = read(MANIFEST), read(TIMING)
    reader = ROOT / manifest['main_reader_script']
    scenes_path = EP / 'writer/top20-split-v4/scene_proposals_v2.json'
    intro_path = EP / 'writer/top20-split-v4/intro-rationale-v3/intro_proposal_v3.json'
    criteria_path = EP / 'writer/top20-split-v4/map-clean-v1/criteria_script.json'
    language_path = ROOT / 'config/video_language.json'
    language_guide = ROOT / 'video-agent-studio/guides/대본_자연스러운표현과_발음.md'
    language = read(language_path)
    protected_sanggye = next(p for p in language['protected_names'] if p['canonical_name'] == '상계2차중앙하이츠')
    assert protected_sanggye['display_name'] == '상계2차 중앙하이츠'
    assert protected_sanggye['reading_text'] == '상계 이차 중앙 하이츠'
    shorts_files = [EP / f'writer/top20-split-v4/jun-and-shorts-v1/{name}.json' for name in ('short01_promo', 'short02_ranks20_16', 'short03_ranks15_11')]
    inputs = [MANIFEST, TIMING, reader, scenes_path, intro_path, criteria_path, language_path, language_guide, *shorts_files]
    input_rows = [{'path': rel(p), 'sha256': sha(p)} for p in inputs]
    baseline = [s for s in manifest['sentences'] if s['kind'] == 'accepted_main']
    timed = {s['sentence_id']: s for s in timing['sentences']}
    assert len(baseline) == 90 and len({s['sentence_id'] for s in baseline}) == 90
    assert set(EDITS) <= {s['sentence_id'] for s in baseline}
    assert sha(reader) == manifest['main_reader_script_sha256']
    assert sha(MANIFEST) == timing['manifest']['sha256']
    evidence = {}
    for i, scene in enumerate(read(scenes_path)['scenes']):
        for j, sentence in enumerate(scene.get('sentences', [])):
            evidence[sentence['sentence_id']] = {
                'path': rel(scenes_path), 'json_pointer': f'/scenes/{i}/sentences/{j}',
                'claim_ids': sentence.get('claim_ids', []),
                'source_fields': sentence.get('source_fields', []),
                'material_types': sentence.get('material_types', []),
            }
    shorts = {p.stem: [s['sentence_id'] for s in read(p)['sequence']] for p in shorts_files}
    patches, mapping = [], []
    for original in baseline:
        sid = original['sentence_id']
        assert original['text'] == timed[sid]['text']
        assert original['reading_text'] == timed[sid]['reading_text']
        new_text = EDITS.get(sid, original['text'])
        new_reading = READING_OVERRIDES.get(sid, reading(new_text)) if sid in EDITS else original['reading_text']
        if sid in READING_OVERRIDES:
            assert reading(new_text) == new_reading
        links = [name for name, ids in shorts.items() if sid in ids]
        inherited_evidence = evidence.get(sid)
        if inherited_evidence is None:
            inherited_evidence = {
                'path': rel(criteria_path if 'CRITERIA' in sid else intro_path),
                'sentence_id': sid,
                'claim_ids': ['W4-METHOD'] if 'CRITERIA' in sid else (['W4-RANK-SCOPE'] if sid in ('P01-INTRO-V3-04', 'P01-INTRO-V3-05') else []),
                'claim_note': '기존 근거 참조용 분류; 새 사실 근거를 추가하지 않음',
                'material_types': ['editorial_card'] if sid in ('P01-INTRO-V3-01', 'P01-INTRO-V3-02', 'P01-INTRO-V3-06') else (['map'] if sid in ('P01-INTRO-V3-07', 'P01-INTRO-V3-08') else ['data_chart']),
            }
        row = {
            'sentence_id': sid, 'oldID': sid, 'scene_id': timed[sid]['scene_id'],
            'main_order': original['main_order'], 'text': new_text, 'reading_text': new_reading,
            'changed': sid in EDITS, 'evidence_reference': inherited_evidence,
            'linked_shorts': links, 'status': 'writing_reference_pending_parent_review',
        }
        mapping.append(row)
        if sid in EDITS:
            numeric_ok = numeric_tokens(original['text']) == numeric_tokens(new_text)
            assert numeric_ok or sid == 'P01-INTRO-V3-04', sid
            assert not re.search(r'\d|[A-Za-z/]', new_reading), (sid, new_reading)
            patches.append({
                'oldID': sid, 'sentence_id': sid, 'new_sentence_id': sid,
                'scene_id': row['scene_id'], 'old_text': original['text'], 'new_text': new_text,
                'old_reading_text': original['reading_text'], 'new_reading_text': new_reading,
                'reason': reason(sid, original['text']),
                'facts_preserved': {
                    'preserved': True,
                    'numeric_tokens_unchanged': numeric_ok,
                    'only_numeric_addition': '기존 브리프·도입 근거의 2024년 통계를 명시' if not numeric_ok else None,
                    'price_rank_sample_period_region_evidence': '순위·지역·쌍 수·가격·기간·면적과 원본 표본/출처 참조를 유지; 재집계·새 인과·매수 가능성 주장 없음',
                    'evidence_reference': inherited_evidence,
                },
                'linked_shorts_impact': {
                    'short_ids': links,
                    'action': '부모가 해당 문장 재사용 여부와 자막·음성·컷 길이를 새 버전에서 판단' if links else '기존 쇼츠 원문에 직접 재사용되지 않는 본편 문장',
                    'existing_assets_modified': False,
                },
            })
    changed_scenes = list(dict.fromkeys(p['scene_id'] for p in patches))
    review_deltas = []
    for before, after in zip(reviewed_mapping, mapping):
        assert before['sentence_id'] == after['sentence_id']
        text_changed = before['text'] != after['text']
        reading_changed = before['reading_text'] != after['reading_text']
        if text_changed or reading_changed:
            review_deltas.append({'sentence_id': after['sentence_id'], 'text_changed': text_changed, 'reading_changed': reading_changed})
    assert {r['sentence_id'] for r in review_deltas} == {'P01-INTRO-V3-02', 'P01-INTRO-V3-04', 'P01-R20-V2-05'}
    chunk_changes = []
    for chunk in timing['chunks']:
        ids = [sid for sid in chunk['sentence_ids'] if sid in EDITS]
        if ids:
            chunk_changes.append({'asset_id': chunk['asset_id'], 'scene_id': chunk['scene_id'], 'changed_sentence_ids': ids, 'original_chunk_duration_s_reference_only': chunk['duration_s'], 'new_duration_s': None})
    intro_old = [s for s in baseline if timed[s['sentence_id']]['scene_id'].startswith('INTRO-')]
    intro_new = [s for s in mapping if s['scene_id'].startswith('INTRO-')]
    length_old = sum(len(s['reading_text']) for s in intro_old)
    length_new = sum(len(s['reading_text']) for s in intro_new)
    old_intro_time = sum(c['duration_s'] for c in timing['chunks'] if c['scene_id'].startswith('INTRO-'))
    estimate = {
        'basis': '기존 Jun 도입 청크의 실측 길이에 낭독 문자 수 비율을 적용한 estimate; 새 음성의 길이가 아님',
        'old_intro_measured_chunk_sum_s': round(old_intro_time, 2),
        'old_intro_reading_characters': length_old, 'new_intro_reading_characters': length_new,
        'reading_character_change_percent': round((length_new / length_old - 1) * 100, 2),
        'new_intro_duration_estimate_s_rounded': round(old_intro_time * length_new / length_old),
        'timing_locked': False,
    }
    write('sentence_patches.json', {'task_id': TASK, 'status': 'writing_reference_only_not_approved', 'patch_count': len(patches), 'parent_review_delta': review_deltas, 'patches': patches, 'input_revisions': input_rows})
    write('sentence_mapping.json', {'task_id': TASK, 'main_sentence_count': 90, 'sentences': mapping, 'unchanged_shared_cta_sentence_ids': ['SHORTS-CTA-01', 'SHORTS-CTA-02'], 'status': 'writing_reference_only'})
    write('phonetics.json', {
        'task_id': TASK, 'scope': '발음 보호가 필요한 단지명·영문명·숫자 포함 고유명과 교통명; 실제 TTS 발음 미청취',
        'entries': [{'canonical_entity': c, 'display_name': d, 'reading_text': r, 'note': n} for c, d, r, n in PHONETICS] + [{'canonical_entity': '데이터로보는부동산', 'display_name': '데이터로보는부동산', 'reading_text': '데이터로 보는 부동산', 'note': '표시 브랜드 유지; 낭독만 단어 단위로 띄움'}],
        'emphasis': ['데이터로보는부동산', '2024년 신혼부부 통계', '20위부터 11위', '단지별 중위가격', '상계 이차 중앙 하이츠'],
        'reading_policy': '슬래시·괄호 문자를 읽지 않음; 차수와 노선 번호를 유지; 학교·역 이름은 원문을 유지',
        'precedence': '보호 고유명사의 전체 낭독을 숫자 변환보다 먼저 고정; P01-R11-V2-04는 전체 낭독문을 명시적으로 지정',
        'language_config': {'path': rel(language_path), 'revision': language['revision'], 'sha256': sha(language_path)},
        'must_listen_before_final_merge': ['P01-R11-V2-04'],
    })
    title_by_scene = {'INTRO-HOOK': '도입', 'INTRO-PURPOSE': '채널과 지역 선정 기준', 'INTRO-CRITERIA': '가격 기준', 'INTRO-METHOD': '지도 보는 법', 'P01-OUTRO': '마무리'}
    for s in mapping:
        if re.fullmatch(r'P01-R\d{2}', s['scene_id']) and s['sentence_id'].endswith('-01'):
            title_by_scene[s['scene_id']] = s['text'].split(',')[0].replace('위는 ', '위 · ')
    lines = ['# 신혼부부 거주 TOP20 · 1편 20~11위 · 대본 v5', '', '문구 검토용 기준 제안입니다. 승인·음성 생성·시간 확정·렌더 완료 상태가 아닙니다.', '', '문장 ID는 기존 90개를 그대로 유지합니다. 변경 전후·낭독문은 sentence_patches.json, 전체 대응은 sentence_mapping.json을 봅니다.', '']
    previous = None
    for s in mapping:
        if s['scene_id'] != previous:
            lines += ['## ' + title_by_scene[s['scene_id']], '']
            previous = s['scene_id']
        lines += [f'<!-- {s["sentence_id"]} -->', s['text'], '']
    lines += ['---', '', '제작 참고: 신혼부부 거주 수는 지역 선정의 출발점입니다. 지역별 적합성·가격 상승·매수 가능 여부를 증명하는 지표로 확대하지 않습니다.', '', '통계: 기존 근거의 2024.11.01 거주 기준, 수도권 53개 구. 가격: 2026.05~10 계약, 전용 83~85㎡, 2026.11.03 조회, 취소 제외, 10월은 조회일까지 신고분. 지도 점은 단지별 거래 중위가격, 동별 비교 가격과 표본은 원본 근거의 정의를 그대로 사용합니다.', '', f'도입 길이: estimate 약 {estimate["new_intro_duration_estimate_s_rounded"]}초. 기존 도입 청크 합계 {estimate["old_intro_measured_chunk_sum_s"]}초에 낭독 문자 수 비율을 적용한 참고치이며 새 음성 길이가 아닙니다.', '', '상계2차 중앙하이츠 → 상계 이차 중앙 하이츠. 다른 발음 보호명과 강조어는 phonetics.json 참조.', '']
    (OUT / 'script_v5.md').write_text('\n'.join(lines), encoding='utf-8')
    compare = ['# v4 → v5 문구 변경', '', f'본편 90개 ID 중 {len(patches)}개를 수정하고 {90-len(patches)}개는 표시문·낭독문 모두 유지했습니다. 문장 추가·삭제와 순위 재배열은 없습니다.', '', '도입은 기존 02~04만 교체했습니다. 채널 목표 → 실제 거주 수를 출발점으로 지역 선정 → 2024년 통계 → 기존 53개 구·20~11위 범위 → 기존 후속 예산별 아파트 비교 순서입니다.', '', f'도입 낭독문은 {length_old}자에서 {length_new}자({estimate["reading_character_change_percent"]:+.2f}%)입니다. 길이는 estimate이며 실제 새 음성은 없습니다.', '', 'GTX-A·수인분당선·경춘선 등 고유 노선명은 유지합니다. KTX는 이 본편 원문에 등장하지 않습니다. 폐선 철길·경춘선숲길의 철길 의미는 유지합니다.', '', '순위와 10개 지역, 쌍 수·가격·면적·집계 기간은 유지했습니다. 표본 수와 출처는 기존 문장별 근거를 그대로 참조하며 새 집계·원자료 재검증을 수행하지 않았습니다.', '', '## 문장별 비교', '']
    for p in patches:
        compare += [f'### {p["oldID"]}', '', f'- 전: {p["old_text"]}', f'- 후: {p["new_text"]}', f'- 낭독: {p["new_reading_text"]}', f'- 이유: {p["reason"]}', '- 쇼츠: ' + (', '.join(p['linked_shorts_impact']['short_ids']) if p['linked_shorts_impact']['short_ids'] else '직접 재사용 없음'), '']
    compare += ['## 후속 처리', '', '이 문구안은 writing authority reference입니다. 부모 총괄이 대본 결정·변경 청크·새 정확한 예산 제안·독립 QA를 연결합니다. 기존 6500 크레딧 상한은 이 수정안의 새 유료 생성 승인으로 기록하지 않습니다.', '', 'TTS·외부 API·Claude·업로드·기존 영상/음성 변경은 실행하지 않았습니다. 기존 문장의 시간값은 v5에 복사하지 않았습니다.', '']
    (OUT / 'before_after.md').write_text('\n'.join(compare), encoding='utf-8')
    with (OUT / 'before_after.md').open('a', encoding='utf-8') as f:
        f.write('\n부모 검토 후 추가 반영: INTRO04·R20-05 표시문과 읽기문 수정, INTRO02는 읽기문 띄어쓰기만 수정. 직전 writer 검토본은 parent_review_before_tweaks에 보존했습니다. 그 외 표시문·읽기문은 바꾸지 않았습니다.\n')
    linked_impact = {name: [sid for sid in ids if sid in EDITS] for name, ids in shorts.items()}
    validation = {
        'task_id': TASK, 'status': 'local_text_mapping_checks_passed_not_independent_qa',
        'checks': {
            'canonical_main_count_90': True, 'manifest_timing_text_reading_match_90': True,
            'reader_sha_matches_manifest': True, 'manifest_sha_matches_timing': True,
            'all_90_sentence_ids_and_order_preserved': [s['sentence_id'] for s in baseline] == [s['sentence_id'] for s in mapping],
            'unchanged_sentence_text_and_reading_preserved': all(s['text'] == o['text'] and s['reading_text'] == o['reading_text'] for s, o in zip(mapping, baseline) if not s['changed']),
            'rank_count_and_order_preserved': all(s['text'] == o['text'] for s, o in zip(mapping, baseline) if re.fullmatch(r'P01-R\d{2}-V2-01', s['sentence_id'])),
            'numeric_tokens_preserved_except_documented_intro_2024': all(numeric_tokens(o['text']) == numeric_tokens(s['text']) for s, o in zip(mapping, baseline) if s['sentence_id'] != 'P01-INTRO-V3-04'),
            'protected_price_criteria_sentences_unchanged': all(s['text'] == o['text'] for s, o in zip(mapping, baseline) if 'CRITERIA' in s['sentence_id']),
            'no_unread_digits_latin_or_slashes_in_changed_readings': all(not re.search(r'\d|[A-Za-z/]', p['new_reading_text']) for p in patches),
            'sanggye_2nd_retained': next(s for s in mapping if s['sentence_id'] == 'P01-R11-V2-04')['reading_text'].startswith('상계 이차 중앙 하이츠 '),
            'sanggye_explicit_reading_override_matches_protected_name_config': READING_OVERRIDES['P01-R11-V2-04'].startswith(protected_sanggye['reading_text'] + ' '),
            'only_three_requested_parent_review_sentence_ids_changed': {r['sentence_id'] for r in review_deltas} == {'P01-INTRO-V3-02', 'P01-INTRO-V3-04', 'P01-R20-V2-05'},
            'intro02_display_brand_unchanged_reading_spaced': next(s for s in mapping if s['sentence_id'] == 'P01-INTRO-V3-02')['reading_text'].startswith('데이터로 보는 부동산에서는 '),
            'all_input_hashes_unchanged_after_write': all(sha(ROOT / x['path']) == x['sha256'] for x in input_rows),
        },
        'changed_sentence_count': len(patches), 'unchanged_sentence_count': 90-len(patches),
        'parent_review_delta': review_deltas,
        'changed_scene_ids': changed_scenes, 'changed_chunks_reference_only': chunk_changes,
        'linked_shorts_changed_sentence_ids': linked_impact, 'intro_duration_estimate': estimate,
        'reading_characters': {'old_full_main': sum(len(s['reading_text']) for s in baseline), 'new_full_main': sum(len(s['reading_text']) for s in mapping), 'changed_sentences_new': sum(len(p['new_reading_text']) for p in patches), 'note': '문자 수는 로컬 원문 길이. 새 유료 청크 입력·예상 비용·상한의 정확한 제안과 승인 판단은 부모 총괄 담당'},
        'actual_listening': False, 'continuous_playback': False, 'new_audio_generated': False,
        'independent_qa_performed': False, 'new_paid_generation_authorized_by_this_packet': False,
        'input_revisions': input_rows,
    }
    assert all(validation['checks'].values()), validation['checks']
    write('validation.json', validation)
    write('issue_V5-PARENT-ADOPTION.json', {
        'issue_id': 'V5-PARENT-ADOPTION', 'task_id': TASK, 'scene_ids': changed_scenes,
        'problem': '문구안 채택 시 기존 Jun 청크·자막·일부 쇼츠 재사용 구간의 후속 버전 연결 필요',
        'evidence': ['sentence_patches.json', 'validation.json'],
        'proposal': '총괄이 script 결정과 필요한 독립 QA를 진행하고, 유료 생성 전에 이 문구안 기준의 정확한 새 입력·예산 제안을 확정',
        'impact': {'main': changed_scenes, 'shorts': linked_impact, 'shared_cta_changed': False},
        'status': 'proposal_to_director_not_applied', 'peer_message_tool_available': False,
    })
    outputs = ['script_v5.md', 'sentence_patches.json', 'sentence_mapping.json', 'before_after.md', 'phonetics.json', 'validation.json', 'issue_V5-PARENT-ADOPTION.json', 'build_packet.py', 'verify_packet.py', 'verification.json', 'freeze_manifest.json']
    write('handoff.json', {
        'task_id': TASK, 'role': 'writer', 'status': 'writing_reference_ready_for_parent_review_not_approved_or_rendered',
        'artifact_base': rel(OUT),
        'input_revisions': 'validation.json#/input_revisions',
        'outputs': outputs,
        'changed_counts': {'main_total': 90, 'changed': len(patches), 'unchanged': 90-len(patches), 'added_ids': 0, 'removed_ids': 0},
        'reading_characters': {'all_main': validation['reading_characters']['new_full_main'], 'changed_sentences': validation['reading_characters']['changed_sentences_new']},
        'affected_scene_ids': changed_scenes,
        'checks': [{'check': f'문장 ID·숫자·원본 SHA·보호명사·수정 범위 등 로컬 검사 {len(validation["checks"])}개', 'result': 'passed', 'evidence': 'validation.json'}],
        'open_issue_ids': ['V5-PARENT-ADOPTION'], 'issue_path': 'issue_V5-PARENT-ADOPTION.json',
        'unresolved': ['총괄 채택·대본 결정', '독립 QA 미실행', '새 유료 생성 전 정확한 새 예산 제안은 부모 담당', '발음 사전은 제안이며 실제 새 음성 발음 미청취'],
        'next_role': 'director',
        'actual_listening': False, 'continuous_playback': False, 'tts_api_calls': 0, 'external_transfer': False, 'upload': False,
    })
    print(json.dumps({'task_id': TASK, 'changed': len(patches), 'unchanged': 90-len(patches), 'intro_estimate': estimate, 'shorts_impact': linked_impact, 'checks_passed': len(validation['checks']), 'output_folder': rel(OUT)}, ensure_ascii=False))

if __name__ == '__main__':
    main()
