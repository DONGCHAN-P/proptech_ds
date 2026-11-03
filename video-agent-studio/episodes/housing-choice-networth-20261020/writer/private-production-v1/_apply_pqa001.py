from pathlib import Path
import collections
import difflib
import hashlib
import json
import re

OUT = Path(__file__).resolve().parent
EP = OUT.parent.parent
SCRIPT = OUT / 'script_v4_candidate.md'
QA = EP / 'qa/private-production-v1/findings.json'
SOURCE = EP / 'outputs/cost-wording-v3/script_cost_v3.md'
sha = lambda b: hashlib.sha256(b).hexdigest()
expected_script_sha = '2ee62730f6d2f85b834982efbdf4ce357f68c0d4048cda6e2960182cc4752520'
assert sha(SCRIPT.read_bytes()) == expected_script_sha, '후보가 다른 작업으로 변경됨; 덮어쓰기 중단'
loaded_bytes = {p.name:p.read_bytes() for p in OUT.glob('*.json')}
docs = {name:json.loads(content.decode('utf-8')) for name,content in loaded_bytes.items()}
qa_bytes = QA.read_bytes()
qa = json.loads(qa_bytes.decode('utf-8-sig'))
finding = next(x for x in qa['findings'] if x['issue_id'] == 'PQA-001')
assert finding['severity'] == 'required'

pattern = r'^## (\d+)\. ([^\n]+)\n(.*?)(?=^## |\Z)'
def sections(text):
    return [(int(m[1]),m[2],[p.strip() for p in m[3].strip().split('\n\n') if p.strip()]) for m in re.finditer(pattern,text,re.M|re.S)]

before_script = SCRIPT.read_text(encoding='utf-8')
before_sections = sections(before_script)
source_sections = sections(SOURCE.read_text(encoding='utf-8-sig'))
old = before_sections[1][2][1]
new = '집값은 먼저 짚고 가겠습니다. 최근에 집을 알아보셨다면 연 2%라는 숫자가 작게 느껴질 수 있습니다. 2006년부터 모은 실거래로 같은 단지·같은 전용면적에서 두 분기 각각 2건 이상 거래된 표본을 연결한 자체 지수를 만들었습니다. 각 분기는 30단지 이상을 연결하며, 포함되는 표본은 분기마다 바뀝니다. 이 지수로 본 2016년 2분기부터 2026년 2분기까지의 연평균 상승률은 서울 약 11.7%, 경기 6.6%, 인천 4.0%였습니다. 표본 선택 기준에 따라 상승률도 달라집니다.'
assert before_script.count(old) == 1
after_script = before_script.replace(old,new)
after_sections = sections(after_script)
for a,b in zip(before_sections,after_sections):
    assert a[:2] == b[:2] and len(a[2]) == len(b[2])
    for i,(ap,bp) in enumerate(zip(a[2],b[2]),1):
        if (a[0],i) != (2,2): assert ap == bp
assert before_sections[1][2][2] == after_sections[1][2][2]
nums = lambda s:collections.Counter(re.findall(r'\d+(?:\.\d+)?',s))
assert nums(after_script) - nums(before_script) == collections.Counter({'2':1,'30':1})
assert not nums(before_script) - nums(after_script)
assert nums(new.replace('2건','').replace('30단지','')) == nums(old)
assert all(x in new for x in ['같은 단지·같은 전용면적','두 분기 각각 2건 이상','30단지 이상','표본은 분기마다 바뀝니다','표본 선택 기준에 따라 상승률도 달라집니다','서울 약 11.7%, 경기 6.6%, 인천 4.0%'])
assert not re.search(r'공식 지수|43단지|2022Q4|아닙니다|아님|오해',new)
target_sha = sha(after_script.encode('utf-8'))
for doc in docs.values():
    if 'target_sha256' in doc:
        assert doc['target_sha256'] == expected_script_sha
        doc['target_sha256'] = target_sha

changes = docs['changes.json']
changes['scope'] += ' 최신 직접지시에 따라 PQA-001의 표본 기준·교체 표본·민감도 설명을 2장에 추가.'
changes['numbers_changed'] = True
changes['model_and_result_numbers_changed'] = False
changes['numeric_policy_exception'] = {'authorization':'최신 사용자 직접지시 및 PQA-001','added_disclosure_only':['두 분기 각각 2건 이상','30단지 이상 연결'],'existing_numbers_and_results':'보존; 새 수익률·새 원인·새 계산값 없음'}
changes['qa_input'] = {'path':'qa/private-production-v1/findings.json','sha256':sha(qa_bytes),'issue_id':'PQA-001','reviewed_revision':'script-cost-wording-v3','status':'문구 반영; 현 후보의 QA 재확인 대기'}
changes['changes'].append({'scene_id':'W4-C02-P02','chapter':2,'paragraph':2,'issue_id':'PQA-001','reason':['자체 연결 지수의 동일 단지·동일 면적, 두 분기 각각 거래 2건 이상, 연결 30단지 이상 기준 명시','분기마다 포함 표본이 바뀜과 표본 선택 기준에 따른 상승률 민감도를 짧게 설명','기존 연 2% 언급·2006년 수집 시작·최근 10년 기간·지역 상승률 유지'],'before':old,'after':new,'numbers':'기존 값 보존; 승인된 표본 기준 2건·30단지만 설명에 추가'})
changes['changes'].sort(key=lambda x:(x['chapter'],x['paragraph']))
changes['changed_paragraphs'] = len(changes['changes'])
changes['unchanged_paragraphs'] = 54-len(changes['changes'])

