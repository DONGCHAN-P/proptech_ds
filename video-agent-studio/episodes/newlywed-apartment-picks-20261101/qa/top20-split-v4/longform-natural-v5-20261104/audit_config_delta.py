import hashlib
import json
from pathlib import Path

ROOT = Path('C:/projects/realestate_reco')
OUT = Path(__file__).resolve().parent
KEY = 'config/video_language.json'
prior = json.loads((OUT/'script_audit_checks.json').read_text(encoding='utf-8'))
raw = (ROOT/KEY).read_bytes()
config = json.loads(raw.decode('utf-8-sig'))
names = {x['canonical_name']: x for x in config['protected_names']}
checks = {
    '단지명_차수보존': names['상계2차중앙하이츠']['reading_text'] == '상계 이차 중앙 하이츠' and '2차' in names['상계2차중앙하이츠']['retain_tokens'],
    '브랜드_간격추가_최신읽기문과일치': names['데이터로보는부동산']['reading_text'] == '데이터로 보는 부동산' and '데이터로 보는 부동산' in prior['latest_targeted_texts']['P01-INTRO-V3-02']['reading_text'],
    '고유명사_숫자변환보다우선': config['review_policy']['protected_names_before_number_normalization'] is True,
    '실제청취_요구유지': all(names[k]['listen_before_final_merge'] for k in ['상계2차중앙하이츠','데이터로보는부동산']) and config['review_policy']['spacing_is_not_proof_of_audible_naturalness'] is True,
    '원본숫자_장소_근거보존': config['review_policy']['preserve_numbers_places_entities_and_evidence'] is True,
}
result = {'task_id': prior['task_id'], 'path': KEY,
          'previous_sha256': prior['input_sha256'][KEY], 'current_sha256': hashlib.sha256(raw).hexdigest(),
          'observed_delta': '최종 납품 확인 중 브랜드 보호명 항목 추가를 발견해 해당 설정과 최신 읽기문 관계만 재검수했다. 기존 단지명 보호와 숫자 변환 전 처리·실제 청취 조건은 유지된다.',
          'checks': checks, 'passed': all(checks.values()), 'actual_generation_pipeline_execution': 'unchecked'}
(OUT/'config_delta_checks.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps(result, ensure_ascii=False))
assert result['passed']