outline = docs['scene_outline.json']
row = outline['chapters'][1]['paragraphs'][1]
row['narration_anchor'] = new[:65]
row['narration_sha256'] = sha(new.encode('utf-8'))
row['message'] = '같은 단지·면적의 거래를 분기별로 연결한 자체 지수이며 표본 기준에 따라 상승률이 달라진다'
row['visual_direction'] = '기존 서울·경기·인천의 최근 10년 수치를 유지하고 발화 지역만 강조. 표·차트에 자체 실거래 연결 지수, 2016년 2분기→2026년 2분기, 연환산 복리상승률 %, 두 분기 각각 거래 2건 이상·연결 30단지 이상을 짧게 표시. 분기별 연결 표본의 교체와 표본 선택 민감도를 설명에 연결. 표본 수를 표시할 때는 분기별 연결 단지 수로 명시.'
row['changes'] = changes['changes'][next(i for i,x in enumerate(changes['changes']) if x['scene_id']=='W4-C02-P02')]['reason']
row['evidence'] = 'qa/private-production-v1/findings.json의 PQA-001 근거와 수정안 확인. writer의 원거래 재집계·독립 지수 재검수는 미수행. 동일 기간·수치 보존.'
row['internal_evidence'] = {'path':'qa/private-production-v1/findings.json','sha256':sha(qa_bytes),'pointer':'/findings/0/evidence','use':'서울 최소 표본 분기·단지 수와 강화 문턱 민감도 상세는 이 내부 근거에 보존; 낭독에 추가하지 않음'}
row['existing_screen_reuse']['content'] = '기존 최근 10년 지역 상승률 화면만 조건부 재사용. PQA-001의 지수 명칭·기간·단위·거래/연결 문턱·분기별 표본 설명을 추가하고 후속 QA가 실제 표기 확인.'
row['estimate_duration_seconds'] = [int(len(re.sub(r'\s','',new))/600*60+0.999),int(len(re.sub(r'\s','',new))/500*60+0.999)]

checks = docs['checks.json']
checks['qa_input'] = changes['qa_input']
checks['checks']['numeric_tokens_and_counts_equal'] = False
checks['checks']['numeric_difference_explained'] = 'PQA-001 직접 승인으로 표본 설명 2건·30단지 각 1회 추가. 기존 금액·비율·기간·계산값은 보존.'
checks['checks']['new_numeric_values'] = ['표본 기준 2건·30단지의 언급 추가; 기존 모형·결과 값 추가 없음']
checks['checks']['regional_history_paragraph_verbatim'] = False
checks['checks']['regional_period_and_rates_preserved'] = True
checks['checks']['all_other_v4_paragraphs_unchanged_by_pqa001'] = True
checks['checks']['pqa001_sample_criteria_and_sensitivity_explicit'] = True
checks['checks']['pqa001_qa_recheck'] = 'pending; writer 문구 반영은 QA 이슈 종결이 아님'
source_narration = '\n\n'.join(p for c in source_sections for p in c[2])
target_narration = '\n\n'.join(p for c in after_sections for p in c[2])
checks['metrics'].update({'target_narration_characters':len(target_narration),'target_narration_nonspace_characters':len(re.sub(r'\s','',target_narration)),'wording_similarity':round(difflib.SequenceMatcher(None,source_narration,target_narration,autojunk=False).ratio(),4)})
checks['pqa001_patch'] = {'previous_candidate_sha256':expected_script_sha,'changed_paragraph':'2장 2문단','other_paragraphs_verbatim':53,'existing_numbers_preserved':True,'approved_extra_mentions':['2건','30단지'],'new_causes_added':False,'independent_qa_closed':False}
docs['narration_handoff.json']['pronunciation'].update({'2건':'두 건','30단지':'서른 단지'})

issue = docs['issue_W4_QA_HANDOFF.json']
issue['status'] = 'PQA-001 문구 반영 완료·QA 재확인 요청; 이슈 종결 아님'
issue['proposal'] = '2장 2문단에 자체 지수·동일 단지/면적·두 분기 각각 2건 이상·연결 30단지 이상·분기별 표본 교체·민감도를 반영. 해당 문단과 지역 차트의 실제 표기만 우선 재확인. 2% 계획 가정·최근 10년 수치는 유지. 나머지 후보의 진행 중 QA 범위 유지.'
issue['qa_reference'] = changes['qa_input']
issue['target_sha256'] = target_sha

handoff = docs['handoff.json']
handoff['input_revisions']['PQA-001_findings'] = sha(qa_bytes)
handoff['affected_scene_ids'] = [x['scene_id'] for x in changes['changes']]
handoff['checks'][0]['check'] = '10장·54문단·기존 수치·결말 보존; 표본 기준 2건·30단지만 승인 추가'
handoff['checks'].append({'check':'PQA-001 문구·장면지시 반영','result':'implemented_pending_qa_recheck','evidence':'changes.json / checks.json'})

# 읽은 버전과 같을 때만 이 담당이 소유한 파일을 갱신한다.
assert sha(SCRIPT.read_bytes()) == expected_script_sha
assert QA.read_bytes() == qa_bytes
for name,content in loaded_bytes.items(): assert (OUT/name).read_bytes() == content, name
SCRIPT.write_text(after_script,encoding='utf-8',newline='\n')
for name,doc in docs.items():
    (OUT/name).write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'status':'PQA-001 incorporated; QA recheck pending','target_sha256':target_sha,'changed_from_previous_candidate':'2장 2문단 only','preserved_other_paragraphs':53,'model_and_result_numbers_changed':False},ensure_ascii=False))
